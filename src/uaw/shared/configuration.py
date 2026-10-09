"""Platform configuration owner: typed registrations, immutable snapshots and live revocation."""

import hashlib
import hmac
from typing import Any
from urllib.parse import urlsplit

from pydantic import SecretStr

from uaw.infrastructure.db.records import PostgresRecordStore, parameter_hash
from uaw.infrastructure.db.transactions import (
    RecordTransaction,
    TransactionalStore,
    identifier,
    reference,
)
from uaw.shared.contracts import Principal, RequestMeta
from uaw.shared.credentials import CredentialStorePort
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreConflict, StoreMissing

Payload = dict[str, Any]
DEFAULT_DISABLED = (
    "code_execution",
    "local_files",
    "multi_agent",
    "search",
    "mcp",
    "memory",
    "extensions",
)


class ConfigurationService:
    def __init__(
        self, store: PostgresRecordStore, credentials: CredentialStorePort, platform: Principal
    ) -> None:
        self.store = store
        self.transactions = TransactionalStore(store.database)
        self.credentials = credentials
        self.platform = platform

    @staticmethod
    def _admin(actor: Principal) -> None:
        if actor.kind != "admin":
            raise reject(
                "admin_required",
                "Only an authenticated administrator may configure the platform",
                403,
                "permission",
            )

    async def register(
        self, actor: Principal, kind: str, request: Payload, meta: RequestMeta
    ) -> Payload:
        self._admin(actor)
        contracts = {
            "provider": "AdminProvidersConfigureRequest",
            "model": "AdminModelsRegisterRequest",
            "policy": "AdminPoliciesRegisterRequest",
            "environment": "AdminEnvironmentsRegisterRequest",
        }
        if kind not in contracts:
            raise CapabilityUnavailable(kind)
        validate_contract(contracts[kind], request)

        async def write(tx: RecordTransaction) -> Payload:
            if kind == "provider":
                draft = request["provider"]
                self._profile(draft)
                resource_id = draft["id"]
                if "credential_handle" in draft:
                    receipt = await tx.load("credentials", draft["credential_handle"])
                    if receipt.payload["provider_id"] != resource_id:
                        raise reject(
                            "credential_scope_mismatch",
                            "Credential belongs to another provider",
                            403,
                            "permission",
                        )
                expected = meta.expected_revision or 0
                await tx.write("provider.configs", resource_id, "ProviderDraft", draft, expected)
                result = {
                    "id": resource_id,
                    "revision": expected + 1,
                    "kind": draft["kind"],
                    "state": "disconnected",
                    "config_ref": reference("configuration", resource_id, expected + 1),
                }
                await tx.write("providers", resource_id, "ProviderBinding", result, expected)
                return result
            if kind == "model":
                entry = request["entry"]
                provider = await self._reference(tx, "providers", entry["provider_ref"], "provider")
                if provider["kind"] != "model" or provider["state"] == "revoked":
                    raise reject(
                        "model_provider_invalid", "Model requires a configured model provider"
                    )
                if entry["output_limit_tokens"] > entry["context_limit_tokens"]:
                    raise reject("model_limits_invalid", "Output limit exceeds the context limit")
                expected = meta.expected_revision or 0
                result = {**entry, "revision": expected + 1, "status": "active"}
                await tx.write("models", entry["id"], "ModelCatalogEntry", result, expected)
                return result
            if kind == "environment":
                template = request["template"]
                if template["version"] != str((meta.expected_revision or 0) + 1):
                    raise reject(
                        "environment_version_invalid",
                        "Development template version must match its next revision",
                    )
                if template["setup_actions"] or template["verification_actions"]:
                    raise CapabilityUnavailable("environment_process_actions")
                network = await self._reference(
                    tx, "policies", template["network_policy_ref"], "policy"
                )
                validate_contract("CapabilityPolicy", network)
                await tx.write(
                    "environments",
                    template["id"],
                    "EnvironmentTemplate",
                    template,
                    meta.expected_revision or 0,
                )
                return dict(template)
            draft = request["draft"]
            policy = dict(draft["payload"])
            schema = self._policy_schema(policy)
            expected = meta.expected_revision or 0
            policy["revision"] = expected + 1
            if "id" in policy:
                policy["id"] = draft["name"]
            await tx.write("policies", draft["name"], schema, policy, expected)
            return reference("policy", draft["name"], expected + 1)

        return await self.transactions.execute(
            self.platform,
            "configuration",
            meta,
            {
                "action": f"register.{kind}",
                "actor": actor.id,
                "request": request,
                "expected": meta.expected_revision,
            },
            write,
        )

    @staticmethod
    def _profile(draft: Payload) -> None:
        profile = draft["profile_ref"]
        if profile == reference("provider_profile", "tool.builtin.office", 1):
            if (
                draft["kind"] != "local"
                or set(draft) != {"id", "kind", "profile_ref", "settings"}
                or draft["settings"] != {"adapter_version": "1", "currency": "USD"}
            ):
                raise reject("builtin_provider_invalid", "Closed built-in office profile required")
            return
        if (
            profile
            not in (
                reference("provider_profile", "model.http", 1),
                reference("provider_profile", "model.chat_completions", 1),
            )
            or draft["kind"] != "model"
        ):
            raise CapabilityUnavailable("provider_profile")
        values = draft["settings"]
        validate_contract(
            "ModelHttpSettings"
            if profile["id"] == "model.http"
            else "ModelChatCompletionsSettings",
            values,
        )
        validate_contract("NonEmptyText", values["model_name"])
        if "default_reasoning_level" in values and values[
            "default_reasoning_level"
        ] not in values.get("reasoning_levels", []):
            raise reject("provider_reasoning_default_invalid", "Default reasoning must be approved")
        if type(values["timeout_ms"]) is not int or not 1000 <= values["timeout_ms"] <= 300000:
            raise reject("provider_timeout_invalid", "Timeout must be between 1000 and 300000 ms")
        try:
            url = urlsplit(draft["endpoint"])
            _ = url.port
        except ValueError:
            raise reject(
                "provider_endpoint_invalid", "Endpoint is not a valid HTTP address"
            ) from None
        if (
            url.username
            or url.password
            or url.query
            or url.fragment
            or not url.hostname
            or not (
                url.scheme == "https"
                or (url.scheme == "http" and url.hostname in ("127.0.0.1", "::1"))
            )
        ):
            raise reject(
                "provider_endpoint_invalid",
                "Endpoint must be HTTPS or a loopback development URL without credentials",
            )

    @staticmethod
    def _policy_schema(policy: Payload) -> str:
        if "allowed_modes" in policy:
            if policy["allowed_modes"] != ["manual"] or policy["default_mode"] != "manual":
                raise CapabilityUnavailable("non_manual_approval")
            if any(rule["allow_assisted_review"] for rule in policy["rules"]):
                raise CapabilityUnavailable("assisted_approval_review")
            return "ApprovalPolicy"
        if "local_cache_enabled" in policy:
            if policy["mode"] != "local_authoritative":
                raise CapabilityUnavailable("cloud_storage_backend")
            # Supplied deployment policy is recorded; no product storage mode is auto-selected.
            if policy["encrypted"] or policy["local_cache_enabled"]:
                raise CapabilityUnavailable("encrypted_history_or_replica_cache")
            return "StoragePolicy"
        if "allowed_capabilities" in policy:
            return "CapabilityPolicy"
        raise CapabilityUnavailable("policy_kind")

    async def _reference(
        self, tx: RecordTransaction, namespace: str, ref: Payload, kind: str
    ) -> Payload:
        if ref["kind"] != kind:
            raise reject(
                "reference_kind_invalid", "Reference kind is incompatible with this configuration"
            )
        row = await tx.load(namespace, ref["id"])
        if str(row.revision) != ref["version"]:
            raise StoreConflict("reference_revision_conflict")
        return dict(row.payload)

    async def put_secret(self, actor: Principal, request: Payload, meta: RequestMeta) -> Payload:
        self._admin(actor)
        validate_contract("AdminSecretsPutRequest", request)
        handle = (
            "credential-"
            + hashlib.sha256(
                f"{self.platform.id}:{request['provider_id']}:{meta.request_id}".encode()
            ).hexdigest()
        )

        async def verify() -> None:
            try:
                old = await self.credentials.resolve(handle)
            except Exception as exc:
                from uaw.shared.errors import DomainError

                if not isinstance(exc, DomainError) or exc.failure.code != "credential_missing":
                    raise
                await self.credentials.put(handle, SecretStr(request["secret"]))
            else:
                if not hmac.compare_digest(
                    old.get_secret_value().encode(), request["secret"].encode()
                ):
                    raise StoreConflict("idempotency_conflict")

        async def write(tx: RecordTransaction) -> Payload:
            receipt = {"credential_handle": handle, "version": "1"}
            await tx.write(
                "credentials",
                handle,
                "CredentialMetadata",
                {"provider_id": request["provider_id"], "receipt": receipt},
            )
            return receipt

        # Never hash/store the raw secret in the database deduplication or trace records.
        return await self.transactions.execute(
            self.platform,
            "configuration",
            meta,
            {
                "action": "secret.put",
                "actor": actor.id,
                "provider_id": request["provider_id"],
                "handle": handle,
            },
            write,
            verify,
        )

    async def stage(self, actor: Principal, request: Payload, meta: RequestMeta) -> Payload:
        self._admin(actor)
        validate_contract("AdminConfigurationStageRequest", request)

        async def write(tx: RecordTransaction) -> Payload:
            value = {
                **request["configuration"],
                "id": identifier("configuration"),
                "revision": 1,
                "state": "draft",
            }
            await tx.write("configurations", value["id"], "ConfigurationVersion", value)
            return value

        return await self.transactions.execute(
            self.platform,
            "configuration",
            meta,
            {"action": "stage", "actor": actor.id, "request": request},
            write,
        )

    async def _check(self, tx: RecordTransaction, value: Payload) -> None:
        providers = {}
        for ref in value["provider_refs"]:
            provider = await self._reference(tx, "providers", ref, "provider")
            if provider["state"] == "revoked":
                raise reject(
                    "provider_revoked",
                    "Configuration references a revoked provider",
                    403,
                    "permission",
                )
            providers[provider["id"]] = provider
        if len(providers) != len(value["provider_refs"]):
            raise reject("duplicate_reference", "Provider references must be unique")
        model_ids = set()
        for ref in value["model_refs"]:
            model = await self._reference(tx, "models", ref, "model")
            if model["provider_ref"]["id"] not in providers or model["status"] != "active":
                raise reject("model_provider_missing", "Model provider is absent or disabled")
            if providers[model["provider_ref"]["id"]]["revision"] != int(
                model["provider_ref"]["version"]
            ):
                raise StoreConflict("reference_revision_conflict")
            if model["id"] in model_ids:
                raise reject("duplicate_reference", "Model references must be unique")
            model_ids.add(model["id"])
        for ref in value["environment_template_refs"]:
            await self._reference(tx, "environments", ref, "environment")
        approval = await self._reference(tx, "policies", value["approval_policy_ref"], "policy")
        storage = await self._reference(tx, "policies", value["storage_policy_ref"], "policy")
        validate_contract("ApprovalPolicy", approval)
        validate_contract("StoragePolicy", storage)
        seen = set()
        for flag in value["feature_flags"]:
            if flag["id"] not in DEFAULT_DISABLED or flag["enabled"]:
                raise CapabilityUnavailable(flag["id"])
            if flag["scope"].get("resource_refs"):
                raise CapabilityUnavailable("resource_scoped_flags")
            key = (flag["id"], str(sorted(flag["scope"].items())))
            if key in seen:
                raise reject(
                    "duplicate_feature_flag", "Feature flags must be unique within a scope"
                )
            seen.add(key)

    async def validate(self, actor: Principal, configuration_id: str, meta: RequestMeta) -> Payload:
        self._admin(actor)
        validate_contract("ID", configuration_id)

        async def write(tx: RecordTransaction) -> Payload:
            row = await tx.load("configurations", configuration_id)
            if row.payload["state"] != "draft":
                raise reject(
                    "configuration_state_invalid",
                    "Only draft configurations can be validated",
                    409,
                    "conflict",
                )
            if meta.expected_revision != row.revision:
                raise StoreConflict()
            await self._check(tx, row.payload)
            value = {**row.payload, "revision": row.revision + 1, "state": "validated"}
            await tx.write(
                "configurations", configuration_id, "ConfigurationVersion", value, row.revision
            )
            return {
                "valid": True,
                "violations": [],
                "evidence_refs": [],
                "normalized_ref": reference("configuration", configuration_id, value["revision"]),
            }

        return await self.transactions.execute(
            self.platform,
            "configuration",
            meta,
            {
                "action": "validate",
                "actor": actor.id,
                "id": configuration_id,
                "expected": meta.expected_revision,
            },
            write,
        )

    async def activate(self, actor: Principal, configuration_id: str, meta: RequestMeta) -> Payload:
        self._admin(actor)

        async def write(tx: RecordTransaction) -> Payload:
            row = await tx.load("configurations", configuration_id)
            if row.payload["state"] != "validated":
                raise reject(
                    "configuration_state_invalid",
                    "Configuration must be validated before activation",
                    409,
                    "conflict",
                )
            if meta.expected_revision != row.revision:
                raise StoreConflict()
            await self._check(tx, row.payload)
            value = {**row.payload, "revision": row.revision + 1, "state": "active"}
            await tx.write(
                "configurations", configuration_id, "ConfigurationVersion", value, row.revision
            )
            try:
                pointer = await tx.load("configuration.pointer", "current")
                expected = pointer.revision
            except StoreMissing:
                expected = 0
            await tx.write(
                "configuration.pointer",
                "current",
                "Ref",
                reference("configuration", configuration_id, value["revision"]),
                expected,
            )
            await tx.emit(
                "configuration",
                "configuration.activated",
                value,
                base_revision=row.revision - 1,
                result_revision=value["revision"],
            )
            return value

        return await self.transactions.execute(
            self.platform,
            "configuration",
            meta,
            {
                "action": "activate",
                "actor": actor.id,
                "id": configuration_id,
                "expected": meta.expected_revision,
            },
            write,
        )

    async def revoke_provider(
        self, actor: Principal, provider_id: str, meta: RequestMeta
    ) -> Payload:
        self._admin(actor)

        async def write(tx: RecordTransaction) -> Payload:
            row = await tx.load("providers", provider_id)
            if meta.expected_revision != row.revision:
                raise StoreConflict()
            value = {**row.payload, "state": "revoked", "revision": row.revision + 1}
            await tx.write("providers", provider_id, "ProviderBinding", value, row.revision)
            return value

        return await self.transactions.execute(
            self.platform,
            "configuration",
            meta,
            {
                "action": "provider.revoke",
                "actor": actor.id,
                "id": provider_id,
                "expected": meta.expected_revision,
            },
            write,
        )

    async def current(self) -> Payload:
        try:
            pointer = await self.store.get(self.platform, "configuration.pointer", "current")
        except StoreMissing:
            raise reject(
                "configuration_unavailable",
                "An administrator must publish platform configuration",
                503,
                "dependency",
            ) from None
        return await self.snapshot(pointer.payload)

    async def snapshot(self, ref: Payload) -> Payload:
        if ref["kind"] != "configuration":
            raise reject("reference_kind_invalid", "Expected a configuration reference")
        record = await self.store.get(
            self.platform, "configurations", ref["id"], revision=int(ref["version"])
        )
        return record.payload

    async def models(self) -> Payload:
        config = await self.current()
        entries = []
        for ref in config["model_refs"]:
            model = (
                await self.store.get(
                    self.platform, "models", ref["id"], revision=int(ref["version"])
                )
            ).payload
            provider = (
                await self.store.get(self.platform, "providers", model["provider_ref"]["id"])
            ).payload
            if provider["state"] != "revoked":
                entries.append(model)
        return {"items": entries, "snapshot_revision": config["revision"]}

    async def require_model(self, model_id: str, snapshot: Payload | None = None) -> Payload:
        config = snapshot or await self.current()
        for ref in config["model_refs"]:
            if ref["id"] == model_id:
                model = (
                    await self.store.get(
                        self.platform, "models", model_id, revision=int(ref["version"])
                    )
                ).payload
                provider = (
                    await self.store.get(self.platform, "providers", model["provider_ref"]["id"])
                ).payload
                if provider["state"] == "revoked":
                    raise reject("provider_revoked", "Provider has been revoked", 403, "permission")
                return model
        raise reject(
            "model_unavailable",
            "Selected model is absent from the active catalogue",
            409,
            "dependency",
        )

    async def require_capability(
        self,
        capability: str,
        fixed_ref: Payload,
        scope: Payload,
        *,
        implemented: bool,
        boundary: str,
    ) -> None:
        if boundary not in ("discovery", "call", "resume", "child"):
            raise ValueError("Unknown capability boundary")
        for config in (await self.snapshot(fixed_ref), await self.current()):
            flags = [
                f
                for f in config["feature_flags"]
                if f["id"] == capability
                and all(scope.get(k) == v for k, v in f["scope"].items() if k != "resource_refs")
                and (
                    not f["scope"].get("resource_refs")
                    or (
                        bool(scope.get("resource_refs"))
                        and {parameter_hash(r) for r in scope["resource_refs"]}.issubset(
                            {parameter_hash(r) for r in f["scope"]["resource_refs"]}
                        )
                    )
                )
            ]
            if not flags or any(not f["enabled"] for f in flags):
                raise reject(
                    "feature_disabled",
                    "Capability is disabled by platform configuration",
                    403,
                    "permission",
                )
        if not implemented:
            raise CapabilityUnavailable(capability)
