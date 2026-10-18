"""Real SQL/owning clock and queue, controlled model HTTP and long-wait time."""

import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from tests.integration.agent.test_completion_postgres import review
from tests.integration.agent.test_conversation_postgres import case as case
from tests.integration.agent.test_conversation_postgres import domain as domain
from tests.integration.agent.test_conversation_postgres import inventory, output
from tests.integration.agent.test_conversation_postgres import scenario as scenario
from tests.integration.test_control_plane import meta
from uaw.agent.completion.contracts import contract_from_frame
from uaw.api.application import create_app
from uaw.run.background import BackgroundAgent
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.conversation_control import ConversationControls
from uaw.run.execution_clock import ExecutionClocks, measure
from uaw.run.execution_segments import ExecutionSegments
from uaw.run.jobs import JOBS
from uaw.run.presentation import RunPresentationReader
from uaw.run.review_wait import ReviewWaitSources
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.conversation import ConversationRequestMeta, RunCorrectionRequest
from uaw.shared.errors import DomainError, reject

pytestmark = pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)


async def ready(p, *, expect_park=True):
    p.future = datetime.now(UTC)
    p.clocks = ExecutionClocks(
        p.runs.store,
        effects=RunIdleEffects(),
        reviews=ReviewWaitSources(p.runs.store),
        now=lambda: p.future.isoformat(),
    )
    p.driver = BackgroundAgent(
        p.control,
        conversation_clocks=p.clocks,
        conversation_segments=ExecutionSegments(p.runs.store),
    )
    p.queue = await p.driver.prepare()
    frame = (await p.runs.store.get(p.actor, "intent.frames", p.run["task_id"])).payload
    p.case.responses[:] = [
        output(
            {"protocol": "conversation-v1", "action": "deliver", "text": "The requested report."}
        ),
        review(contract_from_frame(frame)["requirements"]),
    ]
    assert await p.queue.tick()
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    if not expect_park:
        return job, None
    assert job["stage"] == "delivery" and job["state"] == "blocked", job
    view = await RunPresentationReader(p.runs.store).read(p.actor, p.run["id"])
    assert view["phase"] == "awaiting_acceptance", view
    return job, view


async def decide(p, job, view, decision="accept"):
    return await p.control.completion_controller.accept(
        p.actor,
        Ref.model_validate(view["delivery"]["bundle_ref"]),
        Ref.model_validate(view["delivery"]["artifact_ref"]),
        decision,
        TrustedExecutionContext.model_validate_json(json.dumps(job["step_context"])),
        meta("review-decision"),
    )


async def test_long_review_wait_survives_restart_accepts_once_without_model_or_budget_renewal(
    scenario, monkeypatch
):
    p = scenario
    job, view = await ready(p)
    before = await p.clocks.current(p.actor, p.run["id"])
    assert before.mode == "waiting_for_user"
    assert before.waiting_item_ref.kind == "item"
    budget = (await p.runs.get_run(p.actor, p.run["id"]))["budget"]
    ledger = (await p.runs.store.get(p.actor, "budget.ledgers", p.run["id"])).payload
    p.future = datetime.fromisoformat(budget["deadline"]) + timedelta(hours=2)
    monkeypatch.setattr("uaw.run.execution_segments.utcnow", lambda: p.future)
    read = measure(await p.clocks.current(p.actor, p.run["id"]), p.future.isoformat())
    assert read.active_elapsed_ms == before.active_elapsed_ms and read.wait_elapsed_ms > 7200000
    ctx = TrustedExecutionContext.model_validate_json(json.dumps(job["step_context"]))
    with pytest.raises(DomainError, match="Execution deadline"):
        await ExecutionSegments(p.runs.store).deadline(ctx, view["run"], ledger, now=p.future)
    # Original queue scans do not rewrite the parked job/clock or resend calls.
    for _ in range(2):
        assert not await p.queue.tick()
    assert (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload == job
    assert len(p.case.requests) == 2
    p.driver = BackgroundAgent(
        p.control,
        conversation_clocks=p.clocks,
        conversation_segments=ExecutionSegments(p.runs.store),
    )
    p.queue = await p.driver.prepare()
    await decide(p, job, view)
    assert await p.control.conversation_recovery.scan()
    assert await p.queue.tick()
    final = await p.runs.get_run(p.actor, p.run["id"])
    assert final["status"] == "completed" and final["budget"] == budget
    clock = await p.clocks.current(p.actor, p.run["id"])
    assert clock.mode == "stopped" and clock.active_elapsed_ms == before.active_elapsed_ms
    assert clock.wait_elapsed_ms == read.wait_elapsed_ms
    assert (await p.runs.store.get(p.actor, "budget.ledgers", p.run["id"])).payload == ledger
    assert len(p.case.requests) == 2


async def test_cancel_review_wait_stops_clock_and_retains_report(scenario):
    p = scenario
    job, view = await ready(p)
    before = await p.clocks.current(p.actor, p.run["id"])
    p.future += timedelta(hours=3)
    await p.runs.control(
        p.actor,
        {
            "run_id": p.run["id"],
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "Cancel review"},
        },
        meta("cancel-review", view["run"]["revision"]),
    )
    assert not await p.queue.tick()
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "cancelled"
    clock = await p.clocks.current(p.actor, p.run["id"])
    assert clock.mode == "stopped" and clock.active_elapsed_ms == before.active_elapsed_ms
    assert len(await inventory(p, "workspace.artifacts")) == 1 and len(p.case.requests) == 2
    with pytest.raises(DomainError):
        await decide(p, job, view)


