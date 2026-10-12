"""Real Windows dual-process/key vault/native SQLite checks; registration is a fixture.

No SQL watch, production account mapping or human confirmation is claimed here.
"""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from uaw_runner.read_watch import LocalReadInvalidation

from tests.integration.runner.test_windows_ipc import ipc_case as ipc_case
from tests.integration.runner.test_windows_read_ipc import endpoint_setup, read_setup
from uaw.shared.errors import DomainError


@pytest.mark.parametrize(
    "change",
    [
        "control_key",
        "device_key",
        "private",
        "exit",
        "disconnect",
        "expired",
        "identity",
        "root_replaced",
        "grant",
        "root_expired",
    ],
)
async def test_real_local_invalidation_while_waiting(ipc_case, change):
    case = ipc_case
    native = await read_setup(case)
    endpoint, process, registry = await endpoint_setup(case, native)
    session = endpoint.session
    until = asyncio.get_running_loop().time() + 3
    await session.check_local(deadline=until)
    runner = await endpoint.runners.create(native["command_ref"], channel_ref=session.channel_ref)
    source = await native["reader"].resolve(
        native["command_ref"], authenticated_principal=native["owners"].value
    )
    monitor = LocalReadInvalidation(native["source"])
    connection = asyncio.create_task(monitor.watch_connection(session, deadline=until))
    root = asyncio.create_task(
        monitor.watch(
            runner,
            source,
            authenticated_principal=native["owners"].value,
            session=session,
            registry=registry,
            deadline=until,
        )
    )
    try:
        await asyncio.sleep(0.08)
        if change.endswith("_key"):
            case["keys"].revoke_key(
                "control1" if change == "control_key" else "device1", expected_revision=0
            )
        elif change == "private":
            await case["store"].delete(case["handles"][0])
        elif change == "exit":
            process.terminate()
            await asyncio.to_thread(process.wait, timeout=5)
        elif change == "disconnect":
            await session.close()
        elif change == "expired":
            session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        elif change == "identity":
            session.local = replace(
                session.local, identity=replace(session.local.identity, created=0)
            )
        elif change == "root_replaced":
            native["root"].rename(native["tmp"] / "old-root")
            native["root"].mkdir()
        elif change == "grant":
            native["grants"].revoke("native-root1", expected_revision=0)
        elif change == "root_expired":
            native["clock"][0] += timedelta(minutes=20)
        done, _ = await asyncio.wait(
            (connection, root), timeout=1, return_when=asyncio.FIRST_COMPLETED
        )
        assert done, "Actual local source change must end the original wait promptly"
        with pytest.raises(DomainError):
            await next(iter(done))
        assert await asyncio.to_thread(runner.executions.get, source, native["command_ref"]) is None
    finally:
        for task in (connection, root):
            task.cancel()
        await asyncio.gather(connection, root, return_exceptions=True)
        await registry.close()
