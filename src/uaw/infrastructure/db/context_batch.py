"""One-statement current/historical Context reads with owner isolation and no partial result."""

from copy import deepcopy

from sqlalchemy import BigInteger, Integer, String, and_, case, cast, column, select, values

from uaw.context.contracts import RecordReadKey
from uaw.infrastructure.db.models import RecordRow, RecordVersionRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.shared.contracts import Principal
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import Record, StoreMissing


class PostgresContextRecordBatch:
    def __init__(self, records: PostgresRecordStore) -> None:
        self.records = records

    async def read(
        self, principal: Principal, keys: tuple[RecordReadKey, ...]
    ) -> tuple[Record, ...]:
        validate_contract("Principal", principal.wire())
        if principal.kind != "user" or not principal.auth_session_id:
            raise reject("context_record_batch_denied", "Authenticated Context user required", 403)
        if type(keys) is not tuple or len(keys) > 128:
            raise reject("context_record_batch_invalid", "At most 128 keys required", 422)
        for key in keys:
            if type(key) is not RecordReadKey or (
                key.revision is not None
                and (type(key.revision) is not int or not 1 <= key.revision <= 2147483647)
            ):
                raise reject("context_record_batch_invalid", "Invalid exact record revision", 422)
            validate_contract("ID", key.namespace)
            validate_contract("ID", key.resource_id)
        if not keys:
            return ()
        requested = (
            values(
                column("ordinal", Integer),
                column("namespace", String),
                column("resource_id", String),
                column("requested_revision", BigInteger),
            )
            .data([(i, k.namespace, k.resource_id, k.revision) for i, k in enumerate(keys)])
            .cte("context_requested")
        )
        current, history = RecordRow, RecordVersionRow
        join = requested.outerjoin(
            current,
            and_(
                current.principal_id == principal.id,
                current.namespace == requested.c.namespace,
                current.resource_id == requested.c.resource_id,
                current.deleted.is_(False),
            ),
        ).outerjoin(
            history,
            and_(
                requested.c.requested_revision.is_not(None),
                history.principal_id == current.principal_id,
                history.namespace == current.namespace,
                history.resource_id == current.resource_id,
                history.revision == cast(requested.c.requested_revision, BigInteger),
            ),
        )
        statement = (
            select(
                current.namespace,
                current.resource_id,
                case(
                    (requested.c.requested_revision.is_(None), current.revision),
                    else_=history.revision,
                ),
                case(
                    (requested.c.requested_revision.is_(None), current.schema_name),
                    else_=history.schema_name,
                ),
                case(
                    (requested.c.requested_revision.is_(None), current.payload),
                    else_=history.payload,
                ),
            )
            .select_from(join)
            .order_by(requested.c.ordinal)
        )
        async with self.records.database.sessions() as session:
            rows = (await session.execute(statement)).all()
        if len(rows) != len(keys) or any(any(v is None for v in row) for row in rows):
            raise StoreMissing()
        return tuple(Record(row[0], row[1], row[2], row[3], deepcopy(row[4])) for row in rows)
