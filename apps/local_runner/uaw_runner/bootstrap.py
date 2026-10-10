"""Consume A-owned current registration/challenge ports; no enrollment or wire DTO.

OS identity is an instance binding, never an account. No source means unavailable.
"""

import asyncio
import hashlib
from collections.abc import Callable
from datetime import UTC, datetime

from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.workspace.binding import aware
from uaw.workspace.ports import CurrentKeyDirectory, RunnerPrincipalMappingPort
from uaw_runner.ipc.channel_source import ConnectionRegistry
from uaw_runner.ipc.sessions import AuthenticatedPipeSession, PeerRegistrationPort, RegisteredPeer
from uaw_runner.ipc.windows_pipe import OsIdentity
from uaw_runner.keys import ProtectedSigner
from uaw_runner.native_confirmation import (
    NativeChallenge,
    NativeChallengeSourcePort,
    RegisteredNativeChallenges,
)
from uaw_runner.read_executor import DeviceSigningBinding
from uaw_runner.receipts import canonical, fixed_ref
from uaw_runner.state import LocalState


class BootstrapConsumer:
    def __init__(
        self,
        *,
        registration: PeerRegistrationPort | None,
        challenges: NativeChallengeSourcePort | None,
        mapping: RunnerPrincipalMappingPort | None,
        directory: CurrentKeyDirectory,
        signer: ProtectedSigner,
        device_key: DeviceSigningBinding,
    ) -> None:
        if signer.directory is not directory:
            raise ValueError("Bootstrap and protected signer need the same current keys")
        self.registration, self.challenges, self.mapping = registration, challenges, mapping
        self.directory, self.signer, self.device_key = directory, signer, device_key

    def available(self) -> None:
        for name, value in (
            ("registration", self.registration),
            ("challenges", self.challenges),
            ("mapping", self.mapping),
            ("credentials", self.signer.credentials),
        ):
            if value is None:
                raise CapabilityUnavailable("runner.bootstrap." + name)

    async def local(self, identity: OsIdentity) -> RegisteredPeer:
        self.available()
        assert self.registration is not None and self.mapping is not None
        peer = await self.registration.current(identity, role="device")
        if not isinstance(peer, RegisteredPeer):
            raise reject("dependency_protocol_invalid", "Bootstrap registration type invalid", 503)
        Principal.model_validate_json(canonical(peer.owner.wire()))
        Principal.model_validate_json(canonical(peer.actor.wire()))
        fixed_ref(peer.key_ref)
        fixed_ref(peer.pairing_ref)
        binding = self.device_key
        if (
            peer.identity != identity
            or peer.role != "device"
            or peer.owner.kind != "user"
            or peer.actor.kind not in {"user", "runner"}
            or (peer.actor.kind == "user" and peer.actor.wire() != peer.owner.wire())
            or peer.device_id != binding.device_id
            or peer.key_id != binding.key_id
            or peer.key_ref.id != peer.key_id
        ):
            raise reject(
                "permission_denied", "Bootstrap instance/account/key mismatch", 403, "permission"
            )
        key = await asyncio.to_thread(self.directory.lookup, peer.key_id, device_id=peer.device_id)
        if (
            key.revoked
            or key.role != "device"
            or key.key_id != peer.key_id
            or key.device_id != peer.device_id
            or peer.key_ref.content_hash != hashlib.sha256(key.public_bytes).hexdigest()
        ):
            raise reject(
                "permission_denied", "Bootstrap current device key rejected", 403, "permission"
            )
        owner = await self.mapping.owner(
            authenticated_principal=peer.actor, device_id=peer.device_id
        )
        if owner.wire() != peer.owner.wire():
            raise reject(
                "permission_denied", "Bootstrap independent owner differs", 403, "permission"
            )
        await self.signer.check_private(
            device_id=peer.device_id,
            key_id=peer.key_id,
            credential_handle=binding.credential_handle,
        )
        final = await self.registration.current(identity, role="device")
        if not isinstance(final, RegisteredPeer) or final.wire() != peer.wire():
            raise reject("permission_denied", "Bootstrap source changed", 403, "permission")
        final_owner = await self.mapping.owner(
            authenticated_principal=peer.actor, device_id=peer.device_id
        )
        if final_owner.wire() != peer.owner.wire():
            raise reject("permission_denied", "Bootstrap owner changed", 403, "permission")
        final_key = await asyncio.to_thread(
            self.directory.lookup, peer.key_id, device_id=peer.device_id
        )
        if final_key != key or aware(peer.expires_at) <= datetime.now(UTC):
            raise reject("permission_denied", "Bootstrap expired or key changed", 403, "permission")
        return peer

    async def connected(self, session: AuthenticatedPipeSession) -> None:
        self.available()
        if session.registration is not self.registration or session.directory is not self.directory:
            raise ValueError("Handshake must use the original bootstrap registration and keys")
        await session.check()
        assert session.local is not None
        current = await self.local(session.local.identity)
        if current.wire() != session.local.wire():
            raise reject("permission_denied", "Bootstrap connection changed", 403, "permission")
        await session.check()

    async def verify_challenge(
        self, local: NativeChallenge, registry: ConnectionRegistry
    ) -> NativeChallenge:
        self.available()
        assert self.challenges is not None and self.mapping is not None
        session = await registry.session(local.channel_ref, device_id=self.device_key.device_id)
        await self.connected(session)
        current = await self.challenges.current(local.ticket.ticket_id)
        if not isinstance(current, NativeChallenge):
            raise reject("dependency_protocol_invalid", "Bootstrap challenge type invalid", 503)
        # Exact original document/revision/state and complete session; no body authority.
        if (
            current.fingerprint() != local.fingerprint()
            or current.ticket.key_id != self.device_key.key_id
            or current.ticket.device_id != self.device_key.device_id
            or aware(current.expires_at) <= datetime.now(UTC)
        ):
            raise reject(
                "permission_denied", "Independent bootstrap challenge differs", 403, "permission"
            )
        await self.connected(session)
        return current


class BootstrapNativeChallenges(RegisteredNativeChallenges):
    """Intersection of original local Ticket/live OS channel and A-owned challenge."""

    def __init__(
        self,
        *,
        bootstrap: BootstrapConsumer,
        state: LocalState,
        registry: ConnectionRegistry,
        channel_ref: Ref,
        device_id: str,
        mapping: RunnerPrincipalMappingPort | None,
        clock: Callable[[], datetime],
    ) -> None:
        super().__init__(
            state=state,
            registry=registry,
            channel_ref=channel_ref,
            device_id=device_id,
            mapping=mapping,
            clock=clock,
        )
        if (
            self.mapping is not bootstrap.mapping
            or self.device_id != bootstrap.device_key.device_id
        ):
            raise ValueError("Challenge mapping/device must match bootstrap")
        self.bootstrap = bootstrap

    async def current(self, ticket_id: str) -> NativeChallenge:
        first = await super().current(ticket_id)
        await self.bootstrap.verify_challenge(first, self.registry)
        final = await super().current(ticket_id)
        if final.fingerprint() != first.fingerprint():
            raise reject(
                "permission_denied", "Challenge changed during bootstrap await", 403, "permission"
            )
        return final
