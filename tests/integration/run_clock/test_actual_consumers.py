"""Actual A queue/Run/SQL inventory + D clocks; time and model HTTP replies controlled.

No live LLM, human answers, production service or native/Runner execution claims.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from tests.integration.agent.test_conversation_controls import answer, ask, control_meta
from tests.integration.agent.test_conversation_controls import case as case
from tests.integration.agent.test_conversation_controls import domain as domain
from tests.integration.agent.test_conversation_controls import scenario as scenario
from tests.integration.agent.test_conversation_postgres import inventory, output
from tests.integration.test_control_plane import meta
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.transactions import reference
from uaw.run import background, conversation_resume, execution_segments, jobs
from uaw.run.background import BackgroundAgent
from uaw.run.clock_ports import ClockChange
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.execution_clock import ExecutionClocks
from uaw.run.execution_segments import ExecutionSegments
from uaw.run.jobs import JOBS, RunJobs
from uaw.shared.errors import DomainError

pytestmark = pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)


async def actual_question(p):
    row = await p.runs.store.get(p.actor, "run.execution_clocks", p.run["id"])
    p.clock_time = [
        (
            datetime.fromisoformat(row.payload["captured_at"]) + timedelta(milliseconds=1000)
        ).isoformat()
    ]
    p.clock = ExecutionClocks(p.runs.store, effects=RunIdleEffects(), now=lambda: p.clock_time[0])
    p.driver.conversation_clocks = p.clock
    control, view = await ask(p)
    clock = await p.clock.current(p.actor, p.run["id"])
    assert clock.mode == "waiting_for_user" and clock.active_elapsed_ms == 1000
    return control, view


async def test_actual_a_queue_two_calls_late_answer_new_segment_and_terminal_clock(
    scenario, monkeypatch
):
    p = scenario
    control, view = await actual_question(p)
    old_job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    ledger = (await p.runs.store.get(p.actor, "budget.ledgers", p.run["id"])).payload
    original_calls = await inventory(p, "model.invocations")
    original_accounts = await inventory(p, "budget.accounting")
    old_clock = await p.clock.current(p.actor, p.run["id"])
    receipt = await control.answer(p.actor, answer(view), control_meta(view))
    future = datetime.fromisoformat(p.run["budget"]["deadline"]) + timedelta(seconds=100)
    p.clock_time[0] = future.isoformat()

    class Future(datetime):
        @classmethod
        def now(cls, tz=None):
            return future

    monkeypatch.setattr(execution_segments, "utcnow", lambda: future)
    monkeypatch.setattr(background, "datetime", Future)
    monkeypatch.setattr(jobs, "datetime", Future)
    monkeypatch.setattr(conversation_resume, "datetime", Future)
    p.driver = BackgroundAgent(
        p.control,
        conversation_clocks=p.clock,
        conversation_segments=ExecutionSegments(p.runs.store),
    )
    p.queue = await p.driver.prepare()
    assert await p.driver.resume_conversation(p.actor, p.run["id"])
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert job["context"]["deadline"] != old_job["context"]["deadline"]
    assert (await p.runs.store.get(p.actor, "budget.ledgers", p.run["id"])).payload == ledger
    assert await inventory(p, "model.invocations") == original_calls
    assert await inventory(p, "budget.accounting") == original_accounts
    resumed = await p.clock.current(p.actor, p.run["id"])
    assert (
        resumed.active_limit_ms == old_clock.active_limit_ms and resumed.active_elapsed_ms == 1000
    )
    assert resumed.wait_elapsed_ms > 100000 and resumed.revision == old_clock.revision + 1
    segments = await inventory(p, "run.active_segments")
    assert len(segments) == 1 and segments[0]["clock_ref"]["version"] == str(resumed.revision)
    assert job["fence"] > old_job["fence"]
    assert job["context"]["model_policy_ref"] == old_job["context"]["model_policy_ref"]
    p.queue = RunJobs(p.runs.store, p.actor, advance=p.driver.advance, finalize=p.driver.finalize)
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "reply",
                "text": "Answer from original clarification; controlled protocol fixture.",
            }
        )
    ]
    for _ in range(4):
        assert await p.queue.tick()
        state = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
        assert state["state"] != "blocked", state.get("failure")
    restored = await control.lookup(p.actor, p.run["id"], "answer-1")
    assert restored.patch.input_ref == receipt.patch.input_ref and restored.patch.state == "applied"
    assert restored.run["status"] == "completed" and len(p.case.requests) == 2
    stopped = await p.clock.current(p.actor, p.run["id"])
    assert stopped.mode == "stopped" and stopped.active_elapsed_ms >= 1000
    assert (await p.runs.store.get(p.actor, "budget.ledgers", p.run["id"])).payload[
        "deadline"
    ] == ledger["deadline"]
    current_calls = await inventory(p, "model.invocations")
    assert all(v in current_calls for v in original_calls)


@pytest.mark.parametrize(
    "effect",
    [
        "known_money_pending",
        "live_held",
        "model_claimed",
        "model_unknown",
        "reservation_live",
        "tool_unknown",
        "tool_confirmed",
    ],
)
async def test_real_idle_inventory_with_known_and_unresolved_model_accounting(scenario, effect):
    p = scenario
    control, view = await actual_question(p)
    row = await p.runs.store.get(p.actor, "budget.ledgers", p.run["id"])
    assert row.payload["billing_pending"]
    if effect == "live_held":
        await p.runs.store.put(
            p.actor,
            row.namespace,
            row.resource_id,
            row.schema_name,
            {
                **row.payload,
                "revision": row.revision + 1,
                "held": {**row.payload["held"], "model_calls": 1},
            },
            expected_revision=row.revision,
            request_id="d-clock-held",
        )
    elif effect == "reservation_live":
        async with p.runs.store.database.sessions() as sql:
            accounting = next(
                row
                for row in await sql.scalars(
                    select(RecordRow).where(
                        RecordRow.principal_id == p.actor.id,
                        RecordRow.namespace == "budget.accounting",
                        RecordRow.deleted.is_(False),
                    )
                )
                if row.payload["run_id"] == p.run["id"]
            )
        reservation = await p.runs.store.get(p.actor, "budget.reservations", accounting.resource_id)
        await p.runs.store.put(
            p.actor,
            reservation.namespace,
            reservation.resource_id,
            reservation.schema_name,
            {**reservation.payload, "revision": reservation.revision + 1, "status": "reserved"},
            expected_revision=reservation.revision,
            request_id="d-clock-live-reservation",
        )
    elif effect.startswith("tool_"):
        # Controlled persisted inventory rows, NOT a real Tool dispatch/effect receipt.
        key = "d-controlled-tool-inventory"
        await p.runs.store.put(
            p.actor,
            "tool.contexts",
            key,
            "TrustedExecutionContext",
            p.job["context"],
            expected_revision=0,
            request_id="d-clock-tool-context",
        )
        await p.runs.store.put(
            p.actor,
            "tool.dispatch.intents",
            key,
            "InternalToolInvocationDispatchRequest",
            {
                "validated_action_ref": reference("tool_call", key),
                "reservation_ref": reference("reservation", "controlled-reservation"),
                "provider_binding_ref": reference("provider", "controlled-provider"),
            },
            expected_revision=0,
            request_id="d-clock-tool-intent",
        )
        await p.runs.store.put(
            p.actor,
            "tool.effects",
            key,
            "EffectRecord",
            {
                "action_id": key,
                "arguments_hash": "a" * 64,
                "provider_ref": reference("provider", "controlled-provider"),
                "attempt_ids": ["controlled-tool-attempt"],
                "state": "unknown" if effect == "tool_unknown" else "confirmed",
                "revision": 1,
            },
            expected_revision=0,
            request_id="d-clock-tool-effect",
        )
    elif effect.startswith("model_"):
        calls = await inventory(p, "model.invocations")
        original = next(v for v in calls if v["run_id"] == p.run["id"])
        row = await p.runs.store.get(p.actor, "model.invocations", original["id"])
        value = {**row.payload, "state": "claimed"}
        value.pop("result", None)
        if effect == "model_unknown":
            value = {
                **row.payload,
                "result": {
                    "kind": "failed",
                    "failure": {
                        "code": "unknown_clock_fixture",
                        "category": "unknown_effect",
                        "message": "unresolved",
                        "retryable": False,
                        "failed_phase": "dispatch",
                    },
                    "output_refs": [],
                },
            }
        await p.runs.store.put(
            p.actor,
            row.namespace,
            row.resource_id,
            row.schema_name,
            value,
            expected_revision=row.revision,
            request_id="d-clock-" + effect,
        )
    before = (await p.clock.current(p.actor, p.run["id"])).wire()
    p.clock_time[0] = (
        datetime.fromisoformat(p.clock_time[0]) + timedelta(milliseconds=100)
    ).isoformat()

    # Use the original stable Item, not a nested clock read in another transaction.
    from uaw.shared.contracts import Ref

    async def write(tx):
        return (
            await p.clock.change(
                tx,
                p.actor,
                p.run["id"],
                ClockChange(
                    before["revision"],
                    "waiting_for_user",
                    waiting_item_ref=Ref(
                        kind="item", id=view.question.question.item_id, version="1"
                    ),
                ),
            )
        ).wire()

    if effect in ("known_money_pending", "tool_confirmed"):
        result = await control.transactions.inspect(
            p.actor, "conversation:" + p.run["conversation_id"], write
        )
        assert result["wait_elapsed_ms"] == 100 and result["active_elapsed_ms"] == 1000
        assert (await p.runs.store.get(p.actor, "budget.ledgers", p.run["id"])).payload[
            "billing_pending"
        ]
    else:
        with pytest.raises(DomainError) as error:
            await control.transactions.inspect(
                p.actor, "conversation:" + p.run["conversation_id"], write
            )
        assert error.value.failure.code == "conversation_effect_pending"
        assert (await p.clock.current(p.actor, p.run["id"])).wire() == before
    assert len(p.case.requests) == 1


async def test_actual_cancel_stops_wait_clock_without_erasing_pending_money_or_question(scenario):
    p = scenario
    control, view = await actual_question(p)
    before = await p.clock.current(p.actor, p.run["id"])
    p.clock_time[0] = (datetime.fromisoformat(p.clock_time[0]) + timedelta(seconds=30)).isoformat()
    run = await p.runs.get_run(p.actor, p.run["id"])
    await p.runs.control(
        p.actor,
        {
            "run_id": run["id"],
            "control": {
                "mode": "cancel",
                "reason": "D controlled cancellation",
                "preserve_refs": [],
            },
        },
        meta("d-clock-stop", run["revision"]),
    )
    job = (await p.runs.store.get(p.actor, JOBS, run["id"])).payload
    await p.driver.finalize(job)
    after = await p.clock.current(p.actor, p.run["id"])
    assert after.mode == "stopped" and after.active_elapsed_ms == before.active_elapsed_ms
    assert after.wait_elapsed_ms == 30000
    assert (await p.runs.store.get(p.actor, "budget.ledgers", run["id"])).payload["billing_pending"]
    assert len(p.case.requests) == 1
    assert (
        await control.question(p.actor, run["id"], view.question.question.item_id)
    ).question.state == "cancelled"
