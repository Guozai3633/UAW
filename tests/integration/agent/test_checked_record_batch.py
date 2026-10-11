"""Fresh SQL witnesses, detached inputs and cancellation for one metadata pass."""

import asyncio

import pytest
from sqlalchemy import event, update

from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.shared.stores import StoreConflict, StoreMissing


async def saved(database, principal):
    store = PostgresRecordStore(database, checked_metadata=True)
    await store.put(
        principal,
        "checked-batch-test",
        "record",
        "Acknowledgement",
        {"operation_id": "before", "status": "completed"},
        expected_revision=0,
        request_id="before",
    )
    return store


@pytest.mark.parametrize("change", ["none", "update", "delete", "revert", "payload", "schema"])
async def test_final_witness_rejects_every_changed_row(database, principal, change):
    store = await saved(database, principal)

    async def consume():
        async with store.checked_read_batch():
            before = await store.get(principal, "checked-batch-test", "record")
            before.payload["operation_id"] = "local-copy"
            if change in {"update", "revert"}:
                await store.put(
                    principal,
                    "checked-batch-test",
                    "record",
                    "Acknowledgement",
                    {"operation_id": "after", "status": "completed"},
                    expected_revision=1,
                    request_id="after",
                )
                if change == "revert":
                    await store.put(
                        principal,
                        "checked-batch-test",
                        "record",
                        "Acknowledgement",
                        {"operation_id": "before", "status": "completed"},
                        expected_revision=2,
                        request_id="revert",
                    )
            elif change == "delete":
                await store.delete(
                    principal,
                    "checked-batch-test",
                    "record",
                    expected_revision=1,
                    request_id="delete",
                )
            elif change in {"payload", "schema"}:
                async with database.sessions.begin() as session:
                    values = (
                        {"payload": {"operation_id": "after", "status": "completed"}}
                        if change == "payload"
                        else {"schema_name": "UnexpectedSchema"}
                    )
                    await session.execute(
                        update(RecordRow)
                        .where(
                            RecordRow.principal_id == principal.id,
                            RecordRow.namespace == "checked-batch-test",
                            RecordRow.resource_id == "record",
                        )
                        .values(**values)
                    )
            current_input = await store.get(principal, "checked-batch-test", "record")
            assert current_input.payload["operation_id"] == "before"
            assert current_input is not before

    if change == "none":
        await consume()
    else:
        with pytest.raises(StoreConflict) as denied:
            await consume()
        assert denied.value.failure.code == "current_read_source_changed"
    assert store._current_batch.get() is None
    assert store._current_reads.get() is None


async def test_duplicates_use_one_lookup_and_one_fresh_full_witness(database, principal):
    store = await saved(database, principal)
    queries = []

    def capture(_connection, _cursor, statement, _parameters, _context, _many):
        if statement.lstrip().upper().startswith("SELECT") and "uaw_records" in statement:
            queries.append(statement)

    event.listen(database.engine.sync_engine, "before_cursor_execute", capture)
    try:
        async with store.checked_read_batch():
            for _ in range(20):
                assert (await store.get(principal, "checked-batch-test", "record")).revision == 1
        assert len(queries) == 2
        assert " IN " in queries[-1]
        async with store.checked_read_batch():
            assert (await store.get(principal, "checked-batch-test", "record")).revision == 1
        assert len(queries) == 4  # Later passes never reuse the prior input.
    finally:
        event.remove(database.engine.sync_engine, "before_cursor_execute", capture)


async def test_child_task_reads_new_state_and_parent_witness_rejects(database, principal):
    store = await saved(database, principal)
    with pytest.raises(StoreConflict):
        async with store.checked_read_batch():
            await store.get(principal, "checked-batch-test", "record")
            parent = store._current_reads.get()[1]

            async def child():
                await store.put(
                    principal,
                    "checked-batch-test",
                    "record",
                    "Acknowledgement",
                    {"operation_id": "child", "status": "completed"},
                    expected_revision=1,
                    request_id="child",
                )
                async with store.checked_read_batch():
                    assert store._current_reads.get()[1] is not parent
                    current = await store.get(principal, "checked-batch-test", "record")
                    assert current.payload["operation_id"] == "child"

            await asyncio.create_task(child())
    assert store._current_batch.get() is None


async def test_cancelled_batch_releases_input_and_sql_scope(database, principal):
    store = await saved(database, principal)
    ready = asyncio.Event()

    async def consume():
        try:
            async with store.checked_read_batch():
                await store.get(principal, "checked-batch-test", "record")
                ready.set()
                await asyncio.Event().wait()
        finally:
            assert store._current_batch.get() is None
            assert store._current_reads.get() is None

    task = asyncio.create_task(consume())
    async with asyncio.timeout(5):
        await ready.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    assert (await store.get(principal, "checked-batch-test", "record")).revision == 1


async def test_historical_read_still_checks_current_tombstone(database, principal):
    store = await saved(database, principal)
    async with store.checked_read_batch():
        before = await store.get(principal, "checked-batch-test", "record", revision=1)
        assert before.revision == 1
        await store.delete(
            principal, "checked-batch-test", "record", expected_revision=1, request_id="delete"
        )
        with pytest.raises(StoreMissing):
            await store.get(principal, "checked-batch-test", "record", revision=1)


async def test_nested_source_wait_cannot_escape_outer_witness(database, principal):
    store = await saved(database, principal)
    with pytest.raises(StoreConflict):
        async with store.checked_read_batch():
            outer = store._current_batch.get()[1]
            async with store.checked_read_batch():
                assert store._current_batch.get()[1] is outer
                await store.get(principal, "checked-batch-test", "record")
                await store.delete(
                    principal,
                    "checked-batch-test",
                    "record",
                    expected_revision=1,
                    request_id="delete-nested",
                )
            assert store._current_batch.get()[1] is outer
    assert store._current_batch.get() is None


async def test_default_mode_keeps_every_read_fresh(database, principal):
    await saved(database, principal)
    store = PostgresRecordStore(database)
    assert store.checked_metadata is False
    async with store.checked_read_batch():
        assert store._current_batch.get() is None
        assert (await store.get(principal, "checked-batch-test", "record")).revision == 1
        await store.put(
            principal,
            "checked-batch-test",
            "record",
            "Acknowledgement",
            {"operation_id": "after", "status": "completed"},
            expected_revision=1,
            request_id="default-after",
        )
        after = await store.get(principal, "checked-batch-test", "record")
        assert after.revision == 2 and after.payload["operation_id"] == "after"
    assert store._current_reads.get() is None
