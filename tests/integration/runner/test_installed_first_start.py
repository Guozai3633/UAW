"""A fixed installed production module with real D SQL/Web/OS protected delivery.

Only cancellation/source denial; never affirmative native UI or user directory access.
"""

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

import pytest

from tests.integration.test_browser_sessions import login
from tests.integration.test_browser_sessions import web as web
from tests.integration.test_control_plane import meta
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch
from uaw.shared.contracts import Principal
from uaw.shared.errors import DomainError

ROOT = Path(__file__).resolve().parents[3]


def environment():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "src"), str(ROOT / "apps/local_runner"), str(ROOT / ".venv/Lib/site-packages")]
    )
    return env


async def prepare(c, owner, path):
    assert ":55435/" in os.environ["UAW_TEST_DATABASE_URL"]
    return await PreparedEnrollmentLaunch.prepare(
        c,
        owner=owner,
        python=Path(sys._base_executable),
        state_directory=path.resolve(),
        currency="USD",
        environment=environment(),
    )


async def cleanup(launch, path):
    report = dict(
        source="A-ms-i2l-a1-fixed-installed",
        backend="real_D55435_SQL_Web_WinVault",
        human_confirmation="pending_no_Yes",
        cleaned=False,
    )
    try:
        await asyncio.gather(launch.close(), launch.close())
        missing = 0
        for handle in launch.handles:
            with pytest.raises(DomainError) as absent:
                await launch.vault.resolve(handle)
            assert absent.value.failure.code == "credential_missing"
            missing += 1
        assert missing == 4
        assert all(
            launch.state.lookup(key.key_id, device_id=key.device_id).revoked for key in launch.keys
        )
        assert launch.helper.closed and launch.helper.process.returncode == 0
        assert launch.helper.process.stdin.closed and launch.helper.process.stdout.closed
        assert launch.proof.listener.connection.closed.is_set()
        report.update(
            cleaned=True,
            protected_handles_deleted=missing,
            role_keys_revoked=2,
            owned_process_exit=0,
            proof_pipe_closed=True,
        )
    finally:
        await asyncio.to_thread(
            (path.parents[1] / ("installed-cleanup-" + uuid.uuid4().hex + ".json")).write_text,
            json.dumps(report, indent=2),
            encoding="utf-8",
        )


@pytest.mark.parametrize("action", ["stop", "EOF", "cancel", "logout", "key-revoked"])
async def test_actual_installed_first_wait_current_sources_cancel_and_cleanup(
    web, tmp_path, action
):
    c, client = web
    owner = Principal.model_validate((await login(client))["principal"])
    launch = await prepare(c, owner, tmp_path)
    waiting = asyncio.Event()
    seen = []

    class Observer:
        async def waiting(self, policy):
            assert policy == launch.policy
            seen.append(policy)
            waiting.set()

    task = asyncio.create_task(launch.start(on_progress=Observer()))
    try:
        async with asyncio.timeout(12):
            await waiting.wait()
        assert seen == [launch.policy]
        # Real protected proof has been received and checked before progress/native.
        assert launch.proof.used
        assert (await c.runner_enrollments.get(owner, launch.enrollment_id))["state"] == "pending"
        await asyncio.sleep(0.3)  # Permit only own native window to open; never click Yes.
        if action == "stop":
            await launch.close()
        elif action == "EOF":
            await asyncio.to_thread(launch.helper.process.stdin.close)
        elif action == "cancel":
            task.cancel()
        elif action == "logout":
            await c.browser_sessions.logout(owner, meta("D-installed-wait-logout"))
        else:
            key = launch.keys[0]
            await asyncio.to_thread(launch.state.revoke_key, key.key_id, expected_revision=0)
        if action == "cancel":
            with pytest.raises(asyncio.CancelledError):
                await task
        else:
            async with asyncio.timeout(12):
                with pytest.raises(DomainError) as denied:
                    await task
            if action == "logout":
                assert denied.value.failure.code == "web_session_revoked"
            elif action == "key-revoked":
                assert denied.value.failure.code == "enrollment_launcher_key_denied"
        assert seen == [launch.policy]
    finally:
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        await cleanup(launch, tmp_path)


async def test_actual_installed_restart_new_original_candidate_and_wait(web, tmp_path):
    c, client = web
    owner = Principal.model_validate((await login(client))["principal"])
    originals = []
    for index in range(2):
        path = tmp_path / ("launch-" + str(index))
        launch = await prepare(c, owner, path)
        waiting = asyncio.Event()

        class Observer:
            def __init__(self, original, signal):
                self.original, self.signal = original, signal

            async def waiting(self, policy):
                assert policy == self.original
                self.signal.set()

        task = asyncio.create_task(launch.start(on_progress=Observer(launch.policy, waiting)))
        try:
            async with asyncio.timeout(12):
                await waiting.wait()
            record = await c.runner_enrollments.get(owner, launch.enrollment_id)
            assert record["state"] == "pending" and "pairing_ref" not in record
            originals.append(
                (
                    launch.helper.identity,
                    launch.candidate_id,
                    launch.enrollment_id,
                    launch.policy.challenge_hash,
                )
            )
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            await cleanup(launch, path)
    assert all(old != new for old, new in zip(originals[0], originals[1], strict=True))
