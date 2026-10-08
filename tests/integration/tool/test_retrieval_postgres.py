"""Actual PostgreSQL authorization + SQLite cache; embeddings are controlled numerics."""

import asyncio
import sqlite3
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from tests.integration.test_control_plane import meta
from tests.integration.test_runtime_sources import profile
from tests.integration.test_runtime_sources import sources as sources
from tests.integration.tool.test_durable import cancel
from tests.unit.tool.test_retrieval import NumericalEmbedding
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.run.budget import BudgetService
from uaw.run.execution_sources import RunExecutionSources
from uaw.run.permissions import ExecutionPolicyResolver
from uaw.run.tool_sources import RunToolAccessSources
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.tool.facade import ToolFacade
from uaw.tool.index import SQLiteVectorIndex
from uaw.tool.registry import AdapterBinding
from uaw.tool.retrieval import ToolRetriever


def wired(sources, tool_case, tmp_path, *, embedding=None):
    cache = SQLiteVectorIndex(tmp_path / "vectors.sqlite")
    embedding = embedding or NumericalEmbedding()
    retriever = ToolRetriever(tool_case.registry, sources[0], embeddings=embedding, index=cache)
    return ToolFacade(tool_case.registry, sources[0], retriever=retriever), embedding, cache


async def test_registered_sql_access_cache_restart_without_execution(sources, tool_case, tmp_path):
    facade, embedding, cache = wired(sources, tool_case, tmp_path)
    request = {"query": "PRIVATE QUERY EXACT 文本", "max_candidates": 3}
    fixed = tool_case.ctx.wire()
    budget = BudgetService(tool_case.ledger.store)
    before = await budget.get_ledger(tool_case.ctx)
    first = await facade.discover(request, tool_case.ctx)
    assert first["kind"] == "ok"
    assert [t["tool_ref"]["id"] for t in first["payload"]["tools"]] == ["text.inspect"]
    assert len(embedding.requests[0]) == 2 and "fixture.write" not in str(embedding.requests)
    records = PostgresRecordStore(tool_case.ledger.store.database)
    config = tool_case.domain[0]
    restored_access = RunToolAccessSources(
        records,
        config,
        RunExecutionSources(records, config, ExecutionPolicyResolver(records)),
        environment="sql-component-test",
    )
    fresh = NumericalEmbedding()
    restored = ToolFacade(
        tool_case.registry,
        restored_access,
        retriever=ToolRetriever(
            tool_case.registry,
            restored_access,
            embeddings=fresh,
            index=SQLiteVectorIndex(cache.path),
        ),
    )
    assert await restored.discover(request, tool_case.ctx) == first
    assert fresh.requests == [(request["query"],)]
    assert tool_case.ctx.wire() == fixed and await budget.get_ledger(tool_case.ctx) == before
    assert b"PRIVATE QUERY EXACT" not in cache.path.read_bytes()
    assert (
        await tool_case.ledger.get(
            "tool.invocation.receipts", tool_case.ctx.attempt_id, tool_case.ctx
        )
        is None
    )


@pytest.mark.parametrize("mode", ["lexical-only", "semantic-required"])
async def test_explicit_missing_embedding_mode(sources, tool_case, mode):
    retriever = ToolRetriever(tool_case.registry, sources[0], mode=mode)
    result = await ToolFacade(tool_case.registry, sources[0], retriever=retriever).discover(
        {"query": "text.inspect", "max_candidates": 1}, tool_case.ctx
    )
    if mode == "lexical-only":
        assert result["kind"] == "ok"
    else:
        assert result["failure"]["code"] == "dependency_unavailable"


