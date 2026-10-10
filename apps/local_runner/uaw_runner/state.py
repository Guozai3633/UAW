"""Explicit development SQLite adapter; internal local records, NOT public DTOs or D01."""

import hashlib
import hmac
import json
import secrets
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

from uaw.shared.contracts import JsonObject
from uaw.shared.errors import reject
from uaw.shared.runner_signatures import KEY_ID, VerificationKey
from uaw.shared.schema import validate_contract
from uaw.workspace.binding import aware


@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    kind: Literal["pair", "root"]
    principal_id: str
    device_id: str
    key_id: str
    public_bytes: bytes
    nonce: str
    challenge: str
    expires_at: datetime
    state: str
    revision: int
    root_handle: str = ""
    display_name: str = ""

    def document(self) -> JsonObject:
        # Internal signing fixture profile; network DTO requires A's versioned publication.
        return {
            "ticket_id": self.ticket_id,
            "kind": self.kind,
            "principal_id": self.principal_id,
            "device_id": self.device_id,
            "key_id": self.key_id,
            "public_key_hash": hashlib.sha256(self.public_bytes).hexdigest(),
            "nonce": self.nonce,
            "challenge": self.challenge,
            "expires_at": self.expires_at.isoformat(),
            "root_handle": self.root_handle,
            "display_name": self.display_name,
            "capabilities": ["read"] if self.kind == "root" else [],
        }


@dataclass(frozen=True)
class IssuedTicket:
    ticket: Ticket
    verification_code: str | None = field(repr=False)  # Returned only on first issue.


