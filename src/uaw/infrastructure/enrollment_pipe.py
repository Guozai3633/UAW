"""Purpose-bound first proof transport; it cannot execute commands or grant roots."""

import asyncio
import base64
import json
import secrets
from typing import Any

from uaw_runner.ipc.windows_pipe import (
    OsIdentity,
    WindowsApi,
    WindowsPipeListener,
    connect_pipe,
)

from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.enrollment_candidates import OwnedEnrollmentCandidates
from uaw.infrastructure.enrollment_control import WindowsEnrollmentControlProof
from uaw.run.enrollment import RunnerEnrollments
from uaw.shared.contracts import Principal
from uaw.shared.errors import reject
from uaw.shared.runner_signatures import VerificationKey, verify
from uaw.workspace.ports import CurrentKeyDirectory


def identity(value: dict[str, Any]) -> OsIdentity:
    return OsIdentity(value["pid"], int(value["created"]), value["user_sid"], value["logon_sid"])


def decode(data: bytes) -> dict[str, Any]:
    if not 0 < len(data) <= 4096:
        raise reject("enrollment_pipe_invalid", "Bounded first proof message required", 403)

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("Duplicate field")
            value[key] = item
        return value

    try:
        value = json.loads(data, object_pairs_hook=unique)
        if not isinstance(value, dict):
            raise ValueError("Object required")
    except ValueError, UnicodeError:
        raise reject("enrollment_pipe_invalid", "Invalid first proof message", 403) from None
    return value


class EnrollmentProofServer:
    """One owned listener, original service challenge and actual device OS instance.

    Only trusted control assembly creates this listener. Its name is a locator,
    not authority. A signature contains no private key or file material. A new
    process or changed account/key/challenge must obtain a new original enrollment.
    """

    def __init__(
        self, provider: WindowsEnrollmentControlProof, *, owner: Principal, enrollment_id: str
    ) -> None:
        self.provider, self.owner, self.key = provider, owner, enrollment_id
        self.listener: WindowsPipeListener | None = None
        self.used = False
        self.allocated = False

    async def prepare(self) -> str:
        async with asyncio.timeout(10):
            return await self._prepare()

    async def _prepare(self) -> str:
        if self.allocated or self.used:
            raise reject("enrollment_pipe_used", "First proof listener already allocated", 409)
        self.allocated = True
        document, _ = await self.provider.checked(self.owner, self.key)
        # Constructor enforces the current exact logon SID and a single OS pipe instance.
        opening = asyncio.create_task(
            asyncio.to_thread(
                WindowsPipeListener,
                name="uaw-enroll-" + secrets.token_hex(16),
                logon_sid=document["control"]["identity"]["logon_sid"],
            )
        )
        try:
            self.listener = await asyncio.shield(opening)
        except BaseException:
            # Drain an owned OS handle that may arrive after cancellation.
            while not opening.done():
                try:
                    await asyncio.shield(opening)
                except asyncio.CancelledError:
                    continue
            if not opening.cancelled() and opening.exception() is None:
                self.listener = opening.result()
                await self.close()
            raise
        try:
            if (await self.provider.checked(self.owner, self.key))[0] != document:
                raise reject("enrollment_pipe_changed", "Original first proof source changed", 412)
            return self.listener.name
        except BaseException:
            await self.close()
            raise

    async def serve_once(self) -> None:
        if self.listener is None or self.used:
            raise reject("enrollment_pipe_used", "Original prepared listener required", 409)
        self.used = True
        try:
            async with asyncio.timeout(10):
                document, _ = await self.provider.checked(self.owner, self.key)
                connection = await self.listener.accept()
                expected = identity(document["device"]["identity"])
                # Server token impersonation requires a received client message.
                # Read bounded data first, then authenticate before interpreting it.
                request_data = await connection.receive()
                if await connection.identify() != expected:
                    raise reject(
                        "enrollment_pipe_peer_denied", "Original device instance required", 403
                    )
                request = decode(request_data)
                if request != {"protocol": "uaw-enrollment-proof-v1", "enrollment_id": self.key}:
                    raise reject(
                        "enrollment_pipe_invalid", "Original first proof request required", 403
                    )
                proof = await self.provider.issue(self.owner, self.key)
                if (await self.provider.checked(self.owner, self.key))[
                    0
                ] != document or await connection.identify() != expected:
                    raise reject("enrollment_pipe_changed", "Current source or device changed", 412)
                response = {
                    "protocol": "uaw-enrollment-proof-v1",
                    "enrollment_id": self.key,
                    "document_hash": parameter_hash(document),
                    "control_proof": proof,
                }
                await connection.send(json.dumps(response, separators=(",", ":")).encode())
        finally:
            await self.close()

    async def close(self) -> None:
        if self.listener is not None:
            await self.listener.close()


class EnrollmentProofClient:
    """FirstEnrollmentDeviceFactory port; same owner/document and real control peer."""

    def __init__(
        self,
        service: RunnerEnrollments,
        directory: CurrentKeyDirectory,
        *,
        owner: Principal,
        enrollment_id: str,
        pipe_name: str,
    ) -> None:
        self.service, self.directory = service, directory
        self.owner, self.key, self.name = owner, enrollment_id, pipe_name

    async def current(self, enrollment_id: str, *, owner: Principal) -> str:
        if enrollment_id != self.key or owner != self.owner:
            raise reject("enrollment_pipe_owner_denied", "Original first proof owner required", 403)
        async with asyncio.timeout(10):
            document = await self.service.challenge(owner, self.key)
            actual = await asyncio.to_thread(WindowsApi().current)
            if document["device"]["identity"] != OwnedEnrollmentCandidates.identity(actual):
                raise reject(
                    "enrollment_pipe_device_denied", "Original actual device required", 403
                )
            connection = await connect_pipe(name=self.name, logon_sid=actual.logon_sid)
            try:
                expected = identity(document["control"]["identity"])
                if await connection.identify() != expected:
                    raise reject(
                        "enrollment_pipe_peer_denied", "Original control instance required", 403
                    )
                await connection.send(
                    json.dumps(
                        {"protocol": "uaw-enrollment-proof-v1", "enrollment_id": self.key}
                    ).encode()
                )
                response = decode(await connection.receive())
                if (
                    set(response) != {"protocol", "enrollment_id", "document_hash", "control_proof"}
                    or response["protocol"] != "uaw-enrollment-proof-v1"
                    or response["enrollment_id"] != self.key
                    or response["document_hash"] != parameter_hash(document)
                    or not isinstance(response["control_proof"], str)
                    or len(response["control_proof"]) > 240
                ):
                    raise reject(
                        "enrollment_pipe_invalid", "Original first proof response required", 403
                    )
                peer = document["control"]
                key = await asyncio.to_thread(
                    self.directory.lookup, peer["key_id"], device_id=document["device_id"]
                )
                expected_key = VerificationKey(
                    peer["key_id"],
                    document["device_id"],
                    base64.b64decode(peer["public_key"], validate=True),
                    "control",
                )
                if key != expected_key or not verify(
                    document, response["control_proof"], key, "command"
                ):
                    raise reject(
                        "enrollment_control_proof_denied", "Current first proof invalid", 403
                    )
                if (
                    await self.service.challenge(owner, self.key) != document
                    or await connection.identify() != expected
                    or await asyncio.to_thread(
                        self.directory.lookup, peer["key_id"], device_id=document["device_id"]
                    )
                    != key
                ):
                    raise reject(
                        "enrollment_pipe_changed", "Current first proof source changed", 412
                    )
                return response["control_proof"]
            finally:
                await connection.close()
