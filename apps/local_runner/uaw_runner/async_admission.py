"""Asynchronous protocol admission, with fresh authority and cooperative cancellation.

No transport, pairing V2, execution or cross-service atomic authorization is claimed.
"""

import asyncio
import json
from collections.abc import Callable
from datetime import datetime
from threading import Event

from uaw.shared.contracts import Principal
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.ports import AsyncRunnerAuthorityPort
from uaw.shared.schema import parse_json
from uaw.workspace.binding import RootBindings, aware
from uaw.workspace.contracts import RunnerAuthoritySnapshot, RunnerCommand
from uaw.workspace.ports import (
    Admission,
    AdmissionRepository,
    CheckedAdmissionRepository,
    RunnerPrincipalMappingPort,
    SignaturePort,
)
from uaw_runner.protocol import fingerprint, timestamp


class AsyncAdmission:
    def __init__(
        self,
        *,
        device_id: str,
        bindings: RootBindings,
        admissions: AdmissionRepository,
        signatures: SignaturePort | None,
        authority: AsyncRunnerAuthorityPort | None,
        mapping: RunnerPrincipalMappingPort | None,
        clock: Callable[[], datetime],
    ) -> None:
        self.device_id, self.bindings, self.admissions = device_id, bindings, admissions
        self.signatures, self.authority, self.mapping, self.clock = (
            signatures,
            authority,
            mapping,
            clock,
        )

    def deadline(
        self, command: RunnerCommand, current: RunnerAuthoritySnapshot | None = None
    ) -> None:
        now = aware(self.clock())
        deadlines = [timestamp(command.expires_at), timestamp(command.trusted_context.deadline)]
        if current is not None:
            deadlines.extend(
                [timestamp(current.context.deadline), timestamp(current.lease_expires_at)]
            )
        if min(deadlines) <= now:
            raise reject("deadline_exceeded", "Runner admission deadline exceeded", 410, "timeout")

    async def owner(self, command: RunnerCommand, actor: Principal) -> Principal:
        if self.mapping is None:
            raise CapabilityUnavailable("runner.device_owner_mapping")
        result = await self.mapping.owner(authenticated_principal=actor, device_id=self.device_id)
        self.deadline(command)
        owner = Principal.model_validate(result.wire())
        if owner.kind != "user":
            raise reject(
                "permission_denied", "Device owner must be a registered user", 403, "permission"
            )
        if actor.kind == "user":
            if actor.wire() != owner.wire():
                raise reject(
                    "permission_denied", "Channel user does not own device", 403, "permission"
                )
        elif actor.kind != "runner":
            raise reject(
                "permission_denied", "Channel principal kind is not allowed", 403, "permission"
            )
        if owner.wire() != command.trusted_context.principal.wire():
            raise reject(
                "binding_mismatch", "Registered owner differs from command claim", 403, "permission"
            )
        return owner

    async def current(
        self,
        command: RunnerCommand,
        actor: Principal,
        owner: Principal,
    ) -> RunnerAuthoritySnapshot:
        if self.authority is None:
            raise CapabilityUnavailable("runner.current_authority_async")
        # Supply a fresh wire copy so an adapter cannot mutate the retained signed command.
        result = await self.authority.current(command.wire(), authenticated_principal=actor)
        self.deadline(command)
        snapshot = RunnerAuthoritySnapshot.model_validate_json(json.dumps(result))
        self.check(command, snapshot, owner)
        return snapshot

    def check(
        self, command: RunnerCommand, current: RunnerAuthoritySnapshot, owner: Principal
    ) -> None:
        self.deadline(command, current)
        ctx = command.trusted_context
        if (
            command.operation_id != ctx.operation_id
            or current.device_id != self.device_id
            or current.context.principal.wire() != owner.wire()
            or current.context.wire() != ctx.wire()
        ):
            raise reject(
                "binding_mismatch",
                "Current context/device differs from signed command",
                403,
                "permission",
            )
        if current.cancelled:
            raise reject("cancelled", "Run is cancelled", 409, "cancelled")
        if not current.connected:
            raise CapabilityUnavailable("runner.connected_device")
        if not current.feature_enabled:
            raise reject("feature_disabled", "Runner feature is disabled", 403, "permission")
        if current.fencing_token != command.fencing_token:
            raise reject("revision_conflict", "Runner fence changed", 409)
        if (
            current.request_ref.wire() != command.request_ref.wire()
            or current.request_parameters != command.parameters
            or current.policy_ref.wire() != ctx.capability_policy_ref.wire()
        ):
            raise reject("revision_conflict", "Request/parameters/policy version changed", 409)
        action = command.parameters["action"]
        if action not in ("file.read", "file.list"):
            raise CapabilityUnavailable("runner.execution_D03")
        if (
            action not in current.allowed_actions
            or current.required_scope_capability not in ctx.scope.capabilities
            or current.workspace_ref not in ctx.scope.resource_refs
            or current.workspace_ref.kind != "workspace"
        ):
            raise reject(
                "permission_denied", "Runner scope does not allow this action", 403, "permission"
            )
        parameters = command.parameters["parameters"]
        assert isinstance(parameters, dict)
        matches = (
            parameters["workspace_ref"] == current.workspace_ref.wire()
            if action == "file.read"
            else parameters["workspace_id"] == current.workspace_ref.id
        )
        if not matches:
            raise reject("binding_mismatch", "Workspace version changed", 403, "permission")

    def external(self, command: RunnerCommand, current: RunnerAuthoritySnapshot) -> None:
        if self.signatures is None:
            raise CapabilityUnavailable("runner.signature")
        if not self.signatures.verify_command(command, device_id=self.device_id):
            raise reject(
                "permission_denied", "Current command key/signature rejected", 403, "permission"
            )
        parameters = command.parameters["parameters"]
        assert isinstance(parameters, dict) and isinstance(parameters["path"], str)
        self.bindings.check_scope(
            root_handle=current.root_handle,
            principal_id=current.context.principal.id,
            device_id=self.device_id,
            workspace_ref=current.workspace_ref,
            expected_revision=current.binding_revision,
            relative_path=parameters["path"],
        )
        self.deadline(command, current)

    def commit(
        self,
        command: RunnerCommand,
        current: RunnerAuthoritySnapshot,
        cancelled: Event,
    ) -> Admission:
        def guard() -> None:
            if cancelled.is_set():
                raise reject("cancelled", "Admission coroutine cancelled", 409, "cancelled")
            self.deadline(command, current)

        guard()
        # Fresh local key/root checks after the second authority await, off the event loop.
        self.external(command, current)
        if not isinstance(self.admissions, CheckedAdmissionRepository):
            raise CapabilityUnavailable("runner.checked_admission_CAS")
        return self.admissions.reserve_checked(
            current.context.principal.id,
            self.device_id,
            Admission(
                command.command_id,
                command.trusted_context.attempt_id,
                fingerprint(
                    command,
                    root_handle=current.root_handle,
                    binding_revision=current.binding_revision,
                ),
            ),
            check=guard,
        )

    async def admit(self, data: str | bytes, *, authenticated_principal: Principal) -> Admission:
        parse_json(data)
        command = RunnerCommand.model_validate_json(data)
        actor = Principal.model_validate(authenticated_principal.wire())
        self.deadline(command)
        if self.signatures is None:
            raise CapabilityUnavailable("runner.signature")
        if self.authority is None:
            raise CapabilityUnavailable("runner.current_authority_async")
        if self.mapping is None:
            raise CapabilityUnavailable("runner.device_owner_mapping")
        cancelled = Event()
        try:
            owner = await self.owner(command, actor)
            first = await self.current(command, actor, owner)
            await asyncio.to_thread(self.external, command, first)
            self.deadline(command, first)
            # Recheck registered ownership/session after external work.
            second_owner = await self.owner(command, actor)
            self.deadline(command, first)
            if second_owner.wire() != owner.wire():
                raise reject("binding_mismatch", "Device owner changed", 403, "permission")
            final = await self.current(command, actor, second_owner)
            self.deadline(command, final)
            if final.wire() != first.wire():
                raise reject("revision_conflict", "Authority changed during admission", 409)
            result = await asyncio.to_thread(self.commit, command, final, cancelled)
            self.deadline(command, final)
            # A late failure may leave a valid earlier CAS record. It never grants execution.
            return result
        except asyncio.CancelledError:
            cancelled.set()
            raise
