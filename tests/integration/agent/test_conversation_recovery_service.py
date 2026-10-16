"""Actual acceptance/queue restart SQL; controlled clock seam, no D/live quality claim."""

import asyncio

import httpx
import pytest

from tests.integration.agent.test_conversation_controls import answer, ask, control_meta
from tests.integration.agent.test_conversation_controls import (
    case as case,
)
from tests.integration.agent.test_conversation_controls import (
    domain as domain,
)
from tests.integration.agent.test_conversation_controls import (
    scenario as scenario,
)
from tests.integration.agent.test_conversation_postgres import inventory, output
from tests.integration.agent.test_conversation_resume import ControlledClockSeam
from tests.integration.test_control_plane import meta
from uaw.api.application import create_app
from uaw.infrastructure.db.transactions import RecordTransaction
from uaw.run.background import BackgroundAgent
from uaw.run.conversation_control import PATCHES
from uaw.run.conversation_recovery import FAILURES, ConversationRecovery
from uaw.run.jobs import JOBS
from uaw.shared.errors import CapabilityUnavailable, DomainError, reject

pytestmark = pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)


async def composed(p):
    # Replace this non-running fixture driver with a new, explicitly composed
    # candidate. Original production Container.start is not hot-reconfigured.
    p.driver = BackgroundAgent(p.control, conversation_clocks=ControlledClockSeam(p.runs.store))
    p.queue = await p.driver.prepare()
    p.control.background_jobs = p.queue
    p.recovery = p.control.conversation_recovery
    assert p.recovery is not None and p.queue.recover is not None


async def prepared(p):
    await composed(p)
    control, view = await ask(p)
    return control, view


async def accepted(p):
    control, view = await prepared(p)
    receipt = await control.answer(p.actor, answer(view), control_meta(view))
    return control, view, receipt


async def finish(p):
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "reply",
                "text": "Completed using your original answer.",
            }
        )
    ]
    for _ in range(4):
        assert await p.queue.tick()
        job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
        assert job["state"] != "blocked", job.get("failure")
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "completed"


