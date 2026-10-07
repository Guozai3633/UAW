"""Versioned Runner wire signing primitives; live key authorization belongs to the caller."""

import base64
import json
import re
from dataclasses import dataclass
from typing import Any, Literal

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

Domain = Literal["command", "receipt", "pairing-proof", "root-selection"]
DOMAINS = {"command", "receipt", "pairing-proof", "root-selection"}
KEY_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
MAX_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class VerificationKey:
    """Read from the trusted live key registry, never from a command/receipt payload."""

    key_id: str
    device_id: str
    public_bytes: bytes
    role: Literal["control", "device"]
    revoked: bool = False


def _bounded(value: Any, depth: int = 0) -> None:
    if depth > 32:
        raise ValueError("Runner signature value exceeds nesting limit")
    if value is None or isinstance(value, (str, bool)):
        return
    if type(value) is int and abs(value) <= 2**53 - 1:
        return
    if isinstance(value, dict) and len(value) <= 1024:
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError("Runner signature keys must be text")
            _bounded(child, depth + 1)
        return
    if isinstance(value, list) and len(value) <= 4096:
        for child in value:
            _bounded(child, depth + 1)
        return
    raise ValueError("Runner signature value is outside the v1 JSON profile")


def signing_bytes(document: dict[str, Any], device_id: str, key_id: str, domain: Domain) -> bytes:
    if (
        domain not in DOMAINS
        or not KEY_ID.fullmatch(key_id)
        or not device_id
        or len(device_id) > 128
    ):
        raise ValueError("Invalid Runner signing identity")
    payload = {key: value for key, value in document.items() if key != "signature"}
    _bounded(payload)
    envelope = {
        "protocol": "uaw-ed25519-v1",
        "domain": domain,
        "device_id": device_id,
        "key_id": key_id,
        "payload": payload,
    }
    raw = json.dumps(
        envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    if len(raw) > MAX_BYTES:
        raise ValueError("Runner signature value exceeds byte limit")
    return raw


def sign(
    document: dict[str, Any], private_bytes: bytes, device_id: str, key_id: str, domain: Domain
) -> str:
    raw = signing_bytes(document, device_id, key_id, domain)
    signature = Ed25519PrivateKey.from_private_bytes(private_bytes).sign(raw)
    encoded = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return f"uaw-ed25519-v1:{key_id}:{encoded}"


def verify(document: dict[str, Any], signature: str, key: VerificationKey, domain: Domain) -> bool:
    """Cryptographic verification only. Caller still checks live Run/lease/fence/root authority."""
    if key.revoked or key.role != ("control" if domain == "command" else "device"):
        return False
    if not isinstance(signature, str) or len(signature) > 240:
        return False
    parts = signature.split(":")
    if len(parts) != 3 or parts[:2] != ["uaw-ed25519-v1", key.key_id]:
        return False
    if not re.fullmatch(r"[A-Za-z0-9_-]{86}", parts[2]):
        return False
    try:
        signature_bytes = base64.b64decode(parts[2] + "==", altchars=b"-_", validate=True)
        if base64.urlsafe_b64encode(signature_bytes).decode("ascii").rstrip("=") != parts[2]:
            return False
        Ed25519PublicKey.from_public_bytes(key.public_bytes).verify(
            signature_bytes, signing_bytes(document, key.device_id, key.key_id, domain)
        )
    except InvalidSignature, ValueError, UnicodeError, TypeError:
        return False
    return True
