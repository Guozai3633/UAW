"""Signed terminal receipt journal; explicit development SQLite, no execution authority."""

import asyncio
import hashlib
import json
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Any

from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.workspace.contracts import RegisteredReceiptCommand, RunnerCommand, RunnerReceipt
from uaw.workspace.ports import ReceiptCommandReaderPort
from uaw_runner.protocol import RunnerProtocol


def canonical(value: Any) -> str:
    # Internal content addressing only; signature verification uses the public receipt domain.
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def fixed_ref(ref: Ref) -> Ref:
    copied = Ref.model_validate_json(canonical(ref.wire()))
    if (
        copied.content_hash is None
        or copied.version in ("latest", "current", "*")
        or "location" in copied.wire()
        or "access_scope" in copied.wire()
    ):
        raise reject("schema_invalid", "A whole fixed version and content hash are required")
    return copied


@dataclass(frozen=True)
class SavedReceipt:
    receipt_id: str
    owner_kind: str
    owner_id: str
    owner_hash: str
    device_id: str
    command_id: str
    attempt_id: str
    command_ref: Ref
    receipt_data: str
    receipt_hash: str

    def ref(self) -> Ref:
        # ms-i2e RefKind has no runner_receipt enum. Use its existing artifact container
        # with an internal runner_receipt namespace; a new public kind belongs to A.
        return Ref(kind="artifact", id=self.receipt_id, version="1", content_hash=self.receipt_hash)


def receipt_id(owner: Principal, device_id: str, command: RunnerCommand) -> str:
    key = [owner.kind, owner.id, device_id, command.command_id, command.trusted_context.attempt_id]
    return "runner_receipt-" + digest(key)