async def test_http_acceptance_only_signals_then_background_recovers_and_replay_reads_current(
    scenario,
):
    p = scenario
    _, view = await prepared(p)
    app = create_app(p.control)
    headers = {
        "Authorization": "Bearer " + p.control.settings.development_user_token.get_secret_value()
    }
    target = f"/v1/runs/{p.run['id']}/clarifications/{view.question.question.item_id}/answers"
    payload = answer(view).wire()
    payload.pop("run_id")
    payload.pop("question_item_id")
    body = {"meta": control_meta(view).wire(), "payload": payload}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8000"
    ) as client:
        first = await client.post(target, headers=headers, json=body)
        assert first.status_code == 200 and first.json()["payload"]["patch"]["state"] == "accepted"
        assert len(p.case.requests) == 1
        assert (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload["state"] == "blocked"
        assert await p.queue.tick()  # Scan/wake only; no model call here.
        assert len(p.case.requests) == 1
        await finish(p)
        repeated = await client.post(target, headers=headers, json=body)
        assert (
            repeated.status_code == 200
            and repeated.json()["payload"]["patch"]["state"] == "applied"
        )
        assert repeated.json()["payload"]["run"]["id"] == p.run["id"]
        assert len(await inventory(p, PATCHES)) == 1 and len(p.case.requests) == 2


async def test_crash_after_acceptance_before_signal_reconstructed_service_finds_original_input(
    scenario,
):
    p = scenario
    control, _, receipt = await accepted(p)
    restarted = ConversationRecovery(
        p.runs.store, owner_id=p.actor.id, resume=p.driver.resume_conversation
    )
    p.queue.recover = restarted.scan
    assert await p.queue.tick()
    assert len(p.case.requests) == 1
    await finish(p)
    latest = await control.lookup(p.actor, p.run["id"], "answer-1")
    assert latest.patch.input_ref == receipt.patch.input_ref and latest.patch.state == "applied"
    assert len(p.case.requests) == 2


async def test_unavailable_source_backoff_and_feedback_are_durable_without_resending(scenario):
    p = scenario
    control, _, _ = await accepted(p)
    calls = []
    now = [0.0]

    async def unavailable(actor, run_id):
        calls.append((actor.wire(), run_id))
        raise CapabilityUnavailable("actual.production.clock")

    recovery = ConversationRecovery(
        p.runs.store, owner_id=p.actor.id, resume=unavailable, now=lambda: now[0]
    )
    assert not await recovery.scan()
    assert not await recovery.scan()
    assert not await recovery.notify(p.actor, p.run["id"])
    assert len(calls) == 1
    notices = [v for v in await inventory(p, "items") if v["type"] == "user_control"]
    assert len(notices) == 1 and "执行组件暂不可用" in notices[0]["text"]
    seq = len(await inventory(p, "events"))
    now[0] = 3
    assert not await recovery.scan()
    assert len(calls) == 2 and len(await inventory(p, "events")) == seq
    assert len(await inventory(p, FAILURES)) == 1
    recovery.resume = p.driver.resume_conversation
    now[0] = 8
    assert await recovery.scan()
    notices = [v for v in await inventory(p, "items") if v["type"] == "user_control"]
    assert len(notices) == 1 and notices[0]["status"] == "completed" and notices[0]["revision"] == 2
    assert (await control.lookup(p.actor, p.run["id"], "answer-1")).patch.state == "accepted"
    assert len(p.case.requests) == 1


async def test_foreign_session_cannot_write_recovery_feedback(scenario):
    p = scenario
    await accepted(p)
    before = await inventory(p, "items")
    with pytest.raises(DomainError) as denied:
        await p.recovery.notify(
            p.actor.model_copy(update={"auth_session_id": "other"}), p.run["id"]
        )
    assert denied.value.status_code == 403
    assert await inventory(p, "items") == before and len(p.case.requests) == 1


async def test_concurrent_notifications_only_execute_one_original_resume(scenario):
    p = scenario
    await accepted(p)
    assert sorted(
        await asyncio.gather(*(p.recovery.notify(p.actor, p.run["id"]) for _ in range(8)))
    ) == [False] * 7 + [True]
    assert len(p.case.requests) == 1
    await finish(p)
    assert len(p.case.requests) == 2


async def test_notice_storage_failure_retains_patch_and_recovery_restarts_from_database(
    scenario, monkeypatch
):
    p = scenario
    control, _, receipt = await accepted(p)

    async def unavailable(actor, run_id):
        raise reject("conversation_effect_pending", "Original model unresolved", 409)

    recovery = ConversationRecovery(p.runs.store, owner_id=p.actor.id, resume=unavailable)
    write = RecordTransaction.write

    async def broken(self, namespace, resource_id, schema, payload, expected=0):
        if namespace == "items" and payload.get("type") == "user_control":
            raise RuntimeError("injected notice storage failure")
        return await write(self, namespace, resource_id, schema, payload, expected)

    monkeypatch.setattr(RecordTransaction, "write", broken)
    assert not await recovery.notify(p.actor, p.run["id"])
    assert not await inventory(p, FAILURES)  # notice and raw failure rolled back together
    assert not [v for v in await inventory(p, "items") if v["id"].startswith("recovery-notice-")]
    monkeypatch.setattr(RecordTransaction, "write", write)
    assert await p.recovery.scan()
    assert (
        await control.lookup(p.actor, p.run["id"], "answer-1")
    ).patch.input_ref == receipt.patch.input_ref
    assert len(p.case.requests) == 1


async def test_cancelled_patch_is_not_selected_on_restart(scenario):
    p = scenario
    await accepted(p)
    run = await p.runs.get_run(p.actor, p.run["id"])
    await p.runs.control(
        p.actor,
        {
            "run_id": p.run["id"],
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop before restart"},
        },
        meta("cancel-before-recovery", run["revision"]),
    )
    assert not await p.recovery.scan()
    assert len(p.case.requests) == 1
    assert not [v for v in await inventory(p, "items") if v["id"].startswith("recovery-notice-")]


async def test_scan_cursor_does_not_starve_next_blocked_task(scenario):
    p = scenario
    await accepted(p)
    job = await p.runs.store.get(p.actor, JOBS, p.run["id"])

    async def enqueue(tx, run):
        await p.queue.enqueue(tx, run, p.actor)

    sibling = await p.runs.submit(
        p.actor,
        {
            "conversation_id": p.run["conversation_id"],
            "text": "Other question",
            "attachment_refs": [],
        },
        meta("sibling-recovery"),
        on_admitted=enqueue,
    )
    # Create a second original task in the SAME actual queue and runtime.
    for _ in range(4):
        assert await p.queue.tick()
    sibling_job = (await p.runs.store.get(p.actor, JOBS, sibling["id"])).payload
    original_run, original_job = p.run, p.job
    p.run, p.job = sibling, sibling_job

    control, view = await ask(p)
    await control.answer(p.actor, answer(view), control_meta(view, "sibling-answer"))
    p.run, p.job = original_run, original_job
    # A bounded scanner visits one blocked Run per tick; failures cannot pin its cursor.
    seen = []
    now = [0.0]

    async def unavailable(actor, run_id):
        seen.append(run_id)
        raise CapabilityUnavailable("clock")

    recovery = ConversationRecovery(
        p.runs.store, owner_id=p.actor.id, resume=unavailable, batch_size=1, now=lambda: now[0]
    )
    assert not await recovery.scan()
    now[0] = 3
    assert not await recovery.scan()
    assert set(seen) == {original_run["id"], sibling["id"]}
    assert (await p.runs.store.get(p.actor, JOBS, original_run["id"])).payload == job.payload


@pytest.mark.parametrize("unresolved", [False, True])
async def test_cancellation_stops_clock_only_after_original_effects_settle(scenario, unresolved):
    p = scenario
    await accepted(p)
    if unresolved:
        original = next(
            v for v in await inventory(p, "model.invocations") if v["run_id"] == p.run["id"]
        )
        row = await p.runs.store.get(p.actor, "model.invocations", original["id"])
        await p.runs.store.put(
            p.actor,
            row.namespace,
            row.resource_id,
            row.schema_name,
            {**row.payload, "state": "claimed"},
            expected_revision=row.revision,
            request_id="unknown-before-stop",
        )
    run = await p.runs.get_run(p.actor, p.run["id"])
    await p.runs.control(
        p.actor,
        {
            "run_id": p.run["id"],
            "control": {
                "mode": "cancel",
                "preserve_refs": [],
                "reason": "Stop actual original task",
            },
        },
        meta("stop-with-clock", run["revision"]),
    )
    assert not await p.queue.tick()
    clock = (await p.runs.store.get(p.actor, "run.execution_clocks", p.run["id"])).payload
    current = await p.runs.get_run(p.actor, p.run["id"])
    assert current["status"] == ("waiting_for_user" if unresolved else "cancelled")
    assert clock["mode"] == ("waiting_for_user" if unresolved else "stopped")
    assert len(p.case.requests) == 1


async def test_clock_failure_rolls_back_cancel_terminal_commit_and_restart_retries_original(
    scenario,
):
    p = scenario
    await accepted(p)
    run = await p.runs.get_run(p.actor, p.run["id"])
    await p.runs.control(
        p.actor,
        {
            "run_id": p.run["id"],
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "Cancellation requested"},
        },
        meta("cancel-atomic-clock", run["revision"]),
    )
    from tests.integration.agent.test_conversation_resume import snapshot

    before = await snapshot(p)
    p.driver.conversation_clocks.fail = True
    with pytest.raises(RuntimeError):
        await p.queue.tick()
    assert await snapshot(p) == before
    p.driver.conversation_clocks.fail = False
    assert not await p.queue.tick()
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "cancelled"
    assert (await p.runs.store.get(p.actor, "run.execution_clocks", p.run["id"])).payload[
        "mode"
    ] == "stopped"
    assert len(p.case.requests) == 1


