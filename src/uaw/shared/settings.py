"""Explicit deployment configuration; fail before accepting untrusted requests."""

import os
import tomllib
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

from uaw.shared.contracts import ID


class ConfigurationError(ValueError):
    pass


class Settings(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True, hide_input_in_errors=True)
    profile: Literal["development"]
    host: Literal["127.0.0.1", "::1"] = "127.0.0.1"
    port: int = Field(default=8000, ge=1024, le=65535)
    development_principal_id: ID
    development_admin_id: ID = "development-admin"
    platform_id: ID = "uaw-platform"
    development_user_token: SecretStr | None = None
    development_admin_token: SecretStr | None = None
    cursor_signing_key: SecretStr | None = None
    database_url: SecretStr | None = None
    blob_directory: Path = Path(".data/blobs")
    max_request_bytes: int = Field(default=1_048_576, ge=1024, le=1_048_576)

    @model_validator(mode="after")
    def valid_database(self) -> Self:
        if self.database_url and not self.database_url.get_secret_value().startswith(
            "postgresql+psycopg://"
        ):
            raise ValueError("database_url must use the PostgreSQL psycopg adapter")
        secrets = [
            self.development_user_token,
            self.development_admin_token,
            self.cursor_signing_key,
        ]
        if any(value and len(value.get_secret_value()) < 32 for value in secrets):
            raise ValueError(
                "Development authentication and cursor keys require at least 32 characters"
            )
        if self.development_user_token and not self.cursor_signing_key:
            raise ValueError("Authenticated history requires a persistent cursor signing key")
        if self.development_user_token and self.development_admin_token:
            if self.development_user_token == self.development_admin_token:
                raise ValueError("User and administrator must have different authentication tokens")
        supplied = [value.get_secret_value() for value in secrets if value]
        if len(set(supplied)) != len(supplied):
            raise ValueError("Authentication tokens and cursor signing key must be independent")
        if self.development_principal_id in (self.development_admin_id, self.platform_id):
            raise ValueError("User, administrator and platform identities must be separate")
        if self.development_admin_id == self.platform_id:
            raise ValueError("Administrator and platform identities must be separate")
        return self

    @classmethod
    def from_file(cls, path: Path) -> Self:
        try:
            with path.open("rb") as stream:
                config = tomllib.load(stream)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ConfigurationError("Configuration file is missing or invalid") from exc
        for field in (
            "database_url",
            "development_user_token",
            "development_admin_token",
            "cursor_signing_key",
        ):
            if field in config:
                raise ConfigurationError(f"Use {field}_env instead of a plaintext secret")
            variable = config.pop(f"{field}_env", None)
            handle = config.pop(f"{field}_keyring_handle", None)
            if variable and handle:
                raise ConfigurationError("Choose one credential source per field")
            if handle:
                from uaw.infrastructure.credentials import WindowsCredentialStore

                try:
                    from uaw.shared.schema import validate_contract

                    validate_contract("ID", handle)
                    namespace = WindowsCredentialStore(config.get("platform_id", "uaw-platform"))
                    stored = namespace._backend().get_password(namespace.namespace, handle)
                    if stored is None:
                        raise ValueError
                    config[field] = SecretStr(stored)
                except Exception:
                    raise ConfigurationError(
                        f"Secure development credential missing for {field}"
                    ) from None
            if variable:
                if not isinstance(variable, str):
                    raise ConfigurationError("Secret environment variable names must be strings")
                value = os.environ.get(variable)
                if not value:
                    raise ConfigurationError(
                        f"Required environment variable is missing: {variable}"
                    )
                config[field] = SecretStr(value)
        if "blob_directory" in config:
            directory = Path(config["blob_directory"])
            config["blob_directory"] = directory.resolve()
        try:
            return cls.model_validate(config)
        except ValueError as exc:
            raise ConfigurationError(
                "Invalid deployment fields; check the configuration template"
            ) from exc
