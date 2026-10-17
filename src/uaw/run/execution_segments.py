"""A-owned remaining-active execution segments, never renewal of an old send.

Only explicit candidate composition can mint a segment after an owning clock
transition. Ordinary Runs keep the original deadline and do no segment reads.
"""

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Any

from uaw.infrastructure.db.models import RecordVersionRow
from uaw.infrastructure.db.records import PostgresRecordStore, parameter_hash
from uaw.infrastructure.db.transactions import RecordTransaction, reference
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import Record, StoreMissing

Payload = dict[str, Any]
SEGMENTS = "run.active_segments"


def utcnow() -> datetime:
    return datetime.now(UTC)


def instant(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() is None:
        raise reject("execution_segment_time_invalid", "Aware service time required", 412)
    return result


def identity(ctx: Payload) -> Payload:
    return {
        k: v
        for k, v in ctx.items()
        if k not in ("operation_id", "attempt_id", "trace_id", "deadline", "budget_reservation_ref")
    }


class ExecutionSegments:
    def __init__(self, records: PostgresRecordStore) -> None:
        self.records = records

    async def load(
        self,
        ctx: TrustedExecutionContext,
        namespace: str,
        *,
        revision: int | None = None,
        tx: RecordTransaction | None = None,
    ) -> Record:
        key = ctx.run_id or ""
        if tx is None:
            return await self.records.get(ctx.principal, namespace, key, revision=revision)
        if tx.owner != ctx.principal.id:
            raise reject(
                "execution_segment_owner_denied", "Original user transaction required", 403
            )
        if revision is None:
            row = await tx.load(namespace, key)
        else:
            historical = await tx.session.get(
                RecordVersionRow, (tx.owner, namespace, key, revision)
            )
            if historical is None:
                raise StoreMissing()
            observed = Record(
                namespace, key, historical.revision, historical.schema_name, historical.payload
            )
            if tx.database is not None:
                tx.database.observe_record((tx.owner, namespace, key), revision, observed)
            return observed
        return Record(namespace, key, row.revision, row.schema_name, deepcopy(row.payload))

    async def mint(
        self, tx: RecordTransaction, job: Payload, clock: Payload
    ) -> TrustedExecutionContext:
        """Join A's safe wake transaction, after actual clock CAS; no new grants."""
        import json

        ctx = TrustedExecutionContext.model_validate_json(json.dumps(job["context"]))
        run = await self.load(ctx, "runs", tx=tx)
        ledger = await self.load(ctx, "budget.ledgers", tx=tx)
        source_job = await self.load(ctx, "run.background.jobs", tx=tx)
        current_clock = await self.load(ctx, "run.execution_clocks", tx=tx)
        admission_clock = await self.load(ctx, "run.execution_clocks", revision=1, tx=tx)
        inputs = await self.load(ctx, "run.input_sets", tx=tx)
        validate_contract("RunExecutionClock", clock)
        if (
            source_job.payload != job
            or job["state"] != "blocked"
            or job["principal"] != ctx.principal.wire()
            or ctx.principal.kind != "user"
            or ctx.agent_id is not None
            or ctx.node_id is not None
            or ctx.budget_reservation_ref is not None
            or ctx.run_id != job["run_id"]
            or run.payload["status"] != "preparing"
            or run.payload.get("root_agent_ref", {}).get("id") != job["instance_ref"]["id"]
            or current_clock.payload != clock
            or current_clock.revision != clock["revision"]
            or admission_clock.payload["active_limit_ms"] != clock["active_limit_ms"]
            or clock["mode"] != "active"
            or clock["in_flight_refs"]
            or clock["active_since"] != clock["captured_at"]
            or instant(clock["captured_at"]) > utcnow()
            or ledger.payload["cancel_requested"]
            or ledger.payload["overdrawn"]
        ):
            raise reject("execution_segment_unproven", "Original owning wake sources differ", 412)
        remaining = clock["active_limit_ms"] - clock["active_elapsed_ms"]
        if remaining <= 0:
            raise reject(
                "execution_segment_exhausted", "Active execution budget exhausted", 409, "budget"
            )
        deadline = instant(clock["captured_at"]) + timedelta(milliseconds=remaining)
        if deadline <= utcnow():
            raise reject(
                "execution_segment_expired", "New execution segment already expired", 409, "timeout"
            )
        continued = ctx.model_copy(update={"deadline": deadline.isoformat()})
        try:
            previous = await self.load(ctx, SEGMENTS, tx=tx)
        except StoreMissing:
            previous = None
        value = {
            "protocol": "conversation-v1",
            "run_id": ctx.run_id,
            "revision": previous.revision + 1 if previous else 1,
            "input_revision": inputs.revision,
            "context": continued.wire(),
            "source_job_ref": {
                **reference("checkpoint", job["run_id"], source_job.revision),
                "content_hash": parameter_hash(job),
            },
            "clock_ref": {
                **reference("checkpoint", job["run_id"], current_clock.revision),
                "content_hash": parameter_hash(clock),
            },
            "budget_hash": parameter_hash(run.payload["budget"]),
            "ledger_deadline": ledger.payload["deadline"],
            "issued_at": clock["captured_at"],
        }
        await tx.write(
            SEGMENTS,
            job["run_id"],
            "InternalRunActiveSegment",
            value,
            previous.revision if previous else 0,
        )
        return continued

    async def deadline(
        self,
        ctx: TrustedExecutionContext,
        run: Payload,
        ledger: Payload,
        *,
        tx: RecordTransaction | None = None,
        now: datetime | None = None,
    ) -> datetime:
        """Fresh timing proof only; callers still check authentication/policy/effects."""
        current_time = now if now is not None else utcnow()
        caller_deadline = instant(ctx.deadline)
        original = min(instant(run["budget"]["deadline"]), instant(ledger["deadline"]))
        result = min(caller_deadline, original)
        # A resumed call may already carry a proven remaining-active segment
        # while the initial wall deadline is still live. Its new reservation
        # must use that same bound, not silently clamp it to the old ledger.
        # Ordinary original contexts keep the no-segment-read fast path.
        if original < caller_deadline and current_time < caller_deadline:
            try:
                segment = await self.load(ctx, SEGMENTS, tx=tx)
            except StoreMissing:
                pass  # Legacy/missing sources retain the original expired deadline.
            else:
                result = await self.proven(ctx, segment, run, ledger, tx=tx)
        if result <= current_time:
            raise reject(
                "execution_deadline_expired", "Execution deadline has passed", 409, "timeout"
            )
        return result

    async def root_deadline(
        self,
        ctx: TrustedExecutionContext,
        run: Payload,
        ledger: Payload,
        *,
        tx: RecordTransaction,
        now: datetime,
    ) -> datetime:
        """Observe the root bound for lease state; an old caller stays expired.

        An expired old context must not revoke a newer live root lease merely
        because the immutable initial budget deadline is now in the past.
        """
        import json

        original = min(instant(run["budget"]["deadline"]), instant(ledger["deadline"]))
        if original > now:
            return original
        try:
            segment = await self.load(ctx, SEGMENTS, tx=tx)
        except StoreMissing:
            return original
        current = TrustedExecutionContext.model_validate_json(
            json.dumps(segment.payload["context"])
        )
        if identity(current.wire()) != identity(ctx.wire()):
            raise reject("execution_segment_owner_denied", "Original root scope required", 403)
        return await self.proven(current, segment, run, ledger, tx=tx)

    async def proven(
        self,
        ctx: TrustedExecutionContext,
        segment: Record,
        run: Payload,
        ledger: Payload,
        *,
        tx: RecordTransaction | None = None,
    ) -> datetime:
        from uaw.run.jobs import JOBS

        value = segment.payload
        validate_contract("InternalRunActiveSegment", value)
        binding = await self.load(ctx, "run.protocol_bindings", tx=tx)
        clock = await self.load(ctx, "run.execution_clocks", tx=tx)
        validate_contract("ConversationProtocolBinding", binding.payload)
        validate_contract("RunExecutionClock", clock.payload)
        pins = (value["clock_ref"], value["source_job_ref"])
        if any(
            p["kind"] != "checkpoint"
            or p["id"] != ctx.run_id
            or set(p) != {"kind", "id", "version", "content_hash"}
            for p in pins
        ):
            raise reject("execution_segment_unproven", "Exact historical sources required", 412)
        origin = await self.load(
            ctx, "run.execution_clocks", revision=int(pins[0]["version"]), tx=tx
        )
        admission_clock = await self.load(ctx, "run.execution_clocks", revision=1, tx=tx)
        source = await self.load(ctx, JOBS, revision=int(pins[1]["version"]), tx=tx)
        validate_contract("RunExecutionClock", origin.payload)
        validate_contract("BackgroundRunJob", source.payload)
        remaining = origin.payload["active_limit_ms"] - origin.payload["active_elapsed_ms"]
        derived = instant(origin.payload["captured_at"]) + timedelta(milliseconds=remaining)
        if (
            segment.schema_name != "InternalRunActiveSegment"
            or value["revision"] != segment.revision
            or value["run_id"] != ctx.run_id
            or run["id"] != ctx.run_id
            or run["conversation_id"] != ctx.scope.conversation_id
            or run["task_id"] != ctx.task_id
            or ctx.principal.kind != "user"
            or identity(value["context"]) != identity(ctx.wire())
            or value["context"]["deadline"] != ctx.deadline
            or identity(source.payload.get("context", {})) != identity(ctx.wire())
            or source.payload["principal"] != ctx.principal.wire()
            or source.payload["state"] != "blocked"
            or source.schema_name != "BackgroundRunJob"
            or source.payload["revision"] != source.revision
            or source.payload.get("instance_ref", {}).get("id")
            != run.get("root_agent_ref", {}).get("id")
            or parameter_hash(source.payload) != pins[1]["content_hash"]
            or origin.schema_name != "RunExecutionClock"
            or origin.payload["revision"] != origin.revision
            or origin.payload["run_id"] != ctx.run_id
            or parameter_hash(origin.payload) != pins[0]["content_hash"]
            or origin.payload["mode"] != "active"
            or origin.payload["active_since"] != origin.payload["captured_at"]
            or origin.payload["in_flight_refs"]
            or remaining <= 0
            or origin.payload["active_limit_ms"] != admission_clock.payload["active_limit_ms"]
            or derived != instant(ctx.deadline)
            or value["issued_at"] != origin.payload["captured_at"]
            or value["budget_hash"] != parameter_hash(run["budget"])
            or value["ledger_deadline"] != ledger["deadline"]
            or binding.payload["owner_id"] != ctx.principal.id
            or binding.payload["revision"] != binding.revision
            or binding.payload["run_id"] != ctx.run_id
            or binding.payload["input_revision"] < value["input_revision"]
            or binding.payload["clock_ref"]
            != reference("checkpoint", ctx.run_id or "", clock.revision)
            or clock.payload["revision"] != clock.revision
            or clock.schema_name != "RunExecutionClock"
            or clock.revision < origin.revision
            or clock.payload["run_id"] != ctx.run_id
            or clock.payload["mode"] != "active"
            or instant(clock.payload["captured_at"]) < instant(value["issued_at"])
            or instant(clock.payload["captured_at"]) > utcnow()
            or clock.payload["active_limit_ms"] != origin.payload["active_limit_ms"]
            or clock.payload["active_elapsed_ms"] < origin.payload["active_elapsed_ms"]
            or clock.payload["active_elapsed_ms"] >= clock.payload["active_limit_ms"]
            or ledger["cancel_requested"]
            or ledger["overdrawn"]
            or run["status"] not in ("preparing", "running", "verifying", "waiting_for_user")
        ):
            raise reject(
                "execution_segment_unproven", "Current execution segment sources differ", 412
            )
        return derived