async def test_formal_artifact_stops_injected_clock_only_after_actual_user_acceptance(scenario):
    from tests.integration.agent.test_conversation_postgres import (
        test_deliver_keeps_artifact_verification_and_user_acceptance as deliver,
    )

    p = scenario
    await composed(p)
    await deliver(p)
    assert (await p.runs.store.get(p.actor, "run.execution_clocks", p.run["id"])).payload[
        "mode"
    ] == "stopped"
    assert len(await inventory(p, "run.completion.acceptance")) == 1
    assert [v.mode for v in p.driver.conversation_clocks.changes] == ["stopped"]


async def test_signal_failure_after_http_commit_does_not_turn_acceptance_into_error(
    scenario, monkeypatch
):
    p = scenario
    control, view = await prepared(p)

    def broken(actor, run_id):
        raise RuntimeError("injected post-acceptance signal failure")

    monkeypatch.setattr(p.recovery, "signal", broken)
    payload = answer(view).wire()
    payload.pop("run_id")
    payload.pop("question_item_id")
    target = f"/v1/runs/{p.run['id']}/clarifications/{view.question.question.item_id}/answers"
    headers = {
        "Authorization": "Bearer " + p.control.settings.development_user_token.get_secret_value()
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(p.control)), base_url="http://127.0.0.1:8000"
    ) as client:
        response = await client.post(
            target, headers=headers, json={"meta": control_meta(view).wire(), "payload": payload}
        )
        assert (
            response.status_code == 200
            and response.json()["payload"]["patch"]["state"] == "accepted"
        )
    assert len(await inventory(p, PATCHES)) == 1 and len(p.case.requests) == 1
    assert await p.queue.tick()  # durable scan recovers even without the lost signal
    assert (await control.lookup(p.actor, p.run["id"], "answer-1")).patch.state == "accepted"


