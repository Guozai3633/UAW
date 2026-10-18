"""Original-call display checkpoints. Reading/recovering never repeats a model send."""

from time import monotonic
from typing import Any

from sqlalchemy import select

from uaw.agent.contracts import identifier
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import (
    RecordTransaction,
    TransactionalStore,
    reference,
    timestamp,
)
from uaw.model.contracts import (
    ProviderFailure,
    ProviderObservation,
    ProviderRequest,
    ProviderResponse,
)
from uaw.model.stream_text import ReplyText
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing

NAMESPACE = "run.conversation.streams"
Payload = dict[str, Any]


class ConversationStreams:
    def __init__(self, records: PostgresRecordStore) -> None:
        self.records = records
        self.transactions = TransactionalStore(records.database)

    async def open(
        self, request: ProviderRequest, ctx: TrustedExecutionContext, invocation_id: str
    ) -> ConversationStream | None:
        from uaw.shared.conversation import first_decision_schema

        if request.protocol != "json_schema" or request.output_schema != first_decision_schema():
            return None
        operation_id = identifier(
            "agent-op-",
            {
                "agent": (await self.records.get(ctx.principal, "runs", ctx.run_id or ""))
                .payload.get("root_agent_ref", {})
                .get("id"),
                "operation": ctx.operation_id,
            },
        )

        async def write(tx: RecordTransaction) -> Payload:
            run = await tx.load("runs", ctx.run_id or "")
            operation = await tx.load("agent.loop.operations", operation_id)
            inputs = await tx.load("run.input_sets", ctx.run_id or "")
            frame = await tx.load("intent.frames", ctx.task_id or "")
            ledger = await tx.load("budget.ledgers", ctx.run_id or "")
            invocation = await tx.load("model.invocations", invocation_id)
            if (
                run.payload["status"] != "running"
                or run.payload["conversation_id"] != ctx.conversation_id
                or inputs.revision != frame.payload["input_revision"]
                or ledger.payload["cancel_requested"]
                or invocation.payload["state"] != "claimed"
                or invocation.payload["request"]["context_snapshot_ref"]
                != operation.payload["snapshot_ref"]
                or invocation.payload["request"]["model_config"] != request.config
                or operation.payload["context"] != ctx.wire()
                or operation.payload["phase"] != "prepared"
            ):
                raise reject("conversation_stream_stale", "Original model/Run/input required", 412)
            existing = await optional(tx, NAMESPACE, invocation_id)
            if existing:
                raise reject("conversation_stream_pending", "Original stream cannot be resent", 409)
            now = timestamp()
            value = {
                "id": invocation_id,
                "revision": 1,
                "run_id": ctx.run_id,
                "conversation_id": ctx.conversation_id,
                "operation_id": operation_id,
                "item_id": identifier("conversation-message-", {"operation": operation_id}),
                "input_revision": inputs.revision,
                "attempt_id": ctx.attempt_id,
                "snapshot_ref": operation.payload["snapshot_ref"],
                "model_config": request.config,
                "state": "receiving",
                "text": "",
                "created_at": now,
                "updated_at": now,
                "provider_chunks": 0,
                "persisted_chunks": 0,
            }
            await tx.write(NAMESPACE, invocation_id, "ConversationStreamRecord", value)
            return value

        value = await self.transactions.inspect(
            ctx.principal, "conversation:" + (ctx.conversation_id or ""), write
        )
        return ConversationStream(self, ctx, value)


async def optional(tx: RecordTransaction, namespace: str, key: str) -> Payload | None:
    try:
        return (await tx.load(namespace, key)).payload
    except StoreMissing:
        return None


