"""Actual Windows Credential Manager test; random namespace/handle, no insecure fallback."""

import json
import uuid
from datetime import UTC, datetime, timedelta

from uaw_runner.control_signing import ControlCommandSigner, ControlKeyBinding
from uaw_runner.keys import ProtectedSigner
from uaw_runner.state import LocalState

from uaw.infrastructure.credentials import WindowsCredentialStore
from uaw.shared.errors import DomainError
from uaw.shared.runner_signatures import VerificationKey


async def test_actual_windows_control_key_read_sign_reopen_and_cleanup(tmp_path):
    namespace = "D-MS-R2d-test-" + uuid.uuid4().hex
    handle = "control-" + uuid.uuid4().hex
    store = WindowsCredentialStore(namespace)
    state = LocalState(tmp_path / "keys.sqlite")
    protected = ProtectedSigner(state, store)
    attempted = False
    report = {
        "backend": "keyring.backends.Windows.WinVaultKeyring",
        "status": "not_verified",
        "namespace": namespace,
        "handle": handle,
        "cleaned": False,
    }
    report_path = tmp_path.parents[1] / "windows-control-receipt.json"
    try:
        try:
            await store.resolve(handle)
        except DomainError as exc:
            assert exc.failure.code == "credential_missing", "Actual Windows backend unavailable"
        else:
            raise AssertionError("Random test handle already exists; no credential modification")
        attempted = True  # Missing was proven in THIS random namespace before any write.
        public = await protected.provision_private(credential_handle=handle)
        state.register_key(VerificationKey("test-control", "test-device", public, "control"))
        assert "**********" in repr(await store.resolve(handle))
        adapter = ControlCommandSigner(
            (ControlKeyBinding("test-device", "test-control", handle),),
            directory=state,
            signer=protected,
        )
        expires = (datetime.now(UTC) + timedelta(minutes=5)).isoformat()
        draft = {
            "command_id": "os-test-command",
            "operation_id": "os-test-op",
            "request_ref": {"kind": "check", "id": "os-test-request", "version": "1"},
            "trusted_context": {
                "principal": {
                    "id": "test-owner",
                    "kind": "user",
                    "auth_session_id": "test-session",
                },
                "scope": {"principal_id": "test-owner"},
                "operation_id": "os-test-op",
                "trace_id": "test-trace",
                "attempt_id": "test-attempt",
                "deadline": expires,
                "capability_policy_ref": {"kind": "policy", "id": "test-policy", "version": "1"},
            },
            "fencing_token": 1,
            "expires_at": expires,
            "parameters": {
                "action": "file.list",
                "parameters": {"workspace_id": "test-workspace", "path": "."},
            },
        }
        command = await adapter.sign(draft, device_id="test-device")
        assert {k: v for k, v in command.items() if k != "signature"} == draft
        await adapter.verify(command, device_id="test-device")
        reopened = LocalState(state.path)
        second_store = WindowsCredentialStore(namespace)
        second = ControlCommandSigner(
            tuple(adapter.bindings.values()),
            directory=reopened,
            signer=ProtectedSigner(reopened, second_store),
        )
        await second.verify(command, device_id="test-device")
        await second.sign(draft, device_id="test-device")  # Re-read actual OS private handle.
        reopened.revoke_key("test-control", expected_revision=0)
        try:
            await second.verify(command, device_id="test-device")
        except DomainError:
            pass
        else:
            raise AssertionError("Revoked actual OS signing key was accepted")
        report["status"] = "passed"
    finally:
        if attempted:
            try:
                await store.resolve(handle)
            except DomainError as exc:
                if exc.failure.code != "credential_missing":
                    raise
            else:
                await store.delete(handle)
            try:
                await store.resolve(handle)
            except DomainError as exc:
                assert exc.failure.code == "credential_missing"
                report["cleaned"] = True
            else:
                raise AssertionError("Random OS credential cleanup failed")
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
