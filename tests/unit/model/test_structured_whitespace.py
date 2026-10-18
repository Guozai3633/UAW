"""Provider prose serialization compatibility cannot change actions or hide bad JSON."""

import json
from dataclasses import replace

import httpx
import pytest

from tests.integration.model.test_gateway import reply
from tests.unit.model.test_adapter import request
from uaw.model.adapters import ChatCompletionsAdapter
from uaw.model.contracts import ProviderFailure


def configured(mode="json_object"):
    original = request()
    return replace(
        original,
        protocol="json_schema",
        settings={**original.settings, "structured_output_mode": mode},
        output_schema={
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
            "additionalProperties": False,
        },
    )


@pytest.mark.parametrize("prose", ["标题\n正文", "a\r\nb", "a\tb", "a\\path\n“引述”"])
def test_literal_prose_whitespace_preserves_exact_string_and_raw_response(prose):
    # Encode every other character normally; only these three literal characters
    # reproduce the observed json_object provider's malformed prose encoding.
    content = json.dumps({"answer": prose}, ensure_ascii=False)
    for encoded, literal in [("\\n", "\n"), ("\\r", "\r"), ("\\t", "\t")]:
        content = content.replace(encoded, literal)
    raw = json.dumps(reply(content), ensure_ascii=False).encode()
    result = ChatCompletionsAdapter.parse(raw, configured())
    assert result.structured_data == {"answer": prose}
    assert result.text == content and result.raw == raw
    assert result.resources == {"input_tokens": 20, "output_tokens": 8}


def test_valid_escaped_quotes_backslashes_and_formatting_stay_unchanged():
    prose = 'literal \\n, a "quote", and newline\nend'
    content = json.dumps({"answer": prose}, indent=2)
    raw = json.dumps(reply(content)).encode()
    result = ChatCompletionsAdapter.parse(raw, configured())
    assert result.structured_data == {"answer": prose}
    assert result.text == content and result.raw == raw


@pytest.mark.parametrize(
    "content",
    [
        '{"answer":"raw\nline", "answer":"duplicate"}',
        '{"answer":"raw\nline", "other":true}',
        '{"answer":"A "quoted" term\nend"}',
        '{"answer":"unfinished\n',
        '```json\n{"answer":"wrapped"}\n```',
        '{"answer":"raw\x00null\nline"}',
        '{"answer":"raw\nline"} trailing',
        '{"answer":NaN,"line":"raw\nline"}',
        '{"answer":"bad\\\ncontinuation"}',
        '{"answer":"one\nline"}{"answer":"second"}',
    ],
)
def test_whitespace_compatibility_cannot_repair_structure_or_change_schema(content):
    with pytest.raises(ProviderFailure) as failed:
        ChatCompletionsAdapter.parse(json.dumps(reply(content)).encode(), configured())
    assert failed.value.failure.code == "provider_structured_output_invalid"


def test_native_schema_mode_keeps_strict_transport_contract():
    raw = json.dumps(reply('{"answer":"raw\nline"}')).encode()
    with pytest.raises(ProviderFailure) as failed:
        ChatCompletionsAdapter.parse(raw, configured("json_schema"))
    assert failed.value.failure.code == "provider_structured_output_invalid"


async def test_compatible_response_is_one_call_and_invalid_usage_is_still_rejected():
    content = '{"answer":"a\nb"}'
    raw = json.dumps(reply(content)).encode()
    sent = []

    def respond(req):
        sent.append(req)
        return httpx.Response(200, content=raw)

    adapter = ChatCompletionsAdapter(httpx.AsyncClient(transport=httpx.MockTransport(respond)))
    try:
        result = await adapter.generate(configured())
        assert len(sent) == 1 and result.structured_data == {"answer": "a\nb"}
        assert result.text == content and result.raw == raw
    finally:
        await adapter.close()
    malformed_usage = reply(content)
    malformed_usage["usage"]["total_tokens"] += 1
    with pytest.raises(ProviderFailure) as failed:
        ChatCompletionsAdapter.parse(json.dumps(malformed_usage).encode(), configured())
    assert failed.value.failure.code == "provider_usage_invalid"


def test_length_finish_does_not_turn_partial_text_into_a_decision():
    wire = reply('{"answer":"truncated\n')
    wire["choices"][0]["finish_reason"] = "length"
    result = ChatCompletionsAdapter.parse(json.dumps(wire).encode(), configured())
    assert result.finish_reason == "length" and result.structured_data is None
