"""Strict private frame parser; no transport or native authorization is claimed here."""

import json

import pytest
from uaw_runner.ipc.frames import decode, encode
from uaw_runner.ipc.windows_pipe import MAX_FRAME

from uaw.shared.errors import DomainError


def frame():
    return {
        "version": 1,
        "kind": "command",
        "connection": "ipc-test",
        "nonce": "a" * 64,
        "peer_nonce": "b" * 64,
        "sequence": 1,
        "body": {"id": "message"},
        "signature": "pending",
    }


def test_unicode_private_frame_preserves_original_text():
    value = frame()
    value["body"] = {"text": "原文 é 😀\r\n"}
    assert decode(encode(value)) == value


@pytest.mark.parametrize("field", list(frame()))
def test_required_envelope_fields(field):
    value = frame()
    del value[field]
    with pytest.raises(DomainError):
        decode(json.dumps(value).encode())


@pytest.mark.parametrize(
    "raw",
    [
        b'{"version":1,"version":1}',
        b'{"x":NaN}',
        b'{"x":1e999}',
        b"[]",
        b"null",
        b"\xff",
        b"",
        b"a" * (MAX_FRAME + 1),
    ],
    ids=["duplicate", "nonfinite", "overflow", "array", "null", "utf8", "empty", "too_large"],
)
def test_invalid_frames(raw):
    with pytest.raises(DomainError):
        decode(raw)


@pytest.mark.parametrize(
    "field,value",
    [
        ("version", True),
        ("version", 2),
        ("kind", "approved"),
        ("sequence", True),
        ("sequence", -1),
        ("sequence", 2**31),
        ("nonce", "x" * 64),
        ("nonce", None),
        ("body", []),
        ("signature", ""),
        ("signature", "a" * 241),
    ],
)
def test_frame_version_types_and_no_authorization_branches(field, value):
    current = frame()
    current[field] = value
    with pytest.raises(DomainError):
        decode(json.dumps(current).encode())


def test_unknown_envelope_field_denied():
    value = frame()
    value["approved"] = True
    with pytest.raises(DomainError):
        decode(json.dumps(value).encode())
