"""Rebuildable bounded SQLite vector cache, never a registry or authority."""

import asyncio
import hashlib
import sqlite3
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from uaw.shared.contracts import Ref
from uaw.tool.embedding import EmbeddingBinding, vector
from uaw.tool.errors import fail
from uaw.tool.schema import canonical

MAX_INDEX_BYTES = 16 * 1024 * 1024
APPLICATION_ID = 0x55415743


@dataclass(frozen=True)
class IndexDocument:
    tool_ref: Ref
    provider_ref: Ref
    text_hash: str

    def wire(self) -> dict[str, object]:
        return {
            "tool_ref": self.tool_ref.wire(),
            "provider_ref": self.provider_ref.wire(),
            "text_hash": self.text_hash,
        }


@dataclass(frozen=True)
class IndexPlan:
    namespace: str  # hash of independent full principal/session; not a permission snapshot
    binding: EmbeddingBinding
    documents: tuple[IndexDocument, ...]

    def validate(self) -> None:
        self.binding.validate()
        if len(self.namespace) != 64 or any(c not in "0123456789abcdef" for c in self.namespace):
            raise ValueError("Expected hashed cache namespace")
        if type(self.documents) is not tuple or not 1 <= len(self.documents) <= 128:
            raise ValueError("Bounded document batch required")
        refs = []
        for doc in self.documents:
            if (
                doc.tool_ref.kind != "configuration"
                or not doc.tool_ref.version
                or not doc.tool_ref.content_hash
                or doc.provider_ref.kind != "provider"
                or not doc.provider_ref.version
                or doc.tool_ref.location is not None
                or doc.tool_ref.access_scope is not None
                or doc.provider_ref.location is not None
                or doc.provider_ref.access_scope is not None
                or len(doc.text_hash) != 64
                or any(c not in "0123456789abcdef" for c in doc.text_hash)
            ):
                raise ValueError("Invalid fixed index document metadata")
            refs.append(canonical(doc.tool_ref.wire()))
        if len(refs) != len(set(refs)):
            raise ValueError("Duplicate index document")

    def metadata(self) -> bytes:
        self.validate()
        return canonical(
            {
                "format": 1,
                "binding": {
                    "provider_ref": self.binding.provider_ref.wire(),
                    "model_ref": self.binding.model_ref.wire(),
                    "dimensions": self.binding.dimensions,
                    "text_version": self.binding.text_version,
                },
                "documents": [d.wire() for d in self.documents],
            }
        )


class ToolVectorIndexPort(Protocol):
    async def read(self, plan: IndexPlan) -> tuple[tuple[float, ...], ...] | None: ...

    async def replace(self, plan: IndexPlan, vectors: tuple[tuple[float, ...], ...]) -> None: ...

    async def invalidate(self, namespace: str) -> None: ...


