"""Actual fresh-process SQL/blob result recovery; no executor in the new process."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

from tests.integration.tool.text_pipeline_fixture import (
    approved_pipeline,
)
from tests.integration.tool.text_pipeline_fixture import (
    text_pipeline as text_pipeline,
)
from uaw.tool.providers.text import inspect_text


async def test_text_new_process_recovers_saved_response_without_new_send(text_pipeline):
    p = await approved_pipeline(text_pipeline)
    original = p.executor.execute

    async def lost(*args):
        await original(*args)
        raise TimeoutError("Actual saved text response preceded controlled lost executor reply")

    p.executor.execute = lost
    first = await p.facade.invoke(p.raw, p.case.ctx)
    assert first["failure"]["code"] == "invocation_interrupted" and p.executor.calls == 1
    child = Path(__file__).with_name("text_recovery_child.py")
    request = json.dumps(
        {"context": p.case.ctx.wire(), "request": p.raw, "blob_directory": str(p.blob.directory)}
    )
    before = await p.case.budget.get_ledger(p.case.ctx)
    completed = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-m", "tests.integration.tool.text_recovery_child"],
        input=request,
        text=True,
        capture_output=True,
        timeout=60,
        cwd=child.parents[3],
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    actual = json.loads(completed.stdout)
    assert actual == {
        "kind": "ok",
        "outcome": "applied",
        "failure_code": None,
        "sha256": inspect_text(p.raw["arguments"]["text"])["sha256"],
    }
    after = await p.case.budget.get_ledger(p.case.ctx)
    assert before["held"]["tool_calls"] == 1 and after["used"]["tool_calls"] == 1
    assert after["held"]["tool_calls"] == 0 and p.executor.calls == 1
