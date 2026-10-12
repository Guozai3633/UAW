"""Actual SQL/Windows/dual keys pair vs singles, not execution or human acceptance."""

import json
import threading
import time

from sqlalchemy import event

from tests.integration.runner.installed_file_fixture import installed_file_case
from tests.integration.test_browser_sessions import web as web
from uaw.infrastructure import enrollment_peers


async def test_actual_pair_same_peers_one_owning_check_fewer_sql(web, tmp_path, monkeypatch):
    async with installed_file_case(web, tmp_path, monkeypatch) as p:
        session = p.container.installed_lifecycle.active.launch.connection.session
        registry = session.registration
        owning = registry.enrollments.recheck_owned
        key_read = registry.directory.lookup
        api = enrollment_peers.WindowsApi
        counts = {"owning_checks": 0, "os": 0, "key": 0, "sql": 0}
        lock = threading.Lock()

        class MeasuredApi(api):
            def process(self, pid):
                with lock:
                    counts["os"] += 1
                return super().process(pid)

        def lookup(*args, **kwargs):
            with lock:
                counts["key"] += 1
            return key_read(*args, **kwargs)

        async def recheck(*args):
            counts["owning_checks"] += 1
            return await owning(*args)

        def sql(_connection, _cursor, statement, _parameters, _context, _many):
            if statement.lstrip().upper().startswith("SELECT") and "uaw_records" in statement:
                counts["sql"] += 1

        engine = p.container.database.engine.sync_engine
        monkeypatch.setattr(enrollment_peers, "WindowsApi", MeasuredApi)
        registry.directory.lookup = lookup
        registry.enrollments.recheck_owned = recheck
        event.listen(engine, "before_cursor_execute", sql)
        try:
            by_role = {peer.role: peer for peer in (session.local, session.peer)}
            control, device = by_role["control"], by_role["device"]
            results, samples = [], []
            for paired in (False, True):
                for name in counts:
                    counts[name] = 0
                started = time.perf_counter()
                if paired:
                    results.append(await registry.current_pair(control.identity, device.identity))
                else:
                    results.append(
                        (
                            await registry.current(control.identity, role="control"),
                            await registry.current(device.identity, role="device"),
                        )
                    )
                samples.append({**counts, "seconds": time.perf_counter() - started})
            assert results[0] == results[1] == (control, device)
            assert samples[0]["owning_checks"] == 2 and samples[1]["owning_checks"] == 1
            assert samples[1]["sql"] < samples[0]["sql"]
            assert samples[1]["os"] == samples[0]["os"] > 0
            assert samples[1]["key"] == samples[0]["key"] > 0
            assert not p.container.records.checked_metadata
            assert p.metrics["sends"] == [] and (await p.child_metrics())["opens"] == 0
            (tmp_path / "a20-installed-pair-measurement.json").write_text(
                json.dumps(
                    {
                        "same_results": True,
                        "singles": samples[0],
                        "pair": samples[1],
                        "actual": "SQL/Windows/dual current keys/two processes",
                        "controlled": "native confirmation/initial flags/model metadata",
                        "single_sample_not_production_ratio": True,
                    }
                ),
                encoding="utf-8",
            )
        finally:
            registry.directory.lookup = key_read
            registry.enrollments.recheck_owned = owning
            event.remove(engine, "before_cursor_execute", sql)
    assert p.metrics["cleanup"] == {
        "credential_handles_absent": 4,
        "role_keys_revoked": 2,
        "child_exited": True,
        "proof_pipe_closed": True,
    }
