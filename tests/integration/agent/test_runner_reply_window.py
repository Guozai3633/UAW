"""A original total reply deadline covers source waits, send and response.

Real SQL/crypto with controlled transport; no native user consent or production
IPC execution is represented by these tests.
"""

import asyncio

import pytest

from tests.integration.agent.test_file_bridge_postgres import bridge_case as bridge_case
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_runner_control import case as case
from uaw.shared.errors import DomainError


async def test_source_wait_uses_original_window_and_never_sends(bridge_case, monkeypatch):
    p = bridge_case
    p.session.pipe.timeout = 0.15
    original = p.bridge.pipe.registry.authenticated_principal
    exchange = p.bridge.pipe._exchange
    observed = {}

    async def capture(*args, **kwargs):
        observed["deadline"] = kwargs["deadline"]
        observed["remaining"] = kwargs["deadline"] - asyncio.get_running_loop().time()
        return await exchange(*args, **kwargs)

    async def wait(*args, **kwargs):
        actor = await original(*args, **kwargs)
        observed["source_started"] = True
        await asyncio.Event().wait()
        return actor

    monkeypatch.setattr(p.bridge.pipe, "_exchange", capture)
    monkeypatch.setattr(p.bridge.pipe.registry, "authenticated_principal", wait)
    with pytest.raises(TimeoutError):
        await p.bridge.execute(p.call, p.spec, p.ctx)
    assert observed["source_started"] and 0 < observed["remaining"] <= 0.15
    assert p.session.closed and p.session.sent == [] and p.session.opens == 0
    assert p.bridge.pipe.busy is False


async def test_received_wait_cannot_restart_total_window_or_resend(bridge_case, monkeypatch):
    p = bridge_case
    p.session.pipe.timeout = 1.0
    exchange = p.bridge.pipe._exchange
    observed = {}

    async def capture(*args, **kwargs):
        observed["start"] = asyncio.get_running_loop().time()
        observed["deadline"] = kwargs["deadline"]
        return await exchange(*args, **kwargs)

    async def wait():
        observed["receive_start"] = asyncio.get_running_loop().time()
        await asyncio.Event().wait()

    monkeypatch.setattr(p.bridge.pipe, "_exchange", capture)
    monkeypatch.setattr(p.session, "receive", wait)
    with pytest.raises(TimeoutError):
        await p.bridge.execute(p.call, p.spec, p.ctx)
    assert observed["start"] < observed["receive_start"] < observed["deadline"]
    assert observed["deadline"] - observed["start"] <= 1.0
    assert p.session.closed and p.session.sent == ["command"] and p.session.opens == 1
    with pytest.raises(DomainError):
        await p.bridge.execute(p.call, p.spec, p.ctx)
    assert p.session.sent == ["command"] and p.session.opens == 1


async def test_pending_exchange_denies_another_caller_and_cleans_up(bridge_case, monkeypatch):
    p = bridge_case
    pending = asyncio.Event()
    original = p.bridge.pipe._exchange
    command_ref = None

    async def waiting(*args, **kwargs):
        nonlocal command_ref
        command_ref = args[0]
        pending.set()
        await asyncio.Event().wait()
        return await original(*args, **kwargs)

    monkeypatch.setattr(p.bridge.pipe, "_exchange", waiting)
    task = asyncio.create_task(p.bridge.execute(p.call, p.spec, p.ctx))
    try:
        await asyncio.wait_for(pending.wait(), 5)
        assert command_ref is not None
        with pytest.raises(DomainError) as denied:
            await p.bridge.pipe.read(command_ref)
        assert denied.value.failure.code == "ipc_busy"
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert p.session.closed and p.bridge.pipe.busy is False
        assert p.session.sent == [] and p.session.opens == 0
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


@pytest.mark.parametrize("phase", ["source", "receive", "source_uncancel"])
async def test_dependency_swallowing_timeout_cannot_send_or_report_success(
    bridge_case, monkeypatch, phase
):
    p = bridge_case
    source_phase = phase.startswith("source")
    p.session.pipe.timeout = 1.0 if phase == "receive" else 0.15
    original = p.bridge.pipe.registry.authenticated_principal if source_phase else p.session.receive
    started = False

    async def swallowed(*args, **kwargs):
        nonlocal started
        result = await original(*args, **kwargs)
        started = True
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            if phase == "source_uncancel":
                asyncio.current_task().uncancel()
            return result  # Deliberately faulty dependency; caller must still reject.

    if source_phase:
        monkeypatch.setattr(p.bridge.pipe.registry, "authenticated_principal", swallowed)
    else:
        monkeypatch.setattr(p.session, "receive", swallowed)
    with pytest.raises((TimeoutError, DomainError)) as stopped:
        await p.bridge.execute(p.call, p.spec, p.ctx)
    if phase == "source_uncancel":
        assert stopped.value.failure.code == "runner_pipe_reply_expired"
        assert stopped.value.failure.category == "timeout"
    assert started and p.session.closed and p.bridge.pipe.busy is False
    assert p.session.sent == ([] if source_phase else ["command"])
    assert p.session.opens == (0 if source_phase else 1)


async def test_dependency_swallowing_caller_cancel_cannot_send(bridge_case, monkeypatch):
    p = bridge_case
    started = asyncio.Event()
    original = p.bridge.pipe.registry.authenticated_principal

    async def swallowed(*args, **kwargs):
        actor = await original(*args, **kwargs)
        started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            return actor

    monkeypatch.setattr(p.bridge.pipe.registry, "authenticated_principal", swallowed)
    task = asyncio.create_task(p.bridge.execute(p.call, p.spec, p.ctx))
    try:
        await asyncio.wait_for(started.wait(), 5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert p.session.closed and p.session.sent == [] and p.session.opens == 0
        assert p.bridge.pipe.busy is False
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
