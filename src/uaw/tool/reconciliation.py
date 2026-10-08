"""Trusted receipt reconciliation; no executor, new admission or inferred effects."""

import asyncio
import json
from datetime import UTC, datetime
from typing import Any, Protocol, cast

from uaw.infrastructure.db.transactions import reference
from uaw.shared.contracts import JsonObject, Ref, TrustedExecutionContext
from uaw.shared.errors import DomainError, error_result
from uaw.shared.ports import ToolReceiptReaderPort
from uaw.shared.schema import ContractViolation, validate_contract
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.errors import fail, validate_dependency
from uaw.tool.ledger import ToolLedger, action_key
from uaw.tool.schema import canonical

Payload = dict[str, Any]


class ToolEvidenceReaderPort(Protocol):
    """Owning source checks current access/provenance and returns the actual pinned Ref.

    Recovery access is distinct from permission to issue a new action. A well formed
    Ref, previous Scope or cached approval is never evidence of current source access.
    """

    async def check(self, ref: Ref, ctx: TrustedExecutionContext) -> Ref: ...


class ToolReconciler:
    def __init__(
        self,
        ledger: ToolLedger,
        budgets: ToolBudgetAdapter,
        *,
        receipts: ToolReceiptReaderPort | None = None,
        evidence: ToolEvidenceReaderPort | None = None,
    ) -> None:
        self.ledger, self.budgets = ledger, budgets
        self.receipts, self.evidence = receipts, evidence

    async def check_action(self, action_id: str, ctx: TrustedExecutionContext) -> None:
        """Verify the fixed Tool binding only; owning Readers still authorize access."""
        validate_contract("ID", action_id)
        call = await self.ledger.attempt(ctx)
        if call["action_id"] != action_id:
            raise fail(
                "receipt_binding_conflict",
                "Requested action differs from the original attempt",
                phase="reconcile",
                category="conflict",
                status=409,
            )
        await self.ledger.action(action_id, ctx)

    async def _accepted(
        self, action_id: str, ctx: TrustedExecutionContext
    ) -> tuple[Payload, Payload]:
        await self.check_action(action_id, ctx)
        effect = await self.ledger.effect(action_id, ctx)
        wire = effect.get("receipt_ref")
        if wire is None:
            raise fail(
                "receipt_missing",
                "Action has no accepted outcome receipt",
                phase="receipt",
                category="dependency",
                status=404,
            )
        validate_dependency("Ref", wire, "receipt")
        key = self.ledger.receipt_key({"receipt_ref": wire})
        accepted = await self.ledger.get("tool.reconciliation.receipts", key, ctx)
        if accepted is not None:
            validate_dependency("ToolReconciliationReceipt", accepted, "receipt")
        active = await self.ledger.get("tool.reconciliation.active", ctx.attempt_id, ctx)
        intent = await self.ledger.get("tool.dispatch.intents", action_key(ctx, action_id), ctx)
        if (
            accepted is None
            or active != accepted
            or accepted["receipt_ref"] != wire
            or ctx.attempt_id not in effect["attempt_ids"]
            or intent is None
        ):
            raise fail(
                "receipt_binding_conflict",
                "Effect does not reference this attempt's accepted receipt",
                phase="receipt",
                category="conflict",
                status=409,
            )
        return effect, accepted

    async def read_outcome(self, action_id: str, ctx: TrustedExecutionContext) -> JsonObject:
        """Recheck an accepted receipt's actual source/evidence, without accounting.

        Acceptance of an effect observation does not require completed fee settlement.
        Read the fixed accepted version, never an unaccepted newer Lookup result.
        No receipt means no inferred outcome, even if EffectRecord says confirmed.
        """
        try:
            effect, accepted = await self._accepted(action_id, ctx)
            ref = Ref.model_validate_json(json.dumps(accepted["receipt_ref"]))
            actual = await self._read(ref, ctx)
            if canonical(actual) != canonical(accepted):
                raise fail(
                    "receipt_conflict",
                    "Accepted receipt version changed its contents",
                    phase="receipt",
                    category="conflict",
                    status=409,
                )
            # No source await under Tool locks. Refuse a concurrently superseded
            # observation rather than returning it as the action's current outcome.
            current, pinned = await self._accepted(action_id, ctx)
            if current != effect or pinned != accepted:
                raise fail(
                    "receipt_version_stale",
                    "Accepted outcome changed while reading its sources",
                    phase="receipt",
                    category="conflict",
                    status=412,
                )
            return cast(JsonObject, json.loads(canonical(actual)))
        except (ContractViolation, ValueError, TypeError, OverflowError, RecursionError) as exc:
            raise fail(
                "receipt_invalid", "Outcome receipt violates its strict contract", phase="receipt"
            ) from exc
        except TimeoutError as exc:
            raise fail(
                "reconciliation_interrupted",
                "Outcome source response is unresolved",
                phase="receipt",
                category="infrastructure",
                status=503,
            ) from exc

    async def _read(self, receipt_ref: Ref, ctx: TrustedExecutionContext) -> Payload:
        if self.receipts is None:
            raise fail(
                "dependency_unavailable",
                "Production receipt Reader is not wired",
                phase="receipt",
                category="dependency",
                status=503,
            )
        raw = await self.receipts.read(receipt_ref, ctx)
        receipt: Payload = json.loads(canonical(raw))
        validate_dependency("ToolReconciliationReceipt", receipt, "receipt")
        call = await self.ledger.attempt(ctx)
        _, spec, _ = await self.ledger.action(call["action_id"], ctx)
        if (
            receipt["action_ref"] != reference("tool_call", action_key(ctx, call["action_id"]))
            or receipt["attempt_id"] != ctx.attempt_id
            or receipt["usage"]["attempt_id"] != ctx.attempt_id
            or receipt["provider_ref"] != spec["provider_ref"]
            or receipt["receipt_ref"] != receipt_ref.wire()
        ):
            raise fail(
                "receipt_binding_conflict",
                "Receipt is not bound to this actual attempt",
                phase="receipt",
                category="conflict",
                status=409,
            )
        if datetime.fromisoformat(receipt["observed_at"].replace("Z", "+00:00")) > datetime.now(
            UTC
        ):
            raise fail(
                "receipt_version_stale",
                "Receipt observation is in the future",
                phase="receipt",
                category="conflict",
                status=412,
            )
        if receipt["evidence_refs"] and self.evidence is None:
            raise fail(
                "dependency_unavailable",
                "Actual evidence Reader is not wired",
                phase="evidence",
                category="dependency",
                status=503,
            )
        for wire in receipt["evidence_refs"]:
            ref = Ref.model_validate_json(json.dumps(wire))
            assert self.evidence is not None
            actual = await self.evidence.check(ref, ctx)
            if not isinstance(actual, Ref):
                raise fail(
                    "dependency_protocol_invalid",
                    "Evidence Reader did not return an actual Ref",
                    phase="evidence",
                    category="dependency",
                    status=503,
                )
            validate_dependency("Ref", actual.wire(), "evidence")
            if actual.wire() != ref.wire():
                raise fail(
                    "receipt_version_stale",
                    "Actual evidence differs from its pinned version",
                    phase="evidence",
                    category="conflict",
                    status=412,
                )
        # The receipt source must still be accessible after other source awaits.
        again = await self.receipts.read(receipt_ref, ctx)
        validate_dependency("ToolReconciliationReceipt", again, "receipt")
        if canonical(again) != canonical(receipt):
            raise fail(
                "receipt_version_stale",
                "Receipt changed while checking evidence",
                phase="receipt",
                category="conflict",
                status=412,
            )
        return receipt

    async def reconcile(
        self, receipt_ref: Ref, ctx: TrustedExecutionContext, *, expected_revision: int
    ) -> JsonObject:
        """Internal fixed-ref entry, returns existing RuntimeToolruntimeReconcileResult.

        ok confirms the reconciliation record, not tool execution. EffectRecord's
        confirmed means an actual deterministic conclusion; read its receipt's
        applied/not_applied outcome. Fees are an independent persistent settlement.
        """
        try:
            if type(expected_revision) is not int or expected_revision < 0:
                raise fail(
                    "invalid_arguments",
                    "Expected effect revision must be a strict integer",
                    phase="reconcile",
                )
            receipt = await self._read(receipt_ref, ctx)
            # Recovery reads validate ownership without treating cancellation/expiry
            # as a new admission, or constructing a fresh attempt/reservation.
            await self.budgets.get_ledger(ctx)
            step = await self.ledger.begin_reconciliation(receipt, ctx, expected_revision)
            key = str(step["key"])
            settlement = step.get("settlement")
            if settlement is None:
                try:
                    settlement = await self.budgets.settle_receipt(receipt, key, ctx)
                except DomainError as exc:
                    # These BudgetService errors are definite transaction rejections.
                    # Keep actual effects/observations and permit a later confirmed bill.
                    if exc.failure.code in {
                        "usage_reconciliation_denied",
                        "usage_settlement_denied",
                    }:
                        await self.ledger.save(
                            "tool.reconciliation.failures", key, "Failure", exc.failure.wire(), ctx
                        )
                    raise
            await self.ledger.finish_reconciliation(receipt, settlement, ctx)
            effect = await self.ledger.effect_from_attempt(ctx)
            result: Payload = {
                "kind": "ok",
                "payload": effect,
                "revision": effect["revision"],
                "output_refs": [receipt_ref.wire()],
            }
            if settlement["usage_refs"]:
                result["usage_ref"] = settlement["usage_refs"][0]
        except asyncio.CancelledError:
            # The fixed plan/actual effect survives cancellation; no fake fee/effect receipt.
            raise
        except DomainError as exc:
            result = error_result(exc)
        except ContractViolation, ValueError, TypeError, OverflowError, RecursionError:
            result = error_result(
                fail("receipt_invalid", "Receipt violates its strict contract", phase="receipt")
            )
        except TimeoutError:
            result = error_result(
                fail(
                    "reconciliation_interrupted",
                    "Receipt/budget response is unresolved; replay the fixed plan",
                    phase="reconcile",
                    category="infrastructure",
                    status=503,
                )
            )
        validate_contract("RuntimeToolruntimeReconcileResult", result)
        return result
