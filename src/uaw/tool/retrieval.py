"""Permission-first bounded lexical/vector retrieval; only the model chooses tools."""

import asyncio
import json
import math
from datetime import UTC, datetime
from typing import Literal, cast

from uaw.shared.contracts import JsonObject, TrustedExecutionContext
from uaw.shared.errors import DomainError
from uaw.shared.schema import validate_contract
from uaw.tool.discovery import check_access, require_entry
from uaw.tool.embedding import EmbeddingBinding, ToolEmbeddingPort, validate_batch
from uaw.tool.errors import fail
from uaw.tool.ports import ToolAccessPort
from uaw.tool.registry import RegistryEntry, ToolRegistry
from uaw.tool.schema import canonical

MAX_QUERY_BYTES = 8192
MAX_ENTRIES = 128


def projection(entry: RegistryEntry) -> str:
    spec = entry.spec()
    # Exact metadata projection; descriptions remain untrusted tool documentation.
    return canonical(
        {"id": spec["id"], "description": spec["description"], "categories": spec["categories"]}
    ).decode("utf-8")


def lexical(query: str, entries: tuple[RegistryEntry, ...]) -> list[tuple[int, float]]:
    tokens = query.casefold().split()
    scored = []
    for i, entry in enumerate(entries):
        spec = entry.spec()
        text = (spec["id"] + " " + spec["description"]).casefold()
        score = (
            1.0
            if query.casefold() == spec["id"].casefold()
            else sum(t in text for t in tokens) / max(len(tokens), 1)
        )
        if not tokens or score > 0:
            scored.append((i, score))
    return scored


def cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    na, nb = math.hypot(*a), math.hypot(*b)
    return max(-1.0, min(1.0, math.fsum((x / na) * (y / nb) for x, y in zip(a, b, strict=True))))


