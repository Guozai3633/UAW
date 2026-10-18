"""Display only decoded conversation-v1 reply text, never arbitrary JSON fields."""

import json

from uaw.model.contracts import ProviderFailure


def string_prefix(text: str, start: int) -> tuple[str, int, bool]:
    result: list[str] = []
    i = start + 1
    escapes = {
        '"': '"',
        "\\": "\\",
        "/": "/",
        "b": "\b",
        "f": "\f",
        "n": "\n",
        "r": "\r",
        "t": "\t",
    }
    while i < len(text):
        ch = text[i]
        if ch == '"':
            return "".join(result), i + 1, True
        if ch != "\\":
            if ord(ch) < 32 and ch not in "\n\r\t":
                raise ProviderFailure("provider_stream_text_invalid")
            result.append(ch)
            i += 1
            continue
        if i + 1 >= len(text):
            break
        escape = text[i + 1]
        if escape in escapes:
            result.append(escapes[escape])
            i += 2
            continue
        if escape != "u":
            raise ProviderFailure("provider_stream_text_escape_invalid")
        if i + 6 > len(text):
            break
        if any(ch not in "0123456789abcdefABCDEF" for ch in text[i + 2 : i + 6]):
            raise ProviderFailure("provider_stream_text_escape_invalid")
        try:
            code = int(text[i + 2 : i + 6], 16)
        except ValueError:
            raise ProviderFailure("provider_stream_text_escape_invalid") from None
        consumed = 6
        if 0xD800 <= code <= 0xDBFF:
            if i + 12 > len(text):
                break
            try:
                low = int(text[i + 8 : i + 12], 16)
            except ValueError:
                raise ProviderFailure("provider_stream_surrogate_invalid") from None
            if text[i + 6 : i + 8] != "\\u" or not 0xDC00 <= low <= 0xDFFF:
                raise ProviderFailure("provider_stream_surrogate_invalid")
            code = 0x10000 + ((code - 0xD800) << 10) + low - 0xDC00
            consumed = 12
        elif 0xDC00 <= code <= 0xDFFF:
            raise ProviderFailure("provider_stream_surrogate_invalid")
        result.append(chr(code))
        i += consumed
    return "".join(result), i, False


class ReplyText:
    def __init__(self) -> None:
        self.buffer = ""
        self.displayed = ""

    def feed(self, delta: str) -> str:
        self.buffer += delta
        if len(self.buffer) > 262144:
            raise ProviderFailure("provider_stream_text_too_large")
        text = self.buffer
        i = len(text) - len(text.lstrip())
        if i >= len(text):
            return self.displayed
        if text[i] != "{":
            raise ProviderFailure("provider_stream_object_required")
        i += 1
        fields: dict[str, object] = {}
        candidate = ""
        decoder = json.JSONDecoder()
        while i < len(text):
            while i < len(text) and text[i].isspace():
                i += 1
            if i >= len(text) or text[i] == "}":
                break
            try:
                key, i = decoder.raw_decode(text, i)
            except json.JSONDecodeError:
                break
            if not isinstance(key, str) or key in fields:
                raise ProviderFailure("provider_stream_duplicate_field")
            while i < len(text) and text[i].isspace():
                i += 1
            if i >= len(text):
                break
            if text[i] != ":":
                raise ProviderFailure("provider_stream_object_invalid")
            i += 1
            while i < len(text) and text[i].isspace():
                i += 1
            if i >= len(text):
                break
            if key == "text" and text[i] == '"':
                candidate, i, complete = string_prefix(text, i)
                fields[key] = candidate
                if not complete:
                    break
            else:
                try:
                    fields[key], i = decoder.raw_decode(text, i)
                except json.JSONDecodeError:
                    break
            while i < len(text) and text[i].isspace():
                i += 1
            if i >= len(text) or text[i] == "}":
                break
            if text[i] != ",":
                raise ProviderFailure("provider_stream_object_invalid")
            i += 1
        if fields.get("protocol") == "conversation-v1" and fields.get("action") == "reply":
            if not candidate.startswith(self.displayed) or len(candidate) > 65536:
                raise ProviderFailure("provider_stream_prefix_changed")
            self.displayed = candidate
        return self.displayed
