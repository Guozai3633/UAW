"""Actual Windows double process/OS vault/ACL. UAW pairing/account registry is fixture."""

import asyncio
import hashlib
import json
import subprocess
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from uaw_runner.ipc.sessions import AuthenticatedPipeSession, IpcSigner, IpcSigningBinding
from uaw_runner.ipc.windows_pipe import WindowsApi, WindowsPipeListener
from uaw_runner.keys import ProtectedSigner
from uaw_runner.receipts import canonical
from uaw_runner.state import LocalState

from tests.integration.runner.ipc_fixture import FixturePeerRegistry
from uaw.infrastructure.credentials import WindowsCredentialStore
from uaw.shared.errors import DomainError
from uaw.shared.runner_signatures import VerificationKey


@pytest.fixture
async def ipc_case(tmp_path):
    namespace = "D-MS-R2f-" + uuid.uuid4().hex
    handles = ["device-" + uuid.uuid4().hex, "control-" + uuid.uuid4().hex]
    store = WindowsCredentialStore(namespace)
    keys = LocalState(tmp_path / "keys.sqlite")
    protected = ProtectedSigner(keys, store)
    attempted = False
    processes = []
    listeners = []
    sessions = []
    report = {
        "backend": "WinVaultKeyring",
        "namespace": namespace,
        "status": "not_verified",
        "cleaned": False,
        "authorization": "controlled_registration_not_native_confirmation",
    }
    try:
        for handle in handles:
            try:
                await store.resolve(handle)
            except DomainError as exc:
                assert exc.failure.code == "credential_missing"
            else:
                raise AssertionError("Random credential exists; do not modify")
        attempted = True
        for key_id, handle, role in [
            ("device1", handles[0], "device"),
            ("control1", handles[1], "control"),
        ]:
            public = await protected.provision_private(credential_handle=handle)
            keys.register_key(VerificationKey(key_id, "d1", public, role))
        identity = WindowsApi().current()
        owner = {"id": "u1", "kind": "user", "auth_session_id": "s1"}
        pairing = {
            "kind": "content",
            "id": "fixture-pairing",
            "version": "1",
            "content_hash": "a" * 64,
        }

        def entry(role, osidentity):
            keyid = "device1" if role == "device" else "control1"
            return {
                "identity": osidentity,
                "owner": owner,
                "actor": owner,
                "device_id": "d1",
                "key_id": keyid,
                "key_ref": {
                    "kind": "content",
                    "id": keyid,
                    "version": "1",
                    "content_hash": hashlib.sha256(
                        keys.lookup(keyid, device_id="d1").public_bytes
                    ).hexdigest(),
                },
                "pairing_ref": pairing,
                "expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
            }

        case = dict(
            tmp=tmp_path,
            namespace=namespace,
            handles=handles,
            keys=keys,
            store=store,
            entry=entry,
            processes=processes,
            listeners=listeners,
            sessions=sessions,
            report=report,
            registry={
                "namespace": namespace,
                "control_handle": handles[1],
                "keys": str(keys.path),
                "server": entry("device", identity.__dict__),
                "client": None,
                "revoked": False,
            },
        )
        yield case
        report["status"] = "fixture_completed"
    finally:
        for session in sessions:
            await session.close()
        for listener in listeners:
            await listener.close()
        for process in processes:
            if process.poll() is None:
                process.terminate()
            await asyncio.to_thread(process.wait, timeout=5)
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream:
                    stream.close()
        if attempted:
            for handle in handles:
                try:
                    await store.resolve(handle)
                except DomainError as exc:
                    assert exc.failure.code == "credential_missing"
                else:
                    await store.delete(handle)
                try:
                    await store.resolve(handle)
                except DomainError as exc:
                    assert exc.failure.code == "credential_missing"
                else:
                    raise AssertionError("Random OS credential cleanup failed")
            report["cleaned"] = True
        await asyncio.to_thread(
            (
                tmp_path.parents[1] / ("windows-ipc-" + tmp_path.name + "-" + namespace + ".json")
            ).write_text,
            json.dumps(report, indent=2),
            encoding="utf-8",
        )


