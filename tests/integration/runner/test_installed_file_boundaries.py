"""A8 real SQL/OS/IPC source changes after a genuine await, before dispatch/open.

Native and initial availability remain explicit disposable fixtures, not human consent.
"""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from tests.integration.runner.installed_file_fixture import installed_file_case
from tests.integration.test_browser_sessions import web as web
from tests.integration.test_control_plane import meta


@pytest.mark.parametrize(
    "change", ["root", "control_key", "stop", "role", "cancel", "policy_version", "expiry"]
)
async def test_original_file_admission_rechecks_after_source_wait(
    web, tmp_path, monkeypatch, change
):
    async with installed_file_case(web, tmp_path, monkeypatch) as p:
        bridge = p.bindings.bridge
        current = bridge.routes.current
        fired = False
        entered = asyncio.Event()
        release = asyncio.Event()

        async def wait_source(*args, **kwargs):
            nonlocal fired
            value = await current(*args, **kwargs)
            if not fired:
                fired = True
                entered.set()
                await release.wait()
            return value

        bridge.routes.current = wait_source
        if change == "expiry":
            # Earlier caller deadline only, never extend Run/root/session/lease.
            p.ctx = p.ctx.model_copy(
                update={"deadline": (datetime.now(UTC) + timedelta(seconds=8)).isoformat()}
            )
        work = asyncio.create_task(p.bindings.tool.facade.invoke(p.raw, p.ctx))
        try:
            async with asyncio.timeout(20):
                await entered.wait()
            assert not p.metrics["sends"]
            if change == "root":
                await asyncio.to_thread(
                    bridge.commands.roots.grants.revoke,
                    p.grant.root_handle,
                    expected_revision=p.grant.revision,
                )
            elif change == "control_key":
                launch = p.container.installed_lifecycle.active.launch
                await asyncio.to_thread(
                    launch.state.revoke_key, launch.control_key.key_id, expected_revision=0
                )
            elif change == "stop":
                await p.container.installed_lifecycle.close_owner(p.owner)
            elif change == "role":
                await p.container.tool_access.revoke(
                    p.ctx,
                    meta("d-after-wait-role", 1),
                    authenticated_service=p.container.configuration.platform,
                )
            elif change == "cancel":
                run = await p.container.run_service.get_run(p.owner, p.ctx.run_id)
                await p.container.run_service.control(
                    p.owner,
                    {
                        "run_id": p.ctx.run_id,
                        "control": {
                            "mode": "cancel",
                            "preserve_refs": [],
                            "reason": "D controlled wait cancellation",
                        },
                    },
                    meta("d-after-wait-cancel", run["revision"]),
                )
            elif change == "policy_version":
                row = await p.container.records.get(
                    p.owner, "execution.policies", p.ctx.capability_policy_ref.id
                )
                await p.container.records.put(
                    p.owner,
                    "execution.policies",
                    row.resource_id,
                    "CapabilityPolicy",
                    {**row.payload, "revision": row.revision + 1},
                    expected_revision=row.revision,
                    request_id="d-current-policy-version",
                )
            else:
                remaining = (
                    datetime.fromisoformat(p.ctx.deadline) - datetime.now(UTC)
                ).total_seconds()
                await asyncio.sleep(max(0, remaining) + 0.02)
            release.set()
            async with p.phase("after_wait_" + change):
                async with asyncio.timeout(30):
                    result = await work
            assert result["kind"] not in {"ok", "waiting"}, result
            p.metrics["boundary"] = {"change": change, "failure_code": result["failure"]["code"]}
            assert p.metrics["sends"] == []
            assert (await p.child_metrics())["opens"] == 0
            assert (
                await p.bindings.tool.ledger.get("tool.budget.dispatched", p.ctx.attempt_id, p.ctx)
                is None
            )
        finally:
            release.set()
            if not work.done():
                work.cancel()
            await asyncio.gather(work, return_exceptions=True)
