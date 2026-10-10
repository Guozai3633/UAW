"""Controlled dialog thread verifies cleanup/code, never actual human approval."""

import asyncio
from datetime import UTC, datetime, timedelta
from threading import Event
from types import SimpleNamespace

import pytest

from uaw.infrastructure import enrollment_native
from uaw.infrastructure.enrollment_native import WindowsEnrollmentConfirmation
from uaw.shared.contracts import Principal
from uaw.shared.errors import DomainError
from uaw.shared.stores import StoreMissing


class ControlledConfirmation(WindowsEnrollmentConfirmation):
    async def checked(self, owner, key, control_proof):
        return {
            "device_id": "controlled-device",
            "expires_at": (datetime.now(UTC) + timedelta(minutes=1)).isoformat(),
        }


def setup(monkeypatch, timeout):
    entered, drained = Event(), Event()

    class ControlledDialog:
        def show(self, prompt, stopped, deadline):
            entered.set()
            assert stopped.wait(2), "Owning native cancellation must release its thread"
            drained.set()
            return None

    class Records:
        async def get(self, *args):
            raise StoreMissing()

        async def put(self, *args, **kwargs):
            raise AssertionError("No native journal after timeout/cancel")

    directory = object()
    service = SimpleNamespace(records=Records(), controller=object())
    signer = SimpleNamespace(directory=directory)
    monkeypatch.setattr(enrollment_native, "WindowsNativeDialog", ControlledDialog)
    confirmation = ControlledConfirmation(
        service,
        directory,
        signer,
        device_credential_handle="controlled-handle",
        timeout_seconds=timeout,
    )
    return confirmation, entered, drained


async def test_native_original_deadline_is_typed_and_thread_drained(monkeypatch):
    confirmation, entered, drained = setup(monkeypatch, 0.05)
    owner = Principal(id="controlled-user", kind="user", auth_session_id="controlled-session")
    with pytest.raises(DomainError) as error:
        await confirmation.confirm(owner, "controlled-enrollment", control_proof="controlled-proof")
    assert error.value.failure.code == "enrollment_native_timeout"
    assert error.value.failure.category == "timeout"
    assert error.value.status_code == 410
    assert entered.is_set() and drained.is_set() and not confirmation.busy


async def test_native_parent_cancel_remains_cancel_and_drains_owned_worker(monkeypatch):
    confirmation, entered, drained = setup(monkeypatch, 1)
    owner = Principal(id="controlled-user", kind="user", auth_session_id="controlled-session")
    task = asyncio.create_task(
        confirmation.confirm(owner, "controlled-enrollment", control_proof="controlled-proof")
    )
    assert await asyncio.to_thread(entered.wait, 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert drained.is_set() and not confirmation.busy
