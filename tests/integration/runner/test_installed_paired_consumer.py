"""Actual A20 SQL/OS dual-role registry through D session consumer; native input controlled.

This is command0/open0 metadata only, not human confirmation or first file execution.
"""

import asyncio
import json
import threading
import time

from sqlalchemy import event

from tests.integration.runner.installed_file_fixture import installed_file_case
from tests.integration.test_browser_sessions import web as web
from uaw.infrastructure import enrollment_peers


async def test_actual_installed_d_pair_consumer_one_owning_graph_same_complete_peers(
    web, tmp_path, monkeypatch
):
    async with installed_file_case(web, tmp_path, monkeypatch) as p:
        session = p.container.installed_lifecycle.active.launch.connection.session
        peers = session.registration
        owning = peers.enrollments.recheck_owned
        key_read = peers.directory.lookup
        api = enrollment_peers.WindowsApi
        counts = {"owning": 0, "os": 0, "key": 0, "sql": 0, "pair": 0}
        lock = threading.Lock()
        task = None
        pair = peers.current_pair

        class MeasuredApi(api):
            def process(self, pid):
                with lock:
                    counts["os"] += 1
                return super().process(pid)

        def lookup(*args, **kwargs):
            with lock:
                counts["key"] += 1
            return key_read(*args, **kwargs)

        async def recheck(*args, **kwargs):
            counts["owning"] += 1
            return await owning(*args, **kwargs)

        async def paired(*args, **kwargs):
            counts["pair"] += 1
            return await pair(*args, **kwargs)

        class Legacy:
            # Only the original current interface, no pair attribute/fallback trick.
            async def current(self, *args, **kwargs):
                return await peers.current(*args, **kwargs)

        def sql(_connection, _cursor, statement, _parameters, _context, _many):
            if (
                asyncio.current_task() is task
                and statement.lstrip().upper().startswith("SELECT")
                and "uaw_records" in statement
            ):
                counts["sql"] += 1

        monkeypatch.setattr(enrollment_peers, "WindowsApi", MeasuredApi)
        peers.directory.lookup = lookup
        peers.enrollments.recheck_owned = recheck
        peers.current_pair = paired
        event.listen(p.container.database.engine.sync_engine, "before_cursor_execute", sql)
        samples = []
        originals = (session.local.wire(), session.peer.wire(), session.channel_ref.wire())
        try:
            task = asyncio.current_task()
            for registration in (Legacy(), peers):
                session.registration = registration
                for k in counts:
                    counts[k] = 0
                started = time.perf_counter()
                await session.check()
                samples.append({**counts, "seconds": time.perf_counter() - started})
                assert (
                    session.local.wire(),
                    session.peer.wire(),
                    session.channel_ref.wire(),
                ) == originals
            assert samples[0]["owning"] == 2 and samples[1]["owning"] == 1
            assert samples[0]["pair"] == 0 and samples[1]["pair"] == 1
            assert samples[1]["sql"] < samples[0]["sql"]
            assert samples[1]["os"] >= samples[0]["os"] > 0
            assert samples[1]["key"] == samples[0]["key"] > 0
            assert not p.container.records.checked_metadata
            assert p.metrics["sends"] == [] and (await p.child_metrics())["opens"] == 0
            p.metrics["pair_consumer_measurement"] = {
                "legacy": samples[0],
                "paired": samples[1],
                "same_complete_peers": True,
                "single_sample_not_production_ratio": True,
            }
            (tmp_path / "paired-consumer-measurement.json").write_text(
                json.dumps(p.metrics["pair_consumer_measurement"]), encoding="utf-8"
            )
        finally:
            session.registration = peers
            peers.directory.lookup = key_read
            peers.enrollments.recheck_owned = owning
            peers.current_pair = pair
            event.remove(p.container.database.engine.sync_engine, "before_cursor_execute", sql)
