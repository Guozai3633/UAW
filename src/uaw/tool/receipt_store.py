"""Named SQL provider records and principal-isolated blobs of actual raw responses."""

import hashlib
import json
from typing import Any

from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.db.transactions import RecordTransaction, reference, timestamp
from uaw.shared.contracts import JsonObject, Principal, Ref, TrustedExecutionContext
from uaw.shared.stores import BlobStorePort
from uaw.tool.errors import fail, validate_dependency
from uaw.tool.ledger import ToolLedger, action_key, immutable
from uaw.tool.ports import ToolOutputVerifierPort, ToolRecoveryAccessPort
from uaw.tool.schema import canonical, compile_schema, digest

Payload = dict[str, Any]


def response_id(ctx: TrustedExecutionContext) -> str:
    return "tool-raw-" + parameter_hash({"run": ctx.run_id, "attempt": ctx.attempt_id})


class ToolResponseStore:
    """One explicitly bound provider. Missing current recovery authority is unavailable.

    Raw JSON bytes are evidence, not a ToolResult. The fixed output schema and an
    actual owning verifier must validate them before business success is possible.
    """

    def __init__(
        self,
        ledger: ToolLedger,
        blobs: BlobStorePort,
        *,
        provider_ref: Ref,
        provider: Principal,
        access: ToolRecoveryAccessPort | None = None,
    ) -> None:
        self.ledger, self.blobs = ledger, blobs
        self.provider_ref, self.provider, self.access = provider_ref, provider, access

    transport_status = "local_computation_completed"

    def data_bytes(self, data: JsonObject) -> bytes:
        return canonical(data)

    async def binding(self, ctx: TrustedExecutionContext) -> tuple[Payload, Payload]:
        call = await self.ledger.attempt(ctx)
        fixed, spec, _ = await self.ledger.action(call["action_id"], ctx)
        key = action_key(ctx, call["action_id"])
        effect = await self.ledger.effect(call["action_id"], ctx)
        intent = await self.ledger.get("tool.dispatch.intents", key, ctx)
        if (
            call != fixed
            or spec["provider_ref"] != self.provider_ref.wire()
            or spec["effect"] != "read"
            or ctx.attempt_id not in effect["attempt_ids"]
            or intent is None
            or intent["validated_action_ref"]["id"] != key
            or intent["provider_binding_ref"] != spec["provider_ref"]
        ):
            raise fail(
                "receipt_binding_conflict",
                "Response source is outside its registered read attempt",
                phase="result_source",
                category="conflict",
                status=409,
            )
        if self.access is None:
            raise fail(
                "dependency_unavailable",
                "Current result recovery authority is not wired",
                phase="result_source",
                category="dependency",
                status=503,
            )
        await self.access.check(call, spec, ctx, provider=self.provider)
        return call, spec

    def authenticate(self, authenticated_provider: Principal) -> None:
        if authenticated_provider != self.provider or self.provider.kind != "service":
            raise fail(
                "provider_scope_denied",
                "Provider identity differs from trusted adapter binding",
                phase="result_source",
                category="authorization",
                status=403,
            )

    async def save_response(
        self,
        data: JsonObject,
        usage: JsonObject,
        ctx: TrustedExecutionContext,
        *,
        authenticated_provider: Principal,
    ) -> JsonObject:
        self.authenticate(authenticated_provider)
        await self.binding(ctx)
        raw = self.data_bytes(data)
        measured: Payload = json.loads(canonical(usage))
        validate_dependency("Usage", measured, "result_source")
        if measured["attempt_id"] != ctx.attempt_id:
            raise fail(
                "receipt_binding_conflict",
                "Measured usage belongs to another attempt",
                phase="result_source",
                category="conflict",
                status=409,
            )
        content_hash = await self.blobs.put(ctx.principal, raw)
        if content_hash != hashlib.sha256(raw).hexdigest():
            raise fail(
                "dependency_protocol_invalid",
                "Raw blob digest differs from actual response",
                phase="result_source",
                category="dependency",
                status=503,
            )
        await self.binding(ctx)
        ref = Ref(kind="content", id=response_id(ctx), version="1", content_hash=content_hash)
        receipt = {
            "attempt_id": ctx.attempt_id,
            "raw_result_ref": ref.wire(),
            "transport_status": self.transport_status,
            "effect_state": "confirmed",
            "usage": measured,
        }
        validate_dependency("ProviderReceipt", receipt, "result_source")

        async def write(tx: RecordTransaction) -> Payload:
            await immutable(tx, "tool.response.refs", ctx.attempt_id, "Ref", ref.wire())
            await immutable(
                tx, "tool.response.providers", ctx.attempt_id, "Principal", self.provider.wire()
            )
            return await immutable(
                tx, "tool.provider.receipts", ctx.attempt_id, "ProviderReceipt", receipt
            )

        saved = await self.ledger.transactions.inspect(
            ctx.principal, self.ledger.aggregate(ctx), write
        )
        return saved

    async def provider_receipt(self, ctx: TrustedExecutionContext) -> Payload | None:
        await self.binding(ctx)
        receipt = await self.ledger.get("tool.provider.receipts", ctx.attempt_id, ctx)
        if receipt is None:
            return None
        validate_dependency("ProviderReceipt", receipt, "result_source")
        provider = await self.ledger.get("tool.response.providers", ctx.attempt_id, ctx)
        ref = await self.ledger.get("tool.response.refs", ctx.attempt_id, ctx)
        if (
            provider != self.provider.wire()
            or receipt["attempt_id"] != ctx.attempt_id
            or receipt["usage"]["attempt_id"] != ctx.attempt_id
            or receipt["raw_result_ref"] != ref
        ):
            raise fail(
                "receipt_binding_conflict",
                "Saved response/identity/usage binding changed",
                phase="result_source",
                category="conflict",
                status=409,
            )
        return receipt

    async def read_raw(self, ref: Ref, ctx: TrustedExecutionContext) -> JsonObject:
        receipt = await self.provider_receipt(ctx)
        if receipt is None or receipt["raw_result_ref"] != ref.wire() or ref.content_hash is None:
            raise fail(
                "receipt_binding_conflict",
                "Raw response is not this attempt's fixed saved content",
                phase="result_source",
                category="conflict",
                status=409,
            )
        content = await self.blobs.get(ctx.principal, ref.content_hash)
        data = json.loads(content)
        if (
            type(data) is not dict
            or self.data_bytes(data) != content
            or hashlib.sha256(content).hexdigest() != ref.content_hash
        ):
            raise fail(
                "raw_result_invalid",
                "Actual saved raw response violates its fixed digest",
                phase="result_source",
                category="conflict",
                status=409,
            )
        again = await self.provider_receipt(ctx)
        if again != receipt:
            raise fail(
                "receipt_version_stale",
                "Response changed while reading its blob",
                phase="result_source",
                category="conflict",
                status=412,
            )
        return data


