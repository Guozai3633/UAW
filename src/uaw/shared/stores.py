"""Internal storage ports; domain repositories retain ownership of business state."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

from uaw.shared.contracts import ID, Failure, Principal
from uaw.shared.errors import DomainError


class StoreConflict(DomainError):
    def __init__(self, code: str = "revision_conflict") -> None:
        super().__init__(
            Failure(
                code=code,
                category="conflict",
                message="Stored version or idempotent request parameters conflict",
                retryable=False,
                failed_phase="repository",
            ),
            status_code=409,
        )


class StoreMissing(DomainError):
    def __init__(self) -> None:
        super().__init__(
            Failure(
                code="resource_missing",
                category="dependency",
                message="Resource is unavailable in the authenticated scope",
                retryable=False,
                failed_phase="repository",
            ),
            status_code=404,
        )


@dataclass(frozen=True)
class Record:
    namespace: str
    resource_id: str
    revision: int
    schema_name: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class WriteReceipt:
    record: Record
    unchanged: bool


@dataclass(frozen=True)
class DeleteReceipt:
    namespace: str
    resource_id: str
    revision: int
    unchanged: bool


@dataclass(frozen=True)
class PendingEvent:
    # This is an internal Outbox command, not a public EventEnvelope/wire DTO.
    event_id: ID
    stream_id: ID
    seq: int
    event_type: str
    payload: dict[str, Any]
    payload_schema: str


@dataclass(frozen=True)
class StoredEvent:
    event_id: str
    stream_id: str
    seq: int
    event_type: str
    payload: dict[str, Any]


class RecordStorePort(Protocol):
    async def get(
        self, principal: Principal, namespace: str, resource_id: str, *, revision: int | None = None
    ) -> Record: ...

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
    ) -> WriteReceipt: ...

    async def delete(
        self,
        principal: Principal,
        namespace: str,
        resource_id: str,
        *,
        expected_revision: int,
        request_id: str,
    ) -> DeleteReceipt: ...


class BlobStorePort(Protocol):
    async def put(self, principal: Principal, content: bytes) -> str: ...

    async def get(self, principal: Principal, content_hash: str) -> bytes: ...


EventConsumer = Callable[[StoredEvent], Awaitable[None]]
