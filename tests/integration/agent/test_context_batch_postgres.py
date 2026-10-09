"""Actual single-statement batch views, historical reads, deletion and isolation."""

import pytest
from sqlalchemy import event

from uaw.context.contracts import RecordReadKey
from uaw.infrastructure.db.context_batch import PostgresContextRecordBatch
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.shared.errors import DomainError
from uaw.shared.stores import StoreMissing


def input_record(identifier, text):
    return {
        "id": identifier,
        "conversation_id": "conversation",
        "turn_id": "turn",
        "text": text,
        "attachment_refs": [],
        "created_at": "2026-10-09T00:00:00Z",
    }


@pytest.fixture
async def batch_case(database, principal):
    store = PostgresRecordStore(database)
    for name in ("a", "b"):
        await store.put(
            principal,
            "context.test",
            name,
            "InputRecord",
            input_record(name, name),
            expected_revision=0,
            request_id="create-" + name,
        )
    await store.put(
        principal,
        "context.test",
        "a",
        "InputRecord",
        input_record("a", "new"),
        expected_revision=1,
        request_id="revise",
    )
    return store, PostgresContextRecordBatch(store)


async def test_batch_preserves_order_duplicates_and_history_in_one_statement(batch_case, principal):
    store, batch = batch_case
    statements = []

    def observe(*args):
        statements.append(args[2])

    event.listen(store.database.engine.sync_engine, "before_cursor_execute", observe)
    try:
        keys = (
            RecordReadKey("context.test", "b"),
            RecordReadKey("context.test", "a", 1),
            RecordReadKey("context.test", "a"),
            RecordReadKey("context.test", "b"),
        )
        rows = await batch.read(principal, keys)
    finally:
        event.remove(store.database.engine.sync_engine, "before_cursor_execute", observe)
    assert len(statements) == 1
    assert [r.resource_id for r in rows] == ["b", "a", "a", "b"]
    assert [r.revision for r in rows] == [1, 1, 2, 1]
    assert rows[1].payload["text"] == "a"
    assert rows[2].payload["text"] == "new"
    rows[0].payload["text"] = "mutated"
    assert rows[3].payload["text"] == "b"


async def test_batch_missing_member_denies_entire_result(batch_case, principal):
    _, batch = batch_case
    with pytest.raises(StoreMissing):
        await batch.read(
            principal,
            (RecordReadKey("context.test", "a"), RecordReadKey("context.test", "missing")),
        )
    with pytest.raises(StoreMissing):
        await batch.read(principal, (RecordReadKey("context.test", "a", 99),))


async def test_batch_deleted_resource_cannot_reveal_history(batch_case, principal):
    store, batch = batch_case
    await store.delete(principal, "context.test", "a", expected_revision=2, request_id="delete")
    with pytest.raises(StoreMissing):
        await batch.read(principal, (RecordReadKey("context.test", "a", 1),))


async def test_batch_foreign_owner_and_wrong_kind_fail(batch_case, principal):
    _, batch = batch_case
    with pytest.raises(StoreMissing):
        await batch.read(
            principal.model_copy(update={"id": "another-owner"}),
            (RecordReadKey("context.test", "a"),),
        )
    with pytest.raises(DomainError):
        await batch.read(principal.model_copy(update={"kind": "service"}), ())


@pytest.mark.parametrize("revision", [True, 0, -1, 2147483648])
async def test_batch_invalid_revision_never_queries(batch_case, principal, revision):
    _, batch = batch_case
    with pytest.raises(DomainError):
        await batch.read(principal, (RecordReadKey("context.test", "a", revision),))


async def test_batch_empty_and_capacity(batch_case, principal):
    _, batch = batch_case
    assert await batch.read(principal, ()) == ()
    with pytest.raises(DomainError):
        await batch.read(principal, (RecordReadKey("context.test", "a"),) * 129)
