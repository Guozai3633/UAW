"""Private control-plane ports. No credential read operation is exposed as an Agent tool."""

from typing import Protocol

from pydantic import SecretStr


class CredentialStorePort(Protocol):
    async def put(self, handle: str, secret: SecretStr) -> None: ...
    async def resolve(self, handle: str) -> SecretStr: ...
    async def delete(self, handle: str) -> None: ...
