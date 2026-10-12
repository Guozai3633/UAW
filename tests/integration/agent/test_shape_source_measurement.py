"""Same registered SQL source/predicates; count schema work separately from fresh SQL."""

import asyncio
import json
import time
from contextlib import asynccontextmanager

from sqlalchemy import event

from tests.integration.agent.test_registered_runner_recheck import prepared
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_runner_control import case as case
from uaw.shared import schema


async def test_same_registered_current_reduces_shape_work_keeps_fresh_selects(
    case, tmp_path, monkeypatch
):
    source, ref, channel, _ = await prepared(case)
    scopes = []
    queries = []
    original_scope = schema.contract_validation_scope
    shape_bytes = schema._shape_bytes

    @asynccontextmanager
    async def measured():
        async with original_scope() as scope:
            yield scope
            scopes.append({"hits": scope.hits, "misses": scope.misses})

    def queried(_connection, _cursor, statement, _parameters, _context, _many):
        if statement.lstrip().upper().startswith("SELECT") and "uaw_records" in statement:
            queries.append(None)

    monkeypatch.setattr("uaw.run.runner_recheck.contract_validation_scope", measured)
    engine = case.commands.store.database.engine.sync_engine
    event.listen(engine, "before_cursor_execute", queried)
    try:
        outcomes = []
        stats = []
        for enabled in (False, True):
            monkeypatch.setattr(schema, "_shape_bytes", shape_bytes if enabled else lambda _: None)
            queries.clear()
            started = time.perf_counter()
            outcomes.append(
                await source.current(
                    ref,
                    authenticated_principal=case.actor,
                    channel_ref=channel,
                    deadline=asyncio.get_running_loop().time() + 10,
                )
            )
            stats.append(
                {**scopes[-1], "selects": len(queries), "seconds": time.perf_counter() - started}
            )
        assert outcomes[0] == outcomes[1]
        assert stats[0]["selects"] == stats[1]["selects"] > 0
        assert stats[1]["hits"] > 0 and stats[1]["misses"] < stats[0]["misses"]
        assert schema._shape_scope.get() is None
        (tmp_path / "a17-shape-measurement.json").write_text(
            json.dumps(
                {
                    "same_full_projection": True,
                    "unchanged_fresh_sql": True,
                    "baseline": stats[0],
                    "shape_reuse": stats[1],
                    "scope": "actual registered SQL; channel/root/native/gate controlled",
                }
            ),
            encoding="utf-8",
        )
    finally:
        event.remove(engine, "before_cursor_execute", queried)
