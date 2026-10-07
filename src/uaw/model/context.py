"""Context window metadata resolved through the same fixed policy as generation."""

from uaw.context.contracts import ModelWindow
from uaw.context.seed import revision
from uaw.model.policy import PolicyResolver
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import reject


class FixedModelWindow:
    def __init__(self, policies: PolicyResolver) -> None:
        self.policies = policies

    async def resolve(self, policy_ref: Ref, ctx: TrustedExecutionContext) -> ModelWindow:
        store = self.policies.store
        binding = (await store.get(ctx.principal, "run.bindings", ctx.run_id or "")).payload
        if policy_ref.wire() != binding["model_policy_ref"]:
            raise reject("model_policy_denied", "Context cannot replace the fixed Run model", 403)
        policy = (
            await store.get(
                ctx.principal,
                "model.policies",
                policy_ref.id,
                revision=revision(policy_ref.wire(), "policy"),
            )
        ).payload
        snapshot = await self.policies.configuration.snapshot(binding["configuration_ref"])
        model = await self.policies.configuration.require_model(policy["fixed_model_id"], snapshot)
        selection = await self.policies.resolve(
            {
                "model_id": model["id"],
                "catalog_revision": model["revision"],
                "provider_ref": model["provider_ref"],
                "policy_ref": policy_ref.wire(),
                "max_output_tokens": model["output_limit_tokens"],
            },
            ctx,
        )
        # Conservative envelope estimate; the gateway checks the complete native body as well.
        return ModelWindow(
            policy_ref,
            selection.model["context_limit_tokens"],
            selection.model["output_limit_tokens"],
            serialization_reserve=512,
        )
