"""Explicit scheduler doubles, never production SQL watch or native consent."""

import asyncio
from types import SimpleNamespace

import pytest
from uaw_runner.ipc.read_endpoint import ReadOnlyPipeEndpoint
from uaw_runner.read_watch import stop_on_change

from uaw.shared.errors import DomainError, reject


@pytest.mark.parametrize("outcome", ["return", "denial", "cancel"])
async def test_any_watch_completion_cancels_and_drains_sibling(outcome):
    entered, drained = asyncio.Event(), asyncio.Event()

    async def waiting():
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            drained.set()

    async def changed():
        await entered.wait()
        if outcome == "denial":
            raise reject("fixture_revoked", "Explicit controlled change", 403)
        if outcome == "cancel":
            raise asyncio.CancelledError

    error = asyncio.CancelledError if outcome == "cancel" else DomainError
    with pytest.raises(error):
        await stop_on_change(changed(), waiting())
    assert drained.is_set()


async def test_ordinary_monitor_return_aborts_owned_dispatch():
    entered, cancelled = asyncio.Event(), asyncio.Event()
    until = asyncio.get_running_loop().time() + 0.2

    async def dispatch(*args, **kwargs):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    async def receive(**kwargs):
        return {"kind": "command", "body": {}}

    async def close():
        pass

    async def monitor():
        await entered.wait()

    session = SimpleNamespace(
        pipe=SimpleNamespace(deadline=lambda value: value),
        monotonic_expiry=until,
        receive=receive,
        close=close,
    )
    endpoint = ReadOnlyPipeEndpoint(session=session, registry=None)
    endpoint.dispatch, endpoint.watch = dispatch, monitor
    with pytest.raises(DomainError) as error:
        await endpoint.serve_once(deadline=until)
    assert error.value.failure.code == "runner_current_changed"
    assert cancelled.is_set() and endpoint.watch_frame is None and not endpoint.busy
