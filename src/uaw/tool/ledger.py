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

    async def claim(self, intent: Payload, ctx: TrustedExecutionContext) -> bool:
        """Record one send intent, never send. Ambiguous claims are irrevocably unknown.

        Internal composition must do live approval/resource checks first. MS-T2a
        has no executor and does not call this from its public invoke boundary.
        """
        validate_contract("InternalToolInvocationDispatchRequest", intent)
        call = await self.attempt(ctx)
        key = action_key(ctx, call["action_id"])
        intent = json.loads(canonical(intent))

        async def write(tx: RecordTransaction) -> Payload:
            run = (await tx.load("runs", ctx.run_id or "")).payload
            ledger = (await tx.load("budget.ledgers", ctx.run_id or "")).payload
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
            reserved = await tx.load("budget.reservations", intent["reservation_ref"]["id"])
            account = (await tx.load("budget.accounting", reserved.resource_id)).payload
            fixed = (await tx.load("tool.specs", key)).payload
            if (
                intent["validated_action_ref"] != reference("tool_call", key)
                or intent["provider_binding_ref"] != fixed["provider_ref"]
                or intent["reservation_ref"]
                != reference("reservation", reserved.resource_id, reserved.revision)
                or any(
                    account[k] != getattr(ctx, k)
                    for k in ("run_id", "attempt_id", "operation_id", "trace_id")
                )
                or reserved.payload["status"] != "reserved"
            ):
                raise fail(
                    "dispatch_binding_stale",
                    "Dispatch inputs differ from their authority",
                    phase="dispatch",
                    category="conflict",
                    status=412,
                )
            if min(
                datetime.fromisoformat(s.replace("Z", "+00:00"))
                for s in (ctx.deadline, account["deadline"], ledger["deadline"])
            ) <= datetime.now(UTC):
                raise fail(
                    "deadline_exceeded",
                    "Dispatch deadline expired",
                    phase="dispatch",
                    category="timeout",
                )
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
            if account["dispatched"]:
                raise fail(
                    "unknown_effect",
                    "Reservation already dispatched without this intent",
                    phase="dispatch",
                    category="unknown_effect",
                    status=409,
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
