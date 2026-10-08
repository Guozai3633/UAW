"""Actual new-process SQLite/Ed25519 checks, with an explicitly controlled command registry."""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from uaw_runner.receipts import digest
from uaw_runner.state import LocalState

from uaw.shared.runner_signatures import VerificationKey, sign
from uaw.workspace.contracts import RunnerCommand, RunnerReceipt

CHILD = Path(__file__).with_name("receipt_child.py")


@pytest.fixture
def process_case(tmp_path):
    control, device = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
    keys = LocalState(tmp_path / "keys.sqlite")
    keys.register_key(
        VerificationKey(
            "control-key", "device1", control.public_key().public_bytes_raw(), "control"
        )
    )
    keys.register_key(
        VerificationKey("device-key", "device1", device.public_key().public_bytes_raw(), "device")
    )
    owner = {"id": "owner1", "kind": "user", "auth_session_id": "source-session"}
    command = {
        "command_id": "command1",
        "operation_id": "operation1",
        "request_ref": {"kind": "artifact", "id": "request1", "version": "1"},
        "trusted_context": {
            "principal": owner,
            "scope": {"principal_id": "owner1"},
            "operation_id": "operation1",
            "trace_id": "trace1",
            "attempt_id": "original-attempt",
            "deadline": "2020-01-01T00:00:00Z",
            "run_id": "cancelled-run",
            "capability_policy_ref": {"kind": "policy", "id": "policy1", "version": "1"},
        },
        "fencing_token": 1,
        "expires_at": "2020-01-01T00:00:00Z",
        "signature": "pending",
        "parameters": {
            "action": "file.read",
            "parameters": {
                "workspace_ref": {"kind": "workspace", "id": "fixture-workspace", "version": "1"},
                "path": "fixture.txt",
            },
        },
    }
    command["signature"] = sign(
        command, control.private_bytes_raw(), "device1", "control-key", "command"
    )
    RunnerCommand.model_validate_json(json.dumps(command))
    ref = {
        "kind": "artifact",
        "id": "fixture-command",
        "version": "1",
        "content_hash": digest(command),
    }
    registry = {
        "command": command,
        "command_ref": ref,
        "device_id": "device1",
        "owner": owner,
        "channels": [owner],
        "revoked": False,
        "run_cancelled": True,
    }
    (tmp_path / "registry.json").write_text(json.dumps(registry), encoding="utf-8")
    receipt = {
        "command_id": "command1",
        "attempt_id": "original-attempt",
        "kind": "cancelled",
        "usage": {
            "attempt_id": "original-attempt",
            "billing_state": "pending",
            "resources": {"wall_time_ms": 42, "currency": "CNY"},
        },
        "failure": {
            "code": "cancelled",
            "category": "cancelled",
            "message": "Signed fixture only",
            "retryable": False,
            "failed_phase": "dispatch",
        },
        "signature": "pending",
    }
    receipt["signature"] = sign(
        receipt, device.private_bytes_raw(), "device1", "device-key", "receipt"
    )
    RunnerReceipt.model_validate_json(json.dumps(receipt))
    return tmp_path, owner, ref, receipt, device, keys


def input_file(case, name, **values):
    path = case[0] / name
    path.write_text(json.dumps({"actor": case[1], **values}), encoding="utf-8")
    return path


def start(case, operation, incoming):
    return subprocess.Popen(
        [sys.executable, str(CHILD), str(case[0]), operation, str(incoming)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=Path(__file__).resolve().parents[3],
    )


def finish(process):
    out, err = process.communicate(timeout=30)
    assert process.returncode == 0, err
    return json.loads(out)


def publish_input(case, name="publish.json", receipt=None):
    return input_file(case, name, command_ref=case[2], receipt_data=json.dumps(receipt or case[3]))


def test_six_processes_unique_commit_then_new_process_recovery(process_case):
    case = process_case
    incoming = publish_input(case)
    processes = [start(case, "publish", incoming) for _ in range(6)]
    results = [finish(p) for p in processes]
    assert all(result == results[0] for result in results)
    ref = results[0]["value"]
    assert ref["version"] == "1" and ref["content_hash"] == digest(case[3])
    with sqlite3.connect(case[0] / "journal.sqlite") as db:
        assert db.execute(
            "SELECT count(*),min(revision),max(revision) FROM terminal_receipts"
        ).fetchone() == (1, 1, 1)
    recovered = finish(start(case, "read", input_file(case, "read.json", receipt_ref=ref)))
    assert recovered["value"] == case[3]
    assert "money" not in recovered["value"]["usage"]["resources"]
    # Replay in another process returns the actual original Ref and original attempt.
    assert finish(start(case, "publish", incoming)) == results[0]


def test_concurrent_different_signed_terminal_has_one_winner(process_case):
    case = process_case
    changed = json.loads(json.dumps(case[3]))
    changed["failure"]["message"] = "Conflicting fixture"
    changed["signature"] = sign(
        changed, case[4].private_bytes_raw(), "device1", "device-key", "receipt"
    )
    processes = [
        start(case, "publish", publish_input(case, "first.json")),
        start(case, "publish", publish_input(case, "second.json", changed)),
    ]
    results = [finish(p) for p in processes]
    success = [r for r in results if "value" in r]
    assert len(success) == 1
    assert [r for r in results if "failure" in r] == [
        {"failure": "revision_conflict", "status": 409}
    ]
    result = finish(
        start(case, "read", input_file(case, "read.json", receipt_ref=success[0]["value"]))
    )
    assert result["value"] in (case[3], changed)


@pytest.mark.parametrize("revocation", ["key", "source", "channel"])
def test_new_process_rechecks_current_recovery_access(process_case, revocation):
    case = process_case
    ref = finish(start(case, "publish", publish_input(case)))["value"]
    if revocation == "key":
        case[5].revoke_key("device-key", expected_revision=0)
    else:
        registry_path = case[0] / "registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        if revocation == "source":
            registry["revoked"] = True
        else:
            registry["channels"] = []
        registry_path.write_text(json.dumps(registry), encoding="utf-8")
    result = finish(start(case, "read", input_file(case, "read.json", receipt_ref=ref)))
    assert result["status"] == 403
    with sqlite3.connect(case[0] / "journal.sqlite") as db:
        assert db.execute("SELECT count(*) FROM terminal_receipts").fetchone()[0] == 1
