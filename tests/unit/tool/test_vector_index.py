"""Actual SQLite persistence and bounded numerics; no semantic provider is simulated."""

import asyncio
import sqlite3
import struct
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from tests.unit.tool.test_retrieval import NumericalEmbedding
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.tool.embedding import text_hash
from uaw.tool.facade import ToolFacade
from uaw.tool.index import IndexDocument, IndexPlan, SQLiteVectorIndex
from uaw.tool.retrieval import ToolRetriever, projection
from uaw.tool.schema import digest


@pytest.fixture
def plan(registry, ctx):
    embedding = NumericalEmbedding()
    entry = registry.snapshot()[1][0]
    return IndexPlan(
        digest(ctx.principal.wire()),
        embedding.binding,
        (
            IndexDocument(
                Ref.model_validate(registry.reference(entry)),
                Ref.model_validate(entry.spec()["provider_ref"]),
                text_hash(projection(entry)),
            ),
        ),
    )


async def test_actual_sqlite_restart_generation_and_explicit_delete(tmp_path, plan):
    cache = SQLiteVectorIndex(tmp_path / "cache.sqlite")
    assert await cache.read(plan) is None
    await cache.replace(plan, ((1.0, 0.0),))
    restored = SQLiteVectorIndex(cache.path)
    assert await restored.read(plan) == ((1.0, 0.0),)
    await restored.invalidate(plan.namespace)
    assert await cache.read(plan) is None


@pytest.mark.parametrize(
    "change", ["model", "provider", "dimension", "spec", "tool-provider", "text", "namespace"]
)
async def test_index_exact_metadata_binding_invalidates(tmp_path, plan, change):
    cache = SQLiteVectorIndex(tmp_path / "cache.sqlite")
    await cache.replace(plan, ((1.0, 0.0),))
    if change in {"model", "provider"}:
        field = change + "_ref"
        ref = getattr(plan.binding, field).model_copy(
            update={"version": "2", "content_hash": "c" * 64}
        )
        altered = replace(plan, binding=replace(plan.binding, **{field: ref}))
    elif change == "dimension":
        altered = replace(plan, binding=replace(plan.binding, dimensions=3))
    elif change == "namespace":
        altered = replace(plan, namespace="f" * 64)
    else:
        doc = plan.documents[0]
        if change == "text":
            doc = replace(doc, text_hash="d" * 64)
        elif change == "spec":
            doc = replace(doc, tool_ref=doc.tool_ref.model_copy(update={"content_hash": "e" * 64}))
        else:
            doc = replace(doc, provider_ref=doc.provider_ref.model_copy(update={"version": "2"}))
        altered = replace(plan, documents=(doc,))
    assert await cache.read(altered) is None
    assert await cache.read(plan) == ((1.0, 0.0),)


@pytest.mark.parametrize("damage", ["checksum", "blob", "count", "missing", "format"])
async def test_corrupt_index_never_becomes_candidates(tmp_path, plan, damage):
    cache = SQLiteVectorIndex(tmp_path / "cache.sqlite")
    await cache.replace(plan, ((1.0, 0.0),))
    with sqlite3.connect(cache.path) as db:
        if damage == "checksum":
            db.execute("UPDATE snapshots SET checksum='corrupt'")
        elif damage == "blob":
            db.execute("UPDATE vectors SET value=?", (struct.pack(">2d", 0.0, 1.0),))
        elif damage == "count":
            db.execute("UPDATE snapshots SET count=100000000")
        elif damage == "missing":
            db.execute("DELETE FROM vectors")
        else:
            db.execute("PRAGMA user_version=99")
    with pytest.raises(DomainError) as error:
        await cache.read(plan)
    assert error.value.failure.code == "index_invalid"


async def test_non_sqlite_or_oversized_file_refused_without_overwrite(tmp_path, plan):
    path = tmp_path / "bad.sqlite"
    for content in (b"not a database", b"x" * 32769):
        path.write_bytes(content)
        with pytest.raises(DomainError):
            await SQLiteVectorIndex(path, max_bytes=32768).read(plan)
        assert path.read_bytes() == content


async def test_actual_sqlite_concurrent_whole_generations(tmp_path, plan):
    path = tmp_path / "cache.sqlite"
    caches = [SQLiteVectorIndex(path) for _ in range(4)]
    await caches[0].replace(plan, ((1.0, 0.0),))

    async def writer(n):
        await caches[n].replace(plan, (((1.0, 0.0) if n % 2 else (0.0, 1.0)),))

    async def reader(n):
        assert await caches[n].read(plan) in {((1.0, 0.0),), ((0.0, 1.0),)}

    await asyncio.gather(*(writer(n) for n in range(4)), *(reader(n) for n in range(4)))
    assert await caches[0].read(plan) in {((1.0, 0.0),), ((0.0, 1.0),)}
    assert path.stat().st_size <= caches[0].database_bytes


