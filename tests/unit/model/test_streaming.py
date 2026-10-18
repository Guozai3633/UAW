"""Protocol/security tests; these fixtures are not actual model or human evidence."""

import asyncio
import json
from dataclasses import replace

import httpx
import pytest

from tests.unit.model.test_adapter import request
from uaw.model.adapters import ChatCompletionsAdapter
from uaw.model.contracts import ProviderFailure
from uaw.model.stream_text import ReplyText
from uaw.model.streaming import CompletionStream


def frame(delta, *, reason=None, usage=None, model="fixture-model", receipt="fixture-call"):
    return (
        "data: "
        + json.dumps(
            {
                "id": receipt,
                "object": "chat.completion.chunk",
                "model": model,
                "choices": [{"index": 0, "delta": delta, "finish_reason": reason}],
                "usage": usage,
            },
            ensure_ascii=False,
        )
        + "\n\n"
    ).encode()


@pytest.mark.parametrize("split", [1, 2, 7, 128, 8192])
def test_sse_arbitrary_byte_splits_preserve_unicode_and_ignore_reasoning(split):
    raw = (
        b": keepalive\r\n\r\n"
        + frame({"role": "assistant", "reasoning_content": "NEVER DISPLAY"})
        + frame({"content": "你好🌍"})
        + frame({}, reason="stop", usage={"prompt_tokens": 5, "completion_tokens": 2})
        + b"data: [DONE]\n\n"
    )
    parser = CompletionStream(("fixture-model",))
    displayed = []
    for i in range(0, len(raw), split):
        displayed.extend(parser.feed(raw[i : i + split]))
    result = json.loads(parser.complete())
    assert displayed == ["你好🌍"]
    assert result["choices"][0]["message"]["content"] == "你好🌍"
    assert bytes(parser.raw) == raw and result["usage"]["prompt_tokens"] == 5
    assert "NEVER DISPLAY" not in json.dumps(result)


@pytest.mark.parametrize(
    "fault", ["missing_done", "changed_model", "changed_id", "after_done", "limit"]
)
def test_sse_rejects_incomplete_or_conflicting_identity(fault):
    parser = CompletionStream(("fixture-model",), limit=1 if fault == "limit" else 8192)
    with pytest.raises(ProviderFailure):
        parser.feed(frame({"content": "prefix"}))
        if fault == "changed_model":
            parser.feed(frame({"content": "other"}, model="different"))
        if fault == "changed_id":
            parser.feed(frame({"content": "other"}, receipt="different"))
        parser.feed(frame({}, reason="stop"))
        if fault != "missing_done":
            parser.feed(b"data: [DONE]\n\n")
        if fault == "after_done":
            parser.feed(frame({"content": "late"}))
        parser.complete()


def test_usage_only_frame_is_supported_without_inventing_content():
    parser = CompletionStream(("fixture-model",))
    parser.feed(frame({"content": "answer"}, reason="stop"))
    row = json.loads(frame({}).decode()[6:].strip())
    row.update(choices=[], usage={"prompt_tokens": 2, "completion_tokens": 1})
    assert parser.feed(("data: " + json.dumps(row) + "\n\ndata: [DONE]\n\n").encode()) == []
    assert json.loads(parser.complete())["usage"]["completion_tokens"] == 1


@pytest.mark.parametrize("chunk_size", [1, 3, 17, 65536])
def test_reply_parser_emits_only_actual_decoded_text(chunk_size):
    expected = '第一行\n"quoted" 😀'
    raw = json.dumps(
        {"protocol": "conversation-v1", "action": "reply", "text": expected}, ensure_ascii=True
    )
    parser = ReplyText()
    observed = []
    for i in range(0, len(raw), chunk_size):
        text = parser.feed(raw[i : i + chunk_size])
        assert expected.startswith(text)
        observed.append(text)
    assert observed[-1] == expected
    assert all('"protocol"' not in item for item in observed)


@pytest.mark.parametrize("action", ["tool", "deliver", "ask"])
def test_non_reply_or_missing_discriminator_never_becomes_chat_text(action):
    parser = ReplyText()
    assert parser.feed('{"text":"PRIVATE TOOL ARGUMENT"') == ""
    assert parser.feed(',"protocol":"conversation-v1","action":' + json.dumps(action) + "}") == ""


def test_unordered_complete_text_waits_for_reply_identity():
    parser = ReplyText()
    assert parser.feed('{"text":"safe answer","action":"reply"') == ""
    assert parser.feed(',"protocol":"conversation-v1"}') == "safe answer"


def test_late_duplicate_fields_are_rejected_without_replacing_the_prefix():
    parser = ReplyText()
    assert parser.feed('{"protocol":"conversation-v1","action":"reply","text":"prefix"') == "prefix"
    with pytest.raises(ProviderFailure):
        parser.feed(',"action":"tool"}')
    assert parser.displayed == "prefix"


class Fragments(httpx.AsyncByteStream):
    def __init__(self, chunks):
        self.chunks, self.ended = chunks, False

    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk
            await asyncio.sleep(0)
        self.ended = True


async def test_adapter_releases_real_deltas_before_done_and_preserves_usage_and_raw():
    chunks = [
        frame({"role": "assistant", "reasoning_content": "hidden"}),
        frame({"content": "first "}),
        frame({"content": "second"}),
        frame({}, reason="stop", usage={"prompt_tokens": 5, "completion_tokens": 2}),
        b"data: [DONE]\n\n",
    ]
    source = Fragments(chunks)
    observed = []

    async def content(delta):
        assert not source.ended
        observed.append(delta)

    async def handle(incoming):
        body = json.loads(incoming.content)
        assert body["stream"] is True and body["stream_options"] == {"include_usage": True}
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=source)

    adapter = ChatCompletionsAdapter(httpx.AsyncClient(transport=httpx.MockTransport(handle)))
    try:
        result = await adapter.generate(replace(request(), on_content=content))
    finally:
        await adapter.close()
    assert observed == ["first ", "second"] and result.text == "first second"
    assert result.resources == {"input_tokens": 5, "output_tokens": 2}
    assert result.raw == b"".join(chunks)


async def test_interruption_preserves_received_raw_usage_and_never_retries():
    raw = frame(
        {"content": "partial"}, reason="stop", usage={"prompt_tokens": 5, "completion_tokens": 2}
    )
    calls = 0

    async def handle(incoming):
        nonlocal calls
        calls += 1
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, stream=Fragments([raw])
        )

    async def content(delta):
        assert delta == "partial"

    adapter = ChatCompletionsAdapter(httpx.AsyncClient(transport=httpx.MockTransport(handle)))
    try:
        with pytest.raises(ProviderFailure) as caught:
            await adapter.generate(replace(request(), on_content=content))
    finally:
        await adapter.close()
    assert calls == 1 and not caught.value.safe_retry
    assert caught.value.failure.category == "unknown_effect"
    assert caught.value.response_raw == raw and caught.value.resources["output_tokens"] == 2
