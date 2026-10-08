"""Named SQL provider records and principal-isolated blobs of actual raw responses."""

import json
from typing import Any

from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.db.transactions import RecordTransaction
from uaw.shared.contracts import JsonObject, Principal, Ref, TrustedExecutionContext
from uaw.shared.stores import BlobStorePort
from uaw.tool.errors import fail, validate_dependency
from uaw.tool.ledger import ToolLedger, action_key, immutable
from uaw.tool.ports import ToolRecoveryAccessPort
from uaw.tool.schema import canonical, digest

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
        raw = canonical(data)
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
        if content_hash != digest(data):
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
            "transport_status": "local_computation_completed",
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
        if type(data) is not dict or canonical(data) != content or digest(data) != ref.content_hash:
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
