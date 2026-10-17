"""Actual A SQL time adapter; Tool claim consumption is a separate pending gate."""

import asyncio
import json
from datetime import datetime, timedelta

import pytest
from sqlalchemy import update

from tests.integration.agent.test_conversation_controls import ask, control_meta
from tests.integration.agent.test_conversation_controls import case as case
from tests.integration.agent.test_conversation_controls import domain as domain
from tests.integration.agent.test_conversation_controls import scenario as scenario
from tests.integration.agent.test_conversation_postgres import inventory
from tests.integration.agent.test_conversation_resume import ControlledClockSeam, snapshot
from tests.integration.agent.test_execution_segments import resumed
from tests.integration.test_control_plane import meta
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore
from uaw.run import execution_segments
from uaw.run.background import BackgroundAgent
from uaw.run.execution_segments import SEGMENTS, ExecutionSegments
from uaw.run.jobs import JOBS
from uaw.run.tool_timing import RunToolDispatchTiming
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.conversation import RunCorrectionRequest
from uaw.shared.errors import DomainError
from uaw.shared.stores import StoreMissing

pytestmark = pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)


async def check(p, adapter, ctx=None, action=None):
    async def write(tx):
        assert await adapter.check(tx, ctx or p.ctx) is None
        if action is not None:
            await action(tx)
        return {"checked": True}

    return await TransactionalStore(p.runs.store.database).inspect(
        p.actor, "tool-run:" + p.run["id"], write
    )


async def test_new_segment_checks_without_mutation_old_context_stays_expired(scenario, monkeypatch):
    p = scenario
    await resumed(p, monkeypatch)
    before = await snapshot(p)
    accounts = await inventory(p, "budget.accounting")
    for _ in range(2):
        assert await check(p, RunToolDispatchTiming(p.runs.store, segments=p.segments)) == {
            "checked": True
        }
    old = TrustedExecutionContext.model_validate_json(json.dumps(p.original_job["context"]))
    with pytest.raises(DomainError) as expired:
        await check(p, RunToolDispatchTiming(p.runs.store, segments=p.segments), old)
    assert expired.value.failure.code == "execution_deadline_expired"
    with pytest.raises(DomainError):
        await check(p, RunToolDispatchTiming(p.runs.store))
    different_session = p.ctx.model_copy(
        update={"principal": p.actor.model_copy(update={"auth_session_id": "different-session"})}
    )
    with pytest.raises(DomainError):
        await check(p, RunToolDispatchTiming(p.runs.store, segments=p.segments), different_session)
    assert await snapshot(p) == before
    assert await inventory(p, "budget.accounting") == accounts
    assert not await inventory(p, "tool.dispatch.intents") and len(p.case.requests) == 1


async def test_cancelled_after_cached_reads_is_seen_in_original_tool_transaction(
    scenario, monkeypatch
):
    p = scenario
    await resumed(p, monkeypatch)
    cached, cancelled = asyncio.Event(), asyncio.Event()
    adapter = RunToolDispatchTiming(p.runs.store, segments=p.segments)

    async def original_claim(tx):
        # Hold references so the ORM identity map really retains the older rows.
        run = await tx.load("runs", p.run["id"])
        ledger = await tx.load("budget.ledgers", p.run["id"])
        assert run.payload["status"] == "preparing" and not ledger.payload["cancel_requested"]
        cached.set()
        await cancelled.wait()
        await adapter.check(tx, p.ctx)
        raise AssertionError("Cancellation must reject before claim")

    task = asyncio.create_task(
        TransactionalStore(p.runs.store.database).inspect(
            p.actor, "tool-run:" + p.run["id"], original_claim
        )
    )
    try:
        await asyncio.wait_for(cached.wait(), timeout=5)
        run = await p.runs.get_run(p.actor, p.run["id"])
        await p.runs.control(
            p.actor,
            {
                "run_id": p.run["id"],
                "control": {"mode": "cancel", "reason": "Cancel", "preserve_refs": []},
            },
            meta("timing-cancel", run["revision"]),
        )
    finally:
        cancelled.set()
    with pytest.raises(DomainError) as denied:
        await task
    assert denied.value.failure.code == "execution_cancelled"
    assert not await inventory(p, "tool.dispatch.intents")


