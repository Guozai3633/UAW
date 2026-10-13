"""Real SQL and fixed Model protocol; controlled verdicts are not LLM quality evidence."""

import json

import pytest

from tests.integration.agent.conftest import agent_case as agent_case
from tests.integration.agent.test_completion_postgres import deliver
from tests.integration.intent.test_understanding import proposal, response
from tests.integration.model.test_gateway import case as case
from tests.integration.test_control_plane import meta
from uaw.agent.completion.delivery import REPORTS
from uaw.shared.errors import DomainError


@pytest.fixture
async def understanding(understanding, case):
    value = proposal(understanding.original["text"])
    value["assumptions"] = ["A general explanation can explicitly discuss alternative meanings."]
    value["unresolved"] = ["The precise implementation has not been specified."]
    case.responses[:] = [response(value)]
    return understanding


@pytest.mark.parametrize("state", ["passed", "blocked"])
async def test_advisory_note_does_not_override_actual_semantic_verdict(agent_case, state):
    p = agent_case
    completion, pin, _, ctx = await deliver(
        p,
        state=state,
        text="Assuming the common interpretation, here is the general idea; alternatives differ.",
    )
    report = (await p.control.records.get(ctx.principal, REPORTS, pin.id)).payload
    assert not any(c["id"] == "unresolved-task" for c in report["checks"])
    assert report["outcome"] == ("succeeded" if state == "passed" else "blocked")
    assert all(v["state"] == state for v in report["verdicts"])
    native = json.loads(p.model_case.requests[-1].content)
    evaluation = json.loads(native["messages"][-1]["content"])
    frame = evaluation["task_frame"]
    assert frame["unresolved"] == ["The precise implementation has not been specified."]
    assert frame["assumptions"]
    assert frame["goal"] == p.understanding.original["text"]
    stored = await p.control.records.get(ctx.principal, "intent.frames", ctx.task_id)
    assert stored.payload == frame  # No deletion of uncertainty or substitution of the user goal.
    run = await p.domain[1].get_run(ctx.principal, ctx.run_id)
    if state == "passed":
        final = await completion.controller.complete(
            pin, ctx, meta("qualified-complete", run["revision"])
        )
        assert final["status"] == "completed"
    else:
        with pytest.raises(DomainError, match="not all passed"):
            await completion.controller.complete(pin, ctx, meta("essential-gap", run["revision"]))
        assert (await p.domain[1].get_run(ctx.principal, ctx.run_id))["status"] != "completed"
    assert len(p.model_case.requests) == 2
