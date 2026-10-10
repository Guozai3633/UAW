"""Controlled first-start timing factory; original root/owner/authority are fixtures.

Real hidden process, real OS credentials and IPC. Never production enrollment/UI Yes.
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from threading import Event

from uaw_runner.helper_host import HelperBootstrapProgress, emit
from uaw_runner.native_dialog import NativePrompt, WindowsNativeDialog

from tests.integration.runner.helper_fixture import assembly as paired_fixture
from uaw.shared.errors import reject
from uaw.shared.runner_bootstrap import FirstStartPolicy


class Factory:
    async def create(self, identity):
        path = Path(os.environ["UAW_D_TEST_HELPER_INPUT"])
        config = json.loads(await asyncio.to_thread(path.read_text, encoding="utf-8"))
        scenario = config["startup_fixture"]
        temp = Path(config["temp"])
        await asyncio.to_thread((temp / "factory-begun").touch)
        value = scenario["policy"]
        policy = FirstStartPolicy(
            datetime.fromisoformat(value["expires_at"]),
            value["challenge_hash"],
            value["wait_seconds"],
        )
        mode = scenario.get("mode", "valid")
        if mode != "no-progress":
            if mode in {"valid", "native", "deny", "late"}:
                await HelperBootstrapProgress().waiting(policy)
            else:
                fields = dict(
                    stage="enrollment",
                    expires_at=policy.expires_at.isoformat(),
                    challenge_hash=policy.challenge_hash,
                )
                if mode == "hash":
                    fields["challenge_hash"] = "b" * 64
                elif mode == "expiry":
                    fields["expires_at"] = "2000-01-01T00:00:00Z"
                elif mode == "stage":
                    fields["stage"] = "approved"
                elif mode == "extra":
                    fields["owner"] = "forbidden"
                if mode == "duplicate":
                    print('{"event":"bootstrap_waiting","event":"bootstrap_waiting"}', flush=True)
                elif mode == "oversize":
                    print("x" * 4096, flush=True)
                elif mode == "truncated":
                    print('{"event":"bootstrap_waiting"', end="", flush=True)
                    return await paired_fixture.create(identity)
                elif mode == "exit":
                    raise SystemExit(0)
                else:
                    emit("bootstrap_waiting", **fields)
                if mode == "repeat":
                    emit("bootstrap_waiting", **fields)
        try:
            if mode == "native":
                cancelled = Event()
                worker = asyncio.create_task(
                    asyncio.to_thread(
                        WindowsNativeDialog().show,
                        NativePrompt(
                            "controlled-u1",
                            "fixture-d1",
                            policy.expires_at.isoformat(),
                            policy.challenge_hash,
                            False,
                        ),
                        cancelled,
                        time.monotonic() + 60,
                    )
                )
                try:
                    await asyncio.shield(worker)
                finally:
                    cancelled.set()
                    await asyncio.gather(worker, return_exceptions=True)
                    await asyncio.to_thread((temp / "native-worker-drained").touch)
            else:
                await asyncio.sleep(scenario.get("delay", 0))
            if mode == "deny":
                raise reject("native_denied", "Controlled first confirmation refused", 403)
            return await paired_fixture.create(identity)
        except asyncio.CancelledError:
            await asyncio.to_thread((temp / "factory-cancelled").touch)
            if mode == "late":
                application = await paired_fixture.create(identity)
                close = application.helper.close

                async def record_close():
                    await close()
                    await asyncio.to_thread((temp / "late-helper-closed").touch)

                application.helper.close = record_close
                return application
            raise


assembly = Factory()
