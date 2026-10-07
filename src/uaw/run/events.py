"""Signed, owner-bound pagination of committed events; replay has no execution path."""

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from pydantic import SecretStr
from sqlalchemy import func, select

from uaw.infrastructure.db.models import OutboxRow, RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.shared.contracts import Principal
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import parse_json, validate_contract


class EventReader:
    def __init__(self, store: PostgresRecordStore, signing_key: SecretStr | None) -> None:
        self.store = store
        self.signing_key = signing_key

    def _key(self) -> bytes:
        if self.signing_key is None:
            raise CapabilityUnavailable("signed_history_cursor")
        return self.signing_key.get_secret_value().encode()

    def _encode(self, value: dict[str, Any]) -> str:
        data = base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode()).rstrip(
            b"="
        )
        signature = hmac.new(self._key(), data, hashlib.sha256).hexdigest()
        return f"{data.decode()}.{signature}"

    def _decode(
        self, cursor: str, principal: Principal, conversation_id: str, kind: str
    ) -> dict[str, Any]:
        validate_contract("Cursor", cursor)
        try:
            data, signature = cursor.split(".")
            if not hmac.compare_digest(
                signature, hmac.new(self._key(), data.encode(), hashlib.sha256).hexdigest()
            ):
                raise ValueError
            value = parse_json(base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)))
            if (
                not isinstance(value, dict)
                or value.get("owner") != principal.id
                or value.get("conversation") != conversation_id
                or value.get("kind") != kind
                or value.get("expires", 0) < time.time()
            ):
                raise ValueError
            return value
        except ValueError, TypeError:
            raise reject(
                "cursor_invalid",
                "Cursor is invalid, expired or belongs to another scope",
                412,
                "conflict",
            ) from None

    async def read(
        self,
        principal: Principal,
        conversation_id: str,
        *,
        limit: int = 50,
        cursor: str | None = None,
        items: bool = False,
    ) -> dict[str, Any]:
        validate_contract("PageLimit", limit)
        await self.store.get(principal, "conversations", conversation_id)
        kind = "items" if items else "events"
        value = self._decode(cursor, principal, conversation_id, kind) if cursor else None
        async with self.store.database.sessions() as session:
            current = (
                await session.scalar(
                    select(func.max(OutboxRow.seq)).where(
                        OutboxRow.principal_id == principal.id,
                        OutboxRow.stream_id == conversation_id,
                    )
                )
            ) or 0
            watermark = value["watermark"] if value else current
            after = value["after"] if value else 0
            filters = [
                OutboxRow.principal_id == principal.id,
                OutboxRow.stream_id == conversation_id,
                OutboxRow.seq <= watermark,
            ]
            if items:
                # Last committed version of every stable Item at the fixed page watermark.
                latest = (
                    select(
                        OutboxRow.event_id,
                        OutboxRow.seq,
                        func.row_number()
                        .over(
                            partition_by=OutboxRow.payload["parameters"]["id"].astext,
                            order_by=OutboxRow.seq.desc(),
                        )
                        .label("rank"),
                    )
                    .where(*filters, OutboxRow.event_type == "item.updated")
                    .subquery()
                )
                query = (
                    select(OutboxRow)
                    .join(latest, OutboxRow.event_id == latest.c.event_id)
                    .where(latest.c.rank == 1, latest.c.seq > after)
                    .order_by(OutboxRow.seq)
                    .limit(limit + 1)
                )
            else:
                query = (
                    select(OutboxRow)
                    .where(*filters, OutboxRow.seq > after)
                    .order_by(OutboxRow.seq)
                    .limit(limit + 1)
                )
            rows = list((await session.scalars(query)).all())
            page_rows = rows[:limit]
            entries = []
            for row in page_rows:
                if items:
                    entries.append(row.payload["parameters"])
                else:
                    event = await session.get(RecordRow, (principal.id, "events", row.event_id))
                    if event is None or event.deleted:
                        raise reject(
                            "snapshot_required",
                            "Event history is no longer available",
                            410,
                            "dependency",
                        )
                    entries.append(event.payload)
            result = {"items": entries, "snapshot_revision": watermark}
            if len(rows) > limit:
                result["next_cursor"] = self._encode(
                    {
                        "owner": principal.id,
                        "conversation": conversation_id,
                        "kind": kind,
                        "after": page_rows[-1].seq,
                        "watermark": watermark,
                        "expires": value["expires"] if value else int(time.time()) + 3600,
                    }
                )
        validate_contract("ItemPage" if items else "EventPage", result)
        return result
