"""Protected installed selectors are strict, bounded and never caller approval."""

import json
from datetime import UTC, datetime

import pytest
from uaw_runner.ipc.windows_pipe import OsIdentity

from uaw.infrastructure.installed_helper import (
    HANDLE_ENV,
    NAMESPACE_ENV,
    InstalledHelperAssembly,
    InstalledLaunch,
)
from uaw.shared.errors import CapabilityUnavailable


def descriptor(tmp_path):
    return {
        "owner": {"id": "user-one", "kind": "user", "auth_session_id": "web-session-one"},
        "enrollment_id": "enrollment-one",
        "challenge_hash": "a" * 64,
        "device_id": "device-one",
        "device_key_id": "device-key-one",
        "device_credential_handle": "device-private-one",
        "state_directory": str(tmp_path.resolve()),
        "proof_pipe_name": "uaw-enroll-one",
        "settings_handle": "settings-one",
        "identity": {"pid": 10, "created": 100, "user_sid": "sid", "logon_sid": "logon"},
        "expires_at": "2026-10-10T12:00:00Z",
        "currency": "USD",
    }


@pytest.mark.parametrize(
    "change", ["approval", "naive", "relative", "boolean_pid", "currency", "owner", "hash"]
)
def test_installed_launch_rejects_untrusted_or_changed_shape(tmp_path, change):
    value = descriptor(tmp_path)
    if change == "approval":
        value["approved"] = True
    elif change == "naive":
        value["expires_at"] = "2026-10-10T12:00:00"
    elif change == "relative":
        value["state_directory"] = "relative"
    elif change == "boolean_pid":
        value["identity"]["pid"] = True
    elif change == "currency":
        value["currency"] = "A1X"
    elif change == "owner":
        value["owner"]["auth_session_id"] = "cli-session"
    else:
        value["challenge_hash"] = "not-a-hash"
    with pytest.raises(ValueError):
        InstalledLaunch.from_bytes(json.dumps(value).encode())


def test_installed_original_shape_retains_exact_instance_and_expiry(tmp_path):
    launch = InstalledLaunch.from_bytes(json.dumps(descriptor(tmp_path)).encode())
    assert launch.identity == OsIdentity(10, 100, "sid", "logon")
    assert launch.expires_at == datetime(2026, 10, 10, 12, tzinfo=UTC)
    assert launch.currency == "USD"


async def test_installed_missing_locator_does_not_allocate_or_retry(monkeypatch):
    monkeypatch.delenv(NAMESPACE_ENV, raising=False)
    monkeypatch.delenv(HANDLE_ENV, raising=False)
    factory = InstalledHelperAssembly()
    with pytest.raises(CapabilityUnavailable):
        await factory.create(OsIdentity(10, 100, "sid", "logon"))
    with pytest.raises(CapabilityUnavailable) as repeat:
        await factory.create(OsIdentity(10, 100, "sid", "logon"))
    assert "already_consumed" in repeat.value.failure.message
