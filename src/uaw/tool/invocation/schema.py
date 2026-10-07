"""Normalize against the exact registered schema without coercion or defaults."""

import json
from typing import Any

from uaw.shared.schema import validate_contract
from uaw.tool.errors import fail
from uaw.tool.registry import ToolRegistry
from uaw.tool.schema import RESERVED, canonical, compile_schema, digest


def normalize(request: dict[str, Any], registry: ToolRegistry) -> dict[str, Any]:
    try:
        # Bounds and JSON-native types are checked before general schema traversal.
        canonical(request)
        validate_contract("NormalizeCallRequest", request)
        if set(request["arguments"]) & RESERVED:
            raise ValueError("Trusted fields cannot be supplied as tool arguments")
    except (ValueError, RecursionError, OverflowError) as exc:
        raise fail(
            "invalid_arguments", "Tool call contains invalid or trusted fields", phase="normalize"
        ) from exc
    entry = registry.get(request["tool_ref"])
    validator = compile_schema(entry.spec()["input_schema"], arguments=True)
    if not validator.is_valid(request["arguments"]):
        raise fail(
            "invalid_arguments", "Arguments violate the fixed tool input schema", phase="normalize"
        )
    result = {
        "tool_ref": registry.reference(entry),
        "arguments": json.loads(canonical(request["arguments"])),
        "arguments_hash": digest(request["arguments"]),
        "action_id": request["action_id"],
    }
    validate_contract("ValidatedCall", result)
    return result
