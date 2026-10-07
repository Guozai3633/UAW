"""Protocol admission only. No IPC, file IO executor, signer or process launcher."""

import hashlib
import json
from datetime import datetime

from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import parse_json
from uaw.workspace.binding import RootBindings, aware
from uaw.workspace.contracts import RunnerCommand, RunnerReceipt
from uaw.workspace.ports import Admission, AdmissionRepository, AuthorityPort, SignaturePort


def timestamp(value: str) -> datetime:
    return aware(datetime.fromisoformat(value.replace("Z", "+00:00")))


def context_identity(context: TrustedExecutionContext) -> dict[str, object]:
    wire = context.wire()
    for field in ("attempt_id", "trace_id", "deadline"):
        wire.pop(field)
    return wire


def fingerprint(command: RunnerCommand, *, root_handle: str, binding_revision: int) -> str:
    # Retry metadata may vary, but logical identity/versions/permissions/fence cannot.
    wire = command.wire()
    wire.pop("signature")
    wire.pop("expires_at")
    wire["trusted_context"] = context_identity(command.trusted_context)
    wire = {"command": wire, "root_handle": root_handle, "binding_revision": binding_revision}
    encoded = json.dumps(wire, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class RunnerProtocol:
    def __init__(
        self,
        *,
        device_id: str,
        bindings: RootBindings,
        admissions: AdmissionRepository,
        signatures: SignaturePort | None = None,
        authority: AuthorityPort | None = None,
    ) -> None:
        self.device_id = device_id
        self.bindings = bindings
        self.admissions = admissions
        self.signatures = signatures
        self.authority = authority

    def admit(self, data: str | bytes, *, now: datetime) -> Admission:
        parse_json(data)  # Reject duplicate keys/non-finite values before Pydantic JSON parsing.
        command = RunnerCommand.model_validate_json(data)
        aware(now)
        if self.signatures is None:
            raise CapabilityUnavailable("runner.signature")
        if not self.signatures.verify_command(command, device_id=self.device_id):
            raise reject("permission_denied", "Command signature rejected", 403, "permission")
        ctx = command.trusted_context
        if command.operation_id != ctx.operation_id:
            raise reject("permission_denied", "Command operation mismatch", 403, "permission")
        if min(timestamp(command.expires_at), timestamp(ctx.deadline)) <= now:
            raise reject("deadline_exceeded", "Command deadline exceeded", 410, "timeout")
        if self.authority is None:
            raise CapabilityUnavailable("runner.current_authority")
        current = self.authority.current(command)
        if current.device_id != self.device_id or context_identity(
            current.context
        ) != context_identity(ctx):
            raise reject("binding_mismatch", "Device or principal mismatch", 403, "permission")
        if timestamp(ctx.deadline) > timestamp(current.context.deadline):
            raise reject("deadline_exceeded", "Command extends authorized deadline", 410, "timeout")
        if not current.connected:
            raise CapabilityUnavailable("runner.connected_device")
        if current.cancelled:
            raise reject("cancelled", "Run was cancelled", 409, "cancelled")
        if not current.feature_enabled:
            raise reject("feature_disabled", "Runner feature is disabled", 403, "permission")
        if command.fencing_token != current.fencing_token:
            raise reject("revision_conflict", "Execution fence changed", 409)
        if aware(current.lease_expires_at) <= now:
            raise reject("deadline_exceeded", "Execution lease expired", 410, "timeout")
        if (
            command.request_ref.wire() != current.request_ref.wire()
            or command.parameters != current.request_parameters
            or ctx.capability_policy_ref.wire() != current.policy_ref.wire()
        ):
            raise reject("revision_conflict", "Request or policy version changed", 409)
        action = command.parameters["action"]
        if action not in ("file.read", "file.list"):
            raise CapabilityUnavailable("runner.execution_D03")
        if (
            action not in current.allowed_actions
            or not current.required_scope_capability
            or current.required_scope_capability not in ctx.scope.capabilities
            or current.workspace_ref not in ctx.scope.resource_refs
        ):
            raise reject("permission_denied", "Command exceeds authorized scope", 403, "permission")
        parameters = command.parameters["parameters"]
        assert isinstance(parameters, dict)  # Authoritative RunnerParameters schema checked above.
        if action == "file.read":
            matches = parameters["workspace_ref"] == current.workspace_ref.wire()
        else:
            matches = parameters["workspace_id"] == current.workspace_ref.id
        if not matches:
            raise reject("binding_mismatch", "Workspace version mismatch", 403, "permission")
        path = parameters["path"]
        assert isinstance(path, str)
        self.bindings.check_scope(
            root_handle=current.root_handle,
            principal_id=ctx.principal.id,
            device_id=self.device_id,
            workspace_ref=current.workspace_ref,
            expected_revision=current.binding_revision,
            relative_path=path,
        )
        return self.admissions.reserve(
            ctx.principal.id,
            self.device_id,
            Admission(
                command.command_id,
                ctx.attempt_id,
                fingerprint(
                    command,
                    root_handle=current.root_handle,
                    binding_revision=current.binding_revision,
                ),
            ),
        )

    def verify_receipt(self, data: str | bytes, *, command: RunnerCommand) -> RunnerReceipt:
        command = RunnerCommand.model_validate_json(json.dumps(command.wire()))
        try:
            parse_json(data)
            receipt = RunnerReceipt.model_validate_json(data)
        except ValueError:
            # The shared schema now rejects mixed branches before the domain checks below.
            raise reject("schema_invalid", "Receipt schema or branches are invalid") from None
        if self.signatures is None:
            raise CapabilityUnavailable("runner.signature")
        if not self.signatures.verify_receipt(receipt.wire(), device_id=self.device_id):
            raise reject("permission_denied", "Receipt signature rejected", 403, "permission")
        if (
            receipt.command_id != command.command_id
            or receipt.attempt_id != command.trusted_context.attempt_id
            or receipt.usage["attempt_id"] != receipt.attempt_id
        ):
            raise reject("revision_conflict", "Receipt command/attempt mismatch", 409)
        supplied = {
            field for field in ("payload", "wait_ref", "failure") if field in receipt.wire()
        }
        expected = {
            "ok": {"payload"},
            "waiting": {"wait_ref"},
            "failed": {"failure"},
            "cancelled": {"failure"},
        }[receipt.kind]
        if supplied != expected:
            raise reject("schema_invalid", "Receipt contains incompatible result branches")
        if (
            receipt.payload is not None
            and receipt.payload["action"] != command.parameters["action"]
        ):
            raise reject("revision_conflict", "Receipt action mismatch", 409)
        if receipt.kind == "cancelled" and (
            receipt.failure is None or receipt.failure.category != "cancelled"
        ):
            raise reject("schema_invalid", "Cancelled receipt requires cancellation failure")
        if receipt.payload is not None and command.parameters["action"] == "file.read":
            result = receipt.payload["result"]
            parameters = command.parameters["parameters"]
            assert isinstance(result, dict) and isinstance(parameters, dict)
            if (
                result["workspace_ref"] != parameters["workspace_ref"]
                or result["path"] != parameters["path"]
            ):
                raise reject("revision_conflict", "Receipt resource/version mismatch", 409)
        return receipt

    def dispatch(self, data: str | bytes, *, now: datetime) -> RunnerReceipt:
        self.admit(data, now=now)
        # An admission is not an execution receipt. Never fabricate success/usage/signature.
        raise CapabilityUnavailable("runner.executor")
