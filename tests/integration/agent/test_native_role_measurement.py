"""Real installed same peers/SQL/keys; coalesced observation preserves live reads."""

import asyncio
import json
import threading
import time

from sqlalchemy import event

from tests.integration.runner.installed_file_fixture import installed_file_case
from tests.integration.test_browser_sessions import web as web
from uaw.infrastructure import enrollment_peers


async def test_actual_peers_same_projection_reads_and_fewer_role_worker_waits(
    web, tmp_path, monkeypatch
):
    async with installed_file_case(web, tmp_path, monkeypatch) as p:
        launch = p.container.installed_lifecycle.active.launch
        registry = launch.connection.peers
        actual = registry._role_observation
        key_read = registry.directory.lookup
        process_api = enrollment_peers.WindowsApi
        lock = threading.Lock()
        counts = {"process": 0, "key": 0, "sql": 0, "role_waits": 0}

        class MeasuredApi(process_api):
            def process(self, pid):
                with lock:
                    counts["process"] += 1
                return super().process(pid)

        def lookup(*args, **kwargs):
            with lock:
                counts["key"] += 1
            return key_read(*args, **kwargs)

        def sql(_connection, _cursor, statement, _parameters, _context, _many):
            if statement.lstrip().upper().startswith("SELECT") and "uaw_records" in statement:
                counts["sql"] += 1

        async def old_observation(peer, *, device_id):
            counts["role_waits"] += 2
            identity = await registry.observe(peer["identity"]["pid"])
            key = await asyncio.to_thread(
                registry.directory.lookup, peer["key_id"], device_id=device_id
            )
            return identity, key

        async def grouped_observation(peer, *, device_id):
            counts["role_waits"] += 1
            return await actual(peer, device_id=device_id)

        engine = p.container.database.engine.sync_engine
        monkeypatch.setattr(enrollment_peers, "WindowsApi", MeasuredApi)
        registry.directory.lookup = lookup
        event.listen(engine, "before_cursor_execute", sql)
        results, samples = [], []
        try:
            session = launch.connection.session
            for observe in (old_observation, grouped_observation):
                for name in counts:
                    counts[name] = 0
                registry._role_observation = observe
                started = time.perf_counter()
                results.append(
                    tuple(
                        [
                            await registry.current(saved.identity, role=saved.role)
                            for saved in (session.local, session.peer)
                        ]
                    )
                )
                samples.append({**counts, "seconds": time.perf_counter() - started})
            assert results[0] == results[1] == (session.local, session.peer)
            assert samples[0]["process"] == samples[1]["process"] > 0
            assert samples[0]["key"] == samples[1]["key"] > 0
            assert samples[0]["sql"] == samples[1]["sql"] > 0
            assert samples[0]["role_waits"] == samples[1]["role_waits"] * 2 > 0
            assert p.metrics["sends"] == [] and (await p.child_metrics())["opens"] == 0
            (tmp_path / "a18-role-measurement.json").write_text(
                json.dumps(
                    {
                        "same_projection_and_live_reads": True,
                        "old_registry_role_waits": samples[0],
                        "grouped_registry_role_waits": samples[1],
                        "scope": "actual Windows peers/SQL/keys; native/approval controlled",
                        "candidate_observation_grouped_in_both_samples": True,
                        "single_sample_not_production_ratio": True,
                    }
                ),
                encoding="utf-8",
            )
        finally:
            registry._role_observation = actual
            registry.directory.lookup = key_read
            event.remove(engine, "before_cursor_execute", sql)
    assert p.metrics["cleanup"] == {
        "credential_handles_absent": 4,
        "role_keys_revoked": 2,
        "child_exited": True,
        "proof_pipe_closed": True,
    }
