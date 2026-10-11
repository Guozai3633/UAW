"""Idle scheduling only: source doubles are not actual OS/authorization evidence."""

import asyncio
import time
from types import SimpleNamespace

import pytest
from uaw_runner.ipc.windows_pipe import PipeConnection
from uaw_runner.runtime import ReadOnlyHelper

from uaw.shared.errors import DomainError, reject


@pytest.mark.parametrize("mode", ["byte", "expiry", "cancel"])
async def test_idle_wait_preserves_original_deadline_and_cancellation(mode):
    checks = []
    deadline = time.monotonic() + 0.08

    def readable(until):
        checks.append(until)
        if time.monotonic() >= until:
            raise reject("ipc_timeout", "Original deadline", 410)
        return mode == "byte" and len(checks) >= 2

    port = SimpleNamespace(readable_sync=readable)
    task = asyncio.create_task(PipeConnection.wait_readable(port, deadline=deadline))
    if mode == "cancel":
        await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    elif mode == "expiry":
        with pytest.raises(DomainError) as expired:
            await task
        assert expired.value.failure.code == "ipc_timeout"
    else:
        assert await task <= deadline
    assert checks and set(checks) == {deadline}


async def test_ready_bytes_does_not_extend_bootstrap_or_frame_budget():
    calls = []
    until = asyncio.get_running_loop().time() + 0.1

    class Pipe:
        timeout = 0.1

        async def wait_readable(self, *, deadline):
            calls.append(deadline)
            return asyncio.get_running_loop().time()

    async def bootstrap(session):
        await asyncio.sleep(0.2)

    async def endpoint():
        pytest.fail("Expired bootstrap cannot enter read endpoint")

    helper = SimpleNamespace(
        available=lambda: None,
        operation=None,
        bootstrap=SimpleNamespace(connected=bootstrap),
        session=SimpleNamespace(pipe=Pipe(), monotonic_expiry=until),
        endpoint=SimpleNamespace(serve_once=endpoint),
    )
    with pytest.raises(DomainError) as expired:
        await ReadOnlyHelper.serve_once(helper)
    assert expired.value.failure.code == "ipc_timeout"
    assert calls == [until] and helper.operation is None


@pytest.mark.parametrize("mode", ["disconnect", "expiry", "cancel"])
async def test_sent_receipt_waits_only_original_close_or_expiry(mode):
    from uaw_runner.helper_host import wait_reply_close

    checks = []

    def live():
        checks.append(True)
        return mode != "disconnect"

    until = asyncio.get_running_loop().time() + 0.06
    helper = SimpleNamespace(
        session=SimpleNamespace(monotonic_expiry=until, pipe=SimpleNamespace(live_sync=live))
    )
    task = asyncio.create_task(wait_reply_close(helper))
    if mode == "cancel":
        await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    else:
        await task
    assert checks and helper.session.monotonic_expiry == until
