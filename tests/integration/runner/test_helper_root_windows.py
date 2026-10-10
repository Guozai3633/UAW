"""Real hidden Windows helper/IPC/keys/temp file; root affirmative UI/account are doubles."""

import asyncio
import json
from datetime import UTC, datetime, timedelta

import pytest
from uaw_runner.receipts import canonical

from tests.integration.runner.test_helper_runtime import (
    connect_helper,
    prepare_helper,
    read_reply,
    wait_consumed,
)
from tests.integration.runner.test_windows_ipc import ipc_case as _ipc_fixture
from uaw.shared.errors import DomainError

ipc_case = _ipc_fixture


async def prepare_window(
    case,
    *,
    seconds=120,
    native=None,
    ui="typed-double",
    short_registration=None,
    ticket_expires_at=None,
):
    native, process, path = await prepare_helper(
        case, native=native, ui=ui, ticket_expires_at=ticket_expires_at
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    data["observe_helper_windows"] = True
    data["helper_windows"] = (
        {}
        if seconds is None
        else dict(session_lifetime_seconds=seconds, native_timeout_seconds=seconds)
    )
    if short_registration is not None:
        data["server"]["expires_at"] = short_registration.isoformat()
    path.write_text(canonical(data), encoding="utf-8")
    return native, process, path


async def record(case):
    async with asyncio.timeout(8):
        while True:
            path = case["tmp"] / "helper-windows.json"
            if path.exists():
                try:
                    value = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    value = {}  # Observation may race the test worker's write.
                if "prompt_expires_at" in value:
                    return value
            await asyncio.sleep(0.02)


@pytest.mark.parametrize("seconds", [None, 120])
async def test_real_helper_default_and_120_native_session_injection(ipc_case, seconds):
    case = ipc_case
    native, process, path = await prepare_window(case, seconds=seconds)
    try:
        session = await connect_helper(
            case,
            process,
            path,
            await process.start(),
            lifetime_seconds=60 if seconds is None else seconds,
        )
        body = await read_reply(case, process, session, native)
        value = await record(case)
        limit = 60 if seconds is None else seconds
        assert value["session_lifetime"] == value["native_timeout"] == limit
        expiry = datetime.fromisoformat(value["session_expires_at"])
        assert 30 < (expiry - datetime.now(UTC)).total_seconds() <= limit
        if seconds == 120:
            assert (expiry - datetime.now(UTC)).total_seconds() > 90
        assert datetime.fromisoformat(value["prompt_expires_at"]) <= expiry
        assert body["receipt"]["kind"] == "ok"
    finally:
        await process.close()
    assert process.process.returncode == 0


async def test_short_current_registration_caps_120_and_expired_read_denied(ipc_case):
    case = ipc_case
    # New explicit registration only; no old source/authorization extended.
    until = datetime.now(UTC) + timedelta(seconds=8)
    native, process, path = await prepare_window(case, short_registration=until)
    try:
        session = await connect_helper(
            case, process, path, await process.start(), lifetime_seconds=120
        )
        value = await record(case)
        assert datetime.fromisoformat(value["session_expires_at"]) == until
        assert datetime.fromisoformat(value["prompt_expires_at"]) <= until
        await asyncio.sleep(max(0, (until - datetime.now(UTC)).total_seconds()) + 0.1)
        with pytest.raises(DomainError):
            await session.check()
        with native["executions"].transaction() as db:
            assert db.execute("SELECT count(*) FROM file_read_attempts").fetchone()[0] == 0
    finally:
        await process.close()


async def test_short_original_ticket_caps_prompt_and_root_on_120_channel(ipc_case):
    case = ipc_case
    until = datetime.now(UTC) + timedelta(seconds=8)
    native, process, path = await prepare_window(case, ticket_expires_at=until)
    try:
        session = await connect_helper(
            case, process, path, await process.start(), lifetime_seconds=120
        )
        value = await record(case)
        assert datetime.fromisoformat(value["prompt_expires_at"]) == until
        assert datetime.fromisoformat(value["session_expires_at"]) > until
        await wait_consumed(native)
        grant = native["grants"].get("native-root1")
        assert grant.expires_at == until and grant.confirmation_expires_at <= until
        await asyncio.sleep(max(0, (until - datetime.now(UTC)).total_seconds()) + 0.1)
        await session.send("command", {"command_ref": native["command_ref"].wire()})
        event = await process.event()
        assert event["event"] == "failure"
        with native["executions"].transaction() as db:
            assert db.execute("SELECT count(*) FROM file_read_attempts").fetchone()[0] == 0
    finally:
        await process.close()


async def test_cancel_actual_native_on_120_helper_closes_own_window_without_grant(ipc_case):
    case = ipc_case
    native, process, path = await prepare_window(case, ui="actual-wait")
    try:
        await connect_helper(case, process, path, await process.start(), lifetime_seconds=120)
        async with asyncio.timeout(8):
            while not (case["tmp"] / "helper-windows.json").exists():  # noqa: ASYNC110
                await asyncio.sleep(0.02)
        await asyncio.sleep(0.2)
        await asyncio.gather(process.close(), process.close())
        assert native["state"].get(native["ticket_id"], now=datetime.now(UTC)).state == "pending"
        assert not (case["tmp"] / "native-selected.json").exists()
    finally:
        await process.close()
    assert process.process.returncode == 0


async def test_120_restart_recover_original_signature_without_extending_grant(ipc_case):
    case = ipc_case
    native, process, path = await prepare_window(case)
    try:
        session = await connect_helper(
            case, process, path, await process.start(), lifetime_seconds=120
        )
        original = await read_reply(case, process, session, native)
        grant = native["grants"].get("native-root1")
        await session.close()
        await process.close()
        native["target"].unlink()
        native, second, reg = await prepare_window(case, native=native)
        connected = await connect_helper(
            case, second, reg, await second.start(), lifetime_seconds=120
        )
        assert connected.channel_ref != session.channel_ref
        assert await read_reply(case, second, connected, native, "recover") == original
        restored = native["grants"].get("native-root1")
        assert restored.expires_at == grant.expires_at
        assert restored.confirmation_expires_at == grant.confirmation_expires_at
        with native["executions"].transaction() as db:
            assert db.execute("SELECT count(*) FROM file_read_attempts").fetchone()[0] == 1
    finally:
        for owned in case["helper_processes"]:
            await owned.close()
