"""A-owned first candidate registration from an already owned, stopped helper."""

import asyncio
import base64
import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from uaw_runner.helper_process import HelperProcess
from uaw_runner.ipc.windows_pipe import OsIdentity, WindowsApi

from uaw.infrastructure.enrollment_peers import observe_windows_process
from uaw.run.enrollment import Payload, RunnerEnrollments, frozen
from uaw.shared.contracts import Principal
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.workspace.ports import CurrentKeyDirectory

CANDIDATES = "runner.enrollment.launcher.candidates"


class OwnedEnrollmentCandidates:
    """Only trusted local composition calls capture; no HTTP/body registration port.

    D prepare yields a process whose independently observed OS instance is retained.
    Preparation starts no paired runtime, opens no native window and grants no root.
    A captures the authenticated Web owner and both current role keys. Every read
    checks those originals, both live processes and the current browser owner again.
    This adapter does not invent a paired peer to start the device bootstrap.
    """

    def __init__(self, service: RunnerEnrollments, directory: CurrentKeyDirectory) -> None:
        self.service, self.directory = service, directory
        self.lock = asyncio.Lock()

    @staticmethod
    def identity(value: OsIdentity) -> Payload:
        return {
            "pid": value.pid,
            "created": str(value.created),
            "user_sid": value.user_sid,
            "logon_sid": value.logon_sid,
        }

    async def peer(
        self, identity: OsIdentity, actor: Principal, *, device_id: str, key_id: str, role: str
    ) -> Payload:
        if actor.kind != "runner":
            raise reject("enrollment_launcher_actor_denied", "Explicit Runner role required", 403)
        key = await asyncio.to_thread(self.directory.lookup, key_id, device_id=device_id)
        if key.revoked or key.role != role or key.key_id != key_id or key.device_id != device_id:
            raise reject("enrollment_launcher_key_denied", "Current role key differs", 403)
        value = {
            "identity": self.identity(identity),
            "actor": actor.wire(),
            "role": role,
            "key_id": key_id,
            "key_ref": {
                "kind": "content",
                "id": key_id,
                "version": "1",
                "content_hash": hashlib.sha256(key.public_bytes).hexdigest(),
            },
            "public_key": base64.b64encode(key.public_bytes).decode("ascii"),
        }
        self.service.peer(value, role)
        return value

    async def capture(
        self,
        owner: Principal,
        helper: HelperProcess,
        *,
        device_id: str,
        control_actor: Principal,
        device_actor: Principal,
        control_key_id: str,
        device_key_id: str,
    ) -> Payload:
        """Deployment-only fixed bindings; PIDs/public keys are never input claims."""
        validate_contract("ID", device_id)
        async with self.lock, asyncio.timeout(10):
            actor = await self.service.actor(owner)
            if helper.closed or helper.started or helper.process.poll() is not None:
                raise reject(
                    "enrollment_launcher_not_prepared", "Live prepared helper required", 403
                )
            control = await asyncio.to_thread(WindowsApi().current)
            device = await observe_windows_process(helper.process.pid)
            if (
                device != helper.identity
                or control.pid == device.pid
                or control.user_sid != device.user_sid
                or control.logon_sid != device.logon_sid
            ):
                raise reject(
                    "enrollment_launcher_instance_denied", "Owned OS instances differ", 403
                )
            expires = min(
                self.service.instant(actor["expires_at"]),
                datetime.now(UTC) + timedelta(minutes=5),
            )
            value: Payload = {
                "id": "launcher-candidate-" + uuid4().hex,
                "owner": owner.wire(),
                "device_id": device_id,
                "control": await self.peer(
                    control,
                    control_actor,
                    device_id=device_id,
                    key_id=control_key_id,
                    role="control",
                ),
                "device": await self.peer(
                    device, device_actor, device_id=device_id, key_id=device_key_id, role="device"
                ),
                "expires_at": expires.isoformat(),
            }
            validate_contract("RunnerEnrollmentCandidate", value)
            if (
                await self.service.actor(owner) != actor
                or await observe_windows_process(control.pid) != control
                or await observe_windows_process(device.pid) != device
            ):
                raise reject("enrollment_launcher_source_changed", "Original launch changed", 412)
            await self.service.records.put(
                self.service.controller,
                CANDIDATES,
                value["id"],
                "RunnerEnrollmentCandidate",
                value,
                expected_revision=0,
                request_id="capture-" + value["id"],
            )
            # Read the actual owning row and fresh keys after the write as well.
            return await self.current(value["id"], owner=owner)

    async def current(self, candidate_id: str, *, owner: Principal) -> Payload:
        validate_contract("ID", candidate_id)
        await self.service.actor(owner)
        row = await self.service.records.get(self.service.controller, CANDIDATES, candidate_id)
        value = frozen(row.payload)
        validate_contract("RunnerEnrollmentCandidate", value)
        if (
            row.schema_name != "RunnerEnrollmentCandidate"
            or row.revision != 1
            or value["id"] != candidate_id
            or value["owner"] != owner.wire()
            or self.service.instant(value["expires_at"]) <= self.service.now()
        ):
            raise reject(
                "enrollment_launcher_binding_denied", "Original launch owner or pin differs", 403
            )
        for role in ("control", "device"):
            original = value[role]
            actual = await observe_windows_process(original["identity"]["pid"])
            current = await self.peer(
                actual,
                Principal.model_validate(original["actor"]),
                device_id=value["device_id"],
                key_id=original["key_id"],
                role=role,
            )
            if current != original:
                raise reject("enrollment_launcher_source_changed", "Original OS/key changed", 412)
        await self.service.actor(owner)
        final = await self.service.records.get(self.service.controller, CANDIDATES, candidate_id)
        if (
            final.revision != row.revision
            or final.payload != value
            or final.schema_name != row.schema_name
        ):
            raise reject("enrollment_launcher_source_changed", "Original launch row changed", 412)
        return value
