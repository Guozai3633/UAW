"""Actual installed source/witness graph at registered metadata boundaries, no send."""

import asyncio
import json
import threading
import time

import pytest
from sqlalchemy import event

from tests.integration.runner.installed_file_fixture import installed_file_case
from tests.integration.test_browser_sessions import web as web
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.test_runner_control import case as case
from uaw.infrastructure import enrollment_peers
from uaw.infrastructure.db.records import parameter_hash
from uaw.run.runner_recheck import RegisteredRunnerRechecks
from uaw.run.tool_sources import RunToolAccessSources
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import DomainError
from uaw.shared.stores import StoreConflict


async def test_custom_sources_keep_legacy_collection(case):
    await case.dispatch()
    record = await case.register()
    assert not case.commands.supports_registered_collection()
    with pytest.raises(DomainError):
        await case.commands.collect_registered(record, case.actor)
    assert await case.commands.collect(record, case.actor)


async def test_joined_budget_rows_remain_in_the_closing_witness(case):
    await case.dispatch()
    store = case.commands.store
    reservation = case.ctx.budget_reservation_ref.id
    with pytest.raises(StoreConflict):
        async with store.current_witness():
            actual = await case.budgets.execution_state(reservation, case.ctx)
            assert actual["attempt"]["dispatched"]
            row = await store.get(case.ctx.principal, "budget.accounting", reservation)
            await store.delete(
                case.ctx.principal,
                "budget.accounting",
                reservation,
                expected_revision=row.revision,
                request_id="joined-budget-disappeared",
            )


async def test_actual_registered_collection_same_result_and_bounded_sql(web, tmp_path, monkeypatch):
    async with installed_file_case(web, tmp_path, monkeypatch) as p:
        await p.approve()
        commands = p.bindings.control.commands
        roots, peers = commands.roots, p.bindings.bridge.pipe.session.registration
        counts = dict.fromkeys(("root", "owning", "sql", "os", "key", "gate"), 0)
        originals, lock = [], threading.Lock()
        owning_task = asyncio.current_task()

        def wrap(obj, method, field, sync=False):
            original = getattr(obj, method)
            originals.append((obj, method, original))
            if sync:

                def measured(*args, **kwargs):
                    with lock:
                        counts[field] += 1
                    return original(*args, **kwargs)
            else:

                async def measured(*args, **kwargs):
                    counts[field] += 1
                    return await original(*args, **kwargs)

            setattr(obj, method, measured)

        def sql(conn, cursor, statement, parameters, context, many):
            if (
                asyncio.current_task() is owning_task
                and statement.lstrip().upper().startswith("SELECT")
                and "uaw_records" in statement
            ):
                counts["sql"] += 1

        api = enrollment_peers.WindowsApi

        class MeasuredApi(api):
            def process(self, pid):
                with lock:
                    counts["os"] += 1
                return super().process(pid)

        bridge = p.bindings.bridge
        evidence = bridge.evidence
        completed = False

        async def capture(call, spec, ctx, command_ref, *, recover):
            nonlocal completed
            record = await commands.record(command_ref.id)
            actor = Principal.model_validate(
                (await commands.devices._load(p.grant.device_id))["source"]["actor"]
            )
            assert commands.supports_registered_collection()
            samples, results = {}, []

            async def legacy_checked(access, context, *, check):
                return await access._snapshot(context, check=check)

            for name, operation in (
                ("legacy", commands.collect),
                ("registered", commands.collect_registered),
                ("registered_legacy_role", commands.collect_registered),
            ):
                for field in counts:
                    counts[field] = 0
                started = time.perf_counter()
                with monkeypatch.context() as scope:
                    if name == "registered_legacy_role":
                        scope.setattr(RunToolAccessSources, "checked_snapshot", legacy_checked)
                    results.append(await operation(record, actor))
                samples[name] = {**counts, "seconds": time.perf_counter() - started}
            assert results[0] == results[1] == results[2]
            assert samples["legacy"]["gate"] == 2 and samples["registered"]["gate"] == 1
            assert 0 < samples["registered"]["sql"] < samples["legacy"]["sql"]
            assert samples["registered"]["root"] >= samples["legacy"]["root"]
            assert samples["registered"]["owning"] > 0 and samples["registered"]["os"] > 0
            assert samples["registered"]["sql"] < samples["registered_legacy_role"]["sql"]
            for field in ("root", "owning", "os", "key", "gate"):
                assert samples["registered"][field] == samples["registered_legacy_role"][field]
            p.metrics["registered_collection_measurement"] = samples
            (tmp_path / "registered-collection-measurement.json").write_text(
                json.dumps(samples), encoding="utf-8"
            )
            completed = True
            raise RuntimeError("Metadata-only test stops before pipe send")

        try:
            wrap(roots, "_read", "root", True)
            wrap(peers.enrollments, "recheck_owned", "owning")
            wrap(roots.directory, "lookup", "key", True)
            wrap(commands.gate, "check_root", "gate")
            monkeypatch.setattr(enrollment_peers, "WindowsApi", MeasuredApi)
            bridge.evidence = capture
            event.listen(p.container.database.engine.sync_engine, "before_cursor_execute", sql)
            with pytest.raises(RuntimeError, match="Metadata-only test stops before pipe send"):
                await p.bindings.tool.facade.invoke(p.raw, p.ctx)
            assert completed
        finally:
            bridge.evidence = evidence
            for obj, method, original in reversed(originals):
                setattr(obj, method, original)
            event.remove(p.container.database.engine.sync_engine, "before_cursor_execute", sql)
        assert p.metrics["sends"] == [] and (await p.child_metrics())["opens"] == 0