async def test_revoked_policy_after_wait_cannot_accept_and_original_report_remains(scenario):
    p = scenario
    job, view = await ready(p)
    p.future += timedelta(hours=2)
    ctx = TrustedExecutionContext.model_validate_json(json.dumps(job["step_context"]))
    row = await p.runs.store.get(p.actor, "execution.policies", ctx.capability_policy_ref.id)
    await p.runs.store.put(
        p.actor,
        row.namespace,
        row.resource_id,
        row.schema_name,
        {**row.payload, "revision": row.revision + 1},
        expected_revision=row.revision,
        request_id="revoke-review-policy",
    )
    with pytest.raises(DomainError):
        await decide(p, job, view)
    assert not await inventory(p, "run.completion.acceptance")
    assert (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload == job
    assert len(p.case.requests) == 2


async def test_correction_after_long_review_uses_remaining_time_and_stales_old_proposal(
    scenario, monkeypatch
):
    p = scenario
    job, view = await ready(p)
    before = await p.clocks.current(p.actor, p.run["id"])
    p.future = datetime.fromisoformat(view["run"]["budget"]["deadline"]) + timedelta(hours=2)
    monkeypatch.setattr("uaw.run.execution_segments.utcnow", lambda: p.future)
    controls = ConversationControls(p.runs.store)
    await controls.correct(
        p.actor,
        RunCorrectionRequest(
            run_id=p.run["id"],
            expected_input_revision=1,
            text="Make the report for students.",
            attachment_refs=(),
        ),
        ConversationRequestMeta(
            request_id="review-correction",
            schema_version="0.2",
            expected_revision=view["run"]["revision"],
        ),
    )
    assert await p.driver.resume_conversation(p.actor, p.run["id"])
    clock = await p.clocks.current(p.actor, p.run["id"])
    assert clock.mode == "active" and clock.active_elapsed_ms == before.active_elapsed_ms
    fresh = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert fresh["stage"] == "prepared" and "proposal_ref" not in fresh
    assert datetime.fromisoformat(fresh["context"]["deadline"]) == p.future + timedelta(
        milliseconds=before.active_limit_ms - before.active_elapsed_ms
    )
    with pytest.raises(DomainError):
        await decide(p, job, view)
    assert len(p.case.requests) == 2
    for _ in range(5):
        if (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload["stage"] == "step":
            break
        assert await p.queue.tick()
    frame = (await p.runs.store.get(p.actor, "intent.frames", p.run["task_id"])).payload
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "deliver",
                "text": "A revised report for students.",
            }
        ),
        review(contract_from_frame(frame)["requirements"]),
    ]
    assert await p.queue.tick()
    fresh = await RunPresentationReader(p.runs.store).read(p.actor, p.run["id"])
    assert fresh["phase"] == "awaiting_acceptance" and fresh["input_revision"] == 2
    assert fresh["delivery"]["artifact_ref"] != view["delivery"]["artifact_ref"]
    assert (
        await controls.lookup(p.actor, p.run["id"], "review-correction")
    ).patch.state == "applied"
    assert len(p.case.requests) == 4


async def test_unknown_effect_and_missing_review_source_refuse_acceptance_or_clock_pause(scenario):
    p = scenario
    job, view = await ready(p)
    root = p.job["step_context"]["attempt_id"]
    row = await p.runs.store.get(p.actor, "model.invocations", root)
    value = {**row.payload, "state": "claimed"}
    value.pop("result")
    await p.runs.store.put(
        p.actor,
        row.namespace,
        row.resource_id,
        row.schema_name,
        value,
        expected_revision=row.revision,
        request_id="review-unknown-effect",
    )
    with pytest.raises(DomainError):
        await decide(p, job, view)
    assert not await inventory(p, "run.completion.acceptance")
    plain = ExecutionClocks(p.runs.store, effects=RunIdleEffects())
    with pytest.raises(DomainError):
        await plain.current(p.actor, p.run["id"])


async def test_http_acceptance_receipt_wakes_original_parked_delivery_and_replay_does_not_resend(
    scenario,
):
    p = scenario
    job, view = await ready(p)
    body = {
        "meta": meta("review-http-accept").wire(),
        "payload": {
            "bundle_ref": view["delivery"]["bundle_ref"],
            "artifact_ref": view["delivery"]["artifact_ref"],
            "decision": "accept",
        },
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(p.control)), base_url="http://test"
    ) as client:
        headers = {"Authorization": "Bearer " + "u" * 40}
        reply = await client.post(
            f"/v1/runs/{p.run['id']}/delivery/acceptance", json=body, headers=headers
        )
        assert reply.status_code == 200, reply.json()
        replay = await client.post(
            f"/v1/runs/{p.run['id']}/delivery/acceptance", json=body, headers=headers
        )
        assert replay.status_code == 200 and replay.json() == reply.json()
    assert await p.queue.tick()  # persisted scan wakes original acceptance
    assert await p.queue.tick()  # completion only, no model invocation
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "completed"
    assert len(p.case.requests) == 2


