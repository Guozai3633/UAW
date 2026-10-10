"""Opt-in real person temp-only helper acceptance. Default never opens a window.

A account/challenge/authority remain explicitly controlled; no production acceptance.
"""

import argparse
import asyncio
import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "apps/local_runner"))

from tests.integration.runner.test_helper_runtime import (  # noqa: E402
    connect_helper,
    prepare_helper,
    read_reply,
)
from tests.integration.runner.test_windows_ipc import ipc_case  # noqa: E402


async def run_human():
    artifacts = await asyncio.to_thread(Path("tests/.artifacts/D/MS-R2h").absolute)
    await asyncio.to_thread(artifacts.mkdir, parents=True, exist_ok=True)
    receipt = {
        "human_approval": "pending",
        "account_source": "controlled_test_ports_not_A_production",
        "helper": "actual_hidden_process",
        "cleaned": False,
    }
    with tempfile.TemporaryDirectory(prefix="human-", dir=artifacts) as temporary:
        path = Path(temporary)
        fixture = ipc_case.__wrapped__(path)
        case = await anext(fixture)
        try:
            native, process, registration = await prepare_helper(case, ui="human")
            print("仅请选择本轮自有临时根：" + str(native["root"]), flush=True)
            print("窗口账号 u1/s1、设备 d1 为受控测试来源；不是生产账号 bootstrap。", flush=True)
            ready = await process.start()
            session = await connect_helper(case, process, registration, ready)
            # No automated mouse/key approval. Only original durable native result is observed.
            async with asyncio.timeout(55):
                while True:
                    ticket = await asyncio.to_thread(
                        native["state"].get, native["ticket_id"], now=datetime.now(UTC)
                    )
                    if ticket.state == "consumed":
                        break
                    if process.process.poll() is not None:
                        raise RuntimeError("Helper closed; no approval")
                    await asyncio.sleep(0.1)
            body = await read_reply(case, process, session, native)
            receipt.update(
                human_approval="actual_person_confirmed",
                receipt_ref=body["receipt_ref"],
                result_kind=body["receipt"]["kind"],
                production_bootstrap="pending",
            )
            await session.close()
            await process.close()
            # Revocation must use a current trusted local native facade, not a boolean.
            native, process, registration = await prepare_helper(case, native=native)
            data = json.loads(registration.read_text(encoding="utf-8"))
            data["trusted_local_operation"] = "revoke"
            registration.write_text(json.dumps(data), encoding="utf-8")
            session = await connect_helper(case, process, registration, await process.start())
            async with asyncio.timeout(10):
                while not await asyncio.to_thread(  # noqa: ASYNC110 - bounded cross-process CAS polling
                    lambda: native["grants"].get("native-root1").revoked
                ):
                    await asyncio.sleep(0.1)
            receipt["revoked"] = True
        finally:
            for owned in case.get("helper_processes", []):
                await owned.close()
            await fixture.aclose()
            receipt["cleaned"] = case["report"]["cleaned"]
            (artifacts / "human-helper-receipt.json").write_text(
                json.dumps(receipt, indent=2), encoding="utf-8"
            )
    print(json.dumps(receipt), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-human", action="store_true")
    args = parser.parse_args()
    if not args.run_human:
        print("pending: 未执行本人选择确认；A 生产 bootstrap 来源仍待接线。")
        return
    asyncio.run(run_human())


if __name__ == "__main__":
    main()
