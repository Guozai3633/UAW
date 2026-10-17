"""A's real owning queue/model/SQL with D's clock and controlled provider/time.

These exercise the actual cross-module accounting implementation, not real
elapsed long waits, live provider quality, native access or human acceptance.
"""

from datetime import UTC, datetime, timedelta

import pytest

from tests.integration.agent import test_execution_segments as segment_cases
from tests.integration.agent.test_conversation_controls import answer, control_meta
from tests.integration.agent.test_conversation_controls import case as case
from tests.integration.agent.test_conversation_controls import domain as domain
from tests.integration.agent.test_conversation_controls import scenario as scenario
from tests.integration.agent.test_conversation_postgres import inventory, output
from tests.integration.agent.test_conversation_resume import snapshot
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.execution_clock import ExecutionClocks
from uaw.run.jobs import JOBS, RunJobs

pytestmark = pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)


def install(p, monkeypatch):
    def factory(records):
        return ExecutionClocks(
            records,
            effects=RunIdleEffects(),
            now=lambda: (p.future if hasattr(p, "future") else datetime.now(UTC)).isoformat(),
        )

    monkeypatch.setattr(segment_cases, "ControlledClockSeam", factory)


async def test_real_owned_clock_resumes_original_queue_and_stops_after_reply(scenario, monkeypatch):
    p = scenario
    install(p, monkeypatch)
    control, _ = await segment_cases.resumed(p, monkeypatch)
    clocks = p.driver.conversation_clocks
    assert type(clocks) is ExecutionClocks
    current = await clocks.current(p.actor, p.run["id"])
    waiting = await p.runs.store.get(
        p.actor, "run.execution_clocks", p.run["id"], revision=current.revision - 1
    )
    assert waiting.payload["mode"] == "waiting_for_user"
    assert current.active_elapsed_ms == waiting.payload["active_elapsed_ms"]
    elapsed_wait = p.future - datetime.fromisoformat(waiting.payload["captured_at"])
    assert current.wait_elapsed_ms == (
        (elapsed_wait.days * 86400 + elapsed_wait.seconds) * 1000
        + elapsed_wait.microseconds // 1000
    )
    expected = p.future + timedelta(
        milliseconds=current.active_limit_ms - current.active_elapsed_ms
    )
    assert datetime.fromisoformat(p.ctx.deadline) == expected
    p.future += timedelta(milliseconds=1234)
    p.queue = RunJobs(p.runs.store, p.actor, advance=p.driver.advance, finalize=p.driver.finalize)
    await segment_cases.finish(p)
    final = await clocks.current(p.actor, p.run["id"])
    assert final.mode == "stopped"
    assert final.active_elapsed_ms == current.active_elapsed_ms + 1234
    assert final.wait_elapsed_ms == current.wait_elapsed_ms
    assert final.active_limit_ms == current.active_limit_ms
    assert (await control.lookup(p.actor, p.run["id"], "answer-1")).patch.state == "applied"
    assert (await p.runs.get_run(p.actor, p.run["id"]))["budget"] == p.before_run["budget"]
    assert len(p.case.requests) == 2


async def test_real_clock_two_waits_preserve_limit_and_do_not_resend_original_calls(
    scenario, monkeypatch
):
    p = scenario
    install(p, monkeypatch)
    control, _ = await segment_cases.resumed(p, monkeypatch)
    first = await p.driver.conversation_clocks.current(p.actor, p.run["id"])
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "ask",
                "question": {
                    "text": "Which audience?",
                    "reason": "Choose the audience.",
                    "options": [],
                },
            }
        )
    ]
    assert await p.queue.tick()
    view = await control.view(p.actor, p.run["id"])
    assert view.question is not None and view.input_revision == 2
    await control.answer(p.actor, answer(view, "For beginners"), control_meta(view, "answer-two"))
    p.future += timedelta(minutes=30)
    assert await p.driver.resume_conversation(p.actor, p.run["id"])
    second = await p.driver.conversation_clocks.current(p.actor, p.run["id"])
    assert second.active_limit_ms == first.active_limit_ms
    assert second.active_elapsed_ms == first.active_elapsed_ms
    assert second.wait_elapsed_ms == first.wait_elapsed_ms + 1800000
    assert len(await inventory(p, "model.invocations")) == 2
    assert len(p.case.requests) == 2
    await segment_cases.finish(p)
    assert (await control.lookup(p.actor, p.run["id"], "answer-two")).patch.state == "applied"
    assert len(p.case.requests) == 3
    segment = await p.runs.store.get(p.actor, "run.active_segments", p.run["id"])
    assert segment.revision == 2
    assert (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload["state"] == "finished"


async def test_real_clock_change_rolls_back_with_failed_segment_and_retries_original_input(
    scenario, monkeypatch
):
    p = scenario
    install(p, monkeypatch)
    await segment_cases.waiting(p, monkeypatch)
    before = await snapshot(p)
    mint = p.segments.mint

    async def interrupted(*args):
        await mint(*args)
        raise RuntimeError("Owning wake interrupted after clock and segment")

    monkeypatch.setattr(p.segments, "mint", interrupted)
    with pytest.raises(RuntimeError):
        await p.driver.resume_conversation(p.actor, p.run["id"])
    assert await snapshot(p) == before
    monkeypatch.setattr(p.segments, "mint", mint)
    assert await p.driver.resume_conversation(p.actor, p.run["id"])
    clock = await p.driver.conversation_clocks.current(p.actor, p.run["id"])
    assert clock.mode == "active" and len(p.case.requests) == 1
