"""Bounded Chat Completions SSE framing; reasoning never enters display callbacks."""

import codecs
import json
from typing import Any

from uaw.model.contracts import ProviderFailure
from uaw.shared.schema import parse_json, validator


class CompletionStream:
    def __init__(self, models: tuple[str, ...], limit: int = 2_097_152) -> None:
        self.models, self.limit = models, limit
        self.raw = bytearray()
        self.decoder = codecs.getincrementaldecoder("utf-8")("strict")
        self.pending = ""
        self.lines: list[str] = []
        self.content: list[str] = []
        self.model: str | None = None
        self.receipt: str | None = None
        self.reason: str | None = None
        self.usage: dict[str, Any] | None = None
        self.refusal: str | None = None
        self.done = False

    def feed(self, chunk: bytes) -> list[str]:
        if len(self.raw) + len(chunk) > self.limit:
            raise ProviderFailure("provider_response_too_large")
        self.raw.extend(chunk)
        try:
            self.pending += self.decoder.decode(chunk)
        except UnicodeDecodeError:
            raise ProviderFailure("provider_stream_utf8_invalid") from None
        result: list[str] = []
        while "\n" in self.pending:
            line, self.pending = self.pending.split("\n", 1)
            if line.endswith("\r"):
                line = line[:-1]
            if not line:
                if self.lines:
                    value = self.event("\n".join(self.lines))
                    if value:
                        result.append(value)
                    self.lines.clear()
            elif line.startswith("data:"):
                data = line[5:]
                self.lines.append(data[1:] if data.startswith(" ") else data)
            elif not line.startswith(":"):
                raise ProviderFailure("provider_stream_field_unsupported")
        return result

    def event(self, text: str) -> str:
        if self.done:
            raise ProviderFailure("provider_stream_after_done")
        if text == "[DONE]":
            if self.reason is None:
                raise ProviderFailure("provider_stream_finish_missing")
            self.done = True
            return ""
        try:
            row = parse_json(text)
        except ValueError, TypeError, RecursionError:
            raise ProviderFailure("provider_stream_json_invalid") from None
        if not isinstance(row, dict) or row.get("object") != "chat.completion.chunk":
            raise ProviderFailure("provider_stream_chunk_invalid")
        model, receipt = row.get("model"), row.get("id")
        if model not in self.models or self.model is not None and model != self.model:
            raise ProviderFailure("provider_model_mismatch")
        if not validator("ID").is_valid(receipt) or (
            self.receipt is not None and receipt != self.receipt
        ):
            raise ProviderFailure("provider_stream_identity_changed")
        self.model, self.receipt = model, receipt
        choices = row.get("choices")
        usage = row.get("usage")
        if usage is not None:
            if self.usage is not None or not isinstance(usage, dict):
                raise ProviderFailure("provider_usage_invalid")
            self.usage = usage
        if choices == [] and usage is not None and self.reason is not None:
            return ""
        if not isinstance(choices, list) or len(choices) != 1:
            raise ProviderFailure("provider_choice_count_invalid")
        choice = choices[0]
        if (
            not isinstance(choice, dict)
            or type(choice.get("index")) is not int
            or choice["index"] != 0
        ):
            raise ProviderFailure("provider_stream_choice_invalid")
        delta = choice.get("delta")
        if not isinstance(delta, dict) or delta.get("role", "assistant") != "assistant":
            raise ProviderFailure("provider_message_role_invalid")
        if delta.get("tool_calls"):
            raise ProviderFailure("provider_stream_tool_delta_unsupported")
        content = delta.get("content")
        if content is None:
            content = ""
        if not isinstance(content, str) or self.reason is not None:
            raise ProviderFailure("provider_stream_content_invalid")
        refusal = delta.get("refusal")
        if refusal is not None:
            if not isinstance(refusal, str):
                raise ProviderFailure("provider_stream_refusal_invalid")
            self.refusal = (self.refusal or "") + refusal
        reason = choice.get("finish_reason")
        if reason is not None:
            if reason not in ("stop", "length", "content_filter", "refusal"):
                raise ProviderFailure("provider_finish_reason_invalid")
            self.reason = reason
        self.content.append(content)
        return content

    def complete(self) -> bytes:
        try:
            remaining = self.decoder.decode(b"", final=True)
        except UnicodeDecodeError:
            raise ProviderFailure("provider_stream_utf8_invalid") from None
        if not self.done or self.lines or self.pending.strip() or remaining:
            raise ProviderFailure("provider_stream_incomplete", category="unknown_effect")
        if self.model is None or self.receipt is None:
            raise ProviderFailure("provider_stream_identity_missing")
        message: dict[str, Any] = {"role": "assistant", "content": "".join(self.content)}
        if self.refusal:
            message["refusal"] = self.refusal
        return json.dumps(
            {
                "id": self.receipt,
                "model": self.model,
                "choices": [{"index": 0, "finish_reason": self.reason, "message": message}],
                "usage": self.usage,
            },
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
