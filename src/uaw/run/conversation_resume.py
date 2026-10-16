"""A-owned safe queue wake. A clock transition is never execution authorization.

This first adapter admits only calls still inside their original deadlines.
Long waits require a separate proven execution segment; no deadline is renewed.
"""

import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore
from uaw.run.clock_ports import ClockChange, ConversationClockPort
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.conversation_control import QUESTIONS, ConversationControls
from uaw.run.jobs import JOBS, RunJobs
from uaw.shared.contracts import Principal, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract

Payload = dict[str, Any]
ResumeCheck = Callable[[Payload], Awaitable[None]]


class ConversationResumer:
    def __init__(
        self,
        records: PostgresRecordStore,
        jobs: RunJobs,
        *,
        clocks: ConversationClockPort | None,
        verify: ResumeCheck,
    ) -> None:
        if jobs.records is not records:
            raise ValueError("Continuation must use the original queue/store")
        self.records, self.jobs, self.clocks, self.verify = records, jobs, clocks, verify
        self.controls = ConversationControls(records)
        self.transactions = TransactionalStore(records.database)

    async def resume(self, actor: Principal, run_id: str) -> bool:
        if self.clocks is None:
            raise CapabilityUnavailable("conversation.original_execution_clocks")
        clocks = self.clocks
        aggregate = await self.controls.aggregate(actor, run_id)
        job = (await self.records.get(actor, JOBS, run_id)).payload
        validate_contract("BackgroundRunJob", job)
        if job["principal"] != actor.wire():
            raise reject("conversation_resume_owner", "Original complete session required", 403)
        if job["state"] != "blocked":
            return False
        if "context" not in job or "instance_ref" not in job or "role_ref" not in job:
            raise CapabilityUnavailable("conversation.original_prepared_job")
        ctx = TrustedExecutionContext.model_validate_json(json.dumps(job["context"]))
        if ctx.principal != actor or ctx.run_id != run_id:
            raise reject("conversation_resume_owner", "Original execution context required", 403)
        await self.verify(job)

        async def write(tx: RecordTransaction) -> Payload:
            run = await self.controls.owned(tx, actor, run_id)
            current = await tx.load(JOBS, run_id)
            if current.payload != job:
                return {"woken": False}  # Another page/worker already progressed it.
            if run["status"] not in ("running", "waiting_for_user", "preparing"):
                raise reject("conversation_resume_state", "Run cannot resume", 409)
            if (
                ctx.conversation_id != run["conversation_id"]
                or ctx.task_id != run["task_id"]
                or ctx.scope.conversation_id != run["conversation_id"]
                or ctx.scope.task_id != run["task_id"]
                or run.get("root_agent_ref", {}).get("id") != job["instance_ref"]["id"]
            ):
                raise reject("conversation_resume_owner", "Original task/root differs", 403)
            if not await self.controls.pending_since(tx, actor, run_id, job.get("frame_ref")):
                return {"woken": False}
            if any(
                r.payload["state"] == "open"
                for r in await self.controls.matching(tx, QUESTIONS, run_id)
            ):
                raise reject("conversation_resume_question", "Original question still open", 409)
            await RunIdleEffects().check(tx, actor, run_id)
            ledger = await tx.load("budget.ledgers", run_id)
            if any(
                datetime.fromisoformat(v.replace("Z", "+00:00")) <= datetime.now(UTC)
                for v in (ctx.deadline, run["budget"]["deadline"], ledger.payload["deadline"])
            ):
                raise CapabilityUnavailable("conversation.new_active_execution_segment")
            clock = await tx.load("run.execution_clocks", run_id)
            original_limit = clock.payload["active_limit_ms"]
            clock_revision = clock.revision
            elapsed = clock.payload["active_elapsed_ms"]
            if clock.payload["mode"] == "stopped":
                raise reject(
                    "conversation_resume_clock_stopped", "Stopped clock cannot resume", 409
                )
            base_revision = run["revision"]
            changed = {**run, "revision": base_revision + 1, "status": "preparing"}
            await tx.write("runs", run_id, "RunRecord", changed, base_revision)
            resumed = await clocks.change(tx, actor, run_id, ClockChange(clock_revision, "active"))
            actual = await tx.load("run.execution_clocks", run_id)
            binding = await tx.load("run.protocol_bindings", run_id)
            validate_contract("RunExecutionClock", resumed.wire())
            if (
                actual.payload != resumed.wire()
                or actual.revision != clock_revision + 1
                or resumed.revision != actual.revision
                or resumed.run_id != run_id
                or resumed.mode != "active"
                or resumed.in_flight_refs
                or resumed.active_limit_ms != original_limit
                or resumed.active_elapsed_ms < elapsed
                or resumed.active_elapsed_ms >= resumed.active_limit_ms
                or binding.payload["clock_ref"]
                != {"kind": "checkpoint", "id": run_id, "version": str(actual.revision)}
            ):
                raise reject("conversation_resume_clock_unproven", "Owning clock differs", 412)
            if await self.controls.owned(tx, actor, run_id) != changed:
                raise reject("conversation_resume_run_changed", "Clock changed Run state", 412)
            await self.jobs.wake(tx, job)
            await self.verify(job)  # Auth/model/policy are re-read after all awaits.
            await tx.emit(
                run["conversation_id"],
                "run.updated",
                changed,
                base_revision=base_revision,
                result_revision=base_revision + 1,
            )
            return {"woken": True}

        return bool((await self.transactions.inspect(actor, aggregate, write))["woken"])