class ToolRetriever:
    def __init__(
        self,
        registry: ToolRegistry,
        access: ToolAccessPort,
        *,
        mode: Literal["lexical-only", "semantic-required"] = "semantic-required",
        embeddings: ToolEmbeddingPort | None = None,
    ) -> None:
        if mode not in {"lexical-only", "semantic-required"}:
            raise ValueError("Explicit lexical-only or semantic-required mode required")
        self.registry, self.access, self.mode, self.embeddings = registry, access, mode, embeddings

    async def discover(
        self, query: str, categories: list[str], max_candidates: int, ctx: TrustedExecutionContext
    ) -> JsonObject:
        validate_contract(
            "ToolToolsDiscoverInput",
            {"query": query, "categories": categories, "max_candidates": max_candidates},
        )
        if type(query) is not str or len(query.encode("utf-8")) > MAX_QUERY_BYTES:
            raise fail(
                "invalid_arguments", "Retrieval query exceeds UTF-8 limit", phase="retrieval"
            )
        if type(max_candidates) is not int:
            raise ValueError("Strict integer candidate limit required")
        frozen = canonical(ctx.wire())
        deadline = datetime.fromisoformat(ctx.deadline.replace("Z", "+00:00"))
        remaining = (deadline - datetime.now(UTC)).total_seconds()
        if remaining <= 0:
            raise fail(
                "deadline_exceeded",
                "Retrieval deadline expired",
                phase="retrieval",
                category="timeout",
            )
        try:
            async with asyncio.timeout(remaining):
                return await self._discover(query, tuple(categories), max_candidates, ctx, frozen)
        except TimeoutError as exc:
            code = "deadline_exceeded" if datetime.now(UTC) >= deadline else "retrieval_interrupted"
            raise fail(
                code,
                "Retrieval wait unresolved; no candidates returned",
                phase="retrieval",
                category="timeout",
                status=503,
            ) from exc

    async def _discover(
        self,
        query: str,
        categories: tuple[str, ...],
        limit: int,
        ctx: TrustedExecutionContext,
        frozen: bytes,
    ) -> JsonObject:
        revision, entries = self.registry.snapshot()
        if len(entries) > MAX_ENTRIES:
            raise fail("registry_limit", "Retrieval catalogue exceeds 128 tools", phase="retrieval")

        async def allowed() -> tuple[RegistryEntry, ...]:
            access = await self.access.snapshot(ctx)
            check_access(access, ctx)
            if canonical(ctx.wire()) != frozen or self.registry.snapshot() != (revision, entries):
                raise fail(
                    "registry_changed",
                    "Fixed retrieval sources changed",
                    phase="retrieval",
                    category="conflict",
                    status=412,
                )
            result = []
            for entry in entries:
                try:
                    require_entry(entry, access)
                except DomainError:
                    continue
                if not categories or set(entry.spec()["categories"]) & set(categories):
                    result.append(entry)
            return tuple(sorted(result, key=lambda e: (e.spec()["id"], e.spec()["version"])))

        eligible = await allowed()
        if not eligible:
            raise fail(
                "capability_gap",
                "No currently available tools",
                phase="retrieval",
                category="dependency",
                status=503,
            )

        async def guard() -> None:
            if await allowed() != eligible:
                raise fail(
                    "access_changed",
                    "Tool access changed during retrieval",
                    phase="retrieval",
                    category="authorization",
                    status=403,
                )

        def order(items: list[tuple[int, float]]) -> list[tuple[int, float]]:
            return sorted(
                items,
                key=lambda item: (
                    -item[1],
                    eligible[item[0]].spec()["id"],
                    eligible[item[0]].spec()["version"],
                ),
            )

        words = order(lexical(query, eligible))
        scores = dict(words)
        if self.mode == "semantic-required":
            if self.embeddings is None:
                raise fail(
                    "dependency_unavailable",
                    "Actual embedding adapter is not wired",
                    phase="retrieval",
                    category="dependency",
                    status=503,
                )
            binding = await self.embeddings.current(ctx)
            self._binding(binding)
            await guard()
            texts = tuple(projection(e) for e in eligible)
            batch = await self.embeddings.embed((query, *texts), ctx)
            await guard()
            vectors = validate_batch(batch, binding, (query, *texts))
            current = await self.embeddings.current(ctx)
            self._binding(current)
            await guard()
            if current != binding:
                raise fail(
                    "embedding_changed",
                    "Embedding configuration changed",
                    phase="retrieval",
                    category="conflict",
                    status=412,
                )
            semantic = order(
                [
                    (i, cosine(vectors[0], v))
                    for i, v in enumerate(vectors[1:])
                    if cosine(vectors[0], v) > 0
                ]
            )
            # Reciprocal rank fusion, k=60; deterministic tie order and score in [0,1].
            scores = {}
            for ranking in (words, semantic):
                for rank, (i, _) in enumerate(ranking, 1):
                    scores[i] = scores.get(i, 0.0) + 61.0 / (2 * (60 + rank))
        ranked = order(list(scores.items()))[:limit]
        await guard()
        if not ranked:
            raise fail(
                "capability_gap",
                "No available tool matches retrieval",
                phase="retrieval",
                category="dependency",
                status=503,
            )
        tools = []
        for i, score in ranked:
            entry = eligible[i]
            spec = entry.spec()
            tools.append(
                {
                    "tool_ref": self.registry.reference(entry),
                    "description": spec["description"],
                    "input_schema": spec["input_schema"],
                    "effect": spec["effect"],
                    "score": score,
                }
            )
        result = cast(JsonObject, {"tools": tools, "agents": [], "registry_revision": revision})
        validate_contract("DiscoveryResult", result)
        return json.loads(canonical(result))  # type: ignore[no-any-return]

    @staticmethod
    def _binding(binding: EmbeddingBinding) -> None:
        try:
            if type(binding) is not EmbeddingBinding:
                raise ValueError("Expected explicit binding")
            binding.validate()
        except (ValueError, TypeError) as exc:
            raise fail(
                "embedding_invalid",
                "Invalid current embedding binding",
                phase="retrieval",
                category="dependency",
                status=503,
            ) from exc
