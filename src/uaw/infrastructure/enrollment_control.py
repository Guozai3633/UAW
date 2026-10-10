"""Purpose-bound first enrollment proof; ordinary Runner commands retain their gate."""

import asyncio
import base64
import hashlib

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from uaw_runner.ipc.windows_pipe import WindowsApi

from uaw.run.enrollment import Payload, RunnerEnrollments
from uaw.shared.contracts import Principal
from uaw.shared.credentials import CredentialStorePort
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.runner_signatures import VerificationKey, sign, verify
from uaw.shared.schema import validate_contract
from uaw.workspace.ports import CurrentKeyDirectory


class WindowsEnrollmentControlProof:
    """Sign only the current service-owned challenge in its original OS process.

    The owner/id are lookup selectors, never a caller-provided document. This proof
    binds the control role and grants neither pairing nor a directory permission.
    The independent device confirmation and both current role keys are still required.
    """

    def __init__(
        self,
        service: RunnerEnrollments,
        directory: CurrentKeyDirectory,
        credentials: CredentialStorePort | None,
        *,
        control_credential_handle: str,
    ) -> None:
        self.service, self.directory, self.credentials = service, directory, credentials
        self.handle = control_credential_handle

    async def checked(
        self, owner: Principal, enrollment_id: str
    ) -> tuple[Payload, VerificationKey]:
        document = await self.service.challenge(owner, enrollment_id)
        validate_contract("RunnerEnrollmentProofDocument", document)
        actual = await asyncio.to_thread(WindowsApi().current)
        expected = document["control"]["identity"]
        if expected != {
            "pid": actual.pid,
            "created": str(actual.created),
            "user_sid": actual.user_sid,
            "logon_sid": actual.logon_sid,
        }:
            raise reject(
                "enrollment_control_instance_denied", "Original control OS instance differs", 403
            )
        keys = {}
        for role in ("control", "device"):
            peer = document[role]
            key = await asyncio.to_thread(
                self.directory.lookup, peer["key_id"], device_id=document["device_id"]
            )
            if (
                key.revoked
                or key.role != role
                or key.device_id != document["device_id"]
                or key.key_id != peer["key_id"]
                or key.public_bytes != base64.b64decode(peer["public_key"], validate=True)
                or hashlib.sha256(key.public_bytes).hexdigest() != peer["key_ref"]["content_hash"]
            ):
                raise reject(
                    "enrollment_control_key_denied", "Original current role key differs", 403
                )
            keys[role] = key
        if await self.service.challenge(owner, enrollment_id) != document:
            raise reject("enrollment_control_source_changed", "Original challenge changed", 412)
        return document, keys["control"]

    async def issue(self, owner: Principal, enrollment_id: str) -> str:
        if self.credentials is None:
            raise CapabilityUnavailable("enrollment.control_protected_credentials")
        async with asyncio.timeout(10):
            document, key = await self.checked(owner, enrollment_id)
            secret = await self.credentials.resolve(self.handle)
            try:
                raw = base64.b64decode(secret.get_secret_value(), validate=True)
                private = Ed25519PrivateKey.from_private_bytes(raw)
                if private.public_key().public_bytes_raw() != key.public_bytes:
                    raise ValueError("Different protected key")
                proof = sign(document, raw, key.device_id, key.key_id, "command")
            except ValueError, TypeError:
                raise reject(
                    "enrollment_control_private_key_denied", "Protected control key differs", 403
                ) from None
            final, current = await self.checked(owner, enrollment_id)
            if (
                final != document
                or current != key
                or not verify(document, proof, current, "command")
            ):
                raise reject(
                    "enrollment_control_source_changed", "Original role source changed", 412
                )
            return proof
