"""Real PostgreSQL and HTTP session boundaries, including restart and racing exchange."""

import asyncio
import json
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import delete, select

from uaw.api.application import create_app
from uaw.api.browser import COOKIE, SESSIONS, TICKETS, BrowserSessions
from uaw.composition import Container, compose
from uaw.infrastructure.db.models import RecordRow, RecordVersionRow, RequestRow
from uaw.shared.contracts import Principal
from uaw.shared.errors import DomainError
from uaw.shared.schema import validate_contract
from uaw.shared.settings import Settings

ORIGIN = "http://127.0.0.1:5173"
API = "http://127.0.0.1:8000"


def envelope(name: str, **payload: str) -> dict:
    return {"meta": {"request_id": name, "schema_version": "0.1"}, "payload": payload}


@pytest.fixture
async def web(database, principal) -> AsyncIterator[tuple[Container, httpx.AsyncClient]]:
    settings = Settings(
        profile="development",
        development_principal_id=principal.id,
        platform_id="web-platform-" + principal.id,
        development_admin_id="admin-" + principal.id,
        development_user_token=SecretStr("u" * 40),
        development_admin_token=SecretStr("a" * 40),
        cursor_signing_key=SecretStr("c" * 40),
        browser_session_signing_key=SecretStr("b" * 40),
        browser_origin=ORIGIN,
        database_url=SecretStr(os.environ["UAW_TEST_DATABASE_URL"]),
    )
    container = compose(settings)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(container)),
        base_url=API,
    ) as client:
        try:
            yield container, client
        finally:
            async with database.sessions.begin() as session:
                for table in (RequestRow, RecordVersionRow, RecordRow):
                    await session.execute(
                        delete(table).where(table.principal_id == settings.platform_id)
                    )
            await container.close()


async def launch(client: httpx.AsyncClient, name: str = "launch") -> str:
    response = await client.post(
        "/v1/web/launch",
        headers={"Authorization": "Bearer " + "u" * 40},
        json=envelope(name),
    )
    assert response.status_code == 200, response.json()
    validate_contract("HttpWebLaunchResult", response.json())
    assert response.headers["cache-control"] == "no-store"
    url = urlsplit(response.json()["payload"]["launch_url"])
    assert f"{url.scheme}://{url.netloc}" == ORIGIN and not url.query
    return parse_qs(url.fragment)["uaw_launch"][0]


async def login(client: httpx.AsyncClient) -> dict:
    code = await launch(client)
    response = await client.post(
        "/v1/web/session",
        headers={"Origin": ORIGIN},
        json=envelope("login", launch_code=code),
    )
    assert response.status_code == 200, response.json()
    validate_contract("HttpWebSessionExchangeResult", response.json())
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie and "Domain=" not in cookie
    assert "Path=/v1" in cookie
    return response.json()["payload"]


async def test_real_session_logout_restart_and_no_persisted_credentials(web):
    container, client = web
    public = await login(client)
    actor = Principal.model_validate(public["principal"])
    assert actor.id == container.settings.development_principal_id and actor.kind == "user"
    restarted = BrowserSessions(container.records, container.settings)
    assert restarted.public(await restarted.principal(actor)) == public
    read = await client.get("/v1/web/session", headers={"Referer": ORIGIN + "/"})
    assert read.status_code == 200 and read.json()["payload"] == public
    async with container.database.sessions() as session:
        rows = (
            await session.scalars(
                select(RecordRow).where(
                    RecordRow.principal_id == container.settings.platform_id,
                )
            )
        ).all()
        requests = (
            await session.scalars(
                select(RequestRow).where(
                    RequestRow.principal_id == container.settings.platform_id,
                )
            )
        ).all()
        serialized = json.dumps([r.payload for r in rows] + [r.result for r in requests])
    assert public["csrf_token"] not in serialized
    assert client.cookies.get(COOKIE) not in serialized
    assert "u" * 40 not in serialized and "a" * 40 not in serialized
    response = await client.request(
        "DELETE",
        "/v1/web/session",
        headers={"Origin": ORIGIN, "X-UAW-CSRF": public["csrf_token"]},
        json=envelope("logout"),
    )
    assert response.status_code == 200 and "Max-Age=0" in response.headers["set-cookie"]
    with pytest.raises(DomainError, match="revoked"):
        await restarted.principal(actor)
    assert (await client.get("/v1/web/session", headers={"Origin": ORIGIN})).status_code == 401


