"""Bounded, closed JSON Schema subset. No remote retrieval or semantic rewriting."""

import hashlib
import json
import math
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from uaw.tool.errors import fail

MAX_BYTES = 65536
MAX_DEPTH = 24
MAX_NODES = 4096
RESERVED = frozenset(
    {
        "owner",
        "approved",
        "principal",
        "principal_id",
        "scope",
        "supplied_context",
        "execution",
        "approval_ref",
        "attempt_id",
        "effect",
        "capability_policy_ref",
        "model_policy_ref",
    }
)


def canonical(value: Any) -> bytes:
    """Preserve strings/numbers/null/omissions; only sort JSON object keys."""
    count = 0
    text_bytes = 0

    def visit(item: Any, depth: int) -> None:
        nonlocal count, text_bytes
        count += 1
        if count > MAX_NODES or depth > MAX_DEPTH:
            raise ValueError("JSON exceeds structural limits")
        if type(item) is dict:
            for key, child in item.items():
                if type(key) is not str:
                    raise ValueError("JSON object keys must be strings")
                visit(key, depth + 1)
                visit(child, depth + 1)
        elif type(item) is list:
            for child in item:
                visit(child, depth + 1)
        elif type(item) is str:
            if len(item) > MAX_BYTES:
                raise ValueError("JSON exceeds string limit")
            text_bytes += len(item.encode("utf-8"))
            if text_bytes > MAX_BYTES:
                raise ValueError("JSON exceeds cumulative string limit")
        elif item is not None and type(item) not in (str, bool, int, float):
            raise ValueError("Only JSON values are accepted")
        elif type(item) is float and not math.isfinite(item):
            raise ValueError("JSON numbers must be finite")

    visit(value, 0)
    result = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    if len(result) > MAX_BYTES:
        raise ValueError("JSON exceeds byte limit")
    return result


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def compile_schema(schema: dict[str, Any], *, arguments: bool = False) -> Draft202012Validator:
    """Reject unsupported shapes rather than silently widening a registered contract.

    Supports acyclic local JSON pointers into $defs. Regex/composition/dynamic refs
    are deliberately unavailable in this first small catalogue.
    """
    try:
        canonical(schema)
        Draft202012Validator.check_schema(schema)
        allowed = {
            "$schema",
            "$defs",
            "$ref",
            "type",
            "title",
            "description",
            "default",
            "examples",
            "properties",
            "required",
            "additionalProperties",
            "items",
            "minItems",
            "maxItems",
            "minLength",
            "maxLength",
            "minimum",
            "maximum",
            "exclusiveMinimum",
            "exclusiveMaximum",
            "multipleOf",
            "enum",
            "const",
            "format",
        }
        checker = FormatChecker()

        expanded_nodes = 0

        def check(node: Any, active: tuple[str, ...], depth: int) -> None:
            nonlocal expanded_nodes
            expanded_nodes += 1
            if (
                expanded_nodes > MAX_NODES
                or depth > MAX_DEPTH
                or not isinstance(node, dict)
                or set(node) - allowed
            ):
                raise ValueError("Unsupported schema or excessive reference depth")
            for child in node.get("$defs", {}).values():
                check(child, active, depth + 1)
            if (
                "$schema" in node
                and node["$schema"] != "https://json-schema.org/draft/2020-12/schema"
            ):
                raise ValueError("Only JSON Schema 2020-12 is supported")
            if "$ref" in node:
                ref = node["$ref"]
                if not ref.startswith("#/$defs/") or ref in active:
                    raise ValueError("Only acyclic local $defs references are supported")
                target = schema
                for part in ref[2:].split("/"):
                    target = target[part.replace("~1", "/").replace("~0", "~")]
                check(target, (*active, ref), depth + 1)
                if set(node) - {"$ref", "title", "description"}:
                    raise ValueError("Reference siblings are unsupported")
                return
            kind = node.get("type")
            if kind not in ("object", "array", "string", "integer", "number", "boolean", "null"):
                raise ValueError("Explicit single type required")
            if kind == "object":
                if node.get("additionalProperties") is not False:
                    raise ValueError("Every object must be closed")
                for child in node.get("properties", {}).values():
                    check(child, active, depth + 1)
            if kind == "array":
                if not 0 <= node.get("maxItems", -1) <= 256:
                    raise ValueError("Arrays must have a bounded maxItems")
                check(node.get("items"), active, depth + 1)
            if "format" in node and node["format"] not in checker.checkers:
                raise ValueError("Unknown format")

        check(schema, (), 0)
        if arguments:
            if schema.get("type") != "object" or set(schema.get("properties", {})) & RESERVED:
                raise ValueError("Arguments must be a closed object without trusted fields")
        return Draft202012Validator(schema, format_checker=checker)
    except (ValueError, KeyError, TypeError, SchemaError, RecursionError, OverflowError) as exc:
        raise fail(
            "registration_invalid", "Tool schema is invalid or unsupported", phase="registration"
        ) from exc
