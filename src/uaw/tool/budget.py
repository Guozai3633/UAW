"""Recoverable BudgetPort steps. No service call while a tool SQL lock is held.

Plans and receipts use existing BudgetReserveRequest/BudgetReservation/Ref/etc.
CAS retries use new immutable plans only after a definite conflict, never on timeout.
Unknown send intent prevents its own release and any new write attempt.
"""

import json
from typing import Any

from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.db.transactions import RecordTransaction, reference
from uaw.shared.contracts import RequestMeta, TrustedExecutionContext
from uaw.shared.ports import BudgetPort, BudgetStatePort
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreConflict, StoreMissing
from uaw.tool.approval import ToolApprovalAdapter
from uaw.tool.errors import fail, validate_dependency
from uaw.tool.ledger import ToolLedger, action_key
from uaw.tool.schema import canonical

Payload = dict[str, Any]


def step_meta(step: str, key: str) -> RequestMeta:
    return RequestMeta(
        request_id="tool-budget-" + parameter_hash({"step": step, "key": key}), schema_version="0.1"
    )


class ToolBudgetAdapter:
    def __init__(
        self,
        ledger: ToolLedger,
        budgets: BudgetPort,
        approvals: ToolApprovalAdapter | None = None,
        *,
        state: BudgetStatePort | None = None,
    ) -> None:
        self.ledger, self.budgets, self.approvals, self.state = ledger, budgets, approvals, state

    async def _authorize(self, ctx: TrustedExecutionContext) -> None:
        if self.approvals is None:
            raise fail(
                "dependency_unavailable",
                "Live approval authority is not wired",
                phase="budget",
                category="dependency",
                status=503,
            )
        await self.approvals.require_approved(ctx)

    async def reserve(self, estimates: Payload, ctx: TrustedExecutionContext) -> Payload:
        validate_contract("ResourceVector", estimates)
        await self._authorize(ctx)
        call = await self.ledger.attempt(ctx)
        effect = await self.ledger.effect(call["action_id"], ctx)
        if effect["attempt_ids"]:
            raise fail(
                "unknown_effect",
                "Action already has a send intent; no new attempt reserved",
                phase="reserve",
                category="unknown_effect",
                status=409,
            )
        pinned = await self.ledger.save(
            "tool.attempt.estimates", ctx.attempt_id, "ResourceVector", estimates, ctx
        )
        previous = await self.ledger.get("tool.budget.reserved", ctx.attempt_id, ctx)
        if await self.ledger.get("tool.budget.release.refs", ctx.attempt_id, ctx):
            raise fail(
                "attempt_released",
                "Released attempt cannot reserve again",
                phase="reserve",
                category="conflict",
                status=409,
            )
        if previous:
            current = await self.get_reservation(previous["id"], ctx)
            if current["status"] != "reserved":
                raise fail(
                    "attempt_released",
                    "Attempt is no longer reserved",
                    phase="reserve",
                    category="conflict",
                    status=409,
                )
            return previous
        for index in range(4):
            key = "plan-" + parameter_hash({"attempt": ctx.attempt_id, "index": index})
            request = await self.ledger.get("tool.budget.reserve.plans", key, ctx)
            if request is None:
                ledger = await self.get_ledger(ctx)
                request = {
                    "reservation_id": "tool-reservation-"
                    + parameter_hash({"attempt": ctx.attempt_id}),
                    "parent_run_id": ctx.run_id,
                    "estimates": pinned,
                    "deadline": ctx.deadline,
                    "expected_ledger_revision": ledger["revision"],
                }
                request = await self._plan(
                    "tool.budget.reserve.plans", key, "BudgetReserveRequest", request, ctx
                )
            try:
                receipt = await self.budgets.reserve(
                    ctx.principal, request, step_meta("reserve", key), ctx
                )
                validate_dependency("BudgetReservation", receipt, "budget")
                return await self.ledger.save(
                    "tool.budget.reserved", ctx.attempt_id, "BudgetReservation", receipt, ctx
                )
            except StoreConflict as exc:
                if exc.failure.code != "revision_conflict":
                    raise
        raise fail(
            "revision_conflict",
            "Budget contention exceeded bounded recovery",
            phase="reserve",
            category="conflict",
            status=409,
        )

    async def reservation_ref(self, ctx: TrustedExecutionContext) -> Payload:
        await self.ledger.attempt(ctx)
        reservation = await self.ledger.get("tool.budget.reserved", ctx.attempt_id, ctx)
        if reservation is None:
            raise fail(
                "dependency_unavailable",
                "Attempt has no durable reservation",
                phase="budget",
                category="dependency",
                status=503,
            )
        return reference("reservation", reservation["id"], reservation["revision"])

    async def mark_dispatch(self, ctx: TrustedExecutionContext) -> bool:
        """Internal future send boundary: records intent and BudgetPort dispatch only.

        Caller must perform live ApprovalPort/Reader recheck. No executor is called.
        Returns whether this caller owns the first intent; a replay is never a send token.
        """
        await self._authorize(ctx)
        call = await self.ledger.attempt(ctx)
        _, spec, _ = await self.ledger.action(call["action_id"], ctx)
        ref = await self.reservation_ref(ctx)
        if await self.ledger.get("tool.budget.release.refs", ctx.attempt_id, ctx):
            raise fail(
                "attempt_released",
                "Release began before dispatch",
                phase="dispatch",
                category="conflict",
                status=409,
            )
        intent = {
            "validated_action_ref": reference("tool_call", action_key(ctx, call["action_id"])),
            "reservation_ref": ref,
            "provider_binding_ref": spec["provider_ref"],
        }
        budget = await self.get_ledger(ctx)
        reserved = await self.get_reservation(ref["id"], ctx)
        new = await self.ledger.claim(intent, ctx, budget=budget, reservation=reserved)
        # Crash between claim and BudgetPort.dispatch retains unknown. Recovery replays
        # only accounting with the same request ID, never the executor/send.
        if await self.ledger.get("tool.budget.dispatched", ctx.attempt_id, ctx):
            return new
        receipt = await self.budgets.dispatch(
            ctx.principal, ref, step_meta("dispatch", ctx.attempt_id), ctx
        )
        validate_dependency("Acknowledgement", receipt, "dispatch")
        if receipt["operation_id"] != ctx.operation_id or receipt["status"] not in {
            "accepted",
            "unchanged",
        }:
            raise fail(
                "dependency_protocol_invalid",
                "Budget acknowledgement differs from this attempt",
                phase="dispatch",
                category="dependency",
                status=503,
            )
        await self.ledger.acknowledge(receipt, ctx)
        return new

    async def release(self, ctx: TrustedExecutionContext) -> Payload:
        call = await self.ledger.attempt(ctx)
        effect = await self.ledger.effect(call["action_id"], ctx)
        if ctx.attempt_id in effect["attempt_ids"]:
            raise fail(
                "unknown_effect",
                "Dispatched effects/usage cannot be released",
                phase="release",
                category="unknown_effect",
                status=409,
            )
        await self.recover_reserved(ctx)
        ref = await self.reservation_ref(ctx)

        # Serializes release intent against dispatch intent, not across BudgetPort call.
        async def write(tx: RecordTransaction) -> Payload:
            from uaw.tool.ledger import immutable, optional

            intent = await optional(tx, "tool.dispatch.intents", action_key(ctx, call["action_id"]))
            if intent and intent["reservation_ref"]["id"] == ref["id"]:
                raise fail(
                    "unknown_effect",
                    "Dispatch intent blocks release",
                    phase="release",
                    category="unknown_effect",
                    status=409,
                )
            return await immutable(tx, "tool.budget.release.refs", ctx.attempt_id, "Ref", ref)

        await self.ledger.transactions.inspect(ctx.principal, self.ledger.aggregate(ctx), write)
        receipt = await self.budgets.release(
            ctx.principal, ref, step_meta("release", ctx.attempt_id), ctx
        )
        validate_dependency("BudgetReservation", receipt, "budget")
        return await self.ledger.save(
            "tool.budget.released", ctx.attempt_id, "BudgetReservation", receipt, ctx
        )

    async def settle_unknown(self, ctx: TrustedExecutionContext) -> Payload:
        """No invented measured usage. Pending billing retains all unobserved holds."""
        if await self.ledger.get("tool.reconciliation.active", ctx.attempt_id, ctx):
            raise fail(
                "reconciliation_pending",
                "This attempt now uses its trusted receipt plans",
                phase="settle",
                category="conflict",
                status=409,
            )
        call = await self.ledger.attempt(ctx)
        effect = await self.ledger.effect(call["action_id"], ctx)
        if effect["attempt_ids"] != [ctx.attempt_id] or effect["state"] != "unknown":
            raise fail(
                "unknown_effect",
                "No unresolved send intent belongs to this attempt",
                phase="settle",
                category="unknown_effect",
                status=409,
            )
        ref = await self.reservation_ref(ctx)
        estimates = await self.ledger.get("tool.attempt.estimates", ctx.attempt_id, ctx)
        assert estimates is not None
        for index in range(4):
            key = "plan-" + parameter_hash({"attempt": ctx.attempt_id, "index": index})
            request = await self.ledger.get("tool.budget.settle.plans", key, ctx)
            if request is None:
                ledger = await self.get_ledger(ctx)
                request = {
                    "reservation_ref": ref,
                    "usage": {
                        "attempt_id": ctx.attempt_id,
                        "resources": {"currency": estimates["currency"]},
                        "billing_state": "pending",
                    },
                    "expected_ledger_revision": ledger["revision"],
                }
                request = await self._plan(
                    "tool.budget.settle.plans", key, "BudgetSettleRequest", request, ctx
                )
            try:
                receipt = await self.budgets.settle(
                    ctx.principal, request, step_meta("settle-unknown", key), ctx, status="unknown"
                )
                validate_dependency("UsageSettlement", receipt, "settle")
                return await self.ledger.save(
                    "tool.budget.unknown.settled", ctx.attempt_id, "UsageSettlement", receipt, ctx
                )
            except StoreConflict as exc:
                if exc.failure.code != "revision_conflict":
                    raise
        raise fail(
            "revision_conflict",
            "Settlement contention exceeded bounded recovery",
            phase="settle",
            category="conflict",
            status=409,
        )

    async def _plan(
        self, namespace: str, key: str, schema: str, request: Payload, ctx: TrustedExecutionContext
    ) -> Payload:
        async def write(tx: RecordTransaction) -> Payload:
            from uaw.tool.ledger import optional

            previous = await optional(tx, namespace, key)
            if previous is not None:
                return previous
            value = request
            await tx.write(namespace, key, schema, value)
            return value

        return await self.ledger.transactions.inspect(
            ctx.principal, self.ledger.aggregate(ctx), write
        )

    async def recover_reserved(self, ctx: TrustedExecutionContext) -> Payload:
        """Replay only previously persisted reserve plans; never creates a new plan.

        Used to release a committed reservation after cancellation/crash. If the
        service had not committed, its current admission/deadline checks still apply.
        """
        await self.ledger.attempt(ctx)
        receipt = await self.ledger.get("tool.budget.reserved", ctx.attempt_id, ctx)
        if receipt:
            await self.get_reservation(receipt["id"], ctx)
            return receipt
        for index in range(4):
            key = "plan-" + parameter_hash({"attempt": ctx.attempt_id, "index": index})
            plan = await self.ledger.get("tool.budget.reserve.plans", key, ctx)
            if plan is None:
                break
            # Recovery must never create a reservation after policy/approval revocation.
            try:
                await self.get_reservation(plan["reservation_id"], ctx)
            except StoreMissing:
                continue
            try:
                receipt = await self.budgets.reserve(
                    ctx.principal, plan, step_meta("reserve", key), ctx
                )
                validate_dependency("BudgetReservation", receipt, "budget")
                return await self.ledger.save(
                    "tool.budget.reserved", ctx.attempt_id, "BudgetReservation", receipt, ctx
                )
            except StoreConflict as exc:
                if exc.failure.code != "revision_conflict":
                    raise
        raise fail(
            "dependency_unavailable",
            "No committed reservation could be recovered",
            phase="reserve",
            category="dependency",
            status=503,
        )

    async def get_ledger(self, ctx: TrustedExecutionContext) -> Payload:
        if self.state is None:
            raise fail(
                "dependency_unavailable",
                "Budget state port is not wired",
                phase="budget_state",
                category="dependency",
                status=503,
            )
        result = await self.state.get_ledger(ctx)
        validate_dependency("RootBudgetLedger", result, "budget_state")
        if result["run_id"] != ctx.run_id or result["id"] != ctx.run_id:
            raise fail(
                "attempt_scope_denied",
                "Budget state differs from this Run",
                phase="budget_state",
                category="authorization",
                status=403,
            )
        return json.loads(canonical(result))  # type: ignore[no-any-return]

    async def get_reservation(self, reservation_id: str, ctx: TrustedExecutionContext) -> Payload:
        if self.state is None:
            raise fail(
                "dependency_unavailable",
                "Budget state port is not wired",
                phase="budget_state",
                category="dependency",
                status=503,
            )
        result = await self.state.get_reservation(reservation_id, ctx)
        validate_dependency("BudgetReservation", result, "budget_state")
        if result["id"] != reservation_id:
            raise fail(
                "attempt_scope_denied",
                "Reservation state differs from this attempt",
                phase="budget_state",
                category="authorization",
                status=403,
            )
        return json.loads(canonical(result))  # type: ignore[no-any-return]

    async def settle_receipt(
        self, receipt: Payload, receipt_key: str, ctx: TrustedExecutionContext
    ) -> Payload:
        """Recovery of original accounting only; no live execution permission is issued."""
        await self.ledger.attempt(ctx)
        validate_contract("ToolReconciliationReceipt", receipt)
        if (
            receipt["attempt_id"] != ctx.attempt_id
            or receipt["usage"]["attempt_id"] != ctx.attempt_id
        ):
            raise fail(
                "attempt_scope_denied",
                "Receipt usage belongs to another attempt",
                phase="settle",
                category="authorization",
                status=403,
            )
        original = await self.recover_reserved(ctx)
        status = {"applied": "succeeded", "not_applied": "failed", "unknown": "unknown"}[
            receipt["outcome"]
        ]
        for index in range(4):
            key = "reconcile-plan-" + parameter_hash({"receipt": receipt_key, "index": index})
            plan = await self.ledger.get("tool.reconciliation.budget.plans", key, ctx)
            if plan is None:
                budget = await self.get_ledger(ctx)
                reservation = await self.get_reservation(original["id"], ctx)
                plan = {
                    "reservation_ref": reference(
                        "reservation", reservation["id"], reservation["revision"]
                    ),
                    "usage": receipt["usage"],
                    "expected_ledger_revision": budget["revision"],
                }
                plan = await self._plan(
                    "tool.reconciliation.budget.plans", key, "BudgetSettleRequest", plan, ctx
                )
            try:
                result: Payload = await self.budgets.settle(
                    ctx.principal, plan, step_meta("reconcile", key), ctx, status=status
                )
                validate_dependency("UsageSettlement", result, "settle")
                if (
                    result["reservation_ref"]["kind"] != "reservation"
                    or result["reservation_ref"]["id"] != plan["reservation_ref"]["id"]
                    or result["reservation_ref"]["version"]
                    != str(int(plan["reservation_ref"]["version"]) + 1)
                    or not result["usage_refs"]
                    or any(ref["kind"] != "usage" for ref in result["usage_refs"])
                ):
                    raise fail(
                        "dependency_protocol_invalid",
                        "Settlement receipt differs from the fixed attempt plan",
                        phase="settle",
                        category="dependency",
                        status=503,
                    )
                return result
            except StoreConflict as exc:
                if exc.failure.code != "revision_conflict":
                    raise
        raise fail(
            "revision_conflict",
            "Receipt accounting exceeded bounded CAS recovery",
            phase="settle",
            category="conflict",
            status=409,
        )
