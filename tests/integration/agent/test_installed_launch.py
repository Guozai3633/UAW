"""Real A Web/SQL, hidden installed Windows child and protected delivery; no UI approval."""

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

from tests.integration.test_browser_sessions import login
from tests.integration.test_browser_sessions import web as web
from tests.integration.test_control_plane import meta
from uaw.infrastructure.credentials import WindowsCredentialStore
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch
from uaw.infrastructure.installed_helper import InstalledLaunch
from uaw.shared.contracts import Principal
from uaw.shared.errors import CapabilityUnavailable, DomainError

ROOT = Path(__file__).resolve().parents[3]


def installed_environment():
    # Test environment for the installed production module, not a test assembly.
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "src"), str(ROOT / "apps/local_runner"), str(ROOT / ".venv/Lib/site-packages")]
    )
    return env


async def prepare(c, owner, tmp_path):
    return await PreparedEnrollmentLaunch.prepare(
        c,
        owner=owner,
        python=Path(sys._base_executable),
        state_directory=tmp_path.resolve(),
        currency="USD",
        environment=installed_environment(),
    )


async def cleaned(launch):
    await launch.close()
    await launch.close()
    for handle in launch.handles:
        with pytest.raises(DomainError) as missing:
            await launch.vault.resolve(handle)
        assert missing.value.failure.code == "credential_missing"
    for key in launch.keys:
        assert launch.state.lookup(key.key_id, device_id=key.device_id).revoked
    if launch.helper:
        assert launch.helper.closed and launch.helper.process.poll() is not None
    assert (
        launch.proof is None
        or launch.proof.listener is None
        or launch.proof.listener.connection.closed.is_set()
    )


async def test_installed_prepare_real_sources_no_permission_and_idempotent_cleanup(web, tmp_path):
    c, client = web
    owner = Principal.model_validate((await login(client))["principal"])
    launch = await prepare(c, owner, tmp_path)
    try:
        helper, service = launch.helper, c.runner_enrollments
        assert helper is not None and not helper.started and helper.process.poll() is None
        value = await service.get(owner, launch.enrollment_id)
        assert value["state"] == "pending" and "pairing_ref" not in value
        assert value["proof_document"]["device"]["identity"]["pid"] == helper.process.pid
        assert launch.policy.challenge_hash and launch.policy.remaining(service.now()) <= 90
        assert len(launch.handles) == 4 and len(launch.keys) == 2
        descriptor = (await launch.vault.resolve(launch.handles[-1])).get_secret_value()
        parsed = InstalledLaunch.from_bytes(descriptor.encode())
        assert parsed.owner == owner and parsed.identity == helper.identity
        assert parsed.challenge_hash == launch.policy.challenge_hash
        assert not {"path", "approved", "proof", "code", "private_key"}.intersection(
            json.loads(descriptor)
        )
        assert helper.process.args[-1] == "uaw.infrastructure.installed_helper"
        with pytest.raises(CapabilityUnavailable) as twice:
            await prepare(c, owner, tmp_path)
        assert twice.value.failure.code == "capability_unavailable"
        # Current baseline lacks D's first start; never start with ordinary 15sec fallback.
        if "first_start" not in __import__("inspect").signature(helper.start).parameters:
            with pytest.raises(CapabilityUnavailable):
                await launch.start()
            assert not helper.started
    finally:
        await cleaned(launch)
    assert c.runner_enrollments.candidates is None


@pytest.mark.parametrize(
    "change", ["logout", "wrong_identity", "wrong_challenge", "missing_delivery"]
)
async def test_installed_actual_child_denies_changed_source_before_native(web, tmp_path, change):
    c, client = web
    owner = Principal.model_validate((await login(client))["principal"])
    launch = await prepare(c, owner, tmp_path)
    try:
        if change == "logout":
            await c.browser_sessions.logout(owner, meta("installed-logout"))
        elif change == "missing_delivery":
            await launch.vault.delete(launch.handles[-1])
        else:
            handle = launch.handles[-1]
            value = json.loads((await launch.vault.resolve(handle)).get_secret_value())
            if change == "wrong_identity":
                value["identity"]["created"] += 1
            else:
                value["challenge_hash"] = "a" * 64
            from pydantic import SecretStr

            await launch.vault.put(handle, SecretStr(json.dumps(value)))
        # Invoke the existing ordinary host only to prove denial before a native window;
        # this is not first-start success/90sec verification and sends no file command.
        events = []
        original_event = launch.helper.event

        async def observed_event(**kwargs):
            event = await original_event(**kwargs)
            events.append(event)
            return event

        launch.helper.event = observed_event
        with pytest.raises(DomainError):
            await launch.helper.start()
        expected_code = {
            "logout": "web_session_revoked",
            "wrong_identity": "enrollment_installed_instance_denied",
            "wrong_challenge": "enrollment_installed_source_changed",
            "missing_delivery": "credential_missing",
        }[change]
        assert events[0] == {"event": "failure", "code": expected_code}
        if not launch.helper.closed:
            assert (await launch.helper.event())["event"] == "closed"
        async with asyncio.timeout(5):
            await asyncio.to_thread(launch.helper.process.wait)
    finally:
        await cleaned(launch)


async def test_installed_logout_rejects_before_allocating_private_sources(web, tmp_path):
    c, client = web
    owner = Principal.model_validate((await login(client))["principal"])
    await c.browser_sessions.logout(owner, meta("before-launch-logout"))
    with pytest.raises(DomainError) as rejected:
        await prepare(c, owner, tmp_path)
    assert rejected.value.failure.code == "web_session_revoked"
    assert not list(tmp_path.iterdir())


async def test_installed_cancel_late_os_credential_write_is_drained_and_deleted(
    web, tmp_path, monkeypatch
):
    c, client = web
    owner = Principal.model_validate((await login(client))["principal"])
    entered, release = asyncio.Event(), asyncio.Event()
    created = []
    real = WindowsCredentialStore.put

    async def late(store, handle, secret):
        await real(store, handle, secret)
        created.append((store, handle))
        entered.set()
        await release.wait()

    monkeypatch.setattr(WindowsCredentialStore, "put", late)
    task = asyncio.create_task(prepare(c, owner, tmp_path))
    try:
        async with asyncio.timeout(5):
            await entered.wait()
        task.cancel()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert len(created) == 1
        for store, handle in created:
            with pytest.raises(DomainError) as missing:
                await store.resolve(handle)
            assert missing.value.failure.code == "credential_missing"
        assert c.runner_enrollments.candidates is None
    finally:
        release.set()
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)
