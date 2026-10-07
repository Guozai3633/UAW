"""Read-only, Run-owned source set. Intent never writes its own original-input ledger."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from uaw.context.seed import revision
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.stores import StoreMissing

Payload = dict[str, Any]


@dataclass(frozen=True)
class InputSet:
    run: Payload
    state: Payload
    refs: tuple[Payload, ...]
    inputs: tuple[Payload, ...]


class RunInputReader:
    def __init__(self, store: PostgresRecordStore) -> None:
        self.store = store

    async def read(self, ctx: TrustedExecutionContext) -> InputSet:
        run = (await self.store.get(ctx.principal, "runs", ctx.run_id or "")).payload
        if (
            run["conversation_id"] != ctx.scope.conversation_id
            or (ctx.task_id and ctx.task_id != run["task_id"])
            or (ctx.scope.task_id and ctx.scope.task_id != run["task_id"])
        ):
            raise reject("intent_scope_denied", "Source set is outside the trusted scope", 403)
        if run["status"] not in ("preparing", "running"):
            raise reject(
                "intent_run_unavailable", "Run is not at an active understanding boundary", 409
            )
        ledger = (await self.store.get(ctx.principal, "budget.ledgers", run["id"])).payload
        if ledger["cancel_requested"]:
            raise reject("intent_cancelled", "Run has been cancelled", 409, "cancelled")
        deadlines = (ctx.deadline, run["budget"]["deadline"])
        if any(
            datetime.fromisoformat(d.replace("Z", "+00:00")) <= datetime.now(UTC) for d in deadlines
        ):
            raise reject(
                "intent_deadline_expired", "Understanding deadline has passed", 409, "timeout"
            )
        try:
            state = (await self.store.get(ctx.principal, "run.input_sets", run["id"])).payload
        except StoreMissing as exc:
            # Pre-P1 Runs remain readable; their sources are never silently reconstructed.
            raise reject(
                "intent_input_set_unavailable",
                "This Run predates source-set tracking; submit a new turn",
                503,
                "dependency",
            ) from exc
        binding = (await self.store.get(ctx.principal, "run.bindings", run["id"])).payload
        if (
            state["run_id"] != run["id"]
            or state["conversation_id"] != run["conversation_id"]
            or state["original_input_ref"] != binding["input_ref"]
        ):
            raise reject(
                "intent_source_invalid", "Input set does not match the original Run binding", 412
            )
        refs = (state["original_input_ref"], *state["patch_refs"])
        inputs: list[Payload] = []
        for ref in refs:
            value = (
                await self.store.get(
                    ctx.principal, "inputs", ref["id"], revision=revision(ref, "input")
                )
            ).payload
            if value["conversation_id"] != run["conversation_id"] or not value["text"].strip():
                raise reject("intent_source_invalid", "Input source is unavailable or empty", 412)
            inputs.append(value)
        if sum(len(value["text"].encode()) for value in inputs) > 65536:
            raise reject("intent_input_too_large", "Understanding source set exceeds 64 KiB", 413)
        return InputSet(run, state, refs, tuple(inputs))