async def test_one_launch_code_consumed_by_one_concurrent_request(web):
    container, client = web
    code = await launch(client)

    async def exchange(name):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=create_app(container)), base_url=API
        ) as peer:
            return await peer.post(
                "/v1/web/session", headers={"Origin": ORIGIN}, json=envelope(name, launch_code=code)
            )

    responses = await asyncio.gather(exchange("login-a"), exchange("login-b"))
    assert sorted(r.status_code for r in responses) == [200, 409]
    assert (
        next(r for r in responses if r.status_code == 409).json()["failure"]["code"]
        == "web_ticket_used"
    )
    assert (
        await client.post(
            "/v1/web/session",
            headers={"Origin": ORIGIN},
            json=envelope("login-a", launch_code=code),
        )
    ).status_code == 409
    with pytest.raises(DomainError):
        await BrowserSessions(container.records, container.settings).exchange(code)


@pytest.mark.parametrize(
    "origin", ["https://untrusted.invalid", "http://localhost:5173", ORIGIN + "/", "null", None]
)
async def test_exchange_denies_nonexact_origin_before_consuming_ticket(web, origin):
    _, client = web
    code = await launch(client)
    headers = {"Origin": origin} if origin else {}
    response = await client.post(
        "/v1/web/session", headers=headers, json=envelope("login", launch_code=code)
    )
    assert response.status_code == 403 and response.json()["failure"]["code"] == "origin_denied"
    assert (
        await client.post(
            "/v1/web/session", headers={"Origin": ORIGIN}, json=envelope("good", launch_code=code)
        )
    ).status_code == 200


@pytest.mark.parametrize(
    "headers",
    [{}, {"X-UAW-CSRF": "0" * 64}, {"Origin": "https://wrong.invalid", "X-UAW-CSRF": "0" * 64}],
)
async def test_write_requires_current_csrf_and_origin(web, headers):
    _, client = web
    public = await login(client)
    response = await client.request(
        "DELETE", "/v1/web/session", headers={"Origin": ORIGIN, **headers}, json=envelope("logout")
    )
    assert response.status_code == 403
    assert (await client.get("/v1/web/session", headers={"Origin": ORIGIN})).json()[
        "payload"
    ] == public


async def test_user_only_launch_and_cli_compatibility(web):
    _, client = web
    assert (
        await client.post(
            "/v1/web/launch",
            headers={"Authorization": "Bearer " + "a" * 40},
            json=envelope("launch"),
        )
    ).status_code == 403
    assert (
        await client.post(
            "/v1/web/launch",
            headers={"Authorization": "Bearer " + "u" * 40, "Origin": ORIGIN},
            json=envelope("launch"),
        )
    ).status_code == 403
    code = await launch(client)
    assert code == await launch(client)  # original request receipt, no second ticket
    assert (
        await client.get("/v1/models", headers={"Authorization": "Bearer " + "u" * 40})
    ).status_code != 401
    await login(client)
    assert (
        await client.get("/v1/admin/configuration", headers={"Origin": ORIGIN})
    ).status_code == 403
    assert (
        await client.get(
            "/v1/models", headers={"Origin": ORIGIN, "Authorization": "Bearer " + "a" * 40}
        )
    ).status_code == 403


