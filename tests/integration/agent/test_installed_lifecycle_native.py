"""Actual HTTP/SQL/OS/IPC lifecycle; native input is the test's own disposable root."""

import asyncio
import os
from pathlib import Path

import pytest

from tests.integration.agent.test_installed_launch import cleaned
from tests.integration.agent.test_installed_lifecycle import configured
from tests.integration.test_browser_sessions import ORIGIN, envelope, login
from tests.integration.test_browser_sessions import web as web
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch
from uaw.infrastructure.installed_files import assemble_installed_file
from uaw.shared.contracts import Principal, Ref, Scope, TrustedExecutionContext
from uaw.shared.errors import DomainError
from uaw.tool.providers.file_read import file_read_spec
from uaw.tool.registry import AdapterBinding, ToolRegistry

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("consume_file_sources", [False, True])
async def test_actual_http_launch_to_complete_callback_ready_and_owned_stop(
    web, tmp_path, monkeypatch, consume_file_sources
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
        if consume_file_sources:
            # This consumer verifies the installed root/device/signing/pipe
            # assembly only. No configured file provider, Run, approval, budget,
            # command admission or content read is inferred from these sources.
            workspace = Ref.model_validate(view["workspace_ref"])
            provider_ref = Ref(kind="provider", id="not-published-file-provider", version="1")
            registry = ToolRegistry()
            registry.register(
                file_read_spec(provider_ref),
                expected_revision=0,
                binding=AdapterBinding(provider_ref, frozenset({"development"}), implemented=True),
            )
            tool_ref = Ref.model_validate(registry.reference(registry.snapshot()[1][0]))
            actual = await assemble_installed_file(
                c,
                owner=owner,
                workspace=workspace,
                registry=registry,
                tool_ref=tool_ref,
                provider=Principal(
                    id="internal-file-provider", kind="service", auth_session_id="internal"
                ),
                money_ceiling="0.05",
            )
            actual.bridge.ready()
            ctx = TrustedExecutionContext(
                principal=owner,
                scope=Scope(
                    principal_id=owner.id,
                    resource_refs=(workspace,),
                    capabilities=("file.read", "workspace.process"),
                ),
                capability_policy_ref=Ref(kind="policy", id="no-run-policy", version="1"),
                operation_id="source-inspection",
                trace_id="source-trace",
                attempt_id="source-attempt",
                deadline=view["expires_at"],
            )
            # No missing Run may be promoted to an executable command.
            with pytest.raises(DomainError):
                await actual.bridge.commands._run(ctx)
            route = await actual.route.current(workspace, ctx)
            assert route.device_ref == Ref.model_validate(view["device_ref"])
            root = await actual.control.commands.roots.current(route.device_ref.id, workspace, ctx)
            assert root["owner"] == owner.wire() and root["workspace_ref"] == workspace.wire()
            assert set(root["allowed_actions"]) <= {"file.read", "file.list"}
            assert actual.bridge.pipe.session is service.active.launch.connection.session
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
