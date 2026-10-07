"""One owner transaction for related records, deduplication and durable events."""

from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from uaw.infrastructure.db.models import OutboxRow, RecordRow, RecordVersionRow, RequestRow, utcnow
from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.db.session import Database
from uaw.shared.contracts import Principal, RequestMeta
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreConflict, StoreMissing

Payload = dict[str, Any]


def identifier(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def timestamp() -> str:
    return utcnow().isoformat()


def reference(kind: str, resource_id: str, revision: int = 1) -> Payload:
    value = {"kind": kind, "id": resource_id, "version": str(revision)}
    validate_contract("Ref", value)
    return value


class RecordTransaction:
    def __init__(self, session: AsyncSession, owner: str) -> None:
        self.session = session
        self.owner = owner

    async def load(self, namespace: str, resource_id: str) -> RecordRow:
        row = await self.session.get(RecordRow, (self.owner, namespace, resource_id))
        if row is None or row.deleted:
            raise StoreMissing()
        return row

    async def write(
        self, namespace: str, resource_id: str, schema: str, payload: Payload, expected: int = 0
    ) -> RecordRow:
        validate_contract("ID", resource_id)
        validate_contract(schema, payload)
        row = await self.session.get(RecordRow, (self.owner, namespace, resource_id))
        if row:
            if (
                row.deleted
                or row.revision != expected
                or namespace in ("inputs", "event.payloads", "user.actions")
            ):
                raise StoreConflict()
            row.revision += 1
            row.payload = payload
            row.schema_name = schema
            row.updated_at = utcnow()
        else:
            if expected != 0:
                raise StoreConflict()
            row = RecordRow(
                principal_id=self.owner,
                namespace=namespace,
                resource_id=resource_id,
                revision=1,
                schema_name=schema,
                payload=payload,
                deleted=False,
            )
            self.session.add(row)
        self.session.add(
            RecordVersionRow(
                principal_id=self.owner,
                namespace=namespace,
                resource_id=resource_id,
                revision=row.revision,
                schema_name=schema,
                payload=payload,
            )
        )
        await self.session.flush()
        return row

    async def emit(
        self,
        stream: str,
        event_type: str,
        parameters: Payload,
        *,
        item_ref: Payload | None = None,
        base_revision: int = 0,
        result_revision: int = 1,
    ) -> Payload:
        seq = (
            await self.session.scalar(
                select(func.max(OutboxRow.seq)).where(
                    OutboxRow.principal_id == self.owner, OutboxRow.stream_id == stream
                )
            )
        ) or 0
        event_id = identifier("event")
        payload = {"action": event_type, "parameters": parameters}
        await self.write("event.payloads", event_id, "EventPayload", payload)
        envelope = {
            "event_id": event_id,
            "stream_id": stream,
            "seq": seq + 1,
            "type": event_type,
            "schema_version": "0.1",
            "occurred_at": timestamp(),
            "payload_ref": reference("event", event_id),
            "base_revision": base_revision,
            "result_revision": result_revision,
        }
        if item_ref:
            envelope["item_ref"] = item_ref
        await self.write("events", event_id, "EventEnvelope", envelope)
        self.session.add(
            OutboxRow(
                event_id=event_id,
                principal_id=self.owner,
                stream_id=stream,
                seq=seq + 1,
                event_type=event_type,
                payload=payload,
            )
        )
        await self.session.flush()
        return envelope


class TransactionalStore:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def inspect(
        self,
        owner: Principal,
        aggregate: str,
        action: Callable[[RecordTransaction], Awaitable[Payload]],
    ) -> Payload:
        """Serialize a fresh read/expiry refresh without creating replayable request receipts."""
        validate_contract("Principal", owner.wire())
        async with self.database.sessions() as session, session.begin():
            await session.execute(
                select(
                    func.pg_advisory_xact_lock(func.hashtextextended(f"{owner.id}:{aggregate}", 0))
                )
            )
            return await action(RecordTransaction(session, owner.id))

    async def execute(
        self,
        owner: Principal,
        aggregate: str,
        meta: RequestMeta,
        parameters: Payload,
        action: Callable[[RecordTransaction], Awaitable[Payload]],
        verify: Callable[[], Awaitable[None]] | None = None,
        on_replay: Callable[[Payload], Payload] | None = None,
    ) -> Payload:
        try:
            return await self._execute(
                owner, aggregate, meta, parameters, action, verify, on_replay
            )
        except IntegrityError:
            raise StoreConflict("domain_constraint_conflict") from None

    async def _execute(
        self,
        owner: Principal,
        aggregate: str,
        meta: RequestMeta,
        parameters: Payload,
        action: Callable[[RecordTransaction], Awaitable[Payload]],
        verify: Callable[[], Awaitable[None]] | None,
        on_replay: Callable[[Payload], Payload] | None,
    ) -> Payload:
        validate_contract("Principal", owner.wire())
        digest = parameter_hash(parameters)
        async with self.database.sessions() as session, session.begin():
            # Cross-process aggregate serialization, released automatically on commit/rollback.
            await session.execute(
                select(
                    func.pg_advisory_xact_lock(func.hashtextextended(f"{owner.id}:{aggregate}", 0))
                )
            )
            key = (owner.id, "domain.requests", aggregate, meta.request_id)
            previous = await session.get(RequestRow, key)
            if previous:
                if previous.parameter_hash != digest:
                    raise StoreConflict("idempotency_conflict")
                if verify:
                    await verify()
                result = dict(previous.result)
                return on_replay(result) if on_replay else result
            if verify:
                await verify()
            result = await action(RecordTransaction(session, owner.id))
            session.add(
                RequestRow(
                    principal_id=owner.id,
                    namespace="domain.requests",
                    resource_id=aggregate,
                    request_id=meta.request_id,
                    parameter_hash=digest,
                    result=result,
                )
            )
            return result
