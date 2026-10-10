"""Real hidden Windows child displays its own folder window, then CANCELS."""

import asyncio
import json
import os
import subprocess
import sys


async def test_hidden_child_own_initialized_folder_visible_and_closes(tmp_path):
    report = tmp_path / "visibility.json"
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(["apps/local_runner", "src", "."])
    child = await asyncio.to_thread(
        subprocess.Popen,
        [sys.executable, "-m", "tests.integration.runner.native_visibility_fixture", str(report)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    try:
        _, error = await asyncio.to_thread(child.communicate, timeout=12)
        assert child.returncode == 0, error.decode(errors="replace")
        observed = json.loads(report.read_text(encoding="utf-8"))
        assert observed == dict(
            human_approval="pending",
            automatic="cancel_only",
            displayed=True,
            visible=True,
            topmost=True,
            own_thread=True,
            failure_code="native_cancelled",
            window_closed=True,
        )
    finally:
        if child.poll() is None:
            child.kill()  # Only this test's owned Popen child.
            await asyncio.to_thread(child.wait, timeout=5)
