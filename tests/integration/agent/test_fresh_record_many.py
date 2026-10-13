"""Fresh grouped SQL reads retain owner isolation and full witness visibility."""

import asyncio

import pytest
from sqlalchemy import event

from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.shared.stores import StoreConflict, StoreMissing


async def seed(records, principal):
    for name in ("one", "two"):
        await records.put(
            principal,
            "fresh-many",
            name,
            "Acknowledgement",
            {"operation_id": name, "status": "completed"},
            expected_revision=0,
            request_id=name,
        )


async def test_grouped_read_is_one_query_ordered_detached_and_fresh(database, principal):
    records = PostgresRecordStore(database)
    await seed(records, principal)
    count = 0

    def observe(conn, cursor, statement, params, context, many):
        nonlocal count
        if statement.lstrip().upper().startswith("SELECT") and "uaw_records" in statement:
            count += 1

    event.listen(database.engine.sync_engine, "before_cursor_execute", observe)
    try:
        async with records.current_reads():
            first = await records.get_current_many(
                principal, (("fresh-many", "two"), ("fresh-many", "one"))
            )
            assert count == 1
            assert tuple(r.resource_id for r in first) == ("two", "one")
            first[0].payload["operation_id"] = "local-mutation"
            await asyncio.create_task(
                records.put(
                    principal,
                    "fresh-many",
                    "one",
                    "Acknowledgement",
                    {"operation_id": "changed", "status": "completed"},
                    expected_revision=1,
                    request_id="change-one",
                )
            )
            before = count
            second = await records.get_current_many(
                principal, (("fresh-many", "two"), ("fresh-many", "one"))
            )
            assert count == before + 1
            assert second[0].payload["operation_id"] == "two"
            assert second[1].revision == 2
            assert second[1].payload["operation_id"] == "changed"
    finally:
        event.remove(database.engine.sync_engine, "before_cursor_execute", observe)


async def test_grouped_current_rows_participate_in_final_witness(database, principal):
    records = PostgresRecordStore(database)
    await seed(records, principal)
    with pytest.raises(StoreConflict):
        async with records.current_witness():
            await records.get_current_many(
                principal, (("fresh-many", "one"), ("fresh-many", "two"))
            )
            await asyncio.create_task(
                records.delete(
                    principal, "fresh-many", "two", expected_revision=1, request_id="delete-two"
                )
            )


async def test_grouped_absence_observed_and_other_owner_cannot_read(database, principal):
    records = PostgresRecordStore(database)
    await seed(records, principal)
    other = principal.model_copy(update={"id": "fresh-many-other-owner"})
    with pytest.raises(StoreMissing):
        await records.get_current_many(other, (("fresh-many", "one"),))
    with pytest.raises(StoreConflict):
        async with records.current_witness():
            with pytest.raises(StoreMissing):
                await records.get_current_many(principal, (("fresh-many", "absent"),))
            await records.put(
                principal,
                "fresh-many",
                "absent",
                "Acknowledgement",
                {"operation_id": "appeared", "status": "completed"},
                expected_revision=0,
                request_id="appeared",
            )


@pytest.mark.parametrize(
    "addresses", [(), (("fresh-many", "one"),) * 2, (("fresh-many", "one"),) * 33]
)
async def test_grouped_bounds_reject_before_sql(database, principal, addresses):
    records = PostgresRecordStore(database)
    with pytest.raises(ValueError):
        await records.get_current_many(principal, addresses)
