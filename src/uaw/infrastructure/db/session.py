import asyncio
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from uaw.shared.stores import Record

RecordObserver = Callable[[tuple[str, str, str], int | None, Record | None], None]


class Database:
    def __init__(self, url: str) -> None:
        self.engine = create_async_engine(
            url, echo=False, hide_parameters=True, pool_pre_ping=True, pool_size=5, max_overflow=5
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)
        self._record_observers: ContextVar[
            tuple[asyncio.Task[Any], tuple[RecordObserver, ...]] | None
        ] = ContextVar("uaw_database_record_observers", default=None)

    @contextmanager
    def observe_reads(self, observer: RecordObserver) -> Iterator[None]:
        """Join record and transactional reads for one owning task, no allowance."""
        task = asyncio.current_task()
        if task is None:
            raise RuntimeError("Record observations require an owning task")
        active = self._record_observers.get()
        callbacks = active[1] if active is not None and active[0] is task else ()
        token = self._record_observers.set((task, (*callbacks, observer)))
        try:
            yield
        finally:
            self._record_observers.reset(token)

    def observe_record(
        self, key: tuple[str, str, str], revision: int | None, value: Record | None
    ) -> None:
        active = self._record_observers.get()
        if active is not None and active[0] is asyncio.current_task():
            for callback in active[1]:
                callback(key, revision, value)

    async def check(self) -> None:
        async with self.engine.connect() as connection:
            revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))
            if revision != "0003_attempt_identity":
                raise RuntimeError("Database schema version is missing or incompatible")

    async def close(self) -> None:
        await self.engine.dispose()
