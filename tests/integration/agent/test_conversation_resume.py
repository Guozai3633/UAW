"""Real A queue/SQL/model fixtures with an explicitly controlled clock seam.

The clock below tests port consumption/rollback only, not D's time accounting.
No production clock, long-wait budget, live LLM or new service is claimed here.
"""

import asyncio
import json

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
from tests.integration.test_control_plane import meta
from uaw.infrastructure.db.transactions import reference, timestamp
from uaw.run.conversation_applications import APPLICATIONS
from uaw.run.jobs import JOBS, RunJobs
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.conversation import RunCorrectionRequest, RunExecutionClock
from uaw.shared.errors import DomainError
from uaw.shared.stores import StoreConflict

pytestmark = pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)


class ControlledClockSeam:
    """Write deterministic field transitions; deliberately no time calculation."""

    def __init__(self, records):
        self.records = records
        self.changes = []
        self.fail = False

    async def current(self, actor, run_id):
        row = await self.records.get(actor, "run.execution_clocks", run_id)
        return RunExecutionClock.model_validate_json(json.dumps(row.payload))

    async def change(self, tx, actor, run_id, request):
        row = await tx.load("run.execution_clocks", run_id)
        binding = await tx.load("run.protocol_bindings", run_id)
        run = await tx.load("runs", run_id)
        assert request.expected_clock_revision == row.revision
        assert binding.payload["clock_ref"] == reference("checkpoint", run_id, row.revision)
        assert (
            run.payload["status"]
            == {
                "active": "preparing",
                "waiting_for_user": "waiting_for_user",
                "stopped": "completed",
            }[request.mode]
        )
        revision = row.revision + 1
        data = {
            **row.payload,
            "revision": revision,
            "mode": request.mode,
            "captured_at": timestamp(),
        }
        for key in ("active_since", "waiting_since", "waiting_item_ref"):
            data.pop(key, None)
        if request.mode == "active":
            data["active_since"] = data["captured_at"]
        elif request.mode == "waiting_for_user":
            data["waiting_since"] = data["captured_at"]
            data["waiting_item_ref"] = request.waiting_item_ref.wire()
        await tx.write("run.execution_clocks", run_id, "RunExecutionClock", data, revision - 1)
        await tx.write(
            "run.protocol_bindings",
            run_id,
            "ConversationProtocolBinding",
            {
                **binding.payload,
                "revision": binding.revision + 1,
                "clock_ref": reference("checkpoint", run_id, revision),
            },
            binding.revision,
        )
        self.changes.append(request)
        if self.fail:
            raise RuntimeError("injected clock consumer failure")
        return RunExecutionClock.model_validate_json(json.dumps(data))


async def accepted(p, *, clock=True):
    seam = ControlledClockSeam(p.runs.store)
    if clock:
        p.driver.conversation_clocks = seam
    control, view = await ask(p)
    receipt = await control.answer(p.actor, answer(view), control_meta(view))
    return seam, control, receipt


async def snapshot(p):
    return {
        name: await inventory(p, name)
        for name in (
            JOBS,
            "runs",
            "run.execution_clocks",
            "run.protocol_bindings",
            "run.input_patches",
            "events",
        )
    }


async def test_same_run_answer_wakes_once_fences_old_worker_and_consumes_original_input(
    scenario, monkeypatch
):
    p = scenario
    ctx = TrustedExecutionContext.model_validate_json(json.dumps(p.job["context"]))
    original_role = await p.control.tool_access._binding(ctx)
    saved = []
    save = p.queue.save

    async def capture(original, result):
        saved.append(original)
        return await save(original, result)

    monkeypatch.setattr(p.queue, "save", capture)
    seam, control, receipt = await accepted(p)
    old_working = saved[-1]
    assert sorted(
        await asyncio.gather(
            p.driver.resume_conversation(p.actor, p.run["id"]),
            p.driver.resume_conversation(p.actor, p.run["id"]),
        )
    ) == [False, True]
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert job["stage"] == "prepared" and job["fence"] > old_working["fence"]
    assert job["context"] == p.job["context"] and "step_context" not in job
    with pytest.raises(StoreConflict):
        await save(old_working, {**old_working, "state": "queued"})
    assert (await control.lookup(p.actor, p.run["id"], "answer-1")).patch.state == "accepted"
    p.case.responses[:] = [
        output(
            {"protocol": "conversation-v1", "action": "reply", "text": "Result after your answer."}
        )
    ]
    # Restore a fresh queue instance on the persisted stage, without a new Run/attempt.
    restarted = RunJobs(p.runs.store, p.actor, advance=p.driver.advance, finalize=p.driver.finalize)
    for _ in range(4):
        assert await restarted.tick()
        actual = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
        assert actual["state"] != "blocked", (actual["stage"], actual.get("failure"))
    latest = await control.lookup(p.actor, p.run["id"], "answer-1")
    assert latest.run["status"] == "completed" and latest.patch.state == "applied"
    assert latest.patch.input_ref == receipt.patch.input_ref
    assert len(p.case.requests) == 2 and len(await inventory(p, APPLICATIONS)) == 1
    operations = await inventory(p, "agent.loop.operations")
    assert sorted(v["step"] for v in operations) == [1, 2]
    assert len({v["context"]["attempt_id"] for v in operations}) == 2
    assert [v.mode for v in seam.changes] == ["waiting_for_user", "active", "stopped"]
    assert await p.control.tool_access._binding(ctx) == original_role
    assert not await inventory(p, "workspace.artifacts")
    assert not await restarted.tick()


