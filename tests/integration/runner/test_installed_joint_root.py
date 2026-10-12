"""Actual installed SQL/OS/native root with both A Gate classes; native/decision controlled.

Both metadata Gates run in this owning parent graph. The original chain separately
exercises the actual child process Gate; these samples never dispatch or open files.
"""

import asyncio
import json
import threading
import time

import pytest
from sqlalchemy import event, select

from tests.integration.runner.installed_file_fixture import installed_file_case
from tests.integration.test_browser_sessions import web as web
from tests.integration.test_control_plane import meta
from uaw.infrastructure import enrollment_peers
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.installed_tool_authority import InstalledToolApprovalGate
from uaw.shared.errors import DomainError


async def test_actual_installed_two_gates_joint_root_same_graph_measure_and_revoke(
    web, tmp_path, monkeypatch
):
    async with installed_file_case(web, tmp_path, monkeypatch) as p:
        await p.approve()
        commands = p.bindings.control.commands
        roots, control = commands.roots, commands.gate
        device = p.grant.device_id
        session = p.bindings.bridge.pipe.session
        peers = session.registration
        counts = dict.fromkeys(("root", "owner", "owning", "sql", "os", "key"), 0)
        lock = threading.Lock()
        task = asyncio.current_task()
        originals = []

        def wrap(obj, method, label, synchronous=False):
            original = getattr(obj, method)
            originals.append((obj, method, original))
            if synchronous:

                def measured(*args, **kwargs):
                    with lock:
                        counts[label] += 1
                    return original(*args, **kwargs)
            else:

                async def measured(*args, **kwargs):
                    counts[label] += 1
                    return await original(*args, **kwargs)

            setattr(obj, method, measured)

        api = enrollment_peers.WindowsApi

        class MeasuredApi(api):
            def process(self, pid):
                with lock:
                    counts["os"] += 1
                return super().process(pid)

        def sql(_connection, _cursor, statement, _parameters, _context, _many):
            if (
                asyncio.current_task() is task
                and statement.lstrip().upper().startswith("SELECT")
                and "uaw_records" in statement
            ):
                counts["sql"] += 1

        class Legacy:
            async def current(self, *args, **kwargs):
                return await roots.current(*args, **kwargs)

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
        measurements = {}
        expected = None
        original_authority = control.approvals.approvals.authority
        original_resources = original_authority.resources
        try:
            for name in ("control", "child_class_in_parent_graph"):
                samples = []
                for source in (Legacy(), roots):
                    gate = (
                        control
                        if name == "control"
                        else InstalledToolApprovalGate(p.container, source, device)
                    )
                    for k in counts:
                        counts[k] = 0
                    started = time.perf_counter()
                    result = await gate.check_root(
                        request, p.ctx, roots=source, device_id=device, workspace=p.workspace
                    )
                    samples.append({**counts, "seconds": time.perf_counter() - started})
                    if expected is None:
                        expected = result
                    assert result == expected
                    assert control.approvals.approvals.authority is original_authority
                    assert original_authority.resources is original_resources
                assert samples[0]["root"] >= 4 and samples[1]["root"] == 2
                assert samples[0]["owner"] >= 4 and samples[1]["owner"] == 2
                assert samples[1]["owning"] < samples[0]["owning"]
                assert 0 < samples[1]["sql"] < samples[0]["sql"]
                # Retained complete role/key/root checks per owning graph, no allowed cache.
                assert samples[1]["os"] > 0 and samples[1]["key"] > 0
                measurements[name] = {"legacy": samples[0], "joint": samples[1]}
            p.metrics["joint_root_measurement"] = measurements
            (tmp_path / "joint-root-measurement.json").write_text(
                json.dumps(measurements), encoding="utf-8"
            )
        finally:
            for obj, method, original in reversed(originals):
                setattr(obj, method, original)
            event.remove(p.container.database.engine.sync_engine, "before_cursor_execute", sql)

        # Original roles remain fresh after SQL approval; neither Gate gets a permit cache.
        await p.container.tool_access.revoke(
            p.ctx,
            meta("d-joint-root-revoke-role", 1),
            authenticated_service=p.container.configuration.platform,
        )
        child_gate = InstalledToolApprovalGate(p.container, roots, device)
        for gate in (control, child_gate):
            with pytest.raises(DomainError):
                await gate.check_root(
                    request, p.ctx, roots=roots, device_id=device, workspace=p.workspace
                )
        assert not p.container.records.checked_metadata
        assert p.metrics["sends"] == [] and (await p.child_metrics())["opens"] == 0


