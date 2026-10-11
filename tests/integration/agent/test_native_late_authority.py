"""Real owned Windows IPC: authority changing during a late local read must be rejected."""

import asyncio
from datetime import UTC, datetime
from threading import Event

import pytest

from tests.integration.runner.test_native_authorization import lifecycle_setup
from tests.integration.runner.test_windows_ipc import ipc_case as ipc_case
from uaw.shared.errors import DomainError


async def test_control_key_revoked_during_final_ticket_read_must_be_rejected(ipc_case, monkeypatch):
    native = await lifecycle_setup(ipc_case, clock_start=datetime.now(UTC))
    state = native["state"]
    original = state.get
    entered, released = asyncio.Event(), Event()
    loop = asyncio.get_running_loop()
    calls = 0

    def waiting_read(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            loop.call_soon_threadsafe(entered.set)
            assert released.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(state, "get", waiting_read)
    work = asyncio.create_task(native["challenge"].current(native["ticket_id"]))
    observing = asyncio.create_task(entered.wait())
    try:
        done, _ = await asyncio.wait(
            (work, observing), timeout=5, return_when=asyncio.FIRST_COMPLETED
        )
        assert done
        if observing not in done:
            # Original reader has no late Ticket await. Its next call must still
            # reject a revoked live control key; do not manufacture a new await.
            await work
            state.revoke_key("control1", expected_revision=0)
            released.set()
            with pytest.raises(DomainError):
                await native["challenge"].current(native["ticket_id"])
            return
        # The root Ticket uses device1: revoking control1 does not change it.
        state.revoke_key("control1", expected_revision=0)
        released.set()
        with pytest.raises(DomainError):
            await asyncio.wait_for(work, 5)
    finally:
        released.set()
        if not work.done():
            work.cancel()
        await asyncio.gather(work, return_exceptions=True)
        observing.cancel()
        await asyncio.gather(observing, return_exceptions=True)