@pytest.mark.parametrize(
    "change", ["approval", "account", "policy", "lease", "cancel", "command", "native", "key"]
)
async def test_registered_collection_rejects_changes_after_complete_approval(
    web, tmp_path, monkeypatch, change
):
    async with installed_file_case(web, tmp_path, monkeypatch) as p:
        await p.approve()
        commands, bridge = p.bindings.control.commands, p.bindings.bridge
        evidence, verify = bridge.evidence, commands.signer.verify
        completed = False

        async def capture(call, spec, ctx, command_ref, *, recover):
            nonlocal completed
            record = await commands.record(command_ref.id)
            actor = Principal.model_validate(
                (await commands.devices._load(p.grant.device_id))["source"]["actor"]
            )
            calls = 0

            async def changed(*args, **kwargs):
                nonlocal calls
                await verify(*args, **kwargs)
                calls += 1
                if calls != 2:
                    return
                if change == "account":
                    await p.container.browser_sessions.logout(p.owner, meta("collect-logout"))
                elif change == "native":
                    await asyncio.to_thread(
                        commands.roots.grants.revoke,
                        p.grant.root_handle,
                        expected_revision=p.grant.revision,
                    )
                elif change == "key":
                    await asyncio.to_thread(
                        commands.signer.directory.revoke_key,
                        commands.signer._binding(p.grant.device_id).key_id,
                        expected_revision=1,
                    )
                elif change == "lease":
                    await commands.leases.release(
                        {
                            "lease_ref": record["lease_ref"],
                            "fencing_token": record["command"]["fencing_token"],
                        },
                        meta("collect-release"),
                        ctx,
                        holder=commands.devices.controller,
                    )
                elif change == "command":
                    await commands.revoke(
                        record["command"]["command_id"],
                        1,
                        meta("collect-revoke"),
                        authenticated_service=commands.devices.controller,
                    )
                else:
                    namespace = {
                        "approval": "approval.grants",
                        "policy": "execution.policies",
                        "cancel": "budget.ledgers",
                    }[change]
                    if change == "approval":
                        identifier = (
                            await p.bindings.tool.approvals.get(
                                p.owner,
                                "approval-"
                                + parameter_hash({"run": ctx.run_id, "action": call["action_id"]}),
                            )
                        )["id"]
                    else:
                        identifier = (
                            ctx.capability_policy_ref.id if change == "policy" else ctx.run_id
                        )
                    row = await commands.store.get(p.owner, namespace, identifier)
                    if change == "cancel":
                        await commands.store.put(
                            p.owner,
                            namespace,
                            identifier,
                            row.schema_name,
                            {**row.payload, "revision": row.revision + 1, "cancel_requested": True},
                            expected_revision=row.revision,
                            request_id="collect-cancel",
                        )
                    else:
                        await commands.store.delete(
                            p.owner,
                            namespace,
                            identifier,
                            expected_revision=row.revision,
                            request_id="collect-delete-" + change,
                        )

            commands.signer.verify = changed
            try:
                source = RegisteredRunnerRechecks(commands)
                channel = Ref.model_validate(
                    (await commands.devices._load(p.grant.device_id))["source"]["channel_ref"]
                )
                with pytest.raises((DomainError, StoreConflict)):
                    await source.current(
                        command_ref,
                        authenticated_principal=actor,
                        channel_ref=channel,
                        deadline=asyncio.get_running_loop().time() + 10,
                    )
                assert 2 <= calls <= 3
                completed = True
            finally:
                commands.signer.verify = verify
            raise RuntimeError("Metadata-only adversarial stop before send")

        bridge.evidence = capture
        try:
            with pytest.raises(RuntimeError, match="Metadata-only adversarial stop before send"):
                await p.bindings.tool.facade.invoke(p.raw, p.ctx)
            assert completed
        finally:
            bridge.evidence = evidence
        assert p.metrics["sends"] == [] and (await p.child_metrics())["opens"] == 0
