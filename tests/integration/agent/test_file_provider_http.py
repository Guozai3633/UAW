"""Actual HTTP/SQL admin ownership, original revision and missing-source behavior."""

import hashlib

from tests.integration.agent.test_file_provider_configuration import (
    ControlledAvailability,
    registered,
)
from tests.integration.test_browser_sessions import web as web
from tests.integration.test_control_plane import meta, seed
from uaw.shared.contracts import Principal
from uaw.shared.schema import validate_contract


async def test_file_acceptance_http_is_admin_only_and_source_gated(web):
    c, client = web
    admin = Principal(
        id=c.settings.development_admin_id,
        kind="admin",
        auth_session_id="session-" + hashlib.sha256(("a" * 40).encode()).hexdigest()[:24],
    )
    await seed(c.configuration, admin)
    provider = await registered(c.configuration, admin)
    route = "/v1/admin/providers/" + provider["id"] + "/installed-readonly-acceptance"
    request = {"meta": meta("http-file-accept", 1).wire(), "payload": {}}
    denied = await client.post(route, headers={"Authorization": "Bearer " + "u" * 40}, json=request)
    assert denied.status_code == 403
    unavailable = await client.post(
        route, headers={"Authorization": "Bearer " + "a" * 40}, json=request
    )
    validate_contract("HttpAdminProvidersAcceptResult", unavailable.json())
    assert unavailable.status_code == 503
    assert unavailable.json()["failure"]["code"] == "capability_unavailable"
    assert (await c.records.get(c.configuration.platform, "providers", provider["id"])).payload[
        "state"
    ] == "disconnected"
    c.configuration.file_availability = ControlledAvailability()
    result = await client.post(route, headers={"Authorization": "Bearer " + "a" * 40}, json=request)
    validate_contract("HttpAdminProvidersAcceptResult", result.json())
    assert result.status_code == 200 and result.json()["payload"]["state"] == "active"
    assert result.json()["payload"]["revision"] == 2
    replay = await client.post(route, headers={"Authorization": "Bearer " + "a" * 40}, json=request)
    assert replay.json() == result.json()
    assert not any(f["enabled"] for f in (await c.configuration.current())["feature_flags"])
