"""Strict private IPC v1 envelope, not public pairing V2 or execution authority."""

import re
from typing import Any

from uaw.shared.errors import reject
from uaw.shared.schema import parse_json, validate_contract
from uaw_runner.ipc.windows_pipe import MAX_FRAME
from uaw_runner.receipts import canonical

NONCE = re.compile(r"[0-9a-f]{64}\Z")
FIELDS = {"version", "kind", "connection", "nonce", "peer_nonce", "sequence", "body", "signature"}
KINDS = {"hello", "proof", "ready", "command", "receipt", "recover", "error"}


def decode(data: bytes) -> dict[str, Any]:
    if not 0 < len(data) <= MAX_FRAME:
        raise reject("ipc_frame_invalid", "IPC frame length rejected")
    try:
        value = parse_json(data.decode("utf-8"))
        if not isinstance(value, dict) or set(value) != FIELDS:
            raise ValueError("Frame fields")
        if type(value["version"]) is not int or value["version"] != 1:
            raise ValueError("Frame version")
        if (
            value["kind"] not in KINDS
            or type(value["sequence"]) is not int
            or not 0 <= value["sequence"] < 2**31
        ):
            raise ValueError("Frame sequence/kind")
        validate_contract("ID", value["connection"])
        if not NONCE.fullmatch(value["nonce"]) or not NONCE.fullmatch(value["peer_nonce"]):
            raise ValueError("Frame nonce")
        if (
            not isinstance(value["body"], dict)
            or not isinstance(value["signature"], str)
            or not 1 <= len(value["signature"]) <= 240
        ):
            raise ValueError("Frame body/signature")
        # Public Ed25519 profile rejects floats/deep/large collections before signature use.
        from uaw.shared.runner_signatures import signing_bytes

        signing_bytes(value, "profile", "profile", "pairing-proof")
        return value
    except ValueError, TypeError, KeyError, UnicodeError, RecursionError:
        raise reject("ipc_frame_invalid", "Invalid private IPC envelope") from None


def encode(value: dict[str, Any]) -> bytes:
    data = canonical(value).encode("utf-8")
    decode(data)
    return data


def proof_document(frame: dict[str, Any], *, role: str) -> dict[str, Any]:
    # Explicit purpose and role inside shared canonical signature envelope prevent public
    # command/receipt signatures being reinterpreted as handshake possession proofs.
    return {
        "ipc_protocol": "uaw-windows-local-v1",
        "purpose": "connection-frame",
        "role": role,
        "frame": {k: v for k, v in frame.items() if k != "signature"},
    }
