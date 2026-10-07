"""Validate wire data against the existing contract rather than a second schema."""

import json
import math
from functools import lru_cache
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


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
    errors = sorted(validator(name).iter_errors(value), key=lambda e: str(list(e.path)))
    if errors:
        paths = tuple("/" + "/".join(map(str, e.path)) for e in errors[:16])
        raise ContractViolation(name, paths)


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
