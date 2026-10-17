"""A actual SQL/model composition, controlled service time and clock seam.

This verifies A's new execution source, not D accounting or real elapsed waits.
"""

import asyncio
import json
from datetime import datetime, timedelta

import pytest

from tests.integration.agent.test_conversation_controls import answer, ask, control_meta
from tests.integration.agent.test_conversation_controls import case as case
from tests.integration.agent.test_conversation_controls import domain as domain
from tests.integration.agent.test_conversation_controls import scenario as scenario
from tests.integration.agent.test_conversation_postgres import inventory, output
from tests.integration.agent.test_conversation_resume import ControlledClockSeam
from tests.integration.test_control_plane import meta
from uaw.run import background, conversation_resume, execution_segments, jobs
from uaw.run.background import BackgroundAgent
from uaw.run.execution_segments import SEGMENTS, ExecutionSegments
from uaw.run.jobs import JOBS, RunJobs
from uaw.run.leases import ExecutionLeaseService
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.shared.errors import DomainError

pytestmark = pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)


async def waiting(p, monkeypatch):
    p.segments = ExecutionSegments(p.runs.store)
    p.driver = BackgroundAgent(
        p.control,
        conversation_clocks=ControlledClockSeam(p.runs.store),
        conversation_segments=p.segments,
    )
    p.queue = await p.driver.prepare()
    control, view = await ask(p)
    receipt = await control.answer(p.actor, answer(view), control_meta(view))
    p.original_job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    p.before_run = await p.runs.get_run(p.actor, p.run["id"])
    p.before_ledger = (await p.runs.store.get(p.actor, "budget.ledgers", p.run["id"])).payload
    p.before_accounts = await inventory(p, "budget.accounting")
    p.before_invocations = await inventory(p, "model.invocations")
    p.future = datetime.fromisoformat(p.before_run["budget"]["deadline"]) + timedelta(seconds=100)

    class Future(datetime):
        @classmethod
        def now(cls, tz=None):
            return p.future

    monkeypatch.setattr(execution_segments, "utcnow", lambda: p.future)
    monkeypatch.setattr(background, "datetime", Future)
    monkeypatch.setattr(conversation_resume, "datetime", Future)
    monkeypatch.setattr(jobs, "datetime", Future)
    monkeypatch.setattr(
        "tests.integration.agent.test_conversation_resume.timestamp", lambda: p.future.isoformat()
    )
    return control, receipt


async def resumed(p, monkeypatch):
    control, receipt = await waiting(p, monkeypatch)
    assert await p.driver.resume_conversation(p.actor, p.run["id"])
    p.job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    p.ctx = TrustedExecutionContext.model_validate_json(json.dumps(p.job["context"]))
    return control, receipt


async def finish(p):
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "reply",
                "text": "Answer using the original clarification.",
            }
        )
    ]
    for _ in range(4):
        assert await p.queue.tick()
        job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
        assert job["state"] != "blocked", job.get("failure")


async def test_late_answer_mints_only_new_context_and_completes_original_run_after_restart(
    scenario, monkeypatch
):
    p = scenario
    control, receipt = await resumed(p, monkeypatch)
    assert p.ctx.deadline != p.original_job["context"]["deadline"]
    assert datetime.fromisoformat(p.ctx.deadline) > p.future
    assert (await p.runs.get_run(p.actor, p.run["id"]))["budget"] == p.before_run["budget"]
    assert (
        await p.runs.store.get(p.actor, "budget.ledgers", p.run["id"])
    ).payload == p.before_ledger
    assert await inventory(p, "model.invocations") == p.before_invocations
    assert await inventory(p, "budget.accounting") == p.before_accounts
    original = TrustedExecutionContext.model_validate_json(json.dumps(p.original_job["context"]))
    with pytest.raises(DomainError) as stale:
        await p.control.execution_permissions.resolve(original)
    assert stale.value.failure.code == "execution_deadline_expired"
    p.queue = RunJobs(p.runs.store, p.actor, advance=p.driver.advance, finalize=p.driver.finalize)
    await finish(p)
    latest = await control.lookup(p.actor, p.run["id"], "answer-1")
    assert latest.patch.input_ref == receipt.patch.input_ref and latest.patch.state == "applied"
    assert latest.run["status"] == "completed" and len(p.case.requests) == 2
    accounts = await inventory(p, "budget.accounting")
    invocations = await inventory(p, "model.invocations")
    assert all(v in accounts for v in p.before_accounts)
    assert all(v in invocations for v in p.before_invocations)
    assert (await p.runs.store.get(p.actor, "budget.ledgers", p.run["id"])).payload[
        "deadline"
    ] == p.before_ledger["deadline"]
    assert len(await inventory(p, SEGMENTS)) == 1