async def test_acceptance_between_preview_and_park_finishes_without_false_failure(
    scenario, monkeypatch
):
    from uaw.agent.completion.delivery import row_pin

    p = scenario
    original = BackgroundAgent.park_review

    async def early_accept(driver, actor, run, proposal, job):
        bundle = (await p.runs.store.get(actor, "agent.completion.bundles", proposal.id)).payload
        await p.control.completion_controller.accept(
            actor,
            row_pin("content", proposal.id, bundle),
            Ref.model_validate(bundle["artifact_ref"]),
            "accept",
            TrustedExecutionContext.model_validate_json(json.dumps(job["step_context"])),
            meta("review-immediate-accept"),
        )
        result = await original(driver, actor, run, proposal, job)
        assert result is None
        return result

    monkeypatch.setattr(BackgroundAgent, "park_review", early_accept)
    # This race finishes immediately, so ready()'s parked-state assertions do not apply.
    p.clocks = ExecutionClocks(
        p.runs.store, effects=RunIdleEffects(), reviews=ReviewWaitSources(p.runs.store)
    )
    p.driver = BackgroundAgent(
        p.control,
        conversation_clocks=p.clocks,
        conversation_segments=ExecutionSegments(p.runs.store),
    )
    p.queue = await p.driver.prepare()
    frame = (await p.runs.store.get(p.actor, "intent.frames", p.run["task_id"])).payload
    p.case.responses[:] = [
        output({"protocol": "conversation-v1", "action": "deliver", "text": "The report."}),
        review(contract_from_frame(frame)["requirements"]),
    ]
    assert await p.queue.tick()
    assert (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload["state"] == "queued"
    assert await p.queue.tick()
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "completed"
    assert (await p.clocks.current(p.actor, p.run["id"])).mode == "stopped"
    assert len(p.case.requests) == 2


async def test_cancel_after_acceptance_before_completion_cannot_commit_old_proposal(scenario):
    p = scenario
    job, view = await ready(p)
    await decide(p, job, view)
    await p.runs.control(
        p.actor,
        {
            "run_id": p.run["id"],
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "Cancel accepted report"},
        },
        meta("cancel-accepted-review", view["run"]["revision"]),
    )
    assert not await p.queue.tick()
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "cancelled"
    assert (await p.clocks.current(p.actor, p.run["id"])).mode == "stopped"
    assert len(await inventory(p, "run.completion.acceptance")) == 1
    assert len(p.case.requests) == 2


@pytest.mark.parametrize("fault", ["unknown_before_pause", "after_clock_write"])
async def test_failed_review_parking_leaves_no_partial_wait_checkpoint(
    scenario, monkeypatch, fault
):
    from sqlalchemy import select

    from uaw.infrastructure.db.models import RecordVersionRow

    p = scenario
    original = BackgroundAgent.park_review

    async def fail_parking(driver, actor, run, proposal, job):
        if fault == "unknown_before_pause":
            row = await p.runs.store.get(
                actor, "model.invocations", job["step_context"]["attempt_id"]
            )
            value = {**row.payload, "state": "claimed"}
            value.pop("result")
            await p.runs.store.put(
                actor,
                row.namespace,
                row.resource_id,
                row.schema_name,
                value,
                expected_revision=row.revision,
                request_id="unknown-before-review-pause",
            )
        else:
            change = driver.conversation_clocks.change

            async def fail_after_clock_write(tx, actor, run_id, request):
                result = await change(tx, actor, run_id, request)
                if request.mode == "waiting_for_user":
                    raise reject("review_checkpoint_test_failure", "Abort parked checkpoint", 409)
                return result

            monkeypatch.setattr(driver.conversation_clocks, "change", fail_after_clock_write)
        return await original(driver, actor, run, proposal, job)

    monkeypatch.setattr(BackgroundAgent, "park_review", fail_parking)
    job, _ = await ready(p, expect_park=False)
    assert job["stage"] == "step" and job["state"] == "blocked"
    expected = (
        "conversation_effect_pending"
        if fault == "unknown_before_pause"
        else "review_checkpoint_test_failure"
    )
    assert job["failure"]["code"] == expected
    async with p.runs.store.database.sessions() as session:
        history = list(
            await session.scalars(
                select(RecordVersionRow).where(
                    RecordVersionRow.principal_id == p.actor.id,
                    RecordVersionRow.namespace == "run.execution_clocks",
                    RecordVersionRow.resource_id == p.run["id"],
                )
            )
        )
    assert history and not any(r.payload["mode"] == "waiting_for_user" for r in history)
    assert not await inventory(p, "run.completion.acceptance")
    assert len(p.case.requests) == 2
