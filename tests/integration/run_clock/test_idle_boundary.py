"""A published ClockIdlePort boundary failures, explicit controlled inventory adapters."""

import asyncio

import pytest

from tests.integration.run_clock.helpers import install_question
from tests.integration.run_clock.test_persistence import stored
from uaw.run.clock_ports import ClockChange
from uaw.run.execution_clock import ExecutionClocks
from uaw.shared.errors import CapabilityUnavailable, DomainError


async def test_missing_inventory_cannot_construct_a_free_pause(clock_case):
    p = clock_case
    with pytest.raises(CapabilityUnavailable):
        ExecutionClocks(p.records, effects=None)
    with pytest.raises(TypeError):
        ExecutionClocks(p.records)


@pytest.mark.parametrize(
    "mode", ["false", "exception", "cancel", "clock_changed", "cancel_changed", "question_changed"]
)
async def test_failed_or_changed_inventory_rolls_back_and_never_falls_back(clock_case, mode):
    p = clock_case
    pin = await install_question(p)
    before = await stored(p)
    invoked = 0

    class ControlledInventory:
        async def check(self, tx, actor, run_id):
            nonlocal invoked
            invoked += 1
            if mode == "false":
                return False
            if mode == "exception":
                raise RuntimeError("inventory fixture failure")
            if mode == "cancel":
                raise asyncio.CancelledError()
            namespace = {
                "clock_changed": "run.protocol_bindings",
                "cancel_changed": "budget.ledgers",
                "question_changed": "run.clarification_questions",
            }[mode]
            row = await tx.load(namespace, pin.id if mode == "question_changed" else run_id)
            changed = {**row.payload, "revision": row.revision + 1}
            if mode == "clock_changed":
                changed["clock_ref"] = {"kind": "checkpoint", "id": run_id, "version": "99"}
            elif mode == "cancel_changed":
                changed["cancel_requested"] = True
            else:
                changed["state"] = "stale"
            await tx.write(namespace, row.resource_id, row.schema_name, changed, row.revision)

    p.clocks = ExecutionClocks(p.records, effects=ControlledInventory(), now=lambda: p.now[0])
    error = (
        RuntimeError
        if mode == "exception"
        else asyncio.CancelledError
        if mode == "cancel"
        else DomainError
    )
    with pytest.raises(error):
        await p.change(ClockChange(1, "waiting_for_user", waiting_item_ref=pin))
    assert invoked == 1 and await stored(p) == before
    # Inventory mutations belong to the same outer transaction and roll back as well.
    assert not (await p.records.get(p.actor, "budget.ledgers", p.run["id"])).payload[
        "cancel_requested"
    ]
    assert (await p.records.get(p.actor, "run.clarification_questions", pin.id)).payload[
        "state"
    ] == "open"


async def test_earlier_outer_cancel_drains_inventory_and_keeps_original_clock(clock_case):
    p = clock_case
    pin = await install_question(p)
    before = await stored(p)
    entered, drained = asyncio.Event(), asyncio.Event()

    class ControlledInventory:
        async def check(self, tx, actor, run_id):
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                drained.set()

    p.clocks = ExecutionClocks(p.records, effects=ControlledInventory(), now=lambda: p.now[0])
    task = asyncio.create_task(p.change(ClockChange(1, "waiting_for_user", waiting_item_ref=pin)))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert drained.is_set() and await stored(p) == before


async def test_coherent_new_pin_cannot_increase_original_admission_limit(clock_case):
    p = clock_case

    async def corrupt(tx):
        clock = await tx.load("run.execution_clocks", p.run["id"])
        binding = await tx.load("run.protocol_bindings", p.run["id"])
        await tx.write(
            clock.namespace,
            clock.resource_id,
            clock.schema_name,
            {
                **clock.payload,
                "revision": 2,
                "active_limit_ms": clock.payload["active_limit_ms"] + 1000,
            },
            1,
        )
        await tx.write(
            binding.namespace,
            binding.resource_id,
            binding.schema_name,
            {
                **binding.payload,
                "revision": 2,
                "clock_ref": {"kind": "checkpoint", "id": p.run["id"], "version": "2"},
            },
            1,
        )
        return {}

    await p.transactions.inspect(p.actor, "conversation:" + p.run["conversation_id"], corrupt)
    before = await stored(p)
    with pytest.raises(DomainError) as error:
        await p.change(ClockChange(2, "active"))
    assert error.value.status_code == 412 and await stored(p) == before


@pytest.mark.parametrize(
    "request",
    [
        ClockChange(True, "active"),
        ClockChange(0, "active"),
        ClockChange(1, "approved"),
        ClockChange(1, "active", in_flight_refs=[]),
        {"mode": "active"},
    ],
)
async def test_request_cannot_supply_time_or_boolean_cas(clock_case, request):
    p = clock_case
    before = await stored(p)

    async def write(tx):
        return (await p.clocks.change(tx, p.actor, p.run["id"], request)).wire()

    with pytest.raises(DomainError) as error:
        await p.transactions.inspect(p.actor, "conversation:" + p.run["conversation_id"], write)
    assert error.value.status_code == 412 and await stored(p) == before
