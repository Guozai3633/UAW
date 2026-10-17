"""D55435 restart/CAS/rollback and immutable original deadline verification."""

import asyncio
from copy import deepcopy

import pytest

from tests.integration.run_clock.helpers import (
    install_question,
    protected_snapshot,
    resolve_question,
)
from tests.integration.test_control_plane import meta
from uaw.run.clock_ports import ClockChange
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.execution_clock import ExecutionClocks
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import DomainError


async def stored(p):
    return {
        name: deepcopy((await p.records.get(p.actor, name, p.run["id"])).payload)
        for name in ("run.execution_clocks", "run.protocol_bindings")
    }


async def replace(p, namespace, values, identifier=None):
    row = await p.records.get(p.actor, namespace, identifier or p.run["id"])
    return await p.records.put(
        p.actor,
        namespace,
        row.resource_id,
        row.schema_name,
        {**row.payload, **values},
        expected_revision=row.revision,
        request_id="inject-" + str(p.serial),
    )


async def test_concurrent_expected_revision_has_exactly_one_winner_and_original_replay(clock_case):
    p = clock_case
    p.advance(1234)
    results = await asyncio.gather(
        *[p.change(ClockChange(1, "active"), key=k) for k in ("page-a", "page-b")],
        return_exceptions=True,
    )
    winners = [v for v in results if isinstance(v, dict)]
    failures = [v for v in results if isinstance(v, DomainError)]
    assert len(winners) == 1 and len(failures) == 1 and failures[0].status_code == 409
    assert (await p.clocks.current(p.actor, p.run["id"])).wire() == winners[0]
    winning_key = "page-a" if isinstance(results[0], dict) else "page-b"
    p.advance(5000)
    assert await p.change(ClockChange(1, "active"), key=winning_key) == winners[0]
    assert (await p.clocks.current(p.actor, p.run["id"])).wire() == winners[0]


async def test_outer_transaction_failure_rolls_back_both_records_and_retry_still_owns_old_time(
    clock_case,
):
    p = clock_case
    before = await stored(p)
    original = await protected_snapshot(p)

    async def failed(tx):
        await p.clocks.change(tx, p.actor, p.run["id"], ClockChange(1, "active"))
        raise RuntimeError("outer A transaction failed after clock writes")

    p.advance(2000)
    with pytest.raises(RuntimeError):
        await p.transactions.execute(
            p.actor, "conversation:" + p.run["conversation_id"], meta("rollback"), {}, failed
        )
    assert await stored(p) == before and await protected_snapshot(p) == original
    p.advance(3000)
    assert (await p.change(ClockChange(1, "active")))["active_elapsed_ms"] == 5000


async def test_two_waits_and_restart_do_not_reissue_active_budget(clock_case):
    p = clock_case
    first = await install_question(p, "question-one")
    protected = await protected_snapshot(p)
    p.advance(1000)
    await p.change(ClockChange(1, "waiting_for_user", waiting_item_ref=first))
    p.advance(1200000)
    p.clocks = ExecutionClocks(p.records, effects=RunIdleEffects(), now=lambda: p.now[0])
    paused = await p.clocks.current(p.actor, p.run["id"])
    assert (
        paused.revision == 2
        and paused.remaining_active_ms(p.now[0]) == p.initial["active_limit_ms"] - 1000
    )
    assert await protected_snapshot(p) == protected
    await resolve_question(p, first)
    await p.change(ClockChange(2, "active"))
    p.advance(2000)
    second = await install_question(p, "question-two")
    await p.change(ClockChange(3, "waiting_for_user", waiting_item_ref=second))
    p.advance(1800000)
    await resolve_question(p, second)
    p.clocks = ExecutionClocks(p.records, effects=RunIdleEffects(), now=lambda: p.now[0])
    resumed = await p.change(ClockChange(4, "active"))
    assert resumed["active_elapsed_ms"] == 3000 and resumed["wait_elapsed_ms"] == 3000000
    assert resumed["active_limit_ms"] == p.initial["active_limit_ms"]
    # No lease is acquired by any clock operation. A owns real queue/lease/fence.
    assert resumed["revision"] == 5