@pytest.mark.parametrize("change", ["role", "binding", "cancel", "policy", "provider", "uninstall"])
async def test_sql_sources_change_during_embedding_blocks_candidates(
    sources, tool_case, tmp_path, change
):
    config, run, admin = tool_case.domain

    async def mutate():
        if change == "role":
            await sources[0].register_role(
                profile(categories=[], version="2"),
                meta("revise-retrieval-role", 1),
                authenticated_service=config.platform,
            )
        elif change == "binding":
            await sources[0].revoke(
                tool_case.ctx,
                meta("revoke-retrieval-binding", 1),
                authenticated_service=config.platform,
            )
        elif change == "cancel":
            await cancel(tool_case)
        elif change == "policy":
            row = await run.store.get(
                tool_case.ctx.principal,
                "execution.policies",
                tool_case.ctx.capability_policy_ref.id,
            )
            await run.store.put(
                tool_case.ctx.principal,
                "execution.policies",
                row.payload["id"],
                "CapabilityPolicy",
                {**row.payload, "revision": 2, "denied_capabilities": ["tool.invoke"]},
                expected_revision=1,
                request_id="change-retrieval-policy",
            )
        elif change == "provider":
            await config.revoke_provider(
                admin, "fixture-provider", meta("revoke-retrieval-provider", 2)
            )
        else:
            ref = tool_case.registry.reference(tool_case.registry.snapshot()[1][-1])
            tool_case.registry.unregister(ref, expected_revision=tool_case.registry.revision)

    embedding = NumericalEmbedding(change=mutate)
    facade, _, cache = wired(sources, tool_case, tmp_path, embedding=embedding)
    result = await facade.discover({"query": "content", "max_candidates": 2}, tool_case.ctx)
    assert result["kind"] != "ok" and "payload" not in result
    with sqlite3.connect(cache.path) as db:
        assert db.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0] == 0


@pytest.mark.parametrize("source", ["role", "binding", "provider"])
async def test_old_cache_cannot_bypass_sql_revocation(sources, tool_case, tmp_path, source):
    facade, embedding, _ = wired(sources, tool_case, tmp_path)
    request = {"query": "content", "max_candidates": 2}
    assert (await facade.discover(request, tool_case.ctx))["kind"] == "ok"
    config, _, admin = tool_case.domain
    if source == "role":
        await sources[0].register_role(
            profile(categories=[], version="2"),
            meta("role-revise", 1),
            authenticated_service=config.platform,
        )
    elif source == "binding":
        await sources[0].revoke(
            tool_case.ctx, meta("binding-revoke", 1), authenticated_service=config.platform
        )
    else:
        await config.revoke_provider(admin, "fixture-provider", meta("provider-revoke", 2))
    result = await facade.discover(request, tool_case.ctx)
    assert result["kind"] != "ok" and len(embedding.requests) == 1


@pytest.mark.parametrize("identity", ["session", "kind", "principal", "model", "scope"])
async def test_actual_complete_identity_prevents_cached_candidate_leak(
    sources, tool_case, tmp_path, identity
):
    facade, embedding, _ = wired(sources, tool_case, tmp_path)
    request = {"query": "content", "max_candidates": 2}
    assert (await facade.discover(request, tool_case.ctx))["kind"] == "ok"
    ctx = tool_case.ctx
    if identity in {"session", "kind", "principal"}:
        field = {"session": "auth_session_id", "kind": "kind", "principal": "id"}[identity]
        value = "admin" if identity == "kind" else "foreign"
        ctx = ctx.model_copy(update={"principal": ctx.principal.model_copy(update={field: value})})
    elif identity == "model":
        ctx = ctx.model_copy(
            update={"model_policy_ref": Ref(kind="policy", id="foreign-model", version="1")}
        )
    else:
        ctx = ctx.model_copy(
            update={"scope": ctx.scope.model_copy(update={"capabilities": ("tool.invoke", "exec")})}
        )
    refused = await facade.discover(request, ctx)
    assert refused["kind"] != "ok" and "payload" not in refused and len(embedding.requests) == 1


async def test_corrupt_vector_blocks_actual_sql_discovery(sources, tool_case, tmp_path):
    facade, embedding, cache = wired(sources, tool_case, tmp_path)
    query = {"query": "content", "max_candidates": 2}
    assert (await facade.discover(query, tool_case.ctx))["kind"] == "ok"
    with sqlite3.connect(cache.path) as db:
        db.execute("UPDATE snapshots SET checksum='corrupt'")
    result = await facade.discover(query, tool_case.ctx)
    assert result["failure"]["code"] == "index_invalid" and len(embedding.requests) == 1