async def test_capacity_failed_replace_rolls_back_old_generation(tmp_path, plan):
    cache = SQLiteVectorIndex(tmp_path / "cache.sqlite", max_bytes=65536)
    await cache.replace(plan, ((1.0, 0.0),))
    # Consume page capacity; generation data passes preflight but SQLite must reject
    # the new write. No deletion/partial generation may escape that transaction.
    with sqlite3.connect(cache.path) as db:
        db.execute("INSERT INTO vectors VALUES(?,?,?)", ("orphan-controlled-row", 9, b"x" * 12000))
    altered = replace(plan, binding=replace(plan.binding, dimensions=1000))
    with pytest.raises(DomainError):
        await cache.replace(altered, (tuple(1.0 for _ in range(1000)),))
    assert await cache.read(plan) == ((1.0, 0.0),)


async def test_namespace_eviction_is_bounded_and_never_cross_user_hit(tmp_path, plan):
    cache = SQLiteVectorIndex(tmp_path / "cache.sqlite", namespaces=1)
    await cache.replace(plan, ((1.0, 0.0),))
    foreign = replace(plan, namespace="f" * 64)
    assert await cache.read(foreign) is None
    await cache.replace(foreign, ((0.0, 1.0),))
    assert await cache.read(plan) is None
    assert await cache.read(foreign) == ((0.0, 1.0),)


async def test_restart_reuses_only_document_vectors_never_user_query(
    tmp_path, registry, access, ctx
):
    path = tmp_path / "cache.sqlite"
    first = NumericalEmbedding()
    retriever = ToolRetriever(registry, access, embeddings=first, index=SQLiteVectorIndex(path))
    result = await retriever.discover("PRIVATE QUERY 文本", [], 1, ctx)
    assert len(first.requests[0]) == 2
    fresh = NumericalEmbedding()
    restored = ToolRetriever(registry, access, embeddings=fresh, index=SQLiteVectorIndex(path))
    assert await restored.discover("PRIVATE QUERY 文本", [], 1, ctx) == result
    assert fresh.requests == [("PRIVATE QUERY 文本",)]
    stored = path.read_bytes()
    assert b"PRIVATE QUERY" not in stored and b"Read exact supplied content" not in stored
    assert ctx.principal.auth_session_id.encode() not in stored


@pytest.mark.parametrize("phase", ["read", "replace"])
async def test_access_revocation_during_index_await_never_returns_old_result(
    tmp_path, registry, access, ctx, phase
):
    cache = SQLiteVectorIndex(tmp_path / "cache.sqlite")
    original = getattr(cache, phase)

    async def changed(*args):
        result = await original(*args)
        access.changes = {"role_categories": frozenset()}
        return result

    setattr(cache, phase, changed)
    with pytest.raises(DomainError) as error:
        await ToolRetriever(
            registry, access, embeddings=NumericalEmbedding(), index=cache
        ).discover("content", [], 1, ctx)
    assert error.value.failure.code == "access_changed"


async def test_uninstall_and_reinstall_current_registry_invalidates_vectors(
    tmp_path, registry, access, ctx, spec, binding
):
    cache = SQLiteVectorIndex(tmp_path / "cache.sqlite")
    embedding = NumericalEmbedding()
    retriever = ToolRetriever(registry, access, embeddings=embedding, index=cache)
    first = await retriever.discover("content", [], 1, ctx)
    ref = first["tools"][0]["tool_ref"]
    registry.unregister(ref, expected_revision=1)
    with pytest.raises(DomainError):
        await retriever.discover("content", [], 1, ctx)
    registry.register({**spec, "version": "v2"}, expected_revision=2, binding=binding)
    current = await retriever.discover("content", [], 1, ctx)
    assert current["registry_revision"] == 3 and current["tools"][0]["tool_ref"]["version"] == "v2"
    assert len(embedding.requests) == 2 and len(embedding.requests[-1]) == 2


async def test_deadline_bounds_blocked_embedding_and_async_cancel_propagates(registry, access, ctx):
    entered = asyncio.Event()
    embedding = NumericalEmbedding()

    async def blocked(*args):
        entered.set()
        await asyncio.Event().wait()

    embedding.embed = blocked
    short = ctx.model_copy(
        update={"deadline": (datetime.now(UTC) + timedelta(seconds=0.2)).isoformat()}
    )
    with pytest.raises(DomainError) as error:
        await ToolRetriever(registry, access, embeddings=embedding).discover(
            "content", [], 1, short
        )
    assert error.value.failure.code == "deadline_exceeded"
    entered.clear()
    task = asyncio.create_task(
        ToolRetriever(registry, access, embeddings=embedding).discover("content", [], 1, ctx)
    )
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.parametrize("change", ["flags", "unused-category", "scope"])
async def test_any_access_snapshot_change_is_rejected_even_if_tool_still_eligible(
    registry, access, ctx, change
):
    async def mutate():
        if change == "flags":
            access.changes = {"enabled_flags": frozenset({"local_files"})}
        elif change == "unused-category":
            access.changes = {"role_categories": frozenset({"content", "extra"})}
        else:
            access.changes = {"allowed_capabilities": frozenset()}

    with pytest.raises(DomainError) as error:
        await ToolRetriever(
            registry, access, embeddings=NumericalEmbedding(change=mutate)
        ).discover("content", [], 1, ctx)
    assert error.value.failure.code == "access_changed"


