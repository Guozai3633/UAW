import json
from dataclasses import replace
from datetime import timedelta

import pytest
from pydantic import ValidationError
from uaw_runner.protocol import RunnerProtocol

from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, DomainError
from uaw.shared.schema import ContractViolation
from uaw.workspace.contracts import RunnerCommand, RunnerReceipt

from .conftest import NOW, wire


def test_admission_retries_keep_original_attempt_and_state(setup):
    _, _, _, command, _, signatures, admissions, protocol = setup
    original = protocol.admit(wire(command), now=NOW)
    data = command.wire()
    data["trusted_context"].update(attempt_id="a2", trace_id="t2")
    retry = RunnerCommand.model_validate_json(json.dumps(data))
    assert protocol.admit(wire(retry), now=NOW) == original
    assert signatures.seen == retry.wire()  # Full parameters/context passed to verifier.
    admissions.cancel("u1", "d1", "cmd1")
    assert protocol.admit(wire(retry), now=NOW).state == "cancelled"


@pytest.mark.parametrize("change", ["path", "model", "version"])
def test_command_identity_cannot_change_on_retry(setup, change):
    _, _, _, command, authority, _, _, protocol = setup
    protocol.admit(wire(command), now=NOW)
    data = command.wire()
    if change == "path":
        data["parameters"]["parameters"]["path"] = "."
    elif change == "model":
        data["trusted_context"]["model_policy_ref"]["version"] = "2"
    else:
        data["request_ref"]["version"] = "2"
    changed = RunnerCommand.model_validate_json(json.dumps(data))
    # Even if trusted services now allow this value, the logical ID cannot be reused.
    authority.value = replace(
        authority.value,
        context=changed.trusted_context,
        request_ref=changed.request_ref,
        request_parameters=changed.wire()["parameters"],
    )
    with pytest.raises(DomainError) as error:
        protocol.admit(wire(changed), now=NOW)
    assert error.value.failure.code == "revision_conflict"


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("device_id", "d2", "binding_mismatch"),
        ("root_handle", "unknown", "permission_denied"),
        ("binding_revision", 1, "revision_conflict"),
        ("fencing_token", 5, "revision_conflict"),
        ("feature_enabled", False, "feature_disabled"),
        ("connected", False, "capability_unavailable"),
        ("cancelled", True, "cancelled"),
        ("allowed_actions", frozenset(), "permission_denied"),
        ("required_scope_capability", "other", "permission_denied"),
        ("lease_expires_at", NOW, "deadline_exceeded"),
        ("policy_ref", Ref(kind="policy", id="p1", version="2"), "revision_conflict"),
        ("workspace_ref", Ref(kind="workspace", id="w1", version="2"), "permission_denied"),
    ],
)
def test_live_authority_rechecked_including_retries(setup, field, value, code):
    _, _, _, command, authority, _, _, protocol = setup
    protocol.admit(wire(command), now=NOW)
    authority.value = replace(authority.value, **{field: value})
    with pytest.raises(DomainError) as error:
        protocol.admit(wire(command), now=NOW)
    assert error.value.failure.code == code


def test_scope_identity_and_fixed_model_are_rechecked(setup):
    _, _, _, command, authority, _, _, protocol = setup
    data = command.trusted_context.wire()
    data["model_policy_ref"]["id"] = "silent-fallback"
    authority.value = replace(
        authority.value, context=TrustedExecutionContext.model_validate_json(json.dumps(data))
    )
    with pytest.raises(DomainError, match="Device or principal"):
        protocol.admit(wire(command), now=NOW)


@pytest.mark.parametrize("field", ["expires_at", "deadline"])
def test_deadline_boundary_is_closed(setup, field):
    _, _, _, command, _, _, _, protocol = setup
    data = command.wire()
    target = data if field == "expires_at" else data["trusted_context"]
    target[field] = NOW.isoformat()
    with pytest.raises(DomainError) as error:
        protocol.admit(json.dumps(data), now=NOW)
    assert error.value.failure.code == "deadline_exceeded"


def test_command_cannot_extend_original_deadline(setup):
    _, _, _, command, _, _, _, protocol = setup
    data = command.wire()
    data["trusted_context"]["deadline"] = (NOW + timedelta(days=1)).isoformat()
    with pytest.raises(DomainError) as error:
        protocol.admit(json.dumps(data), now=NOW)
    assert error.value.failure.code == "deadline_exceeded"


def test_signature_missing_ports_and_executor_are_unavailable(setup):
    _, _, bindings, command, authority, signatures, admissions, protocol = setup
    signatures.valid = False
    with pytest.raises(DomainError) as error:
        protocol.admit(wire(command), now=NOW)
    assert error.value.failure.code == "permission_denied"
    signatures.valid = True
    for missing in ("signatures", "authority"):
        options = dict(
            device_id="d1",
            bindings=bindings,
            admissions=admissions,
            signatures=signatures,
            authority=authority,
        )
        options[missing] = None
        with pytest.raises(CapabilityUnavailable):
            RunnerProtocol(**options).admit(wire(command), now=NOW)
    with pytest.raises(CapabilityUnavailable, match="runner.executor"):
        protocol.dispatch(wire(command), now=NOW)


@pytest.mark.parametrize("mutation", ["extra", "fence_bool", "wrong_action", "null", "operation"])
def test_dto_and_operation_boundaries(setup, mutation):
    _, _, _, command, _, _, _, protocol = setup
    data = command.wire()
    if mutation == "extra":
        data["approved"] = True
    elif mutation == "fence_bool":
        data["fencing_token"] = True
    elif mutation == "wrong_action":
        data["parameters"]["action"] = "process.exec"
    elif mutation == "null":
        data["trusted_context"]["run_id"] = None
    else:
        data["operation_id"] = "op2"
    with pytest.raises((ValidationError, ContractViolation, DomainError)):
        protocol.admit(json.dumps(data), now=NOW)


