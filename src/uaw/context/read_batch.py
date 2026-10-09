"""Bounded operation-local record groups. No retained rows or authorization."""

from __future__ import annotations

from copy import deepcopy

from uaw.context.contracts import RecordReadKey
from uaw.context.ports import ContextRecordBatchPort
from uaw.shared.contracts import Principal
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import Record, RecordStorePort

MAX_RECORD_KEYS = 128


class ContextRecordReads:
    def __init__(
        self,
        records: RecordStorePort,
        *,
        batch: ContextRecordBatchPort | None = None,
        required: bool = False,
    ) -> None:
        if type(required) is not bool:
            raise ValueError("required must be a bool")
        self.records, self.batch, self.required = records, batch, required

    async def read(
        self, principal: Principal, keys: tuple[RecordReadKey, ...]
    ) -> tuple[Record, ...]:
        validate_contract("Principal", principal.wire())
        if type(keys) is not tuple or len(keys) > MAX_RECORD_KEYS:
            raise reject("context_record_batch_invalid", "Expected at most 128 record keys", 422)
        for key in keys:
            if (
                type(key) is not RecordReadKey
                or type(key.namespace) is not str
                or not key.namespace
                or len(key.namespace.encode("utf-8")) > 256
                or type(key.resource_id) is not str
                or not key.resource_id
                or len(key.resource_id.encode("utf-8")) > 256
                or (
                    key.revision is not None
                    and (type(key.revision) is not int or not 1 <= key.revision <= 2147483647)
                )
            ):
                raise reject("context_record_batch_invalid", "Invalid named record key", 422)
        if self.required and self.batch is None:
            raise CapabilityUnavailable("context.record_batch")
        if not keys:
            return ()
        # Compatibility is explicitly sequential get, never a claimed SQL batch.
        # A present failing batch adapter never falls back to an older value.
        if self.batch is None:
            rows = tuple(
                [
                    await self.records.get(
                        principal, k.namespace, k.resource_id, revision=k.revision
                    )
                    for k in keys
                ]
            )
        else:
            offered = principal.model_copy(deep=True)
            rows = await self.batch.read(offered, keys)
            if offered != principal:
                raise reject(
                    "context_record_batch_invalid", "Adapter changed Principal identity", 403
                )
        if type(rows) is not tuple or len(rows) != len(keys):
            raise reject("context_record_batch_invalid", "Incomplete record batch", 410)
        for key, row in zip(keys, rows, strict=True):
            if (
                type(row) is not Record
                or row.namespace != key.namespace
                or row.resource_id != key.resource_id
                or type(row.revision) is not int
                or not 1 <= row.revision <= 2147483647
                or (key.revision is not None and row.revision != key.revision)
                or type(row.schema_name) is not str
                or not row.schema_name
                or type(row.payload) is not dict
            ):
                raise reject("context_record_batch_invalid", "Record identity differs", 410)
        # Duplicate lookups in one adapter view cannot name different records.
        seen: dict[RecordReadKey, Record] = {}
        for key, row in zip(keys, rows, strict=True):
            if key in seen and seen[key] != row:
                raise reject(
                    "context_record_batch_invalid", "Duplicate record identity differs", 410
                )
            seen[key] = row
        # Record is frozen but its payload is not. Detach each duplicate too.
        return tuple(deepcopy(row) for row in rows)
