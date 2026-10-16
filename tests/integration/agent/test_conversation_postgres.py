"""Real PostgreSQL queue + owning model HTTP fixtures; not live model quality."""

import hashlib
import json
from types import SimpleNamespace

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import select

from tests.integration.model.test_gateway import case as case
from tests.integration.model.test_gateway import reply
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.test_stage_wiring import container
from uaw.composition import compose_understanding_context
from uaw.infrastructure.db.models import RecordRow
from uaw.intent.facade import IntentFacade
from uaw.intent.frame import FrameRepository
from uaw.intent.original import OriginalReader
from uaw.model.policy import PolicyResolver
from uaw.run.background import BackgroundAgent
from uaw.run.inputs import RunInputReader
from uaw.run.jobs import JOBS, RunJobs
from uaw.shared.builtin_tools import publish_builtin_office
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.settings import Settings

pytestmark = pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)


@pytest.fixture
async def scenario(case, domain, tmp_path):
    config, runs, admin = domain
    await publish_builtin_office(config, admin, "conversation-office")
    control = container(runs.store, config, tmp_path)
    token = "u" * 40
    actor = case.ctx.principal.model_copy(
        update={"auth_session_id": "session-" + hashlib.sha256(token.encode()).hexdigest()[:24]}
    )
    control.settings = Settings(
        profile="development",
        development_principal_id=actor.id,
        development_user_token=SecretStr(token),
        cursor_signing_key=SecretStr("k" * 40),
        agent_execution_enabled=True,
        agent_acceptance_required=True,
    )
    control.run_service, control.model_service = runs, case.model
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
    conversation = await runs.create_conversation(
        actor,
        {
            "title": "Conversation",
            "model_choice": {"mode": "explicit", "model_id": "fixture-model"},
            "memory_policy": {
                "revision": 0,
                "read_enabled": False,
                "contribute_enabled": False,
                "scope": {"resource_refs": []},
            },
        },
        meta("conversation-create"),
    )

    async def enqueue(tx, run):
        await queue.enqueue(tx, run, actor)

    run = await runs.submit(
        actor,
        {
            "conversation_id": conversation["id"],
            "text": "Compare two ideas; explain a reasonable interpretation.",
            "attachment_refs": [],
        },
        meta("conversation-submit"),
        on_admitted=enqueue,
    )
    case.requests.clear()
    for _ in range(4):
        assert await queue.tick()
    job = (await runs.store.get(actor, JOBS, run["id"])).payload
    assert job["stage"] == "step" and not job.get("failure"), job
    return SimpleNamespace(
        case=case,
        runs=runs,
        actor=actor,
        control=control,
        driver=driver,
        queue=queue,
        run=run,
        job=job,
    )


async def inventory(p, namespace):
    async with p.runs.store.database.sessions() as sql:
        return list(
            await sql.scalars(
                select(RecordRow.payload).where(
                    RecordRow.principal_id == p.actor.id,
                    RecordRow.namespace == namespace,
                    RecordRow.deleted.is_(False),
                )
            )
        )


def output(value):
    return httpx.Response(200, json=reply(json.dumps(value)))


async def test_reply_one_call_no_artifact_or_acceptance_and_restart(scenario):
    p = scenario
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "reply",
                "text": "Here is a useful explanation under an explicit assumption.",
            }
        )
    ]
    assert await p.queue.tick()
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert job["state"] == "finished", job.get("failure", job)
    current = await p.runs.get_run(p.actor, p.run["id"])
    assert current["status"] == "completed" and current["outcome"] == "succeeded"
    assert len(p.case.requests) == 1
    assert not await inventory(p, "workspace.artifacts")
    assert not await inventory(p, "agent.completion.reports")
    items = await inventory(p, "items")
    assert len([v for v in items if v["type"] == "agent_message"]) == 1
    assert not [v for v in items if v["type"] == "understanding"]
    replies = await inventory(p, "run.conversation.replies")
    assert len(replies) == 1 and replies[0]["item"]["text"].startswith("Here is")
    assert len(await inventory(p, "agent.conversation.decisions")) == 1
    restarted = RunJobs(p.runs.store, p.actor, advance=p.driver.advance, finalize=p.driver.finalize)
    assert not await restarted.tick()
    assert len(p.case.requests) == 1


