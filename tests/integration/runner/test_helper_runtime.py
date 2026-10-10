"""Actual hidden device helper process, OS keys and IPC. A enrollment/UI are doubles."""

import asyncio
import json
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from uaw_runner.helper_process import HelperProcess
from uaw_runner.ipc.sessions import AuthenticatedPipeSession, IpcSigner, IpcSigningBinding
from uaw_runner.ipc.windows_pipe import WindowsApi, connect_pipe
from uaw_runner.keys import Ed25519SignatureAdapter
from uaw_runner.receipts import canonical, digest

from tests.integration.runner.ipc_fixture import FixturePeerRegistry
from tests.integration.runner.test_native_root_source import make_native_case
from tests.integration.runner.test_read_executor import configure
from tests.integration.runner.test_windows_ipc import ipc_case as _ipc_fixture
from uaw.shared.errors import DomainError

ipc_case = _ipc_fixture


def helper_environment(path):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(Path(sys.prefix) / "Lib/site-packages"),
            str(Path(__file__).parents[3] / "src"),
            str(Path(__file__).parents[3] / "apps/local_runner"),
            str(Path(__file__).parents[3]),
        ]
    )
    env["UAW_D_TEST_HELPER_INPUT"] = str(path)
    return env


async def prepare_helper(case, *, native=None, ui="typed-double"):
    if native is None:
        native = await make_native_case(
            case["tmp"],
            credentials=case["store"],
            device_handle=case["handles"][0],
            control_handle=case["handles"][1],
            existing_keys=case["keys"],
            defer_confirmation=True,
            clock_start=datetime.now(UTC),
        )
        native["tmp"] = case["tmp"]
        native["target"] = native["root"] / "file.txt"
        native["target"].write_bytes("helper 原文中😀\r\n".encode())
        await configure(native)
    path = case["tmp"] / ("helper-input-" + uuid.uuid4().hex + ".json")
    data = {
        **case["registry"],
        "temp": str(case["tmp"]),
        "device_handle": case["handles"][0],
        "client": case["entry"]("control", WindowsApi().current().__dict__),
        "command": native["command"].wire(),
        "command_ref": native["command_ref"].wire(),
        "workspace": native["workspace"].wire(),
        "ctx": native["ctx"].wire(),
        "authority": native["authority"].value,
        "ticket_id": native["ticket_id"],
        "code": native["issued"].verification_code,
        "proof": native["proof"],
        "ui": ui,
    }
    await asyncio.to_thread(path.write_text, canonical(data), encoding="utf-8")
    process = await HelperProcess.prepare(
        python=Path(sys._base_executable),
        assembly_module="tests.integration.runner.helper_fixture",
        environment=helper_environment(path),
    )
    # Trusted harness independently records actual child PID/creation; never from IPC body.
    data["server"] = case["entry"]("device", process.identity.__dict__)
    await asyncio.to_thread(path.write_text, canonical(data), encoding="utf-8")
    case.setdefault("helper_processes", []).append(process)
    return native, process, path


async def connect_helper(case, process, path, ready):
    identity = WindowsApi().current()
    pipe = await connect_pipe(name=ready["name"], logon_sid=identity.logon_sid)
    session = AuthenticatedPipeSession(
        pipe=pipe,
        registration=FixturePeerRegistry(path),
        directory=case["keys"],
        signer=IpcSigner(
            binding=IpcSigningBinding("d1", "control1", "control", case["handles"][1]),
            directory=case["keys"],
            credentials=case["store"],
        ),
    )
    case["sessions"].append(session)
    await session.handshake()
    connected = await process.event()
    assert (
        connected["event"] == "connected" and connected["channel_ref"] == session.channel_ref.wire()
    )
    return session


