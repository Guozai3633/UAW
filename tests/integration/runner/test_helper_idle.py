"""Real Windows child idle/stop boundaries; registration/native decisions are fixtures."""

import asyncio
import ctypes
import sqlite3
import struct
import time

import pytest

from tests.integration.runner.test_helper_runtime import connect_helper, prepare_helper, read_reply
from tests.integration.runner.test_windows_ipc import ipc_case as ipc_case
from uaw.shared.errors import DomainError


async def test_actual_helper_idle_longer_than_frame_limit_then_one_signed_read(ipc_case):
    case = ipc_case
    native, process, path = await prepare_helper(case)
    try:
        ready = await process.start()
        session = await connect_helper(case, process, path, ready)
        await asyncio.sleep(10.2)
        assert process.process.poll() is None
        await session.check()
        body = await read_reply(case, process, session, native)
        assert body["receipt"]["kind"] == "ok"
        await session.close()
        assert (await process.event())["event"] == "ready"
    finally:
        await process.close()


async def test_actual_helper_stop_during_idle_has_no_read_journal(ipc_case):
    case = ipc_case
    native, process, path = await prepare_helper(case)
    try:
        ready = await process.start()
        await connect_helper(case, process, path, ready)
        await asyncio.sleep(0.1)
        await process.close()
        await process.close()
        assert process.process.poll() is not None

        def count():
            path = case["tmp"] / "receipts.sqlite"
            if not path.exists():
                return 0
            with sqlite3.connect(path) as db:
                return db.execute("SELECT count(*) FROM terminal_receipts").fetchone()[0]

        assert await asyncio.to_thread(count) == 0
    finally:
        await process.close()


@pytest.mark.parametrize("mode", ["partial", "overlong"])
async def test_first_byte_keeps_original_frame_limit_and_no_read(ipc_case, mode):
    case = ipc_case
    native, process, path = await prepare_helper(case)
    try:
        ready = await process.start()
        session = await connect_helper(case, process, path, ready)
        await asyncio.sleep(0.2)
        raw = b"\x00" if mode == "partial" else struct.pack("!I", 256 * 1024 + 1)
        buffer = ctypes.create_string_buffer(raw)
        started = time.monotonic()
        await session.pipe.operation(
            session.pipe.overlapped, "write", buffer, len(raw), session.pipe.deadline(None)
        )
        event = await process.event(deadline=asyncio.get_running_loop().time() + 12)
        assert event == {
            "event": "failure",
            "code": "ipc_timeout" if mode == "partial" else "ipc_frame_invalid",
        }
        assert time.monotonic() - started < 11.5
        assert not (case["tmp"] / "receipts.sqlite").exists()
        with pytest.raises(DomainError):
            await session.check()
    finally:
        await process.close()
