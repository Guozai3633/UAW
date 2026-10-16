"""Real SQL/Intent/root lifecycle; controlled model only, no human approval or live LLM."""

import hashlib
import json
from types import SimpleNamespace

import pytest
from pydantic import SecretStr
from sqlalchemy import select

from tests.integration.agent.test_root_postgres import decision
from tests.integration.intent.test_understanding import proposal, response
from tests.integration.model.test_gateway import case as case
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.test_stage_wiring import container
from uaw.agent.repository import pin
from uaw.composition import compose_understanding_context
from uaw.infrastructure.db.models import OutboxRow, RecordRow
from uaw.intent.facade import IntentFacade
from uaw.intent.frame import FrameRepository
from uaw.intent.original import OriginalReader
from uaw.model.policy import PolicyResolver
from uaw.run.background import BackgroundAgent
from uaw.run.inputs import RunInputReader
from uaw.run.jobs import JOBS
from uaw.shared.builtin_tools import publish_builtin_office
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.shared.errors import DomainError
from uaw.shared.schema import validate_contract
from uaw.shared.settings import Settings


@pytest.fixture
async def prepared(case, domain, tmp_path):
    config, runs, admin = domain
    await publish_builtin_office(config, admin, "pause-office")
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
    driver = BackgroundAgent(control, conversation_mode=False)
    queue = await driver.prepare()
    conv = await runs.create_conversation(
        actor,
        {
            "title": "Pause",
            "model_choice": {"mode": "explicit", "model_id": "fixture-model"},
            "memory_policy": {
                "revision": 0,
                "read_enabled": False,
                "contribute_enabled": False,
                "scope": {"resource_refs": []},
            },
        },
        meta("pause-conversation"),
    )

    async def enqueue(tx, run):
        await queue.enqueue(tx, run, actor)

    run = await runs.submit(
        actor,
        {
            "conversation_id": conv["id"],
            "text": "Compare two unspecified approaches",
            "attachment_refs": [],
        },
        meta("pause-submit"),
        on_admitted=enqueue,
    )
    case.requests.clear()
    case.responses[:] = [response(proposal("Compare two unspecified approaches"))]
    for _ in range(4):
        assert await queue.tick()
    job = (await runs.store.get(actor, JOBS, run["id"])).payload
    return SimpleNamespace(
        case=case, actor=actor, runs=runs, driver=driver, queue=queue, run=run, job=job
    )


async def items(p):
    async with p.runs.store.database.sessions() as sql:
        return (
            await sql.scalars(
                select(RecordRow.payload).where(
                    RecordRow.principal_id == p.actor.id,
                    RecordRow.namespace == "items",
                    RecordRow.payload["run_id"].astext == p.run["id"],
                    RecordRow.deleted.is_(False),
                )
            )
        ).all()


async def controlled_pause_operation(p, monkeypatch, text):
    """Fault boundaries use a controlled owning Model reader, never live LLM evidence.

    The end-to-end cases above exercise actual persisted Model/Context replies.
    These cases target SQL publication rollback; rebuilding the full prompt for
    every injected boundary adds unrelated work without changing that boundary.
    """
    agent = p.driver.agent
    ctx = TrustedExecutionContext.model_validate_json(json.dumps(p.job["step_context"]))
    instance, _, state, view = await agent.repository.current(
        Ref.model_validate(p.job["instance_ref"]), ctx
    )
    request = {
        "instance_ref": pin("agent_instance", instance.wire()).wire(),
        "observations": [r.wire() for r in state.observation_refs],
        "current_frame_ref": p.job["frame_ref"],
        "remaining_budget": view.remaining_budget,
    }
    operation, owned = await agent.repository.claim(request, ctx)
    assert owned
    proposal_value = {"action": "wait", "text": text, "proposed_calls": []}
    original_output = await p.runs.store.get(
        p.actor, "model.outputs", p.job["context"]["attempt_id"]
    )
    output = json.loads(json.dumps(original_output.payload))
    output.update(
        attempt_id=ctx.attempt_id, text=json.dumps(proposal_value), structured_data=proposal_value
    )
    output["usage"]["attempt_id"] = ctx.attempt_id
    output_ref = {"kind": "content", "id": ctx.attempt_id, "version": "1"}
    model_result = {"kind": "ok", "payload": output, "output_refs": [output_ref]}
    validate_contract("RuntimeModelruntimeGenerateResult", model_result)
    result = {
        "kind": "ok",
        "output_refs": [],
        "payload": {
            "action": "wait",
            "model_output_ref": output_ref,
            "proposed_calls": [],
            "instance_ref": request["instance_ref"],
        },
    }

    async def verify():
        await agent.runtime.loop.verify(operation, ctx)

    await agent.repository.update(
        operation,
        {
            "phase": "finished",
            "proposal": proposal_value,
            "model_result": model_result,
            "result": result,
        },
        ctx,
        verify=verify,
        finish=True,
    )

    async def read(original, actual):
        assert original == model_result and actual == ctx
        return json.loads(json.dumps(output))

    monkeypatch.setattr(agent.runtime.loop.models, "read", read)


