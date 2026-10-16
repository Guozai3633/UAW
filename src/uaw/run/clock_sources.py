"""Actual Run-owned effect inventory used before any idle pause."""

from decimal import Decimal

from sqlalchemy import select

from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.transactions import RecordTransaction
from uaw.shared.contracts import Principal
from uaw.shared.errors import reject
from uaw.shared.stores import StoreMissing


class RunIdleEffects:
    async def check(self, tx: RecordTransaction, actor: Principal, run_id: str) -> None:
        if actor.kind != "user" or tx.owner != actor.id:
            raise reject("conversation_idle_denied", "Original user transaction required", 403)
        run = await tx.load("runs", run_id)
        conversation = await tx.load("conversations", run.payload["conversation_id"])
        ledger = await tx.load("budget.ledgers", run_id)
        if conversation.payload["owner_id"] != actor.id or ledger.payload["run_id"] != run_id:
            raise reject("conversation_idle_denied", "Effect inventory owner differs", 403)
        if ledger.payload["cancel_requested"] or ledger.payload["overdrawn"]:
            raise reject("conversation_stopped", "Task cancelled or budget exceeded", 409)
        if any(
            Decimal(str(value)) != 0
            for key, value in ledger.payload["held"].items()
            if key not in ("currency", "money")
        ):
            raise reject("conversation_effect_pending", "Executable budget remains reserved", 409)

        async def rows(namespace: str) -> list[RecordRow]:
            return list(
                await tx.session.scalars(
                    select(RecordRow).where(
                        RecordRow.principal_id == actor.id,
                        RecordRow.namespace == namespace,
                        RecordRow.deleted.is_(False),
                        RecordRow.payload["run_id"].as_string() == run_id,
                    )
                )
            )

        for row in await rows("model.invocations"):
            if (
                row.payload["state"] != "finished"
                or row.payload.get("result", {}).get("failure", {}).get("category")
                == "unknown_effect"
            ):
                raise reject("conversation_effect_pending", "Original model effect unresolved", 409)
        for row in await rows("tool.contexts"):
            try:
                await tx.load("tool.dispatch.intents", row.resource_id)
            except StoreMissing:
                continue
            effect = await tx.load("tool.effects", row.resource_id)
            if effect.payload["state"] != "confirmed":
                raise reject("conversation_effect_pending", "Original tool effect unresolved", 409)
        for row in await rows("budget.accounting"):
            reservation = await tx.load("budget.reservations", row.resource_id)
            if reservation.payload["status"] not in ("settled", "partially_settled", "released"):
                raise reject(
                    "conversation_effect_pending", "Original reservation remains executable", 409
                )
