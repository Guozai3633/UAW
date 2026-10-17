"""Bounded strict offline JSON and exclusive immutable report publication."""

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


class EvaluationInputError(ValueError):
    """Safe diagnostic code; never stringify private source/answer contents."""


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in items:
        if key in result:
            raise EvaluationInputError("duplicate_key")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise EvaluationInputError("nonfinite_number")


def canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise EvaluationInputError("noncanonical_json") from exc


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_json(raw: bytes) -> Any:
    if len(raw) > 2 * 1024 * 1024:
        raise EvaluationInputError("json_record_too_large")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
        pending = [(value, 0)]
        while pending:
            node, depth = pending.pop()
            if depth > 48:
                raise EvaluationInputError("json_too_deep")
            if isinstance(node, dict):
                pending.extend((v, depth + 1) for v in node.values())
            elif isinstance(node, list):
                pending.extend((v, depth + 1) for v in node)
        canonical(value)
        return value
    except EvaluationInputError:
        raise
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise EvaluationInputError("invalid_json") from exc


def read_bounded(path: Path, *, limit: int) -> bytes:
    with path.open("rb") as handle:
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise EvaluationInputError("input_file_too_large")
    return raw


def publish_report(path: Path, report: Any) -> None:
    """Hard-link a fully flushed sibling temp file; existing files are never replaced."""
    data = canonical(report) + b"\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=".evaluation-", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
