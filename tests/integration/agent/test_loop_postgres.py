import os

import pytest

from tests.integration.agent.conftest import agent_case as agent_case
from tests.integration.agent.test_root_postgres import decision, request, start
from tests.integration.test_control_plane import meta
from uaw.agent.engines.langgraph import JsonCheckpointSerializer
from uaw.agent.repository import AgentRepository, identifier, pin
from uaw.shared.contracts import Ref

pytestmark = pytest.mark.parametrize("case", [{"active_provider_for_tools": True}], indirect=True)


async def test_actual_tool_wait_approval_resume_and_observation(agent_case):
    p = agent_case
    root = await start(p)
    raw, ctx = await request(p, root)
    call = {
        "tool_ref": p.tool_ref.wire(),
        "action_id": "root-inspect",
        "arguments": {"text": "  A\r\n学术  "},
    }
    p.model_case.responses[:] = [decision("call_tools", "inspect actual text", [call])]
    waiting = await p.assembly.runtime.step(raw, ctx)
    if waiting["kind"] == "ok":
        diagnostic = await p.assembly.runtime.loop.observations.read(
            Ref.model_validate(waiting["output_refs"][0]), ctx
        )
        assert waiting["kind"] == "waiting", diagnostic["result"]
    assert waiting["kind"] == "waiting", waiting
    assert len(p.model_case.requests) == 1
    current = await p.assembly.repository.owned(root.id, ctx)
    operation_ref = current[2].active_operation_ref
    operation = await p.assembly.repository.operation(operation_ref.id, ctx)
    assert (
        await p.tools.ledger.get(
            "tool.budget.reserved", operation.tool_context.attempt_id, operation.tool_context
        )
        is None
    )
    approval = await p.tools.approvals.get(ctx.principal, waiting["wait_ref"]["id"])
    await p.tools.approvals.decide(
        ctx.principal,
        {
            "approval_id": approval["id"],
            "decision": {
                "decision": "approve_once",
                "expected_arguments_hash": approval["arguments_hash"],
                "expected_resource_refs": approval["resource_refs"],
                "reason": "actual SQL test approval",
            },
        },
        meta("root-approve", approval["revision"]),
    )
    # New repository/loop instances recover only the original persisted step.
    from uaw.agent.loop import AgentLoop

    old = p.assembly.runtime.loop
    restored = AgentLoop(
        AgentRepository(old.repository.store, old.repository.sources),
        old.contexts,
        old.models,
        old.observations,
        tools=old.tools,
        tool_access=old.tool_access,
    )
    result = await restored.resume(operation_ref, ctx)
    assert result["kind"] == "ok", result
    assert len(p.model_case.requests) == 1
    saved = await old.observations.read(Ref.model_validate(result["output_refs"][0]), ctx)
    assert saved["result"]["payload"]["data"]["utf8_bytes"] == len(
        call["arguments"]["text"].encode()
    )
    assert saved["result"]["payload"]["status"] == "succeeded"
    assert await p.assembly.runtime.step(raw, ctx) == result
    assert len(p.model_case.requests) == 1
    next_raw, next_ctx = await request(
        p, Ref.model_validate(result["payload"]["instance_ref"]), "after-tool"
    )
    p.model_case.responses[:] = [decision("respond", "Result based on the actual observation")]
    answered = await p.assembly.runtime.step(next_raw, next_ctx)
    assert answered["kind"] == "ok", answered
    assert "utf8_bytes" in p.model_case.requests[-1].content.decode()
    assert (await p.domain[1].get_run(ctx.principal, ctx.run_id))["status"] != "completed"


