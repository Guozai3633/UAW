"""Opt-in HUMAN temp-root acceptance harness, NOT production account pairing.

Run from D worktree only with --run-human. No automatic affirmative click.
"""

import argparse
import asyncio
import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "apps/local_runner"))

from tests.integration.runner.test_native_authorization import (  # noqa: E402
    lifecycle_setup,
    read_native,
    select,
)
from tests.integration.runner.test_windows_ipc import ipc_case  # noqa: E402
from tests.integration.runner.test_windows_read_ipc import child_result  # noqa: E402


async def run() -> None:
    artifacts = await asyncio.to_thread(Path("tests/.artifacts/D/MS-R2g").absolute)
    await asyncio.to_thread(artifacts.mkdir, parents=True, exist_ok=True)
    report = {"human": "pending", "registration": "controlled_temp_account_not_production_pairing"}
    try:
        with tempfile.TemporaryDirectory(prefix="manual-", dir=artifacts) as folder:
            temp = Path(folder)
            fixture = ipc_case.__wrapped__(temp)
            case = await anext(fixture)
            try:
                native = await lifecycle_setup(case, clock_start=datetime.now(UTC))
                print("本人请选择唯一临时测试根：" + str(native["root"]), flush=True)
                print(
                    "只读临时验收，账号 u1 / 设备 d1 为独立测试登记，不是真实生产配对。", flush=True
                )
                selection = await select(native)
                ticket = await asyncio.to_thread(
                    native["state"].get, native["ticket_id"], now=datetime.now(UTC)
                )
                actual = await asyncio.to_thread(native["local"].current, ticket)
                if actual != native["root"]:
                    raise ValueError(
                        "Only the harness temporary root may be bound; no user files read"
                    )
                await native["lifecycle"].bind(selection, native["workspace"])
                endpoint, process, registry = await read_native(native, case)
                try:
                    receipt_ref = await endpoint.serve_once()
                    receipt = await child_result(process)
                    assert (
                        receipt["receipt"]["payload"]["result"]["text"]
                        == "Native selected read 原文\r\n"
                    )
                    report.update(
                        human="actual_click_completed",
                        receipt_ref=receipt_ref.wire(),
                        kind=receipt["receipt"]["kind"],
                    )
                    await native["lifecycle"].revoke("native-root1", expected_revision=0)
                    report["revoked"] = True
                finally:
                    await registry.close()
                    await native["registry"].close()
            finally:
                await fixture.aclose()
                report["random_credentials_cleaned"] = case["report"]["cleaned"]
    except Exception as exc:
        report.update(human="not_passed", failure_type=type(exc).__name__)
        raise
    finally:
        report["timestamp"] = datetime.now(UTC).isoformat()
        await asyncio.to_thread(
            (artifacts / "human-native-receipt.json").write_text,
            json.dumps(report, indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-human", action="store_true")
    options = parser.parse_args()
    if not options.run_human:
        parser.exit(
            message="pending: requires --run-human and actual personal selection/confirmation\n"
        )
    asyncio.run(run())