async def start_peer(case, mode="echo", *, timeout=10):  # noqa: ASYNC109 - OS frame deadline

    name = "uaw-D-test-" + uuid.uuid4().hex
    listener = WindowsPipeListener(
        name=name, logon_sid=WindowsApi().current().logon_sid, timeout=timeout
    )
    case["listeners"].append(listener)
    registry = case["registry"].copy()
    registry.update(pipe=name, timeout=timeout)
    path = case["tmp"] / (name + ".json")
    await asyncio.to_thread(path.write_text, canonical(registry), encoding="utf-8")
    import os

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = (
        str(Path(sys.prefix) / "Lib/site-packages")
        + os.pathsep
        + str(Path(__file__).parents[3] / "src")
    )
    process = await asyncio.to_thread(
        subprocess.Popen,
        [sys._base_executable, str(Path(__file__).with_name("ipc_child.py")), str(path), mode],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        creationflags=subprocess.CREATE_NO_WINDOW,
        env=env,
    )
    case["processes"].append(process)
    line = await asyncio.wait_for(asyncio.to_thread(process.stdout.readline), 5)
    child = json.loads(line)["identity"]
    assert child["pid"] == process.pid and child["pid"] != registry["server"]["identity"]["pid"]
    registry["client"] = case["entry"]("control", child)
    await asyncio.to_thread(path.write_text, canonical(registry), encoding="utf-8")
    process.stdin.write("go\n")
    process.stdin.flush()
    pipe = await listener.accept()
    session = AuthenticatedPipeSession(
        pipe=pipe,
        registration=FixturePeerRegistry(path),
        directory=case["keys"],
        signer=IpcSigner(
            binding=IpcSigningBinding("d1", "device1", "device", case["handles"][0]),
            directory=case["keys"],
            credentials=case["store"],
        ),
    )
    case["sessions"].append(session)
    return session, process, path


async def test_actual_windows_double_process_acl_os_identity_nonce_roles_and_close(ipc_case):
    case = ipc_case
    session, process, path = await start_peer(case)
    await session.handshake()
    assert session.peer.identity.pid == process.pid
    assert "D:P(A;;0x0012019B;;;S-1-5-5-" in case["listeners"][-1].sddl
    assert session.peer.identity.logon_sid == session.local.identity.logon_sid
    frame = await session.receive()
    assert frame["kind"] == "command" and frame["body"] == {"id": "test-message"}
    await session.send("receipt", {"id": "test-reply"})
    result = json.loads(await asyncio.wait_for(asyncio.to_thread(process.stdout.readline), 5))
    assert result["body"] == {"id": "test-reply"}
    assert result["channel_ref"] == session.channel_ref.wire()
    await asyncio.to_thread(process.wait, timeout=5)
    assert not await asyncio.to_thread(session.pipe.live_sync)
    await session.close()
    await session.close()
    assert session.pipe.closed.is_set()


async def ready_registry(case):
    from uaw_runner.ipc.channel_source import ConnectionRegistry

    session, process, path = await start_peer(case, "idle")
    await session.handshake()
    registry = ConnectionRegistry()
    ref = await registry.add(session)
    return session, process, path, registry, ref


async def test_real_channel_snapshot_independent_registration(ipc_case):
    session, process, path, registry, ref = await ready_registry(ipc_case)
    value = await registry.read(ref, device_id="d1")
    assert value["owner"] == session.local.owner.wire()
    assert value["actor"] == session.peer.actor.wire()
    assert value["key_ref"] == session.local.key_ref.wire()
    assert value["pairing_ref"] == session.local.pairing_ref.wire()
    assert value["channel_ref"] == ref.wire() and value["connected"]
    with pytest.raises(DomainError):
        await registry.read(ref, device_id="other-device")
    process.stdin.write("close\n")
    process.stdin.flush()
    await asyncio.to_thread(process.wait, timeout=5)
    with pytest.raises(DomainError):
        await registry.read(ref, device_id="d1")
    await registry.close()


@pytest.mark.parametrize(
    "change", ["owner", "actor", "key", "expiry", "revoked", "disconnect", "process_exit"]
)
async def test_live_source_invalidated_for_current_changes(ipc_case, change):
    session, process, path, registry, ref = await ready_registry(ipc_case)
    value = json.loads(await asyncio.to_thread(path.read_text, encoding="utf-8"))
    if change == "owner":
        value["client"]["owner"]["auth_session_id"] = "other-session"
    elif change == "actor":
        value["client"]["actor"]["id"] = "other-account"
    elif change == "expiry":
        session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    elif change == "revoked":
        value["revoked"] = True
    elif change == "key":
        ipc_case["keys"].revoke_key("control1", expected_revision=0)
    elif change == "disconnect":
        await session.close()
    elif change == "process_exit":
        process.terminate()
        await asyncio.to_thread(process.wait, timeout=5)
    await asyncio.to_thread(path.write_text, canonical(value), encoding="utf-8")
    with pytest.raises(DomainError):
        await registry.read(ref, device_id="d1")
    assert session.pipe.closed.is_set()


