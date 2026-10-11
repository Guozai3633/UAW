"""Immutable per-Run native source admission and fresh original-source checks."""

import json
from typing import TYPE_CHECKING, Any, Protocol

from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.db.transactions import RecordTransaction
from uaw.infrastructure.installed_receipt import current_root
from uaw.shared.configuration import FILE_PROFILE
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.workspace.ports import RootGrant

if TYPE_CHECKING:
    from uaw.composition import Container

Payload = dict[str, Any]
NAMESPACE = "run.file.sources"


class FileRunAdmissionPort(Protocol):
    async def admit(
        self,
        tx: RecordTransaction,
        actor: Principal,
        run: Payload,
        binding: Payload,
        configuration: Payload,
    ) -> None: ...


def root_identity(grant: RootGrant) -> str:
    # No native path/file body enters the Run source contract or its digest.
    return parameter_hash(
        {
            "root_handle": grant.root_handle,
            "revision": grant.revision,
            "workspace_ref": grant.workspace_ref.wire(),
            "device_id": grant.device_id,
            "owner": grant.owner.wire() if grant.owner else None,
            "expires_at": grant.expires_at.isoformat() if grant.expires_at else None,
            "ticket": grant.selection_ticket_id,
            "key": grant.selection_key_id,
            "signature": grant.selection_signature,
            "confirmation_expires_at": grant.confirmation_expires_at.isoformat()
            if grant.confirmation_expires_at
            else None,
        }
    )


