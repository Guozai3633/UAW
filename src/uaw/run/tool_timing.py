"""A's SQL timing proof for a future explicitly installed Tool claim consumer."""

from sqlalchemy import and_, func, or_, select

from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import RecordTransaction
from uaw.run import execution_segments
from uaw.run.execution_segments import SEGMENTS, ExecutionSegments, instant
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing
from uaw.shared.tool_timing import ToolDispatchTimingPort


class RunToolDispatchTiming(ToolDispatchTimingPort):
    def __init__(
        self, records: PostgresRecordStore, *, segments: ExecutionSegments | None = None
    ) -> None:
        if segments is not None and segments.records is not records:
            raise ValueError("Tool timing requires the original execution segment store")
        self.records, self.segments = records, segments

    async def check(self, tx: RecordTransaction, ctx: TrustedExecutionContext) -> None:
        validate_contract("TrustedExecutionContext", ctx.wire())
        if (
            tx.database is not self.records.database
            or tx.session.bind is not self.records.database.engine
            or not tx.session.in_transaction()
            or tx.owner != ctx.principal.id
            or ctx.principal.kind != "user"
            or ctx.scope.principal_id != tx.owner
            or ctx.run_id is None
            or ctx.scope.conversation_id is None
        ):
            raise reject(
                "tool_timing_transaction_denied", "Original owning transaction required", 403
            )
        run_id, conversation_id = ctx.run_id, ctx.scope.conversation_id
        # Tool claim already holds tool-run. No conversation-locked caller may
        # acquire tool-run. Keep this lock until that same outer commit/rollback.
        await tx.session.execute(
            select(
                func.pg_advisory_xact_lock(
                    func.hashtextextended(f"{tx.owner}:conversation:{conversation_id}", 0)
                )
            )
        )
        keys = [("runs", run_id), ("budget.ledgers", run_id), ("conversations", conversation_id)]
        if self.segments is not None:
            keys += [
                (name, run_id)
                for name in (SEGMENTS, "run.execution_clocks", "run.protocol_bindings")
            ]
        # A Tool transaction may have read the Run before waiting for the lock.
        # Refresh only these source rows, preserving its pending Tool writes.
        rows = list(
            await tx.session.scalars(
                select(RecordRow)
                .where(
                    RecordRow.principal_id == tx.owner,
                    or_(
                        *[
                            and_(RecordRow.namespace == ns, RecordRow.resource_id == key)
                            for ns, key in keys
                        ]
                    ),
                )
                .execution_options(populate_existing=True)
            )
        )
        observed = {(row.namespace, row.resource_id): row for row in rows if not row.deleted}
        required = keys[:3]
        for key in required:
            if key not in observed:
                raise StoreMissing()
        run = await tx.load("runs", run_id)
        ledger = await tx.load("budget.ledgers", run_id)
        conversation = await tx.load("conversations", conversation_id)
        for row, schema in (
            (run, "RunRecord"),
            (ledger, "RootBudgetLedger"),
            (conversation, "Conversation"),
        ):
            validate_contract(schema, row.payload)
            if row.schema_name != schema or row.payload["revision"] != row.revision:
                raise reject("tool_timing_source_stale", "Current timing source differs", 412)
        if (
            run.payload["id"] != run_id
            or run.payload["conversation_id"] != conversation_id
            or ctx.conversation_id != conversation_id
            or ctx.task_id != run.payload["task_id"]
            or ctx.scope.task_id != run.payload["task_id"]
            or ctx.scope.project_id is not None
            or conversation.payload["id"] != conversation_id
            or conversation.payload["owner_id"] != tx.owner
            or ledger.payload["run_id"] != run_id
        ):
            raise reject("tool_timing_scope_denied", "Timing is outside the original Run", 403)
        if ledger.payload["cancel_requested"] or run.payload["status"] == "cancelled":
            raise reject("execution_cancelled", "Run has been cancelled", 409, "cancelled")
        if ledger.payload["overdrawn"]:
            raise reject("execution_budget_exceeded", "Run budget exceeded", 409, "budget")
        if run.payload["status"] not in ("preparing", "running", "verifying"):
            raise reject("tool_timing_run_unavailable", "Run cannot dispatch a new tool call", 409)
        if self.segments is not None:
            # Explicit composition only. Missing current proof cannot be supplied
            # by an older ORM identity-map value left in this transaction.
            if any(key not in observed for key in keys[3:]):
                original = min(
                    instant(ctx.deadline),
                    instant(run.payload["budget"]["deadline"]),
                    instant(ledger.payload["deadline"]),
                )
                if original <= execution_segments.utcnow():
                    raise reject(
                        "execution_deadline_expired", "Current segment is missing", 409, "timeout"
                    )
            deadline = await self.segments.deadline(ctx, run.payload, ledger.payload, tx=tx)
            if deadline <= execution_segments.utcnow():
                raise reject(
                    "execution_deadline_expired",
                    "Dispatch check expired while waiting",
                    409,
                    "timeout",
                )
        elif (
            min(
                instant(ctx.deadline),
                instant(run.payload["budget"]["deadline"]),
                instant(ledger.payload["deadline"]),
            )
            <= execution_segments.utcnow()
        ):
            raise reject(
                "execution_deadline_expired", "Execution deadline has passed", 409, "timeout"
            )
