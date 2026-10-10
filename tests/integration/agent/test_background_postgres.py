"""Actual queued Intent/Agent/completion pipeline, with controlled model HTTP replies."""

import hashlib
import json

import pytest
from pydantic import SecretStr

from tests.integration.agent.test_completion_postgres import review
from tests.integration.agent.test_root_postgres import decision
from tests.integration.intent.test_understanding import proposal, response
from tests.integration.model.test_gateway import case as case
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.test_stage_wiring import container
from uaw.agent.completion.contracts import contract_from_frame
from uaw.composition import compose_understanding_context
from uaw.intent.facade import IntentFacade
from uaw.intent.frame import FrameRepository
from uaw.intent.original import OriginalReader
from uaw.model.policy import PolicyResolver
from uaw.run.background import BackgroundAgent
from uaw.run.inputs import RunInputReader
from uaw.run.jobs import JOBS, RunJobs
from uaw.shared.builtin_tools import publish_builtin_office
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.shared.settings import Settings


@pytest.mark.parametrize("case", [{"active_provider_for_tools": True}], indirect=True)
@pytest.mark.parametrize(
    "acceptance,tool_decision",
    [(False, None), (True, None), (False, "approve_once"), (False, "decline")],
)
async def test_real_queue_pipeline_recovers_original_step_and_delivers(
    case, domain, tmp_path, acceptance, tool_decision
):
    config, runs, admin = domain
    await publish_builtin_office(config, admin, "background-office")
    control = container(runs.store, config, tmp_path)
    token = "u" * 40
    actor = Principal(
        id=case.ctx.principal.id,
        kind="user",
        auth_session_id="session-" + hashlib.sha256(token.encode()).hexdigest()[:24],
    )
    control.settings = Settings(
        profile="development",
        development_principal_id=actor.id,
        development_user_token=SecretStr(token),
        cursor_signing_key=SecretStr("k" * 40),
        agent_execution_enabled=True,
        agent_acceptance_required=acceptance,
    )
    control.run_service = runs
    control.model_service = case.model
    policies = PolicyResolver(runs.store, config, control.execution_permissions)
    control.intent_service = IntentFacade(
        OriginalReader(RunInputReader(runs.store)),
        compose_understanding_context(runs.store, policies),
        case.model,
        policies,
        FrameRepository(runs.store),
    )
    driver = BackgroundAgent(control)
    queue = await driver.prepare()
    conv = await runs.create_conversation(
        actor,
        {
            "title": "Background",
            "model_choice": {"mode": "explicit", "model_id": "fixture-model"},
            "memory_policy": {
                "revision": 0,
                "read_enabled": False,
                "contribute_enabled": False,
                "scope": {"resource_refs": []},
            },
        },
        meta("background-conversation"),
    )

    async def enqueue(tx, run):
        await queue.enqueue(tx, run, actor)

    original = await runs.submit(
        actor,
        {"conversation_id": conv["id"], "text": "Explain a concept", "attachment_refs": []},
        meta("background-submit"),
        on_admitted=enqueue,
    )
    case.requests.clear()
    case.responses[:] = [response(proposal("Explain a concept"))]
    assert await queue.tick()  # actual policy + preparing
    assert await queue.tick()  # actual understanding
    frame = await control.intent_service.frames.current(actor, original["task_id"])
    case.responses[:] = [
        decision("propose_completion", "Actual queued answer"),
        review(contract_from_frame(frame)["requirements"]),
    ]
    assert await queue.tick()  # actual role/rule
    assert await queue.tick()  # root creation
    if tool_decision:
        from datetime import UTC, datetime

        registry = driver.tools.facade.registry
        entry = next(e for e in registry.snapshot()[1] if e.spec()["id"] == "text.inspect")
        case.responses.insert(
            0,
            decision(
                "call_tools",
                "Inspect supplied text",
                [
                    {
                        "tool_ref": registry.reference(entry),
                        "arguments": {"text": "A\r\n学术"},
                        "action_id": "background-inspect",
                    }
                ],
            ),
        )

        async def wake(key):
            row = await runs.store.get(actor, JOBS, original["id"])
            await runs.store.put(
                actor,
                JOBS,
                row.resource_id,
                row.schema_name,
                {
                    **row.payload,
                    "revision": row.revision + 1,
                    "ready_at": datetime.now(UTC).isoformat(),
                },
                expected_revision=row.revision,
                request_id=key,
            )

        assert await queue.tick()
        waiting = (await runs.store.get(actor, JOBS, original["id"])).payload
        assert waiting["state"] == "waiting" and waiting["stage"] == "step", waiting
        current = await runs.get_run(actor, original["id"])
        assert current["status"] == "waiting_for_user"
        waiting_ctx = TrustedExecutionContext.model_validate_json(
            json.dumps(waiting["step_context"])
        )
        state = (await driver.agent.repository.owned(waiting["instance_ref"]["id"], waiting_ctx))[2]
        operation = await driver.agent.repository.operation(
            state.active_operation_ref.id, waiting_ctx
        )
        approval = await control.approvals.get(actor, operation.result["wait_ref"]["id"])
        await wake("wake-still-pending")
        assert await queue.tick()
        assert (await runs.get_run(actor, original["id"]))["revision"] == current["revision"]
        assert len(case.requests) == 2
        await control.approvals.decide(
            actor,
            {
                "approval_id": approval["id"],
                "decision": {
                    "decision": tool_decision,
                    "expected_arguments_hash": approval["arguments_hash"],
                    "expected_resource_refs": approval["resource_refs"],
                    "reason": "Actual controlled SQL protocol decision",
                },
            },
            meta("background-approval", approval["revision"]),
        )
        await wake("wake-actual-decision")
        assert await queue.tick()
        resumed = (await runs.store.get(actor, JOBS, original["id"])).payload
        assert resumed["state"] == "queued" and resumed["step"] == 2, resumed
        observed = await driver.agent.runtime.loop.observations.read(
            (
                await driver.agent.repository.operation(operation.id, operation.context)
            ).observation_ref,
            operation.context,
        )
        assert observed["result"]["kind"] == (
            "ok" if tool_decision == "approve_once" else "denied"
        ), observed
        if tool_decision == "approve_once":
            assert observed["result"]["payload"]["data"]["utf8_bytes"] == len("A\r\n学术".encode())
        else:
            assert observed["result"]["failure"]["code"] == "approval_declined"
        assert len(case.requests) == 2
    # Restart the queue before the model step, retaining the original job context.
    queue = RunJobs(runs.store, actor, advance=driver.advance)
    assert await queue.tick()
    job = (await runs.store.get(actor, JOBS, original["id"])).payload
    assert job["stage"] == "delivery" and "failure" not in job, job
    assert len(case.requests) == (4 if tool_decision else 3)
    if acceptance:
        from uaw.run.deliveries import DeliveryReader

        assert await queue.tick()
        waiting = (await runs.store.get(actor, JOBS, original["id"])).payload
        assert waiting["state"] == "waiting" and waiting["stage"] == "delivery"
        delivery, _ = await DeliveryReader(runs.store, control.blobs).read(actor, original["id"])
        await control.completion_controller.accept(
            actor,
            Ref.model_validate(delivery["bundle_ref"]),
            Ref.model_validate(delivery["artifact_ref"]),
            "accept",
            TrustedExecutionContext.model_validate_json(json.dumps(job["step_context"])),
            meta("background-user-accept"),
        )
        # Advance the queue's scheduling clock only; no permissions/timeouts relaxed.
        row = await runs.store.get(actor, JOBS, original["id"])
        from datetime import UTC, datetime

        await runs.store.put(
            actor,
            JOBS,
            row.resource_id,
            row.schema_name,
            {
                **row.payload,
                "revision": row.revision + 1,
                "ready_at": datetime.now(UTC).isoformat(),
            },
            expected_revision=row.revision,
            request_id="wake-after-accept",
        )
    assert await queue.tick()
    final = await runs.get_run(actor, original["id"])
    assert final["status"] == "completed" and len(case.requests) == (4 if tool_decision else 3)
    assert not await queue.tick()