async def read_reply(case, process, session, native, kind="command"):
    await session.send(kind, {"command_ref": native["command_ref"].wire()})
    try:
        frame = await session.receive()
    except DomainError as exc:
        event = await process.event()
        raise AssertionError("Helper public failure event: " + canonical(event)) from exc
    assert frame["kind"] == "receipt"
    body = frame["body"]
    assert Ed25519SignatureAdapter(case["keys"]).verify_receipt(body["receipt"], device_id="d1")
    assert body["receipt_ref"]["content_hash"] == digest(body["receipt"])
    assert (await process.event())["receipt_ref"] == body["receipt_ref"]
    return body


async def test_real_hidden_helper_native_once_read_reconnect_recover_restart(ipc_case):
    case = ipc_case
    native, process, path = await prepare_helper(case)
    try:
        ready = await process.start()
        assert process.identity.pid != os.getpid()
        session = await connect_helper(case, process, path, ready)
        body = await read_reply(case, process, session, native)
        assert body["receipt"]["payload"]["result"]["text"] == "helper 原文中😀\r\n"
        assert native["state"].get(native["ticket_id"], now=datetime.now(UTC)).state == "consumed"
        assert str(native["root"]) not in canonical(body)
        oldref = session.channel_ref
        await session.close()
        ready = await process.event()
        assert ready["event"] == "ready"
        native["target"].unlink()
        data = json.loads(path.read_text(encoding="utf-8"))
        data["authority"]["cancelled"] = True
        path.write_text(canonical(data), encoding="utf-8")
        # Existing factory authority is checked from its owning source fixture on new process.
        await process.close()
        native, process, path = await prepare_helper(case, native=native)
        data = json.loads(path.read_text(encoding="utf-8"))
        data["authority"]["cancelled"] = True
        path.write_text(canonical(data), encoding="utf-8")
        ready = await process.start()
        session = await connect_helper(case, process, path, ready)
        assert session.channel_ref.wire() != oldref.wire()
        restored = await read_reply(case, process, session, native, kind="recover")
        assert restored == body and not native["target"].exists()
        case["report"]["helper"] = "actual_hidden_restart_original_signed_journal"
        case["report"]["human_approval"] = "pending_typed_ui_double"
    finally:
        for owned in case.get("helper_processes", []):
            await owned.close()
            assert owned.process.returncode is not None


@pytest.mark.parametrize("ui", ["actual-timeout"])
async def test_actual_native_helper_timeout_does_not_bind(ipc_case, ui):
    case = ipc_case
    native, process, path = await prepare_helper(case, ui=ui)
    try:
        session = await connect_helper(case, process, path, await process.start())
        event = await process.event()
        assert event["event"] == "failure" and event["code"] == "native_timeout"
        assert native["state"].get(native["ticket_id"], now=datetime.now(UTC)).state == "pending"
        await session.close()
    finally:
        await process.close()


async def test_missing_production_assembly_never_listens_and_closes(ipc_case):
    path = ipc_case["tmp"] / "not-used"
    process = await HelperProcess.prepare(
        python=Path(sys._base_executable),
        assembly_module="uaw_runner.helper_host",
        environment=helper_environment(path),
    )
    try:
        with pytest.raises(DomainError) as failure:
            await process.start()
        assert failure.value.failure.code in {
            "capability_unavailable",
            "dependency_protocol_invalid",
            "permission_denied",
        }
        assert process.closed
    finally:
        await process.close()
    assert process.process.returncode == 0


@pytest.mark.parametrize("change", ["owner", "key", "OS-create", "registration-revoked"])
async def test_hidden_helper_current_bootstrap_rejects_before_listener(ipc_case, change):
    case = ipc_case
    native, process, path = await prepare_helper(case)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if change == "owner":
            data["server"]["owner"]["auth_session_id"] = "changed"
        elif change == "key":
            case["keys"].revoke_key("device1", expected_revision=0)
        elif change == "OS-create":
            data["server"]["identity"]["created"] += 1
        else:
            data["revoked"] = True
        path.write_text(canonical(data), encoding="utf-8")
        # owner switch is a consistent new independent registration only if actor changes too;
        # here old actor explicitly differs, so it must fail before an OS listener.
        with pytest.raises(DomainError) as failure:
            await process.start()
        assert failure.value.failure.code in {
            "capability_unavailable",
            "dependency_protocol_invalid",
            "permission_denied",
        }
        assert process.closed
        assert native["state"].get(native["ticket_id"], now=datetime.now(UTC)).state == (
            "revoked" if change == "key" else "pending"
        )
    finally:
        await process.close()


