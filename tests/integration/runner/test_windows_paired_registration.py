"""Actual D Windows pipe/OS/two-process key vault; account registry controlled.

No native human confirmation or production enrollment is claimed by this fixture.
"""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from tests.integration.runner.test_windows_ipc import ipc_case as ipc_case
from tests.integration.runner.test_windows_ipc import start_peer
from uaw.shared.errors import DomainError


@pytest.mark.parametrize(
    "change",
    [
        "none",
        "control_key",
        "device_key",
        "owner",
        "identity",
        "exit",
        "pipe",
        "expiry",
        "cancel",
        "timeout",
        "swap",
    ],
)
async def test_real_paired_session_checks_after_source_await(ipc_case, change):
    case = ipc_case
    session, process, _ = await start_peer(case)
    await session.handshake()
    original = session.registration
    calls, singles = [], []
    stopped = asyncio.Event()
    timeout = session.pipe.timeout

    class PairFixture:
        async def current(self, *args, **kwargs):
            singles.append(kwargs["role"])
            return await original.current(*args, **kwargs)

        async def current_pair(self, control, device):
            calls.append((control, device))
            result = (
                await original.current(control, role="control"),
                await original.current(device, role="device"),
            )
            await asyncio.sleep(0)
            if change.endswith("_key"):
                case["keys"].revoke_key(
                    change.replace("_", "").replace("key", "1"), expected_revision=0
                )
            elif change == "owner":
                result = (
                    replace(
                        result[0],
                        owner=result[0].owner.model_copy(update={"auth_session_id": "changed"}),
                    ),
                    result[1],
                )
            elif change == "identity":
                result = (
                    replace(result[0], identity=replace(result[0].identity, created=0)),
                    result[1],
                )
            elif change == "exit":
                process.terminate()
                await asyncio.to_thread(process.wait, timeout=5)
            elif change == "pipe":
                await session.pipe.close()
            elif change == "expiry":
                session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
            elif change == "swap":
                result = tuple(reversed(result))
            elif change in {"cancel", "timeout"}:
                try:
                    stopped.set()
                    await asyncio.Event().wait()
                finally:
                    case["report"]["paired_wait_drained"] = True
            return result

    session.registration = PairFixture()
    if change == "none":
        await session.check()
        await session.check_local(deadline=asyncio.get_running_loop().time() + 2)
        assert calls == [(session.peer.identity, session.local.identity)]
        assert not session.pipe.closed.is_set()
    elif change == "cancel":
        work = asyncio.create_task(session.check())
        await stopped.wait()
        work.cancel()
        with pytest.raises(asyncio.CancelledError):
            await work
    else:
        if change == "timeout":
            session.pipe.timeout = 0.08  # earlier test bound only; never increase actual deadline
        with pytest.raises(DomainError):
            await session.check()
    session.pipe.timeout = timeout
    assert len(calls) == 1 and singles == []
    if change != "none":
        assert session.pipe.closed.is_set()
    case["report"]["pair_consumer"] = {
        "change": change,
        "pair_calls": len(calls),
        "fallback_calls": len(singles),
        "registry": "explicit fixture; actual OS/key/pipe",
    }
