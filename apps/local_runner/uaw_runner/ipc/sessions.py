"""Independent current registration + current role key proofs on an owned OS pipe."""

import asyncio
import base64
import secrets
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, Protocol

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from uaw.shared.contracts import Principal, Ref
from uaw.shared.credentials import CredentialStorePort
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.runner_signatures import sign, verify
from uaw.workspace.ports import CurrentKeyDirectory
from uaw_runner.ipc.frames import decode, encode, proof_document
from uaw_runner.ipc.windows_pipe import OsIdentity, PipeConnection
from uaw_runner.receipts import canonical, digest, fixed_ref


@dataclass(frozen=True)
class RegisteredPeer:
    """A trusted registry result, never a frame body. PID+creation binds actual OS instance."""

    identity: OsIdentity
    owner: Principal
    actor: Principal
    device_id: str
    role: Literal["control", "device"]
    key_id: str
    key_ref: Ref
    pairing_ref: Ref
    expires_at: datetime

    def wire(self) -> dict[str, Any]:
        return {
            "identity": {
                "pid": self.identity.pid,
                "created": self.identity.created,
                "user_sid": self.identity.user_sid,
                "logon_sid": self.identity.logon_sid,
            },
            "owner": self.owner.wire(),
            "actor": self.actor.wire(),
            "device_id": self.device_id,
            "role": self.role,
            "key_id": self.key_id,
            "key_ref": self.key_ref.wire(),
            "pairing_ref": self.pairing_ref.wire(),
            "expires_at": self.expires_at.isoformat(),
        }


class PeerRegistrationPort(Protocol):
    async def current(self, identity: OsIdentity, *, role: str) -> RegisteredPeer:
        """Resolve actual OS process to independently registered account/device/key/proof.

        Missing relationship or native pairing source is unavailable. Never register from
        incoming body or assume OS user SID/PID alone identifies a UAW account.
        """
        ...


@dataclass(frozen=True)
class IpcSigningBinding:
    device_id: str
    key_id: str
    role: Literal["control", "device"]
    credential_handle: str = field(repr=False)


class IpcSigner:
    def __init__(
        self,
        *,
        binding: IpcSigningBinding,
        directory: CurrentKeyDirectory,
        credentials: CredentialStorePort | None,
    ) -> None:
        self.binding, self.directory, self.credentials = binding, directory, credentials

    async def signature(self, frame: dict[str, Any]) -> str:
        if self.credentials is None:
            raise CapabilityUnavailable("runner.ipc.protected_key")
        binding = self.binding
        key = await asyncio.to_thread(
            self.directory.lookup, binding.key_id, device_id=binding.device_id
        )
        if (
            key.revoked
            or key.role != binding.role
            or key.key_id != binding.key_id
            or key.device_id != binding.device_id
        ):
            raise reject(
                "ipc_signature_denied", "Current IPC signing key rejected", 403, "permission"
            )
        document = proof_document(decode(encode(frame)), role=binding.role)
        secret = await self.credentials.resolve(binding.credential_handle)
        try:
            raw = base64.b64decode(secret.get_secret_value(), validate=True)
            private = Ed25519PrivateKey.from_private_bytes(raw)
            if private.public_key().public_bytes_raw() != key.public_bytes:
                raise ValueError("Key mismatch")
            result = sign(
                document,
                raw,
                binding.device_id,
                binding.key_id,
                "command" if binding.role == "control" else "pairing-proof",
            )
        except ValueError, TypeError:
            raise reject(
                "ipc_signature_denied", "Protected IPC key rejected", 403, "permission"
            ) from None
        if (
            await asyncio.to_thread(
                self.directory.lookup, binding.key_id, device_id=binding.device_id
            )
            != key
        ):
            raise reject("ipc_signature_denied", "IPC key changed", 403, "permission")
        return result