async def test_reconnect_new_ref_and_nonce_never_revives_old(ipc_case):
    first, process, path, registry, old_ref = await ready_registry(ipc_case)
    await first.close()
    second, new_process, new_path = await start_peer(ipc_case, "idle")
    await second.handshake()
    new_ref = await registry.add(second)
    assert new_ref.wire() != old_ref.wire() and second.nonce != first.nonce
    with pytest.raises(DomainError):
        await registry.read(old_ref, device_id="d1")
    assert (await registry.read(new_ref, device_id="d1"))["connected"]
    await registry.close()


@pytest.mark.parametrize("mode", ["bad-signature", "old-nonce", "replay"])
async def test_actual_peer_signature_nonce_and_replay_rejected(ipc_case, mode):
    session, process, path = await start_peer(ipc_case, mode)
    await session.handshake()
    if mode == "replay":
        await session.receive()
    with pytest.raises(DomainError) as exc:
        await session.receive()
    assert exc.value.failure.code == (
        "ipc_signature_denied" if mode == "bad-signature" else "ipc_replay"
    )
    assert session.pipe.closed.is_set()


@pytest.mark.parametrize("mode", ["raw-long", "raw-zero", "raw-truncated", "raw-silent"])
async def test_actual_pipe_invalid_length_truncation_and_timeout(ipc_case, mode):
    session, process, path = await start_peer(ipc_case, mode)
    session.pipe.timeout = 0.3
    with pytest.raises(DomainError) as exc:
        await session.handshake()
    if mode in {"raw-long", "raw-zero"}:
        assert exc.value.failure.code == "ipc_frame_invalid"
    elif mode == "raw-silent":
        assert exc.value.failure.code == "ipc_timeout"
    assert session.pipe.closed.is_set()


@pytest.mark.parametrize(
    "change", ["pid", "creation", "owner", "device", "key_role", "key_hash", "missing"]
)
async def test_os_peer_not_authenticated_by_untrusted_identity(ipc_case, change):
    session, process, path = await start_peer(ipc_case, "idle")
    value = json.loads(await asyncio.to_thread(path.read_text, encoding="utf-8"))
    if change == "pid":
        value["client"]["identity"]["pid"] += 999
    elif change == "creation":
        value["client"]["identity"]["created"] += 1
    elif change == "owner":
        value["client"]["owner"]["id"] = "another-owner"
        value["client"]["actor"]["id"] = "another-owner"
    elif change == "device":
        value["client"]["device_id"] = "another-device"
    elif change == "key_role":
        value["client"]["key_id"] = "device1"
        value["client"]["key_ref"] = value["server"]["key_ref"]
    elif change == "key_hash":
        value["client"]["key_ref"]["content_hash"] = "f" * 64
    elif change == "missing":
        session.registration = None
    await asyncio.to_thread(path.write_text, canonical(value), encoding="utf-8")
    session.pipe.timeout = 0.6
    with pytest.raises(DomainError):
        await session.handshake()
    assert session.pipe.closed.is_set()


async def test_actual_read_cancel_propagates_and_does_not_block_event_loop(ipc_case):
    session, process, path, registry, ref = await ready_registry(ipc_case)
    operation = asyncio.create_task(session.receive())
    await asyncio.sleep(0.05)
    with pytest.raises(DomainError) as exc:
        await session.receive()
    assert exc.value.failure.code == "ipc_busy"
    operation.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(operation, 1)
    assert session.pipe.closed.is_set() and session.pipe.handle is None
    await registry.close()


