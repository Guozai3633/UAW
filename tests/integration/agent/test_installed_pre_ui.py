"""Actual SQL/OS/IPC pre-dialog wiring, with controlled rejection and no human claim."""

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

from ops.check_installed_readonly import root_lifecycle
from tests.integration.agent.test_installed_launch import cleaned, installed_environment
from tests.integration.test_browser_sessions import login
from tests.integration.test_browser_sessions import web as web
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import DomainError

ROOT = Path(__file__).resolve().parents[3]


async def test_installed_actual_sources_reach_root_dialog_without_file_access(
    web, tmp_path, monkeypatch
):
    c, client = web
    owner = Principal.model_validate((await login(client))["principal"])
    monkeypatch.setattr(
        "uaw.infrastructure.enrollment_launch.MODULE",
        "tests.integration.agent.installed_diagnostic_fixture",
    )
    env = installed_environment()
    env["PYTHONPATH"] += os.pathsep + str(ROOT)
    env["UAW_TEST_INSTALLED_DIAGNOSTIC"] = "1"
    launch = await PreparedEnrollmentLaunch.prepare(
        c,
        owner=owner,
        python=Path(sys._base_executable),
        state_directory=tmp_path.resolve(),
        currency="USD",
        environment=env,
        root_workspace=Ref(kind="workspace", id="controlled-no-read", version="1"),
    )
    try:
        await launch.start()
        await launch.connect()
        assert launch.helper is not None
        with pytest.raises(DomainError) as rejected:
            await root_lifecycle(launch.helper, deadline=asyncio.get_running_loop().time() + 110)
        assert rejected.value.failure.code == "diagnostic_reached_native", (
            rejected.value.failure.code,
            await asyncio.to_thread(
                (launch.state.path.parent / "root-selection-diagnostic.json").read_text
            ),
        )
        diagnostic = json.loads(
            await asyncio.to_thread(
                (launch.state.path.parent / "root-selection-diagnostic.json").read_text
            )
        )
        assert diagnostic == {
            "phase": "native_select",
            "error_type": "DomainError",
            "failure_code": "diagnostic_reached_native",
        }
    finally:
        await cleaned(launch)
