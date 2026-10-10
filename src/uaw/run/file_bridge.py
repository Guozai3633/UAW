"""Original Tool -> registered Runner command -> one signed read; no OS file access."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.db.transactions import reference
from uaw.infrastructure.runner_pipe import RunnerPipeClient
from uaw.run.runner_commands import RunnerCommands, copy, pin
from uaw.run.runner_receipts import RegisteredReceiptCommandReader
from uaw.shared.contracts import JsonObject, Principal, Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing
from uaw.tool.ledger import action_key
from uaw.tool.ports import ToolRecoveryAccessPort
from uaw.tool.providers.file_read import FileReadEvidence, file_arguments, verify_file_evidence
from uaw.workspace.ports import SignaturePort


@dataclass(frozen=True)
class FileDeviceRoute:
    """Current protected owner/workspace mapping; never accepted from HTTP or model."""

    device_ref: Ref
    workspace_ref: Ref


class FileDeviceRoutePort(Protocol):
    async def current(self, workspace: Ref, ctx: TrustedExecutionContext) -> FileDeviceRoute: ...


class RegisteredFileBridge:
    def __init__(
        self,
        *,
        commands: RunnerCommands,
        pipe: RunnerPipeClient | None,
        routes: FileDeviceRoutePort | None,
        access: ToolRecoveryAccessPort | None,
        provider_ref: Ref,
        provider: Principal,
        signatures: SignaturePort | None,
    ) -> None:
        self.commands, self.pipe, self.routes, self.access = commands, pipe, routes, access
        self.provider_ref, self.provider, self.signatures = provider_ref, provider, signatures
        self.reader = RegisteredReceiptCommandReader(commands)

    def ready(self) -> None:
        if (
            self.pipe is None
            or self.routes is None
            or self.access is None
            or self.signatures is None
            or self.commands.roots is None
            or self.commands.gate is None
            or self.commands.signer is None
            or self.commands.devices.channels is None
        ):
            raise CapabilityUnavailable("file.registered_device_root_pipe_sources")

    async def resolve(
        self, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> tuple[Ref, ...]:
        self.ready()
        args = file_arguments(call, spec, self.provider_ref)
        # The present signed Runner receipt contains full bytes only for whole.
        # A partial result cannot supply C's required original full snapshot.
        if args.get("location", {"kind": "whole"}) != {"kind": "whole"} or "cursor" in args:
            raise CapabilityUnavailable("file.native_full_snapshot_for_paging")
        if ctx.scope.project_id is not None:
            raise CapabilityUnavailable("file.current_project_admission")
        workspace = Ref.model_validate(args["workspace_ref"])
        if workspace.wire() not in [r.wire() for r in ctx.scope.resource_refs]:
            raise reject("file_workspace_denied", "Exact owned workspace required", 403)
        assert self.routes and self.access and self.commands.roots
        await self.access.check(call, spec, ctx, provider=self.provider)
        route = await self.routes.current(workspace, ctx)
        device = await self.commands.devices.current(
            route.device_ref.id, authenticated_principal=ctx.principal
        )
        if (
            route.workspace_ref != workspace
            or route.device_ref.wire()
            != {
                **reference("device", device["device_id"], device["revision"]),
                "content_hash": parameter_hash(device),
            }
            or device["source"]["owner"] != ctx.principal.wire()
        ):
            raise reject("file_device_route_changed", "Current owner/device/workspace differs", 412)
        root = copy(await self.commands.roots.current(device["device_id"], workspace, ctx))
        validate_contract("RunnerRootSnapshot", root)
        if (
            root["owner"] != ctx.principal.wire()
            or root["device_id"] != device["device_id"]
            or root["workspace_ref"] != workspace.wire()
            or "file.read" not in root["allowed_actions"]
            or not set(root["allowed_actions"]) <= {"file.read", "file.list"}
            or datetime.fromisoformat(root["expires_at"].replace("Z", "+00:00"))
            <= datetime.now(UTC)
        ):
            raise reject("file_root_denied", "Current native read root missing", 403)
        await self.access.check(call, spec, ctx, provider=self.provider)
        if await self.routes.current(workspace, ctx) != route:
            raise reject("file_device_route_changed", "Device mapping changed while checking", 412)
        # The device is a transport binding, not another resource added to the
        # user's approval scope. FileResourceReader checks this exact workspace.
        return (workspace,)

    @staticmethod
    def command_id(call: JsonObject, ctx: TrustedExecutionContext) -> str:
        return "file-command-" + parameter_hash(
            {
                "owner": ctx.principal.wire(),
                "key": action_key(ctx, str(call["action_id"])),
                "attempt_id": ctx.attempt_id,
            }
        )

    async def evidence(
        self,
        call: JsonObject,
        spec: JsonObject,
        ctx: TrustedExecutionContext,
        command_ref: Ref,
        *,
        recover: bool,
    ) -> FileReadEvidence:
        assert self.pipe and self.signatures
        await self.resolve(call, spec, ctx)
        source = await self.reader.resolve(command_ref, authenticated_principal=ctx.principal)
        assert self.routes
        args = file_arguments(call, spec, self.provider_ref)
        route = await self.routes.current(Ref.model_validate(args["workspace_ref"]), ctx)
        if (
            source.command.trusted_context != ctx
            or source.command.request_ref.wire()
            != pin("tool_call", action_key(ctx, str(call["action_id"])), call)
            or source.device_id != route.device_ref.id
        ):
            raise reject(
                "file_original_command_changed", "Original Tool/Runner binding differs", 412
            )
        receipt = await self.pipe.read(command_ref, recover=recover)
        if receipt.receipt.kind != "ok" or receipt.receipt.payload is None:
            raise reject(
                "file_original_read_unknown",
                "No confirmed original file content",
                409,
                "unknown_effect",
            )
        raw = receipt.receipt.payload["result"]
        if not isinstance(raw, dict):
            raise reject("file_native_content_invalid", "Original FileContent required", 412)
        content = copy(raw)
        validate_contract("FileContent", content)
        if content["location"] != {"kind": "whole"} or content.get("next_cursor"):
            raise CapabilityUnavailable("file.native_full_snapshot_for_paging")
        snapshot = content["text"].encode("utf-8")
        if len(content["text"]) > 16384 or len(snapshot) > 65536:
            raise reject("file_native_text_limit", "Current Runner text boundary exceeded", 413)
        value = FileReadEvidence(
            command_ref,
            receipt.receipt_ref,
            source,
            receipt.receipt,
            snapshot,
            copy(content["location"]),
        )
        verify_file_evidence(value, call, spec, ctx, self.provider_ref, self.signatures)
        await self.resolve(call, spec, ctx)
        if await self.routes.current(route.workspace_ref, ctx) != route:
            raise reject(
                "file_device_route_changed", "Original receipt device mapping changed", 412
            )
        return value

    async def execute(
        self, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> FileReadEvidence:
        resources = await self.resolve(call, spec, ctx)
        assert self.routes
        route = await self.routes.current(resources[0], ctx)
        device_ref = route.device_ref
        commands = self.commands
        identifier = self.command_id(call, ctx)
        try:
            await commands.record(identifier)
        except StoreMissing:
            pass
        else:
            raise reject(
                "file_original_send_unknown",
                "Existing original command requires recovery",
                409,
                "unknown_effect",
            )
        request_ref = await commands.register_tool_request(
            call,
            spec,
            ctx,
            RequestMeta(request_id=identifier + "-request", schema_version="0.1"),
            authenticated_service=commands.devices.controller,
        )
        try:
            state = await commands.leases.state(ctx, holder=commands.devices.controller)
        except StoreMissing:
            lease = copy(
                await commands.leases.acquire(
                    {"lease_ttl_ms": 30000, "expected_revision": 0},
                    RequestMeta(request_id=identifier + "-lease", schema_version="0.1"),
                    ctx,
                    holder=commands.devices.controller,
                )
            )
        else:
            validate_contract("ExecutionLeaseStateRecord", state)
            raw_lease = state["lease"]
            if not isinstance(raw_lease, dict):
                raise reject("file_lease_invalid", "Actual lease record required", 412)
            lease = copy(raw_lease)
            await commands.leases.current(
                Ref.model_validate(reference("lease", lease["id"], lease["revision"])),
                lease["fencing_token"],
                ctx,
                holder=commands.devices.controller,
            )
        validate_contract("ExecutionLease", lease)
        device = await commands.devices.current(
            device_ref.id, authenticated_principal=ctx.principal
        )
        root = (
            copy(await commands.roots.current(device_ref.id, resources[0], ctx))
            if commands.roots
            else {}
        )
        validate_contract("RunnerRootSnapshot", root)
        expires = min(
            datetime.fromisoformat(x.replace("Z", "+00:00"))
            for x in (
                ctx.deadline,
                lease["expires_at"],
                root["expires_at"],
                device["source"]["expires_at"],
            )
        )
        record = await commands.register(
            {
                "command_id": identifier,
                "request_ref": request_ref,
                "device_ref": device_ref.wire(),
                "lease_ref": reference("lease", lease["id"], lease["revision"]),
                "fencing_token": lease["fencing_token"],
                "expires_at": expires.isoformat(),
            },
            RequestMeta(request_id=identifier + "-register", schema_version="0.1"),
            authenticated_service=commands.devices.controller,
        )
        # Registration is not permission to send. Fresh complete authority follows.
        actor = Principal.model_validate(device["source"]["actor"])
        await commands.collect(record, actor)
        await self.resolve(call, spec, ctx)
        return await self.evidence(
            call,
            spec,
            ctx,
            Ref.model_validate(pin("content", identifier, record["command"])),
            recover=False,
        )

    async def recover(
        self, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> FileReadEvidence | None:
        await self.resolve(call, spec, ctx)
        try:
            record = await self.commands.record(self.command_id(call, ctx))
        except StoreMissing:
            return None  # No journal proof, not "not applied"; never call execute.
        return await self.evidence(
            call,
            spec,
            ctx,
            Ref.model_validate(pin("content", record["command"]["command_id"], record["command"])),
            recover=True,
        )
