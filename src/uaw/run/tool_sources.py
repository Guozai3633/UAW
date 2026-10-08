"""Run-owned Tool authorization. Registration is internal and controller-authenticated."""

from typing import Any

from uaw.infrastructure.db.records import PostgresRecordStore, parameter_hash
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore
from uaw.run.execution_sources import RunExecutionSources
from uaw.shared.configuration import ConfigurationService
from uaw.shared.contracts import JsonObject, Principal, Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, DomainError, reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreConflict, StoreMissing
from uaw.tool.discovery import check_access, require_entry
from uaw.tool.invocation.schema import normalize
from uaw.tool.ledger import ToolLedger
from uaw.tool.ports import ToolAccess
from uaw.tool.registry import RegistryEntry, ToolRegistry

Payload = dict[str, Any]
ROLES = "run.tool.roles"
BINDINGS = "run.tool.bindings"


def binding_key(ctx: TrustedExecutionContext) -> str:
    return parameter_hash({"run_id": ctx.run_id, "agent_id": ctx.agent_id})


def reference(kind: str, key: str, revision: int, payload: Payload) -> Ref:
    return Ref.model_validate(
        {"kind": kind, "id": key, "version": str(revision), "content_hash": parameter_hash(payload)}
    )


class RunToolAccessSources:
    """Explicit per-Run/Agent role binding with current SQL and config checks.

    Roles carry categories, never executable adapters or model overrides. No
    binding is inferred from text or automatically granted to a new Agent.
    Effective capabilities come exclusively from the actual policy intersection.
    """

    def __init__(
        self,
        store: PostgresRecordStore,
        configuration: ConfigurationService,
        runs: RunExecutionSources,
        *,
        environment: str,
        implemented_flags: frozenset[str] = frozenset(),
    ) -> None:
        validate_contract("ID", environment)
        self.store, self.configuration, self.runs = store, configuration, runs
        self.controller = configuration.platform
        self.environment, self.implemented_flags = environment, frozenset(implemented_flags)
        self.transactions = TransactionalStore(store.database)

    def _service(self, actor: Principal) -> None:
        validate_contract("Principal", actor.wire())
        if actor.wire() != self.controller.wire() or actor.kind != "service":
            raise reject("tool_service_denied", "Authenticated controller required", 403)

    async def register_role(
        self, profile: Payload, meta: RequestMeta, *, authenticated_service: Principal
    ) -> Ref:
        self._service(authenticated_service)
        validate_contract("RoleProfile", profile)

        async def write(tx: RecordTransaction) -> Payload:
            try:
                old = await tx.load(ROLES, profile["id"])
            except StoreMissing:
                old = None
            expected = old.revision if old else 0
            if meta.expected_revision != expected or profile["version"] != str(expected + 1):
                raise StoreConflict()
            await tx.write(ROLES, profile["id"], "RoleProfile", profile, expected)
            return reference("role_profile", profile["id"], expected + 1, profile).wire()

        wire = await self.transactions.execute(
            self.controller,
            ROLES,
            meta,
            {"profile": profile, "expected_revision": meta.expected_revision},
            write,
        )
        # A replay cannot return a deleted/revised role as current authorization.
        result = Ref.model_validate(wire)
        await self._role(result)
        return result

    async def _role(self, pin: Ref) -> Payload:
        if pin.kind != "role_profile" or pin.location is not None or pin.access_scope is not None:
            raise reject("tool_role_denied", "A fixed role profile is required", 403)
        row = await self.store.get(self.controller, ROLES, pin.id)
        validate_contract("RoleProfile", row.payload)
        if (
            row.schema_name != "RoleProfile"
            or row.payload["id"] != pin.id
            or row.payload["version"] != str(row.revision)
            or reference("role_profile", pin.id, row.revision, row.payload) != pin
        ):
            raise reject("tool_role_stale", "Role profile revision changed", 412)
        return row.payload

    async def bind(
        self,
        ctx: TrustedExecutionContext,
        role_ref: Ref,
        meta: RequestMeta,
        *,
        authenticated_service: Principal,
    ) -> Ref:
        self._service(authenticated_service)
        await self.runs.current(ctx)
        await self._role(role_ref)
        key = binding_key(ctx)

        async def write(tx: RecordTransaction) -> Payload:
            try:
                old = await tx.load(BINDINGS, key)
            except StoreMissing:
                old = None
            expected = old.revision if old else 0
            if meta.expected_revision != expected:
                raise StoreConflict()
            if old and old.payload["principal"] != ctx.principal.wire():
                raise reject(
                    "tool_owner_transfer_denied", "Binding owner/session cannot change", 403
                )
            payload: Payload = {
                "run_id": ctx.run_id,
                "principal": ctx.principal.wire(),
                "scope": ctx.scope.wire(),
                "model_policy_ref": ctx.model_policy_ref.wire() if ctx.model_policy_ref else None,
                "capability_policy_ref": ctx.capability_policy_ref.wire(),
                "role_ref": role_ref.wire(),
                "environment": self.environment,
                "revision": expected + 1,
                "state": "active",
            }
            if ctx.agent_id:
                payload["agent_id"] = ctx.agent_id
            await tx.write(BINDINGS, key, "RunToolAccessBinding", payload, expected)
            return reference("content", key, expected + 1, payload).wire()

        wire = await self.transactions.execute(
            self.controller,
            BINDINGS,
            meta,
            {
                "ctx": ctx.wire(),
                "role_ref": role_ref.wire(),
                "environment": self.environment,
                "expected_revision": meta.expected_revision,
            },
            write,
        )
        row = await self._binding(ctx)
        result = Ref.model_validate(wire)
        if reference("content", key, row["revision"], row) != result:
            raise reject("tool_binding_stale", "Binding changed before registration returned", 412)
        await self.snapshot(ctx)
        return result

    async def revoke(
        self, ctx: TrustedExecutionContext, meta: RequestMeta, *, authenticated_service: Principal
    ) -> Ref:
        # Cleanup/revocation remains possible after Run cancellation or expiry.
        self._service(authenticated_service)
        key = binding_key(ctx)

        async def write(tx: RecordTransaction) -> Payload:
            row = await tx.load(BINDINGS, key)
            if row.payload["principal"] != ctx.principal.wire():
                raise reject("tool_principal_denied", "Binding belongs to another session", 403)
            if meta.expected_revision != row.revision:
                raise StoreConflict()
            payload = {**row.payload, "revision": row.revision + 1, "state": "revoked"}
            await tx.write(BINDINGS, key, "RunToolAccessBinding", payload, row.revision)
            return reference("content", key, payload["revision"], payload).wire()

        return Ref.model_validate(
            await self.transactions.execute(
                self.controller,
                BINDINGS,
                meta,
                {
                    "revoke": key,
                    "principal": ctx.principal.wire(),
                    "expected_revision": meta.expected_revision,
                },
                write,
            )
        )

    async def _binding(self, ctx: TrustedExecutionContext) -> Payload:
        try:
            row = await self.store.get(self.controller, BINDINGS, binding_key(ctx))
        except StoreMissing:
            raise CapabilityUnavailable("tool.registered_role_binding") from None
        value = row.payload
        validate_contract("RunToolAccessBinding", value)
        if (
            row.schema_name != "RunToolAccessBinding"
            or value["revision"] != row.revision
            or value["run_id"] != ctx.run_id
            or value.get("agent_id") != ctx.agent_id
            or value["principal"] != ctx.principal.wire()
            or value["scope"] != ctx.scope.wire()
            or value["model_policy_ref"]
            != (ctx.model_policy_ref.wire() if ctx.model_policy_ref else None)
            or value["capability_policy_ref"] != ctx.capability_policy_ref.wire()
            or value["environment"] != self.environment
        ):
            raise reject(
                "tool_binding_denied", "Tool binding differs from the trusted context", 403
            )
        if value["state"] != "active":
            raise reject("tool_binding_revoked", "Tool role binding has been revoked", 403)
        return value

    async def snapshot(self, ctx: TrustedExecutionContext) -> ToolAccess:
        fixed = await self._binding(ctx)
        role_ref = Ref.model_validate(fixed["role_ref"])
        role = await self._role(role_ref)
        sources = await self.runs.current(ctx)
        fixed_config, current_config = sources.fixed_configuration, sources.current_configuration
        providers = []
        for pin in fixed_config["provider_refs"]:
            if pin not in current_config["provider_refs"]:
                continue
            row = await self.store.get(self.controller, "providers", pin["id"])
            validate_contract("ProviderBinding", row.payload)
            if (
                row.schema_name == "ProviderBinding"
                and row.payload["id"] == pin["id"]
                and row.payload["revision"] == row.revision
                and str(row.revision) == pin["version"]
                and row.payload["state"] == "active"
                and (
                    not pin.get("content_hash")
                    or pin["content_hash"] == parameter_hash(row.payload)
                )
            ):
                providers.append(Ref.model_validate(pin))
        flags = set()
        for flag in self.implemented_flags:
            try:
                await self.configuration.require_capability(
                    flag,
                    sources.admission["configuration_ref"],
                    ctx.scope.wire(),
                    implemented=True,
                    boundary="call",
                )
            except DomainError as exc:
                if exc.failure.code != "feature_disabled":
                    raise
            else:
                flags.add(flag)
        if await self._binding(ctx) != fixed or await self._role(role_ref) != role:
            raise reject("tool_binding_stale", "Tool authorization changed while resolving", 412)
        again = await self.runs.current(ctx)
        if again != sources:
            raise reject("tool_source_changed", "Current Run/configuration sources changed", 412)
        for pin in providers:
            row = await self.store.get(self.controller, "providers", pin.id)
            if row.payload["state"] != "active" or str(row.revision) != pin.version:
                raise reject("tool_provider_changed", "Provider changed while resolving", 412)
        result = ToolAccess(
            policy_ref=ctx.capability_policy_ref,
            scope=ctx.scope,
            role_categories=frozenset(role["tool_categories"]),
            allowed_capabilities=frozenset(sources.permissions["allowed_capabilities"]),
            denied_capabilities=frozenset(sources.permissions["denied_capabilities"]),
            enabled_flags=frozenset(flags),
            environment=self.environment,
            active_provider_refs=tuple(providers),
        )
        check_access(result, ctx)
        return result


