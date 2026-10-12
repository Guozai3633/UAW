"""Scheduling and assembly doubles only; never production IPC or authorization."""

import asyncio
from types import SimpleNamespace

import pytest
from uaw_runner.ipc.read_endpoint import ReadOnlyPipeEndpoint
from uaw_runner.read_current import reply_deadline
from uaw_runner.runtime import ReadOnlyHelper

from uaw.shared.errors import DomainError


async def test_endpoint_receive_dispatch_share_earlier_absolute_deadline():
    loop = asyncio.get_running_loop()
    until = loop.time() + 0.2
    seen = []
    closed = asyncio.Event()

    async def receive(*, deadline):
        seen.append(("receive", deadline))
        await asyncio.sleep(0.005)
        return {"kind": "command", "body": {}}

    async def dispatch(frame, *, deadline):
        seen.append(("dispatch", deadline))
        return "fixture-ref"

    async def check():
        await asyncio.sleep(0)

    async def close():
        closed.set()

    session = SimpleNamespace(
        pipe=SimpleNamespace(
            timeout=0.2, deadline=lambda supplied: min(loop.time() + 0.2, supplied)
        ),
        monotonic_expiry=until + 0.02,
        receive=receive,
        check=check,
        close=close,
    )
    endpoint = ReadOnlyPipeEndpoint(session=session, registry=None)
    endpoint.dispatch = dispatch
    assert await endpoint.serve_once(deadline=until) == "fixture-ref"
    assert seen == [("receive", until), ("dispatch", until)]
    assert not endpoint.busy and not closed.is_set()


async def test_helper_bootstrap_wait_does_not_renew_endpoint_deadline():
    loop = asyncio.get_running_loop()
    first = loop.time()
    expiry = first + 0.15
    seen = []

    async def readable(*, deadline):
        assert deadline == expiry
        return first

    async def connected(session):
        await asyncio.sleep(0.01)

    async def serve(*, deadline):
        seen.append(deadline)
        return "fixture-ref"

    helper = SimpleNamespace(
        available=lambda: None,
        operation=None,
        session=SimpleNamespace(
            pipe=SimpleNamespace(wait_readable=readable, timeout=0.1), monotonic_expiry=expiry
        ),
        bootstrap=SimpleNamespace(connected=connected),
        endpoint=SimpleNamespace(serve_once=serve),
    )
    assert await ReadOnlyHelper.serve_once(helper) == "fixture-ref"
    assert seen == [first + 0.1] and helper.operation is None


@pytest.mark.parametrize("bad", [True, float("inf"), float("nan"), "10", None])
async def test_reply_deadline_rejects_invalid_source_type(bad):
    with pytest.raises(DomainError):
        reply_deadline(bad)


@pytest.mark.parametrize("offset", [-0.01, 10.1])
async def test_reply_deadline_rejects_expired_or_expanded_budget(offset):
    with pytest.raises(DomainError):
        reply_deadline(asyncio.get_running_loop().time() + offset)
