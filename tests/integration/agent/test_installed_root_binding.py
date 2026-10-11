"""Actual source/OS/IPC/root binding with explicit disposable UI input, never human proof."""

import asyncio
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from uaw_runner.keys import Ed25519SignatureAdapter
from uaw_runner.native_authorization import NativeDecisionJournal
from uaw_runner.pairing import LocalRoots
from uaw_runner.root_source import PersistentRootGrants

from tests.integration.agent.test_installed_launch import cleaned, installed_environment
from tests.integration.test_browser_sessions import login
from tests.integration.test_browser_sessions import web as web
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch
from uaw.infrastructure.installed_receipt import current_root
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
                try:
                    grant = await current_root(launch)
                except DomainError as exc:
                    if exc.failure.code != "installed_callback_pending":
                        raise
                    await asyncio.sleep(0.2)
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
        # RootGrant's original native repository starts at0, independently of SQL revisions.
        assert grant.revision == 0 and not grant.revoked and expiry > datetime.now(UTC)
        assert Ed25519SignatureAdapter(launch.state).verify_document(
            {**ticket.document(), "signature": grant.selection_signature},
            device_id=grant.device_id,
            domain="root-selection",
        )
        assert await asyncio.to_thread(grants.get, grant.root_handle) == grant
        await session.check()
    finally:
        await cleaned(launch)
