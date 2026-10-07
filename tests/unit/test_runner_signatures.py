"""Actual Ed25519 signatures, wire domain separation and schema receipt exclusivity."""

import copy
from dataclasses import replace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from uaw.shared.runner_signatures import VerificationKey, sign, signing_bytes, verify
from uaw.shared.schema import ContractViolation, validate_contract


@pytest.fixture
def keys():
    private = Ed25519PrivateKey.generate()
    return private.private_bytes_raw(), VerificationKey(
        "key-1", "device-1", private.public_key().public_bytes_raw(), "control"
    )


def message():
    return {
        "command_id": "command-1",
        "parameters": {"action": "file.read", "text": "原文  空白\n"},
        "fencing_token": 4,
        "expires_at": "2026-10-07T10:00:00Z",
    }


def test_real_signatures_bind_all_payload_fields_and_exact_text(keys):
    private, key = keys
    document = message()
    signature = sign(document, private, key.device_id, key.key_id, "command")
    assert verify(document, signature, key, "command")
    assert verify({**document, "signature": signature}, signature, key, "command")
    altered = copy.deepcopy(document)
    altered["parameters"]["text"] = "原文 空白\n"
    assert not verify(altered, signature, key, "command")
    for field, value in (
        ("fencing_token", 5),
        ("expires_at", "2026-10-08T10:00:00Z"),
        ("command_id", "other"),
    ):
        assert not verify({**document, field: value}, signature, key, "command")


def test_revoked_device_wrong_role_key_and_domain_fail(keys):
    private, key = keys
    document = message()
    signature = sign(document, private, key.device_id, key.key_id, "command")
    for invalid in (
        replace(key, revoked=True),
        replace(key, device_id="device-2"),
        replace(key, role="device"),
        replace(key, key_id="key-2"),
        replace(key, public_bytes=Ed25519PrivateKey.generate().public_key().public_bytes_raw()),
    ):
        assert not verify(document, signature, invalid, "command")
    device_key = replace(key, role="device")
    receipt = sign(document, private, key.device_id, key.key_id, "receipt")
    assert verify(document, receipt, device_key, "receipt")
    assert not verify(document, receipt, device_key, "pairing-proof")
    assert not verify(document, receipt, device_key, "root-selection")


@pytest.mark.parametrize(
    "value",
    [1.0, float("nan"), 2**53, {1: "key"}, "x" * (2 * 1024 * 1024), [[[[None]]]] * 4097],
    ids=["float", "nan", "large-int", "non-text-key", "oversized-text", "oversized-array"],
)
def test_unsupported_or_unbounded_json_is_rejected(keys, value):
    private, key = keys
    with pytest.raises(ValueError):
        sign({"value": value}, private, key.device_id, key.key_id, "command")


@pytest.mark.parametrize(
    "signature",
    [
        "yes",
        "",
        "uaw-ed25519-v1:key-1:" + "A" * 86 + "=",
        "x" * 300,
        "uaw-ed25519-v1:key-1:" + "!" * 86,
    ],
)
def test_invalid_signature_encoding_fails(keys, signature):
    assert not verify(message(), signature, keys[1], "command")


def test_json_key_order_is_stable_omission_is_distinct(keys):
    _, key = keys
    assert signing_bytes(
        {"b": 2, "a": "text"}, key.device_id, key.key_id, "command"
    ) == signing_bytes({"a": "text", "b": 2}, key.device_id, key.key_id, "command")
    assert signing_bytes({"a": None}, key.device_id, key.key_id, "command") != signing_bytes(
        {}, key.device_id, key.key_id, "command"
    )


def test_runner_receipt_status_branches_are_exclusive():
    usage = {
        "attempt_id": "attempt-1",
        "resources": {
            "wall_time_ms": 1,
            "model_calls": 0,
            "tool_calls": 1,
            "child_agents": 0,
            "currency": "USD",
        },
        "billing_state": "pending",
    }
    failure = {
        "code": "cancelled",
        "category": "cancelled",
        "message": "Cancelled",
        "retryable": False,
        "failed_phase": "dispatch",
        "evidence_refs": [],
    }
    receipt = {
        "command_id": "command-1",
        "attempt_id": "attempt-1",
        "kind": "cancelled",
        "failure": failure,
        "usage": usage,
        "signature": "fixture",
    }
    validate_contract("RunnerReceipt", receipt)
    with pytest.raises(ContractViolation):
        validate_contract(
            "RunnerReceipt",
            {**receipt, "wait_ref": {"kind": "approval", "id": "approval-1", "version": "1"}},
        )
    with pytest.raises(ContractViolation):
        validate_contract(
            "RunnerReceipt", {**receipt, "failure": {**failure, "category": "infrastructure"}}
        )
