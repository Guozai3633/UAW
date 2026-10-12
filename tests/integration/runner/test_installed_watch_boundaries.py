"""Actual installed Web/SQL/two-process IPC watch; execute wait/native inputs controlled.

This proves monitoring/cancellation only, never actual file execution or human consent.
"""

import asyncio
import hashlib
import json

import pytest
from sqlalchemy import select

from tests.integration.runner.installed_file_fixture import installed_file_case
from tests.integration.test_browser_sessions import web as web
from tests.integration.test_control_plane import meta
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.enrollment_candidates import CANDIDATES
from uaw.infrastructure.enrollment_native import JOURNAL
from uaw.run.enrollment import ENROLLMENTS


@pytest.mark.parametrize(
    "change",
    [
        "account",
        "enrollment",
        "candidate",
        "native_account",
        "stop",
        "provider",
        "model",
        "approval",
        "budget",
        "policy",
        "lease",
        "device",
        "run",
        "configuration",
        "role",
    ],
)
async def test_actual_installed_sql_watch_cancels_controlled_execution_wait(
    web, tmp_path, monkeypatch, change
):
    async with installed_file_case(web, tmp_path, monkeypatch, monitor_wait=True) as p:
        await p.approve()
        work = asyncio.create_task(p.bindings.tool.facade.invoke(p.raw, p.ctx))
        try:
            async with asyncio.timeout(70):
                while not work.done():
                    metrics = await p.child_metrics()
                    if metrics.get("watch_polling"):
                        break
                    await asyncio.sleep(0.03)
            assert metrics.get("watch_polling"), "Original SQL-only polling must actually start"
            assert metrics.get("controlled_execution_wait") and metrics["opens"] == 0
            covered = metrics["watch_capture"]["current"]
            assert {
                "web.sessions",
                ENROLLMENTS,
                CANDIDATES,
                JOURNAL,
                "execution.leases",
                "runner.devices",
            } <= set(covered)
            assert p.metrics["sends"] == ["command"]
            if change == "stop":
                await p.container.installed_lifecycle.close_owner(p.owner)
            elif change == "account":
                await p.container.browser_sessions.logout(
                    p.owner, meta("d-installed-watch-account")
                )
            elif change in {
                "provider",
                "model",
                "approval",
                "budget",
                "policy",
                "lease",
                "device",
                "run",
                "configuration",
                "role",
            }:
                namespace = {
                    "provider": "providers",
                    "model": "model.policies",
                    "approval": "approval.grants",
                    "budget": "budget.ledgers",
                    "policy": "execution.policies",
                    "lease": "execution.leases",
                    "device": "runner.devices",
                    "run": "runs",
                    "configuration": "configuration.pointer",
                    "role": "run.tool.roles",
                }[change]
                expected = metrics["watch_address_hashes"][namespace]
                target = None
                # This fixture locates only its own rows for mutation; no new production
                # range source is introduced or claimed to be SQL-watch covered.
                for owner in (p.owner, p.container.configuration.platform):
                    async with p.container.database.sessions() as sql:
                        identifiers = await sql.scalars(
                            select(RecordRow.resource_id).where(
                                RecordRow.principal_id == owner.id,
                                RecordRow.namespace == namespace,
                            )
                        )
                        for identifier in identifiers:
                            hashed = hashlib.sha256(
                                json.dumps((owner.id, namespace, identifier)).encode()
                            ).hexdigest()
                            if hashed in expected:
                                target = owner, identifier
                                break
                    if target is not None:
                        break
                assert target is not None, "Actual captured original SQL row required"
                owner, identifier = target
                row = await p.container.records.get(owner, namespace, identifier)
                await p.container.records.delete(
                    owner,
                    namespace,
                    identifier,
                    expected_revision=row.revision,
                    request_id="d-installed-watch-" + change,
                )
            else:
                service = p.container.runner_enrollments
                namespace = {
                    "enrollment": ENROLLMENTS,
                    "candidate": CANDIDATES,
                    "native_account": JOURNAL,
                }[change]
                launch = p.container.installed_lifecycle.active.launch
                identifier = launch.enrollment_id
                if change == "candidate":
                    record = await service.get(p.owner, identifier)
                    identifier = record["proof_document"]["candidate_ref"]["id"]
                row = await p.container.records.get(service.controller, namespace, identifier)
                await p.container.records.delete(
                    service.controller,
                    namespace,
                    identifier,
                    expected_revision=row.revision,
                    request_id="d-installed-watch-" + change,
                )
            async with p.phase("actual_monitor_change_" + change):
                result = await work
            assert result["kind"] != "ok", result
            metrics = await p.child_metrics()
            assert metrics.get("controlled_wait_cancelled") and metrics["opens"] == 0
            assert p.metrics["sends"] == ["command"]
            deadlines = metrics["watch_deadlines"] + metrics["reply_deadlines"]
            assert len(set(deadlines)) == 1
            p.metrics["actual_watch_change"] = {
                "kind": change,
                "command": 1,
                "open": 0,
                "production_grant": False,
            }
        finally:
            work.cancel()
            await asyncio.gather(work, return_exceptions=True)
