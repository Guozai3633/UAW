"""Original root-owner relationship: real SQL/crypto, controlled OS/native inputs."""

import pytest

from tests.integration.agent.test_enrolled_peer_current import active_registry
from tests.integration.agent.test_enrollment_postgres import enrollment_case as enrollment_case
from tests.integration.test_browser_sessions import web as web
from tests.integration.test_control_plane import meta
from uaw.infrastructure.enrollment_native import JOURNAL
from uaw.shared.contracts import Principal
from uaw.shared.errors import DomainError
from uaw.shared.runner_signatures import VerificationKey


@pytest.mark.parametrize(
    "change",
    [
        "none",
        "session",
        "device",
        "control_key",
        "device_key",
        "candidate",
        "journal",
        "logout",
        "enrollment",
    ],
)
async def test_root_owner_requires_original_current_relationship(enrollment_case, change):
    m = await active_registry(enrollment_case)
    p = m.p
    owner, device_id = p.owner, m.peers["device_id"]
    assert await m.registry.owner(authenticated_principal=owner, device_id=device_id) == owner
    if change == "none":
        for role in ("control", "device"):
            actor = Principal.model_validate(m.peers[role]["actor"])
            assert (
                await m.registry.owner(authenticated_principal=actor, device_id=device_id) == owner
            )
        return
    if change == "session":
        owner = owner.model_copy(update={"auth_session_id": "other-original-session"})
    elif change == "device":
        device_id = "other-device"
    elif change.endswith("_key"):
        role = change.removesuffix("_key")
        key = m.keys[role]
        m.keys[role] = VerificationKey(key.key_id, key.device_id, key.public_bytes, key.role, True)
    elif change == "candidate":
        p.candidates.allowed = False
    elif change == "journal":
        await p.control.records.delete(
            p.service.controller,
            JOURNAL,
            m.active["id"],
            expected_revision=1,
            request_id="root-owner-delete",
        )
    elif change == "logout":
        await p.control.browser_sessions.logout(p.owner, meta("root-owner-logout"))
    else:
        await p.service.revoke(p.owner, m.active["id"], meta("root-owner-revoke", 2))
    with pytest.raises(DomainError):
        await m.registry.owner(authenticated_principal=owner, device_id=device_id)


async def test_root_owner_catches_key_revocation_during_final_os_await(enrollment_case):
    m = await active_registry(enrollment_case)
    original = m.registry.observe
    count = 0

    async def observe(pid):
        nonlocal count
        count += 1
        if count == 3:
            key = m.keys["device"]
            m.keys["device"] = VerificationKey(
                key.key_id, key.device_id, key.public_bytes, key.role, True
            )
        return await original(pid)

    m.registry.observe = observe
    with pytest.raises(DomainError) as denied:
        await m.registry.owner(authenticated_principal=m.p.owner, device_id=m.peers["device_id"])
    assert denied.value.failure.code == "enrolled_current_key_denied"
