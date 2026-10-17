"""Owned conversation clock accounting. Readings never grant execution rights."""

import json
from collections.abc import Awaitable, Callable
from copy import deepcopy
from datetime import UTC, datetime

from uaw.infrastructure.db.models import RecordVersionRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import (
    RecordTransaction,
    TransactionalStore,
    reference,
    timestamp,
)
from uaw.run.clock_ports import ClockChange, ClockIdlePort
from uaw.run.conversation_control import QUESTIONS, TERMINAL, ConversationControls
from uaw.shared.contracts import JsonObject, Principal, Ref
from uaw.shared.conversation import RunExecutionClock
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreConflict, StoreMissing


def measure(clock: RunExecutionClock, at: str) -> RunExecutionClock:
    """Pure settlement at trusted service time; retain true overruns and the limit.

    This detached reading has the SAME revision and is not a new persisted pin.
    Only change() may store a new clock/binding revision in the caller's transaction.
    """
    data = clock.wire()
    validate_contract("RunExecutionClock", data)
    validate_contract("Timestamp", at)
    instant = datetime.fromisoformat(at.replace("Z", "+00:00")).astimezone(UTC)
    captured = datetime.fromisoformat(clock.captured_at.replace("Z", "+00:00"))
    if instant < captured:
        raise reject("execution_clock_time_reversed", "Trusted clock moved backwards", 412)
    key = {"active": "active_since", "waiting_for_user": "waiting_since"}.get(clock.mode)
    if key is not None:
        start = datetime.fromisoformat(str(data[key]).replace("Z", "+00:00"))
        delta = instant - start
        elapsed = (delta.days * 86400 + delta.seconds) * 1000 + delta.microseconds // 1000
        target = "active_elapsed_ms" if clock.mode == "active" else "wait_elapsed_ms"
        data[target] += elapsed
        data[key] = at
    data["captured_at"] = at
    validate_contract("RunExecutionClock", data)
    return RunExecutionClock.model_validate_json(json.dumps(data))


async def require_none(operation: Awaitable[object]) -> None:
    if await operation is not None:
        raise reject("execution_clock_idle_invalid", "Idle inventory must return None", 503)