class InstalledFileRunSources:
    def __init__(self, container: Container) -> None:
        self.container = container

    @staticmethod
    def scopes(configuration: Payload, conversation_id: str) -> list[Payload]:
        return [
            f["scope"]
            for f in configuration["feature_flags"]
            if f["id"] == "local_files"
            and f["enabled"]
            and f["scope"].get("conversation_id") == conversation_id
        ]

    async def _native(self, owner: Principal, workspace: Ref) -> Payload:
        c = self.container
        if c.installed_lifecycle is None:
            raise CapabilityUnavailable("file.original_run_installed_sources")
        lifecycle = c.installed_lifecycle
        launch = await lifecycle.owned_ready(owner, workspace)
        entry = lifecycle.active
        if entry is None or launch.connection is None:
            raise CapabilityUnavailable("file.original_run_installed_sources")
        grant = await current_root(launch)
        device = await launch.connection.devices.current(
            grant.device_id, authenticated_principal=owner
        )
        if device["source"]["owner"] != owner.wire():
            raise reject("file_run_owner_denied", "Original device owner differs", 403)
        if (
            await current_root(launch) != grant
            or await launch.connection.devices.current(
                grant.device_id, authenticated_principal=owner
            )
            != device
        ):
            raise reject("file_run_source_changed", "Original native proof changed", 412)
        if (
            lifecycle.active is not entry
            or entry.launch is not launch
            or entry.stopping
            or entry.done.is_set()
        ):
            raise CapabilityUnavailable("file.original_run_installed_sources")
        assert grant.expires_at is not None and grant.confirmation_expires_at is not None
        return {
            "launch_id": entry.id,
            "workspace_ref": workspace.wire(),
            "device_ref": {
                "kind": "device",
                "id": grant.device_id,
                "version": str(device["revision"]),
                "content_hash": parameter_hash(device),
            },
            "root_identity_hash": root_identity(grant),
            "expires_at": min(grant.expires_at, grant.confirmation_expires_at).isoformat(),
        }

    async def _provider(self, configuration: Payload) -> Ref:
        c = self.container
        if c.records is None or c.configuration is None:
            raise CapabilityUnavailable("file.original_run_configuration")
        matches = []
        for ref in configuration["provider_refs"]:
            draft = await c.records.get(c.configuration.platform, "provider.configs", ref["id"])
            if draft.payload["profile_ref"] == FILE_PROFILE:
                c.configuration._profile(draft.payload)
                row = await c.records.get(c.configuration.platform, "providers", ref["id"])
                if (
                    row.revision != draft.revision
                    or str(row.revision) != ref["version"]
                    or row.payload["state"] != "active"
                ):
                    raise reject("file_run_provider_changed", "Original file provider differs", 412)
                matches.append(Ref.model_validate(ref))
        if len(matches) != 1:
            raise CapabilityUnavailable("file.original_run_provider")
        return matches[0]

    async def admit(
        self,
        tx: RecordTransaction,
        actor: Principal,
        run: Payload,
        binding: Payload,
        configuration: Payload,
    ) -> None:
        scopes = self.scopes(configuration, run["conversation_id"])
        if not scopes:
            return
        if len(scopes) != 1 or len(scopes[0].get("resource_refs", [])) != 1:
            raise reject("file_run_scope_denied", "One exact admitted workspace required", 403)
        c = self.container
        assert c.configuration is not None
        workspace = Ref.model_validate(scopes[0]["resource_refs"][0])
        await c.configuration.require_capability(
            "file_access",
            binding["configuration_ref"],
            scopes[0],
            implemented=True,
            boundary="call",
        )
        provider = await self._provider(configuration)
        policy = (await tx.load("model.policies", binding["model_policy_ref"]["id"])).payload
        if (
            policy["mode"] != "explicit"
            or str(policy["revision"]) != binding["model_policy_ref"]["version"]
        ):
            raise reject("file_run_model_denied", "Original explicit user model required", 403)
        await c.configuration.require_model(policy["fixed_model_id"], configuration)
        source = await self._native(actor, workspace)
        await c.configuration.require_capability(
            "file_access",
            binding["configuration_ref"],
            scopes[0],
            implemented=True,
            boundary="call",
        )
        current = await c.configuration.current()
        if (
            provider.wire() not in current["provider_refs"]
            or await self._provider(configuration) != provider
        ):
            raise reject("file_run_provider_changed", "Provider changed during admission", 412)
        value = {
            **source,
            "run_id": run["id"],
            "owner": actor.wire(),
            "conversation_id": run["conversation_id"],
            "task_id": run["task_id"],
            "configuration_ref": binding["configuration_ref"],
            "model_policy_ref": binding["model_policy_ref"],
            "fixed_model_id": policy["fixed_model_id"],
            "provider_ref": provider.wire(),
        }
        validate_contract("FileRunSourceBinding", value)
        # The submission transaction rolls back its Run/input/job on any failure.
        await tx.write(NAMESPACE, run["id"], "FileRunSourceBinding", value)

    async def current(self, ctx: TrustedExecutionContext, workspace: Ref) -> Payload:
        c = self.container
        if c.records is None or c.configuration is None or c.run_sources is None:
            raise CapabilityUnavailable("file.original_run_configuration")
        row = await c.records.get(ctx.principal, NAMESPACE, ctx.run_id or "")
        validate_contract("FileRunSourceBinding", row.payload)
        value: Payload = json.loads(json.dumps(row.payload, allow_nan=False))
        if (
            row.revision != 1
            or row.schema_name != "FileRunSourceBinding"
            or (
                value["run_id"],
                value["owner"],
                value["conversation_id"],
                value["task_id"],
                value["workspace_ref"],
                value["model_policy_ref"],
            )
            != (
                ctx.run_id,
                ctx.principal.wire(),
                ctx.conversation_id,
                ctx.task_id,
                workspace.wire(),
                ctx.model_policy_ref.wire() if ctx.model_policy_ref else None,
            )
            or workspace not in ctx.scope.resource_refs
        ):
            raise reject("file_run_binding_denied", "Original admitted Run scope required", 403)
        sources = await c.run_sources.data(ctx)
        if sources.admission["configuration_ref"] != value["configuration_ref"]:
            raise reject("file_run_binding_changed", "Original Run configuration changed", 412)
        model_policy = await c.records.get(
            ctx.principal, "model.policies", value["model_policy_ref"]["id"]
        )
        if model_policy.payload["fixed_model_id"] != value["fixed_model_id"]:
            raise reject("file_run_model_denied", "Original fixed user model differs", 403)
        await c.configuration.require_capability(
            "file_access",
            value["configuration_ref"],
            ctx.scope.wire(),
            implemented=True,
            boundary="call",
        )
        if (await self._provider(sources.fixed_configuration)).wire() != value[
            "provider_ref"
        ] or value["provider_ref"] not in sources.current_configuration["provider_refs"]:
            raise reject("file_run_provider_changed", "Original file provider changed", 412)
        native = await self._native(ctx.principal, workspace)
        if (
            any(value[k] != v for k, v in native.items())
            or await c.records.get(ctx.principal, NAMESPACE, ctx.run_id or "") != row
        ):
            raise reject("file_run_source_changed", "Original launch/root/device changed", 412)
        if await c.run_sources.data(ctx) != sources:
            raise reject("file_run_source_changed", "Current Run/model/configuration changed", 412)
        await c.configuration.require_capability(
            "file_access",
            value["configuration_ref"],
            ctx.scope.wire(),
            implemented=True,
            boundary="call",
        )
        return value
