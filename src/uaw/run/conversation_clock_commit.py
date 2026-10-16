"""Consume an explicitly composed clock in the owning terminal transaction."""

from copy import deepcopy

from uaw.infrastructure.db.transactions import RecordTransaction, reference
from uaw.run.clock_ports import ClockChange, ConversationClockPort
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing


async def stop_clock(
    tx: RecordTransaction,
    actor: Principal,
    run_id: str,
    clocks: ConversationClockPort | None,
) -> None:
    if clocks is None:
        return  # Compatibility: no invented D component or new grant.
    try:
        binding = await tx.load("run.protocol_bindings", run_id)
    except StoreMissing:
        return  # Original file/legacy protocol remains independently governed.
    run = await tx.load("runs", run_id)
    original = deepcopy(run.payload)
    if (
        tx.owner != actor.id
        or actor.kind != "user"
        or original["status"] not in ("completed", "failed", "cancelled")
    ):
        raise reject("conversation_stop_source", "Owned terminal Run required", 403)
    clock = await tx.load("run.execution_clocks", run_id)
    validate_contract("RunExecutionClock", clock.payload)
    validate_contract("ConversationProtocolBinding", binding.payload)
    if (
        binding.payload["owner_id"] != actor.id
        or binding.payload["run_id"] != run_id
        or clock.payload["run_id"] != run_id
        or clock.payload["revision"] != clock.revision
        or binding.payload["clock_ref"] != reference("checkpoint", run_id, clock.revision)
    ):
        raise reject("conversation_stop_source", "Original clock binding differs", 412)
    if clock.payload["mode"] == "stopped":
        return
    revision = clock.revision
    limit = clock.payload["active_limit_ms"]
    elapsed = clock.payload["active_elapsed_ms"]
    in_flight = deepcopy(clock.payload["in_flight_refs"])
    binding_payload = deepcopy(binding.payload)
    result = await clocks.change(
        tx,
        actor,
        run_id,
        ClockChange(
            revision, "stopped", in_flight_refs=tuple(Ref.model_validate(v) for v in in_flight)
        ),
    )
    validate_contract("RunExecutionClock", result.wire())
    current = await tx.load("run.execution_clocks", run_id)
    actual_binding = await tx.load("run.protocol_bindings", run_id)
    if (
        result.wire() != current.payload
        or current.revision != revision + 1
        or result.revision != current.revision
        or result.run_id != run_id
        or result.mode != "stopped"
        or result.active_limit_ms != limit
        or result.active_elapsed_ms < elapsed
        or [v.wire() for v in result.in_flight_refs] != in_flight
        or actual_binding.payload
        != {
            **binding_payload,
            "revision": binding_payload["revision"] + 1,
            "clock_ref": reference("checkpoint", run_id, current.revision),
        }
        or run.payload != original
    ):
        raise reject("conversation_stop_unproven", "Owning terminal clock differs", 412)
