"""Source evidence includes advisory transactions, not just RecordStore.get."""

import asyncio

import pytest

from tests.integration.agent.test_checked_record_batch import saved
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import TransactionalStore
from uaw.shared.stores import StoreConflict, StoreMissing


@pytest.mark.parametrize("change", ["update", "absent", "tombstone"])
async def test_transactional_inputs_participate_in_final_source_comparison(
    database, principal, change
):
    store = await saved(database, principal)
    transactions = TransactionalStore(database)

    async def read(tx):
        if change == "absent":
            with pytest.raises(StoreMissing):
                await tx.load("checked-batch-test", "new")
            return {}
        row = await tx.load("checked-batch-test", "record")
        return dict(row.payload)

    with pytest.raises(StoreConflict) as denied:
        async with store.current_witness():
            await transactions.inspect(principal, "source-witness", read)
            if change == "tombstone":
                await store.delete(
                    principal,
                    "checked-batch-test",
                    "record",
                    expected_revision=1,
                    request_id="deleted",
                )
            else:
                await store.put(
                    principal,
                    "checked-batch-test",
                    "new" if change == "absent" else "record",
                    "Acknowledgement",
                    {"operation_id": "after", "status": "completed"},
                    expected_revision=0 if change == "absent" else 1,
                    request_id="after",
                )
    assert denied.value.failure.code == "current_read_source_changed"
    assert database._record_observers.get() is None and store._read_witness.get() is None


async def test_other_record_adapter_same_database_is_observed_and_child_is_isolated(
    database, principal
):
    store = await saved(database, principal)
    other = PostgresRecordStore(database)
    async with store.current_witness():
        parent = database._record_observers.get()
        await other.get(principal, "checked-batch-test", "record")
        assert store._read_witness.get()[1]

        async def child():
            async with other.current_witness():
                assert database._record_observers.get()[0] is asyncio.current_task()
                assert database._record_observers.get() is not parent
                await other.get(principal, "checked-batch-test", "record", revision=1)

        await asyncio.create_task(child())
        assert database._record_observers.get() is parent
        assert not store._read_witness.get()[2]
    assert database._record_observers.get() is None


async def test_transaction_only_watch_notifies_on_actual_change(database, principal):
    store = await saved(database, principal)
    transactions = TransactionalStore(database)
    polling = asyncio.Event()
    original = store._witness_rows
    polls = 0
    reads = 0

    async def witness(*args):
        nonlocal polls
        result = await original(*args)
        polls += 1
        if polls == 2:
            polling.set()
        return result

    async def read(tx):
        nonlocal reads
        reads += 1
        return dict((await tx.load("checked-batch-test", "record")).payload)

    async def initial():
        await transactions.inspect(principal, "transaction-watch", read)

    async def mutate():
        await polling.wait()
        await store.put(
            principal,
            "checked-batch-test",
            "record",
            "Acknowledgement",
            {"operation_id": "changed", "status": "completed"},
            expected_revision=1,
            request_id="changed",
        )

    store._witness_rows = witness
    mutation = asyncio.create_task(mutate())
    try:
        assert (
            await store.wait_for_read_change(
                initial, deadline=asyncio.get_running_loop().time() + 2, check=lambda: None
            )
            is None
        )
        await mutation
        assert reads == 1 and polls >= 3
    finally:
        mutation.cancel()
        await asyncio.gather(mutation, return_exceptions=True)
    assert database._record_observers.get() is None