async def test_essential_question_visible_same_run_not_terminal(scenario):
    p = scenario
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "ask",
                "question": {
                    "text": "Please paste the paper to summarize.",
                    "reason": "Its text is required to summarize it accurately.",
                    "options": [],
                },
            }
        )
    ]
    assert await p.queue.tick()
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert job["state"] == "blocked" and not job.get("failure"), job
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "waiting_for_user"
    questions = await inventory(p, "run.clarification_questions")
    assert len(questions) == 1 and questions[0]["state"] == "open"
    assert questions[0]["run_id"] == p.run["id"]
    assert not await inventory(p, "workspace.artifacts")
    assert len(p.case.requests) == 1


async def test_bad_provider_shape_keeps_failure_and_shows_useful_message(scenario):
    p = scenario
    p.case.responses[:] = [output({"protocol": "conversation-v1", "action": "reply"})]
    assert await p.queue.tick()
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert job["failure"]["code"] == "provider_structured_output_invalid", job
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "failed"
    messages = [v["text"] for v in await inventory(p, "items") if v["type"] == "agent_message"]
    assert messages and "响应格式" in messages[0]
    assert not any("protected receipt" in text for text in messages)
    assert len(p.case.requests) == 1
    assert not await inventory(p, "workspace.artifacts")


@pytest.mark.parametrize("choice", ["approve_once", "decline"])
async def test_actual_tool_gates_then_message_only(scenario, choice):
    from datetime import UTC, datetime

    p = scenario
    entry = next(
        e for e in p.driver.tools.facade.registry.snapshot()[1] if e.spec()["id"] == "text.inspect"
    )
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "tool",
                "calls": [
                    {
                        "tool_ref": p.driver.tools.facade.registry.reference(entry),
                        "arguments": {"text": "A\r\n学术"},
                        "action_id": "conversation-inspect",
                    }
                ],
            }
        ),
        output(
            {
                "protocol": "conversation-v1",
                "action": "reply",
                "text": "The tool result is available."
                if choice == "approve_once"
                else "The tool was declined; no inspection was performed.",
            }
        ),
    ]
    assert await p.queue.tick()
    waiting = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert waiting["state"] == "waiting", waiting.get("failure", waiting)
    ctx = TrustedExecutionContext.model_validate_json(json.dumps(waiting["step_context"]))
    state = (await p.driver.agent.repository.owned(waiting["instance_ref"]["id"], ctx))[2]
    operation = await p.driver.agent.repository.operation(state.active_operation_ref.id, ctx)
    approval = await p.control.approvals.get(p.actor, operation.result["wait_ref"]["id"])
    await p.control.approvals.decide(
        p.actor,
        {
            "approval_id": approval["id"],
            "decision": {
                "decision": choice,
                "expected_arguments_hash": approval["arguments_hash"],
                "expected_resource_refs": approval["resource_refs"],
                "reason": "Controlled original exact action",
            },
        },
        meta("conversation-approval", approval["revision"]),
    )
    row = await p.runs.store.get(p.actor, JOBS, p.run["id"])
    await p.runs.store.put(
        p.actor,
        JOBS,
        row.resource_id,
        row.schema_name,
        {**row.payload, "revision": row.revision + 1, "ready_at": datetime.now(UTC).isoformat()},
        expected_revision=row.revision,
        request_id="wake-original",
    )
    assert await p.queue.tick()
    assert len(p.case.requests) == 1
    completed = await p.driver.agent.repository.operation(operation.id, ctx)
    observed = await p.driver.agent.runtime.loop.observations.read(completed.observation_ref, ctx)
    assert observed["result"]["kind"] == ("ok" if choice == "approve_once" else "denied")
    assert await p.queue.tick()
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert job["state"] == "finished", job.get("failure", job)
    assert len(p.case.requests) == 2
    assert not await inventory(p, "workspace.artifacts")


async def test_cancel_after_model_before_reply_does_not_publish(scenario, monkeypatch):
    from uaw.run import conversation_entry

    p = scenario
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "reply",
                "text": "Must not be published after cancellation.",
            }
        )
    ]
    publish = conversation_entry.publish

    async def cancel_then_publish(agent, operation, ctx):
        current = await p.runs.get_run(p.actor, p.run["id"])
        await p.runs.control(
            p.actor,
            {
                "run_id": p.run["id"],
                "control": {
                    "mode": "cancel",
                    "preserve_refs": [],
                    "reason": "Controlled cancellation before terminal commit",
                },
            },
            meta("conversation-cancel", current["revision"]),
        )
        return await publish(agent, operation, ctx)

    monkeypatch.setattr(conversation_entry, "publish", cancel_then_publish)
    assert await p.queue.tick()
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "cancelled"
    assert not [v for v in await inventory(p, "items") if v["type"] == "agent_message"]
    assert not await inventory(p, "run.conversation.replies")
    assert len(p.case.requests) == 1


