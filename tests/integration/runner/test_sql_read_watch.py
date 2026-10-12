"""D cancellation consumer + actual A SQL source. Non-SQL authorities are explicit fixtures.

No native window, installed product consent or file execution is claimed here.
"""

import asyncio

import pytest
from uaw_runner.read_watch import stop_on_change

from tests.integration.agent.test_registered_runner_recheck import prepared
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.test_runner_control import case as case
from uaw.shared.errors import DomainError


@pytest.mark.parametrize(
    "change", ["lease", "device", "run", "policy", "budget", "model", "configuration", "deadline"]
)
async def test_sql_change_ends_d_owned_wait_without_cached_permission(case, change):
    source, ref, channel, record = await prepared(case)
    store = case.commands.store
    original = store._witness_rows
    polling, cancelled = asyncio.Event(), asyncio.Event()
    polls, collections = 0, 0
    collect = case.commands.collect
    captured = set()

    async def counted(*args, **kwargs):
        nonlocal collections
        collections += 1
        return await collect(*args, **kwargs)

    async def witnessed(rows, versions):
        nonlocal polls
        result = await original(rows, versions)
        captured.update(rows)
        captured.update(key[:3] for key in versions)
        polls += 1
        if polls == 3:
            polling.set()
        return result

    async def local_fixture_wait():
        # Explicit local monitor double for this SQL-only cancellation component.
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    case.commands.collect = counted
    store._witness_rows = witnessed
    until = asyncio.get_running_loop().time() + (0.8 if change == "deadline" else 5)
    watching = asyncio.create_task(
        stop_on_change(
            source.wait_changed(
                ref, authenticated_principal=case.actor, channel_ref=channel, deadline=until
            ),
            local_fixture_wait(),
        )
    )
    try:
        await asyncio.wait_for(polling.wait(), 3)
        before = collections
        assert before == 1
        if change == "lease":
            await case.leases.release(
                {
                    "lease_ref": case.registered["lease_ref"],
                    "fencing_token": case.lease["fencing_token"],
                },
                meta("d-watch-lease"),
                case.ctx,
                holder=case.controller,
            )
        elif change == "device":
            await case.devices.revoke(
                case.device["device_id"],
                case.device["revision"],
                meta("d-watch-device"),
                authenticated_service=case.controller,
            )
        elif change == "run":
            value = await case.domain[1].get_run(case.ctx.principal, case.ctx.run_id)
            await case.domain[1].control(
                case.ctx.principal,
                {
                    "run_id": case.ctx.run_id,
                    "control": {
                        "mode": "cancel",
                        "preserve_refs": [],
                        "reason": "D controlled actual SQL wait cancellation",
                    },
                },
                meta("d-watch-run", value["revision"]),
            )
        elif change != "deadline":
            namespace = {
                "policy": "execution.policies",
                "budget": "budget.ledgers",
                "model": "run.bindings",
                "configuration": "configuration.pointer",
            }[change]
            addresses = [key for key in captured if key[1] == namespace]
            assert addresses, (namespace, captured)
            account, _, identifier = addresses[0]
            owners = [
                actor for actor in (case.controller, case.ctx.principal) if actor.id == account
            ]
            assert len(owners) == 1
            owner = owners[0]
            row = await store.get(owner, namespace, identifier)
            # Delete only the original registered input in this test's own namespace.
            await store.delete(
                owner,
                namespace,
                identifier,
                expected_revision=row.revision,
                request_id="d-watch-" + change,
            )
        with pytest.raises(DomainError):
            await watching
        assert cancelled.is_set() and polls >= (3 if change == "deadline" else 4)
        assert collections <= before + 1  # fresh diagnostic only after actual SQL change
        assert store.database._record_observers.get() is None
    finally:
        watching.cancel()
        await asyncio.gather(watching, return_exceptions=True)
        case.commands.collect, store._witness_rows = collect, original