async def test_unknown_response_keeps_actual_failure_but_never_dispatches_again(scenario):
    p = scenario
    await accepted(p)
    original = next(
        v for v in await inventory(p, "model.invocations") if v["run_id"] == p.run["id"]
    )
    row = await p.runs.store.get(p.actor, "model.invocations", original["id"])
    await p.runs.store.put(
        p.actor,
        row.namespace,
        row.resource_id,
        row.schema_name,
        {**row.payload, "state": "claimed"},
        expected_revision=row.revision,
        request_id="unknown-recovery-source",
    )
    assert not await p.recovery.scan()
    failures = await inventory(p, FAILURES)
    assert len(failures) == 1 and failures[0]["code"] == "conversation_effect_pending"
    notice = next(v for v in await inventory(p, "items") if v["id"].startswith("recovery-notice-"))
    assert "核对上一次调用" in notice["text"] and "不会重复执行" in notice["text"]
    assert (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload["state"] == "blocked"
    assert len(p.case.requests) == 1


async def test_cancel_terminal_commit_closes_waiting_recovery_notice_without_false_applied(
    scenario,
):
    p = scenario
    control, _, _ = await accepted(p)
    original_resume = p.recovery.resume

    async def unavailable(actor, run_id):
        raise CapabilityUnavailable("actual_clock")

    p.recovery.resume = unavailable
    assert not await p.recovery.notify(p.actor, p.run["id"])
    p.recovery.resume = original_resume
    run = await p.runs.get_run(p.actor, p.run["id"])
    await p.runs.control(
        p.actor,
        {
            "run_id": p.run["id"],
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop without resuming"},
        },
        meta("stop-with-notice", run["revision"]),
    )
    assert not await p.queue.tick()
    notices = [v for v in await inventory(p, "items") if v["id"].startswith("recovery-notice-")]
    assert len(notices) == 1 and notices[0]["status"] == "cancelled"
    assert "已停止" in notices[0]["text"] and notices[0]["revision"] == 2
    assert (await control.lookup(p.actor, p.run["id"], "answer-1")).patch.state == "cancelled"
    assert len(p.case.requests) == 1


async def test_current_model_failure_closes_injected_clock_without_marking_patch_applied(scenario):
    p = scenario
    control, _, _ = await accepted(p)
    assert await p.queue.tick()
    p.case.responses[:] = [output({"protocol": "conversation-v1", "action": "reply"})]
    for _ in range(4):
        assert await p.queue.tick()
    latest = await control.lookup(p.actor, p.run["id"], "answer-1")
    assert latest.run["status"] == "failed" and latest.patch.state == "accepted"
    assert (await p.runs.store.get(p.actor, "run.execution_clocks", p.run["id"])).payload[
        "mode"
    ] == "stopped"
    assert len(p.case.requests) == 2
