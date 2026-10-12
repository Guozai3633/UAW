"""Explicit-only original success test with A disposable checked-input candidate."""

from tests.integration.runner.test_installed_file_chain import (
    test_a8_file_facade_approval_budget_actual_helper_read as original_chain,
)
from tests.integration.test_browser_sessions import web as web
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch


async def test_original_chain_with_disposable_combined_metadata_inputs(web, tmp_path, monkeypatch):
    prepare = PreparedEnrollmentLaunch.prepare
    store = web[0].records
    assert not store.checked_metadata

    async def candidate_prepare(*args, **kwargs):
        monkeypatch.setattr(
            "uaw.infrastructure.enrollment_launch.MODULE",
            "tests.integration.agent.metadata_candidate_child",
        )
        environment = {**kwargs["environment"], "UAW_A18_INPUT_CANDIDATE": "1"}
        return await prepare(*args, **{**kwargs, "environment": environment})

    monkeypatch.setattr(PreparedEnrollmentLaunch, "prepare", candidate_prepare)
    store._checked_metadata = True
    try:
        await original_chain(web, tmp_path, monkeypatch)
    finally:
        store._checked_metadata = False
        store._read_plans.clear()
        assert store._current_batch.get() is None
