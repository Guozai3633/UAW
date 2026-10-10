"""Internal pairing/selection state verification; no public pair.complete or IPC claim."""

import asyncio
import hashlib
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from threading import Event

from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.runner_signatures import VerificationKey, signing_bytes, verify
from uaw.workspace.binding import aware
from uaw.workspace.contracts import RootSelection
from uaw.workspace.ports import CurrentKeyDirectory, NativeConfirmationPort, SelectedRoot
from uaw_runner.keys import Ed25519SignatureAdapter, ProtectedSigner
from uaw_runner.state import LocalState, Ticket


class LocalRoots:
    """Separate native-path directory; never stored in control-plane ticket/key records."""

    def __init__(self, path: Path) -> None:
        self.state = LocalState(path)
        with self.state.transaction() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS native_roots (
                ticket_id TEXT PRIMARY KEY, root_handle TEXT UNIQUE NOT NULL,
                native_path TEXT NOT NULL, file_device INTEGER NOT NULL, inode INTEGER NOT NULL)""")

    def record(self, ticket: Ticket, path: Path) -> None:
        try:
            if not path.is_absolute():
                raise ValueError("Relative path")
            root = path.resolve(strict=True)
            if root != path.absolute() or any(
                getattr(part.lstat(), "st_file_attributes", 0) & 0x400
                for part in (path, *path.parents)
            ):
                raise ValueError("Reparse/native root changed")
            if not root.is_dir() or root == Path(root.anchor):
                raise ValueError("Invalid root")
            identity = root.stat()
        except OSError, ValueError, RuntimeError:
            raise reject(
                "permission_denied", "Native root is unavailable", 403, "permission"
            ) from None
        values = (ticket.ticket_id, ticket.root_handle, str(root), identity.st_dev, identity.st_ino)
        with self.state.transaction() as db:
            previous = db.execute(
                "SELECT * FROM native_roots WHERE ticket_id=?", (ticket.ticket_id,)
            ).fetchone()
            if previous is not None:
                if tuple(previous) != values:
                    raise reject("revision_conflict", "Native root selection changed", 409)
                return
            if db.execute(
                "SELECT 1 FROM native_roots WHERE root_handle=?", (ticket.root_handle,)
            ).fetchone():
                raise reject("revision_conflict", "Native root handle already exists", 409)
            db.execute("INSERT INTO native_roots VALUES (?,?,?,?,?)", values)

    def current(self, ticket: Ticket) -> Path:
        with self.state.transaction() as db:
            row = db.execute(
                "SELECT * FROM native_roots WHERE ticket_id=?", (ticket.ticket_id,)
            ).fetchone()
            if row is None or row["root_handle"] != ticket.root_handle:
                raise reject("permission_denied", "Native selection is missing", 403, "permission")
            root = Path(row["native_path"])
            try:
                stat = root.stat()
                if root.resolve(strict=True) != root or (stat.st_dev, stat.st_ino) != (
                    row["file_device"],
                    row["inode"],
                ):
                    raise ValueError("Root changed")
            except OSError, ValueError, RuntimeError:
                raise reject(
                    "permission_denied", "Native root changed", 403, "permission"
                ) from None
            return root


class PairingVerifier:
    def __init__(
        self,
        state: LocalState,
        *,
        native: NativeConfirmationPort | None,
        clock: Callable[[], datetime],
        roots: LocalRoots | None = None,
    ) -> None:
        self.state, self.native, self.clock, self.roots = state, native, clock, roots

    async def approve(
        self,
        ticket_id: str,
        *,
        expected_revision: int,
        principal_id: str,
        code: str,
        proof_signature: str,
    ) -> Ticket:
        if self.native is None:
            raise CapabilityUnavailable("runner.trusted_native_confirmation")
        ticket = await asyncio.to_thread(self.state.get, ticket_id, now=aware(self.clock()))
        if ticket.state != "pending" or ticket.revision != expected_revision:
            raise reject("revision_conflict", "Ticket is not pending", 409)
        if ticket.principal_id != principal_id:
            raise reject("permission_denied", "Pairing principal mismatch", 403, "permission")
        # Candidate public key comes from fixed server challenge state, not completion payload.
        # Proof establishes possession only; authenticated native confirmation is mandatory.
        key = VerificationKey(ticket.key_id, ticket.device_id, ticket.public_bytes, "device")
        if ticket.kind == "root":
            current_key = await asyncio.to_thread(
                self.state.lookup, ticket.key_id, device_id=ticket.device_id
            )
            if current_key != key:
                raise reject(
                    "permission_denied", "Current root challenge key differs", 403, "permission"
                )
        document = ticket.document()
        if not verify(document, proof_signature, key, "pairing-proof"):
            raise reject(
                "permission_denied", "Challenge possession proof rejected", 403, "permission"
            )
        document_hash = hashlib.sha256(
            signing_bytes(document, ticket.device_id, ticket.key_id, "pairing-proof")
        ).hexdigest()
        confirmation = await self.native.confirm(
            ticket_id=ticket_id,
            principal_id=principal_id,
            device_id=ticket.device_id,
            document_hash=document_hash,
        )
        now = aware(self.clock())
        if (
            confirmation.ticket_id != ticket_id
            or confirmation.principal_id != principal_id
            or confirmation.device_id != ticket.device_id
            or confirmation.document_hash != document_hash
            or aware(confirmation.expires_at) <= now
            or confirmation.expires_at > ticket.expires_at
        ):
            raise reject(
                "permission_denied", "Native confirmation mismatch/expiry", 403, "permission"
            )
        latest = await asyncio.to_thread(self.state.get, ticket_id, now=now)
        if latest != ticket:
            raise reject("revision_conflict", "Native ticket changed during confirmation", 409)
        if ticket.kind == "root":
            if (
                await asyncio.to_thread(
                    self.state.lookup, ticket.key_id, device_id=ticket.device_id
                )
                != key
            ):
                raise reject("permission_denied", "Current root key changed", 403, "permission")
            if self.roots is None:
                raise CapabilityUnavailable("runner.local_root_directory")
            if confirmation.native_path is None:
                raise reject("permission_denied", "Native path was not selected", 403, "permission")
            # Orphan local record after a losing CAS grants no rights; immutable and fail closed.
            await asyncio.to_thread(self.roots.record, ticket, confirmation.native_path)
        stopped = Event()

        def check() -> datetime:
            if stopped.is_set():
                raise reject(
                    "native_cancelled", "Confirmation cancelled before CAS", 409, "cancelled"
                )
            return aware(self.clock())

        task = asyncio.create_task(
            asyncio.to_thread(
                self.state.approve,
                ticket_id,
                expected_revision=expected_revision,
                code=code,
                confirmation_hash=document_hash,
                confirmation_expires_at=confirmation.expires_at,
                now=aware(self.clock()),
                check=check,
            )
        )
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            stopped.set()
            while not task.done():
                try:
                    await asyncio.shield(task)
                except asyncio.CancelledError:
                    continue
                except Exception:
                    break
            if task.done() and not task.cancelled():
                task.exception()
            raise

    async def root_selection(
        self,
        ticket_id: str,
        *,
        signer: ProtectedSigner,
        credential_handle: str,
    ) -> RootSelection:
        ticket = await asyncio.to_thread(self.state.get, ticket_id, now=aware(self.clock()))
        if ticket.kind != "root" or ticket.state != "approved":
            raise reject("revision_conflict", "Root ticket is not approved", 409)
        if self.roots is None:
            raise CapabilityUnavailable("runner.local_root_directory")
        await asyncio.to_thread(self.roots.current, ticket)
        signature = await signer.sign_document(
            ticket.document(),
            device_id=ticket.device_id,
            key_id=ticket.key_id,
            domain="root-selection",
            credential_handle=credential_handle,
        )
        # A revoke/consume/expiry during async secure-store access must not mint a usable selection.
        current = await asyncio.to_thread(self.state.get, ticket_id, now=aware(self.clock()))
        if current != ticket:
            raise reject("revision_conflict", "Root ticket changed", 409)
        await asyncio.to_thread(self.roots.current, ticket)
        return RootSelection(
            selection_token=signature,
            display_name=ticket.display_name,
            expires_at=ticket.expires_at.isoformat(),
            root_handle=ticket.root_handle,
        )

    def complete_legacy(self) -> None:
        # Old RunnerPairCompleteRequest does not contain challenge proof or native confirmation.
        raise CapabilityUnavailable("runner.versioned_pairing_proof_DTO")


class PersistentRootSelection:
    def __init__(
        self, state: LocalState, roots: LocalRoots, *, directory: CurrentKeyDirectory | None = None
    ) -> None:
        if state.path == roots.state.path:
            raise ValueError("Control records and native roots require separate directories")
        self.state, self.roots = state, roots
        self.directory = directory if directory is not None else state
        self.signatures = Ed25519SignatureAdapter(self.directory)

    def consume(
        self,
        selection: RootSelection,
        *,
        principal_id: str,
        device_id: str,
        now: datetime,
    ) -> SelectedRoot:
        selection = RootSelection.model_validate(selection.wire())
        with self.state.transaction() as db:
            row = db.execute(
                "SELECT ticket_id FROM tickets WHERE root_handle=? AND kind='root'",
                (selection.root_handle,),
            ).fetchone()
            if row is None:
                raise reject("permission_denied", "Root token not found", 403, "permission")
            ticket_id = row["ticket_id"]
        ticket = self.state.get(ticket_id, now=now)
        if (
            ticket.kind != "root"
            or ticket.principal_id != principal_id
            or ticket.device_id != device_id
            or ticket.state != "approved"
            or selection.display_name != ticket.display_name
            or selection.expires_at != ticket.expires_at.isoformat()
        ):
            raise reject(
                "permission_denied", "Root selection identity/state mismatch", 403, "permission"
            )
        key = self.directory.lookup(ticket.key_id, device_id=device_id)
        if (
            key.revoked
            or key.role != "device"
            or key.device_id != device_id
            or key.key_id != ticket.key_id
            or key.public_bytes != ticket.public_bytes
        ):
            raise reject(
                "permission_denied", "Actual root selection key differs", 403, "permission"
            )
        if not self.signatures.verify_document(
            {**ticket.document(), "signature": selection.selection_token},
            device_id=device_id,
            domain="root-selection",
        ):
            raise reject("permission_denied", "Root token signature rejected", 403, "permission")
        root = self.roots.current(ticket)
        if self.directory.lookup(ticket.key_id, device_id=device_id) != key:
            raise reject("permission_denied", "Root selection key changed", 403, "permission")
        self.state.consume(ticket_id, expected_revision=ticket.revision, now=now)
        # Keep the actual bounded native confirmation metadata; no infinite old-grant fallback.
        _, _, confirmation_deadline = self.state.consumed_root(ticket_id, now=now)
        # Crash after consumption may lose availability; the credential cannot be replayed.
        return SelectedRoot(
            principal_id,
            device_id,
            ticket.root_handle,
            root,
            frozenset({"read"}),
            ticket.expires_at,
            selection_ticket_id=ticket.ticket_id,
            selection_key_id=ticket.key_id,
            selection_signature=selection.selection_token,
            confirmation_expires_at=confirmation_deadline,
        )
