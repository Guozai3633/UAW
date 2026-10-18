"""Frozen internal A/D boundary for conversation-v1 clocks.

These commands are trusted composition inputs, never HTTP/model payloads.
Implementations join the caller's Run transaction and grant no execution rights.
"""

from dataclasses import dataclass
from typing import Literal, Protocol

from uaw.infrastructure.db.transactions import RecordTransaction
from uaw.shared.contracts import Principal, Ref
from uaw.shared.conversation import RunExecutionClock
from uaw.shared.ports import ExecutionClockPort


@dataclass(frozen=True, slots=True)
class ClockChange:
    expected_clock_revision: int
    mode: Literal["active", "waiting_for_user", "stopped"]
    in_flight_refs: tuple[Ref, ...] = ()
    waiting_item_ref: Ref | None = None


class ClockIdlePort(Protocol):
    async def check(self, tx: RecordTransaction, actor: Principal, run_id: str) -> None:
        """Read original model/tool/reservation ledgers; reject unresolved effects.

        An empty proposed reference array is not proof of idleness. This port
        must be supplied by actual Run composition; absence grants no pause.
        """
        ...


class ReviewWaitClockPort(Protocol):
    async def check(
        self,
        tx: RecordTransaction,
        actor: Principal,
        run_id: str,
        item_ref: Ref,
        *,
        opened: bool,
    ) -> None:
        """Verify the original artifact Item and owned delivery; never grant execution.

        opened=True requires the current successful, idle, undecided delivery.
        False checks immutable waiting provenance, even after revision/cancel.
        """
        ...


class ConversationClockPort(ExecutionClockPort, Protocol):
    async def change(
        self,
        tx: RecordTransaction,
        actor: Principal,
        run_id: str,
        request: ClockChange,
    ) -> RunExecutionClock:
        """CAS clock + binding.clock_ref in the SAME supplied transaction.

        Current owned Run/conversation/binding/clock and waiting Item are read
        from storage. No commit, new transaction, Run mutation, budget mutation,
        deadline extension, permission grant or background wake occurs here.
        Caller holds conversation:<id>; caller derives in_flight_refs from the
        original effect inventory, never from a proposed empty model array.
        """
        ...
