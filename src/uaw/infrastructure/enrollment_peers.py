"""Live registered peer/mapping adapters; no registration from IPC frame claims."""

import asyncio
import base64
from collections.abc import Awaitable, Callable
from typing import Literal

from uaw_runner.ipc.sessions import RegisteredPeer
from uaw_runner.ipc.windows_pipe import OsIdentity, WindowsApi

from uaw.run.enrollment import RunnerEnrollments
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.runner_signatures import VerificationKey
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

    async def current(self, identity: OsIdentity, *, role: str) -> RegisteredPeer:
        if role not in ("control", "device"):
            raise reject("enrolled_role_denied", "Exact registered peer role required", 403)
        role_name: Literal["control", "device"] = "control" if role == "control" else "device"
        if self.directory is None:
            raise CapabilityUnavailable("enrollment.current_role_key_directory")
        value = await self.enrollments.get(self.user, self.enrollment_id)
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
        final = await self.enrollments.get(self.user, self.enrollment_id)
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
        value = await self.enrollments.get(self.user, self.enrollment_id)
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
        return (await self.current(identity, role=role)).owner