class AuthenticatedPipeSession:
    def __init__(
        self,
        *,
        pipe: PipeConnection,
        registration: PeerRegistrationPort | None,
        directory: CurrentKeyDirectory,
        signer: IpcSigner,
        lifetime_seconds: float = 60,
    ) -> None:
        if not 0 < lifetime_seconds <= 600:
            raise ValueError("IPC lifetime must be in (0,600]")
        self.pipe, self.registration, self.directory, self.signer = (
            pipe,
            registration,
            directory,
            signer,
        )
        self.lifetime = lifetime_seconds
        self.connection = "ipc-" + secrets.token_hex(16)
        self.nonce = secrets.token_hex(32)
        self.peer_nonce = "0" * 64
        self.peer: RegisteredPeer | None = None
        self.local: RegisteredPeer | None = None
        self.channel_ref: Ref | None = None
        self.expires_at = datetime.now(UTC)
        self.monotonic_expiry = time.monotonic()
        self.send_sequence = 0
        self.receive_sequence = 0
        self.busy = asyncio.Lock()

    async def registered(self, identity: OsIdentity, role: str) -> RegisteredPeer:
        if self.registration is None:
            raise CapabilityUnavailable("runner.ipc.peer_registration")
        result = await self.registration.current(identity, role=role)
        if not isinstance(result, RegisteredPeer):
            raise reject("dependency_protocol_invalid", "IPC registry type invalid", 503)
        if (
            result.identity != identity
            or result.role != role
            or result.owner.kind != "user"
            or result.actor.kind not in ("user", "runner")
        ):
            raise reject(
                "ipc_identity_denied", "Registered IPC identity/role invalid", 403, "permission"
            )
        Principal.model_validate_json(canonical(result.owner.wire()))
        Principal.model_validate_json(canonical(result.actor.wire()))
        if result.actor.kind == "user" and result.actor.wire() != result.owner.wire():
            raise reject(
                "ipc_identity_denied", "Registered user differs from owner", 403, "permission"
            )
        fixed_ref(result.key_ref)
        fixed_ref(result.pairing_ref)
        if (
            result.key_ref.id != result.key_id
            or result.expires_at.tzinfo is None
            or result.expires_at <= datetime.now(UTC)
        ):
            raise reject(
                "ipc_identity_denied", "IPC registration expired or key mismatch", 403, "permission"
            )
        key = await asyncio.to_thread(
            self.directory.lookup, result.key_id, device_id=result.device_id
        )
        if (
            key.revoked
            or key.role != role
            or key.key_id != result.key_id
            or key.device_id != result.device_id
        ):
            raise reject(
                "ipc_signature_denied", "Registered current key rejected", 403, "permission"
            )
        return result

    async def check(self) -> None:
        if self.peer is None or self.local is None or self.channel_ref is None:
            raise CapabilityUnavailable("runner.ipc.handshake")
        if datetime.now(UTC) >= self.expires_at or time.monotonic() >= self.monotonic_expiry:
            await self.close()
            raise reject("ipc_timeout", "Connection authorization expired", 410, "timeout")
        try:
            if not await asyncio.to_thread(self.pipe.live_sync):
                raise reject("ipc_closed", "Connection is no longer live", 410, "dependency")
            for saved in (self.peer, self.local):
                current = await self.registered(saved.identity, saved.role)
                if current.wire() != saved.wire():
                    raise reject(
                        "ipc_identity_denied", "Current IPC registration changed", 403, "permission"
                    )
            if datetime.now(UTC) >= self.expires_at or time.monotonic() >= self.monotonic_expiry:
                raise reject(
                    "ipc_timeout", "Connection expired during source await", 410, "timeout"
                )
        except BaseException:
            await self.close()
            raise

    def frame(self, kind: str, body: dict[str, Any], sequence: int) -> dict[str, Any]:
        return {
            "version": 1,
            "kind": kind,
            "connection": self.connection,
            "nonce": self.nonce,
            "peer_nonce": self.peer_nonce,
            "sequence": sequence,
            "body": body,
            "signature": "pending",
        }

    async def outgoing(self, kind: str, body: dict[str, Any], sequence: int, until: float) -> None:
        frame = self.frame(kind, body, sequence)
        frame["signature"] = await self.signer.signature(frame)
        if time.monotonic() >= until:
            raise reject("ipc_timeout", "IPC sign deadline exceeded", 410, "timeout")
        await self.pipe.send(encode(frame), deadline=until)

    async def verify_frame(self, frame: dict[str, Any], peer: RegisteredPeer) -> None:
        key = await asyncio.to_thread(self.directory.lookup, peer.key_id, device_id=peer.device_id)
        if (
            key.role != peer.role
            or key.device_id != peer.device_id
            or key.key_id != peer.key_id
            or not verify(
                proof_document(frame, role=peer.role),
                frame["signature"],
                key,
                "command" if peer.role == "control" else "pairing-proof",
            )
        ):
            raise reject("ipc_signature_denied", "IPC role signature rejected", 403, "permission")

    async def handshake(self) -> None:
        until = time.monotonic() + self.pipe.timeout
        try:
            local_identity = await asyncio.to_thread(self.pipe.api.current)
            role = self.signer.binding.role
            self.local = await self.registered(local_identity, role)
            if (
                self.local.device_id != self.signer.binding.device_id
                or self.local.key_id != self.signer.binding.key_id
            ):
                raise reject(
                    "ipc_identity_denied",
                    "Local signer differs from registration",
                    403,
                    "permission",
                )
            if self.pipe.server:
                await self.outgoing("hello", {}, 0, until)
                incoming = decode(await self.pipe.receive(deadline=until))
                identity = await self.pipe.identify()
                self.peer = await self.registered(
                    identity, "control" if role == "device" else "device"
                )
                if (
                    incoming["kind"] != "proof"
                    or incoming["connection"] != self.connection
                    or incoming["peer_nonce"] != self.nonce
                    or incoming["sequence"] != 0
                    or incoming["body"] != {}
                ):
                    raise reject(
                        "ipc_replay", "Connection challenge proof mismatch", 403, "permission"
                    )
                self.peer_nonce = incoming["nonce"]
                await self.verify_frame(incoming, self.peer)
                await self.outgoing("ready", {}, 0, until)
            else:
                incoming = decode(await self.pipe.receive(deadline=until))
                identity = await self.pipe.identify()
                self.peer = await self.registered(
                    identity, "control" if role == "device" else "device"
                )
                if (
                    incoming["kind"] != "hello"
                    or incoming["peer_nonce"] != "0" * 64
                    or incoming["sequence"] != 0
                    or incoming["body"] != {}
                ):
                    raise reject(
                        "ipc_replay", "Initial connection challenge invalid", 403, "permission"
                    )
                await self.verify_frame(incoming, self.peer)
                self.connection = incoming["connection"]
                self.peer_nonce = incoming["nonce"]
                await self.outgoing("proof", {}, 0, until)
                ready = decode(await self.pipe.receive(deadline=until))
                await self.verify_frame(ready, self.peer)
                if (
                    ready["kind"] != "ready"
                    or ready["connection"] != self.connection
                    or ready["nonce"] != self.peer_nonce
                    or ready["peer_nonce"] != self.nonce
                    or ready["sequence"] != 0
                    or ready["body"] != {}
                ):
                    raise reject("ipc_replay", "Ready challenge mismatch", 403, "permission")
            if (
                self.peer.device_id != self.local.device_id
                or self.peer.owner.wire() != self.local.owner.wire()
                or self.peer.pairing_ref.wire() != self.local.pairing_ref.wire()
            ):
                raise reject(
                    "ipc_identity_denied",
                    "Independent peer pairing/device/owner differs",
                    403,
                    "permission",
                )
            if time.monotonic() >= until:
                raise reject("ipc_timeout", "Handshake exceeded deadline", 410, "timeout")
            self.expires_at = min(
                datetime.now(UTC) + timedelta(seconds=self.lifetime),
                self.local.expires_at,
                self.peer.expires_at,
            )
            self.monotonic_expiry = (
                time.monotonic() + (self.expires_at - datetime.now(UTC)).total_seconds()
            )
            projection = {
                "connection": self.connection,
                "local": self.local.wire(),
                "peer": self.peer.wire(),
                "nonce": self.nonce,
                "peer_nonce": self.peer_nonce,
            }
            self.channel_ref = Ref(
                kind="content", id=self.connection, version="1", content_hash=digest(projection)
            )
            await self.check()
        except BaseException:
            await self.close()
            raise

    async def send(self, kind: str, body: dict[str, Any], *, deadline: float | None = None) -> None:
        if kind not in ("command", "receipt", "recover", "error"):
            raise ValueError("Unsupported application frame")
        if self.busy.locked():
            raise reject("ipc_busy", "One in-flight session operation allowed", 409)
        async with self.busy:
            try:
                await self.check()
                until = min(self.pipe.deadline(deadline), self.monotonic_expiry)
                self.send_sequence += 1
                await self.outgoing(kind, body, self.send_sequence, until)
                await self.check()
            except BaseException:
                await self.close()
                raise

    async def receive(self, *, deadline: float | None = None) -> dict[str, Any]:
        if self.busy.locked():
            raise reject("ipc_busy", "One in-flight session operation allowed", 409)
        async with self.busy:
            try:
                await self.check()
                until = min(self.pipe.deadline(deadline), self.monotonic_expiry)
                value = decode(await self.pipe.receive(deadline=until))
                assert self.peer is not None
                await self.verify_frame(value, self.peer)
                if (
                    value["kind"] not in ("command", "receipt", "recover", "error")
                    or value["connection"] != self.connection
                    or value["nonce"] != self.peer_nonce
                    or value["peer_nonce"] != self.nonce
                    or value["sequence"] != self.receive_sequence + 1
                ):
                    raise reject(
                        "ipc_replay", "Frame connection/nonce/sequence rejected", 403, "permission"
                    )
                self.receive_sequence += 1
                await self.check()
                return value
            except BaseException:
                await self.close()
                raise

    async def close(self) -> None:
        await self.pipe.close()
