"""Bounded durable queue. Job ownership does not grant execution permissions."""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select

from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore, identifier
from uaw.shared.contracts import Principal
from uaw.shared.errors import DomainError, reject
from uaw.shared.observability import report_request_failure
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreConflict

Payload = dict[str, Any]
JOBS = "run.background.jobs"
Advance = Callable[[Payload], Awaitable[Payload]]
Finalize = Callable[[Payload], Awaitable[None]]


class RunJobs:
    def __init__(
        self,
        records: PostgresRecordStore,
        owner: Principal,
        *,
        capacity: int = 16,
        concurrency: int = 1,
        advance: Advance | None = None,
        finalize: Finalize | None = None,
    ) -> None:
        if not 1 <= concurrency <= 4 or not 1 <= capacity <= 64:
            raise ValueError("Bounded queue/concurrency required")
        self.records, self.owner = records, owner
        self.transactions = TransactionalStore(records.database)
        self.capacity, self.concurrency, self.advance = capacity, concurrency, advance
        self.finalize = finalize
        self.worker_id = identifier("worker")
        self.tasks: list[asyncio.Task[None]] = []
        self.stopping = asyncio.Event()

    async def enqueue(self, tx: RecordTransaction, run: Payload, actor: Principal) -> None:
        if tx.owner != actor.id or actor.id != self.owner.id or actor.kind != "user":
            raise reject("job_owner_denied", "Queue owner differs", 403)
        # Executed inside Run admission: capacity failure rolls back input/Run/budget
        # and request receipt together. Cross-conversation capacity is serialized.
        await tx.session.execute(
            select(func.pg_advisory_xact_lock(func.hashtextextended(f"{actor.id}:web.queue", 0)))
        )
        active = list(
            await tx.session.scalars(
                select(RecordRow.resource_id)
                .where(
                    RecordRow.principal_id == actor.id,
                    RecordRow.namespace == JOBS,
                    RecordRow.deleted.is_(False),
                    RecordRow.payload["state"].astext.in_(("queued", "working", "waiting")),
                )
                .limit(self.capacity)
            )
        )
        if len(active) >= self.capacity:
            raise reject("run_queue_full", "Background queue is full; no task was admitted", 409)
        value = {
            "run_id": run["id"],
            "principal": actor.wire(),
            "revision": 1,
            "state": "queued",
            "stage": "admitted",
            "step": 0,
            "fence": 0,
            "ready_at": datetime.now(UTC).isoformat(),
        }
        await tx.write(JOBS, run["id"], "BackgroundRunJob", value)

    async def claim(self) -> Payload:
        async def claim(tx: RecordTransaction) -> Payload:
            rows = list(
                await tx.session.scalars(
                    select(RecordRow)
                    .where(
                        RecordRow.principal_id == self.owner.id,
                        RecordRow.namespace == JOBS,
                        RecordRow.deleted.is_(False),
                        RecordRow.payload["state"].astext.in_(("queued", "working", "waiting")),
                    )
                    .order_by(RecordRow.updated_at, RecordRow.resource_id)
                    .limit(self.capacity)
                )
            )
            now = datetime.now(UTC)
            live = [
                r
                for r in rows
                if r.payload["state"] == "working"
                and datetime.fromisoformat(r.payload["lease_expires"]) > now
            ]
            if len(live) >= self.concurrency:
                return {}
            for row in rows:
                value = row.payload
                validate_contract("BackgroundRunJob", value)
                if row in live or datetime.fromisoformat(value["ready_at"]) > now:
                    continue
                updated = {
                    **value,
                    "state": "working",
                    "revision": row.revision + 1,
                    "fence": value["fence"] + 1,
                    "worker_id": self.worker_id,
                    "lease_expires": (now + timedelta(seconds=300)).isoformat(),
                }
                await tx.write(JOBS, row.resource_id, "BackgroundRunJob", updated, row.revision)
                return updated
            return {}

        return await self.transactions.inspect(self.owner, "web.queue", claim)

    async def save(self, original: Payload, result: Payload) -> Payload:
        validate_contract("BackgroundRunJob", result)

        async def save(tx: RecordTransaction) -> Payload:
            row = await tx.load(JOBS, original["run_id"])
            if (
                self.progress(row.payload) != self.progress(original)
                or row.payload["state"] != "working"
                or row.payload["worker_id"] != self.worker_id
                or row.payload["fence"] != original["fence"]
                or datetime.fromisoformat(row.payload["lease_expires"]) <= datetime.now(UTC)
            ):
                raise StoreConflict("job_fence_stale")
            if (
                result["run_id"] != original["run_id"]
                or result["principal"] != original["principal"]
            ):
                raise reject("job_scope_changed", "Original job identity cannot change", 403)
            value = {
                **result,
                "revision": row.revision + 1,
                "fence": original["fence"],
                "worker_id": self.worker_id,
            }
            if value["state"] == "working":
                value["state"] = "queued"
            await tx.write(JOBS, original["run_id"], "BackgroundRunJob", value, row.revision)
            return value

        return await self.transactions.inspect(self.owner, "web.queue", save)

    @staticmethod
    def progress(value: Payload) -> Payload:
        return {k: v for k, v in value.items() if k not in ("revision", "lease_expires")}

    async def renew(self, original: Payload) -> None:
        async def renew(tx: RecordTransaction) -> Payload:
            row = await tx.load(JOBS, original["run_id"])
            if self.progress(row.payload) != self.progress(original) or datetime.fromisoformat(
                row.payload["lease_expires"]
            ) <= datetime.now(UTC):
                raise StoreConflict("job_fence_stale")
            updated = {
                **row.payload,
                "revision": row.revision + 1,
                "lease_expires": (datetime.now(UTC) + timedelta(seconds=300)).isoformat(),
            }
            await tx.write(JOBS, original["run_id"], "BackgroundRunJob", updated, row.revision)
            return {}

        await self.transactions.inspect(self.owner, "web.queue", renew)

    async def heartbeat(self, job: Payload) -> None:
        while True:
            await asyncio.sleep(15)
            await self.renew(job)

    async def tick(self) -> bool:
        if self.advance is None:
            raise ValueError("Actual driver required")
        job = await self.claim()
        if not job:
            await self.reconcile_stopped()
            return False
        heartbeat = asyncio.create_task(self.heartbeat(job))
        execution = asyncio.ensure_future(self.advance(job))
        try:
            completed, _ = await asyncio.wait(
                (heartbeat, execution), return_when=asyncio.FIRST_COMPLETED
            )
            if heartbeat in completed:
                execution.cancel()
                await asyncio.gather(execution, return_exceptions=True)
                heartbeat.result()
                raise StoreConflict("job_fence_stale")
            result = execution.result()
        except DomainError as exc:
            result = {**job, "state": "blocked", "failure": exc.failure.wire()}
        except asyncio.CancelledError:
            # Original attempts and active operations retain send intent. Restart will
            # recover that exact stage/identity, never generate a replacement attempt.
            execution.cancel()
            await asyncio.gather(execution, return_exceptions=True)
            await self.save(job, {**job, "state": "queued"})
            raise
        except Exception:
            result = {
                **job,
                "state": "blocked",
                "failure": reject(
                    "background_driver_failed",
                    "Background execution stopped; original attempt retained",
                    500,
                    "infrastructure",
                ).failure.wire(),
            }
        finally:
            heartbeat.cancel()
            await asyncio.gather(heartbeat, return_exceptions=True)
        saved = await self.save(job, result)
        if self.finalize is not None and saved["state"] == "blocked":
            await self.finalize(saved)
        return True

    async def reconcile_stopped(self) -> None:
        """Recover a crash after saving a stop; this path never calls the driver."""
        if self.finalize is None:
            return
        async with self.records.database.sessions() as session:
            rows = list(
                await session.scalars(
                    select(RecordRow)
                    .where(
                        RecordRow.principal_id == self.owner.id,
                        RecordRow.namespace == JOBS,
                        RecordRow.deleted.is_(False),
                        RecordRow.payload["state"].astext == "blocked",
                    )
                    .order_by(RecordRow.updated_at)
                    .limit(64)
                )
            )
        for row in rows:
            await self.finalize(row.payload)
            run = await self.records.get(self.owner, "runs", row.resource_id)
            if run.payload["status"] not in ("failed", "cancelled", "completed"):
                continue

            async def finish(
                tx: RecordTransaction, key: str = row.resource_id, revision: int = row.revision
            ) -> Payload:
                current = await tx.load(JOBS, key)
                if current.revision != revision or current.payload["state"] != "blocked":
                    return {}
                value = {
                    **current.payload,
                    "revision": current.revision + 1,
                    "state": "finished",
                    "stage": "finished",
                }
                await tx.write(JOBS, key, "BackgroundRunJob", value, current.revision)
                return {}

            await self.transactions.inspect(self.owner, "web.queue", finish)

    async def _loop(self) -> None:
        while not self.stopping.is_set():
            try:
                progressed = await self.tick()
            except DomainError:
                progressed = False
            except Exception as exc:
                report_request_failure("background.tick", type(exc).__name__)
                progressed = False
            if not progressed:
                try:
                    await asyncio.wait_for(self.stopping.wait(), timeout=0.5)
                except TimeoutError:
                    pass

    def start(self) -> None:
        if self.tasks or self.advance is None:
            raise ValueError("Queue must have one lifecycle and an actual driver")
        self.tasks = [asyncio.create_task(self._loop()) for _ in range(self.concurrency)]

    async def close(self) -> None:
        self.stopping.set()
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
