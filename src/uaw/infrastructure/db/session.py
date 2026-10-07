from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


class Database:
    def __init__(self, url: str) -> None:
        self.engine = create_async_engine(
            url, echo=False, hide_parameters=True, pool_pre_ping=True, pool_size=5, max_overflow=5
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def check(self) -> None:
        async with self.engine.connect() as connection:
            revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))
            if revision != "0003_attempt_identity":
                raise RuntimeError("Database schema version is missing or incompatible")

    async def close(self) -> None:
        await self.engine.dispose()
