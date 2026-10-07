"""Resolve persisted human policy, never trust an LLM-supplied model or provider."""

from dataclasses import dataclass
from urllib.parse import urlsplit

from uaw.context.seed import revision
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.model.contracts import Payload
from uaw.shared.configuration import ConfigurationService
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import parse_json, validate_contract


@dataclass(frozen=True)
class Selection:
    model: Payload
    provider: Payload
    binding: Payload
    config: Payload


class PolicyResolver:
    def __init__(self, store: PostgresRecordStore, configuration: ConfigurationService) -> None:
        self.store, self.configuration = store, configuration

    async def resolve(self, requested: Payload, ctx: TrustedExecutionContext) -> Selection:
        run = (await self.store.get(ctx.principal, "runs", ctx.run_id or "")).payload
        if run["conversation_id"] != ctx.scope.conversation_id:
            raise reject("model_scope_denied", "Model scope does not match the Run", 403)
        binding = (await self.store.get(ctx.principal, "run.bindings", run["id"])).payload
        policy_ref = binding["model_policy_ref"]
        if requested["policy_ref"] != policy_ref or (
            ctx.model_policy_ref and ctx.model_policy_ref.wire() != policy_ref
        ):
            raise reject("model_policy_denied", "Caller cannot replace the fixed Run policy", 403)
        policy = (
            await self.store.get(
                ctx.principal,
                "model.policies",
                policy_ref["id"],
                revision=revision(policy_ref, "policy"),
            )
        ).payload
        source = policy["source_input_ref"]
        original = (
            await self.store.get(
                ctx.principal, "inputs", source["id"], revision=revision(source, "input")
            )
        ).payload
        choice = parse_json(original["text"])
        if policy["mode"] != "explicit" or policy["fixed_model_id"] != requested["model_id"]:
            raise reject(
                "fixed_model_required",
                "Automatic or replacement model selection is not enabled",
                403,
            )
        if original["conversation_id"] != run["conversation_id"] or choice != {
            "mode": "explicit",
            "model_id": policy["fixed_model_id"],
        }:
            raise reject(
                "model_source_invalid", "Fixed selection has no matching authenticated source", 403
            )
        snapshot = await self.configuration.snapshot(binding["configuration_ref"])
        model = await self.configuration.require_model(requested["model_id"], snapshot)
        if (
            requested["catalog_revision"] != model["revision"]
            or requested["provider_ref"] != model["provider_ref"]
        ):
            raise reject(
                "model_configuration_stale", "Model configuration does not match the catalogue", 412
            )
        ref = model["provider_ref"]
        provider = (
            await self.store.get(
                self.configuration.platform,
                "provider.configs",
                ref["id"],
                revision=revision(ref, "provider"),
            )
        ).payload
        profile = provider["profile_ref"]
        if profile != {"kind": "provider_profile", "id": "model.chat_completions", "version": "1"}:
            raise reject(
                "model_adapter_unavailable", "Register an explicit supported provider protocol", 503
            )
        settings = provider["settings"]
        access_ref = ctx.capability_policy_ref.wire()
        access_record = await self.store.get(ctx.principal, "execution.policies", access_ref["id"])
        if access_record.revision != revision(access_ref, "policy"):
            raise reject(
                "model_capability_stale",
                "Execution permission changed; refresh its trusted context",
                412,
            )
        access = access_record.payload
        validate_contract("CapabilityPolicy", access)
        if (
            access["resource_scope"].get("conversation_id") != run["conversation_id"]
            or "model.generate" not in access["allowed_capabilities"]
            or "model.generate" not in ctx.scope.capabilities
            or "model.generate" in access["denied_capabilities"]
            or urlsplit(provider["endpoint"]).hostname not in access["network_allowlist"]
            or not set(ctx.scope.capabilities).issubset(access["allowed_capabilities"])
            or set(ctx.scope.capabilities).intersection(access["denied_capabilities"])
        ):
            raise reject(
                "model_capability_denied",
                "Execution policy does not allow this model endpoint",
                403,
            )
        if not 1 <= requested["max_output_tokens"] <= model["output_limit_tokens"]:
            raise reject(
                "model_output_limit_invalid", "Output reserve exceeds the selected model limit"
            )
        if "temperature" in requested and not settings["allow_temperature"]:
            raise reject(
                "model_parameter_unsupported", "Temperature is not approved for this model"
            )
        if "reasoning_level" in requested and requested["reasoning_level"] not in settings.get(
            "reasoning_levels", []
        ):
            raise reject(
                "model_parameter_unsupported", "Reasoning level is not approved for this model"
            )
        if (
            requested.get("provider_model_name", settings["model_name"]) != settings["model_name"]
            or "response_model_name" in requested
        ):
            raise reject(
                "model_name_override_denied",
                "Caller cannot supply the provider's response name",
                403,
            )
        return Selection(
            model, provider, binding, {**requested, "provider_model_name": settings["model_name"]}
        )
