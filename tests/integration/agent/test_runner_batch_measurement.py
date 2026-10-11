"""Compare the same actual registered authority with/without duplicate row inputs."""

import json
import time
from contextlib import asynccontextmanager

from sqlalchemy import event

from tests.integration.test_control_plane import domain as domain
from tests.integration.test_runner_control import case as case


async def test_same_snapshot_uses_fewer_current_selects(case, tmp_path):
    await case.dispatch()
    record = await case.register()
    store = case.commands.store
    original_mode = store.checked_metadata
    store._checked_metadata = True  # Explicit controlled measurement, never product configuration.
    batch = store.checked_read_batch
    queries = []

    def capture(_connection, _cursor, statement, _parameters, _context, _many):
        if statement.lstrip().upper().startswith("SELECT") and "uaw_records" in statement:
            queries.append(statement)

    @asynccontextmanager
    async def original_reads():
        async with store.current_reads():
            yield

    event.listen(store.database.engine.sync_engine, "before_cursor_execute", capture)
    try:
        store.checked_read_batch = original_reads
        start = time.perf_counter()
        before = await case.authority().current(
            record["command"], authenticated_principal=case.actor
        )
        baseline = {"selects": len(queries), "seconds": time.perf_counter() - start}
        queries.clear()
        store.checked_read_batch = batch
        start = time.perf_counter()
        after = await case.authority().current(
            record["command"], authenticated_principal=case.actor
        )
        current = {"selects": len(queries), "seconds": time.perf_counter() - start}
        assert before == after
        assert current["selects"] < baseline["selects"]
        assert store._current_batch.get() is None
        (tmp_path / "authority-batch-measurement.json").write_text(
            json.dumps(
                {
                    "same_snapshot": True,
                    "baseline": baseline,
                    "checked_batch": current,
                    "scope": "actual SQL/registered authority; channel/root/gate controlled",
                }
            ),
            encoding="utf-8",
        )
    finally:
        store.checked_read_batch = batch
        store._checked_metadata = original_mode
        event.remove(store.database.engine.sync_engine, "before_cursor_execute", capture)