class ToolReceiptStore(ToolResponseStore):
    """Actual fixed provider response -> verified read evidence -> recovery source.

    Implements ActionReceiptLookupPort, ToolReceiptReaderPort and the evidence Reader.
    Does not infer outcome from transport, Runner, timeout or a budget record.
    """

    def __init__(
        self,
        ledger: ToolLedger,
        blobs: BlobStorePort,
        *,
        provider_ref: Ref,
        provider: Principal,
        access: ToolRecoveryAccessPort | None = None,
        verifier: ToolOutputVerifierPort | None = None,
    ) -> None:
        super().__init__(ledger, blobs, provider_ref=provider_ref, provider=provider, access=access)
        self.verifier = verifier

    async def verified(self, receipt: Payload, ctx: TrustedExecutionContext) -> JsonObject:
        receipt = json.loads(canonical(receipt))
        validate_dependency("ProviderReceipt", receipt, "normalize_result")
        actual = await self.provider_receipt(ctx)
        if actual != receipt:
            raise fail(
                "receipt_binding_conflict",
                "Provider response differs from saved original",
                phase="normalize_result",
                category="conflict",
                status=409,
            )
        if self.verifier is None:
            raise fail(
                "dependency_unavailable",
                "Actual tool output verifier is not wired",
                phase="normalize_result",
                category="dependency",
                status=503,
            )
        if receipt["effect_state"] != "confirmed":
            raise fail(
                "unknown_effect",
                "Provider computation remains unresolved",
                phase="normalize_result",
                category="unknown_effect",
                status=409,
            )
        call, spec = await self.binding(ctx)
        data = await self.read_raw(Ref.model_validate(receipt["raw_result_ref"]), ctx)
        if not compile_schema(spec["output_schema"]).is_valid(data):
            raise fail(
                "tool_output_invalid",
                "Actual output violates fixed tool schema",
                phase="normalize_result",
                category="dependency",
                status=503,
            )
        frozen = (self.data_bytes(data), canonical(call), canonical(spec))
        await self.verifier.verify(data, call, spec, ctx)
        if frozen != (self.data_bytes(data), canonical(call), canonical(spec)):
            raise fail(
                "tool_output_invalid",
                "Output verifier changed fixed data",
                phase="normalize_result",
                category="conflict",
                status=409,
            )
        await self.binding(ctx)
        if await self.provider_receipt(ctx) != receipt:
            raise fail(
                "receipt_version_stale",
                "Provider source changed after output verification",
                phase="normalize_result",
                category="conflict",
                status=412,
            )
        return data

    def receipt_ref(self, receipt: Payload, ctx: TrustedExecutionContext) -> Ref:
        # Digest pins the real provider observation plus independently fixed ownership.
        # It is not a self-referential hash of the reconciliation envelope.
        return Ref(
            kind="content",
            id="tool-receipt-" + parameter_hash({"run": ctx.run_id, "attempt": ctx.attempt_id}),
            version="1",
            content_hash=digest(
                {
                    "receipt": receipt,
                    "context": ctx.wire(),
                    "provider": self.provider.wire(),
                    "provider_ref": self.provider_ref.wire(),
                }
            ),
        )

    async def publish(
        self,
        receipt: JsonObject,
        ctx: TrustedExecutionContext,
        *,
        authenticated_provider: Principal,
    ) -> Ref:
        self.authenticate(authenticated_provider)
        fixed: Payload = json.loads(canonical(receipt))
        await self.verified(fixed, ctx)
        call, spec = await self.binding(ctx)
        ref = self.receipt_ref(fixed, ctx)

        async def write(tx: RecordTransaction) -> Payload:
            previous = await self.ledger_optional(tx, ctx)
            if previous is not None:
                if previous["receipt_ref"] != ref.wire() or previous["usage"] != fixed["usage"]:
                    raise fail(
                        "receipt_conflict",
                        "Published source observation changed",
                        phase="result_source",
                        category="conflict",
                        status=409,
                    )
                return previous
            value = {
                "action_ref": reference("tool_call", action_key(ctx, call["action_id"])),
                "attempt_id": ctx.attempt_id,
                "provider_ref": spec["provider_ref"],
                "receipt_ref": ref.wire(),
                "outcome": "applied",
                "evidence_refs": [fixed["raw_result_ref"]],
                "usage": fixed["usage"],
                "observed_at": timestamp(),
            }
            return await immutable(
                tx, "tool.source.receipts", ctx.attempt_id, "ToolReconciliationReceipt", value
            )

        await self.ledger.transactions.inspect(ctx.principal, self.ledger.aggregate(ctx), write)
        return ref

    @staticmethod
    async def ledger_optional(
        tx: RecordTransaction, ctx: TrustedExecutionContext
    ) -> Payload | None:
        from uaw.tool.ledger import optional

        return await optional(tx, "tool.source.receipts", ctx.attempt_id)

    async def find(self, action_id: str, ctx: TrustedExecutionContext) -> Ref | None:
        call, _ = await self.binding(ctx)
        if action_id != call["action_id"]:
            raise fail(
                "receipt_binding_conflict",
                "Lookup action differs from original attempt",
                phase="result_source",
                category="conflict",
                status=409,
            )
        stored = await self.ledger.get("tool.source.receipts", ctx.attempt_id, ctx)
        if stored is None:
            return None
        ref = Ref.model_validate(stored["receipt_ref"])
        await self.read(ref, ctx)
        return ref

    async def read(self, receipt_ref: Ref, ctx: TrustedExecutionContext) -> JsonObject:
        call, spec = await self.binding(ctx)
        value = await self.ledger.get("tool.source.receipts", ctx.attempt_id, ctx)
        if value is None:
            from uaw.shared.stores import StoreMissing

            raise StoreMissing()
        validate_dependency("ToolReconciliationReceipt", value, "result_source")
        raw = await self.provider_receipt(ctx)
        if raw is None:
            raise fail(
                "dependency_unavailable",
                "Published receipt has no actual provider source",
                phase="result_source",
                category="dependency",
                status=503,
            )
        if (
            value["receipt_ref"] != receipt_ref.wire()
            or receipt_ref != self.receipt_ref(raw, ctx)
            or value["action_ref"] != reference("tool_call", action_key(ctx, call["action_id"]))
            or value["attempt_id"] != ctx.attempt_id
            or value["provider_ref"] != spec["provider_ref"]
            or value["outcome"] != "applied"
            or value["evidence_refs"] != [raw["raw_result_ref"]]
            or value["usage"] != raw["usage"]
        ):
            raise fail(
                "receipt_binding_conflict",
                "Published receipt differs from actual saved computation",
                phase="result_source",
                category="conflict",
                status=409,
            )
        await self.verified(raw, ctx)
        if await self.ledger.get("tool.source.receipts", ctx.attempt_id, ctx) != value:
            raise fail(
                "receipt_version_stale",
                "Published receipt changed during recovery read",
                phase="result_source",
                category="conflict",
                status=412,
            )
        return value

    async def check(self, ref: Ref, ctx: TrustedExecutionContext) -> Ref:
        receipt = await self.provider_receipt(ctx)
        if receipt is None or receipt["raw_result_ref"] != ref.wire():
            raise fail(
                "receipt_binding_conflict",
                "Evidence is not this attempt's actual raw response",
                phase="evidence",
                category="conflict",
                status=409,
            )
        await self.verified(receipt, ctx)
        return Ref.model_validate(receipt["raw_result_ref"])
