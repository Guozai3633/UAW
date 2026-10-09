"""Intent's unified entry point; model interpretation is never the source of authority."""

from typing import Any

from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.db.transactions import reference
from uaw.intent.frame import FrameRepository
from uaw.intent.original import OriginalReader
from uaw.intent.ports import UnderstandingContextPort
from uaw.intent.semantic import frame_candidate, ground_proposal, proposal_schema
from uaw.model.policy import PolicyResolver
from uaw.shared.contracts import JsonObject, TrustedExecutionContext
from uaw.shared.errors import DomainError, error_result, reject
from uaw.shared.ports import ModelPort
from uaw.shared.schema import ContractViolation, validate_contract
from uaw.shared.stores import StoreConflict, StoreMissing

Payload = dict[str, Any]


class IntentFacade:
    def __init__(
        self,
        originals: OriginalReader,
        contexts: UnderstandingContextPort,
        models: ModelPort,
        policies: PolicyResolver,
        frames: FrameRepository,
    ) -> None:
        self.originals, self.contexts, self.models = originals, contexts, models
        self.policies, self.frames = policies, frames

    async def understand(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject:
        return await self._entry(request, ctx, revise=False)

    async def revise(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject:
        return await self._entry(request, ctx, revise=True)

    async def _entry(
        self, request: JsonObject, ctx: TrustedExecutionContext, *, revise: bool
    ) -> JsonObject:
        try:
            validate_contract("FramePatchRequest" if revise else "UnderstandingRequest", request)
            if "intent.understand" not in ctx.scope.capabilities:
                raise reject(
                    "intent_capability_denied", "Trusted scope lacks task understanding", 403
                )
            result = await self._understand(request, ctx, revise=revise)
        except ContractViolation:
            result = error_result(
                reject(
                    "intent_request_invalid", "Understanding request/proposal violates its contract"
                )
            )
        except DomainError as exc:
            # Preserve Intent's existing lifecycle errors when the shared gate runs first.
            code = {
                "execution_scope_denied": "intent_scope_denied",
                "execution_cancelled": "intent_cancelled",
                "execution_deadline_expired": "intent_deadline_expired",
                "execution_run_unavailable": "intent_run_unavailable",
            }.get(exc.failure.code)
            if code:
                exc = DomainError(exc.failure.model_copy(update={"code": code}), exc.status_code)
            result = error_result(exc)
        validate_contract(
            "RuntimeIntentruntimeReviseResult"
            if revise
            else "RuntimeIntentruntimeUnderstandResult",
            result,
        )
        return result

    async def _model_config(self, ctx: TrustedExecutionContext) -> Payload:
        store = self.frames.store
        binding = (await store.get(ctx.principal, "run.bindings", ctx.run_id or "")).payload
        policy = (
            await store.get(
                ctx.principal,
                "model.policies",
                binding["model_policy_ref"]["id"],
                revision=int(binding["model_policy_ref"]["version"]),
            )
        ).payload
        config = await self.policies.configuration.snapshot(binding["configuration_ref"])
        entry = await self.policies.configuration.require_model(policy["fixed_model_id"], config)
        requested = {
            "model_id": entry["id"],
            "catalog_revision": entry["revision"],
            "provider_ref": entry["provider_ref"],
            "policy_ref": binding["model_policy_ref"],
            "max_output_tokens": min(4096, entry["output_limit_tokens"]),
        }
        selection = await self.policies.resolve(requested, ctx)
        if "json_schema" not in selection.model["capabilities"]:
            raise reject(
                "intent_protocol_unsupported",
                "Selected model lacks approved structured output",
                409,
            )
        return requested

    async def _understand(
        self, request: Payload, ctx: TrustedExecutionContext, *, revise: bool
    ) -> Payload:
        config = await self._model_config(ctx)
        current = await self.originals.reader.read(ctx)
        digest = parameter_hash(
            {
                "action": "revise" if revise else "understand",
                "request": request,
                "context": ctx.wire(),
            }
        )
        try:
            receipt = (
                await self.frames.store.get(ctx.principal, "intent.receipts", ctx.attempt_id)
            ).payload
        except StoreMissing:
            receipt = None
        if receipt:
            if receipt["request_hash"] != digest:
                raise StoreConflict("idempotency_conflict")
            if (
                receipt["run_id"] != ctx.run_id
                or receipt["input_revision"] != current.state["revision"]
            ):
                raise reject(
                    "intent_input_stale",
                    "Saved understanding belongs to an earlier user requirement",
                    412,
                )
            return receipt["result"]  # type: ignore[no-any-return]
        if revise:
            old_ref = request["current_frame_ref"]
            if old_ref != reference(
                "task_frame", current.run["task_id"], request["expected_revision"]
            ):
                raise reject(
                    "intent_frame_stale",
                    "Revision request does not match its fixed prior frame",
                    412,
                )
            old = (
                await self.frames.store.get(
                    ctx.principal,
                    "intent.frames",
                    old_ref["id"],
                    revision=request["expected_revision"],
                )
            ).payload
            if (
                not current.state["patch_refs"]
                or request["new_input_ref"] != current.state["patch_refs"][-1]
                or old.get("input_revision", 0) >= current.state["revision"]
            ):
                raise reject(
                    "intent_patch_source_invalid",
                    "Revision requires a new Run-owned user requirement",
                    412,
                )
            normal = {
                "original_input_ref": current.refs[0],
                "user_patch_refs": list(current.refs[1:]),
                "material_refs": [],
                "expected_revision": request["expected_revision"],
            }
        else:
            normal = request
        inputs = await self.originals.read(normal, ctx)
        if (
            await self.frames.head_revision(ctx.principal, inputs.run["task_id"])
            != normal["expected_revision"]
        ):
            raise StoreConflict()
        snapshot = await self.contexts.prepare(inputs, ctx, config["max_output_tokens"])
        model_result = await self.models.generate(
            {
                "context_snapshot_ref": snapshot,
                "model_config": config,
                "output_protocol": "json_schema",
                "output_schema": proposal_schema(),
                "attempt_id": ctx.attempt_id,
            },
            ctx,
        )
        validate_contract("RuntimeModelruntimeGenerateResult", model_result)
        if model_result["kind"] != "ok":
            return model_result
        output = model_result["payload"]
        assert isinstance(output, dict)
        if output["finish_reason"] != "stop" or not isinstance(output.get("structured_data"), dict):
            raise reject(
                "intent_output_incomplete",
                "Incomplete/refused output cannot become a task frame",
                409,
            )
        semantic_ref = reference(
            "semantic_parse", "semantic-" + parameter_hash({"attempt": ctx.attempt_id})
        )
        raw_proposal = output["structured_data"]
        assert isinstance(raw_proposal, dict)
        proposal = ground_proposal(raw_proposal, inputs)
        output_attempt = output["attempt_id"]
        assert isinstance(output_attempt, str)
        candidate = frame_candidate(proposal, inputs, semantic_ref)
        semantic = {
            "run_id": inputs.run["id"],
            "input_revision": inputs.state["revision"],
            "source_refs": list(inputs.refs),
            "proposal": proposal,
            "model_output_ref": reference("content", output_attempt),
            "context_snapshot_ref": snapshot,
        }
        # A model call may finish after permissions or requirements were changed.
        await self.policies.resolve(config, ctx)
        return await self.frames.publish(
            candidate, semantic, inputs, normal["expected_revision"], digest, ctx
        )