@pytest.mark.parametrize("mode", ["active", "waiting_for_user", "stopped"])
async def test_time_rollback_never_partially_writes(clock_case, mode):
    p = clock_case
    pin = await install_question(p) if mode == "waiting_for_user" else None
    before = await stored(p)
    p.advance(-1)
    with pytest.raises(DomainError) as error:
        await p.change(ClockChange(1, mode, waiting_item_ref=pin))
    assert error.value.status_code == 412 and await stored(p) == before
    with pytest.raises(DomainError):
        await p.clocks.current(p.actor, p.run["id"])


async def test_real_active_overrun_is_saved_on_stop_not_clamped_or_refilled(clock_case):
    p = clock_case
    p.advance(p.initial["active_limit_ms"] + 1234)
    with pytest.raises(DomainError) as error:
        await p.change(ClockChange(1, "active"))
    assert error.value.status_code == 409
    result = await p.change(ClockChange(1, "stopped"))
    assert result["active_elapsed_ms"] == p.initial["active_limit_ms"] + 1234
    assert (await p.clocks.current(p.actor, p.run["id"])).remaining_active_ms(p.now[0]) == 0
    for mode in ("active", "waiting_for_user", "stopped"):
        with pytest.raises(DomainError) as error:
            await p.change(ClockChange(2, mode))
        assert error.value.status_code == 409


async def test_stop_preserves_unresolved_original_refs_even_if_request_proposes_empty(clock_case):
    p = clock_case
    ref = Ref(kind="checkpoint", id="original-unknown-invocation", version="1")
    await p.change(ClockChange(1, "active", in_flight_refs=(ref,)))
    p.advance(500)
    result = await p.change(ClockChange(2, "stopped"))
    assert result["in_flight_refs"] == [ref.wire()] and result["active_elapsed_ms"] == 500


@pytest.mark.parametrize("source", ["cancel", "overdrawn", "terminal"])
async def test_cancel_or_terminal_source_can_only_stop(clock_case, source):
    p = clock_case
    if source == "terminal":
        await replace(
            p,
            "runs",
            {
                "revision": p.run["revision"] + 1,
                "status": "failed",
                "outcome": "failed",
                "ended_at": p.now[0],
            },
        )
    else:
        row = await p.records.get(p.actor, "budget.ledgers", p.run["id"])
        await replace(
            p,
            "budget.ledgers",
            {
                "revision": row.revision + 1,
                "cancel_requested" if source == "cancel" else "overdrawn": True,
            },
        )
    before = await stored(p)
    with pytest.raises(DomainError) as error:
        await p.change(ClockChange(1, "active"))
    assert error.value.status_code == 409 and await stored(p) == before
    assert (await p.change(ClockChange(1, "stopped")))["mode"] == "stopped"


@pytest.mark.parametrize(
    "source",
    [
        "clock_pin",
        "input_revision",
        "owner",
        "limit",
        "clock_run",
        "question_revision",
        "item_revision",
    ],
)
async def test_changed_owning_sources_never_write_partial_clock(clock_case, source):
    p = clock_case
    pin = await install_question(p)
    if source in ("clock_pin", "input_revision", "owner"):
        binding = (await p.records.get(p.actor, "run.protocol_bindings", p.run["id"])).payload
        field = {"clock_pin": "clock_ref", "input_revision": "input_revision", "owner": "owner_id"}[
            source
        ]
        value = {
            "clock_pin": {"kind": "checkpoint", "id": p.run["id"], "version": "99"},
            "input_revision": 99,
            "owner": "other-user",
        }[source]
        await replace(
            p, "run.protocol_bindings", {field: value, "revision": binding["revision"] + 1}
        )
    elif source in ("limit", "clock_run"):
        values = (
            {"active_limit_ms": p.initial["active_limit_ms"] + 1}
            if source == "limit"
            else {"run_id": "other-run"}
        )
        await replace(p, "run.execution_clocks", values)
    elif source == "question_revision":
        await replace(
            p, "run.clarification_questions", {"revision": 2, "input_revision": 99}, pin.id
        )
    else:
        await replace(p, "items", {"revision": 2}, pin.id)
    before = await stored(p)
    with pytest.raises(DomainError):
        await p.change(ClockChange(1, "waiting_for_user", waiting_item_ref=pin))
    assert await stored(p) == before


