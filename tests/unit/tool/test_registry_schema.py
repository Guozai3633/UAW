from copy import deepcopy
from dataclasses import replace

import pytest

from uaw.shared.errors import DomainError
from uaw.shared.schema import validate_contract
from uaw.tool.invocation.schema import normalize
from uaw.tool.registry import ToolRegistry
from uaw.tool.schema import canonical


def test_fixed_version_idempotency_cas_and_immutable_inputs(spec, binding):
    registry = ToolRegistry(capacity=2)
    assert registry.register(spec, expected_revision=0, binding=binding) == 1
    assert registry.register(deepcopy(spec), expected_revision=0, binding=binding) == 1
    spec["input_schema"]["properties"]["text"]["description"] = "mutated"
    assert (
        "description" not in registry.snapshot()[1][0].spec()["input_schema"]["properties"]["text"]
    )
    with pytest.raises(DomainError, match="immutable"):
        registry.register(spec, expected_revision=1, binding=binding)
    second = {**spec, "version": "v2"}
    with pytest.raises(DomainError, match="revision changed"):
        registry.register(second, expected_revision=0, binding=binding)
    registry.register(second, expected_revision=1, binding=binding)
    with pytest.raises(DomainError, match="full"):
        registry.register({**spec, "version": "v3"}, expected_revision=2, binding=binding)


def test_binding_is_exact_immutable_and_test_metadata_stays_internal(spec, binding):
    registry = ToolRegistry()
    with pytest.raises(DomainError, match="provider"):
        registry.register(
            spec,
            expected_revision=0,
            binding=replace(
                binding, provider_ref=binding.provider_ref.model_copy(update={"version": "2"})
            ),
        )
    registry.register(spec, expected_revision=0, binding=binding)
    with pytest.raises(DomainError, match="immutable"):
        registry.register(spec, expected_revision=1, binding=replace(binding, test_only=True))
    validate_contract("ToolSpec", registry.typed(registry.snapshot()[1][0]).wire())


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "object"},
        {"type": "object", "additionalProperties": True},
        {
            "type": "object",
            "properties": {"approved": {"type": "boolean"}},
            "additionalProperties": False,
        },
        {
            "type": "object",
            "properties": {"x": {"$ref": "https://example.invalid/schema"}},
            "additionalProperties": False,
        },
        {
            "type": "object",
            "properties": {"x": {"$ref": "#/$defs/x"}},
            "$defs": {"x": {"$ref": "#/$defs/x"}},
            "additionalProperties": False,
        },
        {
            "type": "object",
            "properties": {"x": {"type": "array", "items": {"type": "string"}}},
            "additionalProperties": False,
        },
        {
            "type": "object",
            "properties": {"x": {"type": "string", "pattern": "(a+)+$"}},
            "additionalProperties": False,
        },
        {"type": "object", "additionalProperties": False, "anyOf": [{}]},
        {
            "type": "object",
            "properties": {"x": {"type": "string", "format": "unknown-format"}},
            "additionalProperties": False,
        },
    ],
)
def test_unsafe_or_unsupported_registration_fails_without_network(spec, schema):
    spec["input_schema"] = schema
    with pytest.raises(DomainError) as exc:
        ToolRegistry().register(spec, expected_revision=0)
    assert exc.value.failure.code == "registration_invalid"


def test_local_refs_closed_arrays_and_formats(spec):
    spec["input_schema"] = {
        "type": "object",
        "$defs": {"r": {"type": "string", "format": "date-time"}},
        "properties": {"times": {"type": "array", "maxItems": 2, "items": {"$ref": "#/$defs/r"}}},
        "required": ["times"],
        "additionalProperties": False,
    }
    registry = ToolRegistry()
    registry.register(spec, expected_revision=0)
    call = {
        "tool_ref": registry.reference(registry.snapshot()[1][0]),
        "action_id": "a",
        "arguments": {"times": ["2026-10-07T00:00:00Z"]},
    }
    normalize(call, registry)
    call["arguments"]["times"] = ["no-time"]
    with pytest.raises(DomainError):
        normalize(call, registry)


def test_normalize_preserves_original_text_null_and_omission(registry, call):
    first = normalize(call, registry)
    reordered = deepcopy(call)
    reordered["arguments"] = dict(reversed(list(call["arguments"].items())))
    assert normalize(reordered, registry) == first
    assert first["arguments"]["text"] == call["arguments"]["text"]
    assert "optional" not in first["arguments"]
    call["arguments"]["optional"] = None
    assert normalize(call, registry)["arguments_hash"] != first["arguments_hash"]
    validate_contract("ValidatedCall", first)


@pytest.mark.parametrize(
    "changed",
    [
        {"count": "2"},
        {"count": True},
        {"count": 0},
        {"text": None},
        {"owner": "admin"},
        {"approved": True},
        {"effect": "read"},
        {"unknown": "secret-marker"},
        {"count": float("nan")},
        {"count": float("inf")},
    ],
)
def test_strict_arguments_redact_values(registry, call, changed):
    call["arguments"].update(changed)
    with pytest.raises(DomainError) as exc:
        normalize(call, registry)
    assert exc.value.failure.code == "invalid_arguments"
    assert "secret-marker" not in exc.value.failure.model_dump_json()


def test_spoofed_context_ref_and_unregistered_version_rejected(registry, call):
    for field in ("owner", "approved", "attempt_id", "supplied_context"):
        with pytest.raises(DomainError):
            normalize({**call, field: "untrusted"}, registry)
    wrong = deepcopy(call)
    wrong["tool_ref"]["version"] = "absent"
    with pytest.raises(DomainError) as exc:
        normalize(wrong, registry)
    assert exc.value.failure.code == "tool_missing"
    wrong = deepcopy(call)
    wrong["tool_ref"]["content_hash"] = "0" * 64
    with pytest.raises(DomainError) as exc:
        normalize(wrong, registry)
    assert exc.value.failure.code == "stale_resource"


def test_bounded_json_rejects_non_json_and_resource_abuse():
    for value in ({1: "bad"}, {"x": (1, 2)}, {"x": "x" * 65536}):
        with pytest.raises(ValueError):
            canonical(value)
    value = {}
    for _ in range(26):
        value = {"x": value}
    with pytest.raises(ValueError):
        canonical(value)


@pytest.mark.parametrize("revision", [True, 0.0, "0", -1])
def test_registration_revision_is_strict(spec, revision):
    with pytest.raises(DomainError) as exc:
        ToolRegistry().register(spec, expected_revision=revision)
    assert exc.value.failure.code == "registration_invalid"


def test_invalid_toolspec_uses_registration_failure_without_values(spec):
    spec["owner"] = "secret-marker"
    with pytest.raises(DomainError) as exc:
        ToolRegistry().register(spec, expected_revision=0)
    assert exc.value.failure.code == "registration_invalid"
    assert "secret-marker" not in exc.value.failure.model_dump_json()
