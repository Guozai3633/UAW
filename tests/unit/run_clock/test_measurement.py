"""Pure trusted-time measurement; no persistence, execution or permission grants."""

import pytest

from uaw.run.execution_clock import measure
from uaw.shared.conversation import RunExecutionClock
from uaw.shared.errors import DomainError


def active():
    return RunExecutionClock.model_validate_json("""{"protocol":"conversation-v1",
        "run_id":"run-clock","revision":1,"mode":"active","active_limit_ms":10000,
        "active_elapsed_ms":1000,"wait_elapsed_ms":2000,
        "captured_at":"2026-10-17T00:00:01Z","active_since":"2026-10-17T00:00:01Z",
        "in_flight_refs":[]}""")


def test_settles_milliseconds_without_reissuing_limit_or_changing_original():
    clock = active()
    result = measure(clock, "2026-10-17T00:00:03.345678Z")
    assert result.active_elapsed_ms == 3345
    assert result.wait_elapsed_ms == 2000 and result.active_limit_ms == 10000
    assert result.captured_at == result.active_since == "2026-10-17T00:00:03.345678Z"
    assert result.revision == 1 and clock.active_elapsed_ms == 1000
    assert result.remaining_active_ms(result.captured_at) == 6655


@pytest.mark.parametrize("mode", ["active", "waiting_for_user", "stopped"])
def test_mode_only_charges_its_original_persisted_segment(mode):
    data = active().wire()
    data["mode"] = mode
    if mode != "active":
        data.pop("active_since")
    if mode == "waiting_for_user":
        data.update(
            waiting_since="2026-10-17T00:00:01Z",
            waiting_item_ref={"kind": "item", "id": "question", "version": "1"},
        )
    clock = RunExecutionClock.model_validate_json(__import__("json").dumps(data))
    result = measure(clock, "2026-10-18T00:00:02.123Z")
    assert result.active_elapsed_ms == (86402123 if mode == "active" else 1000)
    assert result.wait_elapsed_ms == (86403123 if mode == "waiting_for_user" else 2000)
    assert result.active_limit_ms == 10000
    if mode == "active":
        assert result.remaining_active_ms(result.captured_at) == 0
    else:
        assert result.remaining_active_ms(result.captured_at) == 9000


@pytest.mark.parametrize("at", ["2026-10-17T00:00:00.999999Z", "2026-10-16T23:00:00Z"])
def test_time_reversal_rejected_instead_of_clamped(at):
    with pytest.raises(DomainError) as error:
        measure(active(), at)
    assert error.value.status_code == 412


@pytest.mark.parametrize("at", ["2026-10-17T00:00:01Z", "2026-10-17T08:00:01+08:00"])
def test_equal_utc_instants_and_trusted_offset_do_not_charge_twice(at):
    result = measure(active(), at)
    assert result.active_elapsed_ms == 1000
    assert measure(result, at).active_elapsed_ms == 1000
