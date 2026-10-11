"""Actual Windows IPC/keys; account/authority ports are explicit controlled sources.

No affirmative native dialog, no user files. Mutate current sources during real awaits.
"""

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from threading import Event

import pytest
from uaw_runner.ipc.windows_pipe import WindowsApi
from uaw_runner.receipts import canonical

from tests.integration.runner.test_bootstrap import bootstrap_setup
from tests.integration.runner.test_native_authorization import lifecycle_setup
from tests.integration.runner.test_windows_ipc import ipc_case as _ipc_fixture
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import DomainError

ipc_case = _ipc_fixture


async def test_full_bootstrap_still_current_without_redundant_registry_entry_checks(
    ipc_case, monkeypatch
):
    native = await bootstrap_setup(ipc_case)
    session = native["session"]
    original = session.check
    calls = 0

    async def checked():
        nonlocal calls
        calls += 1
        await original()  # Real live pipe/process/role keys/current registration.

    monkeypatch.setattr(session, "check", checked)
    first = await native["checked"].current(native["ticket_id"])
    # Full independent challenge, before/after native reads, both bootstrap checks.
    assert calls == 14
    second = await native["checked"].current(native["ticket_id"])
    assert calls == 28 and first.fingerprint() == second.fingerprint()
    native["state"].revoke_key("device1", expected_revision=0)
    with pytest.raises(DomainError):
        await native["checked"].current(native["ticket_id"])
    assert calls > 28 and session.pipe.closed.is_set()  # No cached permission.


CHANGES = [
    "owner",
    "actor",
    "control_key",
    "device_key",
    "OS_create",
    "pairing",
    "role",
    "schema",
    "registry_remove",
    "registry_replace",
    "channel_ref",
    "expiry",
    "ticket_revoke",
    "ticket_expiry",
    "process_exit",
    "disconnect",
    "cancel",
]


@pytest.mark.parametrize("boundary", [1, 2], ids=["first-owner-await", "final-owner-await"])
@pytest.mark.parametrize("change", CHANGES)
async def test_changed_source_during_owner_await_never_returns_challenge(
    ipc_case, monkeypatch, boundary, change
):
    native = await lifecycle_setup(ipc_case, clock_start=datetime.now(UTC))
    mapping = native["mapping"]
    original = mapping.owner
    reached, release = asyncio.Event(), asyncio.Event()
    calls = 0

    async def awaited_owner(**kwargs):
        nonlocal calls
        calls += 1
        if calls == boundary:
            reached.set()
            await release.wait()
        # This independent current port must read after its simulated IO wait;
        # an earlier captured value would be a permission cache across an await.
        return await original(**kwargs)

    monkeypatch.setattr(mapping, "owner", awaited_owner)
    work = asyncio.create_task(native["challenge"].current(native["ticket_id"]))
    try:
        await asyncio.wait_for(reached.wait(), 5)
        session = native["session"]
        if change == "owner":
            native["owners"].value = Principal(id="u1", kind="user", auth_session_id="changed")
        elif change in ("actor", "OS_create", "pairing", "role", "schema"):
            path = session.registration.path
            data = json.loads(path.read_text(encoding="utf-8"))
            if change == "actor":
                data["client"]["actor"]["id"] = "impostor"
            elif change == "OS_create":
                data["client"]["identity"]["created"] += 1
            elif change == "pairing":
                data["server"]["pairing_ref"]["content_hash"] = "b" * 64
            elif change == "role":
                data["server"]["key_id"] = "control1"
                data["server"]["key_ref"] = data["client"]["key_ref"]
            else:
                data["client"]["actor"].pop("kind")
            await asyncio.to_thread(path.write_text, canonical(data), encoding="utf-8")
        elif change in ("control_key", "device_key"):
            native["state"].revoke_key(
                "control1" if change == "control_key" else "device1", expected_revision=0
            )
        elif change == "registry_remove":
            native["registry"].connections.pop(session.channel_ref.id)
        elif change == "registry_replace":
            native["registry"].connections[session.channel_ref.id] = object()
        elif change == "channel_ref":
            session.channel_ref = Ref(
                kind="content", id="replacement", version="1", content_hash="a" * 64
            )
        elif change == "expiry":
            session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        elif change == "ticket_revoke":
            native["state"].revoke(native["ticket_id"], expected_revision=0, now=native["clock"][0])
        elif change == "ticket_expiry":
            native["clock"][0] += timedelta(hours=1)
        elif change == "process_exit":
            native["process"].terminate()
            await asyncio.to_thread(native["process"].wait, timeout=5)
        elif change == "disconnect":
            await session.close()
        else:
            work.cancel()
        release.set()
        expected = (
            asyncio.CancelledError
            if change == "cancel"
            else ((DomainError, ValueError) if change == "schema" else DomainError)
        )
        with pytest.raises(expected):
            await asyncio.wait_for(work, 5)
    finally:
        release.set()
        if not work.done():
            work.cancel()
        await asyncio.gather(work, return_exceptions=True)
        # A deliberately replaced internal entry is removed; original session is
        # still owned by ipc_case and closed there. Never affect another process.
        native["registry"].connections.clear()