async def test_segment_mint_failure_rolls_back_clock_job_run_and_events(scenario, monkeypatch):
    from tests.integration.agent.test_conversation_resume import snapshot

    p = scenario
    await waiting(p, monkeypatch)
    before = await snapshot(p)
    original = p.segments.mint

    async def failed(*args):
        await original(*args)
        raise RuntimeError("injected segment write rollback")

    monkeypatch.setattr(p.segments, "mint", failed)
    with pytest.raises(RuntimeError):
        await p.driver.resume_conversation(p.actor, p.run["id"])
    assert await snapshot(p) == before and not await inventory(p, SEGMENTS)
    monkeypatch.setattr(p.segments, "mint", original)
    assert await p.driver.resume_conversation(p.actor, p.run["id"])
    assert len(await inventory(p, SEGMENTS)) == 1 and len(p.case.requests) == 1


@pytest.mark.parametrize("fault", ["context", "clock_pin", "clock_hash", "budget", "clock_stopped"])
async def test_changed_segment_sources_never_authorize_a_new_call(scenario, monkeypatch, fault):
    p = scenario
    await resumed(p, monkeypatch)
    ctx = p.ctx
    if fault == "context":
        ctx = ctx.model_copy(
            update={
                "deadline": (
                    datetime.fromisoformat(ctx.deadline) + timedelta(seconds=1)
                ).isoformat()
            }
        )
    else:
        namespace = {
            "clock_pin": "run.protocol_bindings",
            "clock_hash": SEGMENTS,
            "budget": "runs",
            "clock_stopped": "run.execution_clocks",
        }[fault]
        row = await p.runs.store.get(p.actor, namespace, p.run["id"])
        value = {**row.payload, "revision": row.revision + 1}
        if fault == "clock_pin":
            value["clock_ref"] = {**value["clock_ref"], "version": "99"}
        elif fault == "clock_hash":
            value["clock_ref"] = {**value["clock_ref"], "content_hash": "0" * 64}
        elif fault == "budget":
            value["budget"] = {**value["budget"], "max_steps": value["budget"]["max_steps"] - 1}
        else:
            value["mode"] = "stopped"
            value.pop("active_since")
        await p.runs.store.put(
            p.actor,
            namespace,
            row.resource_id,
            row.schema_name,
            value,
            expected_revision=row.revision,
            request_id="alter-active-source",
        )
    with pytest.raises(DomainError):
        await p.control.execution_permissions.resolve(ctx)
    assert len(p.case.requests) == 1


async def test_missing_segment_keeps_legacy_expiry_and_metadata_inspection_does_not_grant(
    scenario, monkeypatch
):
    p = scenario
    await waiting(p, monkeypatch)
    ctx = TrustedExecutionContext.model_validate_json(json.dumps(p.original_job["context"]))
    later = ctx.model_copy(update={"deadline": (p.future + timedelta(minutes=10)).isoformat()})
    assert await p.control.execution_permissions.inspect_for_continuation(later) is None
    with pytest.raises(DomainError) as missing:
        await p.control.execution_permissions.resolve(later)
    assert missing.value.failure.code == "execution_deadline_expired"
    assert not await inventory(p, SEGMENTS) and len(p.case.requests) == 1


