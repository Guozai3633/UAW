"""Controlled known numerical embeddings test recall/fusion, not semantic quality."""

from copy import deepcopy
from dataclasses import replace

import pytest

from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.tool.embedding import EmbeddingBatch, EmbeddingBinding, text_hash
from uaw.tool.facade import ToolFacade
from uaw.tool.registry import ToolRegistry
from uaw.tool.retrieval import ToolRetriever


class NumericalEmbedding:
    def __init__(self, *, vectors=None, change=None):
        self.binding = EmbeddingBinding(
            Ref(kind="provider", id="controlled-embedding", version="1", content_hash="a" * 64),
            Ref(kind="configuration", id="controlled-model", version="1", content_hash="b" * 64),
            2,
        )
        self.requests = []
        self.current_calls = 0
        self.vectors = vectors
        self.change = change

    async def current(self, ctx):
        self.current_calls += 1
        return self.binding

    async def embed(self, texts, ctx):
        self.requests.append(texts)
        batch = EmbeddingBatch(
            self.binding,
            tuple(text_hash(t) for t in texts),
            self.vectors or tuple((1.0, 0.0) for _ in texts),
        )
        if self.change:
            await self.change()
        return batch


async def test_explicit_modes_and_default_small_catalogue(registry, access, ctx):
    old = await ToolFacade(registry, access).discover(
        {"query": "content.read", "max_candidates": 1}, ctx
    )
    lexical = ToolRetriever(registry, access, mode="lexical-only")
    assert await lexical.discover("content.read", [], 1, ctx) == old["payload"]
    required = ToolFacade(registry, access, retriever=ToolRetriever(registry, access))
    assert (await required.discover({"query": "content.read", "max_candidates": 1}, ctx))[
        "failure"
    ]["code"] == "dependency_unavailable"
    with pytest.raises(ValueError):
        ToolRetriever(registry, access, mode="automatic-fallback")


async def test_vector_recall_can_return_nonlexical_candidate_without_execution(
    registry, access, ctx
):
    embedding = NumericalEmbedding()
    before = ctx.wire()
    retriever = ToolRetriever(registry, access, embeddings=embedding)
    result = await retriever.discover("unmatchedzyx", [], 1, ctx)
    assert result["tools"][0]["tool_ref"]["id"] == "content.read"
    assert result["tools"][0]["score"] == 0.5
    assert result["registry_revision"] == 1 and result["agents"] == []
    assert ctx.wire() == before and len(embedding.requests) == 1
    assert len(embedding.requests[0]) == 2


@pytest.mark.parametrize(
    "change",
    [
        {"role_categories": frozenset()},
        {"allowed_capabilities": frozenset()},
        {"denied_capabilities": frozenset({"content.read"})},
        {"active_provider_refs": ()},
        {"environment": "wrong"},
    ],
)
async def test_current_filter_precedes_any_embedding(registry, access, ctx, change):
    access.changes = change
    embedding = NumericalEmbedding()
    with pytest.raises(DomainError) as error:
        await ToolRetriever(registry, access, embeddings=embedding).discover("supplied", [], 5, ctx)
    assert error.value.failure.code == "capability_gap"
    assert not embedding.requests and embedding.current_calls == 0


async def test_hidden_spec_description_never_sent_to_embedding(spec, binding, access, ctx):
    registry = ToolRegistry()
    registry.register(spec, expected_revision=0, binding=binding)
    hidden = {
        **deepcopy(spec),
        "id": "private.secret",
        "categories": ["private"],
        "description": "PRIVATE DESCRIPTION",
    }
    registry.register(hidden, expected_revision=1, binding=binding)
    embedding = NumericalEmbedding()
    result = await ToolRetriever(registry, access, embeddings=embedding).discover(
        "content", [], 5, ctx
    )
    assert len(result["tools"]) == 1
    assert "PRIVATE" not in str(embedding.requests) and "private.secret" not in str(result)


