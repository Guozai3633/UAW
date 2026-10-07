"""All adapters below are TEST DOUBLES; no real pairing or signing."""

import json
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from uaw.shared.contracts import JsonObject, Ref
from uaw.shared.errors import reject
from uaw.workspace.binding import RootBindings
from uaw.workspace.contracts import RootSelection, RunnerCommand
from uaw.workspace.ports import CommandAuthority, SelectedRoot
from uaw.workspace.repository import MemoryAdmissionRepository, MemoryRootRepository

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "apps/local_runner"))
from uaw_runner.protocol import RunnerProtocol  # noqa: E402

NOW = datetime(2026, 10, 7, 8, tzinfo=UTC)
EXPIRES = "2026-10-07T09:00:00Z"


class SelectionDouble:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.used = False

    def consume(
        self,
        selection: RootSelection,
        *,
        principal_id: str,
        device_id: str,
        now: datetime,
    ) -> SelectedRoot:
        if selection.selection_token != "native-test-token" or self.used:
            raise reject("permission_denied", "Selection proof rejected", 403, "permission")
        self.used = True
        return SelectedRoot(
            principal_id,
            device_id,
            selection.root_handle,
            self.root,
            frozenset({"read"}),
            datetime.fromisoformat(EXPIRES),
        )


class SignatureDouble:
    def __init__(self) -> None:
        self.valid = True
        self.seen: dict[str, object] = {}

    def verify_command(self, command: RunnerCommand, *, device_id: str) -> bool:
        self.seen = command.wire()
        return self.valid

    def verify_receipt(self, receipt: JsonObject, *, device_id: str) -> bool:
        return self.valid


class AuthorityDouble:
    def __init__(self, current: CommandAuthority) -> None:
        self.value = current

    def current(self, command: RunnerCommand) -> CommandAuthority:
        return self.value


@pytest.fixture
def setup(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "source.txt").write_text("User original text 原文", encoding="utf-8")
    workspace = Ref(kind="workspace", id="w1", version="v1")
    selection = RootSelection(
        selection_token="native-test-token",
        display_name="fixture",
        expires_at=EXPIRES,
        root_handle="r1",
    )
    native = SelectionDouble(root)
    bindings = RootBindings(MemoryRootRepository(), native)
    bindings.bind(
        selection,
        principal_id="u1",
        device_id="d1",
        workspace_ref=workspace,
        capabilities=frozenset({"read"}),
        now=NOW,
    )
    command = RunnerCommand.model_validate_json(
        json.dumps(
            {
                "command_id": "cmd1",
                "operation_id": "op1",
                "request_ref": {"kind": "artifact", "id": "req1", "version": "1"},
                "trusted_context": {
                    "principal": {"id": "u1", "kind": "user", "auth_session_id": "s1"},
                    "scope": {
                        "principal_id": "u1",
                        "resource_refs": [workspace.wire()],
                        "capabilities": ["fixture_read"],
                    },
                    "operation_id": "op1",
                    "trace_id": "t1",
                    "attempt_id": "a1",
                    "run_id": "run1",
                    "deadline": EXPIRES,
                    "capability_policy_ref": {"kind": "policy", "id": "p1", "version": "1"},
                    "model_policy_ref": {"kind": "policy", "id": "model1", "version": "1"},
                },
                "fencing_token": 4,
                "expires_at": EXPIRES,
                "signature": "TEST-ONLY",
                "parameters": {
                    "action": "file.read",
                    "parameters": {"workspace_ref": workspace.wire(), "path": "source.txt"},
                },
            }
        )
    )
    authority = AuthorityDouble(
        CommandAuthority(
            context=command.trusted_context,
            device_id="d1",
            root_handle="r1",
            workspace_ref=workspace,
            binding_revision=0,
            fencing_token=4,
            lease_expires_at=datetime.fromisoformat(EXPIRES),
            request_ref=command.request_ref,
            request_parameters=command.wire()["parameters"],
            policy_ref=command.trusted_context.capability_policy_ref,
            required_scope_capability="fixture_read",
            allowed_actions=frozenset({"file.read"}),
            feature_enabled=True,
            connected=True,
            cancelled=False,
        )
    )
    signatures = SignatureDouble()
    admissions = MemoryAdmissionRepository()
    protocol = RunnerProtocol(
        device_id="d1",
        bindings=bindings,
        admissions=admissions,
        signatures=signatures,
        authority=authority,
    )
    return root, selection, bindings, command, authority, signatures, admissions, protocol


def wire(command: RunnerCommand) -> str:
    return json.dumps(command.wire(), ensure_ascii=False)


def change_authority(authority: AuthorityDouble, **changes: object) -> None:
    authority.value = replace(authority.value, **changes)
