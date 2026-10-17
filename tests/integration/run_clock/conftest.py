"""Own D55435 records. Service time is controlled; no live model/native actions."""

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta, seed
from uaw.infrastructure.db.transactions import TransactionalStore
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.conversation_entry import admit
from uaw.run.execution_clock import ExecutionClocks


@pytest.fixture
async def clock_case(domain, principal):
    config, runs, admin = domain
    await seed(config, admin)
    conversation = await runs.create_conversation(
        principal,
        {
            "title": "D isolated clock",
            "model_choice": {"mode": "explicit", "model_id": "fixture-model"},
            "memory_policy": {
                "revision": 0,
                "read_enabled": False,
                "contribute_enabled": False,
                "scope": {"resource_refs": []},
            },
        },
        meta("clock-conversation"),
    )

    async def admitted(tx, run):
        await admit(tx, run, principal)

    run = await runs.submit(
        principal,
        {
            "conversation_id": conversation["id"],
            "text": "鍘熸枃  涓嶆敼\nclock component",
            "attachment_refs": [],
        },
        meta("clock-run"),
        on_admitted=admitted,
    )
    records = runs.store
    initial = (await records.get(principal, "run.execution_clocks", run["id"])).payload
    now = [initial["captured_at"]]
    p = SimpleNamespace(
        records=records,
        actor=principal,
        runs=runs,
        run=run,
        initial=initial,
        now=now,
        transactions=TransactionalStore(records.database),
        serial=0,
    )
    p.clocks = ExecutionClocks(records, effects=RunIdleEffects(), now=lambda: now[0])

    def advance(ms):
        now[0] = (datetime.fromisoformat(now[0]) + timedelta(milliseconds=ms)).isoformat()

    p.advance = advance

    async def change(request, *, key=None, action=None):
        p.serial += 1

        async def write(tx):
            if action is not None:
                await action(tx)
            return (await p.clocks.change(tx, principal, run["id"], request)).wire()

        return await p.transactions.execute(
            principal,
            "conversation:" + run["conversation_id"],
            meta(key or f"clock-change-{p.serial}"),
            {
                "expected": request.expected_clock_revision,
                "mode": request.mode,
                "in_flight_refs": [v.wire() for v in request.in_flight_refs],
                "item": request.waiting_item_ref.wire() if request.waiting_item_ref else None,
            },
            write,
        )

    p.change = change
    return p
