"""Verified raw output, independent accounting and immutable normalized ToolResult."""

import json

from uaw.infrastructure.db.transactions import reference
from uaw.shared.contracts import JsonObject, Ref, TrustedExecutionContext
from uaw.tool.errors import fail, validate_dependency
from uaw.tool.ledger import action_key
from uaw.tool.receipt_store import ToolReceiptStore
from uaw.tool.reconciliation import ToolReconciler
from uaw.tool.schema import canonical


class ToolResults:
    def __init__(self, source: ToolReceiptStore, reconciler: ToolReconciler) -> None:
        if source.ledger is not reconciler.ledger:
            raise ValueError("Result/source/reconciler must share the Tool ledger")
        self.source, self.reconciler, self.ledger = source, reconciler, source.ledger

    def ready(self) -> None:
        if self.source.access is None or self.source.verifier is None:
            raise fail(
                "dependency_unavailable",
                "Current result authority/output verifier is not wired",
                phase="normalize_result",
                category="dependency",
                status=503,
            )

    async def resume(self, call: JsonObject, ctx: TrustedExecutionContext) -> JsonObject:
        fixed = await self.ledger.attempt(ctx)
        if fixed != call:
            raise fail(
                "receipt_binding_conflict",
                "Result recovery changed original call",
                phase="normalize_result",
                category="conflict",
                status=409,
            )
        receipt = await self.source.provider_receipt(ctx)
        if receipt is None:
            raise fail(
                "unknown_effect",
                "Original send has no saved actual response; do not resend",
                phase="result_source",
                category="unknown_effect",
                status=409,
            )
        acknowledged = await self.ledger.get("tool.invocation.receipts", ctx.attempt_id, ctx)
        if acknowledged is not None and acknowledged != receipt:
            raise fail(
                "receipt_binding_conflict",
                "Executor reply differs from actual saved response",
                phase="result_source",
                category="conflict",
                status=409,
            )
        data = await self.source.verified(receipt, ctx)
        ref = await self.source.publish(receipt, ctx, authenticated_provider=self.source.provider)
        effect = await self.ledger.effect_from_attempt(ctx)
        reconciliation = await self.reconciler.reconcile(
            ref, ctx, expected_revision=effect["revision"]
        )
        if reconciliation["kind"] != "ok":
            return reconciliation  # Failure fields conform to the existing invoke result.
        actual = await self.reconciler.read_outcome(str(call["action_id"]), ctx)
        if actual["outcome"] != "applied" or actual["receipt_ref"] != ref.wire():
            raise fail(
                "unknown_effect",
                "No current actual applied computation proof",
                phase="normalize_result",
                category="unknown_effect",
                status=409,
            )
        data = await self.source.verified(receipt, ctx)
        usage_ref = reconciliation.get("usage_ref")
        if usage_ref is None:
            raise fail(
                "dependency_protocol_invalid",
                "No actual usage settlement ref for ToolResult",
                phase="normalize_result",
                category="dependency",
                status=503,
            )
        result = {
            "call_ref": reference("tool_call", action_key(ctx, str(call["action_id"]))),
            "status": "succeeded",
            "data": data,
            "effect_state": "confirmed",
            "output_refs": [receipt["raw_result_ref"], ref.wire()],
            "usage_ref": usage_ref,
        }
        validate_dependency("ToolResult", result, "normalize_result")
        await self.ledger.save("tool.results", ctx.attempt_id, "ToolResult", result, ctx)
        return await self.read_result(str(call["action_id"]), ctx)

    async def read_result(self, action_id: str, ctx: TrustedExecutionContext) -> JsonObject:
        """Return existing RuntimeToolruntimeInvokeResult after current source verification."""
        await self.reconciler.check_action(action_id, ctx)
        stored = await self.ledger.get("tool.results", ctx.attempt_id, ctx)
        if stored is None:
            raise fail(
                "result_missing",
                "Original attempt has no normalized completed result",
                phase="normalize_result",
                category="dependency",
                status=404,
            )
        validate_dependency("ToolResult", stored, "normalize_result")
        actual = await self.reconciler.read_outcome(action_id, ctx)
        raw = await self.source.provider_receipt(ctx)
        assert raw is not None
        data = await self.source.verified(raw, ctx)
        if (
            actual["outcome"] != "applied"
            or stored["data"] != data
            or stored["status"] != "succeeded"
            or stored["effect_state"] != "confirmed"
            or stored["call_ref"] != reference("tool_call", action_key(ctx, action_id))
            or stored["output_refs"] != [raw["raw_result_ref"], actual["receipt_ref"]]
        ):
            raise fail(
                "receipt_binding_conflict",
                "Stored ToolResult differs from current actual sources",
                phase="normalize_result",
                category="conflict",
                status=409,
            )
        key = self.ledger.receipt_key(actual)
        settlement = await self.ledger.get("tool.reconciliation.settled", key, ctx)
        if settlement is None or stored["usage_ref"] not in settlement["usage_refs"]:
            raise fail(
                "receipt_binding_conflict",
                "ToolResult has no matching actual fee settlement",
                phase="normalize_result",
                category="conflict",
                status=409,
            )
        await self.source.read(Ref.model_validate(actual["receipt_ref"]), ctx)
        effect = await self.ledger.effect_from_attempt(ctx)
        result: JsonObject = {
            "kind": "ok",
            "payload": json.loads(canonical(stored)),
            "output_refs": stored["output_refs"],
            "usage_ref": stored["usage_ref"],
            "revision": effect["revision"],
        }
        validate_dependency("RuntimeToolruntimeInvokeResult", result, "normalize_result")
        return result
