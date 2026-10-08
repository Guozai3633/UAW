import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from uaw.shared.contracts import Principal, RequestMeta, ScopeSelector, TrustedExecutionContext
from uaw.shared.schema import ContractViolation, parse_json, validate_contract

ROOT = Path(__file__).resolve().parents[3]


def test_reconciliation_known_effect_requires_evidence_and_no_self_approval() -> None:
    examples = json.loads((ROOT / "contracts/examples.json").read_text(encoding="utf-8"))[
        "examples"
    ]
    receipt = examples["ToolReconciliationReceipt"]
    for outcome in ("applied", "not_applied"):
        with pytest.raises(ContractViolation):
            validate_contract(
                "ToolReconciliationReceipt", {**receipt, "outcome": outcome, "evidence_refs": []}
            )
    validate_contract(
        "ToolReconciliationReceipt", {**receipt, "outcome": "unknown", "evidence_refs": []}
    )
    with pytest.raises(ContractViolation):
        validate_contract("ToolReconciliationReceipt", {**receipt, "approved": True})


def test_runner_authority_has_no_implicit_defaults_or_native_path() -> None:
    examples = json.loads((ROOT / "contracts/examples.json").read_text(encoding="utf-8"))[
        "examples"
    ]
    authority = examples["RunnerAuthoritySnapshot"]
    for field in ("context", "fencing_token", "lease_expires_at", "connected", "feature_enabled"):
        with pytest.raises(ContractViolation):
            validate_contract(
                "RunnerAuthoritySnapshot", {k: v for k, v in authority.items() if k != field}
            )
    with pytest.raises(ContractViolation):
        validate_contract("RunnerAuthoritySnapshot", {**authority, "native_path": "C:/private"})


def test_packaged_schema_has_not_drifted() -> None:
    canonical = (ROOT / "contracts/uaw.schema.json").read_bytes()
    packaged = (ROOT / "src/uaw/resources/uaw.schema.json").read_bytes()
    assert hashlib.sha256(canonical).digest() == hashlib.sha256(packaged).digest()


@pytest.mark.parametrize("revision", [True, "3", -1, 3.5])
def test_revision_does_not_coerce_user_data(revision: object) -> None:
    with pytest.raises(ValidationError):
        RequestMeta.model_validate(
            {"request_id": "r1", "schema_version": "0.1", "expected_revision": revision}
        )


def test_user_selector_cannot_claim_an_identity_or_approval() -> None:
    for injected in [{"principal_id": "admin"}, {"approved": True}, {"capabilities": ["exec"]}]:
        with pytest.raises(ValidationError):
            ScopeSelector.model_validate({"conversation_id": "c1", **injected})


def test_ref_enum_and_timestamp_are_checked_by_authoritative_schema() -> None:
    with pytest.raises(ContractViolation):
        validate_contract("Ref", {"kind": "made-up", "id": "r1", "version": "1"})
    with pytest.raises(ContractViolation):
        validate_contract("Timestamp", "2026-10-07T12:00:00")


def test_scope_must_match_the_authenticated_principal() -> None:
    data = {
        "principal": {"id": "u1", "kind": "user", "auth_session_id": "s1"},
        "scope": {"principal_id": "u2"},
        "operation_id": "op1",
        "trace_id": "t1",
        "attempt_id": "a1",
        "deadline": "2026-10-08T00:00:00Z",
        "capability_policy_ref": {"kind": "policy", "id": "p1", "version": "1"},
    }
    with pytest.raises(ValidationError, match="authenticated principal"):
        TrustedExecutionContext.model_validate(data)


def test_omitted_optional_field_and_null_are_not_interchangeable() -> None:
    principal = Principal(id="u1", kind="user", auth_session_id="s1")
    assert "delegated_by" not in principal.wire()
    with pytest.raises(ValidationError):
        Principal(id="u1", kind="user", auth_session_id="s1", delegated_by=None)


@pytest.mark.parametrize(
    "data", ['{"x": NaN}', '{"x": Infinity}', '{"x": 1, "x": 2}', '{"x": 1e999}']
)
def test_ambiguous_or_non_json_inputs_are_rejected(data: str) -> None:
    with pytest.raises(ValueError):
        parse_json(data)
