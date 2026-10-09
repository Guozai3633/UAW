"""Bounded inspection of exact supplied JSON, without repair or data claims."""

import hashlib
import json
from decimal import Decimal, DecimalException
from typing import Any

from uaw.shared.contracts import JsonObject, Principal, Ref
from uaw.tool.providers.local import LocalExecutor, LocalVerifier, local_estimates, local_spec
from uaw.tool.receipt_store import ToolResponseStore

MAX_JSON_BYTES = 16384
MAX_JSON_DEPTH = 16
MAX_JSON_NODES = 1024
MAX_CONTAINER_ITEMS = 256
MAX_KEY_BYTES = 256
MAX_REQUIRED_KEYS = 64
ROOT_TYPES = ("object", "array", "string", "number", "boolean", "null")


def json_data_spec(provider_ref: Ref) -> JsonObject:
    keys: JsonObject = {
        "type": "array",
        "maxItems": MAX_CONTAINER_ITEMS,
        "items": {"type": "string", "maxLength": MAX_KEY_BYTES},
    }
    inputs: JsonObject = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "maxLength": MAX_JSON_BYTES},
            "required_keys": {**keys, "maxItems": MAX_REQUIRED_KEYS},
        },
        "required": ["text"],
        "additionalProperties": False,
    }
    outputs: JsonObject = {
        "type": "object",
        "properties": {
            "root_type": {"type": "string", "enum": list(ROOT_TYPES)},
            "count": {"type": "integer", "minimum": 0, "maximum": MAX_CONTAINER_ITEMS},
            "keys": keys,
            "missing_keys": {**keys, "maxItems": MAX_REQUIRED_KEYS},
            "nodes": {"type": "integer", "minimum": 1, "maximum": MAX_JSON_NODES},
            "depth": {"type": "integer", "minimum": 0, "maximum": MAX_JSON_DEPTH},
            "utf8_bytes": {"type": "integer", "minimum": 1, "maximum": MAX_JSON_BYTES},
            "sha256": {"type": "string", "minLength": 64, "maxLength": 64},
        },
        "required": [
            "root_type",
            "count",
            "keys",
            "missing_keys",
            "nodes",
            "depth",
            "utf8_bytes",
            "sha256",
        ],
        "additionalProperties": False,
    }
    return local_spec(
        "data.inspect_json",
        "Inspect supplied JSON structure and top-level keys",
        "data",
        provider_ref,
        inputs,
        outputs,
    )


def _number(text: str) -> Decimal:
    if len(text) > 128:
        raise ValueError("JSON number token too long")
    try:
        value = Decimal(text)
    except DecimalException as exc:
        raise ValueError("JSON number exceeds Decimal representation") from exc
    if not value.is_finite() or (not value.is_zero() and abs(value.adjusted()) > 128):
        raise ValueError("JSON number outside bounded finite range")
    return value


def _constant(text: str) -> Any:
    raise ValueError("Non-finite JSON numbers rejected")


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    if len(pairs) > MAX_CONTAINER_ITEMS:
        raise ValueError("Object exceeds key count")
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        if len(key.encode("utf-8")) > MAX_KEY_BYTES:
            raise ValueError("Object key too long")
        result[key] = value
    return result


def inspect_json(args: JsonObject) -> JsonObject:
    if type(args) is not dict or set(args) - {"text", "required_keys"} or "text" not in args:
        raise ValueError("Expected text and optional required_keys only")
    text = args["text"]
    if type(text) is not str:
        raise ValueError("Expected exact JSON text")
    encoded = text.encode("utf-8")
    if not 1 <= len(encoded) <= MAX_JSON_BYTES:
        raise ValueError("JSON text exceeds byte bounds")
    required = args.get("required_keys", [])
    if (
        type(required) is not list
        or len(required) > MAX_REQUIRED_KEYS
        or any(type(k) is not str or len(k.encode("utf-8")) > MAX_KEY_BYTES for k in required)
        or len(set(required)) != len(required)
    ):
        raise ValueError("Expected unique bounded required keys")
    # Bound parser nesting BEFORE json.loads allocates a recursive object tree.
    nesting, in_string, escaped = 0, False, False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "[{":
            nesting += 1
            if nesting > MAX_JSON_DEPTH:
                raise ValueError("JSON nesting too deep")
        elif char in "]}":
            nesting -= 1
    value = json.loads(
        text,
        object_pairs_hook=_object,
        parse_int=_number,
        parse_float=_number,
        parse_constant=_constant,
    )
    nodes, depth = 0, 0

    def visit(item: Any, level: int) -> None:
        nonlocal nodes, depth
        nodes += 1
        if nodes > MAX_JSON_NODES:
            raise ValueError("JSON node count exceeded")
        if isinstance(item, (dict, list)):
            depth = max(depth, level + 1)
            if len(item) > MAX_CONTAINER_ITEMS or depth > MAX_JSON_DEPTH:
                raise ValueError("JSON container bounds exceeded")
            if isinstance(item, dict):
                for key, child in item.items():
                    visit(key, level + 1)
                    visit(child, level + 1)
            else:
                for child in item:
                    visit(child, level + 1)
        elif type(item) is str:
            item.encode("utf-8")  # Reject lone surrogate escapes, never repair them.

    visit(value, 0)
    root_type = (
        "object"
        if isinstance(value, dict)
        else "array"
        if isinstance(value, list)
        else "string"
        if type(value) is str
        else "number"
        if isinstance(value, Decimal)
        else "boolean"
        if type(value) is bool
        else "null"
    )
    if "required_keys" in args and root_type != "object":
        raise ValueError("required_keys applies only to a top-level object")
    keys = sorted(value) if isinstance(value, dict) else []
    return {
        "root_type": root_type,
        "count": len(value) if isinstance(value, (dict, list)) else 1,
        "keys": keys,
        "missing_keys": [key for key in required if key not in keys],
        "nodes": nodes,
        "depth": depth,
        "utf8_bytes": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def json_data_estimates(currency: str = "USD") -> JsonObject:
    return local_estimates(currency)


class JsonDataExecutor(LocalExecutor):
    def __init__(
        self, source: ToolResponseStore, *, provider: Principal, currency: str = "USD"
    ) -> None:
        super().__init__(
            source,
            provider=provider,
            currency=currency,
            factory=json_data_spec,
            calculate=inspect_json,
        )


class JsonDataVerifier(LocalVerifier):
    def __init__(self, provider_ref: Ref) -> None:
        super().__init__(provider_ref, factory=json_data_spec, calculate=inspect_json)
