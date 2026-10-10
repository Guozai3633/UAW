"""Browser opt-in cannot weaken the existing credential boundary."""

import pytest
from pydantic import SecretStr, ValidationError

from uaw.shared.settings import Settings


def values():
    return dict(
        profile="development",
        development_principal_id="user",
        development_user_token=SecretStr("u" * 40),
        cursor_signing_key=SecretStr("c" * 40),
        browser_session_signing_key=SecretStr("b" * 40),
        browser_origin="http://127.0.0.1:5173",
    )


@pytest.mark.parametrize(
    "origin",
    [
        "https://127.0.0.1:5173",
        "http://localhost:5173",
        "http://0.0.0.0:5173",
        "http://127.0.0.1:5173/",
        "http://127.0.0.1:5173?x=1",
        "http://user@127.0.0.1:5173",
        "http://127.0.0.1",
        "http://127.0.0.1:80",
        "http://127.0.0.1:5173#x",
        "http://127.0.0.1:wrong",
    ],
)
def test_only_precise_loopback_origin(origin):
    with pytest.raises(ValidationError):
        Settings(**{**values(), "browser_origin": origin})


@pytest.mark.parametrize(
    "field", ["browser_session_signing_key", "browser_origin", "development_user_token"]
)
def test_browser_identity_and_independent_key_required(field):
    with pytest.raises(ValidationError):
        Settings(**{**values(), field: None})


def test_web_key_cannot_share_auth_or_cursor_secret():
    with pytest.raises(ValidationError):
        Settings(**{**values(), "browser_session_signing_key": SecretStr("c" * 40)})
    assert Settings(**values()).browser_session_seconds == 3600
