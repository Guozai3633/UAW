import asyncio

from tests.integration.agent.conftest import agent_case as agent_case
from tests.integration.agent.test_root_postgres import decision, request, start
from uaw.agent.factory import AgentFactory
from uaw.shared.contracts import Ref


async def test_current_root_limit_and_concurrent_step_prevent_new_model_send(agent_case):
    p = agent_case
    p.assembly.runtime.factory = AgentFactory(p.assembly.repository, max_steps=1)
    root = await start(p)
    raw, ctx = await request(p, root)
    p.model_case.responses[:] = [decision()]
    responses = await asyncio.gather(
        p.assembly.runtime.step(raw, ctx), p.assembly.runtime.step(raw, ctx)
    )
    passed = [r for r in responses if r["kind"] == "ok"]
    assert passed and len(p.model_case.requests) == 1, responses
    next_raw, next_ctx = await request(
        p, Ref.model_validate(passed[0]["payload"]["instance_ref"]), "beyond-limit"
    )
    denied = await p.assembly.runtime.step(next_raw, next_ctx)
    assert denied["failure"]["code"] == "agent_step_limit", denied
    assert len(p.model_case.requests) == 1


async def test_incomplete_task_scope_is_denied_before_root_creation(agent_case):
    p = agent_case
    changed = p.ctx.model_copy(update={"task_id": None})
    denied = await p.assembly.runtime.start(p.start, changed)
    assert denied["kind"] != "ok" and not p.model_case.requests
