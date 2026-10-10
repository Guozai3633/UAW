"""Internal selector scope and owned connection cleanup; no native UI acceptance."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tests.unit.agent.test_installed_launch_contract import descriptor
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch
from uaw.infrastructure.installed_control import InstalledControlConnection
from uaw.infrastructure.installed_helper import InstalledLaunch
from uaw.infrastructure.installed_roots import InstalledRootSelection
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, reject


@pytest.mark.parametrize("change", ["kind", "path", "scope", "approval", "null"])
def test_installed_optional_workspace_never_accepts_path_or_approval(tmp_path, change):
    value = descriptor(tmp_path)
    ref = {"kind": "workspace", "id": "workspace-one", "version": "1"}
    if change == "kind":
        ref["kind"] = "artifact"
    elif change == "path":
        ref["location"] = {"kind": "whole", "relative_path": "user-dir"}
    elif change == "scope":
        ref["access_scope"] = {"principal_id": "user-one"}
    elif change == "approval":
        ref["approved"] = True
    value["root_workspace"] = None if change == "null" else ref
    with pytest.raises(ValueError):
        InstalledLaunch.from_bytes(json.dumps(value).encode())


def test_installed_optional_selector_preserves_fixed_workspace_default_off(tmp_path):
    value = descriptor(tmp_path)
    assert InstalledLaunch.from_bytes(json.dumps(value).encode()).root_workspace is None
    value["root_workspace"] = {"kind": "workspace", "id": "workspace-one", "version": "1"}
    launch = InstalledLaunch.from_bytes(json.dumps(value).encode())
    assert launch.root_workspace.wire() == value["root_workspace"]


@pytest.fixture
def root_case():
    now = datetime.now(UTC)
    workspace = Ref(kind="workspace", id="workspace-one", version="1")
    peer = SimpleNamespace(
        device_id="device-one",
        key_id="device-key",
        owner=Principal(id="user-one", kind="user", auth_session_id="web-session-one"),
        expires_at=now + timedelta(minutes=5),
    )
    expiry = now + timedelta(seconds=45)
    session = SimpleNamespace(local=SimpleNamespace(identity="actual-instance"), expires_at=expiry)
    ticket = SimpleNamespace(ticket_id="original-ticket", document=lambda: {"ticket": "original"})
    issued = SimpleNamespace(ticket=ticket, verification_code="private-code")
    state = SimpleNamespace(issue=lambda **kwargs: issued)
    auth = SimpleNamespace(select=AsyncMock(return_value="native-selection"), bind=AsyncMock())
    helper = SimpleNamespace(
        session=session,
        bootstrap=SimpleNamespace(
            connected=AsyncMock(),
            directory=SimpleNamespace(
                lookup=lambda *a, **k: SimpleNamespace(public_bytes=b"k" * 32)
            ),
            signer=SimpleNamespace(sign_document=AsyncMock(return_value="signed-original")),
            device_key=SimpleNamespace(credential_handle="protected-handle"),
        ),
        roots=SimpleNamespace(selections=state),
        protocol=SimpleNamespace(clock=lambda: now),
        authorization=AsyncMock(return_value=auth),
    )
    peers = SimpleNamespace(current=AsyncMock(return_value=peer))
    selector = InstalledRootSelection(workspace, peers)
    return SimpleNamespace(**locals())


async def test_root_rejection_does_not_bind_or_reopen_on_reconnect(root_case):
    c = root_case
    c.auth.select.side_effect = reject("permission_denied", "Human declined", 403)
    with pytest.raises(Exception) as denied:
        await c.selector(c.helper)
    assert denied.value.failure.code == "permission_denied"
    c.auth.bind.assert_not_awaited()
    await c.selector(c.helper)
    assert c.auth.select.await_count == 1


async def test_root_selection_requires_original_code_and_bounds_to_current_connection(root_case):
    c = root_case
    issued_args = []

    def issue(**kwargs):
        issued_args.append(kwargs)
        return c.issued

    c.state.issue = issue
    await c.selector(c.helper)
    assert issued_args[0]["expires_at"] == c.expiry
    assert not {"path", "approved", "workspace_ref"}.intersection(issued_args[0])
    c.auth.select.assert_awaited_once_with(
        "original-ticket",
        expected_revision=0,
        code="private-code",
        proof_signature="signed-original",
    )
    c.auth.bind.assert_awaited_once_with("native-selection", c.workspace)
    await c.selector(c.helper)
    assert c.auth.select.await_count == 1  # Reconnect is not a new native approval.


async def test_root_current_source_revoked_after_native_does_not_bind(root_case):
    c = root_case

    async def selected(*args, **kwargs):
        c.helper.bootstrap.connected.side_effect = reject(
            "enrolled_current_key_denied", "Revoked", 403
        )
        return "native-selection"

    c.auth.select.side_effect = selected
    with pytest.raises(Exception) as changed:
        await c.selector(c.helper)
    assert changed.value.failure.code == "enrolled_current_key_denied"
    c.auth.bind.assert_not_awaited()


async def test_root_cancellation_drains_late_ticket_writer(root_case):
    from threading import Event

    c = root_case
    started, release, done = Event(), Event(), Event()

    def issue(**kwargs):
        started.set()
        release.wait(5)
        done.set()
        return c.issued

    c.state.issue = issue
    task = asyncio.create_task(c.selector(c.helper))
    try:
        assert await asyncio.to_thread(started.wait, 5)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert done.is_set()
        c.auth.select.assert_not_awaited()
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)


@pytest.mark.parametrize("own", [True, False])
async def test_control_close_revokes_only_its_bound_source_and_is_idempotent(own):
    owner = Principal(id="user-one", kind="user", auth_session_id="web-session-one")
    channel = Ref(kind="content", id="ipc-one", version="1", content_hash="a" * 64)
    row = SimpleNamespace(
        revision=1,
        payload={
            "state": "active",
            "source": {"owner": owner.wire(), "channel_ref": channel.wire()},
        },
    )
    if not own:
        row.payload["source"]["channel_ref"] = channel.model_copy(update={"id": "ipc-other"}).wire()
    c = object.__new__(InstalledControlConnection)
    c.owner, c.control_key, c.channel_ref, c.closing = (
        owner,
        SimpleNamespace(device_id="device-one"),
        channel,
        None,
    )
    c.devices = SimpleNamespace(
        controller="internal",
        store=SimpleNamespace(get=AsyncMock(return_value=row)),
        revoke=AsyncMock(),
    )
    c.registry, c.session = SimpleNamespace(close=AsyncMock()), SimpleNamespace(close=AsyncMock())
    await c.close()
    await c.close()
    assert c.devices.revoke.await_count == int(own)
    assert c.registry.close.await_count == c.session.close.await_count == 1


async def test_launch_close_during_connect_drains_owned_operation_without_deadlock(monkeypatch):
    container = SimpleNamespace(runner_enrollments=None)
    launch = PreparedEnrollmentLaunch(container, SimpleNamespace(), SimpleNamespace())
    connection = SimpleNamespace(close=AsyncMock())
    launch.owner = Principal(id="user-one", kind="user", auth_session_id="web-session-one")
    launch.control_key = "protected-control-binding"
    launch.enrollment_id = "enrollment-one"
    launch.helper = SimpleNamespace(close=AsyncMock())
    launch.ready = {"event": "ready"}
    entered = asyncio.Event()

    async def connecting(*args):
        entered.set()
        await asyncio.Event().wait()

    connection.connect = connecting
    monkeypatch.setattr(
        "uaw.infrastructure.enrollment_launch.InstalledControlConnection",
        lambda **kwargs: connection,
    )
    task = asyncio.create_task(launch.connect())
    await entered.wait()
    async with asyncio.timeout(2):
        await launch.close()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert launch.closed
    connection.close.assert_awaited_once()


async def test_launch_cannot_connect_before_original_ready():
    launch = PreparedEnrollmentLaunch(SimpleNamespace(runner_enrollments=None), None, None)
    with pytest.raises(CapabilityUnavailable):
        await launch.connect()
    assert launch.connection is None
