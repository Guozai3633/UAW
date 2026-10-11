"""Browser-owned native sources for the original File Tool/Runner bridge.

This assembly neither publishes a provider nor enables a flag or grants a scope.
The owning lifecycle retains process/key cleanup. No incoming path opens a file.
"""

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from uaw_runner.admissions import PersistentAdmissions
from uaw_runner.control_signing import ControlCommandSigner, ControlKeyBinding
from uaw_runner.keys import Ed25519SignatureAdapter, ProtectedSigner
from uaw_runner.pairing import LocalRoots
from uaw_runner.protocol import RunnerProtocol
from uaw_runner.read_state import ReadExecutionJournal
from uaw_runner.receipts import ReceiptJournal
from uaw_runner.root_source import NativeRootSource, PersistentRootGrants

from uaw.composition import (
    Container,
    FileToolBindings,
    RunnerControlBindings,
    assemble_file_tool,
    assemble_runner_control,
)
from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.installed_journal import InstalledJournalRecovery
from uaw.infrastructure.installed_lifecycle import InstalledLifecycle
from uaw.infrastructure.installed_receipt import current_root
from uaw.infrastructure.installed_tool_authority import InstalledFileResources
from uaw.infrastructure.runner_pipe import RunnerPipeClient
from uaw.run.file_admission import InstalledFileRunSources
from uaw.run.file_bridge import FileDeviceRoute, RegisteredFileBridge
from uaw.shared.contracts import JsonObject, Principal, Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.tool.approval import ToolApprovalAdapter
from uaw.tool.invocation.schema import normalize
from uaw.tool.ledger import ToolLedger, action_key
from uaw.tool.providers.file_read import file_arguments
from uaw.tool.registry import ToolRegistry
from uaw.workspace.binding import RootBindings


class InstalledFileRoute:
    def __init__(
        self, lifecycle: InstalledLifecycle, *, admitted: InstalledFileRunSources | None = None
    ) -> None:
        self.lifecycle = lifecycle
        self.admitted = admitted

    async def current(self, workspace: Ref, ctx: TrustedExecutionContext) -> FileDeviceRoute:
        workspace = Ref.model_validate_json(json.dumps(workspace.wire(), allow_nan=False))
        ctx = TrustedExecutionContext.model_validate_json(json.dumps(ctx.wire(), allow_nan=False))
        if workspace not in ctx.scope.resource_refs:
            raise reject("file_workspace_denied", "Exact admitted workspace required", 403)
        if self.admitted is not None:
            await self.admitted.current(ctx, workspace)
        launch = await self.lifecycle.owned_source(ctx.principal, workspace)
        entry = self.lifecycle.active
        connection = launch.connection
        assert connection is not None and launch.control_key is not None
        grant = await current_root(launch)
        device = await connection.devices.current(
            grant.device_id, authenticated_principal=ctx.principal
        )
        if await current_root(launch) != grant:
            raise reject("file_installed_root_changed", "Original root changed while waiting", 412)
        if (
            await connection.devices.current(grant.device_id, authenticated_principal=ctx.principal)
            != device
        ):
            raise reject("file_installed_device_changed", "Current device binding changed", 412)
        if (
            entry is None
            or self.lifecycle.active is not entry
            or entry.launch is not launch
            or entry.stopping
            or entry.done.is_set()
        ):
            raise CapabilityUnavailable("file.current_browser_owned_launch")
        return FileDeviceRoute(
            Ref(
                kind="device",
                id=grant.device_id,
                version=str(device["revision"]),
                content_hash=parameter_hash(device),
            ),
            workspace,
        )