async def test_open_question_cannot_resume_even_if_run_preparing_is_proposed(clock_case):
    p = clock_case
    pin = await install_question(p)
    await p.change(ClockChange(1, "waiting_for_user", waiting_item_ref=pin))
    row = await p.records.get(p.actor, "runs", p.run["id"])
    await replace(p, "runs", {"revision": row.revision + 1, "status": "preparing"})
    before = await stored(p)
    with pytest.raises(DomainError) as error:
        await p.change(ClockChange(2, "active"))
    assert error.value.status_code == 409 and await stored(p) == before


async def test_wrong_user_transaction_and_old_protocol_fail_closed(clock_case):
    p = clock_case
    before = await stored(p)
    other = Principal(id="unrelated", kind="user", auth_session_id="unrelated-session")
    with pytest.raises(DomainError) as error:
        await p.clocks.current(other, p.run["id"])
    assert error.value.status_code == 404

    async def wrong(tx):
        await p.clocks.change(tx, other, p.run["id"], ClockChange(1, "active"))
        return {}

    with pytest.raises(DomainError) as error:
        await p.transactions.inspect(p.actor, "conversation:" + p.run["conversation_id"], wrong)
    assert error.value.status_code == 403 and await stored(p) == before
    row = await p.records.get(p.actor, "run.protocol_bindings", p.run["id"])
    await p.records.delete(
        p.actor,
        row.namespace,
        row.resource_id,
        expected_revision=row.revision,
        request_id="old-protocol",
    )
    with pytest.raises(DomainError) as error:
        await p.clocks.current(p.actor, p.run["id"])
    assert error.value.status_code == 503


async def test_real_new_processes_cas_one_winner_and_restart_reads_original_segment(clock_case):
    import json
    import subprocess
    import sys

    p = clock_case
    p.advance(2345)
    base = {
        "actor": p.actor.wire(),
        "run": p.run["id"],
        "now": p.now[0],
        "expected": 1,
        "aggregate": "conversation:" + p.run["conversation_id"],
    }
    children = []

    async def child(mode, key):
        def run_child():
            process = subprocess.Popen(
                [sys.executable, "-m", "tests.integration.run_clock.clock_child"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            children.append(process)
            try:
                output, error = process.communicate(
                    json.dumps({**base, "mode": mode, "key": key}).encode(), timeout=20
                )
                assert process.returncode == 0, error.decode()
                return json.loads(output)
            finally:
                if process.poll() is None:
                    process.terminate()
                process.wait(timeout=5)

        return await asyncio.to_thread(run_child)

    try:
        async with asyncio.timeout(30):
            results = await asyncio.gather(child("change", "child-a"), child("change", "child-b"))
            winner = [r["clock"] for r in results if r["kind"] == "ok"]
            assert len(winner) == 1 and len([r for r in results if r.get("status") == 409]) == 1
            assert winner[0]["active_elapsed_ms"] == 2345 and winner[0]["revision"] == 2
            base["now"] = p.now[0]
            assert (await child("read", "restart"))["clock"] == winner[0]
            assert (await p.clocks.current(p.actor, p.run["id"])).wire() == winner[0]
    finally:
        for process in children:
            if process.poll() is None:
                process.terminate()
            await asyncio.to_thread(process.wait, 5)
        assert all(process.returncode is not None for process in children)


async def test_terminal_waiting_run_can_stop_without_claiming_question_was_answered(clock_case):
    p = clock_case
    pin = await install_question(p)
    await p.change(ClockChange(1, "waiting_for_user", waiting_item_ref=pin))
    row = await p.records.get(p.actor, "runs", p.run["id"])
    await replace(
        p,
        "runs",
        {
            "revision": row.revision + 1,
            "status": "failed",
            "outcome": "failed",
            "ended_at": p.now[0],
        },
    )
    p.advance(3000)
    result = await p.change(ClockChange(2, "stopped"))
    assert result["mode"] == "stopped" and result["wait_elapsed_ms"] == 3000
    assert (await p.records.get(p.actor, "run.clarification_questions", pin.id)).payload[
        "state"
    ] == "open"
