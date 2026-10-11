"""Actual current grant and original native evidence; lifecycle markers grant no access."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from uaw_runner.keys import Ed25519SignatureAdapter
from uaw_runner.native_authorization import NativeDecisionJournal
from uaw_runner.pairing import LocalRoots
from uaw_runner.root_source import PersistentRootGrants

from uaw.infrastructure.db.records import parameter_hash
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import parse_json
from uaw.workspace.ports import RootGrant

if TYPE_CHECKING:
    from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch


def complete_marker(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("rb") as stream:
            raw = stream.read(4097)
        if len(raw) > 4096:
            return None
        marker = parse_json(raw)
        if not isinstance(marker, dict) or set(marker) != {
            "workspace_ref",
            "channel_ref",
            "ticket_hash",
        }:
            return None
        return marker
    except OSError, ValueError:
        return None


async def current_root(launch: PreparedEnrollmentLaunch) -> RootGrant:
    connection = launch.connection
    owner, workspace = launch.owner, launch.root_workspace
    if (
        launch.closed
        or connection is None
        or connection.session is None
        or connection.session.local is None
        or connection.channel_ref is None
        or owner is None
        or workspace is None
        or launch.control_key is None
    ):
        raise CapabilityUnavailable("runner.installed.current_root_receipt")
    session = connection.session
    directory = launch.state.path.parent
    marker = await asyncio.to_thread(complete_marker, directory / "root-selection-complete.json")
    if marker is None:
        # Progress-only absence avoids duplicate role IO while the child finishes
        # its own final checks. It never returns a grant or grants permission.
        raise reject(
            "installed_callback_pending", "Native callback is incomplete", 503, "dependency"
        )
    await session.check()
    grants = await asyncio.to_thread(PersistentRootGrants, directory / "grants.sqlite")
    grant = await asyncio.to_thread(
        grants.find,
        principal_id=owner.id,
        device_id=launch.control_key.device_id,
        workspace_ref=workspace,
    )
    if grant.selection_ticket_id is None or session.local is None:
        raise CapabilityUnavailable("runner.installed.original_root_ticket")
    local_peer = session.local
    ticket, _, expiry = await asyncio.to_thread(
        launch.state.consumed_root, grant.selection_ticket_id, now=datetime.now(UTC)
    )
    local = await asyncio.to_thread(LocalRoots, directory / "native.sqlite")
    decisions = await asyncio.to_thread(NativeDecisionJournal, local)
    await asyncio.to_thread(decisions.check, grant.root_handle, ticket, owner, local_peer.actor)
    now = datetime.now(UTC)
    if (
        grant.owner != owner
        or grant.workspace_ref != workspace
        or grant.revoked
        or grant.device_id != launch.control_key.device_id
        or grant.capabilities != frozenset({"read"})
        or grant.expires_at is None
        or grant.confirmation_expires_at is None
        or min(expiry, grant.expires_at, grant.confirmation_expires_at, session.expires_at) <= now
        or not Ed25519SignatureAdapter(launch.state).verify_document(
            {**ticket.document(), "signature": grant.selection_signature},
            device_id=grant.device_id,
            domain="root-selection",
        )
    ):
        raise reject("installed_native_root_changed", "Current original root proof differs", 412)
    if marker != {
        "workspace_ref": workspace.wire(),
        "channel_ref": connection.channel_ref.wire(),
        "ticket_hash": parameter_hash(ticket.document()),
    }:
        raise reject("installed_callback_changed", "Native callback binding differs", 412)
    if await asyncio.to_thread(grants.get, grant.root_handle) != grant:
        raise reject("installed_native_root_changed", "Current root revision differs", 412)
    await session.check()
    if session.local != local_peer:
        raise reject("installed_native_root_changed", "Current local role differs", 412)
    return grant
