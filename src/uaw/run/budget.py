"""Per-attempt quotas with atomic admission and conservative reconciliation of unknown usage."""

import hashlib
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from typing import Any

from sqlalchemy import select

from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import (
    RecordTransaction,
    TransactionalStore,
    reference,
    timestamp,
)
from uaw.run.facade import zero_resources
from uaw.shared.contracts import Principal, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreConflict

Payload = dict[str, Any]


def arithmetic(left: Payload, right: Payload, sign: int = 1) -> Payload:
    if left["currency"] != right["currency"]:
        raise reject("currency_mismatch", "Budget currency does not match", 422, "budget")
    result = {k: left[k] + sign * right[k] for k in left if k not in ("money", "currency")}
    with localcontext() as context:
        context.prec = 300
        result.update(
            money=format(Decimal(left["money"]) + sign * Decimal(right["money"]), "f"),
            currency=left["currency"],
        )
    return result


def over_limit(value: Payload, limits: Payload) -> bool:
    return any(Decimal(str(value[k])) > Decimal(str(limits[k])) for k in value if k != "currency")


def remaining(ledger: Payload) -> Payload:
    consumed = arithmetic(ledger["used"], ledger["held"])
    raw = arithmetic(ledger["limits"], consumed, -1)
    return {
        k: (
            v if k == "currency" else format(max(Decimal(v), 0), "f") if k == "money" else max(v, 0)
        )
        for k, v in raw.items()
    }