async def test_embedding_change_during_cache_wait_refuses_before_text_send(
    tmp_path, registry, access, ctx
):
    embedding = NumericalEmbedding()
    cache = SQLiteVectorIndex(tmp_path / "cache.sqlite")
    original = cache.read

    async def revise(*args):
        actual = await original(*args)
        embedding.binding = replace(
            embedding.binding,
            model_ref=embedding.binding.model_ref.model_copy(
                update={"version": "2", "content_hash": "c" * 64}
            ),
        )
        return actual

    cache.read = revise
    with pytest.raises(DomainError) as error:
        await ToolRetriever(registry, access, embeddings=embedding, index=cache).discover(
            "content", [], 1, ctx
        )
    assert error.value.failure.code == "embedding_changed" and not embedding.requests


async def test_index_wait_async_cancel_returns_no_candidate_and_keeps_cache_atomic(
    tmp_path, registry, access, ctx
):
    cache = SQLiteVectorIndex(tmp_path / "cache.sqlite")
    entered = asyncio.Event()

    async def blocked(*args):
        entered.set()
        await asyncio.Event().wait()

    cache.read = blocked
    embedding = NumericalEmbedding()
    pending = asyncio.create_task(
        ToolRetriever(registry, access, embeddings=embedding, index=cache).discover(
            "content", [], 1, ctx
        )
    )
    await entered.wait()
    pending.cancel()
    with pytest.raises(asyncio.CancelledError):
        await pending
    assert not embedding.requests


async def test_fresh_process_reads_actual_sqlite_generation(tmp_path, plan):
    import subprocess
    import sys

    path = tmp_path / "cache.sqlite"
    cache = SQLiteVectorIndex(path)
    await cache.replace(plan, ((1.0, 0.0),))
    # New Python process uses stdlib SQLite to verify actual committed binary data.
    code = (
        "import sqlite3,struct,sys; "
        "db=sqlite3.connect(sys.argv[1]); "
        "v=db.execute('SELECT value FROM vectors').fetchone()[0]; "
        "assert struct.unpack('>2d',v)==(1.0,0.0); "
        "assert db.execute('SELECT count FROM snapshots').fetchone()[0]==1; "
        "db.close(); print('actual persisted generation read')"
    )
    completed = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-c", code, str(path)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stdout.strip() == "actual persisted generation read"


async def test_large_default_index_supports_128_fixed_specs_4096_dimensions(tmp_path, plan):
    documents = tuple(
        replace(
            plan.documents[0],
            tool_ref=plan.documents[0].tool_ref.model_copy(update={"id": f"tool-{i}"}),
        )
        for i in range(128)
    )
    large = replace(plan, binding=replace(plan.binding, dimensions=4096), documents=documents)
    cache = SQLiteVectorIndex(tmp_path / "large.sqlite")
    vectors = tuple(tuple(1.0 for _ in range(4096)) for _ in range(128))
    await cache.replace(large, vectors)
    assert await cache.read(large) == vectors
    assert cache.path.stat().st_size <= cache.database_bytes
    assert not cache.path.with_name(cache.path.name + "-journal").exists()


async def test_cache_namespace_changes_with_complete_principal_session(
    tmp_path, registry, access, ctx
):
    cache = SQLiteVectorIndex(tmp_path / "cache.sqlite")
    first_embedding = NumericalEmbedding()
    assert (
        await ToolRetriever(registry, access, embeddings=first_embedding, index=cache).discover(
            "content", [], 1, ctx
        )
    )["tools"]
    second_embedding = NumericalEmbedding()
    different = ctx.model_copy(
        update={"principal": ctx.principal.model_copy(update={"auth_session_id": "fresh-session"})}
    )
    # Current permission fixture intentionally grants both sessions; cache must still miss.
    assert (
        await ToolRetriever(registry, access, embeddings=second_embedding, index=cache).discover(
            "content", [], 1, different
        )
    )["tools"]
    assert len(first_embedding.requests[0]) == len(second_embedding.requests[0]) == 2


@pytest.mark.parametrize("access_kind", ["missing", "malformed"])
async def test_missing_or_malformed_current_access_is_unavailable(
    registry, access, ctx, access_kind
):
    embedding = NumericalEmbedding()
    if access_kind == "missing":
        actual_access = None
    else:

        async def invalid(*args):
            return {"approved": True}

        access.snapshot = invalid
        actual_access = access
    facade = ToolFacade(
        registry, retriever=ToolRetriever(registry, actual_access, embeddings=embedding)
    )
    result = await facade.discover({"query": "content", "max_candidates": 1}, ctx)
    assert result["failure"]["code"] == (
        "dependency_unavailable" if access_kind == "missing" else "dependency_protocol_invalid"
    )
    assert not embedding.requests
