from typing import Protocol

from uaw.model.contracts import ModelPrompt, Payload, ProviderRequest, ProviderResponse
from uaw.shared.contracts import TrustedExecutionContext


class ModelInputPort(Protocol):
    async def resolve(self, ref: Payload, ctx: TrustedExecutionContext) -> ModelPrompt: ...


class ModelProviderPort(Protocol):
    def estimate_input_tokens(self, request: ProviderRequest) -> int:
        """Conservative count of the complete native request, including schemas/tools."""
        ...

    async def generate(self, request: ProviderRequest) -> ProviderResponse: ...

    async def close(self) -> None: ...
