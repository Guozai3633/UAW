"""Trusted internal streaming hooks; not model/user-facing execution arguments."""

from typing import Protocol

from uaw.model.contracts import ProviderFailure, ProviderRequest, ProviderResponse
from uaw.shared.contracts import TrustedExecutionContext


class ModelStreamConsumer(Protocol):
    async def content(self, delta: str) -> None: ...

    async def finish(
        self, response: ProviderResponse | None, failure: ProviderFailure | None
    ) -> None: ...


class ModelStreamPort(Protocol):
    async def open(
        self, request: ProviderRequest, ctx: TrustedExecutionContext, invocation_id: str
    ) -> ModelStreamConsumer | None: ...
