"""Real Windows child idle/stop boundaries; registration/native decisions are fixtures."""

import asyncio
import sqlite3

from tests.integration.runner.test_helper_runtime import connect_helper, prepare_helper, read_reply
from tests.integration.runner.test_windows_ipc import ipc_case as ipc_case


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
