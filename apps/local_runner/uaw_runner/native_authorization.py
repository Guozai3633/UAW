"""Trusted local lifecycle facade; never an HTTP/path/approval endpoint."""

import asyncio

from uaw.shared.contracts import Ref
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.workspace.contracts import RootSelection
from uaw_runner.keys import ProtectedSigner
from uaw_runner.native_confirmation import RegisteredNativeChallenges, WindowsNativeConfirmation
from uaw_runner.pairing import PairingVerifier
from uaw_runner.read_executor import DeviceSigningBinding
from uaw_runner.root_source import NativeRootSource


class NativeReadAuthorization:
    def __init__(
        self,
        *,
        native: WindowsNativeConfirmation,
        challenges: RegisteredNativeChallenges,
        verifier: PairingVerifier,
        signer: ProtectedSigner,
        device_key: DeviceSigningBinding,
        roots: NativeRootSource,
    ) -> None:
        if native.source is not challenges or verifier.native is not native:
            raise ValueError("Native confirmation and challenge source must match")
        if verifier.state is not challenges.state or verifier.roots is not roots.native_roots:
            raise ValueError("Native state/roots must match")
        if roots.selections is not verifier.state or roots.mapping is not challenges.mapping:
            raise ValueError("Consumed selection and owner mapping must match")
        self.native, self.challenges, self.verifier = native, challenges, verifier
        self.signer, self.device_key, self.roots = signer, device_key, roots

    async def select(
        self, ticket_id: str, *, expected_revision: int, code: str, proof_signature: str
    ) -> RootSelection:
        # Caller supplies only proof/code for an independently issued challenge, no owner/path.
        first = await self.challenges.current(ticket_id)
        ticket = first.ticket
        if (
            ticket.kind != "root"
            or ticket.device_id != self.device_key.device_id
            or ticket.key_id != self.device_key.key_id
        ):
            raise reject(
                "permission_denied", "Registered read selection key differs", 403, "permission"
            )
        await self.signer.check_private(
            device_id=ticket.device_id,
            key_id=ticket.key_id,
            credential_handle=self.device_key.credential_handle,
        )
        await self.verifier.approve(
            ticket_id,
            expected_revision=expected_revision,
            principal_id=first.owner.id,
            code=code,
            proof_signature=proof_signature,
        )
        current = await self.challenges.current(ticket_id)
        if (
            current.owner.wire() != first.owner.wire()
            or current.actor.wire() != first.actor.wire()
            or current.channel_ref.wire() != first.channel_ref.wire()
            or current.identity != first.identity
        ):
            raise reject(
                "permission_denied", "Native relationship changed after approval", 403, "permission"
            )
        return await self.verifier.root_selection(
            ticket_id, signer=self.signer, credential_handle=self.device_key.credential_handle
        )

    async def bind(self, selection: RootSelection, workspace_ref: Ref) -> None:
        source = self.challenges
        actor = await source.registry.authenticated_principal(
            source.channel_ref, device_id=source.device_id
        )
        await self.roots.bind(
            selection, workspace_ref, device_id=source.device_id, authenticated_principal=actor
        )
        await source.registry.read(source.channel_ref, device_id=source.device_id)

    async def revoke(self, root_handle: str, *, expected_revision: int) -> None:
        source = self.challenges
        if source.mapping is None or self.roots.grants is None:
            raise CapabilityUnavailable("runner.native_revoke_owner")
        actor = await source.registry.authenticated_principal(
            source.channel_ref, device_id=source.device_id
        )
        owner = await source.mapping.owner(
            authenticated_principal=actor, device_id=source.device_id
        )
        grant = await asyncio.to_thread(self.roots.grants.get, root_handle)
        if (
            grant.owner is None
            or grant.owner.wire() != owner.wire()
            or grant.device_id != source.device_id
        ):
            raise reject("permission_denied", "Root revocation owner differs", 403, "permission")
        await source.registry.read(source.channel_ref, device_id=source.device_id)
        await asyncio.to_thread(
            self.roots.grants.revoke, root_handle, expected_revision=expected_revision
        )
