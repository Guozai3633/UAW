"""Stopping while original cleanup drains cannot cancel cleanup a second time."""

import asyncio

from uaw.infrastructure.installed_lifecycle import InstalledLifecycle, OwnedLaunch
from uaw.shared.contracts import Principal


async def test_stop_during_cleanup_waits_original_task_without_second_cancel():
    owner = Principal(id="cleanup-user", kind="user", auth_session_id="web-session-cleanup")
    entry = OwnedLaunch("cleanup-launch", owner)
    entry.running = True
    entry.cleaning = True
    entered, release = asyncio.Event(), asyncio.Event()
    cancellations = 0

    async def cleanup():
        nonlocal cancellations
        entered.set()
        try:
            await release.wait()
        except asyncio.CancelledError:
            cancellations += 1
            raise
        finally:
            entry.done.set()

    entry.task = asyncio.create_task(cleanup())
    await entered.wait()
    lifecycle = object.__new__(InstalledLifecycle)
    stopping = asyncio.create_task(lifecycle.stop_entry(entry))
    await asyncio.sleep(0)
    assert not stopping.done() and not entry.task.cancelled()
    release.set()
    await stopping
    assert cancellations == 0 and entry.done.is_set()