async def test_unknown_model_send_is_not_resent_by_restart(agent_case):
    p = agent_case
    root = await start(p)
    raw, ctx = await request(p, root)
    loop = p.assembly.runtime.loop
    operation, _ = await loop.repository.claim(raw, ctx)
    snapshot = await loop.contexts.prepare(operation.id, (), ctx)
    model_request = await loop.models.request(snapshot.snapshot_ref, ctx)

    async def verify():
        await loop.verify(operation, ctx)

    prepared = await loop.repository.update(
        operation,
        {
            "phase": "prepared",
            "snapshot_ref": snapshot.snapshot_ref.wire(),
            "context_epoch": snapshot.epoch,
            "model_request": model_request,
        },
        ctx,
        verify=verify,
    )
    # Genuine unfinished Model domain intent; no fake transport success or receipt.
    from uaw.infrastructure.db.records import parameter_hash
    from uaw.infrastructure.db.transactions import RecordTransaction
    from uaw.model.gateway import request_meta

    digest = parameter_hash({"request": model_request, "context": ctx.wire()})

    async def claim(tx: RecordTransaction):
        await tx.write(
            "model.invocations",
            ctx.attempt_id,
            "ModelInvocation",
            {
                "id": ctx.attempt_id,
                "run_id": ctx.run_id,
                "request_hash": digest,
                "request": model_request,
                "operation_id": ctx.operation_id,
                "trace_id": ctx.trace_id,
                "state": "claimed",
                "created_at": "2026-10-09T00:00:00Z",
            },
        )
        return {"new": True}

    await loop.models.model.gateway.transactions.execute(
        ctx.principal,
        "conversation:" + ctx.scope.conversation_id,
        request_meta("model-claim", ctx.attempt_id),
        {"action": "model.claim", "hash": digest},
        claim,
    )
    pending = await loop.resume(pin("content", prepared.wire()), ctx)
    assert pending["kind"] != "ok" and pending["failure"]["category"] == "unknown_effect", pending
    assert not p.model_case.requests
    assert (await loop.repository.owned(root.id, ctx))[2].active_operation_ref is not None


async def test_cancelled_root_stops_before_any_model_send(agent_case):
    p = agent_case
    root = await start(p)
    raw, ctx = await request(p, root)
    current = await p.domain[1].get_run(ctx.principal, ctx.run_id)
    await p.domain[1].control(
        ctx.principal,
        {
            "run_id": ctx.run_id,
            "control": {
                "mode": "cancel",
                "preserve_refs": [],
                "reason": "stop root",
            },
        },
        meta("cancel-root", current["revision"]),
    )
    result = await p.assembly.runtime.step(raw, ctx)
    assert result["kind"] == "cancelled", result
    assert (await p.assembly.repository.owned(root.id, ctx))[0].status == "cancelled"
    assert not p.model_case.requests


async def test_langgraph_has_real_postgres_json_checkpoint_and_end_is_not_completion(agent_case):
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    p = agent_case
    root = await start(p)
    p.model_case.responses[:] = [decision()]
    connection = os.environ["UAW_TEST_DATABASE_URL"].replace("postgresql+psycopg:", "postgresql:")
    async with AsyncPostgresSaver.from_conn_string(
        connection, serde=JsonCheckpointSerializer()
    ) as saver:
        await saver.setup()
        try:
            engine = p.assembly.engine(checkpointer=saver)
            result = await engine.run(root, p.ctx, max_cycles=2)
            assert result["kind"] == "ok", result
            assert result["payload"]["action"] == "respond" and len(p.model_case.requests) == 1
            from uaw.agent.contracts import identity

            thread = identifier(
                "graph-",
                {"owner": identity(p.ctx), "agent": root.wire(), "operation": p.ctx.operation_id},
            )
            checkpoint = await saver.aget_tuple(
                {"configurable": {"thread_id": thread, "checkpoint_ns": ""}}
            )
            assert (
                checkpoint is not None
                and checkpoint.checkpoint["channel_values"]["result"]["kind"] == "ok"
            )
            assert (await p.domain[1].get_run(p.ctx.principal, p.ctx.run_id))[
                "status"
            ] != "completed"
        finally:
            if "thread" in locals():
                await saver.adelete_thread(thread)