async def test_missing_clock_is_explicit_and_does_not_wake_or_change_accepted_input(scenario):
    p = scenario
    await accepted(p, clock=False)
    before = await snapshot(p)
    with pytest.raises(DomainError) as unavailable:
        await p.driver.resume_conversation(p.actor, p.run["id"])
    assert unavailable.value.status_code == 503
    assert await snapshot(p) == before and len(p.case.requests) == 1
    clock = (await p.runs.store.get(p.actor, "run.execution_clocks", p.run["id"])).payload
    binding = (await p.runs.store.get(p.actor, "run.protocol_bindings", p.run["id"])).payload
    assert binding["clock_ref"] == reference("checkpoint", p.run["id"], clock["revision"])


async def test_unknown_original_model_never_wakes_or_resends(scenario):
    p = scenario
    seam, _, _ = await accepted(p)
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
        request_id="fixture-unresolved",
    )
    before = await snapshot(p)
    with pytest.raises(DomainError) as unresolved:
        await p.driver.resume_conversation(p.actor, p.run["id"])
    assert unresolved.value.failure.code == "conversation_effect_pending"
    assert await snapshot(p) == before and len(p.case.requests) == 1
    assert len(seam.changes) == 1


async def test_clock_write_failure_rolls_back_run_binding_job_and_retry_uses_same_input(scenario):
    p = scenario
    seam, control, receipt = await accepted(p)
    seam.fail = True
    before = await snapshot(p)
    with pytest.raises(RuntimeError):
        await p.driver.resume_conversation(p.actor, p.run["id"])
    assert await snapshot(p) == before
    seam.fail = False
    assert await p.driver.resume_conversation(p.actor, p.run["id"])
    latest = await control.lookup(p.actor, p.run["id"], "answer-1")
    assert latest.patch.input_ref == receipt.patch.input_ref and latest.patch.state == "accepted"
    assert len(p.case.requests) == 1


async def test_capacity_failure_rolls_back_clock_and_run(scenario):
    p = scenario
    await accepted(p)
    p.queue.capacity = 1
    sibling = await p.runs.create_conversation(
        p.actor,
        {
            "title": "Other queued work",
            "model_choice": {"mode": "explicit", "model_id": "fixture-model"},
            "memory_policy": {
                "revision": 0,
                "read_enabled": False,
                "contribute_enabled": False,
                "scope": {"resource_refs": []},
            },
        },
        meta("sibling-create"),
    )

    async def enqueue(tx, run):
        await p.queue.enqueue(tx, run, p.actor)

    await p.runs.submit(
        p.actor,
        {"conversation_id": sibling["id"], "text": "Other work", "attachment_refs": []},
        meta("sibling-submit"),
        on_admitted=enqueue,
    )
    before = await snapshot(p)
    with pytest.raises(DomainError) as full:
        await p.driver.resume_conversation(p.actor, p.run["id"])
    assert full.value.failure.code == "run_queue_full"
    assert await snapshot(p) == before and len(p.case.requests) == 1


async def test_auth_revoked_while_clock_awaited_rolls_back_before_wake(scenario, monkeypatch):
    from pydantic import SecretStr

    p = scenario
    seam, _, _ = await accepted(p)
    change = seam.change

    async def revoked(tx, actor, run_id, request):
        result = await change(tx, actor, run_id, request)
        p.control.settings = p.control.settings.model_copy(
            update={"development_user_token": SecretStr("v" * 40)}
        )
        return result

    monkeypatch.setattr(seam, "change", revoked)
    before = await snapshot(p)
    with pytest.raises(DomainError) as denied:
        await p.driver.resume_conversation(p.actor, p.run["id"])
    assert denied.value.status_code == 401
    assert await snapshot(p) == before and len(p.case.requests) == 1


