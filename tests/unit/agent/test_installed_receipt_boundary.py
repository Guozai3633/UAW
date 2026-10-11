"""Progress never substitutes for current permission or original native proof."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import SecretStr, ValidationError

from tests.unit.shared.test_browser_settings import values
from uaw.infrastructure.installed_receipt import complete_marker, current_root
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import DomainError, reject
from uaw.shared.settings import Settings


@pytest.mark.parametrize(
    "raw",
    [
        b"x" * 4097,
        b"{}",
        b'{"ticket_hash":"a","ticket_hash":"b"}',
        b'{"workspace_ref":{},"channel_ref":{},"ticket_hash":"a","approved":true}',
    ],
)
def test_progress_rejects_duplicate_extra_unbounded_fields(tmp_path, raw):
    path = tmp_path / "root-selection-complete.json"
    path.write_bytes(raw)
    assert complete_marker(path) is None


async def test_forged_complete_progress_cannot_override_live_role_denial(tmp_path):
    workspace = Ref(kind="workspace", id="test-workspace", version="1")
    channel = Ref(kind="content", id="test-channel", version="1", content_hash="a" * 64)
    session = SimpleNamespace(
        local="saved-role",
        check=AsyncMock(
            side_effect=reject("enrolled_current_key_denied", "Current role was revoked", 403)
        ),
    )
    owner = Principal(id="test-user", kind="user", auth_session_id="web-session-test")
    launch = SimpleNamespace(
        closed=False,
        owner=owner,
        root_workspace=workspace,
        control_key="saved-key",
        state=SimpleNamespace(path=tmp_path / "roles.sqlite"),
        connection=SimpleNamespace(session=session, channel_ref=channel),
    )
    path = tmp_path / "root-selection-complete.json"
    with pytest.raises(DomainError) as pending:
        await current_root(launch)
    assert pending.value.failure.code == "installed_callback_pending"
    session.check.assert_not_awaited()  # No positive result, no duplicated permission polling.
    path.write_text(
        json.dumps(
            {
                "workspace_ref": workspace.wire(),
                "channel_ref": channel.wire(),
                "ticket_hash": "b" * 64,
            }
        )
    )
    with pytest.raises(DomainError) as denied:
        await current_root(launch)
    assert denied.value.failure.code == "enrolled_current_key_denied"
    session.check.assert_awaited_once()
    assert not (tmp_path / "grants.sqlite").exists()  # No fabricated grant or native source.


@pytest.mark.parametrize(
    "changes",
    [
        {"installed_state_directory": Path("relative")},
        {"installed_workspace_id": "workspace"},
        {"installed_state_directory": Path("relative"), "installed_workspace_id": "workspace"},
    ],
)
def test_installed_deployment_is_explicit_and_absolute(changes):
    base = {**values(), "database_url": SecretStr("postgresql+psycopg://placeholder")}
    with pytest.raises(ValidationError):
        Settings(**{**base, **changes})