class PureTextResourceReader:
    """Only the exact registered bounded text.inspect spec has no external resources."""

    def __init__(self, registry: ToolRegistry, access: RunToolAccessSources, tool_ref: Ref) -> None:
        self.registry, self.access, self.tool_ref = registry, access, tool_ref

    async def resolve(
        self, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> tuple[Ref, ...]:
        entry = self.entry(call, spec)
        snapshot = await self.access.snapshot(ctx)
        require_entry(entry, snapshot)
        return ()

    def entry(self, call: JsonObject, spec: JsonObject) -> RegistryEntry:
        validate_contract("ValidatedCall", call)
        validate_contract("ToolSpec", spec)
        entry = self.registry.get(self.tool_ref.wire())
        registered = entry.spec()
        schema = registered["input_schema"]
        text = schema.get("properties", {}).get("text", {})
        if (
            spec != registered
            or call["tool_ref"] != self.tool_ref.wire()
            or registered["id"] != "text.inspect"
            or registered["effect"] != "read"
            or schema.get("type") != "object"
            or set(schema.get("properties", {})) != {"text"}
            or schema.get("required") != ["text"]
            or schema.get("additionalProperties") is not False
            or text.get("type") != "string"
            or type(text.get("maxLength")) is not int
            or not 1 <= text["maxLength"] <= 1_048_576
            or normalize({k: v for k, v in call.items() if k != "arguments_hash"}, self.registry)
            != call
        ):
            raise CapabilityUnavailable("tool.action_resource_reader")
        return entry


class RunToolRecoveryAccess:
    """Current data access for one explicitly bound pure text provider.

    Recovery checks stored complete owner/session, fixed model, current role,
    configuration and provider. Execution cancellation/expiry/deny is distinct
    from result-data revocation. This class never returns an execution snapshot.
    Resource-bearing tools need their own current Reader; no generic fallback.
    """

    def __init__(
        self,
        resources: PureTextResourceReader,
        ledger: ToolLedger,
        *,
        provider_ref: Ref,
        provider: Principal,
    ) -> None:
        validate_contract("Principal", provider.wire())
        if provider.kind != "service":
            raise ValueError("Recovery provider must be an authenticated internal service")
        self.resources, self.provider_ref, self.provider = resources, provider_ref, provider
        self.ledger = ledger

    async def check(
        self,
        call: JsonObject,
        spec: JsonObject,
        ctx: TrustedExecutionContext,
        *,
        provider: Principal,
    ) -> None:
        if (
            provider.wire() != self.provider.wire()
            or spec["provider_ref"] != self.provider_ref.wire()
        ):
            raise reject("tool_recovery_provider_denied", "Original provider identity differs", 403)
        entry = self.resources.entry(call, spec)
        access = self.resources.access
        fixed_call, fixed_spec, _ = await self.ledger.action(str(call["action_id"]), ctx)
        if fixed_call != call or fixed_spec != spec or await self.ledger.attempt(ctx) != call:
            raise reject("tool_recovery_action_denied", "Original registered action differs", 403)
        binding = await access._binding(ctx)
        role_ref = Ref.model_validate(binding["role_ref"])
        role = await access._role(role_ref)
        if not set(entry.spec()["categories"]) <= set(role["tool_categories"]):
            raise reject("tool_recovery_role_denied", "Current role denies result data", 403)
        sources = await access.runs.data(ctx)
        pin = self.provider_ref.wire()
        if any(
            pin not in config["provider_refs"]
            for config in (sources.fixed_configuration, sources.current_configuration)
        ):
            raise reject("tool_recovery_provider_denied", "Provider is no longer configured", 403)
        row = await access.store.get(access.controller, "providers", self.provider_ref.id)
        validate_contract("ProviderBinding", row.payload)
        if (
            row.schema_name != "ProviderBinding"
            or row.payload["id"] != self.provider_ref.id
            or row.payload["revision"] != row.revision
            or str(row.revision) != self.provider_ref.version
            or row.payload["state"] != "active"
            or (
                self.provider_ref.content_hash is not None
                and self.provider_ref.content_hash != parameter_hash(row.payload)
            )
        ):
            raise reject("tool_recovery_provider_denied", "Current provider differs", 403)
        if (
            await access._binding(ctx) != binding
            or await access._role(role_ref) != role
            or await access.runs.data(ctx) != sources
            or await access.store.get(access.controller, "providers", self.provider_ref.id) != row
        ):
            raise reject("tool_recovery_source_changed", "Current result-data sources changed", 412)