@pytest.mark.parametrize("case", [{"active_provider_for_tools": True}], indirect=True)
@pytest.mark.parametrize("action", ["wait", "blocked"])
async def test_original_question_is_visible_atomic_and_restart_idempotent(prepared, action):
    p = prepared
    text = "请补充具体方案名称。\n\n当前缺少比较对象。"
    p.case.responses[:] = [decision(action, text)]
    assert await p.queue.tick()
    all_items = await items(p)
    questions = [i for i in all_items if i["type"] == "agent_message"]
    assert (
        len(questions) == 1
        and questions[0]["text"] == text
        and questions[0]["status"] == "completed"
    )
    assert len([i for i in all_items if i["type"] == "understanding"]) == 1
    current = await p.runs.get_run(p.actor, p.run["id"])
    assert current["status"] == "waiting_for_user" and "outcome" not in current
    saved = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert saved["state"] == "blocked" and "failure" not in saved
    assert len(p.case.requests) == 2 and not await p.queue.tick()
    assert len(questions[0]["resource_refs"]) == 3
    assert questions[0]["resource_refs"][1]["id"] == "web-step-model-1-" + p.run["id"]
    assert (await p.driver.advance(p.job))["state"] == "blocked"
    assert await items(p) == all_items
    assert (await p.runs.get_run(p.actor, p.run["id"])) == current and len(p.case.requests) == 2
    async with p.runs.store.database.sessions() as sql:
        events = (
            await sql.scalars(
                select(OutboxRow)
                .where(
                    OutboxRow.principal_id == p.actor.id,
                    OutboxRow.stream_id == current["conversation_id"],
                )
                .order_by(OutboxRow.seq)
            )
        ).all()
    question_events = [e for e in events if e.payload.get("parameters") == questions[0]]
    wait_events = [e for e in events if e.payload.get("parameters") == current]
    assert (
        len(question_events) == 1
        and len(wait_events) == 1
        and question_events[0].seq < wait_events[0].seq
    )


@pytest.mark.parametrize("case", [{"active_provider_for_tools": True}], indirect=True)
@pytest.mark.parametrize("mode", ["cancel", "frame", "operation", "model", "blank"])
async def test_changed_cancelled_or_empty_source_never_publishes_question(
    prepared, monkeypatch, mode
):
    p = prepared
    await controlled_pause_operation(p, monkeypatch, "" if mode == "blank" else "Which approach?")
    original = p.driver.publish_pause

    async def changed(agent, operation_id, ctx, result):
        if mode == "cancel":
            current = await p.runs.get_run(p.actor, p.run["id"])
            await p.runs.control(
                p.actor,
                {
                    "run_id": p.run["id"],
                    "control": {"mode": "cancel", "preserve_refs": [], "reason": "stop"},
                },
                meta("pause-cancel", current["revision"]),
            )
        elif mode in ("frame", "operation"):
            namespace = "intent.frames" if mode == "frame" else "agent.loop.operations"
            row = await p.runs.store.get(
                p.actor, namespace, ctx.task_id if mode == "frame" else operation_id
            )
            value = json.loads(json.dumps(row.payload))
            value["revision"] = row.revision + 1
            if mode == "frame":
                value["summary"] = "Changed task"
            else:
                value["proposal"]["text"] = "Different question"
            await p.runs.store.put(
                p.actor,
                namespace,
                row.resource_id,
                row.schema_name,
                value,
                expected_revision=row.revision,
                request_id="pause-change-" + mode,
            )
        elif mode == "model":
            read = agent.runtime.loop.models.read

            async def different(*args):
                output = await read(*args)
                return {
                    **output,
                    "structured_data": {
                        "action": "wait",
                        "text": "Changed output",
                        "proposed_calls": [],
                    },
                }

            monkeypatch.setattr(agent.runtime.loop.models, "read", different)
        await original(agent, operation_id, ctx, result)

    monkeypatch.setattr(p.driver, "publish_pause", changed)
    assert await p.queue.tick()
    assert not [i for i in await items(p) if i["type"] == "agent_message"]
    assert len(p.case.requests) == 1  # Intent only; no model send in boundary publication tests.
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert job["state"] == "blocked" and job["failure"]
    current = await p.runs.get_run(p.actor, p.run["id"])
    assert current["status"] == ("cancelled" if mode == "cancel" else "failed")
    ctx = TrustedExecutionContext.model_validate_json(json.dumps(p.job["step_context"]))
    with pytest.raises(DomainError):
        await original(p.driver.agent, "missing-operation", ctx, {})