class ExecutionClocks:
    """Join the original owning Run transaction; never commit or mint a deadline.

    ``effects`` must be the actual inventory for the same Run. An empty proposed
    reference list is not evidence that executing calls or reservations ended.
    """

    def __init__(
        self,
        records: PostgresRecordStore,
        *,
        effects: ClockIdlePort,
        now: Callable[[], str] = timestamp,
    ) -> None:
        if not callable(getattr(effects, "check", None)):
            raise CapabilityUnavailable("run.clock_idle_inventory")
        self.records, self.effects, self.now = records, effects, now
        self.controls = ConversationControls(records)

    async def _owned(
        self,
        tx: RecordTransaction,
        actor: Principal,
        run_id: str,
    ) -> tuple[JsonObject, JsonObject, RunExecutionClock]:
        validate_contract("Principal", actor.wire())
        validate_contract("ID", run_id)
        if actor.kind != "user" or tx.owner != actor.id:
            raise reject("execution_clock_owner_denied", "Original user transaction required", 403)
        if tx.database is not self.records.database:
            raise reject(
                "execution_clock_source_changed", "Original database transaction required", 412
            )
        run = deepcopy(await self.controls.owned(tx, actor, run_id))
        binding = await tx.load("run.protocol_bindings", run_id)
        try:
            row = await tx.load("run.execution_clocks", run_id)
        except StoreMissing:
            raise CapabilityUnavailable("run.execution_clock") from None
        if row.schema_name != "RunExecutionClock":
            raise reject("execution_clock_source_changed", "Clock schema changed", 412)
        validate_contract("RunExecutionClock", row.payload)
        clock = RunExecutionClock.model_validate_json(json.dumps(row.payload))
        initial = await tx.session.get(
            RecordVersionRow, (actor.id, "run.execution_clocks", run_id, 1)
        )
        if initial is None or initial.schema_name != "RunExecutionClock":
            raise reject("execution_clock_source_changed", "Original clock limit unavailable", 412)
        validate_contract("RunExecutionClock", initial.payload)
        if (
            clock.run_id != run_id
            or clock.revision != row.revision
            or binding.payload["clock_ref"] != reference("checkpoint", run_id, row.revision)
            or initial.payload["run_id"] != run_id
            or initial.payload["revision"] != 1
            or initial.payload["active_limit_ms"] != clock.active_limit_ms
        ):
            raise reject("execution_clock_source_changed", "Original clock pin/limit changed", 412)
        if clock.mode == "waiting_for_user":
            assert clock.waiting_item_ref is not None  # Strict schema requires this field.
            await self._question(tx, run, clock.waiting_item_ref, opened=False)
        return run, deepcopy(binding.payload), clock

    async def _question(
        self,
        tx: RecordTransaction,
        run: JsonObject,
        pin: Ref,
        *,
        opened: bool,
    ) -> None:
        view = await self.controls.question_value(tx, run, pin.id)
        row = await tx.load("run.clarification_questions", pin.id)
        item = await tx.load("items", pin.id)
        validate_contract("InteractionItem", item.payload)
        if (
            pin.wire() != reference("item", item.resource_id, item.revision)
            or item.payload["id"] != item.resource_id
            or item.payload["revision"] != item.revision
            or item.payload["type"] != "agent_message"
            or item.payload["status"] != "completed"
            or row.revision != view.question.revision
            or row.schema_name != "ClarificationQuestion"
            or item.schema_name != "InteractionItem"
            or (opened and (view.question.state != "open" or run["status"] != "waiting_for_user"))
        ):
            raise reject(
                "execution_clock_question_changed", "Original stable question Item differs", 412
            )

    async def current(self, actor: Principal, run_id: str) -> RunExecutionClock:
        aggregate = await self.controls.aggregate(actor, run_id)

        async def read(tx: RecordTransaction) -> JsonObject:
            _, _, clock = await self._owned(tx, actor, run_id)
            measure(clock, self.now())  # Reject rollback, without changing or claiming a segment.
            return clock.wire()

        data = await TransactionalStore(self.records.database).inspect(actor, aggregate, read)
        return RunExecutionClock.model_validate_json(json.dumps(data))

    async def change(
        self,
        tx: RecordTransaction,
        actor: Principal,
        run_id: str,
        request: ClockChange,
    ) -> RunExecutionClock:
        if (
            type(request) is not ClockChange
            or type(request.expected_clock_revision) is not int
            or request.expected_clock_revision < 1
            or request.mode not in ("active", "waiting_for_user", "stopped")
            or type(request.in_flight_refs) is not tuple
            or any(type(r) is not Ref for r in request.in_flight_refs)
            or (request.waiting_item_ref is not None and type(request.waiting_item_ref) is not Ref)
        ):
            raise reject("execution_clock_request_invalid", "Trusted ClockChange required", 412)
        for ref in request.in_flight_refs:
            validate_contract("Ref", ref.wire())
        run, binding, clock = await self._owned(tx, actor, run_id)
        if clock.revision != request.expected_clock_revision:
            raise StoreConflict()
        if clock.mode == "stopped":
            raise reject("execution_clock_stopped", "Stopped clock cannot change", 409)
        ledger = await tx.load("budget.ledgers", run_id)
        validate_contract("RootBudgetLedger", ledger.payload)
        if ledger.payload["run_id"] != run_id:
            raise reject("execution_clock_source_changed", "Original budget owner differs", 412)
        if request.mode != "stopped" and (
            run["status"] in TERMINAL
            or ledger.payload["cancel_requested"]
            or ledger.payload["overdrawn"]
        ):
            raise reject(
                "execution_clock_stopped", "Cancelled/terminal/overdrawn Run may only stop", 409
            )
        ledger_before = deepcopy(ledger.payload)
        if request.mode == "waiting_for_user":
            if request.waiting_item_ref is None or request.in_flight_refs:
                raise reject(
                    "execution_clock_not_idle", "Concrete question and idle inventory required", 409
                )
            await self._question(tx, run, request.waiting_item_ref, opened=True)
            await require_none(self.effects.check(tx, actor, run_id))
            # Recheck current owning sources after independent inventory work. No partial writes.
            again = await self._owned(tx, actor, run_id)
            await self._question(tx, run, request.waiting_item_ref, opened=True)
            if (
                again != (run, binding, clock)
                or (await tx.load("budget.ledgers", run_id)).payload != ledger_before
            ):
                raise reject(
                    "execution_clock_source_changed", "Clock sources changed during inventory", 412
                )
        else:
            if request.waiting_item_ref is not None:
                raise reject(
                    "execution_clock_state_invalid", "Only waiting can select an Item", 409
                )
            if request.mode == "active":
                if run["status"] not in ("queued", "preparing", "running", "verifying"):
                    raise reject(
                        "execution_clock_state_invalid", "Active Run boundary required", 409
                    )
                questions = await self.controls.matching(tx, QUESTIONS, run_id)
                if any(row.payload["state"] == "open" for row in questions):
                    raise reject(
                        "execution_clock_question_open", "Original question remains open", 409
                    )
        measured = measure(clock, self.now())
        if request.mode != "stopped" and measured.active_elapsed_ms >= measured.active_limit_ms:
            raise reject("execution_clock_exhausted", "Active time exhausted", 409, "budget")
        data = measured.wire()
        for field in ("active_since", "waiting_since", "waiting_item_ref"):
            data.pop(field, None)
        data.update(
            revision=clock.revision + 1,
            mode=request.mode,
            in_flight_refs=[ref.wire() for ref in request.in_flight_refs],
        )
        if request.mode == "stopped":
            # Unknown external effects remain visible even if the caller proposes no refs.
            for ref in clock.in_flight_refs:
                if ref.wire() not in data["in_flight_refs"]:
                    data["in_flight_refs"].append(ref.wire())
        elif request.mode == "active":
            data["active_since"] = data["captured_at"]
        else:
            data["waiting_since"] = data["captured_at"]
            assert request.waiting_item_ref is not None
            data["waiting_item_ref"] = request.waiting_item_ref.wire()
        validate_contract("RunExecutionClock", data)
        result = RunExecutionClock.model_validate_json(json.dumps(data))
        binding_revision = binding["revision"]
        if type(binding_revision) is not int:
            raise reject("execution_clock_source_changed", "Binding revision invalid", 412)
        await tx.write("run.execution_clocks", run_id, "RunExecutionClock", data, clock.revision)
        await tx.write(
            "run.protocol_bindings",
            run_id,
            "ConversationProtocolBinding",
            {
                **binding,
                "revision": binding_revision + 1,
                "clock_ref": reference("checkpoint", run_id, result.revision),
            },
            binding_revision,
        )
        return result
