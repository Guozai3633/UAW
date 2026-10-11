"""SQL current-peer regression with controlled OS/native observations, no UI."""

import base64
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from uaw_runner.ipc.windows_pipe import OsIdentity

from tests.integration.agent.test_enrollment_postgres import enrollment_case as enrollment_case
from tests.integration.test_browser_sessions import web as web
from tests.integration.test_control_plane import meta
from uaw.infrastructure.enrollment_native import JOURNAL, RegisteredNativeEnrollmentEvidence
from uaw.infrastructure.enrollment_peers import EnrolledPeerRegistry
from uaw.infrastructure.installed_channels import InstalledConnectionRegistry
from uaw.run.enrollment import ENROLLMENTS, fixed_ref
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.shared.runner_signatures import VerificationKey


async def active_registry(p):
    started = await p.service.begin(p.owner, p.candidate["id"], meta("peer-begin"))
    evidence = await p.native.current(started["proof_document"], owner=p.owner)
    evidence["confirmation_ref"] = fixed_ref(
        "check",
        "native-enrollment-" + started["id"],
        {k: v for k, v in evidence.items() if k != "confirmation_ref"},
    )
    await p.control.records.put(
        p.service.controller,
        JOURNAL,
        started["id"],
        "RunnerNativePairingEvidence",
        evidence,
        expected_revision=0,
        request_id="peer-journal",
    )
    p.service.native = RegisteredNativeEnrollmentEvidence(p.service)
    active = await p.service.complete(p.owner, started["id"], meta("peer-complete", 1))
    peers = started["proof_document"]
    keys = {
        role: VerificationKey(
            peers[role]["key_id"],
            peers["device_id"],
            base64.b64decode(peers[role]["public_key"]),
            role,
        )
        for role in ("control", "device")
    }

    async def observe(pid):
        source = next(peers[r]["identity"] for r in keys if peers[r]["identity"]["pid"] == pid)
        return OsIdentity(
            source["pid"], int(source["created"]), source["user_sid"], source["logon_sid"]
        )

    def lookup(key_id, *, device_id):
        assert device_id == peers["device_id"]
        return next(k for k in keys.values() if k.key_id == key_id)

    registry = EnrolledPeerRegistry(
        p.service,
        owner=p.owner,
        enrollment_id=active["id"],
        directory=SimpleNamespace(lookup=lookup),
        observe=observe,
    )
    return SimpleNamespace(
        p=p, active=active, peers=peers, keys=keys, observe=observe, registry=registry
    )


@pytest.mark.parametrize("change", ["candidate", "role_key", "enrollment", "journal", "owner"])
async def test_immutable_peer_metadata_does_not_cache_authority(enrollment_case, change):
    m = await active_registry(enrollment_case)
    p, active, peers, keys, observe, registry = (
        m.p,
        m.active,
        m.peers,
        m.keys,
        m.observe,
        m.registry,
    )
    identity = await observe(peers["control"]["identity"]["pid"])
    first = await registry.current(identity, role="control")
    assert await registry.current(identity, role="control") == first
    assert registry.original_enrollment is not None
    if change == "candidate":
        p.candidates.allowed = False
    elif change == "role_key":
        old = keys["control"]
        keys["control"] = VerificationKey(
            old.key_id, old.device_id, old.public_bytes, old.role, True
        )
    elif change == "enrollment":
        await p.service.revoke(p.owner, active["id"], meta("peer-revoke", 2))
    elif change == "journal":
        await p.control.records.delete(
            p.service.controller,
            JOURNAL,
            active["id"],
            expected_revision=1,
            request_id="peer-delete",
        )
    else:
        await p.control.browser_sessions.logout(p.owner, meta("peer-logout"))
    with pytest.raises(DomainError):
        await registry.current(identity, role="control")
    # Neither cached comparison bytes nor the old RegisteredPeer revives it.
    assert (await p.control.records.get(p.service.controller, ENROLLMENTS, active["id"])).payload


async def test_two_installed_roles_share_original_expiry_and_recheck_revocation(enrollment_case):
    """Real SQL/signatures; controlled OS/transport, never a production connection."""
    import asyncio

    m = await active_registry(enrollment_case)
    control, device = tuple(
        [
            await m.registry.current(await m.observe(m.peers[role]["identity"]["pid"]), role=role)
            for role in ("control", "device")
        ]
    )
    channel = Ref(kind="content", id="test-installed-channel", version="1", content_hash="a" * 64)

    async def current():
        for saved in (control, device):
            assert await m.registry.current(saved.identity, role=saved.role) == saved

    checks = AsyncMock(side_effect=current)
    sessions = tuple(
        SimpleNamespace(
            local=local,
            peer=peer,
            channel_ref=channel,
            pipe=SimpleNamespace(closed=asyncio.Event()),
            check=checks,
            expires_at=datetime.now(UTC) + timedelta(seconds=60 + delta),
        )
        for local, peer, delta in ((control, device, 0), (device, control, 1))
    )
    registries = tuple(
        InstalledConnectionRegistry(m.active, lifetime_seconds=60.0) for _ in sessions
    )
    for registry, session in zip(registries, sessions, strict=True):
        await registry.add(session)
    first, second = tuple(
        [await registry.read(channel, device_id=control.device_id) for registry in registries]
    )
    assert first == second
    assert first["expires_at"] == registries[0].original_expiry.isoformat()
    assert registries[0].original_expiry <= min(s.expires_at for s in sessions)
    old = m.keys["device"]
    m.keys["device"] = VerificationKey(old.key_id, old.device_id, old.public_bytes, old.role, True)
    with pytest.raises(DomainError):
        await registries[0].read(channel, device_id=control.device_id)
    assert checks.await_count == 5
    # A shortened underlying session is rejected, never extended to match its peer.
    m.keys["device"] = old
    sessions[1].expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(DomainError) as expired:
        await registries[1].read(channel, device_id=control.device_id)
    assert expired.value.failure.code == "installed_channel_expired"