class ReceiptJournal:
    def __init__(
        self,
        path: Path,
        *,
        protocol: RunnerProtocol,
        reader: ReceiptCommandReaderPort | None = None,
    ) -> None:
        # Construction does no filesystem/SQLite IO. All work below runs off the event loop.
        self.path = path.absolute()
        self.protocol, self.reader = protocol, reader
        self.device_id = protocol.device_id

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        db: sqlite3.Connection | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
            db.row_factory = sqlite3.Row
            db.execute("BEGIN IMMEDIATE")
            db.execute("""CREATE TABLE IF NOT EXISTS terminal_receipts (
                receipt_id TEXT PRIMARY KEY, owner_kind TEXT NOT NULL, owner_id TEXT NOT NULL,
                owner_hash TEXT NOT NULL, device_id TEXT NOT NULL, command_id TEXT NOT NULL,
                attempt_id TEXT NOT NULL, command_ref TEXT NOT NULL, receipt_data TEXT NOT NULL,
                receipt_hash TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision=1),
                UNIQUE(owner_kind, owner_id, device_id, command_id, attempt_id))""")
            yield db
            db.commit()
        except sqlite3.IntegrityError:
            raise reject("revision_conflict", "Receipt journal constraint conflict", 409) from None
        except sqlite3.DatabaseError, OSError:
            raise CapabilityUnavailable("runner.receipt_journal") from None
        finally:
            if db is not None:
                # Also rolls back cancellation, validation failures and interrupted insertion.
                db.close()

    async def _resolve(
        self, ref: Ref, actor: Principal, original: RegisteredReceiptCommand | None = None
    ) -> RegisteredReceiptCommand:
        if self.reader is None:
            raise CapabilityUnavailable("runner.receipt_command_reader")
        result = await self.reader.resolve(
            Ref.model_validate_json(canonical(ref.wire())),
            authenticated_principal=Principal.model_validate_json(canonical(actor.wire())),
        )
        if not isinstance(result, RegisteredReceiptCommand):
            raise reject("dependency_protocol_invalid", "Invalid registered command source", 503)
        try:
            command = RunnerCommand.model_validate_json(canonical(result.command.wire()))
            owner = Principal.model_validate_json(canonical(result.owner.wire()))
            validate_contract("ID", result.device_id)
        except ValueError, AttributeError:
            raise reject(
                "dependency_protocol_invalid", "Invalid registered command fields", 503
            ) from None
        current = RegisteredReceiptCommand(command, result.device_id, owner)
        if (
            owner.kind != "user"
            or owner.wire() != command.trusted_context.principal.wire()
            or result.device_id != self.device_id
            or actor.kind not in ("user", "runner")
            or (actor.kind == "user" and actor.wire() != owner.wire())
        ):
            raise reject(
                "permission_denied", "Registered owner/device/channel mismatch", 403, "permission"
            )
        # Reader must independently prove the actual version too; this additionally detects
        # a source violating immutable content at a pinned Ref. No command body is accepted.
        if digest(command.wire()) != ref.content_hash:
            raise reject("revision_conflict", "Registered command changed at fixed Ref", 409)
        if original is not None and (
            current.device_id != original.device_id
            or current.owner.wire() != original.owner.wire()
            or current.command.wire() != original.command.wire()
        ):
            raise reject("revision_conflict", "Registered receipt source changed", 409)
        return current

    def _verify(self, data: str | bytes, source: RegisteredReceiptCommand) -> RunnerReceipt:
        if self.protocol.device_id != self.device_id:
            raise reject("revision_conflict", "Receipt verifier device changed", 409)
        receipt = self.protocol.verify_receipt(data, command=source.command)
        if receipt.kind == "waiting":
            raise CapabilityUnavailable("runner.receipt_progress_journal")
        return receipt

    @staticmethod
    def _row(row: sqlite3.Row) -> SavedReceipt:
        if row["revision"] != 1:
            raise reject("revision_conflict", "Receipt journal version changed", 409)
        return SavedReceipt(
            row["receipt_id"],
            row["owner_kind"],
            row["owner_id"],
            row["owner_hash"],
            row["device_id"],
            row["command_id"],
            row["attempt_id"],
            fixed_ref(Ref.model_validate_json(row["command_ref"])),
            row["receipt_data"],
            row["receipt_hash"],
        )

    def _checked_record(
        self, saved: SavedReceipt, source: RegisteredReceiptCommand
    ) -> RunnerReceipt:
        receipt = self._verify(saved.receipt_data, source)
        if (
            saved.receipt_id != receipt_id(source.owner, source.device_id, source.command)
            or saved.owner_kind != source.owner.kind
            or saved.owner_id != source.owner.id
            or saved.owner_hash != digest(source.owner.wire())
            or saved.device_id != source.device_id
            or saved.command_id != source.command.command_id
            or saved.attempt_id != source.command.trusted_context.attempt_id
            or saved.command_ref.content_hash != digest(source.command.wire())
            or saved.receipt_hash != digest(receipt.wire())
        ):
            raise reject("revision_conflict", "Receipt journal content/binding changed", 409)
        return receipt

    def _save(
        self, saved: SavedReceipt, source: RegisteredReceiptCommand, check: Callable[[], None]
    ) -> SavedReceipt:
        with self._transaction() as db:
            check()  # After acquiring the cross-process write lock, including replay.
            self._checked_record(saved, source)  # Fresh key/role/revocation inside local CAS.
            row = db.execute(
                "SELECT * FROM terminal_receipts WHERE receipt_id=?", (saved.receipt_id,)
            ).fetchone()
            if row is not None:
                old = self._row(row)
                self._checked_record(old, source)
                if (
                    old.command_ref.wire() != saved.command_ref.wire()
                    or old.receipt_hash != saved.receipt_hash
                    or canonical(json.loads(old.receipt_data))
                    != canonical(json.loads(saved.receipt_data))
                ):
                    raise reject(
                        "revision_conflict", "Different terminal receipt already saved", 409
                    )
                result = old
            else:
                db.execute(
                    "INSERT INTO terminal_receipts VALUES (?,?,?,?,?,?,?,?,?,?,1)",
                    (
                        saved.receipt_id,
                        saved.owner_kind,
                        saved.owner_id,
                        saved.owner_hash,
                        saved.device_id,
                        saved.command_id,
                        saved.attempt_id,
                        canonical(saved.command_ref.wire()),
                        saved.receipt_data,
                        saved.receipt_hash,
                    ),
                )
                result = saved
            check()  # Failure here closes/rolls back the transaction, never overwrites history.
            self._checked_record(result, source)
            check()
            return result

    def _load(self, ref: Ref) -> SavedReceipt:
        with self._transaction() as db:
            row = db.execute(
                "SELECT * FROM terminal_receipts WHERE receipt_id=?", (ref.id,)
            ).fetchone()
            if row is None:
                raise reject("receipt_missing", "Receipt journal record missing", 404)
            saved = self._row(row)
            if saved.ref().wire() != ref.wire():
                raise reject(
                    "revision_conflict", "Receipt Ref differs from saved version/hash", 409
                )
            return saved

    async def publish(
        self, command_ref: Ref, receipt_data: str | bytes, *, authenticated_principal: Principal
    ) -> Ref:
        if self.reader is None:
            raise CapabilityUnavailable("runner.receipt_command_reader")
        ref = fixed_ref(command_ref)
        actor = Principal.model_validate_json(canonical(authenticated_principal.wire()))
        # Immutable original input; received JSON text is stored, not re-signed or fabricated.
        try:
            data = receipt_data.decode("utf-8") if isinstance(receipt_data, bytes) else receipt_data
        except UnicodeDecodeError:
            raise reject("schema_invalid", "Receipt must contain UTF-8 JSON") from None
        stopped = Event()

        def check() -> None:
            if stopped.is_set():
                raise reject("cancelled", "Receipt publication cancelled", 409, "cancelled")

        try:
            source = await self._resolve(ref, actor)
            receipt = await asyncio.to_thread(self._verify, data, source)
            source = await self._resolve(ref, actor, source)
            saved = SavedReceipt(
                receipt_id(source.owner, source.device_id, source.command),
                source.owner.kind,
                source.owner.id,
                digest(source.owner.wire()),
                source.device_id,
                source.command.command_id,
                source.command.trusted_context.attempt_id,
                ref,
                data,
                digest(receipt.wire()),
            )
            actual = await asyncio.to_thread(self._save, saved, source, check)
            # Access revoked during lock/IO may leave a truthful committed record but must
            # not return it to the caller. Recovery still requires current Reader/key checks.
            source = await self._resolve(ref, actor, source)
            await asyncio.to_thread(self._checked_record, actual, source)
            return actual.ref()
        except asyncio.CancelledError:
            stopped.set()
            raise

    async def read(self, receipt_ref: Ref, *, authenticated_principal: Principal) -> RunnerReceipt:
        if self.reader is None:
            raise CapabilityUnavailable("runner.receipt_command_reader")
        ref = fixed_ref(receipt_ref)
        actor = Principal.model_validate_json(canonical(authenticated_principal.wire()))
        saved = await asyncio.to_thread(self._load, ref)
        source = await self._resolve(saved.command_ref, actor)
        await asyncio.to_thread(self._checked_record, saved, source)
        source = await self._resolve(saved.command_ref, actor, source)
        return await asyncio.to_thread(self._checked_record, saved, source)
