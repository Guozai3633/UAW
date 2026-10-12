"""Real SQL change signals; unchanged polls never grant or revalidate execution."""

import asyncio

import pytest
from sqlalchemy import event, update

from tests.integration.agent.test_checked_record_batch import saved
from uaw.infrastructure.db.models import RecordVersionRow
from uaw.shared.stores import StoreConflict, StoreMissing


@pytest.mark.parametrize("change", ["current", "historical", "absent", "tombstone"])
async def test_watch_fresh_poll_detects_each_source_change_without_repeating_read(
    database, principal, change
):
    store = await saved(database, principal)
    store._checked_metadata = False
    polling = asyncio.Event()
    reads = 0
    polls = 0
    original = store._witness_rows
    statements = []
    owner = asyncio.current_task()

    def capture(_connection, _cursor, statement, _parameters, _context, _many):
        if (
            asyncio.current_task() is owner
            and statement.lstrip().upper().startswith("SELECT")
            and "uaw_records" in statement
        ):
            statements.append(statement)

    async def witness(*args):
        nonlocal polls
        assert store._current_batch.get() is None
        if polls:
            assert store._read_witness.get() is None and store._current_reads.get() is None
        result = await original(*args)
        polls += 1
        if polls == 3:
            polling.set()
        return result

    async def read():
        nonlocal reads
        reads += 1
        await store.get(principal, "checked-batch-test", "record")
        await store.get(principal, "checked-batch-test", "record", revision=1)
        with pytest.raises(StoreMissing):
            await store.get(principal, "checked-batch-test", "new")

    async def mutate():
        await polling.wait()
        if change == "current":
            await store.put(
                principal,
                "checked-batch-test",
                "record",
                "Acknowledgement",
                {"operation_id": "after", "status": "completed"},
                expected_revision=1,
                request_id="after",
            )
        elif change == "historical":
            async with database.sessions.begin() as session:
                await session.execute(
                    update(RecordVersionRow)
                    .where(
                        RecordVersionRow.principal_id == principal.id,
                        RecordVersionRow.namespace == "checked-batch-test",
                        RecordVersionRow.resource_id == "record",
                        RecordVersionRow.revision == 1,
                    )
                    .values(payload={"operation_id": "changed-history", "status": "completed"})
                )
        elif change == "absent":
            await store.put(
                principal,
                "checked-batch-test",
                "new",
                "Acknowledgement",
                {"operation_id": "created", "status": "completed"},
                expected_revision=0,
                request_id="new",
            )
        else:
            await store.delete(
                principal,
                "checked-batch-test",
                "record",
                expected_revision=1,
                request_id="delete",
            )

    event.listen(database.engine.sync_engine, "before_cursor_execute", capture)
    store._witness_rows = witness
    mutation = asyncio.create_task(mutate())
    try:
        result = await store.wait_for_read_change(
            read, deadline=asyncio.get_running_loop().time() + 3, check=lambda: None
        )
        await mutation
        assert result is None and reads == 1 and polls >= 4
        # Two unchanged polls and the final changed poll each use one fresh
        # statement. No semantic read callback or open connection over sleep.
        assert all("UNION ALL" in text for text in statements[3:])
        assert store._read_witness.get() is None and store._current_reads.get() is None
    finally:
        mutation.cancel()
        await asyncio.gather(mutation, return_exceptions=True)
        event.remove(database.engine.sync_engine, "before_cursor_execute", capture)


async def test_watch_original_deadline_interrupts_poll_io_and_drops_scope(database, principal):
    store = await saved(database, principal)
    store._checked_metadata = False
    original = store._witness_rows
    polls = 0

    async def read():
        await store.get(principal, "checked-batch-test", "record")

    async def delayed(*args):
        nonlocal polls
        polls += 1
        if polls > 1:
            await asyncio.sleep(5)
        return await original(*args)

    store._witness_rows = delayed
    with pytest.raises(TimeoutError):
        await store.wait_for_read_change(
            read, deadline=asyncio.get_running_loop().time() + 0.3, check=lambda: None
        )
    assert polls == 2
    assert store._read_witness.get() is None and store._current_reads.get() is None
    assert (await store.get(principal, "checked-batch-test", "record")).revision == 1


async def test_watch_rejects_empty_or_existing_read_scopes(database, principal):
    store = await saved(database, principal)

    async def empty():
        pass

    with pytest.raises(StoreConflict) as missing:
        await store.wait_for_read_change(
            empty, deadline=asyncio.get_running_loop().time() + 1, check=lambda: None
        )
    assert missing.value.failure.code == "current_watch_sources_missing"
    async with store.current_reads():
        with pytest.raises(StoreConflict) as nested:
            await store.wait_for_read_change(
                empty, deadline=asyncio.get_running_loop().time() + 1, check=lambda: None
            )
    assert nested.value.failure.code == "current_watch_scope_denied"
