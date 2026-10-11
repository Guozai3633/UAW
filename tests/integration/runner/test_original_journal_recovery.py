"""Actual Windows keys/pipe/read/restart; native/authority are controlled test ports.

Not the A8 installed product chain or a human confirmation receipt.
"""

import asyncio
import json

from uaw_runner.helper_process import HelperProcess
from uaw_runner.receipts import canonical

from tests.integration.runner.test_helper_runtime import connect_helper, prepare_helper, read_reply
from tests.integration.runner.test_windows_ipc import ipc_case as ipc_case


async def test_reply_loss_changed_file_restart_original_snapshot_zero_new_open(
    ipc_case, monkeypatch
):
    case = ipc_case
    prepare = HelperProcess.prepare

    async def measured_prepare(**kwargs):
        assert kwargs["assembly_module"] == "tests.integration.runner.helper_fixture"
        kwargs["assembly_module"] = "tests.integration.runner.counted_recovery_child"
        return await prepare(**kwargs)

    monkeypatch.setattr(HelperProcess, "prepare", measured_prepare)
    native, process, path = await prepare_helper(case)
    try:
        ready = await process.start()
        original_session = await connect_helper(case, process, path, ready)
        sends = []

        async def exchange(session, kind):
            sends.append(kind)
            return await read_reply(case, process, session, native, kind=kind)

        # Fault is at the consuming adapter: actual signed reply has arrived, but
        # the application never accepts it. It must resolve the original journal.
        lost = await exchange(original_session, "command")
        assert lost["receipt"]["kind"] == "ok"
        await process.close()
        await asyncio.to_thread(
            native["target"].write_bytes, "changed after original reply 中".encode()
        )
        native, process, path = await prepare_helper(case, native=native)
        data = json.loads(await asyncio.to_thread(path.read_text, encoding="utf-8"))
        data["authority"]["cancelled"] = True
        await asyncio.to_thread(path.write_text, canonical(data), encoding="utf-8")
        ready = await process.start()
        fresh = await connect_helper(case, process, path, ready)
        assert fresh.channel_ref != original_session.channel_ref
        restored = await exchange(fresh, "recover")
        assert restored == lost
        assert restored["receipt"]["payload"]["result"]["text"] == "helper 原文中😀\r\n"
        assert int((case["tmp"] / "os-open-count.txt").read_text()) == 1
        assert sends == ["command", "recover"]
        case["report"]["recovery"] = "actual_restart_changed_file_original_signed_snapshot_one_open"
        case["report"]["authority"] = "controlled_cancelled_source_not_A8_installed"
    finally:
        for helper in case.get("helper_processes", []):
            await helper.close()
