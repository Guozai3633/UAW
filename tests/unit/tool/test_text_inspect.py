"""Actual local calculations; response port is a controlled component fixture."""

import hashlib

import pytest

from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import DomainError
from uaw.tool.invocation.schema import normalize
from uaw.tool.providers.text import (
    MAX_TEXT_BYTES,
    TextInspectExecutor,
    TextInspectVerifier,
    inspect_text,
    text_spec,
)
from uaw.tool.registry import ToolRegistry


@pytest.mark.parametrize(
    "text,lines", [("", 0), ("a", 1), ("a\r\nb\n", 2), ("  原文\r\nKeep\u0301 exact  ", 2)]
)
def test_actual_text_preserves_unicode_whitespace_and_line_endings(text, lines):
    actual = inspect_text(text)
    assert actual == {
        "characters": len(text),
        "utf8_bytes": len(text.encode("utf-8")),
        "lines": lines,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def test_text_bounded_by_utf8_bytes_and_never_coerced():
    assert inspect_text("a" * MAX_TEXT_BYTES)["utf8_bytes"] == MAX_TEXT_BYTES
    for bad in ("原" * MAX_TEXT_BYTES, 123, None):
        with pytest.raises(ValueError):
            inspect_text(bad)


async def test_text_adapter_stores_actual_response_and_strict_measured_usage(ctx):
    provider_ref = Ref(kind="provider", id="internal-text", version="1")
    provider = Principal(
        id="internal-text-service", kind="service", auth_session_id="provider-session"
    )
    spec = text_spec(provider_ref)
    registry = ToolRegistry()
    registry.register(spec, expected_revision=0)
    call = normalize(
        {
            "tool_ref": registry.reference(registry.snapshot()[1][0]),
            "action_id": "text-action",
            "arguments": {"text": "原文\r\n"},
        },
        registry,
    )

    class ResponsePortFixture:
        def __init__(self):
            self.provider_ref = provider_ref
            self.saved = None

        def authenticate(self, principal):
            assert principal == provider

        async def binding(self, context):
            assert context == ctx

        async def save_response(self, data, usage, context, *, authenticated_provider):
            assert context == ctx and authenticated_provider == provider
            self.saved = (data, usage)
            return {
                "attempt_id": ctx.attempt_id,
                "raw_result_ref": {"kind": "content", "id": "saved", "version": "1"},
                "transport_status": "local_computation_completed",
                "effect_state": "confirmed",
                "usage": usage,
            }

    source = ResponsePortFixture()
    executor = TextInspectExecutor(source, provider=provider)
    receipt = await executor.execute(call, spec, ctx)
    data, usage = source.saved
    assert data == inspect_text("原文\r\n") and usage["attempt_id"] == ctx.attempt_id
    assert usage["resources"]["money"] == "0.00" and usage["resources"]["tool_calls"] == 1
    assert receipt["usage"] == usage
    verifier = TextInspectVerifier(provider_ref)
    await verifier.verify(data, call, spec, ctx)
    with pytest.raises(DomainError):
        await verifier.verify({**data, "sha256": "0" * 64}, call, spec, ctx)
    with pytest.raises(DomainError):
        await verifier.verify(data, call, {**spec, "effect": "external_write"}, ctx)
