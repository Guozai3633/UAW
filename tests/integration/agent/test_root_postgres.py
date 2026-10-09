import asyncio
import json

import httpx
from sqlalchemy import select

from tests.integration.agent.conftest import agent_case as agent_case
from tests.integration.model.test_gateway import reply
from uaw.infrastructure.db.models import OutboxRow
from uaw.shared.contracts import Ref
from uaw.shared.schema import validate_contract


async def start(p):
    result = await p.assembly.runtime.start(p.start, p.ctx)
    assert result["kind"] == "ok", result
    return Ref.model_validate(result["output_refs"][0])


async def request(p, ref, operation="step-one"):
    _, _, state, view = await p.assembly.repository.current(ref, p.ctx)
    ctx = p.ctx.model_copy(
        update={
            "operation_id": operation,
            "attempt_id": operation + "-model",
            "trace_id": operation + "-trace",
        }
    )
    return {
        "instance_ref": ref.wire(),
        "observations": [r.wire() for r in state.observation_refs],
        "current_frame_ref": p.start["task_frame_ref"],
        "remaining_budget": view.remaining_budget,
    }, ctx


def decision(action="respond", text="Actual protocol candidate", calls=None):
    return httpx.Response(
        200, json=reply(json.dumps({"action": action, "text": text, "proposed_calls": calls or []}))
    )


async def test_root_creation_has_one_instance_and_never_calls_model(agent_case):
    p = agent_case
    first, again = await asyncio.gather(
        p.assembly.runtime.start(p.start, p.ctx), p.assembly.runtime.start(p.start, p.ctx)
    )
    assert first == again and first["kind"] == "ok", (first, again)
    assert not p.model_case.requests
    assert first["payload"]["model_policy_ref"] == p.ctx.model_policy_ref.wire()
    assert (await p.domain[1].get_run(p.ctx.principal, p.ctx.run_id))["root_agent_ref"] == first[
        "output_refs"
    ][0]
    changed = await p.assembly.runtime.start({**p.start, "creation_key": "other-key"}, p.ctx)
    assert changed["kind"] != "ok" and not p.model_case.requests


async def test_respond_uses_actual_context_fixed_model_and_does_not_complete_run(agent_case):
    p = agent_case
    ref = await start(p)
    raw, ctx = await request(p, ref)
    p.model_case.responses[:] = [decision()]
    result = await p.assembly.runtime.step(raw, ctx)
    assert result["kind"] == "ok", result
    assert result["payload"]["action"] == "respond"
    validate_contract("RuntimeAgentruntimeStepResult", result)
    native = json.loads(p.model_case.requests[-1].content)
    assert native["model"] == "fixture-model" and native["messages"][0]["role"] == "system"
    assert "root Agent" in native["messages"][0]["content"]
    assert (
        p.model_case.run["id"] == (await p.domain[1].get_run(p.ctx.principal, p.ctx.run_id))["id"]
    )
    assert (await p.domain[1].get_run(p.ctx.principal, p.ctx.run_id))["status"] != "completed"
    assert len(p.model_case.requests) == 1
    assert await p.assembly.runtime.step(raw, ctx) == result
    assert len(p.model_case.requests) == 1


async def test_owned_identity_revision_and_budget_are_not_model_parameters(agent_case):
    p = agent_case
    ref = await start(p)
    raw, ctx = await request(p, ref)
    spoof = ctx.model_copy(
        update={
            "principal": ctx.principal.model_copy(update={"auth_session_id": "another-session"})
        }
    )
    assert (await p.assembly.runtime.step(raw, spoof))["kind"] != "ok"
    extra = await p.assembly.runtime.step({**raw, "approved": True}, ctx)
    assert extra["kind"] != "ok"
    unlimited = {**raw, "remaining_budget": {**raw["remaining_budget"], "max_steps": 999}}
    assert (await p.assembly.runtime.step(unlimited, ctx))["failure"][
        "code"
    ] == "agent_budget_stale"
    stale = {**raw, "instance_ref": {**ref.wire(), "version": "999"}}
    assert (await p.assembly.runtime.step(stale, ctx))["kind"] != "ok"
    assert not p.model_case.requests


async def test_completion_proposal_needs_current_verifier_and_emits_actual_revision(agent_case):
    p = agent_case
    root = await start(p)
    raw, ctx = await request(p, root)
    p.model_case.responses[:] = [decision("propose_completion", "Model says work is complete")]
    result = await p.assembly.runtime.step(raw, ctx)
    assert result["kind"] == "failed" and result["failure"]["code"] == "capability_unavailable"
    instance, _, state = await p.assembly.repository.owned(root.id, ctx)
    assert instance.status == "failed" and state.active_operation_ref is None
    assert (await p.domain[1].get_run(ctx.principal, ctx.run_id))["status"] != "completed"
    assert len(p.model_case.requests) == 1
    async with p.assembly.repository.store.database.sessions() as session:
        latest = await session.scalar(
            select(OutboxRow)
            .where(
                OutboxRow.principal_id == ctx.principal.id,
                OutboxRow.event_type == "agent.updated",
            )
            .order_by(OutboxRow.seq.desc())
            .limit(1)
        )
    envelope = await p.assembly.repository.store.get(ctx.principal, "events", latest.event_id)
    assert latest.payload["parameters"]["revision"] == instance.revision
    assert envelope.payload["base_revision"] == instance.revision - 1
    assert envelope.payload["result_revision"] == instance.revision