async def test_concurrent_discovery_has_atomic_cache_and_actual_access(
    sources, tool_case, tmp_path
):
    facade, embedding, cache = wired(sources, tool_case, tmp_path)
    request = {"query": "content", "max_candidates": 2}
    results = await asyncio.gather(*(facade.discover(request, tool_case.ctx) for _ in range(3)))
    assert all(result == results[0] and result["kind"] == "ok" for result in results)
    with sqlite3.connect(cache.path) as db:
        assert db.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM vectors").fetchone()[0] == 1
    assert len(embedding.requests) == 3


async def test_fixed_embedding_model_version_rebuilds_cache(sources, tool_case, tmp_path):
    facade, embedding, cache = wired(sources, tool_case, tmp_path)
    request = {"query": "content", "max_candidates": 2}
    assert (await facade.discover(request, tool_case.ctx))["kind"] == "ok"
    embedding.binding = replace(
        embedding.binding,
        model_ref=embedding.binding.model_ref.model_copy(
            update={"version": "2", "content_hash": "c" * 64}
        ),
    )
    assert (await facade.discover(request, tool_case.ctx))["kind"] == "ok"
    assert [len(batch) for batch in embedding.requests] == [2, 2]
    with sqlite3.connect(cache.path) as db:
        assert db.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0] == 1


async def test_disabled_flags_categories_filter_before_embedding(sources, tool_case, tmp_path):
    spec = {
        **sources[-1],
        "id": "disabled-tool",
        "feature_flag": "local_files",
        "description": "HIDDEN FLAG DESCRIPTION",
    }
    tool_case.registry.register(
        spec,
        expected_revision=tool_case.registry.revision,
        binding=AdapterBinding(
            Ref.model_validate(spec["provider_ref"]),
            frozenset({"sql-component-test"}),
            implemented=True,
        ),
    )
    facade, embedding, _ = wired(sources, tool_case, tmp_path)
    result = await facade.discover({"query": "content", "max_candidates": 2}, tool_case.ctx)
    assert result["kind"] == "ok" and len(result["payload"]["tools"]) == 1
    assert "HIDDEN FLAG" not in str(embedding.requests)
    missing = await facade.discover(
        {"query": "content", "categories": ["forbidden"], "max_candidates": 2}, tool_case.ctx
    )
    assert missing["failure"]["code"] == "capability_gap" and len(embedding.requests) == 1


@pytest.mark.parametrize("phase", ["read", "replace"])
async def test_current_sql_binding_revoked_during_index_wait(sources, tool_case, tmp_path, phase):
    facade, embedding, cache = wired(sources, tool_case, tmp_path)
    original = getattr(cache, phase)

    async def revoke(*args):
        result = await original(*args)
        await sources[0].revoke(
            tool_case.ctx,
            meta("revoke-during-index", 1),
            authenticated_service=tool_case.domain[0].platform,
        )
        return result

    setattr(cache, phase, revoke)
    result = await facade.discover({"query": "content", "max_candidates": 2}, tool_case.ctx)
    assert result["kind"] != "ok" and "payload" not in result
    assert len(embedding.requests) == (0 if phase == "read" else 1)


async def test_deadline_and_async_cancel_bound_sql_authorized_wait(sources, tool_case):
    embedding = NumericalEmbedding()
    entered = asyncio.Event()

    async def blocked(*args):
        entered.set()
        await asyncio.Event().wait()

    embedding.embed = blocked
    retriever = ToolRetriever(tool_case.registry, sources[0], embeddings=embedding)
    short = tool_case.ctx.model_copy(
        update={"deadline": (datetime.now(UTC) + timedelta(seconds=5)).isoformat()}
    )
    # Valid SQL authorization is consumed before the controlled blocked provider.
    with pytest.raises(DomainError) as error:
        await retriever.discover("content", [], 1, short)
    assert error.value.failure.code == "deadline_exceeded"
    entered.clear()
    task = asyncio.create_task(retriever.discover("content", [], 1, tool_case.ctx))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not embedding.requests
