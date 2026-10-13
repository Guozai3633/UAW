"""Run the unchanged original successful first-read/recovery assertions with timing."""

from tests.integration.runner.test_installed_file_chain import (
    test_a8_file_facade_approval_budget_actual_helper_read as original_first_chain,
)
from tests.integration.test_browser_sessions import web as web
from uaw.infrastructure import enrollment_launch
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch


async def test_original_first_read_and_recovery_with_source_trace(web, tmp_path, monkeypatch):
    original_prepare = PreparedEnrollmentLaunch.prepare

    async def traced_prepare(*args, **kwargs):
        environment = dict(kwargs["environment"])
        environment["UAW_A_READ_TRACE"] = str((tmp_path / "source-trace.json").resolve())
        # D's existing fixture calls this wrapper after selecting its normal
        # measured helper. Only this private launch substitutes the A observer.
        monkeypatch.setattr(
            enrollment_launch, "MODULE", "tests.integration.agent.installed_read_trace"
        )
        return await original_prepare(*args, **{**kwargs, "environment": environment})

    monkeypatch.setattr(PreparedEnrollmentLaunch, "prepare", traced_prepare)
    await original_first_chain(web, tmp_path, monkeypatch)