class RegisteredFileDataAccess:
    """Current result-data authority, independent of new execution approval.

    File/root/device checks are made by the owning bridge. This adapter does not
    recurse into that bridge, create an attempt, send, or read a result body.
    """

    def __init__(
        self, container: Container, registry: ToolRegistry, provider_ref: Ref, provider: Principal
    ) -> None:
        if container.tool_access is None or container.records is None:
            raise CapabilityUnavailable("file.current_data_authority")
        self.access, self.registry = container.tool_access, registry
        self.ledger = ToolLedger(container.records)
        self.provider_ref = Ref.model_validate_json(
            json.dumps(provider_ref.wire(), allow_nan=False)
        )
        self.provider = Principal.model_validate_json(json.dumps(provider.wire(), allow_nan=False))
        if provider.kind != "service":
            raise ValueError("Actual internal file provider required")

    async def check(
        self,
        call: dict[str, Any],
        spec: dict[str, Any],
        ctx: TrustedExecutionContext,
        *,
        provider: Principal,
    ) -> None:
        call = json.loads(json.dumps(call, allow_nan=False))
        spec = json.loads(json.dumps(spec, allow_nan=False))
        ctx = TrustedExecutionContext.model_validate_json(json.dumps(ctx.wire(), allow_nan=False))
        if provider != self.provider or spec["provider_ref"] != self.provider_ref.wire():
            raise reject("file_data_provider_denied", "Original file provider differs", 403)
        arguments = file_arguments(call, spec, self.provider_ref)
        if Ref.model_validate(arguments["workspace_ref"]) not in ctx.scope.resource_refs:
            raise reject("file_data_workspace_denied", "Exact admitted workspace required", 403)
        if (
            self.registry.get(call["tool_ref"]).spec() != spec
            or normalize({k: v for k, v in call.items() if k != "arguments_hash"}, self.registry)
            != call
        ):
            raise reject(
                "file_data_registration_denied", "Current registered file tool differs", 403
            )
        fixed_call, fixed_spec, _ = await self.ledger.action(call["action_id"], ctx)
        if (fixed_call, fixed_spec) != (call, spec) or await self.ledger.attempt(ctx) != call:
            raise reject("file_data_action_denied", "Original file attempt differs", 403)
        access = self.access
        binding = await access._binding(ctx)
        role_ref = Ref.model_validate(binding["role_ref"])
        role = await access._role(role_ref)
        if not set(spec["categories"]) <= set(role["tool_categories"]):
            raise reject("file_data_role_denied", "Current role denies file result data", 403)
        sources = await access.runs.data(ctx)
        if any(
            self.provider_ref.wire() not in config["provider_refs"]
            for config in (sources.fixed_configuration, sources.current_configuration)
        ):
            raise reject("file_data_provider_denied", "File provider is no longer configured", 403)
        row = await access.store.get(access.controller, "providers", self.provider_ref.id)
        validate_contract("ProviderBinding", row.payload)
        if (
            row.schema_name != "ProviderBinding"
            or row.payload["id"] != self.provider_ref.id
            or row.revision != row.payload["revision"]
            or str(row.revision) != self.provider_ref.version
            or row.payload["state"] != "active"
            or (
                self.provider_ref.content_hash is not None
                and self.provider_ref.content_hash != parameter_hash(row.payload)
            )
        ):
            raise reject("file_data_provider_denied", "Current file provider differs", 403)
        if (
            await access._binding(ctx) != binding
            or await access._role(role_ref) != role
            or await access.runs.data(ctx) != sources
            or await access.store.get(access.controller, "providers", self.provider_ref.id) != row
        ):
            raise reject("file_data_source_changed", "Current file data sources changed", 412)


class OriginalFileApprovalGate:
    def __init__(self, ledger: ToolLedger) -> None:
        self.ledger = ledger
        self.approvals: ToolApprovalAdapter | None = None

    async def check(self, request: JsonObject, ctx: TrustedExecutionContext) -> None:
        if self.approvals is None:
            raise CapabilityUnavailable("file.original_tool_approval")
        call = await self.ledger.attempt(ctx)
        fixed_call, spec, original = await self.ledger.action(call["action_id"], ctx)
        if (
            fixed_call != call
            or original != ctx
            or spec["id"] != "file.read"
            or request["context"] != ctx.wire()
            or request["parameters"] != {"action": "file.read", "parameters": call["arguments"]}
        ):
            raise reject("file_original_approval_denied", "Original Tool request differs", 403)
        key = action_key(ctx, str(call["action_id"]))
        original_request = await self.ledger.get("tool.approval.requests", key, ctx)
        if original_request is None:
            raise reject("approval_pending", "Original Tool approval required", 403)
        service = self.approvals.approvals
        approval_id = "approval-" + parameter_hash({"run": ctx.run_id, "action": call["action_id"]})
        approval = await service.get(ctx.principal, approval_id)
        if approval["status"] != "approved":
            raise reject(
                "approval_" + str(approval["status"]),
                "Original approval does not allow the read",
                403,
            )
        await service.recheck(
            Ref(kind="approval", id=approval_id, version=str(approval["revision"])),
            original_request,
            ctx,
        )


