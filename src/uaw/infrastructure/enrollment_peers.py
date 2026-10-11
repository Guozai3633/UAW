"""Live registered peer/mapping adapters; no registration from IPC frame claims."""

import asyncio
import base64
import json
from collections.abc import Awaitable, Callable
from typing import Literal

from uaw_runner.ipc.sessions import RegisteredPeer
from uaw_runner.ipc.windows_pipe import OsIdentity, WindowsApi

from uaw.run.enrollment import ENROLLMENTS, Payload, RunnerEnrollments
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.runner_signatures import VerificationKey
from uaw.shared.schema import validate_contract
from uaw.workspace.ports import CurrentKeyDirectory

ObserveProcess = Callable[[int], Awaitable[OsIdentity]]


async def observe_windows_process(pid: int) -> OsIdentity:
    def read() -> OsIdentity:
        api = WindowsApi()
        try:
            handle, identity = api.process(pid)
        except OSError:
            raise reject(
                "enrolled_os_instance_unavailable", "Registered OS process no longer available", 403
            ) from None
        try:
            return identity
        finally:
            api.k.CloseHandle(handle)

    return await asyncio.to_thread(read)


class EnrolledPeerRegistry:
    """One explicitly composed current enrollment, shared by handshake and mapping.

    A live NativePairingEvidencePort remains required. Active SQL alone never
    substitutes for the current owner/session/process/key/native relationship.
    """

    def __init__(
        self,
        enrollments: RunnerEnrollments,
        *,
        owner: Principal,
        enrollment_id: str,
        directory: CurrentKeyDirectory | None,
        observe: ObserveProcess = observe_windows_process,
    ) -> None:
        self.enrollments, self.user, self.enrollment_id = enrollments, owner, enrollment_id
        self.directory, self.observe = directory, observe
        # Immutable comparison bytes, not a cached grant/outcome. Every use
        # still reads current owner/candidate/OS keys/journal/enrollment/expiry.
        self.original_enrollment: bytes | None = None

    async def current(self, identity: OsIdentity, *, role: str) -> RegisteredPeer:
        # A bounded source check only: reuse the owning READ COMMITTED
        # connection, while every nested source read remains a fresh SELECT.
        async with self.enrollments.records.current_reads():
            return await self._current(identity, role=role)

    async def _current(self, identity: OsIdentity, *, role: str) -> RegisteredPeer:
        if role not in ("control", "device"):
            raise reject("enrolled_role_denied", "Exact registered peer role required", 403)
        if self.directory is None:
            raise CapabilityUnavailable("enrollment.current_role_key_directory")
        value = await self._snapshot()
        result = await self._checked_peer(value, identity, role=role)
        encoded = json.dumps(value, sort_keys=True, allow_nan=False).encode()
        if self.original_enrollment is not None and self.original_enrollment != encoded:
            raise reject("enrolled_source_changed", "Original active enrollment changed", 412)
        self.original_enrollment = encoded
        return result

    async def _snapshot(self) -> Payload:
        """Read comparison metadata; this method never returns an admitted peer.

        _checked_peer subsequently validates the full current candidate, owning
        journal and signatures before returning any identity or owner authority.
        """
        service = self.enrollments
        await service.actor(self.user)
        row = await service.records.get(service.controller, ENROLLMENTS, self.enrollment_id)
        validate_contract("RunnerEnrollmentRecord", row.payload)
        if (
            row.schema_name != "RunnerEnrollmentRecord"
            or row.payload["id"] != self.enrollment_id
            or row.payload["revision"] != row.revision
            or (
                self.original_enrollment is not None
                and json.dumps(row.payload, sort_keys=True, allow_nan=False).encode()
                != self.original_enrollment
            )
        ):
            raise reject("enrolled_source_changed", "Original enrollment metadata changed", 412)
        return row.payload

    async def _checked_peer(
        self, value: Payload, identity: OsIdentity, *, role: str
    ) -> RegisteredPeer:
        # Snapshot is comparison data only. Full current enrollment authority is
        # established below, after role observation and before returning a peer.
        if role not in ("control", "device"):
            raise reject("enrolled_role_denied", "Exact registered peer role required", 403)
        role_name: Literal["control", "device"] = "control" if role == "control" else "device"
        if self.directory is None:
            raise CapabilityUnavailable("enrollment.current_role_key_directory")
        if value["state"] != "active":
            raise reject("enrolled_pairing_pending", "Actual native pairing is not active", 403)
        doc = value["proof_document"]
        peer = doc[role]
        registered = OsIdentity(
            peer["identity"]["pid"],
            int(peer["identity"]["created"]),
            peer["identity"]["user_sid"],
            peer["identity"]["logon_sid"],
        )
        if registered != identity or await self.observe(identity.pid) != registered:
            raise reject("enrolled_os_instance_changed", "Actual OS process instance differs", 403)
        key = await asyncio.to_thread(
            self.directory.lookup, peer["key_id"], device_id=doc["device_id"]
        )
        expected = VerificationKey(
            peer["key_id"],
            doc["device_id"],
            base64.b64decode(peer["public_key"], validate=True),
            role_name,
        )
        if key != expected:
            raise reject(
                "enrolled_current_key_denied", "Current role key is revoked or differs", 403
            )
        final = await self.enrollments.recheck_owned(self.user, value)
        if final != value or await self.observe(identity.pid) != registered:
            raise reject("enrolled_source_changed", "Current enrollment/OS source changed", 412)
        if (
            await asyncio.to_thread(
                self.directory.lookup, peer["key_id"], device_id=doc["device_id"]
            )
            != key
        ):
            raise reject("enrolled_current_key_denied", "Current role key changed", 403)
        return RegisteredPeer(
            identity,
            self.user,
            Principal.model_validate(peer["actor"]),
            doc["device_id"],
            role_name,
            peer["key_id"],
            Ref.model_validate(peer["key_ref"]),
            Ref.model_validate(value["pairing_ref"]),
            self.enrollments.instant(doc["expires_at"]),
        )

    async def owner(self, *, authenticated_principal: Principal, device_id: str) -> Principal:
        async with self.enrollments.records.current_reads():
            return await self._owner(
                authenticated_principal=authenticated_principal, device_id=device_id
            )

    async def _owner(self, *, authenticated_principal: Principal, device_id: str) -> Principal:
        value = await self._snapshot()
        if value["state"] != "active" or value["proof_document"]["device_id"] != device_id:
            raise reject(
                "enrolled_device_denied", "Active independent device relationship required", 403
            )
        matches = [
            (role, peer)
            for role, peer in ((r, value["proof_document"][r]) for r in ("control", "device"))
            if peer["actor"] == authenticated_principal.wire()
        ]
        if len(matches) != 1:
            raise reject("enrolled_actor_denied", "Original complete peer actor required", 403)
        role, peer = matches[0]
        identity = OsIdentity(
            peer["identity"]["pid"],
            int(peer["identity"]["created"]),
            peer["identity"]["user_sid"],
            peer["identity"]["logon_sid"],
        )
        return (await self._checked_peer(value, identity, role=role)).owner