class LocalState:
    def __init__(self, path: Path) -> None:
        # Caller explicitly chooses local development storage. Do not auto-select deployment.
        self.path = path.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.transaction() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS verification_keys (
                key_id TEXT PRIMARY KEY, device_id TEXT NOT NULL, public_bytes BLOB NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('control','device')), revoked INTEGER NOT NULL,
                revision INTEGER NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY, kind TEXT NOT NULL, principal_id TEXT NOT NULL,
                device_id TEXT NOT NULL, key_id TEXT NOT NULL, public_bytes BLOB NOT NULL,
                nonce TEXT NOT NULL, challenge TEXT NOT NULL, expires_at TEXT NOT NULL,
                state TEXT NOT NULL, revision INTEGER NOT NULL, salt TEXT NOT NULL,
                code_hash TEXT NOT NULL, root_handle TEXT NOT NULL, display_name TEXT NOT NULL,
                confirmation_hash TEXT, confirmation_expires_at TEXT,
                UNIQUE(kind, device_id, nonce))""")

            db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS unique_root_handle
                ON tickets(root_handle) WHERE kind='root'""")

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            raise reject("revision_conflict", "Local persistent constraint changed", 409) from None
        except sqlite3.DatabaseError:
            db.rollback()
            raise reject(
                "dependency_unavailable", "Local persistent state unavailable", 503, "dependency"
            ) from None
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def register_key(self, key: VerificationKey) -> None:
        # Only trusted provisioning/registration adapter; no public/model method is wired.
        if not KEY_ID.fullmatch(key.key_id) or len(key.public_bytes) != 32 or key.revoked:
            raise reject("schema_invalid", "Invalid new verification key")
        validate_contract("ID", key.device_id)
        if key.role not in ("control", "device"):
            raise reject("schema_invalid", "Invalid key role")
        with self.transaction() as db:
            if db.execute(
                "SELECT 1 FROM verification_keys WHERE key_id=?", (key.key_id,)
            ).fetchone():
                raise reject("revision_conflict", "Key identity cannot be reused", 409)
            db.execute(
                "INSERT INTO verification_keys VALUES (?,?,?,?,0,0)",
                (key.key_id, key.device_id, key.public_bytes, key.role),
            )

    def lookup(self, key_id: str, *, device_id: str) -> VerificationKey:
        with self.transaction() as db:
            row = db.execute("SELECT * FROM verification_keys WHERE key_id=?", (key_id,)).fetchone()
            if row is None or row["device_id"] != device_id:
                raise reject("permission_denied", "Current key is unavailable", 403, "permission")
            return VerificationKey(
                row["key_id"],
                row["device_id"],
                row["public_bytes"],
                row["role"],
                bool(row["revoked"]),
            )

    def revoke_key(self, key_id: str, *, expected_revision: int) -> None:
        with self.transaction() as db:
            updated = db.execute(
                """UPDATE verification_keys SET revoked=1,revision=revision+1
                WHERE key_id=? AND revision=? AND revoked=0""",
                (key_id, expected_revision),
            )
            if updated.rowcount != 1:
                raise reject("revision_conflict", "Key revision changed", 409)
            db.execute(
                """UPDATE tickets SET state='revoked',revision=revision+1
                WHERE key_id=? AND state IN ('pending','approved')""",
                (key_id,),
            )

    def issue(
        self,
        *,
        request_id: str,
        kind: Literal["pair", "root"],
        principal_id: str,
        device_id: str,
        key_id: str,
        public_bytes: bytes,
        expires_at: datetime,
        now: datetime,
        root_handle: str = "",
        display_name: str = "",
    ) -> IssuedTicket:
        for value in (request_id, principal_id, device_id):
            validate_contract("ID", value)
        if not KEY_ID.fullmatch(key_id) or len(public_bytes) != 32 or kind not in ("pair", "root"):
            raise reject("schema_invalid", "Invalid ticket identity")
        if aware(expires_at) <= aware(now):
            raise reject("stale_resource", "Ticket deadline expired", 410)
        if kind == "root":
            validate_contract("ID", root_handle)
            validate_contract("NonEmptyText", display_name)
        code, salt = secrets.token_urlsafe(32), secrets.token_hex(32)
        ticket = Ticket(
            "ticket-"
            + hashlib.sha256(
                json.dumps([principal_id, device_id, request_id], separators=(",", ":")).encode(
                    "utf-8"
                )
            ).hexdigest(),
            kind,
            principal_id,
            device_id,
            key_id,
            public_bytes,
            secrets.token_urlsafe(32),
            secrets.token_urlsafe(32),
            expires_at,
            "pending",
            0,
            root_handle,
            display_name,
        )
        with self.transaction() as db:
            previous = db.execute(
                "SELECT * FROM tickets WHERE ticket_id=?", (ticket.ticket_id,)
            ).fetchone()
            if previous is not None:
                old = self.from_row(previous)
                if (
                    old.kind,
                    old.principal_id,
                    old.device_id,
                    old.key_id,
                    old.public_bytes,
                    old.expires_at,
                    old.root_handle,
                    old.display_name,
                ) != (
                    kind,
                    principal_id,
                    device_id,
                    key_id,
                    public_bytes,
                    expires_at,
                    root_handle,
                    display_name,
                ):
                    raise reject("revision_conflict", "Ticket request identity changed", 409)
                return IssuedTicket(old, None)  # Never re-emit one-time secrets or extend expiry.
            if kind == "root":
                self.require_device_key(db, ticket)
            db.execute(
                """INSERT INTO tickets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL,NULL)""",
                (
                    ticket.ticket_id,
                    kind,
                    principal_id,
                    device_id,
                    key_id,
                    public_bytes,
                    ticket.nonce,
                    ticket.challenge,
                    expires_at.isoformat(),
                    "pending",
                    0,
                    salt,
                    self.code_digest(salt, code),
                    root_handle,
                    display_name,
                ),
            )
        return IssuedTicket(ticket, code)

    @staticmethod
    def code_digest(salt: str, code: str) -> str:
        return hashlib.sha256((salt + ":" + code).encode("utf-8")).hexdigest()

    @staticmethod
    def from_row(row: sqlite3.Row) -> Ticket:
        return Ticket(
            row["ticket_id"],
            row["kind"],
            row["principal_id"],
            row["device_id"],
            row["key_id"],
            row["public_bytes"],
            row["nonce"],
            row["challenge"],
            datetime.fromisoformat(row["expires_at"]),
            row["state"],
            row["revision"],
            row["root_handle"],
            row["display_name"],
        )

    def get(self, ticket_id: str, *, now: datetime) -> Ticket:
        with self.transaction() as db:
            return self.load_current(db, ticket_id, now=now)

    def load_current(self, db: sqlite3.Connection, ticket_id: str, *, now: datetime) -> Ticket:
        row = db.execute("SELECT * FROM tickets WHERE ticket_id=?", (ticket_id,)).fetchone()
        if row is None:
            raise reject("stale_resource", "Ticket not found", 404)
        ticket = self.from_row(row)
        deadline = ticket.expires_at
        if row["confirmation_expires_at"] is not None:
            deadline = min(deadline, datetime.fromisoformat(row["confirmation_expires_at"]))
        if ticket.state in ("pending", "approved") and aware(deadline) <= aware(now):
            db.execute(
                "UPDATE tickets SET state='expired',revision=revision+1 WHERE ticket_id=?",
                (ticket_id,),
            )
            row = db.execute("SELECT * FROM tickets WHERE ticket_id=?", (ticket_id,)).fetchone()
            assert row is not None
            ticket = self.from_row(row)
        return ticket

    @staticmethod
    def require_device_key(db: sqlite3.Connection, ticket: Ticket) -> None:
        row = db.execute(
            "SELECT * FROM verification_keys WHERE key_id=?", (ticket.key_id,)
        ).fetchone()
        if (
            row is None
            or row["revoked"]
            or row["role"] != "device"
            or row["device_id"] != ticket.device_id
            or row["public_bytes"] != ticket.public_bytes
        ):
            raise reject("permission_denied", "Device key is unavailable", 403, "permission")

    def approve(
        self,
        ticket_id: str,
        *,
        expected_revision: int,
        code: str,
        confirmation_hash: str,
        confirmation_expires_at: datetime,
        now: datetime,
        check: Callable[[], datetime] | None = None,
    ) -> Ticket:
        # Private storage primitive: caller must have just verified both IPC and crypto proof.
        if check is not None:
            now = aware(check())
        self.get(ticket_id, now=now)  # Commit expiry tombstone independently of a later rejection.
        with self.transaction() as db:
            if check is not None:
                now = aware(check())
            ticket = self.load_current(db, ticket_id, now=now)
            row = db.execute(
                "SELECT salt,code_hash FROM tickets WHERE ticket_id=?", (ticket_id,)
            ).fetchone()
            assert row is not None
            if ticket.state != "pending" or ticket.revision != expected_revision:
                raise reject("revision_conflict", "Ticket is no longer pending", 409)
            if not hmac.compare_digest(self.code_digest(row["salt"], code), row["code_hash"]):
                raise reject("permission_denied", "One-time code rejected", 403, "permission")
            if not aware(now) < aware(confirmation_expires_at) <= ticket.expires_at:
                raise reject(
                    "permission_denied", "Confirmation deadline invalid", 403, "permission"
                )
            if ticket.kind == "root":
                self.require_device_key(db, ticket)
            else:
                # A previously revoked/registered key identity cannot pair again under the same ID.
                if db.execute(
                    "SELECT 1 FROM verification_keys WHERE key_id=?", (ticket.key_id,)
                ).fetchone():
                    raise reject("revision_conflict", "Pairing key identity already exists", 409)
            db.execute(
                """UPDATE tickets SET state='approved',revision=revision+1,
                confirmation_hash=?,confirmation_expires_at=?
                WHERE ticket_id=? AND revision=? AND state='pending'""",
                (
                    confirmation_hash,
                    confirmation_expires_at.isoformat(),
                    ticket_id,
                    expected_revision,
                ),
            )
            if check is not None:
                if aware(check()) >= min(ticket.expires_at, confirmation_expires_at):
                    raise reject(
                        "native_timeout", "Confirmation expired during CAS", 410, "timeout"
                    )
            return self.load_current(db, ticket_id, now=now)

    def consume(self, ticket_id: str, *, expected_revision: int, now: datetime) -> Ticket:
        self.get(ticket_id, now=now)
        with self.transaction() as db:
            ticket = self.load_current(db, ticket_id, now=now)
            if ticket.state != "approved" or ticket.revision != expected_revision:
                raise reject("revision_conflict", "Ticket cannot be consumed", 409)
            if ticket.kind == "root":
                self.require_device_key(db, ticket)
            else:
                if db.execute(
                    "SELECT 1 FROM verification_keys WHERE key_id=?", (ticket.key_id,)
                ).fetchone():
                    raise reject("revision_conflict", "Pair key identity changed", 409)
            # Pair consumption deliberately does NOT register a device or issue credentials.
            db.execute(
                "UPDATE tickets SET state='consumed',revision=revision+1 WHERE ticket_id=?",
                (ticket_id,),
            )
            return self.load_current(db, ticket_id, now=now)

    def revoke(self, ticket_id: str, *, expected_revision: int, now: datetime) -> Ticket:
        self.get(ticket_id, now=now)
        with self.transaction() as db:
            ticket = self.load_current(db, ticket_id, now=now)
            if ticket.state not in ("pending", "approved") or ticket.revision != expected_revision:
                raise reject("revision_conflict", "Ticket is terminal or revision changed", 409)
            db.execute(
                "UPDATE tickets SET state='revoked',revision=revision+1 WHERE ticket_id=?",
                (ticket_id,),
            )
            return self.load_current(db, ticket_id, now=now)

    def consumed_root(self, ticket_id: str, *, now: datetime) -> tuple[Ticket, str, datetime]:
        """Read persisted approval deadline/proof for an already consumed root selection.

        This never approves/consumes a pending ticket or extends an old grant's lifetime.
        """
        with self.transaction() as db:
            ticket = self.load_current(db, ticket_id, now=now)
            row = db.execute(
                "SELECT confirmation_hash,confirmation_expires_at FROM tickets WHERE ticket_id=?",
                (ticket_id,),
            ).fetchone()
            if (
                ticket.kind != "root"
                or ticket.state != "consumed"
                or ticket.revision != 2
                or row is None
                or not row["confirmation_hash"]
                or not row["confirmation_expires_at"]
            ):
                raise reject(
                    "permission_denied", "Consumed native root proof unavailable", 403, "permission"
                )
            deadline = aware(datetime.fromisoformat(row["confirmation_expires_at"]))
            if not aware(now) < deadline <= ticket.expires_at:
                raise reject(
                    "deadline_exceeded", "Consumed root confirmation expired", 410, "timeout"
                )
            self.require_device_key(db, ticket)
            return ticket, row["confirmation_hash"], deadline
