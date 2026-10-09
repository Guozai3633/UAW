"""Explicit embedding boundary. Numerical fixtures never represent semantic quality."""

import hashlib
import math
from dataclasses import dataclass
from typing import Protocol

from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.schema import validate_contract
from uaw.tool.errors import fail

TEXT_VERSION = "tool-projection-json-v1"
MAX_DIMENSIONS = 4096


@dataclass(frozen=True)
class EmbeddingBinding:
    provider_ref: Ref
    model_ref: Ref
    dimensions: int
    text_version: str = TEXT_VERSION

    def validate(self) -> None:
        for ref in (self.provider_ref, self.model_ref):
            validate_contract("Ref", ref.wire())
            if not ref.version or not ref.content_hash or ref.location or ref.access_scope:
                raise ValueError(
                    "Embedding refs require fixed versions/hashes without location/scope"
                )
        if self.provider_ref.kind != "provider" or self.model_ref.kind != "configuration":
            raise ValueError("Expected embedding provider and model configuration refs")
        if type(self.dimensions) is not int or not 1 <= self.dimensions <= MAX_DIMENSIONS:
            raise ValueError("Embedding dimension out of bounds")
        if self.text_version != TEXT_VERSION:
            raise ValueError("Unsupported embedding text version")


@dataclass(frozen=True)
class EmbeddingBatch:
    binding: EmbeddingBinding
    text_hashes: tuple[str, ...]
    vectors: tuple[tuple[float, ...], ...]


class ToolEmbeddingPort(Protocol):
    """Trusted adapter resolves current admin binding; never changes the user model.

    Texts are data, not instructions. Adapter checks identity, its own billing and
    cancellation. current() verifies availability/revocation against real sources.
    """

    async def current(self, ctx: TrustedExecutionContext) -> EmbeddingBinding: ...

    async def embed(
        self, texts: tuple[str, ...], ctx: TrustedExecutionContext
    ) -> EmbeddingBatch: ...


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def vector(values: object, dimensions: int) -> tuple[float, ...]:
    if type(values) is not tuple or len(values) != dimensions:
        raise ValueError("Embedding vector dimension/type differs")
    if any(type(v) not in (float, int) or not math.isfinite(v) for v in values):
        raise ValueError("Embedding coordinates must be finite numbers")
    result = tuple(float(v) for v in values)
    norm = math.hypot(*result)
    if not math.isfinite(norm) or norm == 0:
        raise ValueError("Embedding norm must be finite and nonzero")
    return result


def validate_batch(
    batch: EmbeddingBatch, binding: EmbeddingBinding, texts: tuple[str, ...]
) -> tuple[tuple[float, ...], ...]:
    try:
        if type(batch) is not EmbeddingBatch or batch.binding != binding:
            raise ValueError("Embedding provider/model binding changed")
        binding.validate()
        if batch.text_hashes != tuple(text_hash(t) for t in texts):
            raise ValueError("Embedding text hashes differ from actual input")
        if type(batch.vectors) is not tuple or len(batch.vectors) != len(texts):
            raise ValueError("Embedding batch count differs")
        return tuple(vector(v, binding.dimensions) for v in batch.vectors)
    except (ValueError, TypeError, OverflowError) as exc:
        raise fail(
            "embedding_invalid",
            "Invalid fixed embedding response",
            phase="retrieval",
            category="dependency",
            status=503,
        ) from exc
