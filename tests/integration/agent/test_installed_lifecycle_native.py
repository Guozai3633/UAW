"""Actual HTTP/SQL/OS/IPC lifecycle; native input is the test's own disposable root."""

import asyncio
import os
from pathlib import Path

from tests.integration.agent.test_installed_launch import cleaned
from tests.integration.agent.test_installed_lifecycle import configured
from tests.integration.test_browser_sessions import ORIGIN, envelope, login
from tests.integration.test_browser_sessions import web as web
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch
from uaw.shared.contracts import Principal

ROOT = Path(__file__).resolve().parents[3]


async def test_actual_http_launch_to_complete_callback_ready_and_owned_stop(
    web, tmp_path, monkeypatch
):
    c, client = web
    public = await login(client)
    owner = Principal.model_validate(public["principal"])
    service = configured(c, tmp_path)
    selected = tmp_path / "explicit-disposable-directory"
    await asyncio.to_thread(selected.mkdir)
    original = PreparedEnrollmentLaunch.prepare
    monkeypatch.setattr(
        "uaw.infrastructure.enrollment_launch.MODULE",
        "tests.integration.agent.installed_diagnostic_fixture",
    )

    async def controlled_prepare(*args, **kwargs):
        env = dict(kwargs["environment"])
        env["PYTHONPATH"] += os.pathsep + str(ROOT)
        env["UAW_TEST_INSTALLED_DIAGNOSTIC"] = "1"
        env["UAW_TEST_INSTALLED_SELECTED_ROOT"] = str(selected)
        return await original(*args, **{**kwargs, "environment": env})

    monkeypatch.setattr(
        "uaw.infrastructure.installed_lifecycle.PreparedEnrollmentLaunch.prepare",
        controlled_prepare,
    )
    headers = {"Origin": ORIGIN, "X-UAW-CSRF": public["csrf_token"]}
    submitted = await client.post("/v1/runner/local", headers=headers, json=envelope("native-once"))
    assert submitted.status_code == 202
    identifier = submitted.json()["payload"]["id"]
    try:
        async with asyncio.timeout(150):
            while True:
                view = await service.record(owner, identifier)
                if view["state"] in ("ready", "closed", "failed", "unavailable"):
                    break
                await asyncio.sleep(0.2)
        assert view["state"] == "ready", view
        assert "device_ref" in view and "expires_at" in view
        # This GET independently checks actual original journal/signature/live keys,
        # not the persistent ready state or the controlled directory input.
        observed = await client.get("/v1/runner/local/" + identifier, headers={"Origin": ORIGIN})
        assert observed.status_code == 200 and observed.json()["payload"]["state"] == "ready"
        stopped = await client.post(
            "/v1/runner/local/" + identifier + "/stop",
            headers=headers,
            json=envelope("native-stop"),
        )
        assert stopped.status_code == 200 and stopped.json()["payload"]["state"] == "closed"
        assert service.active.done.is_set()
        await cleaned(service.active.launch)
    finally:
        await service.close_owner(owner)