async def test_helper_stop_pending_accept_and_pipe_can_no_longer_connect(ipc_case):
    native, process, path = await prepare_helper(ipc_case)
    ready = await process.start()
    await process.close()
    await process.close()
    with pytest.raises(DomainError):
        await connect_pipe(name=ready["name"], logon_sid=process.identity.logon_sid, timeout=0.1)
    assert process.process.returncode == 0


async def wait_consumed(native):
    async with asyncio.timeout(10):
        while True:
            ticket = await asyncio.to_thread(
                native["state"].get, native["ticket_id"], now=datetime.now(UTC)
            )
            if ticket.state == "consumed" and (native["tmp"] / "native-selected.json").exists():
                return
            await asyncio.sleep(0.02)


@pytest.mark.parametrize("operation", ["revoke", "bind-again", "repeat-select"])
async def test_helper_revoke_and_original_root_one_use_after_restart(ipc_case, operation):
    case = ipc_case
    native, process, path = await prepare_helper(case)
    try:
        session = await connect_helper(case, process, path, await process.start())
        await wait_consumed(native)
        source = await native["reader"].resolve(
            native["command_ref"], authenticated_principal=native["owners"].value
        )
        assert native["executions"].get(source, native["command_ref"]) is None
        await session.close()
        await process.close()
        native, process, path = await prepare_helper(case, native=native)
        data = json.loads(path.read_text(encoding="utf-8"))
        data["trusted_local_operation"] = operation
        path.write_text(canonical(data), encoding="utf-8")
        session = await connect_helper(case, process, path, await process.start())
        if operation == "revoke":
            async with asyncio.timeout(10):
                while not await asyncio.to_thread(  # noqa: ASYNC110 - bounded cross-process CAS polling
                    lambda: native["grants"].get("native-root1").revoked
                ):
                    await asyncio.sleep(0.02)
            await session.send("command", {"command_ref": native["command_ref"].wire()})
        event = await process.event()
        assert event["event"] == "failure"
        if operation == "revoke":
            assert event["code"] == "permission_denied"
        else:
            assert event["code"] in {"revision_conflict", "permission_denied"}
        assert native["target"].exists()
        assert native["executions"].get(source, native["command_ref"]) is None
        assert native["state"].get(native["ticket_id"], now=datetime.now(UTC)).state == "consumed"
    finally:
        for owned in case["helper_processes"]:
            await owned.close()


async def test_helper_unknown_recover_cannot_start_read(ipc_case):
    native, process, path = await prepare_helper(ipc_case)
    try:
        session = await connect_helper(ipc_case, process, path, await process.start())
        await wait_consumed(native)
        await session.send("recover", {"command_ref": native["command_ref"].wire()})
        event = await process.event()
        assert event["event"] == "failure" and event["code"] == "capability_unavailable"
        source = await native["reader"].resolve(
            native["command_ref"], authenticated_principal=native["owners"].value
        )
        assert native["executions"].get(source, native["command_ref"]) is None
        assert native["target"].exists()
    finally:
        await process.close()


