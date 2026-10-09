"""Internal acceptance of the closed local office provider; no network credentials."""

from typing import cast

from uaw.infrastructure.db.transactions import RecordTransaction, reference
from uaw.shared.configuration import ConfigurationService
from uaw.shared.contracts import JsonObject, Principal, Ref, RequestMeta
from uaw.shared.errors import reject
from uaw.shared.stores import StoreConflict, StoreMissing
from uaw.tool.invocation.schema import normalize
from uaw.tool.providers.arithmetic import arithmetic_spec, calculate
from uaw.tool.providers.json_data import inspect_json, json_data_spec
from uaw.tool.providers.text import inspect_text, text_spec
from uaw.tool.registry import ToolRegistry
from uaw.tool.schema import compile_schema


class BuiltinToolConnectionAcceptance:
    def __init__(self, configuration: ConfigurationService) -> None:
        self.configuration = configuration

    async def accept(self, actor: Principal, provider: Ref, meta: RequestMeta) -> JsonObject:
        config = self.configuration
        config._admin(actor)
        if (
            not provider.version.isascii()
            or not provider.version.isdigit()
            or provider.wire() != reference("provider", provider.id, int(provider.version))
            or meta.expected_revision != int(provider.version)
        ):
            raise StoreConflict()

        async def write(tx: RecordTransaction) -> JsonObject:
            row = await tx.load("providers", provider.id)
            draft = await tx.load("provider.configs", provider.id)
            config._profile(draft.payload)
            if (
                row.revision != meta.expected_revision
                or draft.revision != row.revision
                or row.payload["revision"] != row.revision
                or row.payload["id"] != provider.id
                or draft.payload["id"] != provider.id
                or row.payload["kind"] != "local"
                or row.payload["state"] != "disconnected"
                or draft.payload["profile_ref"]
                != reference("provider_profile", "tool.builtin.office")
            ):
                raise reject(
                    "builtin_provider_stale", "Closed configured local provider required", 412
                )
            # Actual built-in computations, not a caller supplied 'connected' bit.
            registry = ToolRegistry()
            cases = (
                (
                    arithmetic_spec(provider),
                    {"operation": "add", "operands": ["1", "2"]},
                    calculate,
                    {
                        "value": "3",
                        "precision": 34,
                        "rounding": "ROUND_HALF_EVEN",
                        "rounded": False,
                        "inexact": False,
                    },
                ),
                (
                    json_data_spec(provider),
                    {"text": '{"x":1}', "required_keys": ["x"]},
                    inspect_json,
                    None,
                ),
                (text_spec(provider), {"text": "abc"}, lambda a: inspect_text(a["text"]), None),
            )
            for spec, arguments, compute, expected in cases:
                registry.register(spec, expected_revision=registry.revision)
                entry = registry.get({"kind": "configuration", "id": spec["id"], "version": "1"})
                call = normalize(
                    {
                        "tool_ref": registry.reference(entry),
                        "arguments": arguments,
                        "action_id": "builtin-accept",
                    },
                    registry,
                )
                actual = compute(call["arguments"])
                if not compile_schema(cast(JsonObject, spec["output_schema"])).is_valid(actual):
                    raise reject("builtin_probe_failed", "Output schema failed", 503)
                if expected is not None and actual != expected:
                    raise reject("builtin_probe_failed", "Actual built-in computation failed", 503)
                if spec["id"] == "data.inspect_json" and (
                    actual["missing_keys"] or actual["keys"] != ["x"] or actual["count"] != 1
                ):
                    raise reject("builtin_probe_failed", "Actual JSON inspection failed", 503)
            revision = row.revision + 1
            await tx.write(
                "provider.configs", provider.id, "ProviderDraft", draft.payload, row.revision
            )
            value = {
                **row.payload,
                "revision": revision,
                "state": "active",
                "config_ref": reference("configuration", provider.id, revision),
            }
            await tx.write("providers", provider.id, "ProviderBinding", value, row.revision)
            return value

        return await config.transactions.execute(
            config.platform,
            "configuration",
            meta,
            {"action": "builtin.accept", "actor": actor.wire(), "provider": provider.wire()},
            write,
        )


async def publish_builtin_office(
    config: ConfigurationService, actor: Principal, request_id: str
) -> Ref:
    """Explicit administrator action; future Runs see it, existing pins remain unchanged."""
    config._admin(actor)
    key = "builtin-office-v1"
    draft = {
        "id": key,
        "kind": "local",
        "profile_ref": reference("provider_profile", "tool.builtin.office"),
        "settings": {"adapter_version": "1", "currency": "USD"},
    }
    try:
        row = await config.store.get(config.platform, "providers", key)
        provider = row.payload
        current_draft = await config.store.get(config.platform, "provider.configs", key)
        if current_draft.payload != draft:
            raise StoreConflict()
    except StoreMissing:
        provider = await config.register(
            actor,
            "provider",
            {"provider": draft},
            RequestMeta(
                request_id=request_id + "-register", schema_version="0.1", expected_revision=0
            ),
        )
    if provider["state"] == "disconnected":
        provider = await BuiltinToolConnectionAcceptance(config).accept(
            actor,
            Ref.model_validate(reference("provider", key, provider["revision"])),
            RequestMeta(
                request_id=request_id + "-accept",
                schema_version="0.1",
                expected_revision=provider["revision"],
            ),
        )
    if provider["state"] != "active":
        raise reject("builtin_provider_revoked", "Built-in provider is not active", 403)
    pin = reference("provider", key, provider["revision"])
    active = await config.current()
    if pin not in active["provider_refs"]:
        value = {
            name: active[name]
            for name in (
                "model_refs",
                "environment_template_refs",
                "feature_flags",
                "approval_policy_ref",
                "storage_policy_ref",
            )
        }
        value["provider_refs"] = [r for r in active["provider_refs"] if r["id"] != key] + [pin]
        staged = await config.stage(
            actor,
            {"configuration": value},
            RequestMeta(request_id=request_id + "-stage", schema_version="0.1"),
        )
        await config.validate(
            actor,
            staged["id"],
            RequestMeta(
                request_id=request_id + "-validate", schema_version="0.1", expected_revision=1
            ),
        )
        await config.activate(
            actor,
            staged["id"],
            RequestMeta(
                request_id=request_id + "-activate", schema_version="0.1", expected_revision=2
            ),
        )
    return Ref.model_validate(pin)
