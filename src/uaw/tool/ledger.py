"""Durable tool phases using existing named wire contracts, never an Object blob.

Namespace membership is the phase marker. Each row retains its original schema.
All transactions are short: no reader, approval, budget or executor call under lock.
"""

import json
from datetime import UTC, datetime
from typing import Any

from uaw.infrastructure.db.records import PostgresRecordStore, parameter_hash
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore, reference
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing
from uaw.tool.errors import fail
from uaw.tool.schema import canonical, digest

Payload = dict[str, Any]
PHASE_SCHEMAS = {
    "tool.approval.requests": "ApprovalCreateRequest",
    "tool.attempt.estimates": "ResourceVector",
    "tool.budget.reserve.plans": "BudgetReserveRequest",
    "tool.budget.reserved": "BudgetReservation",
    "tool.budget.release.refs": "Ref",
    "tool.budget.released": "BudgetReservation",
    "tool.budget.dispatched": "Acknowledgement",
    "tool.budget.settle.plans": "BudgetSettleRequest",
    "tool.budget.unknown.settled": "UsageSettlement",
    "tool.reconciliation.budget.plans": "BudgetSettleRequest",
    "tool.reconciliation.failures": "Failure",
    "tool.invocation.receipts": "ProviderReceipt",
}


def stable_context(ctx: TrustedExecutionContext) -> Payload:
    return ctx.model_dump(
        mode="json",
        exclude={"attempt_id", "trace_id", "deadline", "budget_reservation_ref"},
        exclude_unset=True,
    )


def action_key(ctx: TrustedExecutionContext, action_id: str) -> str:
    if not ctx.run_id:
        raise fail(
            "dependency_unavailable",
            "A trusted Run is required",
            phase="identity",
            category="dependency",
            status=503,
        )
    validate_contract("ID", action_id)
    return "tool-" + parameter_hash({"run_id": ctx.run_id, "action_id": action_id})


async def optional(tx: RecordTransaction, namespace: str, key: str) -> Payload | None:
    try:
        return dict((await tx.load(namespace, key)).payload)
    except StoreMissing:
        return None


async def immutable(
    tx: RecordTransaction, namespace: str, key: str, schema: str, payload: Payload
) -> Payload:
    previous = await optional(tx, namespace, key)
    if previous is not None:
        if previous != payload:
            raise fail(
                "action_conflict",
                "Persisted tool phase inputs changed",
                phase="repository",
                category="conflict",
                status=409,
            )
        return previous
    await tx.write(namespace, key, schema, payload)
    return payload


