"""Explicit lifecycle for the installed PostgreSQL checkpointer addon."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from uaw.agent.engines.langgraph import JsonCheckpointSerializer


@asynccontextmanager
async def postgres_checkpoints(
    connection_string: str, *, initialize: bool = False
) -> AsyncIterator[Any]:
    """Trusted deployment configuration only; never a model-supplied connection.

    initialize is an explicit environment preparation operation. Ordinary runs
    do not auto-create checkpoint tables or choose a storage authority.
    """
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    async with AsyncPostgresSaver.from_conn_string(
        connection_string, serde=JsonCheckpointSerializer()
    ) as saver:
        if initialize:
            await saver.setup()
        yield saver
