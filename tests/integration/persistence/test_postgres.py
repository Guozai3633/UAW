import asyncio
import json
import os
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.session import Database
from uaw.shared.contracts import Principal
from uaw.shared.stores import PendingEvent, StoreConflict, StoredEvent, StoreMissing


def input_record(resource_id: str = "input-1") -> dict[str, object]:
    return {
        "id": resource_id,
        "conversation_id": "c1",
        "turn_id": "t1",
        "text": "原始问题，不应由理解覆盖",
        "attachment_refs": [],
        "created_at": "2026-10-07T00:00:00Z",
    }


def event(seq: int, resource_id: str = "input-1") -> PendingEvent:
    return PendingEvent(
        event_id=f"e-{uuid4().hex}",
        stream_id="stream-1",
        seq=seq,
        event_type="input.committed",
        payload={"action": "input.committed", "parameters": input_record(resource_id)},
        payload_schema="EventPayloadInput.committed",
    )


async def test_input_survives_a_separate_process(database: Database, principal: Principal) -> None:
    store = PostgresRecordStore(database)
    await store.put(
        principal,
        "history",
        "input-1",
        "InputRecord",
        input_record(),
        expected_revision=0,
        request_id="request-1",
        events=(event(1),),
    )
    # URL is inherited through environment, never placed on the command line or printed.
    script = """
import asyncio, json, os
from uaw.infrastructure.db.session import Database
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.shared.contracts import Principal
async def main():
    db=Database(os.environ['UAW_TEST_DATABASE_URL'])
    try:
        p=Principal(id=os.environ['UAW_TEST_OWNER'],kind='user',auth_session_id='restart-session')
        record=await PostgresRecordStore(db).get(p,'history','input-1')
        print(json.dumps({'revision':record.revision,'text':record.payload['text']}))
    finally: await db.close()
from uaw.infrastructure.event_loop import control_plane_loop
asyncio.run(main(),loop_factory=control_plane_loop)
"""
    env = {**os.environ, "UAW_TEST_OWNER": principal.id}
    result = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
        check=True,
    )
    restored = json.loads(result.stdout)
    assert restored == {"revision": 1, "text": input_record()["text"]}


async def test_duplicate_request_and_parameter_conflict(
    database: Database, principal: Principal
) -> None:
    store = PostgresRecordStore(database)
    arguments = (principal, "history", "input-1", "InputRecord", input_record())
    results = await asyncio.gather(
        *[store.put(*arguments, expected_revision=0, request_id="r1") for _ in range(2)]
    )
    assert sorted(r.unchanged for r in results) == [False, True]
    assert [r.record.revision for r in results] == [1, 1]
    with pytest.raises(StoreConflict) as raised:
        await store.put(
            principal,
            "history",
            "input-1",
            "InputRecord",
            {**input_record(), "text": "changed"},
            expected_revision=0,
            request_id="r1",
        )
    assert raised.value.failure.code == "idempotency_conflict"


async def test_two_parallel_cas_writes_have_one_winner(
    database: Database, principal: Principal
) -> None:
    store = PostgresRecordStore(database)
    await store.put(
        principal,
        "test",
        "meta",
        "RequestMeta",
        {"request_id": "initial", "schema_version": "0.1"},
        expected_revision=0,
        request_id="create",
    )

    async def compete(label: str) -> str:
        try:
            await store.put(
                principal,
                "test",
                "meta",
                "RequestMeta",
                {"request_id": label, "schema_version": "0.1"},
                expected_revision=1,
                request_id=label,
            )
            return "won"
        except StoreConflict:
            return "conflict"

    assert sorted(await asyncio.gather(compete("a"), compete("b"))) == ["conflict", "won"]
    assert (await store.get(principal, "test", "meta")).revision == 2


async def test_owner_isolation_and_detached_payload(
    database: Database, principal: Principal
) -> None:
    store = PostgresRecordStore(database)
    await store.put(
        principal,
        "history",
        "input-1",
        "InputRecord",
        input_record(),
        expected_revision=0,
        request_id="r1",
    )
    stranger = Principal(id="other-owner", kind="user", auth_session_id="other-session")
    with pytest.raises(StoreMissing):
        await store.get(stranger, "history", "input-1")
    detached = await store.get(principal, "history", "input-1")
    detached.payload["text"] = "mutated in memory"
    assert (await store.get(principal, "history", "input-1")).payload["text"] == input_record()[
        "text"
    ]


