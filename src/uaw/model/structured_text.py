"""Narrow JSON-object prose compatibility; original provider bytes stay unchanged."""

from typing import Any

from uaw.shared.schema import parse_json


def structured_text(text: str, *, literal_whitespace: bool) -> Any:
    """Accept only literal LF/CR/TAB within strings in compatibility mode.

    This does not infer quotes, keys, actions, missing delimiters or a completed
    response. Duplicate keys, non-finite numbers and every other JSON failure
    still use the original strict parser. Callers validate the full schema too.
    """
    try:
        return parse_json(text)
    except ValueError:
        if not literal_whitespace:
            raise
    escaped = inside = changed = False
    characters = []
    replacements = {"\n": "\\n", "\r": "\\r", "\t": "\\t"}
    for character in text:
        if inside and escaped:
            # A backslash followed by a physical newline is an invalid escape,
            # not the provider's observed literal prose-whitespace case.
            escaped = False
        elif inside and character == "\\":
            escaped = True
        elif character == '"':
            inside = not inside
        elif inside and character in replacements:
            character = replacements[character]
            changed = True
        characters.append(character)
    if not changed:
        raise ValueError("structured_text_not_literal_whitespace")
    return parse_json("".join(characters))
