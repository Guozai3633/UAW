"""Optional process-local cache of pure bytes, never authority or source objects.

Limits account for payload bytes and the two ASCII digests per entry. Python
container overhead is additionally bounded by max_entries; this is not an RSS
limit. Keys retain digests only, and values are immutable bytes. Callers must
complete live validation before lookup and retain their final rechecks.
"""

from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from collections.abc import Iterable
from dataclasses import dataclass
from threading import Lock

from uaw.context.contracts import CompositionBinding, ModelWindow, Reading
from uaw.shared.contracts import Ref, TrustedExecutionContext


@dataclass(frozen=True)
class CacheKey:
    owner: str
    digest: str


@dataclass(frozen=True)
class CacheStats:
    entries: int
    size_bytes: int
    hits: int
    misses: int
    evictions: int


class PureComputationCache:
    """LRU of immutable bytes. Either zero limit disables storage and lookup.

    No persistence, TTL-based authorization, negative permission cache, or
    in-flight merging. A shared instance still partitions keys by principal.
    """

    def __init__(self, *, max_entries: int = 0, max_bytes: int = 0) -> None:
        if any(type(n) is not int or n < 0 for n in (max_entries, max_bytes)):
            raise ValueError("Cache limits must be nonnegative integers")
        self._max_entries, self._max_bytes = max_entries, max_bytes
        self._entries: OrderedDict[CacheKey, bytes] = OrderedDict()
        self._size = self._hits = self._misses = self._evictions = 0
        self._lock = Lock()

    @property
    def enabled(self) -> bool:
        return self._max_entries > 0 and self._max_bytes > 0

    @staticmethod
    def _cost(key: CacheKey, value: bytes) -> int:
        return len(key.owner.encode("utf-8")) + len(key.digest.encode("utf-8")) + len(value)

    def get(self, key: CacheKey) -> bytes | None:
        with self._lock:
            value = self._entries.get(key) if self.enabled else None
            if value is None:
                self._misses += 1
            else:
                self._hits += 1
                self._entries.move_to_end(key)
            return value

    def put(self, key: CacheKey, value: bytes) -> None:
        if type(value) is not bytes:
            raise TypeError("Only immutable pure-computation bytes may be cached")
        cost = self._cost(key, value)
        with self._lock:
            if not self.enabled or cost > self._max_bytes:
                return
            previous = self._entries.pop(key, None)
            if previous is not None:
                self._size -= self._cost(key, previous)
            while self._entries and (
                len(self._entries) >= self._max_entries or self._size + cost > self._max_bytes
            ):
                removed, payload = self._entries.popitem(last=False)
                self._size -= self._cost(removed, payload)
                self._evictions += 1
            self._entries[key] = value
            self._size += cost

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._size = 0

    @property
    def stats(self) -> CacheStats:
        with self._lock:
            return CacheStats(
                len(self._entries), self._size, self._hits, self._misses, self._evictions
            )


def reading_key(reading: Reading) -> dict[str, object]:
    return {
        "ref": reading.ref.wire(),
        "text": reading.text,
        "kind": reading.kind,
        "trust": reading.trust,
        "required": reading.required,
        "requirement_ids": reading.requirement_ids,
    }


def window_key(window: ModelWindow) -> dict[str, object]:
    return {
        "policy_ref": window.policy_ref.wire(),
        "context_limit": window.context_limit,
        "max_output_tokens": window.max_output_tokens,
        "serialization_reserve": window.serialization_reserve,
    }


def binding_key(binding: CompositionBinding) -> dict[str, object]:
    # Only hashed key material, never a cached CompositionBinding/permission result.
    return {
        "epoch": binding.epoch,
        "rules": binding.rules.wire(),
        "capability_ref": binding.capability_ref.wire(),
        "preserve": binding.preserve.wire(),
        "dependency_refs": [ref.wire() for ref in binding.dependency_refs],
        "request": binding.request.wire() if binding.request is not None else None,
    }


def cache_enabled(cache: PureComputationCache | None) -> bool:
    try:
        return cache is not None and cache.enabled is True
    except Exception:
        return False


def make_key(
    cache: PureComputationCache | None,
    ctx: TrustedExecutionContext,
    *,
    algorithm: str,
    inputs: object,
    readings: Iterable[Reading],
    pins: Iterable[Ref] = (),
) -> CacheKey | None:
    """Fail open to computation only. No digest-less source can produce a hit.

    Stable security identity includes the full principal (including auth session),
    scope, Run, fixed model/permission/budget refs and agent/node. Operation/trace/
    attempt IDs and deadlines are not pure-input identity; their checks still run.
    No sensitive original key text is retained by the cache.
    """
    try:
        if not cache_enabled(cache) or not algorithm:
            return None
        actual = [*(reading.ref for reading in readings), *pins]
        if not actual or any(not ref.content_hash for ref in actual):
            return None
        security = ctx.wire()
        for name in ("operation_id", "trace_id", "attempt_id", "deadline"):
            security.pop(name, None)
        encoded = json.dumps(
            {
                "key_version": "ms-c4-1",
                "security": security,
                "algorithm": algorithm,
                "inputs": inputs,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        owner = hashlib.sha256(
            json.dumps([ctx.principal.kind, ctx.principal.id]).encode("utf-8")
        ).hexdigest()
        return CacheKey(owner, hashlib.sha256(encoded).hexdigest())
    except Exception:
        return None


def lookup(cache: PureComputationCache | None, key: CacheKey | None) -> bytes | None:
    try:
        value = cache.get(key) if cache is not None and key is not None else None
        return value if type(value) is bytes else None
    except Exception:
        return None


def remember(cache: PureComputationCache | None, key: CacheKey | None, value: bytes) -> None:
    try:
        if cache is not None and key is not None:
            cache.put(key, value)
    except Exception:
        # Only cache writes are best effort. Never wrap live checks or computation.
        pass
