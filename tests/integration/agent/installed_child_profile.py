"""Original full success assertion with A observational child profiler, disposable only."""

from tests.integration.runner.test_installed_file_chain import (
    test_a8_file_facade_approval_budget_actual_helper_read as original_chain,
)
from tests.integration.test_browser_sessions import web as web
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch


async def test_original_installed_chain_with_source_profile(web, tmp_path, monkeypatch):
    prepare = PreparedEnrollmentLaunch.prepare

    async def profiled_prepare(*args, **kwargs):
        monkeypatch.setattr(
            "uaw.infrastructure.enrollment_launch.MODULE",
            "tests.integration.agent.profiled_installed_child",
        )
        return await prepare(*args, **kwargs)

    monkeypatch.setattr(PreparedEnrollmentLaunch, "prepare", profiled_prepare)
    await original_chain(web, tmp_path, monkeypatch)
