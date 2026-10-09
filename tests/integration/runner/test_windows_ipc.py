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
        report["status"] = "passed"
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
            (tmp_path.parents[1] / ("windows-ipc-" + tmp_path.name + ".json")).write_text,
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
    await asyncio.to_thread(process.wait, timeout=5)
    assert not await asyncio.to_thread(session.pipe.live_sync)
    await session.close()
    await session.close()
    assert session.pipe.closed.is_set()