@pytest.mark.parametrize(
    "vectors",
    [
        ((1.0, 0.0), (float("nan"), 0.0)),
        ((1.0, 0.0), (float("inf"), 0.0)),
        ((1.0, 0.0), (True, 0.0)),
        ((1.0, 0.0), (0.0, 0.0)),
        ((1.0, 0.0), (1.0,)),
        ((1.0, 0.0),),
    ],
)
async def test_bad_numeric_vectors_are_unavailable_not_lexical_fallback(
    registry, access, ctx, vectors
):
    embedding = NumericalEmbedding(vectors=vectors)
    facade = ToolFacade(
        registry, access, retriever=ToolRetriever(registry, access, embeddings=embedding)
    )
    result = await facade.discover({"query": "content.read", "max_candidates": 1}, ctx)
    assert result["failure"]["code"] == "embedding_invalid" and "payload" not in result


@pytest.mark.parametrize("change", ["role", "provider", "cancel", "registry", "embedding"])
async def test_wait_revalidates_sources_before_candidates(
    registry, access, ctx, spec, binding, change
):
    async def mutate():
        if change == "role":
            access.changes = {"role_categories": frozenset()}
        elif change == "provider":
            access.changes = {"active_provider_refs": ()}
        elif change == "cancel":
            access.changes = {"cancelled": True}
        elif change == "registry":
            registry.register({**spec, "version": "v2"}, expected_revision=1, binding=binding)
        else:
            embedding.binding = replace(
                embedding.binding,
                model_ref=Ref(
                    kind="configuration", id="new-model", version="2", content_hash="c" * 64
                ),
            )

    embedding = NumericalEmbedding(change=mutate)
    with pytest.raises(DomainError) as error:
        await ToolRetriever(registry, access, embeddings=embedding).discover("content", [], 1, ctx)
    expected = {
        "role": "access_changed",
        "provider": "access_changed",
        "cancel": "cancelled",
        "registry": "registry_changed",
        "embedding": "embedding_changed",
    }
    assert error.value.failure.code == expected[change]


async def test_stable_fusion_and_candidate_limit(spec, binding, access, ctx):
    registry = ToolRegistry()
    for i in reversed(range(4)):
        registry.register(
            {**spec, "id": f"content.tool{i}"}, expected_revision=registry.revision, binding=binding
        )
    embedding = NumericalEmbedding()
    retriever = ToolRetriever(registry, access, embeddings=embedding)
    found = await retriever.discover("content", [], 2, ctx)
    assert [c["tool_ref"]["id"] for c in found["tools"]] == ["content.tool0", "content.tool1"]
    assert found == await retriever.discover("content", [], 2, ctx)
    assert all(0 < c["score"] <= 1 for c in found["tools"])


@pytest.mark.parametrize("change", ["hash", "provider", "dimension"])
async def test_embedding_observation_requires_fixed_binding_and_actual_text_hashes(
    registry, access, ctx, change
):
    embedding = NumericalEmbedding()
    original = embedding.embed

    async def wrong(texts, ctx):
        batch = await original(texts, ctx)
        if change == "hash":
            return replace(batch, text_hashes=("f" * 64,) * len(texts))
        if change == "provider":
            return replace(
                batch,
                binding=replace(
                    batch.binding,
                    provider_ref=Ref(
                        kind="provider", id="foreign", version="1", content_hash="c" * 64
                    ),
                ),
            )
        return replace(batch, binding=replace(batch.binding, dimensions=3))

    embedding.embed = wrong
    with pytest.raises(DomainError) as error:
        await ToolRetriever(registry, access, embeddings=embedding).discover("content", [], 1, ctx)
    assert error.value.failure.code == "embedding_invalid"


async def test_query_limit_rejected_before_access_or_embedding(registry, access, ctx):
    embedding = NumericalEmbedding()
    with pytest.raises(DomainError):
        await ToolRetriever(registry, access, embeddings=embedding).discover(
            "文" * 2731, [], 1, ctx
        )
    assert access.calls == 0 and not embedding.requests