class SQLiteVectorIndex:
    """Trusted private path; no query/raw text, auth result, credentials or ToolResult.

    Transactions replace an entire generation. Separate connections/instances use
    SQLite's single writer; readers see one complete generation. Cache corruption
    fails explicitly; trusted code can discard/rebuild, not silently fake vectors.
    """

    def __init__(
        self, path: Path, *, max_bytes: int = MAX_INDEX_BYTES, namespaces: int = 8
    ) -> None:
        if type(max_bytes) is not int or not 32768 <= max_bytes <= MAX_INDEX_BYTES:
            raise ValueError("Index byte bound must be 32KiB..16MiB")
        if type(namespaces) is not int or not 1 <= namespaces <= 32:
            raise ValueError("Namespace bound must be 1..32")
        self.path, self.max_bytes, self.namespaces = Path(path), max_bytes, namespaces
        # Reserve half for the rollback journal plus per-page/header overhead.
        reserve = max(8192, max_bytes // 64)
        self.database_bytes = ((max_bytes - reserve) // 8192) * 4096

    def _connect(self) -> sqlite3.Connection:
        if self.path.exists() and self.path.stat().st_size > self.database_bytes:
            raise ValueError("Cache file exceeds configured byte bound")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=2, isolation_level=None)
        try:
            db.execute("PRAGMA trusted_schema=OFF")
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA journal_mode=DELETE")
            db.execute("BEGIN IMMEDIATE")
            version = db.execute("PRAGMA user_version").fetchone()[0]
            app = db.execute("PRAGMA application_id").fetchone()[0]
            tables = {
                row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            if version == 0 and app == 0 and not tables:
                db.execute(
                    "CREATE TABLE snapshots(namespace TEXT PRIMARY KEY, metadata BLOB NOT NULL, "
                    "checksum TEXT NOT NULL, generation INTEGER NOT NULL, count INTEGER NOT NULL)"
                )
                db.execute(
                    "CREATE TABLE vectors(namespace TEXT NOT NULL REFERENCES snapshots(namespace) "
                    "ON DELETE CASCADE, position INTEGER NOT NULL, value BLOB NOT NULL, "
                    "PRIMARY KEY(namespace,position))"
                )
                db.execute(f"PRAGMA application_id={APPLICATION_ID}")
                db.execute("PRAGMA user_version=1")
            elif version != 1 or app != APPLICATION_ID or tables != {"snapshots", "vectors"}:
                raise ValueError("Unrecognized index cache format")
            page_size = db.execute("PRAGMA page_size").fetchone()[0]
            if db.execute("PRAGMA page_count").fetchone()[0] * page_size > self.database_bytes:
                raise ValueError("Cache page bound exceeded")
            db.execute(f"PRAGMA max_page_count={self.database_bytes // page_size}")
            db.execute("COMMIT")
            return db
        except BaseException:
            db.close()
            raise

    @staticmethod
    def checksum(metadata: bytes, blobs: tuple[bytes, ...]) -> str:
        sha = hashlib.sha256(metadata)
        for blob in blobs:
            sha.update(struct.pack(">I", len(blob)))
            sha.update(blob)
        return sha.hexdigest()

    async def read(self, plan: IndexPlan) -> tuple[tuple[float, ...], ...] | None:
        metadata = plan.metadata()
        return await asyncio.to_thread(self._read, plan, metadata)

    def _read(self, plan: IndexPlan, metadata: bytes) -> tuple[tuple[float, ...], ...] | None:
        try:
            db = self._connect()
            try:
                db.execute("BEGIN")
                row = db.execute(
                    "SELECT metadata, checksum, count FROM snapshots WHERE namespace=?",
                    (plan.namespace,),
                ).fetchone()
                if row is None:
                    return None
                if (
                    type(row[2]) is not int
                    or not 1 <= row[2] <= 128
                    or type(row[0]) is not bytes
                    or len(row[0]) > 65536
                ):
                    raise ValueError("Invalid cache generation metadata/count")
                rows = db.execute(
                    "SELECT position,value FROM vectors WHERE namespace=? "
                    "ORDER BY position LIMIT 129",
                    (plan.namespace,),
                ).fetchall()
                if len(rows) != row[2] or [r[0] for r in rows] != list(range(row[2])):
                    raise ValueError("Cache generation is incomplete")
                blobs = tuple(r[1] for r in rows)
                if type(row[1]) is not str or any(type(b) is not bytes for b in blobs):
                    raise ValueError("Invalid cache blob/checksum types")
                if self.checksum(row[0], blobs) != row[1]:
                    raise ValueError("Cache content checksum differs")
                if row[0] != metadata:
                    return None  # Definitive config/catalogue mismatch; rebuild with current refs.
                if row[2] != len(plan.documents):
                    raise ValueError("Cache vector count differs")
                result = []
                for blob in blobs:
                    if len(blob) != 8 * plan.binding.dimensions:
                        raise ValueError("Cache vector dimension differs")
                    result.append(
                        vector(
                            struct.unpack(f">{plan.binding.dimensions}d", blob),
                            plan.binding.dimensions,
                        )
                    )
                return tuple(result)
            finally:
                db.close()
        except (sqlite3.Error, OSError, ValueError, TypeError, struct.error) as exc:
            raise fail(
                "index_invalid",
                "Vector cache cannot be verified; explicit rebuild required",
                phase="retrieval",
                category="dependency",
                status=503,
            ) from exc

    async def replace(self, plan: IndexPlan, vectors: tuple[tuple[float, ...], ...]) -> None:
        metadata = plan.metadata()
        if type(vectors) is not tuple or len(vectors) != len(plan.documents):
            raise ValueError("Index vector batch count differs")
        blobs = tuple(
            struct.pack(f">{plan.binding.dimensions}d", *vector(v, plan.binding.dimensions))
            for v in vectors
        )
        if len(metadata) + sum(len(b) for b in blobs) > self.database_bytes - 16384:
            raise fail(
                "index_full",
                "Index generation exceeds configured capacity",
                phase="retrieval",
                category="dependency",
                status=503,
            )
        await asyncio.to_thread(self._replace, plan, metadata, blobs)

    def _replace(self, plan: IndexPlan, metadata: bytes, blobs: tuple[bytes, ...]) -> None:
        try:
            db = self._connect()
            try:
                db.execute("BEGIN IMMEDIATE")
                generation = db.execute(
                    "SELECT COALESCE(MAX(generation),0)+1 FROM snapshots"
                ).fetchone()[0]
                db.execute("DELETE FROM snapshots WHERE namespace=?", (plan.namespace,))
                # Evict old generations deterministically; never store permissions here.
                rows = db.execute(
                    "SELECT namespace FROM snapshots ORDER BY generation DESC,namespace"
                ).fetchall()
                for row in rows[self.namespaces - 1 :]:
                    db.execute("DELETE FROM snapshots WHERE namespace=?", row)
                db.execute(
                    "INSERT INTO snapshots VALUES(?,?,?,?,?)",
                    (
                        plan.namespace,
                        metadata,
                        self.checksum(metadata, blobs),
                        generation,
                        len(blobs),
                    ),
                )
                db.executemany(
                    "INSERT INTO vectors VALUES(?,?,?)",
                    [(plan.namespace, i, b) for i, b in enumerate(blobs)],
                )
                db.execute("COMMIT")
            finally:
                db.close()
        except (sqlite3.Error, OSError, ValueError) as exc:
            raise fail(
                "index_invalid",
                "Atomic index replacement failed; old generation preserved",
                phase="retrieval",
                category="dependency",
                status=503,
            ) from exc

    async def invalidate(self, namespace: str) -> None:
        await asyncio.to_thread(self._invalidate, namespace)

    def _invalidate(self, namespace: str) -> None:
        try:
            db = self._connect()
            try:
                db.execute("BEGIN IMMEDIATE")
                db.execute("DELETE FROM snapshots WHERE namespace=?", (namespace,))
                db.execute("COMMIT")
            finally:
                db.close()
        except (sqlite3.Error, OSError, ValueError) as exc:
            raise fail(
                "index_invalid",
                "Cannot invalidate unverified cache",
                phase="retrieval",
                category="dependency",
                status=503,
            ) from exc
