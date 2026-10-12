"""Final single-statement evidence, including history and absence; no input cache."""

import asyncio

import pytest
from sqlalchemy import event, update

from tests.integration.agent.test_checked_record_batch import saved
from uaw.infrastructure.db.models import RecordVersionRow
from uaw.shared.stores import StoreConflict, StoreMissing


@pytest.mark.parametrize("change", ["current", "historical", "absent", "tombstone"])
async def test_final_fresh_witness_rejects_changed_dependency(database, principal, change):
    store = await saved(database, principal)
    store._checked_metadata = False
    with pytest.raises(StoreConflict) as denied:
        async with store.current_witness():
            if change == "absent":
                with pytest.raises(StoreMissing):
                    await store.get(principal, "checked-batch-test", "new")
                await store.put(
                    principal,
                    "checked-batch-test",
                    "new",
                    "Acknowledgement",
                    {"operation_id": "new", "status": "completed"},
                    expected_revision=0,
                    request_id="created",
                )
            else:
                await store.get(principal, "checked-batch-test", "record")
                await store.get(principal, "checked-batch-test", "record", revision=1)
                if change == "current":
                    await store.put(
                        principal,
                        "checked-batch-test",
                        "record",
                        "Acknowledgement",
                        {"operation_id": "after", "status": "completed"},
                        expected_revision=1,
                        request_id="changed",
                    )
                elif change == "tombstone":
                    await store.delete(
                        principal,
                        "checked-batch-test",
                        "record",
                        expected_revision=1,
                        request_id="deleted",
                    )
                else:
                    async with database.sessions.begin() as session:
                        await session.execute(
                            update(RecordVersionRow)
                            .where(
                                RecordVersionRow.principal_id == principal.id,
                                RecordVersionRow.namespace == "checked-batch-test",
                                RecordVersionRow.resource_id == "record",
                                RecordVersionRow.revision == 1,
                            )
                            .values(
                                payload={"operation_id": "changed-history", "status": "completed"}
                            )
                        )
    assert denied.value.failure.code == "current_read_source_changed"
    assert store._read_witness.get() is None and store._current_reads.get() is None


async def test_witness_preserves_fresh_gets_and_one_final_statement(database, principal):
    store = await saved(database, principal)
    store._checked_metadata = False
    queries = []

    def capture(_connection, _cursor, statement, _parameters, _context, _many):
        if statement.lstrip().upper().startswith("SELECT") and "uaw_records" in statement:
            queries.append(statement)

    event.listen(database.engine.sync_engine, "before_cursor_execute", capture)
    try:
        async with store.current_witness():
            for _ in range(3):
                row = await store.get(principal, "checked-batch-test", "record")
                row.payload["operation_id"] = "local-mutation"
            await store.get(principal, "checked-batch-test", "record", revision=1)
            assert store._current_batch.get() is None
        assert len(queries) == 5 and "UNION ALL" in queries[-1]
    finally:
        event.remove(database.engine.sync_engine, "before_cursor_execute", capture)


async def test_witness_cancellation_and_child_task_are_isolated(database, principal):
    store = await saved(database, principal)
    store._checked_metadata = False
    ready = asyncio.Event()

    async def consume():
        try:
            async with store.current_witness():
                await store.get(principal, "checked-batch-test", "record")
                parent = store._read_witness.get()

                async def child():
                    async with store.current_witness():
                        assert store._read_witness.get() is not parent
                        await store.get(principal, "checked-batch-test", "record", revision=1)

                await asyncio.create_task(child())
                ready.set()
                await asyncio.Event().wait()
        finally:
            assert store._read_witness.get() is None and store._current_reads.get() is None

    task = asyncio.create_task(consume())
    async with asyncio.timeout(5):
        await ready.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
