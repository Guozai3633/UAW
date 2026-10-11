"""Real SQL/Web ownership and cancellation; fake native work is explicitly labelled."""

import asyncio
import json

import pytest

from tests.integration.test_browser_sessions import ORIGIN, envelope, login
from tests.integration.test_browser_sessions import web as web
from uaw.infrastructure.installed_lifecycle import InstalledLifecycle, installed_environment
from uaw.shared.contracts import Principal, RequestMeta
from uaw.shared.errors import DomainError


def configured(c, tmp_path):
    c.settings = c.settings.model_copy(
        update={
            "installed_state_directory": tmp_path.resolve(),
            "installed_workspace_id": "explicit-controlled-workspace",
        }
    )
    c.installed_lifecycle = InstalledLifecycle(c)
    return c.installed_lifecycle


class PendingNative:
    """Only a labelled blocked UI boundary; never claims OS, pairing or root success."""

    def __init__(self):
        self.enrollment_id = "controlled-enrollment"
        self.started = asyncio.Event()
        self.cleaned = asyncio.Event()
        self.closes = 0

    async def start(self):
        self.started.set()
        await asyncio.Event().wait()

    async def close(self):
        await asyncio.sleep(0)
        self.closes += 1
        self.cleaned.set()


async def test_http_current_web_csrf_original_request_and_logout_drain(web, tmp_path, monkeypatch):
    c, client = web
    public = await login(client)
    service = configured(c, tmp_path)
    pending = PendingNative()
    preparations = []

    async def prepare(*args, **kwargs):
        preparations.append(kwargs)
        return pending

    monkeypatch.setattr(
        "uaw.infrastructure.installed_lifecycle.PreparedEnrollmentLaunch.prepare", prepare
    )
    headers = {"Origin": ORIGIN, "X-UAW-CSRF": public["csrf_token"]}
    denied = await client.post(
        "/v1/runner/local", headers={"Origin": ORIGIN}, json=envelope("same")
    )
    assert denied.status_code == 403 and not preparations
    denied = await client.post(
        "/v1/runner/local", headers=headers, json=envelope("same", approved=True)
    )
    assert denied.status_code == 422 and not preparations
    first, replay = await asyncio.gather(
        *[client.post("/v1/runner/local", headers=headers, json=envelope("same")) for _ in range(2)]
    )
    assert first.status_code == replay.status_code == 202
    identifier = first.json()["payload"]["id"]
    assert identifier == replay.json()["payload"]["id"]
    await asyncio.wait_for(pending.started.wait(), 5)
    assert len(preparations) == 1 and preparations[0]["owner"].wire() == public["principal"]
    assert "path" not in preparations[0] and "approved" not in preparations[0]
    read = await client.get("/v1/runner/local/" + identifier, headers={"Origin": ORIGIN})
    assert read.status_code == 200 and read.json()["payload"]["state"] == "waiting_device"
    busy = await client.post("/v1/runner/local", headers=headers, json=envelope("different"))
    assert busy.status_code == 409
    logout = await client.request(
        "DELETE", "/v1/web/session", headers=headers, json=envelope("logout")
    )
    assert logout.status_code == 200 and pending.cleaned.is_set() and pending.closes == 1
    row = await service.record(Principal.model_validate(public["principal"]), identifier)
    assert row["state"] == "closed" and service.active.done.is_set()
    assert (
        await client.get("/v1/runner/local/" + identifier, headers={"Origin": ORIGIN})
    ).status_code == 401


