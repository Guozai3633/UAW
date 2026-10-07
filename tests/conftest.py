import asyncio
import os
from collections.abc import AsyncIterator, Callable, Mapping
from uuid import uuid4

import pytest
from sqlalchemy import delete

from uaw.infrastructure.db.models import (
    ConsumerReceiptRow,
    OutboxRow,
    RecordRow,
    RecordVersionRow,
    RequestRow,
)
from uaw.infrastructure.db.session import Database
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.shared.contracts import Principal


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--require-postgres", action="store_true", default=False)


def pytest_asyncio_loop_factories(
    config: pytest.Config, item: pytest.Item
) -> Mapping[str, Callable[[], asyncio.AbstractEventLoop]]:
    return {"control-plane": control_plane_loop}


@pytest.fixture
def principal() -> Principal:
    return Principal(id=f"test-{uuid4().hex}", kind="user", auth_session_id=f"s-{uuid4().hex}")


@pytest.fixture
async def database(request: pytest.FixtureRequest, principal: Principal) -> AsyncIterator[Database]:
    url = os.environ.get("UAW_TEST_DATABASE_URL")
    if not url:
        if request.config.getoption("--require-postgres"):
            pytest.fail("Real PostgreSQL required; UAW_TEST_DATABASE_URL is missing")
        pytest.skip("Real PostgreSQL not configured; this does not count as persistence acceptance")
    db = Database(url)
    await db.check()
    try:
        yield db
    finally:
        # Only delete the unique principal generated for this test; never truncate the database.
        async with db.sessions.begin() as session:
            for table in [ConsumerReceiptRow, OutboxRow, RequestRow, RecordVersionRow, RecordRow]:
                await session.execute(delete(table).where(table.principal_id == principal.id))
        await db.close()