class BudgetService:
    def __init__(self, store: PostgresRecordStore) -> None:
        self.store = store
        self.transactions = TransactionalStore(store.database)

    @staticmethod
    def _context(actor: Principal, ctx: TrustedExecutionContext, run_id: str) -> None:
        if actor.id != ctx.principal.id or ctx.run_id != run_id:
            raise reject(
                "budget_scope_denied",
                "Budget execution context does not match the Run",
                403,
                "authorization",
            )

    async def _aggregate(self, actor: Principal, run_id: str) -> str:
        run = await self.store.get(actor, "runs", run_id)
        return f"conversation:{run.payload['conversation_id']}"

    async def reserve(
        self, actor: Principal, request: Payload, meta: RequestMeta, ctx: TrustedExecutionContext
    ) -> Payload:
        validate_contract("BudgetReserveRequest", request)
        run_id = request["parent_run_id"]
        self._context(actor, ctx, run_id)
        aggregate = await self._aggregate(actor, run_id)

        async def write(tx: RecordTransaction) -> Payload:
            run = await tx.load("runs", run_id)
            row = await tx.load("budget.ledgers", run_id)
            if row.revision != request["expected_ledger_revision"]:
                raise StoreConflict()
            if (
                run.payload["status"] not in ("preparing", "running", "verifying")
                or row.payload["cancel_requested"]
            ):
                raise reject(
                    "budget_admission_stopped", "Run is not accepting new actions", 409, "cancelled"
                )
            deadline = datetime.fromisoformat(request["deadline"].replace("Z", "+00:00"))
            root_deadline = datetime.fromisoformat(row.payload["deadline"].replace("Z", "+00:00"))
            ctx_deadline = datetime.fromisoformat(ctx.deadline.replace("Z", "+00:00"))
            if not datetime.now(UTC) < deadline <= min(root_deadline, ctx_deadline):
                raise reject(
                    "budget_deadline_invalid",
                    "Reservation deadline is outside the Run deadline",
                    422,
                    "budget",
                )
            estimates = request["estimates"]
            held = arithmetic(row.payload["held"], estimates)
            if row.payload["overdrawn"] or over_limit(
                arithmetic(row.payload["used"], held), row.payload["limits"]
            ):
                raise reject(
                    "budget_exhausted", "Reservation exceeds remaining resources", 409, "budget"
                )
            reservation = {
                "id": request["reservation_id"],
                "parent_ref": reference("reservation", f"root-{run_id}"),
                "estimates": estimates,
                "settled_usage_refs": [],
                "status": "reserved",
                "revision": 1,
            }
            await tx.write(
                "budget.reservations", reservation["id"], "BudgetReservation", reservation
            )
            await tx.write(
                "budget.accounting",
                reservation["id"],
                "ReservationAccounting",
                {
                    "run_id": run_id,
                    "operation_id": ctx.operation_id,
                    "trace_id": ctx.trace_id,
                    "attempt_id": ctx.attempt_id,
                    "deadline": request["deadline"],
                    "dispatched": False,
                    "held": estimates,
                    "used": zero_resources(estimates["currency"]),
                    "billing_pending": False,
                },
            )
            await tx.write(
                "budget.ledgers",
                run_id,
                "RootBudgetLedger",
                {**row.payload, "revision": row.revision + 1, "held": held},
                row.revision,
            )
            return reservation

        return await self.transactions.execute(
            actor,
            aggregate,
            meta,
            {
                "action": "budget.reserve",
                "request": request,
                "attempt_id": ctx.attempt_id,
                "operation_id": ctx.operation_id,
                "trace_id": ctx.trace_id,
            },
            write,
        )

    async def dispatch(
        self,
        actor: Principal,
        reservation_ref: Payload,
        meta: RequestMeta,
        ctx: TrustedExecutionContext,
    ) -> Payload:
        validate_contract("Ref", reservation_ref)
        if not ctx.run_id:
            raise reject("budget_context_missing", "Run context is required", 403, "authorization")
        self._context(actor, ctx, ctx.run_id)
        aggregate = await self._aggregate(actor, ctx.run_id)

        async def write(tx: RecordTransaction) -> Payload:
            row = await tx.load("budget.accounting", reservation_ref["id"])
            reservation = await tx.load("budget.reservations", reservation_ref["id"])
            self._attempt(row.payload, ctx)
            if reservation_ref["kind"] != "reservation" or reservation_ref["version"] != str(
                reservation.revision
            ):
                raise StoreConflict()
            ledger = await tx.load("budget.ledgers", ctx.run_id or "")
            run = await tx.load("runs", ctx.run_id or "")
            if ledger.payload["overdrawn"]:
                raise reject(
                    "budget_exhausted", "Run has exceeded its resource budget", 409, "budget"
                )
            if (
                ledger.payload["cancel_requested"]
                or run.payload["status"] not in ("preparing", "running", "verifying")
                or datetime.fromisoformat(ledger.payload["deadline"].replace("Z", "+00:00"))
                <= datetime.now(UTC)
            ):
                raise reject(
                    "budget_admission_stopped", "Run no longer permits dispatch", 409, "cancelled"
                )
            if datetime.fromisoformat(
                row.payload["deadline"].replace("Z", "+00:00")
            ) <= datetime.now(UTC):
                raise reject(
                    "reservation_expired", "Reservation deadline has passed", 409, "timeout"
                )
            if row.payload["dispatched"] or reservation.payload["status"] != "reserved":
                raise reject(
                    "attempt_already_dispatched",
                    "Attempt already has a dispatch intent",
                    409,
                    "conflict",
                )
            await tx.write(
                "budget.accounting",
                row.resource_id,
                "ReservationAccounting",
                {**row.payload, "dispatched": True, "billing_pending": True},
                row.revision,
            )
            await tx.write(
                "budget.ledgers",
                ledger.resource_id,
                "RootBudgetLedger",
                {**ledger.payload, "revision": ledger.revision + 1, "billing_pending": True},
                ledger.revision,
            )
            return {"operation_id": ctx.operation_id, "status": "accepted"}

        return await self.transactions.execute(
            actor,
            aggregate,
            meta,
            {
                "action": "budget.dispatch",
                "reservation_ref": reservation_ref,
                "attempt_id": ctx.attempt_id,
            },
            write,
            on_replay=lambda previous: {**previous, "status": "unchanged"},
        )

    @staticmethod
    def _attempt(account: Payload, ctx: TrustedExecutionContext) -> None:
        if any(
            account[k] != getattr(ctx, k)
            for k in ("run_id", "operation_id", "trace_id", "attempt_id")
        ):
            raise reject(
                "attempt_scope_denied",
                "Attempt does not own this reservation",
                403,
                "authorization",
            )

    async def settle(
        self,
        actor: Principal,
        request: Payload,
        meta: RequestMeta,
        ctx: TrustedExecutionContext,
        *,
        status: str,
    ) -> Payload:
        validate_contract("BudgetSettleRequest", request)
        if not ctx.run_id or status not in ("succeeded", "failed", "cancelled", "unknown"):
            raise reject(
                "usage_context_invalid", "Usage requires a Run and an actual attempt outcome"
            )
        self._context(actor, ctx, ctx.run_id)
        if request["usage"]["attempt_id"] != ctx.attempt_id:
            raise reject(
                "attempt_scope_denied",
                "Usage attempt does not match its context",
                403,
                "authorization",
            )
        aggregate = await self._aggregate(actor, ctx.run_id)

        async def write(tx: RecordTransaction) -> Payload:
            ref = request["reservation_ref"]
            reservation = await tx.load("budget.reservations", ref["id"])
            account = await tx.load("budget.accounting", ref["id"])
            self._attempt(account.payload, ctx)
            ledger = await tx.load("budget.ledgers", ctx.run_id or "")
            if (
                ref["kind"] != "reservation"
                or ref["version"] != str(reservation.revision)
                or ledger.revision != request["expected_ledger_revision"]
            ):
                raise StoreConflict()
            if not account.payload["dispatched"] or reservation.payload["status"] not in (
                "reserved",
                "partially_settled",
            ):
                raise reject(
                    "usage_settlement_denied",
                    "Reservation has no pending dispatched attempt",
                    409,
                    "conflict",
                )
            usage = request["usage"]
            if "usage" in account.payload and usage["billing_state"] != "confirmed":
                raise reject(
                    "usage_reconciliation_denied",
                    "Pending usage can only be reconciled to confirmed usage",
                    409,
                    "conflict",
                )
            if "usage" in account.payload:
                previous_resources = account.payload["usage"]["resources"]
                if any(
                    key in previous_resources and measured_value < previous_resources[key]
                    for key, measured_value in usage["resources"].items()
                    if key not in ("money", "currency")
                ):
                    raise reject(
                        "usage_decreased",
                        "Confirmed usage cannot erase observed resources",
                        409,
                        "budget",
                    )
            measured = usage["resources"]
            estimates = reservation.payload["estimates"]
            if measured["currency"] != estimates["currency"]:
                raise reject(
                    "currency_mismatch",
                    "Usage currency does not match the reservation",
                    422,
                    "budget",
                )
            known = zero_resources(estimates["currency"])
            hold = zero_resources(estimates["currency"])
            for key in known:
                if key == "currency":
                    continue
                if key in measured and (key != "money" or usage["billing_state"] == "confirmed"):
                    known[key] = measured[key]
                else:
                    hold[key] = estimates[key]
                    if key == "money" and key in measured:
                        hold[key] = format(
                            max(Decimal(estimates[key]), Decimal(measured[key])), "f"
                        )
            pending = usage["billing_state"] != "confirmed"
            used = arithmetic(
                arithmetic(ledger.payload["used"], account.payload["used"], -1), known
            )
            held = arithmetic(arithmetic(ledger.payload["held"], account.payload["held"], -1), hold)
            usage_id = "usage-" + hashlib.sha256(ctx.attempt_id.encode()).hexdigest()
            usage_revision = account.payload.get("usage_revision", 0) + 1
            await tx.write("usage", usage_id, "Usage", usage, usage_revision - 1)
            usage_ref = reference("usage", usage_id, usage_revision)
            await tx.write(
                "budget.accounting",
                ref["id"],
                "ReservationAccounting",
                {
                    **account.payload,
                    "used": known,
                    "held": hold,
                    "billing_pending": pending,
                    "usage": usage,
                    "usage_revision": usage_revision,
                },
                account.revision,
            )
            accounts = (
                await tx.session.scalars(
                    select(RecordRow).where(
                        RecordRow.principal_id == actor.id,
                        RecordRow.namespace == "budget.accounting",
                        RecordRow.payload["run_id"].astext == ctx.run_id,
                    )
                )
            ).all()
            value = {
                **ledger.payload,
                "revision": ledger.revision + 1,
                "used": used,
                "held": held,
                "billing_pending": any(a.payload["billing_pending"] for a in accounts),
                "overdrawn": over_limit(arithmetic(used, held), ledger.payload["limits"]),
            }
            await tx.write(
                "budget.ledgers", ledger.resource_id, "RootBudgetLedger", value, ledger.revision
            )
            updated = {
                **reservation.payload,
                "revision": reservation.revision + 1,
                "status": "partially_settled" if pending else "settled",
                "settled_usage_refs": [usage_ref],
            }
            await tx.write(
                "budget.reservations", ref["id"], "BudgetReservation", updated, reservation.revision
            )
            trace = {
                "operation_id": ctx.operation_id,
                "trace_id": ctx.trace_id,
                "attempt_id": ctx.attempt_id,
                "run_id": ctx.run_id,
                "reservation_ref": reference("reservation", ref["id"], updated["revision"]),
                "status": status,
                "usage_ref": usage_ref,
                "created_at": timestamp(),
            }
            await tx.write("traces", ctx.attempt_id, "AttemptTrace", trace, usage_revision - 1)
            return {
                "reservation_ref": reference("reservation", ref["id"], updated["revision"]),
                "usage_refs": [usage_ref],
                "remaining": remaining(value),
                "revision": value["revision"],
                "billing_pending": value["billing_pending"],
            }

        return await self.transactions.execute(
            actor,
            aggregate,
            meta,
            {
                "action": "budget.settle",
                "request": request,
                "status": status,
                "operation_id": ctx.operation_id,
                "trace_id": ctx.trace_id,
            },
            write,
        )

    async def release(
        self,
        actor: Principal,
        reservation_ref: Payload,
        meta: RequestMeta,
        ctx: TrustedExecutionContext,
    ) -> Payload:
        if not ctx.run_id:
            raise reject("budget_context_missing", "Run context is required", 403, "authorization")
        self._context(actor, ctx, ctx.run_id)
        aggregate = await self._aggregate(actor, ctx.run_id)

        async def write(tx: RecordTransaction) -> Payload:
            reservation = await tx.load("budget.reservations", reservation_ref["id"])
            account = await tx.load("budget.accounting", reservation_ref["id"])
            self._attempt(account.payload, ctx)
            if reservation_ref["kind"] != "reservation" or reservation_ref["version"] != str(
                reservation.revision
            ):
                raise StoreConflict()
            if account.payload["dispatched"] or reservation.payload["status"] != "reserved":
                raise reject(
                    "unknown_usage_held",
                    "Dispatched or unresolved usage cannot be released",
                    409,
                    "budget",
                )
            ledger = await tx.load("budget.ledgers", ctx.run_id or "")
            await tx.write(
                "budget.ledgers",
                ledger.resource_id,
                "RootBudgetLedger",
                {
                    **ledger.payload,
                    "revision": ledger.revision + 1,
                    "held": arithmetic(ledger.payload["held"], account.payload["held"], -1),
                },
                ledger.revision,
            )
            await tx.write(
                "budget.accounting",
                account.resource_id,
                "ReservationAccounting",
                {**account.payload, "held": zero_resources(account.payload["held"]["currency"])},
                account.revision,
            )
            value = {
                **reservation.payload,
                "status": "released",
                "revision": reservation.revision + 1,
            }
            await tx.write(
                "budget.reservations",
                reservation.resource_id,
                "BudgetReservation",
                value,
                reservation.revision,
            )
            return value

        return await self.transactions.execute(
            actor,
            aggregate,
            meta,
            {"action": "budget.release", "ref": reservation_ref, "attempt_id": ctx.attempt_id},
            write,
        )