async def test_same_account_new_session_cannot_take_launch(web, tmp_path, monkeypatch):
    c, client = web
    first = await login(client)
    owner = Principal.model_validate(first["principal"])
    service = configured(c, tmp_path)
    pending = PendingNative()

    async def prepare(*args, **kwargs):
        return pending

    monkeypatch.setattr(
        "uaw.infrastructure.installed_lifecycle.PreparedEnrollmentLaunch.prepare", prepare
    )
    view = await service.begin(owner, RequestMeta(request_id="first", schema_version="0.1"))
    await pending.started.wait()
    # Actual second browser session, not a forged auth_session_id.
    ticket = await c.browser_sessions.launch(
        Principal(id=owner.id, kind="user", auth_session_id="cli"),
        RequestMeta(request_id="second-login", schema_version="0.1"),
    )
    second, _ = await c.browser_sessions.exchange(ticket["launch_url"].split("#uaw_launch=", 1)[1])
    peer = Principal.model_validate(second["principal"])
    assert peer.id == owner.id and peer.auth_session_id != owner.auth_session_id
    with pytest.raises(DomainError) as denied:
        await service.get(peer, view["id"])
    assert denied.value.failure.code == "installed_owner_denied"
    await service.close_owner(peer)
    assert not pending.cleaned.is_set()
    await service.close_owner(owner)
    assert pending.cleaned.is_set()


async def test_restart_marks_original_unavailable_without_launching(web, tmp_path):
    c, client = web
    owner = Principal.model_validate((await login(client))["principal"])
    service = configured(c, tmp_path)
    # Prevent the worker from starting; no fake ready, root or permission record.
    original_run = service.run

    async def wait(entry):
        await asyncio.Event().wait()

    service.run = wait
    view = await service.begin(owner, RequestMeta(request_id="restart", schema_version="0.1"))
    service.active.task.cancel()
    await asyncio.gather(service.active.task, return_exceptions=True)
    service.active.done.set()
    service.run = original_run
    restarted = InstalledLifecycle(c)
    observed = await restarted.get(owner, view["id"])
    assert observed["state"] == "unavailable"
    assert observed["failure_code"] == "installed_instance_lost" and restarted.active is None
    replay = await restarted.begin(owner, RequestMeta(request_id="restart", schema_version="0.1"))
    assert replay == observed and restarted.active is None


async def test_cancel_before_worker_is_scheduled_does_not_allocate(web, tmp_path, monkeypatch):
    c, client = web
    owner = Principal.model_validate((await login(client))["principal"])
    service = configured(c, tmp_path)
    calls = []

    async def prepare(*args, **kwargs):
        calls.append(True)
        raise AssertionError("cancelled before native allocation")

    monkeypatch.setattr(
        "uaw.infrastructure.installed_lifecycle.PreparedEnrollmentLaunch.prepare", prepare
    )
    view = await service.begin(
        owner, RequestMeta(request_id="immediate-stop", schema_version="0.1")
    )
    await asyncio.gather(service.close_owner(owner), service.close_owner(owner))
    assert not calls and (await service.get(owner, view["id"]))["state"] == "closed"


async def test_default_deployment_and_cli_do_not_allocate(web, tmp_path):
    c, client = web
    public = await login(client)
    headers = {"Origin": ORIGIN, "X-UAW-CSRF": public["csrf_token"]}
    response = await client.post("/v1/runner/local", headers=headers, json=envelope("no-config"))
    assert response.status_code == 503 and c.installed_lifecycle is None
    service = configured(c, tmp_path)
    with pytest.raises(DomainError) as denied:
        await service.begin(
            Principal(id=c.settings.development_principal_id, kind="user", auth_session_id="cli"),
            RequestMeta(request_id="cli", schema_version="0.1"),
        )
    assert denied.value.failure.code == "installed_web_required" and service.active is None


def test_installed_environment_does_not_forward_secrets_or_import_selector(monkeypatch):
    monkeypatch.setenv("UAW_DATABASE_URL", "fake-secret-db")
    monkeypatch.setenv("UAW_TEST_INSTALLED_DIAGNOSTIC", "1")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-secret-model")
    monkeypatch.setenv("PYTHONPATH", "untrusted/module")
    actual = installed_environment()
    assert not {
        "UAW_DATABASE_URL",
        "DEEPSEEK_API_KEY",
        "UAW_TEST_INSTALLED_DIAGNOSTIC",
    }.intersection(actual)
    assert "untrusted/module" not in actual["PYTHONPATH"]
    assert "fake-secret" not in json.dumps(actual)