async def test_event_conflict_rolls_back_record_and_idempotency_claim(
    database: Database, principal: Principal
) -> None:
    store = PostgresRecordStore(database)
    await store.put(
        principal,
        "history",
        "input-1",
        "InputRecord",
        input_record(),
        expected_revision=0,
        request_id="r1",
        events=(event(1),),
    )
    conflicting_event = event(1, "input-2")
    with pytest.raises(StoreConflict):
        await store.put(
            principal,
            "history",
            "input-2",
            "InputRecord",
            input_record("input-2"),
            expected_revision=0,
            request_id="r2",
            events=(conflicting_event,),
        )
    with pytest.raises(StoreMissing):
        await store.get(principal, "history", "input-2")
    assert len(await store.events(principal, "stream-1")) == 1
    retry = await store.put(
        principal,
        "history",
        "input-2",
        "InputRecord",
        input_record("input-2"),
        expected_revision=0,
        request_id="r2",
        events=(event(2, "input-2"),),
    )
    assert not retry.unchanged


async def test_repeated_event_consumer_commits_once(
    database: Database, principal: Principal
) -> None:
    store = PostgresRecordStore(database)
    pending = event(1)
    await store.put(
        principal,
        "history",
        "input-1",
        "InputRecord",
        input_record(),
        expected_revision=0,
        request_id="r1",
        events=(pending,),
    )

    async def apply(session: AsyncSession, delivered: StoredEvent) -> None:
        session.add(
            RecordRow(
                principal_id=principal.id,
                namespace="projection",
                resource_id=delivered.event_id,
                revision=1,
                schema_name="InputRecord",
                payload=delivered.payload["parameters"],
                deleted=False,
            )
        )

    outcomes = await asyncio.gather(
        *[store.consume_once(principal, "history-view", pending.event_id, apply) for _ in range(2)]
    )
    assert sorted(outcomes) == [False, True]
    async with database.sessions() as session:
        rows = (
            await session.scalars(
                select(RecordRow).where(
                    RecordRow.principal_id == principal.id, RecordRow.namespace == "projection"
                )
            )
        ).all()
        assert len(rows) == 1


async def test_failed_consumer_can_retry_after_rollback(
    database: Database, principal: Principal
) -> None:
    store = PostgresRecordStore(database)
    pending = event(1)
    await store.put(
        principal,
        "history",
        "input-1",
        "InputRecord",
        input_record(),
        expected_revision=0,
        request_id="r1",
        events=(pending,),
    )

    async def broken(session: AsyncSession, delivered: StoredEvent) -> None:
        raise RuntimeError("Injected projection failure")

    with pytest.raises(RuntimeError):
        await store.consume_once(principal, "projection", pending.event_id, broken)

    async def repaired(session: AsyncSession, delivered: StoredEvent) -> None:
        return None

    assert await store.consume_once(principal, "projection", pending.event_id, repaired)


async def test_immutable_versions_and_deleted_history_cannot_resurface(
    database: Database, principal: Principal
) -> None:
    store = PostgresRecordStore(database)
    for revision, label in [(0, "initial"), (1, "updated")]:
        await store.put(
            principal,
            "test",
            "meta",
            "RequestMeta",
            {"request_id": label, "schema_version": "0.1"},
            expected_revision=revision,
            request_id=label,
        )
    old = await store.get(principal, "test", "meta", revision=1)
    assert old.payload["request_id"] == "initial"
    with pytest.raises(StoreConflict):
        await store.delete(
            principal, "test", "meta", expected_revision=1, request_id="delete-stale"
        )
    deleted = await store.delete(
        principal, "test", "meta", expected_revision=2, request_id="delete"
    )
    assert deleted.revision == 3
    assert (
        await store.delete(principal, "test", "meta", expected_revision=2, request_id="delete")
    ).unchanged
    for revision in [None, 1, 2]:
        with pytest.raises(StoreMissing):
            await store.get(principal, "test", "meta", revision=revision)
    with pytest.raises(StoreConflict):
        await store.put(
            principal,
            "test",
            "meta",
            "RequestMeta",
            {"request_id": "resurrect", "schema_version": "0.1"},
            expected_revision=0,
            request_id="resurrect",
        )
    with pytest.raises(StoreMissing):
        await store.put(
            principal,
            "test",
            "meta",
            "RequestMeta",
            {"request_id": "initial", "schema_version": "0.1"},
            expected_revision=0,
            request_id="initial",
        )