class ConversationStream:
    def __init__(
        self, owner: ConversationStreams, ctx: TrustedExecutionContext, value: Payload
    ) -> None:
        self.owner, self.ctx, self.value = owner, ctx, value
        self.parser = ReplyText()
        self.last_write = 0.0
        self.provider_chunks = 0
        self.first_provider: str | None = None
        self.first_text: str | None = None
        self.observation: ProviderObservation | None = None

    async def content(self, delta: str) -> None:
        self.provider_chunks += 1
        self.first_provider = self.first_provider or timestamp()
        text = self.parser.feed(delta)
        if text:
            self.first_text = self.first_text or timestamp()
        if text != self.value["text"] and (
            not self.value["text"] or monotonic() - self.last_write >= 0.12
        ):
            await self.checkpoint(text)

    async def checkpoint(
        self, text: str, *, state: str = "receiving", failure: str | None = None
    ) -> None:
        ctx = self.ctx

        async def write(tx: RecordTransaction) -> Payload:
            row = await tx.load(NAMESPACE, self.value["id"])
            old = dict(row.payload)
            if old != self.value or old["state"] not in ("receiving", "received"):
                raise reject("conversation_stream_conflict", "Original stream changed", 409)
            run = await tx.load("runs", old["run_id"])
            inputs = await tx.load("run.input_sets", old["run_id"])
            ledger = await tx.load("budget.ledgers", old["run_id"])
            current = (
                inputs.revision == old["input_revision"]
                and not ledger.payload["cancel_requested"]
                and run.payload["status"] == "running"
            )
            if not current and state != "interrupted":
                raise reject(
                    "conversation_stream_stale", "Original input cancelled or changed", 412
                )
            if not text.startswith(old["text"]) or len(text) > 16384:
                raise reject(
                    "conversation_stream_text_bound", "Original bounded prefix required", 412
                )
            now = timestamp()
            changed = {
                **old,
                "revision": row.revision + 1,
                "state": state,
                "text": text,
                "updated_at": now,
                "provider_chunks": self.provider_chunks,
                "persisted_chunks": old["persisted_chunks"] + int(text != old["text"]),
            }
            if self.first_provider:
                changed["first_provider_at"] = self.first_provider
            if self.first_text:
                changed["first_text_at"] = self.first_text
            if self.observation is not None:
                for field in (
                    "started_at",
                    "headers_at",
                    "first_content_at",
                    "last_content_at",
                    "ended_at",
                ):
                    observed = getattr(self.observation, field)
                    if observed is not None:
                        changed["provider_" + field] = observed
            if state == "received":
                changed["received_at"] = now
            if failure:
                changed["failure_code"] = failure
            item = await optional(tx, "items", old["item_id"])
            if text and (item is None or item["status"] == "in_progress"):
                base = item["revision"] if item else 0
                value = {
                    "id": old["item_id"],
                    "conversation_id": ctx.conversation_id,
                    "run_id": ctx.run_id,
                    "type": "agent_message",
                    "status": "in_progress" if state != "interrupted" else "failed",
                    "revision": base + 1,
                    "text": text,
                    "resource_refs": [],
                    "created_at": item["created_at"] if item else now,
                    "updated_at": now,
                }
                await tx.write("items", old["item_id"], "InteractionItem", value, base)
                await tx.emit(
                    ctx.conversation_id or "",
                    "item.updated",
                    value,
                    item_ref=reference("item", old["item_id"], base + 1),
                    base_revision=base,
                    result_revision=base + 1,
                )
            await tx.write(
                NAMESPACE, old["id"], "ConversationStreamRecord", changed, old["revision"]
            )
            return changed

        self.value = await self.owner.transactions.inspect(
            ctx.principal, "conversation:" + (ctx.conversation_id or ""), write
        )
        self.last_write = monotonic()

    async def finish(
        self,
        response: ProviderResponse | None,
        failure: ProviderFailure | None,
        observation: ProviderObservation | None = None,
    ) -> None:
        self.observation = observation
        if failure is not None:
            # On superseded/cancelled input retain only the last committed prefix.
            await self.checkpoint(
                self.value["text"], state="interrupted", failure=failure.failure.code
            )
            return
        assert response is not None
        data = response.structured_data or {}
        text = self.parser.displayed
        if text and (
            response.finish_reason != "stop"
            or data.get("action") != "reply"
            or data.get("text") != text
        ):
            await self.checkpoint(
                self.value["text"], state="interrupted", failure="conversation_stream_final_invalid"
            )
            return
        await self.checkpoint(text, state="received")


async def finish_item(tx: RecordTransaction, invocation_id: str, item: Payload) -> Payload:
    """Called inside the original, fully verified final publication transaction."""
    stream = await optional(tx, NAMESPACE, invocation_id)
    if stream is None:
        return item
    validate_contract("ConversationStreamRecord", stream)
    if (
        stream["state"] != "received"
        or stream["item_id"] != item["id"]
        or (stream["text"] and stream["text"] != item["text"])
    ):
        raise reject("conversation_stream_publication_stale", "Original full reply differs", 412)
    existing = await optional(tx, "items", item["id"])
    if existing:
        if existing["status"] != "in_progress" or existing["run_id"] != item["run_id"]:
            raise reject("conversation_stream_item_stale", "Original pending message required", 412)
        item = {**item, "revision": existing["revision"] + 1, "created_at": existing["created_at"]}
    await tx.write(
        NAMESPACE,
        invocation_id,
        "ConversationStreamRecord",
        {
            **stream,
            "state": "published",
            "revision": stream["revision"] + 1,
            "updated_at": timestamp(),
            "output_ref": reference("content", stream["attempt_id"]),
        },
        stream["revision"],
    )
    return item


async def interrupt_run(tx: RecordTransaction, run_id: str, reason: str) -> None:
    """A stopped original job closes display only, including unknown provider effects."""
    rows = list(
        await tx.session.scalars(
            select(RecordRow).where(
                RecordRow.principal_id == tx.owner,
                RecordRow.namespace == NAMESPACE,
                RecordRow.deleted.is_(False),
                RecordRow.payload["run_id"].as_string() == run_id,
                RecordRow.payload["state"].as_string().in_(("receiving", "received")),
            )
        )
    )
    for row in rows:
        old = dict(row.payload)
        now = timestamp()
        await tx.write(
            NAMESPACE,
            old["id"],
            "ConversationStreamRecord",
            {
                **old,
                "state": "interrupted",
                "failure_code": reason,
                "revision": old["revision"] + 1,
                "updated_at": now,
            },
            old["revision"],
        )
        item = await optional(tx, "items", old["item_id"])
        if item and item["status"] == "in_progress":
            revision = item["revision"]
            changed = {**item, "revision": revision + 1, "status": "failed", "updated_at": now}
            await tx.write("items", item["id"], "InteractionItem", changed, revision)
            await tx.emit(
                old["conversation_id"],
                "item.updated",
                changed,
                item_ref=reference("item", item["id"], revision + 1),
                base_revision=revision,
                result_revision=revision + 1,
            )