async def test_missing_current_segment_cannot_use_cached_proof(scenario, monkeypatch):
    p = scenario
    await resumed(p, monkeypatch)
    adapter = RunToolDispatchTiming(p.runs.store, segments=p.segments)

    async def original_claim(tx):
        segment = await tx.load(SEGMENTS, p.run["id"])
        async with p.runs.store.database.sessions.begin() as other:
            await other.execute(
                update(RecordRow)
                .where(
                    RecordRow.principal_id == p.actor.id,
                    RecordRow.namespace == SEGMENTS,
                    RecordRow.resource_id == p.run["id"],
                )
                .values(deleted=True)
            )
        assert not segment.deleted
        await adapter.check(tx, p.ctx)
        return {"unexpected": True}

    with pytest.raises(DomainError) as missing:
        await TransactionalStore(p.runs.store.database).inspect(
            p.actor, "tool-run:" + p.run["id"], original_claim
        )
    assert missing.value.failure.code == "execution_deadline_expired"


async def test_check_joins_outer_rollback_and_checks_final_time(scenario, monkeypatch):
    p = scenario
    await resumed(p, monkeypatch)
    adapter = RunToolDispatchTiming(p.runs.store, segments=p.segments)
    before = await snapshot(p)
    run = await p.runs.get_run(p.actor, p.run["id"])

    async def fail_after_check(tx):
        await tx.write(
            "event.payloads",
            "timing-rollback",
            "EventPayload",
            {"action": "run.updated", "parameters": run},
        )
        raise RuntimeError("Original claim rollback")

    with pytest.raises(RuntimeError):
        await check(p, adapter, action=fail_after_check)
    with pytest.raises(StoreMissing):
        await p.runs.store.get(p.actor, "event.payloads", "timing-rollback")
    assert await snapshot(p) == before
    original = p.segments.deadline

    async def time_passes(*args, **kwargs):
        deadline = await original(*args, **kwargs)
        monkeypatch.setattr(execution_segments, "utcnow", lambda: deadline + timedelta(seconds=1))
        return deadline

    monkeypatch.setattr(p.segments, "deadline", time_passes)
    with pytest.raises(DomainError) as expired:
        await check(p, adapter)
    assert expired.value.failure.code == "execution_deadline_expired"


async def test_foreign_transaction_and_mismatched_store_are_rejected(scenario):
    p = scenario
    ctx = TrustedExecutionContext.model_validate_json(json.dumps(p.job["context"]))
    adapter = RunToolDispatchTiming(p.runs.store)
    database = p.runs.store.database
    async with database.sessions() as session, session.begin():
        for tx in (
            RecordTransaction(session, "other-owner", database),
            RecordTransaction(session, p.actor.id),
        ):
            with pytest.raises(DomainError) as denied:
                await adapter.check(tx, ctx)
            assert denied.value.failure.code == "tool_timing_transaction_denied"
    different_store = type(p.runs.store)(database)
    with pytest.raises(ValueError):
        RunToolDispatchTiming(p.runs.store, segments=ExecutionSegments(different_store))
    assert not await inventory(p, "tool.dispatch.intents")


async def test_live_legacy_call_needs_no_segment_but_cannot_dispatch_while_waiting(scenario):
    p = scenario
    p.ctx = TrustedExecutionContext.model_validate_json(json.dumps(p.job["context"]))
    assert datetime.fromisoformat(p.ctx.deadline) > execution_segments.utcnow()
    assert await check(p, RunToolDispatchTiming(p.runs.store)) == {"checked": True}
    await ask(p)
    with pytest.raises(DomainError) as denied:
        await check(p, RunToolDispatchTiming(p.runs.store))
    assert denied.value.failure.code == "tool_timing_run_unavailable"


async def test_current_open_question_blocks_accepted_patch_when_segments_installed(scenario):
    p = scenario
    p.driver = BackgroundAgent(
        p.control,
        conversation_clocks=ControlledClockSeam(p.runs.store),
        conversation_segments=ExecutionSegments(p.runs.store),
    )
    p.queue = await p.driver.prepare()
    control, view = await ask(p)
    await control.correct(
        p.actor,
        RunCorrectionRequest(
            run_id=p.run["id"],
            expected_input_revision=view.input_revision,
            text="Additional context, without answering the question.",
            attachment_refs=(),
        ),
        control_meta(view, "correction-open-question"),
    )
    # Corrections normally invalidate the old question. Explicitly install a
    # current unresolved question to test the guard, not that normal behavior.
    question = await p.runs.store.get(
        p.actor, "run.clarification_questions", view.question.question.item_id
    )
    await p.runs.store.put(
        p.actor,
        question.namespace,
        question.resource_id,
        question.schema_name,
        {**question.payload, "revision": question.revision + 1, "state": "open"},
        expected_revision=question.revision,
        request_id="current-open-question",
    )
    before = await snapshot(p)
    with pytest.raises(DomainError) as denied:
        await p.driver.resume_conversation(p.actor, p.run["id"])
    assert denied.value.failure.code == "conversation_resume_question"
    assert await snapshot(p) == before and len(p.case.requests) == 1
    assert (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload["state"] == "blocked"
