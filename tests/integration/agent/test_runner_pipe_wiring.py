"""Actual OS signed read + A verification; native account confirmation remains fixture."""

import asyncio
import copy
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from uaw_runner.ipc.channel_source import ConnectionRegistry
from uaw_runner.ipc.read_endpoint import ReadOnlyPipeEndpoint
from uaw_runner.ipc.sessions import AuthenticatedPipeSession, IpcSigner, IpcSigningBinding
from uaw_runner.ipc.windows_pipe import WindowsApi, WindowsPipeListener
from uaw_runner.keys import Ed25519SignatureAdapter

from tests.integration.runner.ipc_fixture import FixturePeerRegistry
from tests.integration.runner.test_windows_ipc import ipc_case as ipc_case
from tests.integration.runner.test_windows_read_ipc import (
    FixtureAssembly,
    child_result,
    endpoint_setup,
    read_setup,
)
from uaw.infrastructure.runner_pipe import digest, verify_receipt_body
from uaw.shared.errors import DomainError


async def test_a_verifies_actual_two_process_read_and_rejects_transport_tampering(ipc_case):
    native = await read_setup(ipc_case)
    endpoint, process, registry = await endpoint_setup(ipc_case, native)
    try:
        ref = await endpoint.serve_once()
        body = await child_result(process)
        source = await native["reader"].resolve(
            native["command_ref"], authenticated_principal=native["owners"].value
        )
        signatures = Ed25519SignatureAdapter(ipc_case["keys"])
        actual = verify_receipt_body(body, source, native["command_ref"], signatures)
        assert actual.receipt_ref == ref
        assert actual.receipt.payload["result"]["text"] == "actual IPC 中😀\n"
        for field in ("command_ref", "receipt_ref", "receipt"):
            changed = copy.deepcopy(body)
            if field == "receipt":
                changed[field]["attempt_id"] = "another-attempt"
                changed["receipt_ref"]["content_hash"] = digest(changed[field])
            else:
                changed[field]["content_hash"] = "0" * 64
            with pytest.raises(DomainError):
                verify_receipt_body(changed, source, native["command_ref"], signatures)
        changed = copy.deepcopy(body)
        changed["receipt_ref"]["id"] = "another-journal-row"
        with pytest.raises(DomainError):
            verify_receipt_body(changed, source, native["command_ref"], signatures)
        changed = copy.deepcopy(body)
        changed["approved"] = True
        with pytest.raises(DomainError):
            verify_receipt_body(changed, source, native["command_ref"], signatures)
    finally:
        await registry.close()


async def test_actual_a_control_client_to_independent_d_read_endpoint(ipc_case):
    """Actual OS/vault/signature/read; UAW account and root confirmation remain fixtures."""
    case = ipc_case
    native = await read_setup(case)
    name = "uaw-A-control-test-" + uuid.uuid4().hex
    listener = WindowsPipeListener(name=name, logon_sid=WindowsApi().current().logon_sid)
    case["listeners"].append(listener)
    data = {**case["registry"], "pipe": name, "command_snapshot": native["command"].wire()}
    path = case["tmp"] / (name + ".json")
    path.write_text(json.dumps(data), encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = (
        str(Path(sys.prefix) / "Lib/site-packages")
        + os.pathsep
        + str(Path(__file__).parents[3] / "src")
    )
    process = await asyncio.to_thread(
        subprocess.Popen,
        [sys._base_executable, str(Path(__file__).with_name("runner_control_peer.py")), str(path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        creationflags=subprocess.CREATE_NO_WINDOW,
        env=env,
    )
    case["processes"].append(process)
    identity = (await child_result(process))["identity"]
    assert identity["pid"] == process.pid and process.pid != data["server"]["identity"]["pid"]
    data["client"] = case["entry"]("control", identity)
    path.write_text(json.dumps(data), encoding="utf-8")
    process.stdin.write("go\n")
    process.stdin.flush()
    session = AuthenticatedPipeSession(
        pipe=await listener.accept(),
        registration=FixturePeerRegistry(path),
        directory=case["keys"],
        signer=IpcSigner(
            binding=IpcSigningBinding("d1", "device1", "device", case["handles"][0]),
            directory=case["keys"],
            credentials=case["store"],
        ),
    )
    case["sessions"].append(session)
    registry = ConnectionRegistry()
    try:
        await session.handshake()
        await registry.add(session)
        endpoint = ReadOnlyPipeEndpoint(
            session=session,
            registry=registry,
            commands=native["reader"],
            runners=FixtureAssembly(native, registry),
        )
        expected = await endpoint.serve_once()
        actual = await child_result(process)
        assert actual["receipt_ref"] == expected.wire()
        assert actual["receipt"]["payload"]["result"]["text"] == "actual IPC 中😀\n"
        process.stdin.write("close\n")
        process.stdin.flush()
        await asyncio.to_thread(process.wait, timeout=5)
        assert process.returncode == 0
    finally:
        await registry.close()