async def test_source_await_timeout_invalidates_actual_pipe(ipc_case):
    session, process, path, registry, ref = await ready_registry(ipc_case)
    original = session.registration

    class SlowRegistration:
        async def current(self, identity, *, role):
            await asyncio.sleep(5)
            return await original.current(identity, role=role)

    session.registration = SlowRegistration()
    session.pipe.timeout = 0.1
    with pytest.raises(DomainError) as exc:
        await registry.read(ref, device_id="d1")
    assert exc.value.failure.code == "ipc_timeout" and session.pipe.closed.is_set()
    await registry.close()


async def test_registry_bound_and_handshake_one_use(ipc_case):
    from uaw_runner.ipc.channel_source import ConnectionRegistry

    first, process, path, registry, ref = await ready_registry(ipc_case)
    with pytest.raises(DomainError):
        await first.handshake()
    bounded = ConnectionRegistry(max_connections=1)
    await bounded.add(first)
    second, process2, path2 = await start_peer(ipc_case, "idle")
    await second.handshake()
    with pytest.raises(DomainError) as exc:
        await bounded.add(second)
    assert exc.value.failure.code == "ipc_busy"
    await bounded.close()
    await second.close()


async def test_actual_kernel_pipe_dacl_has_only_explicit_logon_ace(ipc_case):
    import ctypes
    from ctypes import wintypes as W

    session, process, path, registry, ref = await ready_registry(ipc_case)
    api = session.pipe.api
    get_security = api.a.GetSecurityInfo
    get_security.argtypes = [W.HANDLE, ctypes.c_int, W.DWORD] + [ctypes.c_void_p] * 5
    get_security.restype = W.DWORD
    convert = api.a.ConvertSecurityDescriptorToStringSecurityDescriptorW
    convert.argtypes = [ctypes.c_void_p, W.DWORD, W.DWORD, ctypes.c_void_p, ctypes.c_void_p]
    convert.restype = W.BOOL
    descriptor, dacl, text = ctypes.c_void_p(), ctypes.c_void_p(), W.LPWSTR()
    try:
        assert (
            get_security(
                session.pipe.handle,
                6,
                4,
                None,
                None,
                ctypes.byref(dacl),
                None,
                ctypes.byref(descriptor),
            )
            == 0
        )
        assert convert(descriptor, 1, 4, ctypes.byref(text), None)
        actual = text.value
        assert actual.count("(A;") == 1 and session.local.identity.logon_sid in actual
        assert "0x12019b" in actual.lower() and ";;;WD)" not in actual and ";;;AN)" not in actual
    finally:
        if text:
            api.k.LocalFree(text)
        if descriptor:
            api.k.LocalFree(descriptor)
        await registry.close()


async def test_unconnected_listener_cancel_reaps_overlapped(ipc_case):
    listener = WindowsPipeListener(
        name="uaw-D-test-" + uuid.uuid4().hex, logon_sid=WindowsApi().current().logon_sid
    )
    ipc_case["listeners"].append(listener)
    work = asyncio.create_task(listener.accept())
    await asyncio.sleep(0.05)
    work.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(work, 1)
    assert listener.connection.closed.is_set() and listener.connection.handle is None


async def test_actual_expiry_during_current_source_await(ipc_case):
    import time

    session, process, path, registry, ref = await ready_registry(ipc_case)
    original = session.registration

    class SlowRegistration:
        async def current(self, identity, *, role):
            await asyncio.sleep(0.05)
            return await original.current(identity, role=role)

    session.registration = SlowRegistration()
    session.monotonic_expiry = time.monotonic() + 0.02
    with pytest.raises(DomainError) as exc:
        await registry.read(ref, device_id="d1")
    assert exc.value.failure.code == "ipc_timeout"
    await registry.close()


async def test_actual_exact_maximum_signed_frame(ipc_case):
    from uaw_runner.ipc.frames import encode
    from uaw_runner.ipc.windows_pipe import MAX_FRAME

    session, process, path = await start_peer(ipc_case, "max-frame")
    await session.handshake()
    frame = await session.receive()
    assert len(encode(frame)) == MAX_FRAME and frame["body"]["data"].startswith("xxx")
    await session.close()


async def test_repeated_cancellation_still_reaps_pipe_handles(ipc_case):
    session, process, path, registry, ref = await ready_registry(ipc_case)
    work = asyncio.create_task(session.receive())
    await asyncio.sleep(0.05)
    work.cancel()
    await asyncio.sleep(0)
    work.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(work, 1)
    assert session.pipe.handle is None and session.pipe.peer_handle is None
    await registry.close()
