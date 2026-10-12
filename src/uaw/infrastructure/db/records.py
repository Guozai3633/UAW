"""Short PostgreSQL transactions. No shared AsyncSession across concurrent calls."""

import asyncio
import hashlib
import json
from collections import OrderedDict
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any

from sqlalchemy import Integer, literal, select, tuple_, union_all, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from uaw.infrastructure.db.models import (
    ConsumerReceiptRow,
    OutboxRow,
    RecordRow,
    RecordVersionRow,
    RequestRow,
    utcnow,
)
from uaw.infrastructure.db.session import Database
from uaw.shared.contracts import Principal
from uaw.shared.schema import validate_contract
from uaw.shared.stores import (
    DeleteReceipt,
    PendingEvent,
    Record,
    StoreConflict,
    StoredEvent,
    StoreMissing,
    WriteReceipt,
)


def parameter_hash(data: dict[str, Any]) -> str:
    serialized = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class PostgresRecordStore:
    def __init__(self, database: Database, *, checked_metadata: bool = False) -> None:
        if type(checked_metadata) is not bool:
            raise ValueError("An explicit internal metadata mode is required")
        self.database = database
        self._checked_metadata = checked_metadata
        self._current_reads: ContextVar[tuple[asyncio.Task[Any], AsyncSession] | None] = ContextVar(
            "uaw_current_record_reads", default=None
        )
        self._current_batch: ContextVar[
            tuple[asyncio.Task[Any], dict[tuple[str, str, str], Record]] | None
        ] = ContextVar("uaw_current_record_batch", default=None)
        # Source-local locators only. Values/permissions never survive a pass.
        self._read_plans: OrderedDict[tuple[str, ...], tuple[tuple[str, str, str], ...]] = (
            OrderedDict()
        )
        self._read_witness: ContextVar[
            tuple[
                asyncio.Task[Any],
                dict[tuple[str, str, str], Record | None],
                dict[tuple[str, str, str, int], Record | None],
            ]
            | None
        ] = ContextVar("uaw_read_witness", default=None)

    @asynccontextmanager
    async def current_witness(self) -> AsyncIterator[None]:
        """Observe fresh reads; reject changes at the final metadata boundary.

        The observer never skips a get or stores an allowance; optional input
        optimization is a separate caller-controlled mode, disabled by default.
        Both current and historical reads (including
        absence/tombstones) receive a final fresh full-record SQL comparison.
        Only the owning task shares its observation scope. No effects belong here.
        """
        task = asyncio.current_task()
        if task is None:
            raise RuntimeError("Current witnesses require an owning task")
        active = self._read_witness.get()
        if active is not None and active[0] is task:
            yield
            return
        rows: dict[tuple[str, str, str], Record | None] = {}
        versions: dict[tuple[str, str, str, int], Record | None] = {}
        async with self.current_reads(), asyncio.timeout(10):
            token = self._read_witness.set((task, rows, versions))
            try:
                yield
                if rows or versions:
                    actual, observed = await self._witness_rows(rows, versions)
                    if {key: actual.get(key) for key in rows} != rows or {
                        key: observed.get(key) for key in versions
                    } != versions:
                        raise StoreConflict("current_read_source_changed")
            finally:
                self._read_witness.reset(token)

    def _observe(
        self, key: tuple[str, str, str], revision: int | None, value: Record | None
    ) -> None:
        active = self._read_witness.get()
        if active is None or active[0] is not asyncio.current_task():
            return
        _, rows, versions = active
        remembered = key in rows if revision is None else (*key, revision) in versions
        if remembered:
            return
        if len(rows) + len(versions) >= 256:
            raise StoreConflict("current_read_capacity_exceeded")
        saved = (
            Record(
                value.namespace,
                value.resource_id,
                value.revision,
                value.schema_name,
                json.loads(json.dumps(value.payload, allow_nan=False)),
            )
            if value is not None
            else None
        )
        if revision is None:
            rows.setdefault(key, saved)
        else:
            versions.setdefault((*key, revision), saved)

    async def _witness_rows(
        self,
        rows: dict[tuple[str, str, str], Record | None],
        versions: dict[tuple[str, str, str, int], Record | None],
    ) -> tuple[dict[tuple[str, str, str], Record], dict[tuple[str, str, str, int], Record]]:
        # Current and historical sources share ONE fresh statement snapshot.
        statements: list[Any] = []
        for model, addresses, historical in (
            (RecordRow, rows, False),
            (RecordVersionRow, versions, True),
        ):
            if not addresses:
                continue
            statement = select(
                model.principal_id,
                model.namespace,
                model.resource_id,
                model.revision,
                model.schema_name,
                model.payload,
                (model.revision if historical else literal(None, Integer)).label(
                    "requested_revision"
                ),
            )
            keys: tuple[Any, ...] = (model.principal_id, model.namespace, model.resource_id)
            if historical:
                statement = statement.join(
                    RecordRow,
                    (model.principal_id == RecordRow.principal_id)
                    & (model.namespace == RecordRow.namespace)
                    & (model.resource_id == RecordRow.resource_id),
                )
                keys = (*keys, model.revision)
            statements.append(
                statement.where(tuple_(*keys).in_(tuple(addresses)), RecordRow.deleted.is_(False))
            )
        current: dict[tuple[str, str, str], Record] = {}
        previous: dict[tuple[str, str, str, int], Record] = {}
        async with self._read_session() as session:
            values = (await session.execute(union_all(*statements))).mappings()
            for value in values:
                key = (value["principal_id"], value["namespace"], value["resource_id"])
                record = Record(
                    value["namespace"],
                    value["resource_id"],
                    value["revision"],
                    value["schema_name"],
                    json.loads(json.dumps(value["payload"], allow_nan=False)),
                )
                if value["requested_revision"] is None:
                    current[key] = record
                else:
                    previous[(*key, value["requested_revision"])] = record
        return current, previous

    @property
    def checked_metadata(self) -> bool:
        return self._checked_metadata

    @asynccontextmanager
    async def checked_read_batch(
        self, *, plan: tuple[str, ...] | None = None
    ) -> AsyncIterator[None]:
        """One bounded metadata pass, with a fresh SQL witness before returning.

        Disabled by default until the installed first-read budget is accepted.
        Duplicate current rows are detached comparison inputs within this pass.
        They are never permission decisions. A single final SELECT checks every
        dependency's current full record, revision and tombstone. Any difference
        rejects the entire pass. No effect/native UI/file read may occur here.
        Historical reads remain independent fresh reads. Child tasks and later
        passes never inherit these inputs. Nested source Readers in the same
        owning task share the outer witness, which must finish before the
        enclosing authority may return. The caller keeps the original deadline.
        An optional owning-source plan retains at most 64 sets of row locators;
        subsequent passes prefetch CURRENT values and still run every predicate
        and the final witness. Plans never retain row payloads or allowed states.
        """
        if not self.checked_metadata:
            async with self.current_reads():
                yield
            return
        if plan is not None and (
            type(plan) is not tuple
            or not 1 <= len(plan) <= 4
            or any(type(part) is not str or not part or len(part) > 256 for part in plan)
        ):
            raise ValueError("A bounded owning-source locator plan is required")
        task = asyncio.current_task()
        if task is None:
            raise RuntimeError("Checked metadata reads require an owning task")
        active = self._current_batch.get()
        if active is not None and active[0] is task:
            yield
            return
        rows: dict[tuple[str, str, str], Record] = {}
        async with self.current_reads(), asyncio.timeout(10):
            token = self._current_batch.set((task, rows))
            try:
                addresses = self._read_plans.get(plan, ()) if plan is not None else ()
                if addresses:
                    rows.update(await self._current_rows(addresses))
                yield
                if rows:
                    if await self._current_rows(tuple(rows)) != rows:
                        raise StoreConflict("current_read_source_changed")
                if plan is not None:
                    # Learn only after every predicate and the final witness
                    # succeeds. Next use performs fresh SQL before consuming
                    # any input; a learned address is never an admitted value.
                    self._read_plans[plan] = tuple(rows)
                    self._read_plans.move_to_end(plan)
                    while len(self._read_plans) > 64:
                        self._read_plans.popitem(last=False)
            finally:
                self._current_batch.reset(token)

    async def _current_rows(
        self, addresses: tuple[tuple[str, str, str], ...]
    ) -> dict[tuple[str, str, str], Record]:
        async with self._read_session() as session:
            current = await session.scalars(
                select(RecordRow)
                .where(
                    tuple_(RecordRow.principal_id, RecordRow.namespace, RecordRow.resource_id).in_(
                        addresses
                    ),
                    RecordRow.deleted.is_(False),
                )
                .execution_options(populate_existing=True)
            )
            return {
                (row.principal_id, row.namespace, row.resource_id): self._record(row)
                for row in current
            }

    @asynccontextmanager
    async def current_reads(self) -> AsyncIterator[None]:
        """Short owning-task READ COMMITTED reads, never an authorization/data cache.

        Each get still executes a fresh SELECT. Reusing checkout avoids a ping and
        rollback for every nested source read. Child tasks never share this session.
        Do not hold this scope over native UI, model, tool dispatch or user waits.
        """
        task = asyncio.current_task()
        if task is None:
            raise RuntimeError("Current record reads require an owning task")
        active = self._current_reads.get()
        if active is not None and active[0] is task:
            yield
            return
        async with self.database.sessions() as session:
            await session.connection(execution_options={"isolation_level": "READ COMMITTED"})
            token = self._current_reads.set((task, session))
            try:
                yield
            finally:
                self._current_reads.reset(token)

    @asynccontextmanager
    async def _read_session(self) -> AsyncIterator[AsyncSession]:
        active = self._current_reads.get()
        if active is not None and active[0] is asyncio.current_task():
            yield active[1]
            return
        async with self.database.sessions() as session:
            yield session

    @staticmethod
    def _identity(principal: Principal, namespace: str, resource_id: str) -> dict[str, str]:
        validate_contract("Principal", principal.wire())
        validate_contract("ID", namespace)
        validate_contract("ID", resource_id)
        return {"principal_id": principal.id, "namespace": namespace, "resource_id": resource_id}

    async def get(
        self, principal: Principal, namespace: str, resource_id: str, *, revision: int | None = None
    ) -> Record:
        key = self._identity(principal, namespace, resource_id)
        active = self._current_batch.get()
        batch = (
            active[1]
            if revision is None and active is not None and active[0] is asyncio.current_task()
            else None
        )
        batch_key = (principal.id, namespace, resource_id)
        if batch is not None and batch_key in batch:
            saved = batch[batch_key]
            result = Record(
                saved.namespace,
                saved.resource_id,
                saved.revision,
                saved.schema_name,
                json.loads(json.dumps(saved.payload, allow_nan=False)),
            )
            self._observe(batch_key, revision, result)
            return result
        if batch is not None and len(batch) >= 256:
            raise StoreConflict("current_read_capacity_exceeded")
        async with self._read_session() as session:
            if revision is not None:
                validate_contract("Revision", revision)
                version = await session.scalar(
                    select(RecordVersionRow)
                    .join(
                        RecordRow,
                        (
                            (RecordVersionRow.principal_id == RecordRow.principal_id)
                            & (RecordVersionRow.namespace == RecordRow.namespace)
                            & (RecordVersionRow.resource_id == RecordRow.resource_id)
                        ),
                    )
                    .where(
                        RecordVersionRow.principal_id == principal.id,
                        RecordVersionRow.namespace == namespace,
                        RecordVersionRow.resource_id == resource_id,
                        RecordVersionRow.revision == revision,
                        RecordRow.deleted.is_(False),
                    )
                )
                if version is None:
                    self._observe(batch_key, revision, None)
                    raise StoreMissing()
                result = self._record(version)
                self._observe(batch_key, revision, result)
                return result
            # Never trust SQLAlchemy's identity map for mutable current authority.
            row = await session.get(RecordRow, key, populate_existing=True)
            if row is None or row.deleted:
                self._observe(batch_key, revision, None)
                raise StoreMissing()
            result = self._record(row)
            if batch is not None:
                batch[batch_key] = self._record(row)
            self._observe(batch_key, revision, result)
            return result

    @staticmethod
    def _record(row: RecordRow | RecordVersionRow) -> Record:
        # Returned JSON is a detached copy, not a mutable ORM entity.
        return Record(
            row.namespace,
            row.resource_id,
            row.revision,
            row.schema_name,
            json.loads(json.dumps(row.payload, allow_nan=False)),
        )

    async def put(
        self,
        principal: Principal,
        namespace: str,
        resource_id: str,
        schema_name: str,
        payload: dict[str, Any],
        *,
        expected_revision: int,
        request_id: str,
        events: tuple[PendingEvent, ...] = (),
    ) -> WriteReceipt:
        key = self._identity(principal, namespace, resource_id)
        validate_contract("Revision", expected_revision)
        validate_contract("ID", request_id)
        validate_contract(schema_name, payload)
        for event in events:
            validate_contract("ID", event.event_id)
            validate_contract("ID", event.stream_id)
            validate_contract("Revision", event.seq)
            if event.seq == 0:
                raise ValueError("Event sequence starts at one")
            validate_contract("EventType", event.event_type)
            if event.payload_schema != f"EventPayload{event.event_type.capitalize()}":
                raise ValueError("Event type must use its registered payload contract")
            validate_contract(event.payload_schema, event.payload)
        digest = parameter_hash(
            {
                "schema": schema_name,
                "payload": payload,
                "expected_revision": expected_revision,
                "events": [
                    {
                        "id": e.event_id,
                        "stream": e.stream_id,
                        "seq": e.seq,
                        "type": e.event_type,
                        "payload": e.payload,
                        "payload_schema": e.payload_schema,
                    }
                    for e in events
                ],
            }
        )
        async with self.database.sessions.begin() as session:
            request_key = {**key, "request_id": request_id}
            claim = await session.execute(
                insert(RequestRow)
                .values(**request_key, parameter_hash=digest, result={}, created_at=utcnow())
                .on_conflict_do_nothing()
                .returning(RequestRow.request_id)
            )
            if claim.scalar_one_or_none() is None:
                prior = await session.get(RequestRow, request_key)
                if prior is None or prior.parameter_hash != digest:
                    raise StoreConflict("idempotency_conflict")
                current = await session.get(RecordRow, key)
                if current is None or current.deleted:
                    raise StoreMissing()
                result = prior.result
                return WriteReceipt(
                    Record(
                        namespace, resource_id, result["revision"], schema_name, result["payload"]
                    ),
                    unchanged=True,
                )
            next_revision = expected_revision + 1
            if expected_revision == 0:
                changed = await session.execute(
                    insert(RecordRow)
                    .values(
                        **key,
                        revision=1,
                        schema_name=schema_name,
                        payload=payload,
                        deleted=False,
                        updated_at=utcnow(),
                    )
                    .on_conflict_do_nothing()
                    .returning(RecordRow.revision)
                )
            else:
                changed = await session.execute(
                    update(RecordRow)
                    .where(
                        RecordRow.principal_id == principal.id,
                        RecordRow.namespace == namespace,
                        RecordRow.resource_id == resource_id,
                        RecordRow.revision == expected_revision,
                        RecordRow.deleted.is_(False),
                        RecordRow.schema_name == schema_name,
                    )
                    .values(revision=next_revision, payload=payload, updated_at=utcnow())
                    .returning(RecordRow.revision)
                )
            if changed.scalar_one_or_none() is None:
                raise StoreConflict()
            session.add(
                RecordVersionRow(
                    **key,
                    revision=next_revision,
                    schema_name=schema_name,
                    payload=payload,
                )
            )
            for event in events:
                session.add(
                    OutboxRow(
                        event_id=event.event_id,
                        principal_id=principal.id,
                        stream_id=event.stream_id,
                        seq=event.seq,
                        event_type=event.event_type,
                        payload=event.payload,
                    )
                )
            # Flush within the transaction: an event conflict rolls back record AND request.
            try:
                await session.flush()
            except IntegrityError:
                raise StoreConflict("event_sequence_conflict") from None
            await session.execute(
                update(RequestRow)
                .where(
                    RequestRow.principal_id == principal.id,
                    RequestRow.namespace == namespace,
                    RequestRow.resource_id == resource_id,
                    RequestRow.request_id == request_id,
                )
                .values(result={"revision": next_revision, "payload": payload})
            )
            return WriteReceipt(
                Record(
                    namespace,
                    resource_id,
                    next_revision,
                    schema_name,
                    json.loads(json.dumps(payload, allow_nan=False)),
                ),
                unchanged=False,
            )

    async def delete(
        self,
        principal: Principal,
        namespace: str,
        resource_id: str,
        *,
        expected_revision: int,
        request_id: str,
    ) -> DeleteReceipt:
        key = self._identity(principal, namespace, resource_id)
        validate_contract("Revision", expected_revision)
        validate_contract("ID", request_id)
        digest = parameter_hash({"action": "delete", "expected_revision": expected_revision})
        async with self.database.sessions.begin() as session:
            request_key = {**key, "request_id": request_id}
            claim = await session.execute(
                insert(RequestRow)
                .values(**request_key, parameter_hash=digest, result={}, created_at=utcnow())
                .on_conflict_do_nothing()
                .returning(RequestRow.request_id)
            )
            if claim.scalar_one_or_none() is None:
                prior = await session.get(RequestRow, request_key)
                if prior is None or prior.parameter_hash != digest:
                    raise StoreConflict("idempotency_conflict")
                return DeleteReceipt(namespace, resource_id, prior.result["revision"], True)
            changed = await session.execute(
                update(RecordRow)
                .where(
                    RecordRow.principal_id == principal.id,
                    RecordRow.namespace == namespace,
                    RecordRow.resource_id == resource_id,
                    RecordRow.revision == expected_revision,
                    RecordRow.deleted.is_(False),
                )
                .values(deleted=True, revision=expected_revision + 1, updated_at=utcnow())
                .returning(RecordRow.revision)
            )
            result_revision = changed.scalar_one_or_none()
            if result_revision is None:
                raise StoreConflict()
            await session.execute(
                update(RequestRow)
                .where(
                    RequestRow.principal_id == principal.id,
                    RequestRow.namespace == namespace,
                    RequestRow.resource_id == resource_id,
                    RequestRow.request_id == request_id,
                )
                .values(result={"deleted": True, "revision": result_revision})
            )
            return DeleteReceipt(namespace, resource_id, result_revision, False)

    async def events(
        self, principal: Principal, stream_id: str, *, after_seq: int = 0, limit: int = 100
    ) -> list[StoredEvent]:
        validate_contract("ID", stream_id)
        validate_contract("Revision", after_seq)
        if not 1 <= limit <= 100:
            raise ValueError("Event limit must be 1..100")
        async with self.database.sessions() as session:
            rows = (
                await session.scalars(
                    select(OutboxRow)
                    .where(
                        OutboxRow.principal_id == principal.id,
                        OutboxRow.stream_id == stream_id,
                        OutboxRow.seq > after_seq,
                    )
                    .order_by(OutboxRow.seq)
                    .limit(limit)
                )
            ).all()
            return [
                StoredEvent(r.event_id, r.stream_id, r.seq, r.event_type, r.payload) for r in rows
            ]

    async def consume_once(
        self,
        principal: Principal,
        consumer_id: str,
        event_id: str,
        apply: Callable[[AsyncSession, StoredEvent], Awaitable[None]],
    ) -> bool:
        """apply only SQL work in this transaction, never an external/network side effect."""
        validate_contract("ID", consumer_id)
        validate_contract("ID", event_id)
        async with self.database.sessions.begin() as session:
            row = await session.scalar(
                select(OutboxRow).where(
                    OutboxRow.event_id == event_id, OutboxRow.principal_id == principal.id
                )
            )
            if row is None:
                raise StoreMissing()
            claim = await session.execute(
                insert(ConsumerReceiptRow)
                .values(
                    principal_id=principal.id,
                    consumer_id=consumer_id,
                    event_id=event_id,
                    applied_at=utcnow(),
                )
                .on_conflict_do_nothing()
                .returning(ConsumerReceiptRow.event_id)
            )
            if claim.scalar_one_or_none() is None:
                return False
            await apply(
                session,
                StoredEvent(row.event_id, row.stream_id, row.seq, row.event_type, row.payload),
            )
            return True
