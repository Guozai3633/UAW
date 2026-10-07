from typing import Protocol

from uaw.model.contracts import ModelPrompt, Payload, ProviderRequest, ProviderResponse
from uaw.shared.contracts import TrustedExecutionContext


class ModelInputPort(Protocol):
    async def resolve(self, ref: Payload, ctx: TrustedExecutionContext) -> ModelPrompt: ...


class ModelProviderPort(Protocol):
    async def generate(self, request: ProviderRequest) -> ProviderResponse: ...

    async def close(self) -> None: ...
