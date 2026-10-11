"""Actual source/OS/IPC/root binding with explicit disposable UI input, never human proof."""

import asyncio
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from uaw_runner.native_authorization import NativeDecisionJournal
from uaw_runner.pairing import LocalRoots
from uaw_runner.root_source import PersistentRootGrants

from tests.integration.agent.test_installed_launch import cleaned, installed_environment
from tests.integration.test_browser_sessions import login
from tests.integration.test_browser_sessions import web as web
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import DomainError

ROOT = Path(__file__).resolve().parents[3]


async def test_actual_installed_root_binding_original_journal_and_current_channel(
    web, tmp_path, monkeypatch
):
    c, client = web
    owner = Principal.model_validate((await login(client))["principal"])
    selected = tmp_path / "explicit-controlled-root"
    await asyncio.to_thread(selected.mkdir)
    monkeypatch.setattr(
        "uaw.infrastructure.enrollment_launch.MODULE",
        "tests.integration.agent.installed_diagnostic_fixture",
    )
    env = installed_environment()
    env["PYTHONPATH"] += os.pathsep + str(ROOT)
    env["UAW_TEST_INSTALLED_DIAGNOSTIC"] = "1"
    env["UAW_TEST_INSTALLED_SELECTED_ROOT"] = str(selected)
    workspace = Ref(kind="workspace", id="explicit-controlled-root-workspace", version="1")
    launch = await PreparedEnrollmentLaunch.prepare(
        c,
        owner=owner,
        python=Path(sys._base_executable),
        state_directory=tmp_path.resolve(),
        currency="USD",
        environment=env,
        root_workspace=workspace,
    )
    try:
        await launch.start()
        await launch.connect()
        session = launch.connection.session
        grants = await asyncio.to_thread(
            PersistentRootGrants, launch.state.path.parent / "grants.sqlite"
        )
        async with asyncio.timeout(110):
            while True:
                await session.check()
                try:
                    grant = await asyncio.to_thread(
                        grants.find,
                        principal_id=owner.id,
                        device_id=launch.control_key.device_id,
                        workspace_ref=workspace,
                    )
                except DomainError as exc:
                    if exc.failure.message != "One actual root binding required":
                        raise
                    await asyncio.sleep(0.1)
                    continue
                break
        ticket, _, expiry = await asyncio.to_thread(
            launch.state.consumed_root, grant.selection_ticket_id, now=datetime.now(UTC)
        )
        local = await asyncio.to_thread(LocalRoots, launch.state.path.parent / "native.sqlite")
        decisions = await asyncio.to_thread(NativeDecisionJournal, local)
        await asyncio.to_thread(
            decisions.check, grant.root_handle, ticket, owner, session.local.actor
        )
        assert grant.owner == owner and grant.workspace_ref == workspace
        assert grant.native_path == selected and grant.capabilities == frozenset({"read"})
        assert grant.revision == 1 and not grant.revoked and expiry > datetime.now(UTC)
        await session.check()
    finally:
        await cleaned(launch)