async def test_restart_after_original_response_does_not_resend(scenario, monkeypatch):
    import asyncio

    p = scenario
    models = p.driver.agent.runtime.loop.models
    generate = models.generate
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "reply",
                "text": "Recover this original response.",
            }
        )
    ]

    async def interrupted(request, ctx):
        await generate(request, ctx)
        raise asyncio.CancelledError()

    monkeypatch.setattr(models, "generate", interrupted)
    with pytest.raises(asyncio.CancelledError):
        await p.queue.tick()
    assert len(p.case.requests) == 1
    monkeypatch.setattr(models, "generate", generate)
    restarted = RunJobs(p.runs.store, p.actor, advance=p.driver.advance, finalize=p.driver.finalize)
    assert await restarted.tick()
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert job["state"] == "finished", job.get("failure", job)
    assert len(p.case.requests) == 1
    assert len(await inventory(p, "run.conversation.replies")) == 1


async def test_deliver_keeps_artifact_verification_and_user_acceptance(scenario):
    from datetime import UTC, datetime

    from tests.integration.agent.test_completion_postgres import review
    from uaw.agent.completion.contracts import contract_from_frame
    from uaw.run.deliveries import DeliveryReader
    from uaw.shared.contracts import Ref

    p = scenario
    frame = (await p.runs.store.get(p.actor, "intent.frames", p.run["task_id"])).payload
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "deliver",
                "text": "A complete formally requested report.",
            }
        ),
        review(contract_from_frame(frame)["requirements"]),
    ]
    assert await p.queue.tick()
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert job["stage"] == "delivery", job.get("failure", job)
    assert len(p.case.requests) == 2
    assert len(await inventory(p, "workspace.artifacts")) == 1
    assert len(await inventory(p, "agent.completion.reports")) == 1
    assert await p.queue.tick()
    current = await p.runs.get_run(p.actor, p.run["id"])
    assert current["status"] != "completed"
    delivery, _ = await DeliveryReader(p.runs.store, p.control.blobs).read(p.actor, p.run["id"])
    await p.control.completion_controller.accept(
        p.actor,
        Ref.model_validate(delivery["bundle_ref"]),
        Ref.model_validate(delivery["artifact_ref"]),
        "accept",
        TrustedExecutionContext.model_validate_json(json.dumps(job["step_context"])),
        meta("conversation-user-accept"),
    )
    row = await p.runs.store.get(p.actor, JOBS, p.run["id"])
    await p.runs.store.put(
        p.actor,
        JOBS,
        row.resource_id,
        row.schema_name,
        {**row.payload, "revision": row.revision + 1, "ready_at": datetime.now(UTC).isoformat()},
        expected_revision=row.revision,
        request_id="wake-acceptance",
    )
    assert await p.queue.tick()
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert job["state"] == "finished", job.get("failure", job)
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "completed"


async def test_policy_revocation_during_model_call_is_not_cached(scenario, monkeypatch):
    p = scenario
    models = p.driver.agent.runtime.loop.models
    generate = models.generate
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "reply",
                "text": "Must not publish after revocation.",
            }
        )
    ]

    async def revoked(request, ctx):
        result = await generate(request, ctx)
        row = await p.runs.store.get(p.actor, "execution.policies", ctx.capability_policy_ref.id)
        value = {
            **row.payload,
            "revision": row.revision + 1,
            "allowed_capabilities": [
                c for c in row.payload["allowed_capabilities"] if c != "agent.step"
            ],
            "denied_capabilities": ["agent.step"],
        }
        await p.runs.store.put(
            p.actor,
            row.namespace,
            row.resource_id,
            row.schema_name,
            value,
            expected_revision=row.revision,
            request_id="revoke-before-publication",
        )
        return result

    monkeypatch.setattr(models, "generate", revoked)
    assert await p.queue.tick()
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert job["state"] == "blocked" and job.get("failure"), job
    assert not await inventory(p, "run.conversation.replies")
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "failed"
    assert all(
        v.get("text") != "Must not publish after revocation." for v in await inventory(p, "items")
    )
    assert len(p.case.requests) == 1