class ToolLedger:
    def __init__(self, store: PostgresRecordStore) -> None:
        self.store = store
        self.transactions = TransactionalStore(store.database)

    @staticmethod
    def aggregate(ctx: TrustedExecutionContext) -> str:
        if not ctx.run_id:
            raise fail(
                "dependency_unavailable",
                "A trusted Run is required",
                phase="identity",
                category="dependency",
                status=503,
            )
        return "tool-run:" + ctx.run_id

    async def get(self, namespace: str, key: str, ctx: TrustedExecutionContext) -> Payload | None:
        if not namespace.startswith("tool."):
            raise fail(
                "phase_schema_invalid",
                "Tool reads cannot access another owner's namespace",
                phase="repository",
            )
        try:
            return dict((await self.store.get(ctx.principal, namespace, key)).payload)
        except StoreMissing:
            return None

    async def save(
        self, namespace: str, key: str, schema: str, payload: Payload, ctx: TrustedExecutionContext
    ) -> Payload:
        if PHASE_SCHEMAS.get(namespace) != schema:
            raise fail(
                "phase_schema_invalid",
                "Unknown tool phase or incorrect named DTO",
                phase="repository",
            )
        payload = json.loads(canonical(payload))

        async def write(tx: RecordTransaction) -> Payload:
            return await immutable(tx, namespace, key, schema, payload)

        return await self.transactions.inspect(ctx.principal, self.aggregate(ctx), write)

    async def bind(self, call: Payload, spec: Payload, ctx: TrustedExecutionContext) -> str:
        validate_contract("ValidatedCall", call)
        validate_contract("ToolSpec", spec)
        if call["arguments_hash"] != digest(call["arguments"]):
            raise fail(
                "action_conflict",
                "Arguments hash differs from fixed parameters",
                phase="identity",
                category="conflict",
                status=409,
            )
        key = action_key(ctx, call["action_id"])
        # Avoid caller-owned dicts changing while a SQL operation yields.
        call, spec = json.loads(canonical(call)), json.loads(canonical(spec))
        if (call["tool_ref"]["id"], call["tool_ref"]["version"]) != (spec["id"], spec["version"]):
            raise fail(
                "action_conflict",
                "Call and ToolSpec versions differ",
                phase="identity",
                category="conflict",
                status=409,
            )

        async def write(tx: RecordTransaction) -> Payload:
            run = (await tx.load("runs", ctx.run_id or "")).payload
            binding = (await tx.load("run.bindings", ctx.run_id or "")).payload
            if (
                run["conversation_id"] != ctx.conversation_id
                or run["conversation_id"] != ctx.scope.conversation_id
                or run["task_id"] != ctx.task_id
                or run["task_id"] != ctx.scope.task_id
                or ctx.scope.project_id is not None
                or ctx.model_policy_ref is None
                or ctx.model_policy_ref.wire() != binding["model_policy_ref"]
            ):
                raise fail(
                    "permission_denied",
                    "Tool context differs from the admitted Run",
                    phase="identity",
                    category="authorization",
                    status=403,
                )
            await immutable(tx, "tool.calls", key, "ValidatedCall", call)
            await immutable(tx, "tool.specs", key, "ToolSpec", spec)
            previous = await optional(tx, "tool.contexts", key)
            if previous:
                pinned = TrustedExecutionContext.model_validate_json(json.dumps(previous))
                if stable_context(pinned) != stable_context(ctx) or datetime.fromisoformat(
                    ctx.deadline.replace("Z", "+00:00")
                ) > datetime.fromisoformat(pinned.deadline.replace("Z", "+00:00")):
                    raise fail(
                        "action_conflict",
                        "Action context or deadline changed",
                        phase="identity",
                        category="conflict",
                        status=409,
                    )
            else:
                await tx.write("tool.contexts", key, "TrustedExecutionContext", ctx.wire())
                await tx.write(
                    "tool.effects",
                    key,
                    "EffectRecord",
                    {
                        "action_id": call["action_id"],
                        "arguments_hash": call["arguments_hash"],
                        "provider_ref": spec["provider_ref"],
                        "attempt_ids": [],
                        "state": "pending",
                        "revision": 1,
                    },
                )
            # Attempt ID is unique within this principal across Runs and actions.
            await immutable(tx, "tool.attempt.calls", ctx.attempt_id, "ValidatedCall", call)
            await immutable(
                tx, "tool.attempt.contexts", ctx.attempt_id, "TrustedExecutionContext", ctx.wire()
            )
            return {"key": key}

        return str(
            (await self.transactions.inspect(ctx.principal, "tool-identities", write))["key"]
        )

    async def action(
        self, action_id: str, ctx: TrustedExecutionContext
    ) -> tuple[Payload, Payload, TrustedExecutionContext]:
        key = action_key(ctx, action_id)
        call = (await self.store.get(ctx.principal, "tool.calls", key)).payload
        spec = (await self.store.get(ctx.principal, "tool.specs", key)).payload
        original = (await self.store.get(ctx.principal, "tool.contexts", key)).payload
        pinned = TrustedExecutionContext.model_validate_json(json.dumps(original))
        if stable_context(ctx) != stable_context(pinned) or datetime.fromisoformat(
            ctx.deadline.replace("Z", "+00:00")
        ) > datetime.fromisoformat(pinned.deadline.replace("Z", "+00:00")):
            raise fail(
                "action_conflict",
                "Action context changed",
                phase="identity",
                category="conflict",
                status=409,
            )
        return dict(call), dict(spec), pinned

    async def attempt(self, ctx: TrustedExecutionContext) -> Payload:
        original = (
            await self.store.get(ctx.principal, "tool.attempt.contexts", ctx.attempt_id)
        ).payload
        if original != ctx.wire():
            raise fail(
                "action_conflict",
                "Attempt context changed",
                phase="identity",
                category="conflict",
                status=409,
            )
        return dict(
            (await self.store.get(ctx.principal, "tool.attempt.calls", ctx.attempt_id)).payload
        )

    async def effect(self, action_id: str, ctx: TrustedExecutionContext) -> Payload:
        await self.action(action_id, ctx)
        return dict(
            (
                await self.store.get(ctx.principal, "tool.effects", action_key(ctx, action_id))
            ).payload
        )

    async def claim(
        self,
        intent: Payload,
        ctx: TrustedExecutionContext,
        *,
        budget: Payload,
        reservation: Payload,
    ) -> bool:
        """Record one send intent, never send. Ambiguous claims are irrevocably unknown.

        Internal composition must do live approval/resource checks first. MS-T2a
        has no executor and does not call this from its public invoke boundary.
        """
        validate_contract("InternalToolInvocationDispatchRequest", intent)
        validate_contract("RootBudgetLedger", budget)
        validate_contract("BudgetReservation", reservation)
        call = await self.attempt(ctx)
        key = action_key(ctx, call["action_id"])
        intent = json.loads(canonical(intent))

        async def write(tx: RecordTransaction) -> Payload:
            run = (await tx.load("runs", ctx.run_id or "")).payload
            ledger = budget
            if ledger["cancel_requested"] or run["status"] not in (
                "preparing",
                "running",
                "verifying",
            ):
                raise fail(
                    "cancelled",
                    "Run no longer accepts dispatch",
                    phase="dispatch",
                    category="cancelled",
                )
            if await optional(tx, "tool.budget.release.refs", ctx.attempt_id):
                raise fail(
                    "attempt_released",
                    "Release intent blocks dispatch",
                    phase="dispatch",
                    category="conflict",
                    status=409,
                )
            fixed = (await tx.load("tool.specs", key)).payload
            existing = await optional(tx, "tool.dispatch.intents", key)
            if existing:
                if existing != intent:
                    raise fail(
                        "unknown_effect",
                        "Action already has an unresolved dispatch intent",
                        phase="dispatch",
                        category="unknown_effect",
                        status=409,
                    )
                return {"claimed": False}
            if (
                intent["validated_action_ref"] != reference("tool_call", key)
                or intent["provider_binding_ref"] != fixed["provider_ref"]
                or intent["reservation_ref"]
                != reference("reservation", reservation["id"], reservation["revision"])
                or ledger["run_id"] != ctx.run_id
                or reservation["status"] != "reserved"
            ):
                raise fail(
                    "dispatch_binding_stale",
                    "Dispatch state differs from its read port",
                    phase="dispatch",
                    category="conflict",
                    status=412,
                )
            if min(
                datetime.fromisoformat(s.replace("Z", "+00:00"))
                for s in (ctx.deadline, ledger["deadline"])
            ) <= datetime.now(UTC):
                raise fail(
                    "deadline_exceeded",
                    "Dispatch deadline expired",
                    phase="dispatch",
                    category="timeout",
                )
            effect = await tx.load("tool.effects", key)
            if effect.payload["state"] != "pending" or effect.payload["attempt_ids"]:
                raise fail(
                    "unknown_effect",
                    "Action effects require reconciliation",
                    phase="dispatch",
                    category="unknown_effect",
                    status=409,
                )
            await tx.write(
                "tool.dispatch.intents", key, "InternalToolInvocationDispatchRequest", intent
            )
            await tx.write(
                "tool.effects",
                key,
                "EffectRecord",
                {
                    **effect.payload,
                    "attempt_ids": [ctx.attempt_id],
                    "state": "unknown",
                    "revision": effect.revision + 1,
                },
                effect.revision,
            )
            return {"claimed": True}

        return bool(
            (await self.transactions.inspect(ctx.principal, self.aggregate(ctx), write))["claimed"]
        )

    async def acknowledge(self, receipt: Payload, ctx: TrustedExecutionContext) -> Payload:
        """Keep the actual first accounting receipt; do not rewrite replay status."""
        validate_contract("Acknowledgement", receipt)

        async def write(tx: RecordTransaction) -> Payload:
            previous = await optional(tx, "tool.budget.dispatched", ctx.attempt_id)
            if previous is not None:
                if {k: v for k, v in previous.items() if k != "status"} != {
                    k: v for k, v in receipt.items() if k != "status"
                }:
                    raise fail(
                        "action_conflict",
                        "Dispatch acknowledgement changed",
                        phase="repository",
                        category="conflict",
                        status=409,
                    )
                return previous
            await tx.write("tool.budget.dispatched", ctx.attempt_id, "Acknowledgement", receipt)
            return receipt

        return await self.transactions.inspect(ctx.principal, self.aggregate(ctx), write)

    async def effect_from_attempt(self, ctx: TrustedExecutionContext) -> Payload:
        call = await self.attempt(ctx)
        return await self.effect(call["action_id"], ctx)

    @staticmethod
    def receipt_key(receipt: Payload) -> str:
        ref = receipt["receipt_ref"]
        # Same version with a changed hash/location/body conflicts, not a new invoice.
        return "receipt-" + parameter_hash({k: ref[k] for k in ("kind", "id", "version")})

    async def begin_reconciliation(
        self, receipt: Payload, ctx: TrustedExecutionContext, expected_revision: int
    ) -> Payload:
        validate_contract("ToolReconciliationReceipt", receipt)
        receipt = json.loads(canonical(receipt))
        call = await self.attempt(ctx)
        key, action = self.receipt_key(receipt), action_key(ctx, call["action_id"])

        async def write(tx: RecordTransaction) -> Payload:
            fixed = (await tx.load("tool.specs", action)).payload
            effect = await tx.load("tool.effects", action)
            if (
                receipt["action_ref"] != reference("tool_call", action)
                or receipt["provider_ref"] != fixed["provider_ref"]
                or receipt["attempt_id"] != ctx.attempt_id
                or receipt["usage"]["attempt_id"] != ctx.attempt_id
                or ctx.attempt_id not in effect.payload["attempt_ids"]
                or await optional(tx, "tool.dispatch.intents", action) is None
            ):
                raise fail(
                    "receipt_binding_conflict",
                    "Receipt does not match a persisted send intent",
                    phase="reconcile",
                    category="conflict",
                    status=409,
                )
            previous = await optional(tx, "tool.reconciliation.receipts", key)
            if previous is not None:
                if previous != receipt:
                    raise fail(
                        "receipt_conflict",
                        "Pinned receipt version changed its contents",
                        phase="reconcile",
                        category="conflict",
                        status=409,
                    )
                done = await optional(tx, "tool.reconciliation.settled", key)
                active = await optional(tx, "tool.reconciliation.active", ctx.attempt_id)
                if done is None and active is not None and self.receipt_key(active) != key:
                    raise fail(
                        "receipt_version_stale",
                        "This unfinished receipt was superseded by later evidence",
                        phase="reconcile",
                        category="conflict",
                        status=412,
                    )
                return {"key": key, "settlement": done}
            if effect.revision != expected_revision:
                raise fail(
                    "revision_conflict",
                    "Effect revision changed before reconciliation",
                    phase="reconcile",
                    category="conflict",
                    status=409,
                )
            active = await optional(tx, "tool.reconciliation.active", ctx.attempt_id)
            reuse = None
            if active is not None:
                active_key = self.receipt_key(active)
                done = await optional(tx, "tool.reconciliation.settled", active_key)
                rejected = await optional(tx, "tool.reconciliation.failures", active_key)
                if done is None and rejected is None:
                    raise fail(
                        "reconciliation_pending",
                        "Previous fixed accounting plan needs recovery",
                        phase="reconcile",
                        category="conflict",
                        status=409,
                    )
                if active["outcome"] != "unknown" and active["outcome"] != receipt["outcome"]:
                    raise fail(
                        "receipt_conflict",
                        "A deterministic outcome cannot be reversed",
                        phase="reconcile",
                        category="conflict",
                        status=409,
                    )
                if datetime.fromisoformat(
                    receipt["observed_at"].replace("Z", "+00:00")
                ) < datetime.fromisoformat(active["observed_at"].replace("Z", "+00:00")):
                    raise fail(
                        "receipt_version_stale",
                        "New evidence predates the accepted observation",
                        phase="reconcile",
                        category="conflict",
                        status=412,
                    )
                if done is not None and active["usage"] == receipt["usage"]:
                    reuse = done
            else:
                # Bridge accepted MS-T2a pending accounting without charging it twice.
                old = await optional(tx, "tool.budget.unknown.settled", ctx.attempt_id)
                if old is not None:
                    for index in range(4):
                        plan_key = "plan-" + parameter_hash(
                            {"attempt": ctx.attempt_id, "index": index}
                        )
                        plan = await optional(tx, "tool.budget.settle.plans", plan_key)
                        if plan and plan["usage"] == receipt["usage"]:
                            reuse = old
                            break
            await tx.write(
                "tool.reconciliation.receipts", key, "ToolReconciliationReceipt", receipt
            )
            if active is None:
                await tx.write(
                    "tool.reconciliation.active",
                    ctx.attempt_id,
                    "ToolReconciliationReceipt",
                    receipt,
                )
            else:
                row = await tx.load("tool.reconciliation.active", ctx.attempt_id)
                await tx.write(
                    "tool.reconciliation.active",
                    ctx.attempt_id,
                    "ToolReconciliationReceipt",
                    receipt,
                    row.revision,
                )
            # Effect knowledge is independent of the subsequent fee service call.
            value = {
                **effect.payload,
                "revision": effect.revision + 1,
                "receipt_ref": receipt["receipt_ref"],
                "state": "unknown" if receipt["outcome"] == "unknown" else "confirmed",
            }
            await tx.write("tool.effects", action, "EffectRecord", value, effect.revision)
            return {"key": key, "settlement": reuse}

        return await self.transactions.inspect(ctx.principal, self.aggregate(ctx), write)

    async def finish_reconciliation(
        self, receipt: Payload, settlement: Payload, ctx: TrustedExecutionContext
    ) -> None:
        validate_contract("UsageSettlement", settlement)
        key = self.receipt_key(receipt)

        async def write(tx: RecordTransaction) -> Payload:
            stored = await tx.load("tool.reconciliation.receipts", key)
            if stored.payload != receipt:
                raise fail(
                    "receipt_conflict",
                    "Cannot finalize another receipt",
                    phase="reconcile",
                    category="conflict",
                    status=409,
                )
            return await immutable(
                tx, "tool.reconciliation.settled", key, "UsageSettlement", settlement
            )

        await self.transactions.inspect(ctx.principal, self.aggregate(ctx), write)
