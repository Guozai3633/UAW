"""Public clock ports with actual owning PostgreSQL transactions and A idle inventory."""

from uaw.run.clock_ports import ClockChange


async def test_active_settlement_persists_clock_and_binding_only(clock_case):
    p = clock_case
    original = {
        name: (await p.records.get(p.actor, name, p.run["id"])).payload
        for name in ("runs", "run.input_sets", "run.bindings", "budget.ledgers")
    }
    p.advance(1234)
    changed = await p.change(ClockChange(1, "active"))
    assert changed["active_elapsed_ms"] == 1234 and changed["revision"] == 2
    assert changed["active_limit_ms"] == p.initial["active_limit_ms"]
    assert (await p.clocks.current(p.actor, p.run["id"])).wire() == changed
    binding = (await p.records.get(p.actor, "run.protocol_bindings", p.run["id"])).payload
    assert binding["clock_ref"] == {"kind": "checkpoint", "id": p.run["id"], "version": "2"}
    assert binding["revision"] == 2
    for name, value in original.items():
        assert (await p.records.get(p.actor, name, p.run["id"])).payload == value


async def test_actual_idle_pause_and_resume_charge_only_original_active_time(clock_case):
    from tests.integration.run_clock.helpers import install_question, resolve_question

    p = clock_case
    pin = await install_question(p)
    p.advance(2000)
    paused = await p.change(ClockChange(1, "waiting_for_user", waiting_item_ref=pin))
    assert paused["active_elapsed_ms"] == 2000 and paused["wait_elapsed_ms"] == 0
    p.advance(1200000)
    # Reads survive the original active wall deadline and never mutate the pin.
    assert (await p.clocks.current(p.actor, p.run["id"])).wire() == paused
    await resolve_question(p, pin)
    resumed = await p.change(ClockChange(2, "active"))
    assert resumed["active_elapsed_ms"] == 2000 and resumed["wait_elapsed_ms"] == 1200000
    assert resumed["active_limit_ms"] == p.initial["active_limit_ms"]
    assert resumed["active_since"] == p.now[0] and resumed["revision"] == 3