async def test_new_lease_uses_segment_but_expired_context_cannot_revoke_it(scenario, monkeypatch):
    p = scenario
    await resumed(p, monkeypatch)
    leases = ExecutionLeaseService(p.runs.store, clock=lambda: p.future)
    holder = Principal(id="candidate-service", kind="service", auth_session_id="candidate-session")
    lease = await leases.acquire(
        {"expected_revision": 0, "lease_ttl_ms": 1000},
        meta("new-segment-lease"),
        p.ctx,
        holder=holder,
    )
    assert datetime.fromisoformat(lease["expires_at"]) <= datetime.fromisoformat(p.ctx.deadline)
    assert lease["fencing_token"] == 1
    original = TrustedExecutionContext.model_validate_json(json.dumps(p.original_job["context"]))
    with pytest.raises(DomainError):
        await leases.current(
            Ref(kind="lease", id=lease["id"], version=str(lease["revision"])),
            lease["fencing_token"],
            original,
            holder=holder,
        )
    state = await p.runs.store.get(p.actor, "execution.leases", lease["id"])
    assert state.payload["state"] == "active" and state.payload["lease"] == lease


async def test_cancellation_and_active_exhaustion_do_not_grant_new_segment(scenario, monkeypatch):
    p = scenario
    await resumed(p, monkeypatch)
    monkeypatch.setattr(
        execution_segments,
        "utcnow",
        lambda: datetime.fromisoformat(p.ctx.deadline) + timedelta(seconds=1),
    )
    with pytest.raises(DomainError) as expired:
        await p.control.execution_permissions.resolve(p.ctx)
    assert expired.value.failure.code == "execution_deadline_expired"
    monkeypatch.setattr(execution_segments, "utcnow", lambda: p.future)
    run = await p.runs.get_run(p.actor, p.run["id"])
    await p.runs.control(
        p.actor,
        {
            "run_id": p.run["id"],
            "control": {"mode": "cancel", "reason": "Stop new segment", "preserve_refs": []},
        },
        meta("segment-cancel", run["revision"]),
    )
    with pytest.raises(DomainError) as cancelled:
        await p.control.execution_permissions.resolve(p.ctx)
    assert cancelled.value.failure.code == "execution_cancelled"
    assert len(p.case.requests) == 1


async def test_two_pages_mint_one_owning_segment_and_do_not_repeat_original_model(
    scenario, monkeypatch
):
    p = scenario
    await waiting(p, monkeypatch)
    results = await asyncio.gather(
        p.driver.resume_conversation(p.actor, p.run["id"]),
        p.driver.resume_conversation(p.actor, p.run["id"]),
    )
    assert sorted(results) == [False, True]
    segment = (await p.runs.store.get(p.actor, SEGMENTS, p.run["id"])).payload
    assert segment["revision"] == 1 and len(p.case.requests) == 1


async def test_later_clock_cannot_increase_original_admission_limit(scenario, monkeypatch):
    from tests.integration.agent.test_conversation_resume import snapshot

    p = scenario
    await waiting(p, monkeypatch)
    row = await p.runs.store.get(p.actor, "run.execution_clocks", p.run["id"])
    value = {
        **row.payload,
        "revision": row.revision + 1,
        "active_limit_ms": row.payload["active_limit_ms"] + 1,
    }
    await p.runs.store.put(
        p.actor,
        row.namespace,
        row.resource_id,
        row.schema_name,
        value,
        expected_revision=row.revision,
        request_id="alter-original-clock-limit",
    )
    binding = await p.runs.store.get(p.actor, "run.protocol_bindings", p.run["id"])
    await p.runs.store.put(
        p.actor,
        binding.namespace,
        binding.resource_id,
        binding.schema_name,
        {
            **binding.payload,
            "revision": binding.revision + 1,
            "clock_ref": {
                "kind": "checkpoint",
                "id": p.run["id"],
                "version": str(row.revision + 1),
            },
        },
        expected_revision=binding.revision,
        request_id="alter-limit-clock-pin",
    )
    before = await snapshot(p)
    with pytest.raises(DomainError) as expanded:
        await p.driver.resume_conversation(p.actor, p.run["id"])
    assert expanded.value.failure.code == "execution_segment_unproven"
    assert await snapshot(p) == before and not await inventory(p, SEGMENTS)


