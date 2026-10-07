"""MS-C1 component entry points. Build/persistence await A's MS-I1 wiring."""

from collections.abc import Mapping
from typing import Any

from uaw.context.ports import (
    Cancellation,
    ModelWindowProvider,
    Reader,
    RuleProvider,
    TokenCounter,
)
from uaw.context.rules import RuleResolver
from uaw.context.selection import Selector
from uaw.context.sources import Guard, SourceResolver, component_result
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable
from uaw.shared.schema import validate_contract


class ContextComponents:
    def __init__(
        self,
        *,
        readers: Mapping[str, Reader],
        cancellation: Cancellation | None,
        rules: RuleProvider | None = None,
        models: ModelWindowProvider | None = None,
        counter: TokenCounter | None = None,
    ) -> None:
        self.sources = SourceResolver(readers, Guard(cancellation))
        self.rules = RuleResolver(self.sources, rules)
        self.selection = Selector(self.sources, models, counter)

    async def resolve_sources(
        self, request: dict[str, Any], ctx: TrustedExecutionContext
    ) -> dict[str, Any]:
        return await self.sources.handle(request, ctx)

    async def resolve_rules(
        self, request: dict[str, Any], ctx: TrustedExecutionContext
    ) -> dict[str, Any]:
        return await self.rules.handle(request, ctx)

    async def select(self, request: dict[str, Any], ctx: TrustedExecutionContext) -> dict[str, Any]:
        return await self.selection.handle(request, ctx)

    async def build(self, request: dict[str, Any], ctx: TrustedExecutionContext) -> dict[str, Any]:
        # No fabricated snapshot ref: Composer/storage/capability assembly need MS-I1.
        async def operation() -> dict[str, Any]:
            validate_contract("ContextRequest", request)
            raise CapabilityUnavailable("context.snapshot_composition")

        return await component_result(
            "RuntimeContextruntimeBuildResult", ctx, self.sources.guard, operation
        )