async def test_two_hidden_helpers_concurrent_once_journal_no_new_read_on_recover(ipc_case):
    case = ipc_case
    native, process, path = await prepare_helper(case)
    try:
        session = await connect_helper(case, process, path, await process.start())
        await wait_consumed(native)
        await session.close()
        await process.close()
        clients = []
        for _ in range(2):
            native, owned, reg = await prepare_helper(case, native=native)
            session = await connect_helper(case, owned, reg, await owned.start())
            clients.append((owned, session))

        async def attempt(owned, session):
            await session.send("command", {"command_ref": native["command_ref"].wire()})
            try:
                frame = await session.receive()
                assert frame["kind"] == "receipt"
                await owned.event()
                return frame["body"]
            except DomainError:
                assert (await owned.event())["event"] == "failure"
                return None

        bodies = await asyncio.gather(*(attempt(*client) for client in clients))
        good = [b for b in bodies if b is not None]
        assert good
        assert all(b == good[0] for b in good)
        source = await native["reader"].resolve(
            native["command_ref"], authenticated_principal=native["owners"].value
        )
        original = native["executions"].get(source, native["command_ref"])
        assert original.receipt_ref.wire() == good[0]["receipt_ref"]
        assert (
            await native["journal"].read(
                original.receipt_ref, authenticated_principal=native["owners"].value
            )
        ).wire() == good[0]["receipt"]
        for owned, session in clients:
            await session.close()
            await owned.close()
        native["target"].unlink()
        native, owned, reg = await prepare_helper(case, native=native)
        session = await connect_helper(case, owned, reg, await owned.start())
        assert await read_reply(case, owned, session, native, "recover") == good[0]
    finally:
        for owned in case["helper_processes"]:
            await owned.close()


async def test_cancel_owner_closes_pending_event_and_actual_process(ipc_case):
    native, process, path = await prepare_helper(ipc_case)
    try:
        await process.start()
        pending = asyncio.create_task(process.event())
        await asyncio.sleep(0.05)
        pending.cancel()
        with pytest.raises(asyncio.CancelledError):
            await pending
        assert process.closed and process.process.returncode is not None
    finally:
        await process.close()


@pytest.mark.parametrize(
    "change", ["logout", "key-revoked", "workspace-version", "command-signature"]
)
async def test_current_sources_and_signature_changed_before_read_are_rejected(ipc_case, change):
    native, process, path = await prepare_helper(ipc_case)
    try:
        session = await connect_helper(ipc_case, process, path, await process.start())
        await wait_consumed(native)
        data = json.loads(path.read_text(encoding="utf-8"))
        if change == "logout":
            data["revoked"] = True
            path.write_text(canonical(data), encoding="utf-8")
        elif change == "key-revoked":
            native["state"].revoke_key("device1", expected_revision=0)
        else:
            await session.close()
            await process.close()
            native, process, path = await prepare_helper(ipc_case, native=native)
            data = json.loads(path.read_text(encoding="utf-8"))
            if change == "workspace-version":
                data["authority"]["workspace_ref"]["version"] = "2"
            else:
                signature = data["command"]["signature"]
                parts = signature.split(":")
                parts[-1] = ("A" if parts[-1][0] != "A" else "B") + parts[-1][1:]
                data["command"]["signature"] = ":".join(parts)
            path.write_text(canonical(data), encoding="utf-8")
            session = await connect_helper(ipc_case, process, path, await process.start())
        try:
            await session.send("command", {"command_ref": native["command_ref"].wire()})
        except DomainError:
            pass
        event = await process.event()
        assert event["event"] == "failure"

        # Actual strict fixed Ref/current root/signature checks rejected before journal claim.
        def count_attempts():
            with native["executions"].transaction() as db:
                return db.execute("SELECT count(*) FROM file_read_attempts").fetchone()[0]

        assert await asyncio.to_thread(count_attempts) == 0
        assert native["target"].exists()
    finally:
        for owned in ipc_case["helper_processes"]:
            await owned.close()


async def test_concurrent_close_waits_for_the_same_actual_process_cleanup(ipc_case):
    native, process, path = await prepare_helper(ipc_case)
    await process.start()
    await asyncio.gather(process.close(), process.close(), process.close())
    assert process.process.returncode == 0
    assert process.process.stdin.closed and process.process.stdout.closed
