"""Root onboarding diagnostics fail promptly and never expose raw child input."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from ops.check_installed_readonly import root_diagnostic, root_lifecycle
from uaw.shared.errors import DomainError


async def test_original_child_failure_surfaces_without_waiting_for_root_expiry():
    helper = SimpleNamespace(
        event=AsyncMock(return_value={"event": "failure", "code": "native_busy"})
    )
    with pytest.raises(DomainError) as failed:
        await root_lifecycle(helper, deadline=123)
    assert failed.value.failure.code == "native_busy"
    helper.event.assert_awaited_once_with(deadline=123)


@pytest.mark.parametrize(
    "event",
    [
        {"event": "failure", "code": "secret\nvalue"},
        {"event": "failure", "code": "native_busy", "path": "private"},
        {"event": "closed"},
        {"event": "ready", "name": "private"},
    ],
)
async def test_unexpected_child_frame_fails_closed_without_raw_fields(event):
    helper = SimpleNamespace(event=AsyncMock(return_value=event))
    with pytest.raises(DomainError) as failed:
        await root_lifecycle(helper, deadline=123)
    assert failed.value.failure.code == "dependency_protocol_invalid"
    assert "private" not in failed.value.failure.message


@pytest.mark.parametrize(
    "content",
    [
        "x" * 1025,
        "not json",
        json.dumps(
            {
                "phase": "native_select",
                "error_type": "ValueError",
                "failure_code": "bad",
                "path": "private",
            }
        ),
        json.dumps(
            {"phase": "native_select", "error_type": "private\ntext", "failure_code": "bad"}
        ),
    ],
)
def test_diagnostic_rejects_unbounded_or_extra_content(tmp_path, content):
    path = tmp_path / "diagnostic.json"
    path.write_text(content)
    assert root_diagnostic(path) is None
