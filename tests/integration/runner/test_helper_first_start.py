"""Actual hidden Windows host cancellation/timing; account/native Yes remain fixtures."""

import asyncio
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from uaw_runner.helper_process import HelperProcess
from uaw_runner.receipts import canonical

from tests.integration.runner.test_helper_runtime import helper_environment, prepare_helper
from tests.integration.runner.test_windows_ipc import ipc_case as _ipc_fixture
from uaw.shared.errors import DomainError
from uaw.shared.runner_bootstrap import FirstStartPolicy

ipc_case = _ipc_fixture


async def prepare_start(case, *, mode="valid", delay=0, seconds=5, native=None):
    native, original, path = await prepare_helper(case, native=native)
    await original.close()
    policy = FirstStartPolicy(datetime.now(UTC) + timedelta(seconds=seconds), "a" * 64, seconds)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["startup_fixture"] = dict(
        mode=mode,
        delay=delay,
        policy=dict(
            expires_at=policy.expires_at.isoformat(),
            challenge_hash=policy.challenge_hash,
            wait_seconds=policy.wait_seconds,
        ),
    )
    path.write_text(canonical(data), encoding="utf-8")
    process = await HelperProcess.prepare(
        python=Path(sys._base_executable),
        assembly_module="tests.integration.runner.helper_start_fixture",
        environment=helper_environment(path),
    )
    data["server"] = case["entry"]("device", process.identity.__dict__)
    path.write_text(canonical(data), encoding="utf-8")
    case["helper_processes"].append(process)
    return native, process, path, policy


async def wait_marker(case, name):
    async with asyncio.timeout(8):
        while not (case["tmp"] / name).exists():  # noqa: ASYNC110 - bounded process observation
            await asyncio.sleep(0.02)


def cleaned(process):
    assert process.closed and process.process.returncode == 0
    assert process.process.stdin.closed and process.process.stdout.closed


async def test_first_start_actual_wait_beyond_ordinary_15s_ready(ipc_case):
    native, process, path, policy = await prepare_start(ipc_case, delay=16, seconds=25)
    seen = []

    class Observer:
        async def waiting(self, value):
            seen.append(value)

    try:
        begin = asyncio.get_running_loop().time()
        assert (await process.start(first_start=policy, on_progress=Observer()))["event"] == "ready"
        assert asyncio.get_running_loop().time() - begin >= 16 and seen == [policy]
    finally:
        await process.close()
    cleaned(process)


@pytest.mark.parametrize(
    "mode",
    [
        "hash",
        "expiry",
        "stage",
        "extra",
        "duplicate",
        "repeat",
        "oversize",
        "truncated",
        "exit",
        "deny",
    ],
)
async def test_real_hidden_first_start_invalid_progress_or_reject(ipc_case, mode):
    native, process, path, policy = await prepare_start(ipc_case, mode=mode, seconds=8)
    try:
        with pytest.raises(DomainError) as failure:
            await process.start(first_start=policy)
        if mode == "deny":
            assert failure.value.failure.code == "native_denied"
        assert process.closed
    finally:
        await process.close()
    cleaned(process)


async def test_ordinary_start_waiting_rejected_even_with_observer(ipc_case):
    native, process, path, policy = await prepare_start(ipc_case)

    class Observer:
        async def waiting(self, value):
            raise AssertionError("No first-start policy must not observe waiting")

    with pytest.raises(DomainError):
        await process.start(on_progress=Observer())
    cleaned(process)


@pytest.mark.parametrize("mode", ["valid", "late", "native"])
async def test_stop_during_factory_cancels_own_native_or_late_helper(ipc_case, mode):
    native, process, path, policy = await prepare_start(ipc_case, mode=mode, delay=60, seconds=30)
    pending = asyncio.create_task(process.start(first_start=policy))
    await wait_marker(ipc_case, "factory-begun")
    await asyncio.sleep(0.3)
    await asyncio.gather(process.close(), process.close())
    await asyncio.gather(pending, return_exceptions=True)
    await wait_marker(ipc_case, "factory-cancelled")
    if mode == "late":
        await wait_marker(ipc_case, "late-helper-closed")
    elif mode == "native":
        await wait_marker(ipc_case, "native-worker-drained")
    cleaned(process)


async def test_actual_stdin_eof_cancels_factory_without_stop_command(ipc_case):
    native, process, path, policy = await prepare_start(ipc_case, delay=60, seconds=30)
    pending = asyncio.create_task(process.start(first_start=policy))
    await wait_marker(ipc_case, "factory-begun")
    await asyncio.to_thread(process.process.stdin.close)
    await asyncio.gather(pending, return_exceptions=True)
    await process.close()
    await wait_marker(ipc_case, "factory-cancelled")
    cleaned(process)


async def test_cancel_parent_first_wait_drains_factory_and_pipe_reader(ipc_case):
    native, process, path, policy = await prepare_start(ipc_case, delay=60, seconds=30)
    pending = asyncio.create_task(process.start(first_start=policy))
    await wait_marker(ipc_case, "factory-begun")
    pending.cancel()
    with pytest.raises(asyncio.CancelledError):
        await pending
    await wait_marker(ipc_case, "factory-cancelled")
    cleaned(process)


async def test_first_deadline_expires_during_factory_no_extension(ipc_case):
    native, process, path, policy = await prepare_start(ipc_case, delay=60, seconds=2.5)
    with pytest.raises(DomainError):
        await process.start(first_start=policy)
    await wait_marker(ipc_case, "factory-cancelled")
    cleaned(process)


async def test_actual_hidden_host_uses_selector_loop_without_global_policy(ipc_case):
    native, process, path, policy = await prepare_start(ipc_case)
    try:
        assert (await process.start(first_start=policy))["event"] == "ready"
        await wait_marker(ipc_case, "selector-loop")
    finally:
        await process.close()
    cleaned(process)


async def test_installed_hidden_selector_reads_actual_session_d_postgres(ipc_case):
    native, process, path, policy = await prepare_start(ipc_case, mode="sql-check", seconds=8)
    try:
        assert (await process.start(first_start=policy))["event"] == "ready"
        await wait_marker(ipc_case, "actual-postgres-checked")
    finally:
        await process.close()
    cleaned(process)
