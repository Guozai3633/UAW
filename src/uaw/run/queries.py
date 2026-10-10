"""Owned read projections. A read never admits, retries or completes work."""

import time
from typing import Any

from sqlalchemy import delete, select

from uaw.infrastructure.db.models import RecordRow, RecordVersionRow, RequestRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore, identifier
from uaw.run.events import EventReader
from uaw.shared.contracts import Principal
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing

Payload = dict[str, Any]
SNAPSHOTS = "run.conversation.list.snapshots"
MAX_CONVERSATIONS = 4096


class RunQueries:
    def __init__(self, store: PostgresRecordStore, events: EventReader) -> None:
        self.store, self.events = store, events
        self.transactions = TransactionalStore(store.database)

    async def conversations(
        self, actor: Principal, *, limit: int = 20, cursor: str | None = None
    ) -> Payload:
        validate_contract("PageLimit", limit)
        value = (
            self.events._decode(cursor, actor, "conversation-list", "conversations")
            if cursor
            else None
        )
        if value:
            if set(value) != {"owner", "conversation", "kind", "snapshot", "after", "expires"}:
                raise reject("cursor_invalid", "Conversation cursor has invalid fields", 412)
            if type(value["after"]) is not int or value["after"] < 0:
                raise reject("cursor_invalid", "Conversation cursor has invalid offset", 412)
            try:
                snapshot = (await self.store.get(actor, SNAPSHOTS, value["snapshot"])).payload
            except StoreMissing:
                raise reject("snapshot_required", "Conversation snapshot expired", 410) from None
        else:
            # Same lock as creation: capture only committed conversations, once. Store fixed
            # versions rather than a wall-clock cutoff, which misses late commits/clock skew.
            async def capture(tx: RecordTransaction) -> Payload:
                expired = select(RecordRow.resource_id).where(
                    RecordRow.principal_id == actor.id,
                    RecordRow.namespace == SNAPSHOTS,
                    RecordRow.payload["expires"].as_integer() < int(time.time()),
                )
                await tx.session.execute(
                    delete(RecordVersionRow).where(
                        RecordVersionRow.principal_id == actor.id,
                        RecordVersionRow.namespace == SNAPSHOTS,
                        RecordVersionRow.resource_id.in_(expired),
                    )
                )
                await tx.session.execute(
                    delete(RecordRow).where(
                        RecordRow.principal_id == actor.id,
                        RecordRow.namespace == SNAPSHOTS,
                        RecordRow.resource_id.in_(expired),
                    )
                )
                rows = list(
                    await tx.session.scalars(
                        select(RecordRow)
                        .where(
                            RecordRow.principal_id == actor.id,
                            RecordRow.namespace == "conversations",
                            RecordRow.deleted.is_(False),
                        )
                        .order_by(RecordRow.updated_at.desc(), RecordRow.resource_id)
                        .limit(MAX_CONVERSATIONS + 1)
                    )
                )
                if len(rows) > MAX_CONVERSATIONS:
                    raise CapabilityUnavailable("conversation_snapshot_capacity")
                captured: Payload = {
                    "id": identifier("conversation-list"),
                    "expires": int(time.time()) + 3600,
                    "versions": [{"id": row.resource_id, "revision": row.revision} for row in rows],
                }
                if len(rows) > limit:
                    active = list(
                        await tx.session.scalars(
                            select(RecordRow.resource_id)
                            .where(
                                RecordRow.principal_id == actor.id,
                                RecordRow.namespace == SNAPSHOTS,
                            )
                            .limit(64)
                        )
                    )
                    if len(active) == 64:
                        raise CapabilityUnavailable("conversation_page_session_capacity")
                    await tx.write(SNAPSHOTS, captured["id"], "ConversationListSnapshot", captured)
                return captured

            snapshot = await self.transactions.inspect(actor, "conversations.create", capture)
        validate_contract("ConversationListSnapshot", snapshot)
        if snapshot["expires"] < time.time() or (value and value["expires"] != snapshot["expires"]):
            raise reject("cursor_invalid", "Conversation snapshot expired", 412)
        after = value["after"] if value else 0
        versions = snapshot["versions"]
        if after > len(versions):
            raise reject("cursor_invalid", "Conversation offset exceeds snapshot", 412)
        entries = []
        for pin in versions[after : after + limit]:
            try:
                row = await self.store.get(
                    actor, "conversations", pin["id"], revision=pin["revision"]
                )
            except StoreMissing:
                raise reject(
                    "snapshot_required", "Conversation snapshot is no longer available", 410
                ) from None
            validate_contract("Conversation", row.payload)
            if row.payload["owner_id"] != actor.id:
                raise reject("conversation_scope_denied", "Conversation owner differs", 403)
            entries.append(row.payload)
        result = {"items": entries, "snapshot_revision": len(versions)}
        if after + limit < len(versions):
            result["next_cursor"] = self.events._encode(
                {
                    "owner": actor.id,
                    "conversation": "conversation-list",
                    "kind": "conversations",
                    "snapshot": snapshot["id"],
                    "after": after + limit,
                    "expires": snapshot["expires"],
                }
            )
        validate_contract("ConversationPage", result)
        return result

    async def original_submission(
        self, actor: Principal, conversation_id: str, request_id: str
    ) -> Payload:
        validate_contract("ID", request_id)
        await self.store.get(actor, "conversations", conversation_id)
        async with self.store.database.sessions() as session:
            receipt = await session.get(
                RequestRow,
                (
                    actor.id,
                    "domain.requests",
                    f"conversation:{conversation_id}",
                    request_id,
                ),
            )
            if receipt is None:
                raise StoreMissing()
            original = receipt.result
            # The same aggregate also records cancellation and execution Items. Never treat
            # a receipt of another action as a submission, or manufacture a new Run.
            try:
                validate_contract("RunRecord", original)
            except ValueError:
                raise StoreMissing() from None
            if original["conversation_id"] != conversation_id:
                raise reject("submission_scope_denied", "Submission conversation differs", 403)
            row = await self.store.get(actor, "runs", original["id"])
            validate_contract("RunRecord", row.payload)
            if row.payload["conversation_id"] != conversation_id:
                raise reject("submission_scope_denied", "Current Run conversation differs", 403)
            return row.payload