@dataclass(frozen=True)
class InstalledFileBindings:
    control: RunnerControlBindings
    bridge: RegisteredFileBridge
    tool: FileToolBindings
    route: InstalledFileRoute


async def assemble_installed_file(
    container: Container,
    *,
    owner: Principal,
    workspace: Ref,
    registry: ToolRegistry,
    tool_ref: Ref,
    provider: Principal,
    money_ceiling: str,
) -> InstalledFileBindings:
    lifecycle = container.installed_lifecycle
    if lifecycle is None or container.records is None:
        raise CapabilityUnavailable("file.browser_installed_sources")
    launch = await lifecycle.owned_ready(owner, workspace)
    connection, key = launch.connection, launch.control_key
    if connection is None or connection.session is None or key is None:
        raise CapabilityUnavailable("file.current_control_sources")
    directory = launch.state.path.parent
    grants = await asyncio.to_thread(PersistentRootGrants, directory / "grants.sqlite")
    native = await asyncio.to_thread(LocalRoots, directory / "native.sqlite")
    signatures = Ed25519SignatureAdapter(launch.state)
    signer = ControlCommandSigner(
        (ControlKeyBinding(key.device_id, key.key_id, key.credential_handle),),
        directory=launch.state,
        signer=ProtectedSigner(launch.state, launch.vault),
    )
    gate = OriginalFileApprovalGate(ToolLedger(container.records))
    control = assemble_runner_control(
        container,
        channels=connection.registry,
        gate=gate,
        signer=signer,
        root_factory=lambda mapping: NativeRootSource(
            RootBindings(grants),
            grants=grants,
            selections=launch.state,
            native_roots=native,
            mapping=mapping,
            directory=launch.state,
        ),
    )
    route = InstalledFileRoute(lifecycle, admitted=container.file_run_sources)
    provider_ref = Ref.model_validate(registry.get(tool_ref.wire()).spec()["provider_ref"])
    access = RegisteredFileDataAccess(container, registry, provider_ref, provider)
    # This verifier has no execution authority or principal mapping. It can
    # only verify existing signed receipts via the original registered Reader.
    journal = ReceiptJournal(
        directory / "receipts.sqlite",
        protocol=RunnerProtocol(
            device_id=key.device_id,
            bindings=RootBindings(grants),
            admissions=PersistentAdmissions(directory / "admissions.sqlite"),
            signatures=signatures,
        ),
        reader=control.receipt_commands,
    )
    bridge = RegisteredFileBridge(
        commands=control.commands,
        pipe=RunnerPipeClient(
            session=connection.session,
            registry=connection.registry,
            commands=control.receipt_commands,
            signatures=signatures,
            recovery=InstalledJournalRecovery(
                executions=ReadExecutionJournal(directory / "reads.sqlite"),
                journal=journal,
                commands=control.receipt_commands,
            ),
        ),
        routes=route,
        access=access,
        provider_ref=provider_ref,
        provider=provider,
        signatures=signatures,
    )
    assert control.commands.roots is not None
    tool = assemble_file_tool(
        container,
        registry=registry,
        tool_ref=tool_ref,
        provider=provider,
        bridge=bridge,
        recovery_access=access,
        signatures=signatures,
        money_ceiling=money_ceiling,
        resource_reader=InstalledFileResources(control.commands.roots, key.device_id),
    )
    assert tool.facade.invocation is not None
    gate.approvals = tool.facade.invocation.approvals
    if gate.approvals is None:
        raise CapabilityUnavailable("file.original_tool_approval")
    if await lifecycle.owned_ready(owner, workspace) is not launch:
        raise reject("file_installed_source_changed", "Owned native instance changed", 412)
    return InstalledFileBindings(control, bridge, tool, route)
