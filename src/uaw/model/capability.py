"""Bounded schemas never resolve remote references or execute model-proposed actions."""

import json
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from uaw.shared.errors import reject


def bounded_schema(schema: dict[str, Any]) -> Draft202012Validator:
    if len(json.dumps(schema, allow_nan=False).encode()) > 65536:
        raise reject("model_schema_too_large", "Output schema exceeds the supported limit")
    pending: list[tuple[Any, int]] = [(schema, 0)]
    count = 0
    while pending:
        value, depth = pending.pop()
        count += 1
        if count > 4096 or depth > 24:
            raise reject("model_schema_too_complex", "Output schema exceeds the supported limit")
        if isinstance(value, dict):
            if any(key in value for key in ("$ref", "$dynamicRef", "$recursiveRef")):
                raise reject("model_schema_refs_unsupported", "Schema references are not enabled")
            if isinstance(value.get("pattern"), str) or "patternProperties" in value:
                raise reject("model_schema_patterns_unsupported", "Dynamic regex is not enabled")
            pending.extend((child, depth + 1) for child in value.values())
        elif isinstance(value, list):
            pending.extend((child, depth + 1) for child in value)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError:
        raise reject("model_schema_invalid", "Output schema is invalid") from None
    return Draft202012Validator(schema, format_checker=FormatChecker())
