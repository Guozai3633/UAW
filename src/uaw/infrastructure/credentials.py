"""Development backend: explicitly select Windows Credential Manager; never auto-fallback."""

import asyncio
import sys

from keyring.backend import KeyringBackend
from pydantic import SecretStr

from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract


class WindowsCredentialStore:
    def __init__(self, namespace: str) -> None:
        validate_contract("ID", namespace)
        self.namespace = f"UAW-development/{namespace}"

    @staticmethod
    def _backend() -> KeyringBackend:
        if sys.platform != "win32":
            raise CapabilityUnavailable("windows_credential_store")
        # Import directly: keyring configuration / third-party insecure backends are ignored.
        from keyring.backends.Windows import WinVaultKeyring

        return WinVaultKeyring()  # type: ignore[no-untyped-call]

    async def put(self, handle: str, secret: SecretStr) -> None:
        validate_contract("ID", handle)
        try:
            await asyncio.to_thread(
                self._backend().set_password, self.namespace, handle, secret.get_secret_value()
            )
        except Exception:
            raise reject(
                "credential_store_unavailable", "Secure credential write failed", 503, "dependency"
            ) from None

    async def resolve(self, handle: str) -> SecretStr:
        validate_contract("ID", handle)
        try:
            value = await asyncio.to_thread(self._backend().get_password, self.namespace, handle)
        except Exception:
            raise reject(
                "credential_store_unavailable", "Secure credential read failed", 503, "dependency"
            ) from None
        if value is None:
            raise reject(
                "credential_missing", "Credential handle is unavailable", 404, "dependency"
            )
        return SecretStr(value)

    async def delete(self, handle: str) -> None:
        validate_contract("ID", handle)
        await asyncio.to_thread(self._backend().delete_password, self.namespace, handle)