async def test_changed_actual_local_os_instance_rejected(ipc_case, monkeypatch):
    native = await lifecycle_setup(ipc_case, clock_start=datetime.now(UTC))
    actual = native["session"].local.identity
    # Explicit OS-call double to exercise mismatch; real parent/peer remain untouched.
    monkeypatch.setattr(
        WindowsApi, "current", lambda self: replace(actual, created=actual.created + 1)
    )
    with pytest.raises(DomainError):
        await native["challenge"].current(native["ticket_id"])


@pytest.mark.parametrize("boundary", [1, 2])
async def test_even_early_captured_owner_cannot_hide_current_channel_owner_change(
    ipc_case, monkeypatch, boundary
):
    native = await lifecycle_setup(ipc_case, clock_start=datetime.now(UTC))
    original = native["mapping"].owner
    calls = 0

    async def wrongly_captured_owner(**kwargs):
        nonlocal calls
        old = await original(**kwargs)
        calls += 1
        if calls == boundary:
            # Deliberately stale fixture; actual current role registry still changes.
            path = native["session"].registration.path
            data = json.loads(path.read_text(encoding="utf-8"))
            for role in ("server", "client"):
                data[role]["owner"]["auth_session_id"] = "new-session"
                data[role]["actor"]["auth_session_id"] = "new-session"
            native["owners"].value = Principal(id="u1", kind="user", auth_session_id="new-session")
            await asyncio.to_thread(path.write_text, canonical(data), encoding="utf-8")
        return old

    monkeypatch.setattr(native["mapping"], "owner", wrongly_captured_owner)
    with pytest.raises(DomainError):
        await native["challenge"].current(native["ticket_id"])
    if boundary == 2:
        assert native["session"].pipe.closed.is_set()


async def test_mutable_owner_returned_by_adapter_cannot_change_baseline(ipc_case, monkeypatch):
    native = await lifecycle_setup(ipc_case, clock_start=datetime.now(UTC))
    borrowed = Principal(id="u1", kind="user", auth_session_id="s1")
    calls = 0

    async def borrowed_owner(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            await asyncio.sleep(0)
            # Explicit adapter fault injection bypasses the frozen Principal;
            # normal adapters cannot mutate it. Never changes OS/user source.
            object.__setattr__(borrowed, "auth_session_id", "changed")
        return borrowed

    monkeypatch.setattr(native["mapping"], "owner", borrowed_owner)
    with pytest.raises(DomainError):
        await native["challenge"].current(native["ticket_id"])


@pytest.mark.parametrize("missing", ["kind", "id"])
async def test_private_snapshot_rejects_missing_principal_fields(ipc_case, monkeypatch, missing):
    native = await lifecycle_setup(ipc_case, clock_start=datetime.now(UTC))
    session = native["session"]
    original = Principal.wire
    actor = session.peer.actor

    def malformed(self):
        value = original(self)
        if self is actor:
            value.pop(missing)
        return value

    monkeypatch.setattr(Principal, "wire", malformed)
    with pytest.raises(ValueError):
        native["registry"]._snapshot(session, session.channel_ref, device_id="d1")


@pytest.mark.parametrize("change", ["control_key", "ticket_revoke", "cancel"])
async def test_authority_changed_during_final_ticket_read_is_rechecked(
    ipc_case, monkeypatch, change
):
    native = await lifecycle_setup(ipc_case, clock_start=datetime.now(UTC))
    original = native["state"].get
    loop = asyncio.get_running_loop()
    entered, release = asyncio.Event(), Event()
    calls = 0

    def waiting_read(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            loop.call_soon_threadsafe(entered.set)
            assert release.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(native["state"], "get", waiting_read)
    work = asyncio.create_task(native["challenge"].current(native["ticket_id"]))
    try:
        await asyncio.wait_for(entered.wait(), 5)
        if change == "control_key":
            native["state"].revoke_key("control1", expected_revision=0)
        elif change == "ticket_revoke":
            native["state"].revoke(native["ticket_id"], expected_revision=0, now=native["clock"][0])
        else:
            work.cancel()
        release.set()
        with pytest.raises(asyncio.CancelledError if change == "cancel" else DomainError):
            await asyncio.wait_for(work, 5)
    finally:
        release.set()
        if not work.done():
            work.cancel()
        await asyncio.gather(work, return_exceptions=True)


async def test_ticket_revoked_in_last_role_check_cannot_approve_or_create_grant(
    ipc_case, monkeypatch
):
    native = await lifecycle_setup(ipc_case, clock_start=datetime.now(UTC))
    original = native["session"].check
    calls = 0

    async def last_check_changes_ticket():
        nonlocal calls
        calls += 1
        await original()
        if calls == 3:
            # The final role read has completed; this is not a grant. Existing
            # approve/current revision/CAS must reject a changed original Ticket.
            native["state"].revoke(native["ticket_id"], expected_revision=0, now=native["clock"][0])

    monkeypatch.setattr(native["session"], "check", last_check_changes_ticket)
    monkeypatch.setattr(
        "uaw_runner.native_confirmation.WindowsNativeDialog",
        lambda: pytest.fail("revoked Ticket must never open UI"),
    )
    with pytest.raises(DomainError):
        await native["lifecycle"].select(
            native["ticket_id"],
            expected_revision=0,
            code=native["issued"].verification_code,
            proof_signature=native["proof"],
        )
    assert native["state"].get(native["ticket_id"], now=native["clock"][0]).state == "revoked"
    with native["grants"].state.transaction() as db:
        assert db.execute("SELECT COUNT(*) FROM root_grants").fetchone()[0] == 0