def test_duplicate_json_keys_rejected(setup):
    protocol = setup[-1]
    with pytest.raises(ValueError, match="Duplicate"):
        protocol.admit('{"command_id":"one","command_id":"two"}', now=NOW)


def test_no_write_exec_even_with_trusted_policy_permission(setup):
    _, _, _, command, authority, _, _, protocol = setup
    data = command.wire()
    data["parameters"] = {
        "action": "file.write",
        "parameters": {
            "workspace_ref": authority.value.workspace_ref.wire(),
            "path": "source.txt",
            "text": "do not write",
            "create_only": False,
            "expected_content_hash": "a" * 64,
        },
    }
    changed = RunnerCommand.model_validate_json(json.dumps(data))
    authority.value = replace(
        authority.value,
        request_parameters=changed.wire()["parameters"],
        allowed_actions=frozenset({"file.write"}),
    )
    with pytest.raises(CapabilityUnavailable, match="D03"):
        protocol.admit(wire(changed), now=NOW)
    assert (setup[0] / "source.txt").read_text(encoding="utf-8") == "User original text 原文"


def failure_receipt(command):
    return {
        "command_id": command.command_id,
        "attempt_id": "a1",
        "kind": "failed",
        "usage": {
            "attempt_id": "a1",
            "resources": {
                "model_calls": 0,
                "tool_calls": 0,
                "child_agents": 0,
                "wall_time_ms": 0,
                "currency": "CNY",
            },
            "billing_state": "pending",
        },
        "signature": "TEST-ONLY",
        "failure": {
            "code": "dependency_unavailable",
            "category": "dependency",
            "message": "Executor unavailable",
            "retryable": False,
            "failed_phase": "dispatch",
        },
    }


def test_receipt_branches_identity_usage_and_signature(setup):
    _, _, _, command, _, signatures, _, protocol = setup
    receipt = failure_receipt(command)
    assert protocol.verify_receipt(json.dumps(receipt), command=command).kind == "failed"
    for field in ("attempt_id", "command_id"):
        bad = {**receipt, field: "wrong"}
        with pytest.raises(DomainError):
            protocol.verify_receipt(json.dumps(bad), command=command)
    bad = {**receipt, "usage": {**receipt["usage"], "attempt_id": "wrong"}}
    with pytest.raises(DomainError):
        protocol.verify_receipt(json.dumps(bad), command=command)
    bad = {**receipt, "wait_ref": command.request_ref.wire()}
    with pytest.raises(DomainError, match="branches"):
        protocol.verify_receipt(json.dumps(bad), command=command)
    signatures.valid = False
    with pytest.raises(DomainError, match="signature"):
        protocol.verify_receipt(json.dumps(receipt), command=command)
    for kind in ("ok", "waiting", "cancelled"):
        bad = {**receipt, "kind": kind}
        if kind == "cancelled":
            del bad["failure"]
        with pytest.raises((ValidationError, ContractViolation)):
            RunnerReceipt.model_validate(bad)


def test_root_mapping_change_cannot_reuse_command_identity(setup):
    _, _, bindings, command, authority, _, _, protocol = setup
    protocol.admit(wire(command), now=NOW)
    old = bindings.repository.get("r1")
    bindings.repository.add(replace(old, root_handle="r2"))
    authority.value = replace(authority.value, root_handle="r2")
    with pytest.raises(DomainError) as error:
        protocol.admit(wire(command), now=NOW)
    assert error.value.failure.code == "revision_conflict"


def test_list_admission_preserves_workspace_version(setup):
    _, _, _, command, authority, _, _, protocol = setup
    data = command.wire()
    data["parameters"] = {"action": "file.list", "parameters": {"workspace_id": "w1", "path": "."}}
    authority.value = replace(
        authority.value,
        request_parameters=data["parameters"],
        allowed_actions=frozenset({"file.list"}),
    )
    assert protocol.admit(json.dumps(data), now=NOW).state == "admitted"


def test_signed_receipt_success_waiting_cancellation_and_resource_match(setup):
    _, _, _, command, _, _, _, protocol = setup
    original = failure_receipt(command)
    receipt = {k: v for k, v in original.items() if k not in ("failure", "kind")}
    receipt.update(
        kind="ok",
        payload={
            "action": "file.read",
            "result": {
                "workspace_ref": command.wire()["parameters"]["parameters"]["workspace_ref"],
                "path": "source.txt",
                "encoding": "utf-8",
                "text": "fixture only 原文",
                "content_hash": "a" * 64,
                "location": {"kind": "whole"},
            },
        },
    )
    assert protocol.verify_receipt(json.dumps(receipt), command=command).kind == "ok"
    receipt["payload"]["result"]["workspace_ref"]["version"] = "stale"
    with pytest.raises(DomainError):
        protocol.verify_receipt(json.dumps(receipt), command=command)
    waiting = {k: v for k, v in original.items() if k != "failure"}
    waiting.update(kind="waiting", wait_ref=command.request_ref.wire())
    assert protocol.verify_receipt(json.dumps(waiting), command=command).kind == "waiting"
    cancelled = {**original, "kind": "cancelled"}
    with pytest.raises(DomainError):
        protocol.verify_receipt(json.dumps(cancelled), command=command)
    cancelled["failure"] = {**cancelled["failure"], "category": "cancelled", "code": "cancelled"}
    assert protocol.verify_receipt(json.dumps(cancelled), command=command).kind == "cancelled"
