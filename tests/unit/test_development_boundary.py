import pytest
from pydantic import SecretStr, ValidationError

from uaw.shared.settings import Settings


def test_admin_token_and_cursor_key_cannot_be_user_token():
    with pytest.raises(ValidationError):
        Settings(
            profile="development",
            development_principal_id="u1",
            development_user_token=SecretStr("u" * 40),
            cursor_signing_key=SecretStr("u" * 40),
        )
    with pytest.raises(ValidationError):
        Settings(
            profile="development",
            development_principal_id="u1",
            development_admin_id="uaw-platform",
            platform_id="uaw-platform",
        )