async def test_late_text_delivery_keeps_verification_and_independent_acceptance(
    scenario, monkeypatch
):
    from tests.integration.agent.test_completion_postgres import review
    from uaw.agent.completion.contracts import contract_from_frame
    from uaw.run.deliveries import DeliveryReader

    p = scenario
    await resumed(p, monkeypatch)
    for _ in range(3):
        assert await p.queue.tick()
    frame = (await p.runs.store.get(p.actor, "intent.frames", p.run["task_id"])).payload
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "deliver",
                "text": "Report based on the clarified original task.",
            }
        ),
        review(contract_from_frame(frame)["requirements"]),
    ]
    assert await p.queue.tick()
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert job["stage"] == "delivery", job.get("failure")
    assert len(p.case.requests) == 3  # original ask + deliver + controlled semantic review
    assert len(await inventory(p, "workspace.artifacts")) == 1
    assert len(await inventory(p, "agent.completion.reports")) == 1
    assert not await inventory(p, "run.completion.acceptance")
    assert await p.queue.tick()
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] != "completed"
    delivery, _ = await DeliveryReader(p.runs.store, p.control.blobs).read(p.actor, p.run["id"])
    await p.control.completion_controller.accept(
        p.actor,
        Ref.model_validate(delivery["bundle_ref"]),
        Ref.model_validate(delivery["artifact_ref"]),
        "accept",
        TrustedExecutionContext.model_validate_json(json.dumps(job["step_context"])),
        meta("late-report-fixture-acceptance"),
    )
    p.future += timedelta(seconds=3)  # queued poll becomes ready, still inside the same bound
    assert await p.queue.tick()
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "completed"
    assert (await p.runs.store.get(p.actor, "run.execution_clocks", p.run["id"])).payload[
        "mode"
    ] == "stopped"
    assert len(p.case.requests) == 3


async def test_expired_original_lease_is_replaced_with_new_fence_not_renewed(scenario, monkeypatch):
    p = scenario
    await resumed(p, monkeypatch)
    original = TrustedExecutionContext.model_validate_json(json.dumps(p.original_job["context"]))
    old_time = datetime.fromisoformat(original.deadline) - timedelta(seconds=10)
    holder = Principal(
        id="segment-worker", kind="service", auth_session_id="segment-worker-session"
    )
    old_service = ExecutionLeaseService(p.runs.store, clock=lambda: old_time)
    old = await old_service.acquire(
        {"expected_revision": 0, "lease_ttl_ms": 1000}, meta("old-lease"), original, holder=holder
    )
    current_service = ExecutionLeaseService(p.runs.store, clock=lambda: p.future)
    old_ref = Ref(kind="lease", id=old["id"], version=str(old["revision"]))
    with pytest.raises(DomainError) as denied:
        await current_service.renew(
            {
                "lease_ref": old_ref.wire(),
                "fencing_token": old["fencing_token"],
                "lease_ttl_ms": 1000,
            },
            meta("no-renew-old"),
            original,
            holder=holder,
        )
    assert denied.value.failure.code in ("lease_context_expired", "lease_expired")
    actual = await p.runs.store.get(p.actor, "execution.leases", old["id"])
    assert actual.payload["state"] == "expired"
    assert actual.revision == old["revision"] + 1
    assert actual.payload["lease"]["expires_at"] == old["expires_at"]
    assert actual.payload["lease"]["fencing_token"] == old["fencing_token"]
    new = await current_service.acquire(
        {"expected_revision": actual.revision, "lease_ttl_ms": 1000},
        meta("fresh-lease"),
        p.ctx,
        holder=holder,
    )
    assert new["fencing_token"] == old["fencing_token"] + 1
    assert new["revision"] == actual.revision + 1
    historical = await p.runs.store.get(p.actor, "execution.leases", old["id"], revision=1)
    assert historical.payload["lease"] == old
