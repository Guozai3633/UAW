"""Development SQLite once-use read journal. Unknown attempts never run again.

A durable claim precedes opening the file. A signed result precedes publication.
No private key, path or plaintext file content is stored outside the signed receipt.
"""

import sqlite3
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from uaw.shared.contracts import Ref
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.workspace.contracts import RegisteredReceiptCommand
from uaw_runner.receipts import canonical, digest, fixed_ref, receipt_id


@dataclass(frozen=True)
class ReadAttempt:
    id: str
    binding: str
    token: str
    root_handle: str
    root_revision: int
    receipt_data: str | None = None
    receipt_ref: Ref | None = None


class ReadExecutionJournal:
    def __init__(self, path: Path) -> None:
        self.path = path.absolute()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        db = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            db = sqlite3.connect(self.path, timeout=1, isolation_level=None)
            db.row_factory = sqlite3.Row
            db.execute("BEGIN IMMEDIATE")
            db.execute("""CREATE TABLE IF NOT EXISTS file_read_attempts (
                id TEXT PRIMARY KEY, binding TEXT NOT NULL, token TEXT NOT NULL,
                root_handle TEXT NOT NULL, root_revision INTEGER NOT NULL,
                receipt_data TEXT, receipt_ref TEXT)""")
            yield db
            db.commit()
        except sqlite3.DatabaseError, OSError:
            raise CapabilityUnavailable("runner.file_read_journal") from None
        finally:
            if db is not None:
                db.close()

    @staticmethod
    def key(source: RegisteredReceiptCommand, command_ref: Ref) -> tuple[str, str]:
        # Stable command ID across attempts: different attempt/body/fence cannot read twice.
        ident = digest(
            [source.owner.kind, source.owner.id, source.device_id, source.command.command_id]
        )
        binding = digest(
            [
                source.owner.wire(),
                source.device_id,
                fixed_ref(command_ref).wire(),
                source.command.wire(),
            ]
        )
        return ident, binding

    @staticmethod
    def row(row: sqlite3.Row, binding: str) -> ReadAttempt:
        if row["binding"] != binding:
            raise reject("revision_conflict", "Read command/owner/version changed", 409)
        ref = fixed_ref(Ref.model_validate_json(row["receipt_ref"])) if row["receipt_ref"] else None
        if ref is not None and not row["receipt_data"]:
            raise reject("revision_conflict", "Read journal is inconsistent", 409)
        return ReadAttempt(
            row["id"],
            binding,
            row["token"],
            row["root_handle"],
            row["root_revision"],
            row["receipt_data"],
            ref,
        )

    def get(self, source: RegisteredReceiptCommand, command_ref: Ref) -> ReadAttempt | None:
        ident, binding = self.key(source, command_ref)
        with self.transaction() as db:
            row = db.execute("SELECT * FROM file_read_attempts WHERE id=?", (ident,)).fetchone()
            return self.row(row, binding) if row is not None else None

    def claim(
        self,
        source: RegisteredReceiptCommand,
        command_ref: Ref,
        *,
        root_handle: str,
        root_revision: int,
        check: Callable[[], None],
    ) -> tuple[ReadAttempt, bool]:
        ident, binding = self.key(source, command_ref)
        with self.transaction() as db:
            check()
            old = db.execute("SELECT * FROM file_read_attempts WHERE id=?", (ident,)).fetchone()
            if old is not None:
                result = self.row(old, binding)
                check()
                return result, False
            attempt = ReadAttempt(ident, binding, uuid.uuid4().hex, root_handle, root_revision)
            db.execute(
                "INSERT INTO file_read_attempts VALUES (?,?,?,?,?,NULL,NULL)",
                (ident, binding, attempt.token, root_handle, root_revision),
            )
            check()
            return attempt, True

    def signed(self, attempt: ReadAttempt, data: str, *, check: Callable[[], None]) -> None:
        with self.transaction() as db:
            check()
            row = db.execute(
                "SELECT * FROM file_read_attempts WHERE id=?", (attempt.id,)
            ).fetchone()
            if row is None or row["binding"] != attempt.binding or row["token"] != attempt.token:
                raise reject("revision_conflict", "Read journal claim changed", 409)
            if row["receipt_data"] is not None and row["receipt_data"] != data:
                raise reject("revision_conflict", "Different signed read outcome", 409)
            db.execute(
                "UPDATE file_read_attempts SET receipt_data=? WHERE id=?", (data, attempt.id)
            )
            check()

    def published(self, attempt: ReadAttempt, receipt_ref: Ref) -> None:
        ref = fixed_ref(receipt_ref)
        with self.transaction() as db:
            row = db.execute(
                "SELECT * FROM file_read_attempts WHERE id=?", (attempt.id,)
            ).fetchone()
            if row is None or row["binding"] != attempt.binding or not row["receipt_data"]:
                raise reject("revision_conflict", "No signed outcome to publish", 409)
            if row["receipt_ref"] is not None and row["receipt_ref"] != canonical(ref.wire()):
                raise reject("revision_conflict", "Different published read Ref", 409)
            db.execute(
                "UPDATE file_read_attempts SET receipt_ref=? WHERE id=?",
                (canonical(ref.wire()), attempt.id),
            )

    @staticmethod
    def expected_receipt(source: RegisteredReceiptCommand, data: str) -> Ref:
        from uaw.workspace.contracts import RunnerReceipt

        receipt = RunnerReceipt.model_validate_json(data)
        return Ref(
            kind="content",
            id=receipt_id(source.owner, source.device_id, source.command),
            version="1",
            content_hash=digest(receipt.wire()),
        )
