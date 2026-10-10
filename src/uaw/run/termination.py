"""Independent failure/cancellation commit; unknown sends remain unresolved."""

from decimal import Decimal
from typing import Any

from sqlalchemy import select

from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore, timestamp
from uaw.run.jobs import JOBS
from uaw.shared.contracts import Principal
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing


class RunTerminationController:
    def __init__(self, records: PostgresRecordStore) -> None:
        self.records = records
        self.transactions = TransactionalStore(records.database)

    async def settle(self, actor: Principal, run_id: str) -> None:
        initial = (await self.records.get(actor, "runs", run_id)).payload

        async def write(tx: RecordTransaction) -> dict[str, Any]:
            job = (await tx.load(JOBS, run_id)).payload
            validate_contract("BackgroundRunJob", job)
            if job["principal"] != actor.wire() or job["state"] != "blocked":
                raise reject(
                    "termination_original_job_required", "Stopped original job required", 403
                )
            run = await tx.load("runs", run_id)
            if run.payload["status"] in ("completed", "failed", "cancelled"):
                return {}
            ledger = await tx.load("budget.ledgers", run_id)
            if any(
                Decimal(str(value)) != 0
                for key, value in ledger.payload["held"].items()
                if key not in ("currency", "money")
            ):
                return {}  # Preserve actual pending reservations and cancellation intent.
            unresolved = await tx.session.scalar(
                select(RecordRow.resource_id)
                .where(
                    RecordRow.principal_id == actor.id,
                    RecordRow.namespace == "model.invocations",
                    RecordRow.deleted.is_(False),
                    RecordRow.payload["run_id"].as_string() == run_id,
                    (RecordRow.payload["state"].as_string() != "finished")
                    | (
                        RecordRow.payload["result"]["failure"]["category"].as_string()
                        == "unknown_effect"
                    ),
                )
                .limit(1)
            )
            if unresolved:
                return {}
            contexts = list(
                await tx.session.scalars(
                    select(RecordRow).where(
                        RecordRow.principal_id == actor.id,
                        RecordRow.namespace == "tool.contexts",
                        RecordRow.deleted.is_(False),
                        RecordRow.payload["run_id"].as_string() == run_id,
                    )
                )
            )
            for context in contexts:
                try:
                    await tx.load("tool.dispatch.intents", context.resource_id)
                except StoreMissing:
                    continue
                effect = await tx.load("tool.effects", context.resource_id)
                if effect.payload["state"] != "confirmed":
                    return {}
            accounts = list(
                await tx.session.scalars(
                    select(RecordRow).where(
                        RecordRow.principal_id == actor.id,
                        RecordRow.namespace == "budget.accounting",
                        RecordRow.deleted.is_(False),
                        RecordRow.payload["run_id"].as_string() == run_id,
                    )
                )
            )
            for account in accounts:
                reservation = await tx.load("budget.reservations", account.resource_id)
                if reservation.payload["status"] not in (
                    "settled",
                    "partially_settled",
                    "released",
                ):
                    return {}
            failure = job.get("failure")
            cancelled = ledger.payload["cancel_requested"]
            if not cancelled and (not failure or failure["category"] == "unknown_effect"):
                return {}
            target = "cancelled" if cancelled else "failed"
            value = {
                **run.payload,
                "revision": run.revision + 1,
                "status": target,
                "outcome": target,
                "ended_at": timestamp(),
            }
            await tx.write("runs", run_id, "RunRecord", value, run.revision)
            task = await tx.load("tasks", run.payload["task_id"])
            changed = {
                **task.payload,
                "revision": task.revision + 1,
                "active_run_refs": [
                    r for r in task.payload["active_run_refs"] if r["id"] != run_id
                ],
            }
            await tx.write("tasks", task.resource_id, "TaskRecord", changed, task.revision)
            await tx.emit(
                run.payload["conversation_id"],
                "run.updated",
                value,
                base_revision=run.revision - 1,
                result_revision=run.revision,
            )
            return {}

        await self.transactions.inspect(actor, "conversation:" + initial["conversation_id"], write)
