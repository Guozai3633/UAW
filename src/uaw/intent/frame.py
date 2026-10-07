"""CAS publication of frame, current pointers, interaction item and event in one transaction."""

import hashlib
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select

from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import (
    RecordTransaction,
    TransactionalStore,
    reference,
    timestamp,
)
from uaw.run.inputs import InputSet
from uaw.shared.contracts import Principal, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreConflict, StoreMissing

Payload = dict[str, Any]


class FrameRepository:
    def __init__(self, store: PostgresRecordStore) -> None:
        self.store = store
        self.transactions = TransactionalStore(store.database)

    async def head_revision(self, owner: Principal, task_id: str) -> int:
        try:
            return (await self.store.get(owner, "intent.frames", task_id)).revision
        except StoreMissing:
            return 0

    async def current(self, owner: Principal, task_id: str) -> Payload:
        task = (await self.store.get(owner, "tasks", task_id)).payload
        conversation = task["conversation_refs"][0]["id"]
        async with self.store.database.sessions() as session, session.begin():
            await session.execute(
                select(
                    func.pg_advisory_xact_lock(
                        func.hashtextextended(f"{owner.id}:conversation:{conversation}", 0)
                    )
                )
            )
            tx = RecordTransaction(session, owner.id)
            current_task = await tx.load("tasks", task_id)
            if "frame_ref" not in current_task.payload:
                raise reject(
                    "task_frame_unavailable", "Task has no current understanding", 404, "dependency"
                )
            value = await tx.load("intent.frames", task_id)
            binding = await tx.load("intent.frame_bindings", f"{task_id}.{value.revision}")
            sources = await tx.load("run.input_sets", binding.payload["run_id"])
            if (
                current_task.payload["frame_ref"]
                != reference("task_frame", task_id, value.revision)
                or binding.payload["input_revision"] != sources.revision
            ):
                raise reject("intent_input_stale", "Current understanding requires a refresh", 412)
            return dict(value.payload)

    async def publish(
        self,
        candidate: Payload,
        semantic: Payload,
        inputs: InputSet,
        expected: int,
        digest: str,
        ctx: TrustedExecutionContext,
    ) -> Payload:
        task_id = inputs.run["task_id"]

        async def write(tx: RecordTransaction) -> Payload:
            current_inputs = await tx.load("run.input_sets", inputs.run["id"])
            run = await tx.load("runs", inputs.run["id"])
            task = await tx.load("tasks", task_id)
            ledger = await tx.load("budget.ledgers", inputs.run["id"])
            if current_inputs.payload != inputs.state:
                raise reject("intent_input_stale", "New user input invalidated the proposal", 412)
            if ledger.payload["cancel_requested"]:
                raise reject(
                    "intent_cancelled",
                    "Cancelled understanding cannot be committed",
                    409,
                    "cancelled",
                )
            if run.payload["status"] not in ("preparing", "running"):
                raise reject("intent_run_unavailable", "Run no longer accepts understanding", 409)
            if any(
                datetime.fromisoformat(deadline.replace("Z", "+00:00")) <= datetime.now(UTC)
                for deadline in (ctx.deadline, run.payload["budget"]["deadline"])
            ):
                raise reject(
                    "intent_deadline_expired",
                    "Understanding deadline expired before commit",
                    409,
                    "timeout",
                )
            try:
                old = await tx.load("intent.frames", task_id)
                current_revision = old.revision
            except StoreMissing:
                current_revision = 0
            if current_revision != expected:
                raise StoreConflict()
            # Exact source membership is rechecked within the publication transaction.
            for ref in inputs.refs:
                source = await tx.load("inputs", ref["id"])
                if source.payload != inputs.inputs[
                    inputs.refs.index(ref)
                ] or source.revision != int(ref["version"]):
                    raise reject("intent_source_stale", "Input source changed before commit", 412)
            next_revision = expected + 1
            value = {**candidate, "revision": next_revision, "created_at": timestamp()}
            frame_ref = reference("task_frame", task_id, next_revision)
            semantic_ref = candidate["semantic_parse_ref"]
            await tx.write("intent.semantic", semantic_ref["id"], "IntentSemanticRecord", semantic)
            if current_revision and all(
                old.payload.get(key) == item
                for key, item in candidate.items()
                if key != "semantic_parse_ref"
            ):
                frame_ref = reference("task_frame", task_id, current_revision)
                result = {
                    "kind": "ok",
                    "payload": old.payload,
                    "revision": current_revision,
                    "output_refs": [frame_ref],
                }
                await tx.write(
                    "intent.receipts",
                    ctx.attempt_id,
                    "IntentReceipt",
                    {
                        "request_hash": digest,
                        "run_id": inputs.run["id"],
                        "input_revision": inputs.state["revision"],
                        "frame_ref": frame_ref,
                        "result": result,
                    },
                )
                return result
            await tx.write("intent.frames", task_id, "TaskFrame", value, expected)
            await tx.write(
                "intent.frame_bindings",
                f"{task_id}.{next_revision}",
                "IntentFrameBinding",
                {
                    "run_id": inputs.run["id"],
                    "input_revision": inputs.state["revision"],
                    "source_refs": list(inputs.refs),
                    "semantic_parse_ref": semantic_ref,
                },
            )
            for namespace, row, schema in (
                ("runs", run, "RunRecord"),
                ("tasks", task, "TaskRecord"),
            ):
                base = row.revision
                changed = {**row.payload, "revision": base + 1, "frame_ref": frame_ref}
                await tx.write(namespace, row.resource_id, schema, changed, base)
                if namespace == "runs":
                    await tx.emit(
                        inputs.run["conversation_id"],
                        "run.updated",
                        changed,
                        base_revision=base,
                        result_revision=base + 1,
                    )
            item_id = "understanding-" + task_id
            try:
                item_row = await tx.load("items", item_id)
                item_base, item_created = item_row.revision, item_row.payload["created_at"]
            except StoreMissing:
                item_base, item_created = 0, value["created_at"]
            item = {
                "id": item_id,
                "conversation_id": inputs.run["conversation_id"],
                "run_id": inputs.run["id"],
                "type": "understanding",
                "status": "completed",
                "revision": item_base + 1,
                "text": value["summary"],
                "resource_refs": [frame_ref, *inputs.refs],
                "created_at": item_created,
                "updated_at": value["created_at"],
            }
            await tx.write("items", item_id, "InteractionItem", item, item_base)
            await tx.emit(
                inputs.run["conversation_id"],
                "task.frame.committed",
                value,
                base_revision=expected,
                result_revision=next_revision,
            )
            await tx.emit(
                inputs.run["conversation_id"],
                "item.updated",
                item,
                item_ref=reference("item", item_id, item_base + 1),
                base_revision=item_base,
                result_revision=item_base + 1,
            )
            result = {
                "kind": "ok",
                "payload": value,
                "revision": next_revision,
                "output_refs": [frame_ref],
            }
            validate_contract("RuntimeIntentruntimeUnderstandResult", result)
            await tx.write(
                "intent.receipts",
                ctx.attempt_id,
                "IntentReceipt",
                {
                    "request_hash": digest,
                    "run_id": inputs.run["id"],
                    "input_revision": inputs.state["revision"],
                    "frame_ref": frame_ref,
                    "result": result,
                },
            )
            return result

        return await self.transactions.execute(
            ctx.principal,
            f"conversation:{inputs.run['conversation_id']}",
            RequestMeta(
                request_id="intent-publish-" + hashlib.sha256(ctx.attempt_id.encode()).hexdigest(),
                schema_version="0.1",
            ),
            {"hash": digest},
            write,
        )
