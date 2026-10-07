"""Provision only UAW's development tokens in Windows Credential Manager; print no values."""

import asyncio
import secrets

from pydantic import SecretStr

from uaw.infrastructure.credentials import WindowsCredentialStore
from uaw.shared.errors import DomainError


async def provision() -> None:
    store = WindowsCredentialStore("uaw-platform")
    for handle in ("development-user-token", "development-admin-token", "cursor-signing-key"):
        try:
            await store.resolve(handle)
        except DomainError as exc:
            if exc.failure.code != "credential_missing":
                raise
            await store.put(handle, SecretStr(secrets.token_urlsafe(48)))
    print("Development user/admin tokens and cursor key ready in Windows Credential Manager.")


if __name__ == "__main__":
    asyncio.run(provision())