async def test_correction_during_model_discards_only_settled_old_operation_and_continues(
    scenario, monkeypatch
):
    from uaw.run.conversation_control import ConversationControls

    p = scenario
    p.driver.conversation_clocks = ControlledClockSeam(p.runs.store)
    control = ConversationControls(p.runs.store)
    models = p.driver.agent.runtime.loop.models
    generate = models.generate
    p.case.responses[:] = [
        output({"protocol": "conversation-v1", "action": "reply", "text": "Old answer"})
    ]

    async def corrected(request, ctx):
        result = await generate(request, ctx)
        view = await control.view(p.actor, p.run["id"])
        await control.correct(
            p.actor,
            RunCorrectionRequest(
                run_id=p.run["id"],
                expected_input_revision=view.input_revision,
                text="Please use my new audience.",
                attachment_refs=(),
            ),
            control_meta(view, "correction-1"),
        )
        return result

    monkeypatch.setattr(models, "generate", corrected)
    assert await p.queue.tick()
    monkeypatch.setattr(models, "generate", generate)
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "running"
    assert await p.driver.resume_conversation(p.actor, p.run["id"])
    p.case.responses[:] = [
        output({"protocol": "conversation-v1", "action": "reply", "text": "New answer"})
    ]
    for _ in range(4):
        assert await p.queue.tick()
        actual = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
        assert actual["state"] != "blocked", (actual["stage"], actual.get("failure"))
    latest = await control.lookup(p.actor, p.run["id"], "correction-1")
    assert latest.run["status"] == "completed" and latest.patch.state == "applied"
    ops = sorted(await inventory(p, "agent.loop.operations"), key=lambda v: v["step"])
    assert [v["phase"] for v in ops] == ["failed", "finished"]
    assert ops[0]["result"]["failure"]["code"] == "agent_task_changed"
    replies = await inventory(p, "run.conversation.replies")
    assert len(replies) == 1 and replies[0]["item"]["text"] == "New answer"
    assert len(p.case.requests) == 2 and len(await inventory(p, "model.invocations")) == 2


@pytest.mark.parametrize("reason", ["foreign_session", "cancel"])
async def test_new_session_or_cancel_does_not_revive_original_job(scenario, reason):
    p = scenario
    await accepted(p)
    actor = p.actor
    if reason == "cancel":
        run = await p.runs.get_run(actor, p.run["id"])
        await p.runs.control(
            actor,
            {
                "run_id": p.run["id"],
                "control": {
                    "mode": "cancel",
                    "preserve_refs": [],
                    "reason": "Stop waiting task",
                },
            },
            meta("stop-before-wake", run["revision"]),
        )
    else:
        actor = actor.model_copy(update={"auth_session_id": "different-real-session"})
    before = await snapshot(p)
    with pytest.raises(DomainError):
        await p.driver.resume_conversation(actor, p.run["id"])
    assert await snapshot(p) == before and len(p.case.requests) == 1


async def test_wait_does_not_renew_expired_original_deadline(scenario, monkeypatch):
    from datetime import datetime, timedelta

    from uaw.run import background

    p = scenario
    seam, _, _ = await accepted(p)
    current = await p.runs.get_run(p.actor, p.run["id"])
    expired_now = datetime.fromisoformat(current["budget"]["deadline"]) + timedelta(seconds=1)

    class Expired(datetime):
        @classmethod
        def now(cls, tz=None):
            return expired_now

    monkeypatch.setattr(background, "datetime", Expired)
    before = await snapshot(p)
    with pytest.raises(DomainError) as late:
        await p.driver.resume_conversation(p.actor, p.run["id"])
    assert late.value.failure.code == "background_deadline_expired"
    assert await snapshot(p) == before and len(seam.changes) == 1
    assert len(p.case.requests) == 1


@pytest.mark.parametrize("fault", ["expanded_limit", "uncommitted_return"])
async def test_clock_consumer_rejects_different_owning_result_atomically(
    scenario, monkeypatch, fault
):
    p = scenario
    seam, _, _ = await accepted(p)
    change = seam.change

    async def mismatched(tx, actor, run_id, request):
        result = await change(tx, actor, run_id, request)
        data = result.wire()
        data["active_limit_ms"] += 1
        if fault == "expanded_limit":
            # Simulate a component bug which updates its returned and owning row.
            row = await tx.load("run.execution_clocks", run_id)
            row.payload = data
        return RunExecutionClock.model_validate_json(json.dumps(data))

    monkeypatch.setattr(seam, "change", mismatched)
    before = await snapshot(p)
    with pytest.raises(DomainError) as rejected:
        await p.driver.resume_conversation(p.actor, p.run["id"])
    assert rejected.value.failure.code == "conversation_resume_clock_unproven"
    assert await snapshot(p) == before and len(p.case.requests) == 1
