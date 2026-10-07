import asyncio
import hashlib
import os
import tempfile
from pathlib import Path

from uaw.shared.contracts import Principal
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing


class BlobCorrupt(ValueError):
    pass


class FSBlobStore:
    """The directory must be private to the control-plane OS account, not task code."""

    def __init__(self, directory: Path, *, max_bytes: int = 104_857_600) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        self.directory = directory.resolve(strict=True)
        self.max_bytes = max_bytes

    def _path(
        self, principal: Principal, content_hash: str, *, create_parent: bool = False
    ) -> Path:
        validate_contract("Principal", principal.wire())
        validate_contract("Hash", content_hash)
        owner = hashlib.sha256(principal.id.encode("utf-8")).hexdigest()
        path = self.directory / owner / content_hash[:2] / content_hash
        # Check existing ancestors before creating anything. Resolving nonexistent paths
        # concurrently with mkdir can give inconsistent paths on Windows.
        ancestor = path.parent
        while not ancestor.exists():
            ancestor = ancestor.parent
        if not ancestor.resolve(strict=True).is_relative_to(self.directory):
            raise ValueError("Blob path escapes private data directory")
        if create_parent:
            path.parent.mkdir(parents=True, exist_ok=True)
        if not path.parent.exists():
            raise StoreMissing()
        if not path.parent.resolve(strict=True).is_relative_to(self.directory):
            raise ValueError("Blob path escapes private data directory")
        if path.exists() and not path.resolve(strict=True).is_relative_to(self.directory):
            raise ValueError("Blob path escapes private data directory")
        return path

    async def put(self, principal: Principal, content: bytes) -> str:
        if len(content) > self.max_bytes:
            raise ValueError("Blob exceeds configured size limit")
        digest = hashlib.sha256(content).hexdigest()
        path = self._path(principal, digest, create_parent=True)
        await asyncio.to_thread(self._write, path, content, digest)
        return digest

    def _write(self, path: Path, content: bytes, digest: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.resolve().is_relative_to(self.directory):
            raise ValueError("Blob path escapes private data directory")
        descriptor, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            # Exclusive publication. Concurrent identical writes cannot replace existing content.
            try:
                os.link(temporary, path)
            except FileExistsError:
                if self._read(path, digest) != content:
                    raise BlobCorrupt(
                        "Existing blob differs from the expected immutable content"
                    ) from None
        finally:
            Path(temporary).unlink(missing_ok=True)

    async def get(self, principal: Principal, content_hash: str) -> bytes:
        path = self._path(principal, content_hash)
        return await asyncio.to_thread(self._read, path, content_hash)

    def _read(self, path: Path, digest: str) -> bytes:
        if not path.resolve().is_relative_to(self.directory):
            raise ValueError("Blob path escapes private data directory")
        try:
            with path.open("rb") as stream:
                data = stream.read(self.max_bytes + 1)
        except FileNotFoundError as exc:
            raise StoreMissing() from exc
        if len(data) > self.max_bytes or hashlib.sha256(data).hexdigest() != digest:
            raise BlobCorrupt("Blob integrity check failed")
        return data
