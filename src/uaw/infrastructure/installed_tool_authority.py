"""Child-side original SQL approval and verify-only control-key sources."""

import asyncio
import json
from typing import TYPE_CHECKING, Any

from uaw_runner.keys import Ed25519SignatureAdapter, signature_key_id

from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.installed_file_approval import InstalledFileApprovalAuthority
from uaw.infrastructure.installed_root_check import checked_file_root
from uaw.run.approval import ApprovalService
from uaw.run.tool_sources import RunToolAccessSources
from uaw.shared.contracts import JsonObject, Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.ports import RunnerRootSourcePort
from uaw.tool.authority import ToolApprovalAuthority
from uaw.tool.ledger import ToolLedger
from uaw.tool.providers.file_read import file_arguments, file_read_spec
from uaw.tool.registry import AdapterBinding, ToolRegistry
from uaw.workspace.contracts import RunnerCommand, RunnerRootSnapshot
from uaw.workspace.ports import CurrentKeyDirectory

if TYPE_CHECKING:
    from uaw.composition import Container


class InstalledControlVerifier:
    def __init__(
        self, directory: CurrentKeyDirectory, *, device_id: str, control_key_id: str
    ) -> None:
        self.directory, self.device_id, self.control_key_id = directory, device_id, control_key_id

    async def sign(self, draft: JsonObject, *, device_id: str) -> JsonObject:
        raise CapabilityUnavailable("installed.child_control_signing")

    async def verify(self, command: JsonObject, *, device_id: str) -> None:
        signed = RunnerCommand.model_validate_json(json.dumps(command, allow_nan=False))
        if device_id != self.device_id or signature_key_id(signed.signature) != self.control_key_id:
            raise reject("installed_control_key_denied", "Original control signature required", 403)
        key = await asyncio.to_thread(
            self.directory.lookup, self.control_key_id, device_id=device_id
        )
        if (
            key.revoked
            or key.role != "control"
            or key.device_id != device_id
            or key.key_id != self.control_key_id
        ):
            raise reject(
                "installed_control_key_denied", "Current original control key required", 403
            )
        if not await asyncio.to_thread(
            Ed25519SignatureAdapter(self.directory).verify_command, signed, device_id=device_id
        ):
            raise reject(
                "installed_control_signature_denied", "Original control signature rejected", 403
            )
        if (
            await asyncio.to_thread(self.directory.lookup, self.control_key_id, device_id=device_id)
            != key
        ):
            raise reject(
                "installed_control_key_changed", "Control key changed during verification", 412
            )


class InstalledFileResources:
    def __init__(
        self, roots: RunnerRootSourcePort, device_id: str, *, observed: JsonObject | None = None
    ) -> None:
        self.roots, self.device_id = roots, device_id
        self.observed = (
            None if observed is None else json.loads(json.dumps(observed, allow_nan=False))
        )

    async def resolve(
        self, call: dict[str, Any], spec: dict[str, Any], ctx: TrustedExecutionContext
    ) -> tuple[Ref, ...]:
        pin = Ref.model_validate(spec["provider_ref"])
        if spec != file_read_spec(pin):
            raise reject(
                "installed_file_spec_denied", "Original closed file.read ToolSpec required", 403
            )
        args = file_arguments(call, spec, pin)
        workspace = Ref.model_validate(args["workspace_ref"])
        if workspace not in ctx.scope.resource_refs:
            raise reject("installed_file_workspace_denied", "Original Run workspace required", 403)
        snapshot = RunnerRootSnapshot.model_validate_json(
            json.dumps(
                self.observed
                if self.observed is not None
                else await self.roots.current(self.device_id, workspace, ctx),
                allow_nan=False,
            )
        )
        root = snapshot.wire()
        if (
            root["owner"] != ctx.principal.wire()
            or root["device_id"] != self.device_id
            or root["workspace_ref"] != workspace.wire()
            or "file.read" not in snapshot.allowed_actions
        ):
            raise reject(
                "installed_file_root_denied", "Current original native read root required", 403
            )
        return (workspace,)


class InstalledToolApprovalGate:
    def __init__(self, container: Container, roots: RunnerRootSourcePort, device_id: str) -> None:
        if (
            not container.records
            or not container.configuration
            or not container.run_sources
            or not container.tool_access
            or not container.execution_permissions
        ):
            raise CapabilityUnavailable("installed.original_tool_authority")
        self.container, self.roots, self.device_id = container, roots, device_id

    async def check(self, request: JsonObject, ctx: TrustedExecutionContext) -> None:
        await self._check(request, ctx, InstalledFileResources(self.roots, self.device_id))

    async def check_root(
        self,
        request: JsonObject,
        ctx: TrustedExecutionContext,
        *,
        roots: RunnerRootSourcePort,
        device_id: str,
        workspace: Ref,
    ) -> JsonObject:
        if roots is not self.roots or device_id != self.device_id:
            raise reject("installed_root_source_changed", "Original root source required", 412)

        async def check(observed: JsonObject | None) -> None:
            await self._check(
                request, ctx, InstalledFileResources(roots, device_id, observed=observed)
            )

        return await checked_file_root(roots, device_id, workspace, ctx, check)

    async def _check(
        self, request: JsonObject, ctx: TrustedExecutionContext, resources: InstalledFileResources
    ) -> None:
        c = self.container
        assert (
            c.records
            and c.configuration
            and c.run_sources
            and c.tool_access
            and c.execution_permissions
        )
        ledger = ToolLedger(c.records)
        call = await ledger.attempt(ctx)
        fixed, spec, original = await ledger.action(str(call["action_id"]), ctx)
        if (
            fixed != call
            or original != ctx
            or request["context"] != ctx.wire()
            or request["parameters"] != {"action": "file.read", "parameters": call["arguments"]}
        ):
            raise reject(
                "installed_original_tool_denied", "Original complete Tool context required", 403
            )
        pin = Ref.model_validate(spec["provider_ref"])
        if spec != file_read_spec(pin):
            raise reject(
                "installed_file_spec_denied", "Original closed file ToolSpec required", 403
            )
        registry = ToolRegistry()
        access = RunToolAccessSources(
            c.records,
            c.configuration,
            c.run_sources,
            environment=c.tool_access.environment,
            implemented_flags=frozenset({"file_access"}),
        )
        registry.register(
            spec,
            expected_revision=0,
            binding=AdapterBinding(pin, frozenset({access.environment}), implemented=True),
        )
        authority_type = (
            InstalledFileApprovalAuthority
            if resources.observed is not None
            else ToolApprovalAuthority
        )
        authority = authority_type(
            ledger,
            registry,
            c.configuration,
            access,
            resources,
            policies=c.execution_permissions,
        )
        from uaw.infrastructure.installed_file_decision import InstalledFileDecision

        service_type = InstalledFileDecision if resources.observed is not None else ApprovalService
        service = service_type(
            c.records, c.configuration, authority, permissions=c.execution_permissions
        )
        approval_id = "approval-" + parameter_hash({"run": ctx.run_id, "action": call["action_id"]})
        # A child only reads/rechecks the already persisted decision. It cannot
        # create an approval, decide it or cause a Tool/budget/command dispatch.
        approval = await service.get(ctx.principal, approval_id)
        binding = await c.records.get(ctx.principal, "approval.bindings", approval_id)
        if binding.payload["context"] != ctx.wire():
            raise reject(
                "installed_original_approval_denied", "Original approval context required", 403
            )
        await service.recheck(
            Ref(kind="approval", id=approval_id, version=str(approval["revision"])),
            binding.payload["request"],
            ctx,
        )
