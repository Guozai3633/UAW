"""Trusted local lifecycle facade; never an HTTP/path/approval endpoint."""

import asyncio

from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.workspace.contracts import RootSelection
from uaw_runner.keys import ProtectedSigner
from uaw_runner.native_confirmation import (
    NativeChallenge,
    RegisteredNativeChallenges,
    WindowsNativeConfirmation,
)
from uaw_runner.pairing import LocalRoots, PairingVerifier
from uaw_runner.read_executor import DeviceSigningBinding
from uaw_runner.receipts import canonical, digest
from uaw_runner.root_source import NativeRootSource
from uaw_runner.state import Ticket


class NativeDecisionJournal:
    """Local confirmation evidence, never a cached current permission or public DTO."""

    def __init__(self, roots: LocalRoots) -> None:
        self.state = roots.state
        with self.state.transaction() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS native_decisions (
                root_handle TEXT PRIMARY KEY, ticket_id TEXT UNIQUE NOT NULL,
                evidence TEXT NOT NULL)""")

    def record(self, source: NativeChallenge) -> None:
        evidence = canonical(
            {
                "ticket": source.ticket.document(),
                "owner": source.owner.wire(),
                "actor": source.actor.wire(),
                "origin_channel": source.channel_ref.wire(),
            }
        )
        with self.state.transaction() as db:
            old = db.execute(
                "SELECT evidence FROM native_decisions WHERE root_handle=?",
                (source.ticket.root_handle,),
            ).fetchone()
            if old is not None and old[0] != evidence:
                raise reject("revision_conflict", "Different native decision evidence", 409)
            if old is None:
                db.execute(
                    "INSERT INTO native_decisions VALUES (?,?,?)",
                    (source.ticket.root_handle, source.ticket.ticket_id, evidence),
                )

    def check(self, root_handle: str, ticket: Ticket, owner: Principal, actor: Principal) -> None:
        import json

        with self.state.transaction() as db:
            row = db.execute(
                "SELECT evidence FROM native_decisions WHERE root_handle=? AND ticket_id=?",
                (root_handle, ticket.ticket_id),
            ).fetchone()
            if row is None:
                raise CapabilityUnavailable("runner.native_original_decision")
            data = json.loads(row[0])
            if (
                digest(data["ticket"]) != digest(ticket.document())
                or data["owner"] != owner.wire()
                or data["actor"] != actor.wire()
            ):
                raise reject(
                    "permission_denied",
                    "Original confirmed account/session differs",
                    403,
                    "permission",
                )


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
        if native.local_roots is not verifier.roots:
            raise ValueError("Native chosen identity record must match local roots")
        if native.source is not challenges or verifier.native is not native:
            raise ValueError("Native confirmation and challenge source must match")
        if verifier.state is not challenges.state or verifier.roots is not roots.native_roots:
            raise ValueError("Native state/roots must match")
        if roots.selections is not verifier.state or roots.mapping is not challenges.mapping:
            raise ValueError("Consumed selection and owner mapping must match")
        self.native, self.challenges, self.verifier = native, challenges, verifier
        if verifier.roots is None:
            raise ValueError("Local native roots are required")
        if native.directory is not signer.directory or native.directory is not roots.directory:
            raise ValueError("Current native and receipt key sources must match")
        self.signer, self.device_key, self.roots = signer, device_key, roots
        self.decisions = NativeDecisionJournal(verifier.roots)

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
        await asyncio.to_thread(self.decisions.record, first)
        selection = await self.verifier.root_selection(
            ticket_id, signer=self.signer, credential_handle=self.device_key.credential_handle
        )

        final = await self.challenges.current(ticket_id)
        if final.owner.wire() != first.owner.wire() or final.actor.wire() != first.actor.wire():
            raise reject(
                "permission_denied", "Account changed while signing selection", 403, "permission"
            )
        return selection

    async def bind(self, selection: RootSelection, workspace_ref: Ref) -> None:
        source = self.challenges
        actor = await source.registry.authenticated_principal(
            source.channel_ref, device_id=source.device_id
        )
        if source.mapping is None:
            raise CapabilityUnavailable("runner.native_registered_owner")
        owner = await source.mapping.owner(
            authenticated_principal=actor, device_id=source.device_id
        )

        def selected_ticket() -> Ticket:
            with source.state.transaction() as db:
                row = db.execute(
                    "SELECT ticket_id FROM tickets WHERE root_handle=? AND kind='root'",
                    (selection.root_handle,),
                ).fetchone()
                if row is None:
                    raise CapabilityUnavailable("runner.native_original_decision")
            return source.state.get(row[0], now=source.clock())

        ticket = await asyncio.to_thread(selected_ticket)
        await asyncio.to_thread(self.decisions.check, selection.root_handle, ticket, owner, actor)
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
