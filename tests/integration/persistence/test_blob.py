import asyncio
import hashlib
from pathlib import Path

import pytest

from uaw.infrastructure.blob.filesystem import BlobCorrupt, FSBlobStore
from uaw.shared.contracts import Principal
from uaw.shared.schema import ContractViolation
from uaw.shared.stores import StoreMissing


async def test_blobs_are_immutable_scoped_and_survive_new_adapter(
    tmp_path: Path, principal: Principal
) -> None:
    store = FSBlobStore(tmp_path)
    data = "用户原始材料".encode()
    digests = await asyncio.gather(store.put(principal, data), store.put(principal, data))
    assert digests == [hashlib.sha256(data).hexdigest()] * 2
    assert await FSBlobStore(tmp_path).get(principal, digests[0]) == data
    stranger = Principal(id="stranger", kind="user", auth_session_id="stranger-session")
    with pytest.raises(StoreMissing):
        await store.get(stranger, digests[0])
    with pytest.raises(ContractViolation):
        await store.get(principal, "../../outside")


async def test_tampered_blob_is_never_returned(tmp_path: Path, principal: Principal) -> None:
    store = FSBlobStore(tmp_path)
    digest = await store.put(principal, b"original")
    owner = hashlib.sha256(principal.id.encode()).hexdigest()
    (tmp_path / owner / digest[:2] / digest).write_bytes(b"changed")
    with pytest.raises(BlobCorrupt):
        await store.get(principal, digest)
    with pytest.raises(BlobCorrupt):
        await store.put(principal, b"original")


async def test_blob_size_limit_is_checked(tmp_path: Path, principal: Principal) -> None:
    with pytest.raises(ValueError, match="size limit"):
        await FSBlobStore(tmp_path, max_bytes=4).put(principal, b"12345")
