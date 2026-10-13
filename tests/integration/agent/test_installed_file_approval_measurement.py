"""Actual installed metadata graph comparison, no human decisions or file execution."""

import asyncio
import json
import threading
import time

from sqlalchemy import event

from tests.integration.runner.installed_file_fixture import installed_file_case
from tests.integration.test_browser_sessions import web as web
from uaw.infrastructure import enrollment_peers, installed_files, installed_tool_authority
from uaw.infrastructure.installed_tool_authority import InstalledToolApprovalGate
from uaw.tool.authority import ToolApprovalAuthority


async def test_actual_same_installed_roots_generic_and_joint_source_approval_graph(
    web, tmp_path, monkeypatch
):
    async with installed_file_case(web, tmp_path, monkeypatch) as p:
        await p.approve()
        commands = p.bindings.control.commands
        roots, control = commands.roots, commands.gate
        peers = p.bindings.bridge.pipe.session.registration
        counts = dict.fromkeys(("root", "owner", "owning", "sql", "os", "key"), 0)
        lock, owning_task = threading.Lock(), asyncio.current_task()
        originals = []

        def wrap(obj, method, field, synchronous=False):
            original = getattr(obj, method)
            originals.append((obj, method, original))
            if synchronous:

                def measured(*args, **kwargs):
                    with lock:
                        counts[field] += 1
                    return original(*args, **kwargs)
            else:

                async def measured(*args, **kwargs):
                    counts[field] += 1
                    return await original(*args, **kwargs)

            setattr(obj, method, measured)

        api = enrollment_peers.WindowsApi

        class MeasuredApi(api):
            def process(self, pid):
                with lock:
                    counts["os"] += 1
                return super().process(pid)

        def sql(conn, cursor, statement, parameters, context, many):
            if (
                asyncio.current_task() is owning_task
                and statement.lstrip().upper().startswith("SELECT")
                and "uaw_records" in statement
            ):
                counts["sql"] += 1

        wrap(roots, "_read", "root", True)
        wrap(roots, "_owner", "owner")
        wrap(peers.enrollments, "recheck_owned", "owning")
        wrap(roots.directory, "lookup", "key", True)
        monkeypatch.setattr(enrollment_peers, "WindowsApi", MeasuredApi)
        event.listen(p.container.database.engine.sync_engine, "before_cursor_execute", sql)
        request = {
            "context": p.ctx.wire(),
            "parameters": {"action": "file.read", "parameters": p.raw["arguments"]},
        }
        authority = control.approvals.approvals.authority
        resource_reader = authority.resources
        trials, expected = {}, None
        try:
            for name in ("control", "child_class_in_parent"):
                gate = (
                    control
                    if name == "control"
                    else InstalledToolApprovalGate(p.container, roots, p.grant.device_id)
                )
                samples = {}
                for strategy in ("generic", "joint_sources"):
                    for field in counts:
                        counts[field] = 0
                    started = time.perf_counter()
                    # Baseline consumes the existing generic authority in the exact
                    # same root bracket. Only this test's parent owning task runs it.
                    with monkeypatch.context() as scope:
                        if strategy == "generic":
                            scope.setattr(
                                installed_files,
                                "InstalledFileApprovalAuthority",
                                ToolApprovalAuthority,
                            )
                            scope.setattr(
                                installed_tool_authority,
                                "InstalledFileApprovalAuthority",
                                ToolApprovalAuthority,
                            )
                        result = await gate.check_root(
                            request,
                            p.ctx,
                            roots=roots,
                            device_id=p.grant.device_id,
                            workspace=p.workspace,
                        )
                    samples[strategy] = {**counts, "seconds": time.perf_counter() - started}
                    if expected is None:
                        expected = result
                    assert result == expected
                    assert control.approvals.approvals.authority is authority
                    assert authority.resources is resource_reader
                for field in ("root", "owner", "owning", "os", "key"):
                    assert samples["generic"][field] == samples["joint_sources"][field] > 0
                assert 0 < samples["joint_sources"]["sql"] < samples["generic"]["sql"]
                trials[name] = samples
            p.metrics["joint_source_measurement"] = trials
            (tmp_path / "joint-source-measurement.json").write_text(
                json.dumps(trials), encoding="utf-8"
            )
        finally:
            for obj, method, original in reversed(originals):
                setattr(obj, method, original)
            event.remove(p.container.database.engine.sync_engine, "before_cursor_execute", sql)
        assert not p.container.records.checked_metadata
        assert p.metrics["sends"] == [] and (await p.child_metrics())["opens"] == 0
