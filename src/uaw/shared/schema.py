"""Validate wire data against the existing contract rather than a second schema."""

import asyncio
import hashlib
import json
import math
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import lru_cache
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


@dataclass
class ShapeValidationScope:
    """Pure successful schema checks only: bounded digests, no input or permission."""

    owner: asyncio.Task[Any]
    entries: dict[tuple[str, bytes], Draft202012Validator] = field(default_factory=dict)
    hits: int = 0
    misses: int = 0


_shape_scope: ContextVar[ShapeValidationScope | None] = ContextVar(
    "uaw_pure_shape_validation", default=None
)


@asynccontextmanager
async def contract_validation_scope() -> AsyncIterator[ShapeValidationScope]:
    """One owning metadata pass; nested calls share, child/thread/later calls do not.

    This skips only repeated pure schema work on exact JSON content and the same
    packaged validator. Domain predicates, SQL, signatures and external checks
    are unchanged. No model/tool/file/user wait belongs inside this scope.
    """
    task = asyncio.current_task()
    if task is None:
        raise RuntimeError("Schema scopes require an owning task")
    active = _shape_scope.get()
    if active is not None and active.owner is task:
        yield active
        return
    scope = ShapeValidationScope(task)
    token = _shape_scope.set(scope)
    try:
        yield scope
    finally:
        scope.entries.clear()
        _shape_scope.reset(token)


def _shape_bytes(value: Any) -> bytes | None:
    # JSON encoders conflate tuple/list and non-string/string dict keys. Only
    # exact JSON builtin types can participate; custom/subclass inputs bypass.
    pending = [(value, 0)]
    visited = 0
    while pending:
        item, depth = pending.pop()
        visited += 1
        if visited > 2048 or depth > 32:
            return None
        kind = type(item)
        if kind is dict:
            if len(item) > 2048 or any(type(k) is not str for k in item):
                return None
            pending.extend((v, depth + 1) for v in item.values())
        elif kind is list:
            if len(item) > 2048:
                return None
            pending.extend((v, depth + 1) for v in item)
        elif kind is str:
            if len(item) > 16384:
                return None
        elif kind not in (int, float, bool, type(None)):
            return None
    try:
        encoded = json.dumps(
            value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
    except ValueError, TypeError, UnicodeError:
        return None
    return encoded if len(encoded) <= 16384 else None


class ContractViolation(ValueError):
    def __init__(self, name: str, paths: tuple[str, ...]) -> None:
        self.name = name
        self.paths = paths
        # Validation errors may contain credentials/user content. Only retain field paths.
        super().__init__(f"{name}: invalid fields at {', '.join(paths)}")


@lru_cache(maxsize=1)
def contract_schema() -> dict[str, Any]:
    resource = files("uaw.resources").joinpath("uaw.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


@lru_cache(maxsize=128)
def validator(name: str) -> Draft202012Validator:
    schema = contract_schema()
    if name not in schema["$defs"]:
        raise KeyError(f"Unknown contract type: {name}")
    checker = FormatChecker()
    if "date-time" not in checker.checkers or "uri" not in checker.checkers:
        raise RuntimeError("Required contract format validators are not installed")
    return Draft202012Validator(
        {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": f"#/$defs/{name}"},
        format_checker=checker,
    )


def validate_contract(name: str, value: Any) -> None:
    actual = validator(name)
    scope = _shape_scope.get()
    try:
        task = asyncio.current_task()
    except RuntimeError:
        task = None
    if scope is not None and scope.owner is not task:
        scope = None
    encoded = _shape_bytes(value) if scope is not None else None
    key = (name, hashlib.sha256(encoded).digest()) if encoded is not None else None
    if scope is not None and key is not None and scope.entries.get(key) is actual:
        scope.hits += 1
        return
    if scope is not None:
        scope.misses += 1
    errors = sorted(actual.iter_errors(value), key=lambda e: str(list(e.path)))
    if errors:
        paths = tuple("/" + "/".join(map(str, e.path)) for e in errors[:16])
        raise ContractViolation(name, paths)
    if (
        scope is not None
        and key is not None
        and len(scope.entries) < 256
        and _shape_bytes(value) == encoded
    ):
        # Retain the validator object as well as the digest: eviction/replacement
        # cannot reuse an object id to create a false schema hit. No raw values.
        scope.entries[key] = actual


def parse_json(data: bytes | str) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"Non-JSON numeric constant: {value}")

    def unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON object key")
            result[key] = value
        return result

    def finite_float(value: str) -> float:
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("JSON number exceeds the supported finite range")
        return parsed

    return json.loads(
        data,
        parse_constant=reject_constant,
        parse_float=finite_float,
        object_pairs_hook=unique_keys,
    )