@pytest.mark.parametrize("change", ["expired", "user", "origin", "key"])
async def test_session_expiry_and_settings_rotation_revoke_original(web, change):
    container, client = web
    public = await login(client)
    actor = Principal.model_validate(public["principal"])
    service = container.browser_sessions
    if change == "expired":
        row = await service.records.get(service.owner, SESSIONS, actor.auth_session_id)
        await service.records.put(
            service.owner,
            SESSIONS,
            row.resource_id,
            row.schema_name,
            {
                **row.payload,
                "expires_at": (datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
                "revision": 2,
            },
            expected_revision=1,
            request_id="expire",
        )
    else:
        update = {
            "user": {"development_user_token": SecretStr("v" * 40)},
            "origin": {"browser_origin": "http://127.0.0.1:5174"},
            "key": {"browser_session_signing_key": SecretStr("z" * 40)},
        }[change]
        service = BrowserSessions(container.records, container.settings.model_copy(update=update))
    if change == "key":
        with pytest.raises(DomainError):
            service.decode("session", client.cookies.get(COOKIE))
    else:
        with pytest.raises(DomainError):
            await service.principal(actor)


async def test_expired_ticket_not_consumed_and_bad_host_rejected(web):
    container, client = web
    code = await launch(client)
    service = container.browser_sessions
    ticket_id = service.decode("launch", code)
    row = await service.records.get(service.owner, TICKETS, ticket_id)
    await service.records.put(
        service.owner,
        TICKETS,
        ticket_id,
        row.schema_name,
        {
            **row.payload,
            "expires_at": (datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
            "revision": 2,
        },
        expected_revision=1,
        request_id="expire",
    )
    response = await client.post(
        "/v1/web/session", headers={"Origin": ORIGIN}, json=envelope("login", launch_code=code)
    )
    assert (
        response.status_code == 401 and response.json()["failure"]["code"] == "web_ticket_expired"
    )
    fresh = await launch(client, "fresh")
    response = await client.post(
        "/v1/web/session",
        headers={"Origin": ORIGIN, "Host": "attacker.invalid:8000"},
        json=envelope("login", launch_code=fresh),
    )
    assert response.status_code == 403 and response.json()["failure"]["code"] == "web_host_denied"


async def test_precise_cors_and_duplicate_cookie_rejection(web):
    _, client = web
    preflight = await client.options(
        "/v1/web/session",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "DELETE",
            "Access-Control-Request-Headers": "content-type,x-uaw-csrf",
        },
    )
    assert (
        preflight.status_code == 200 and preflight.headers["access-control-allow-origin"] == ORIGIN
    )
    assert preflight.headers["access-control-allow-credentials"] == "true"
    denied = await client.options(
        "/v1/web/session",
        headers={"Origin": "https://wrong.invalid", "Access-Control-Request-Method": "POST"},
    )
    assert denied.status_code == 400 and "access-control-allow-origin" not in denied.headers
    await login(client)
    cookie = client.cookies.get(COOKIE)
    response = await client.get(
        "/v1/web/session",
        headers={"Origin": ORIGIN, "Cookie": f"{COOKIE}={cookie}; {COOKIE}={cookie}"},
    )
    assert response.status_code == 401


async def test_exchange_body_owner_injection_is_rejected(web):
    _, client = web
    code = await launch(client)
    response = await client.post(
        "/v1/web/session",
        headers={"Origin": ORIGIN},
        json=envelope("login", launch_code=code, principal="admin"),
    )
    assert response.status_code == 422
    assert (
        await client.post(
            "/v1/web/session", headers={"Origin": ORIGIN}, json=envelope("login", launch_code=code)
        )
    ).status_code == 200


async def test_forwarded_loopback_cannot_override_actual_remote_peer(web):
    container, client = web
    code = await launch(client)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(container), client=("192.0.2.1", 1234)),
        base_url=API,
    ) as remote:
        response = await remote.post(
            "/v1/web/session",
            headers={"Origin": ORIGIN, "X-Forwarded-For": "127.0.0.1"},
            json=envelope("login", launch_code=code),
        )
    assert response.status_code == 403 and response.json()["failure"]["code"] == "web_host_denied"


async def test_corrupt_credential_and_referer_are_denied(web):
    _, client = web
    await login(client)
    response = await client.get("/v1/web/session", headers={"Referer": "http://[invalid/"})
    assert response.status_code == 403
    cookie = client.cookies.get(COOKIE)
    response = await client.get(
        "/v1/web/session",
        headers={
            "Origin": ORIGIN,
            "Cookie": COOKIE + "=" + cookie[:-1] + ("0" if cookie[-1] != "0" else "1"),
        },
    )
    assert response.status_code == 401
