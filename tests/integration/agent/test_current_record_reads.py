"""Real READ COMMITTED visibility, task isolation and cleanup; no permission cache."""

import asyncio

import pytest
from sqlalchemy import text

from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.shared.stores import StoreMissing


async def test_current_scope_observes_external_change_and_tombstone(database, principal):
    records = PostgresRecordStore(database)
    await records.put(
        principal,
        "current-test",
        "record",
        "Acknowledgement",
        {"operation_id": "before", "status": "completed"},
        expected_revision=0,
        request_id="before",
    )
    async with records.current_reads():
        scope = records._current_reads.get()
        assert await scope[1].scalar(text("SHOW transaction_isolation")) == "read committed"
        before = await records.get(principal, "current-test", "record")

        async def changed():
            await records.put(
                principal,
                "current-test",
                "record",
                "Acknowledgement",
                {"operation_id": "after", "status": "completed"},
                expected_revision=1,
                request_id="after",
            )

        await asyncio.create_task(changed())
        after = await records.get(principal, "current-test", "record")
        assert after.revision == 2 and after.payload["operation_id"] == "after"
        assert before.payload["operation_id"] == "before"  # Detached result, not ORM identity.
        await records.delete(
            principal, "current-test", "record", expected_revision=2, request_id="delete"
        )
        with pytest.raises(StoreMissing):
            await records.get(principal, "current-test", "record")
    assert records._current_reads.get() is None


async def test_cancelled_scope_drains_session_and_resets_own_context(database):
    records = PostgresRecordStore(database)
    ready = asyncio.Event()
    released = asyncio.Event()

    async def owner():
        try:
            async with records.current_reads():
                assert await records._current_reads.get()[1].scalar(text("SELECT 1")) == 1
                ready.set()
                await asyncio.Event().wait()
        finally:
            assert records._current_reads.get() is None
            released.set()

    task = asyncio.create_task(owner())
    async with asyncio.timeout(10):
        await ready.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    assert released.is_set()
    async with records.current_reads():
        assert await records._current_reads.get()[1].scalar(text("SELECT 1")) == 1


async def test_inherited_child_task_never_shares_parent_async_session(database):
    records = PostgresRecordStore(database)
    async with records.current_reads():
        parent = records._current_reads.get()[1]
        async with records.current_reads():
            assert records._current_reads.get()[1] is parent

        async def child():
            async with records._read_session() as own:
                assert own is not parent
                assert await own.scalar(text("SELECT 1")) == 1
            async with records.current_reads():
                assert records._current_reads.get()[1] is not parent

        await asyncio.gather(child(), child())
        assert await parent.scalar(text("SELECT 1")) == 1
    assert records._current_reads.get() is None