async def test_actual_installed_joint_root_cancel_earlier_timeout_and_root_revoke(
    web, tmp_path, monkeypatch
):
    async with installed_file_case(web, tmp_path, monkeypatch) as p:
        roots = p.bindings.control.commands.roots
        started, drained = asyncio.Event(), asyncio.Event()

        async def metadata_wait(root):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                drained.set()

        async def run():
            return await roots.checked_current(
                p.grant.device_id, p.workspace, p.ctx, check=metadata_wait
            )

        task = asyncio.create_task(run())
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert drained.is_set()
        started.clear()
        drained.clear()
        # The caller's shorter absolute budget remains authoritative; never extended.
        with pytest.raises(TimeoutError):
            async with asyncio.timeout(0.5):
                await run()
        # Timeout may occur in original owner SQL before callback; no fallback allowed.
        assert not p.container.records.checked_metadata
        called = 0

        async def revoke(root):
            nonlocal called
            called += 1
            await asyncio.to_thread(
                roots.grants.revoke, p.grant.root_handle, expected_revision=p.grant.revision
            )

        with pytest.raises(DomainError):
            await roots.checked_current(p.grant.device_id, p.workspace, p.ctx, check=revoke)
        assert called == 1
        assert p.metrics["sends"] == [] and (await p.child_metrics())["opens"] == 0


@pytest.mark.parametrize("changed", ["provider", "approval", "account"])
async def test_actual_installed_joint_gates_fresh_sql_source_denial(
    web, tmp_path, monkeypatch, changed
):
    async with installed_file_case(web, tmp_path, monkeypatch) as p:
        await p.approve()
        commands = p.bindings.control.commands
        roots, control = commands.roots, commands.gate
        device = p.grant.device_id
        request = {
            "context": p.ctx.wire(),
            "parameters": {"action": "file.read", "parameters": p.raw["arguments"]},
        }
        child = InstalledToolApprovalGate(p.container, roots, device)
        # Establish actual joint successful metadata checks before changing own SQL.
        for gate in (control, child):
            await gate.check_root(
                request, p.ctx, roots=roots, device_id=device, workspace=p.workspace
            )
        if changed == "account":
            await p.container.browser_sessions.logout(p.owner, meta("d-joint-account"))
        else:
            namespace = "providers" if changed == "provider" else "approval.grants"
            owner = p.container.configuration.platform if changed == "provider" else p.owner
            async with p.container.database.sessions() as sql:
                identifiers = list(
                    await sql.scalars(
                        select(RecordRow.resource_id).where(
                            RecordRow.principal_id == owner.id, RecordRow.namespace == namespace
                        )
                    )
                )
            assert len(identifiers) == 1, "Only this fixture's owning source may be changed"
            row = await p.container.records.get(owner, namespace, identifiers[0])
            await p.container.records.delete(
                owner,
                namespace,
                row.resource_id,
                expected_revision=row.revision,
                request_id="d-joint-" + changed,
            )
        for gate in (control, child):
            with pytest.raises(DomainError):
                await gate.check_root(
                    request, p.ctx, roots=roots, device_id=device, workspace=p.workspace
                )
        p.metrics["joint_source_denied"] = changed
        assert p.metrics["sends"] == [] and (await p.child_metrics())["opens"] == 0
