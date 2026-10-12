"""A native observation coalesces worker waits, not live reads or permission checks."""

import threading
from types import SimpleNamespace

import pytest
from uaw_runner.ipc.windows_pipe import OsIdentity

from uaw.infrastructure import enrollment_peers as peers
from uaw.shared.errors import DomainError
from uaw.shared.runner_signatures import VerificationKey


def sources(monkeypatch, *, process_failure=False, key_failure=False):
    calls = []
    identity = OsIdentity(100, 200, "user", "logon")
    current = [VerificationKey("role-key", "device", b"a" * 32, "device")]
    closed = []

    class Api:
        def __init__(self):
            self.k = SimpleNamespace(CloseHandle=lambda handle: closed.append(handle))

        def process(self, pid):
            calls.append(("process", threading.get_ident()))
            assert pid == identity.pid
            if process_failure:
                raise OSError("test process absent")
            return 123, identity

    def lookup(key_id, *, device_id):
        calls.append(("key", threading.get_ident()))
        assert closed and key_id == "role-key" and device_id == "device"
        if key_failure:
            raise OSError("test key absent")
        return current[0]

    monkeypatch.setattr(peers, "WindowsApi", Api)
    return SimpleNamespace(lookup=lookup), identity, current, calls, closed


async def test_native_observations_are_fresh_ordered_and_one_worker(monkeypatch):
    directory, identity, current, calls, closed = sources(monkeypatch)
    first = await peers.observe_windows_role(
        directory, pid=identity.pid, key_id="role-key", device_id="device"
    )
    current[0] = VerificationKey("role-key", "device", b"a" * 32, "device", True)
    second = await peers.observe_windows_role(
        directory, pid=identity.pid, key_id="role-key", device_id="device"
    )
    assert first[0] == second[0] == identity
    assert not first[1].revoked and second[1].revoked
    assert [c[0] for c in calls] == ["process", "key", "process", "key"]
    assert calls[0][1] == calls[1][1] != threading.get_ident()
    assert calls[2][1] == calls[3][1] != threading.get_ident()
    assert closed == [123, 123]


@pytest.mark.parametrize("failure", ["process", "key"])
async def test_failed_observation_closes_handles_and_never_returns_permission(monkeypatch, failure):
    directory, identity, _, calls, closed = sources(
        monkeypatch, process_failure=failure == "process", key_failure=failure == "key"
    )
    with pytest.raises(DomainError if failure == "process" else OSError) as denied:
        await peers.observe_windows_role(
            directory, pid=identity.pid, key_id="role-key", device_id="device"
        )
    if failure == "process":
        assert denied.value.failure.code == "enrolled_os_instance_unavailable"
        assert not closed and len(calls) == 1
    else:
        assert closed == [123] and len(calls) == 2


async def test_custom_async_observer_retains_original_independent_waits(monkeypatch):
    directory, identity, _, calls, closed = sources(monkeypatch)
    closed.append(123)  # Custom provider owns its own OS observation lifecycle.

    async def observe(pid):
        assert pid == identity.pid
        calls.append(("custom", threading.get_ident()))
        return identity

    registry = peers.EnrolledPeerRegistry(
        SimpleNamespace(),
        owner=SimpleNamespace(),
        enrollment_id="enrollment",
        directory=directory,
        observe=observe,
    )
    result = await registry._role_observation(
        {"identity": {"pid": identity.pid}, "key_id": "role-key"}, device_id="device"
    )
    assert result[0] == identity and [v[0] for v in calls] == ["custom", "key"]
    assert calls[0][1] == threading.get_ident() != calls[1][1]
