"""Append original input and stable interaction identity within the Run transaction."""

from typing import Any

from uaw.infrastructure.db.transactions import RecordTransaction, identifier, reference, timestamp


async def append_input(
    tx: RecordTransaction,
    conversation_id: str,
    turn_id: str,
    text: str,
    attachments: list[dict[str, Any]],
    *,
    run_id: str | None = None,
    original: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "id": identifier("input"),
        "conversation_id": conversation_id,
        "turn_id": turn_id,
        "text": text,
        "attachment_refs": attachments,
        "created_at": timestamp(),
    }
    if original:
        value = dict(original)
    await tx.write("inputs", value["id"], "InputRecord", value)
    item: dict[str, Any] = {
        "id": identifier("item"),
        "conversation_id": conversation_id,
        "type": "user_message",
        "status": "completed",
        "revision": 1,
        "text": text,
        "resource_refs": [reference("input", value["id"])],
        "created_at": value["created_at"],
        "updated_at": value["created_at"],
    }
    if run_id:
        item["run_id"] = run_id
    await tx.write("items", item["id"], "InteractionItem", item)
    await tx.emit(conversation_id, "input.committed", value)
    await tx.emit(conversation_id, "item.updated", item, item_ref=reference("item", item["id"]))
    return value
