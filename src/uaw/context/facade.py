"""Context component entry points. General build requires explicit storage and authority."""

from collections.abc import Mapping
from typing import Any

from uaw.context.composer import Composer
from uaw.context.contracts import ContextRequest, digest, from_wire
from uaw.context.ports import (
    Cancellation,
    CompositionAuthority,
    ModelWindowProvider,
    Reader,
    RuleProvider,
    TokenCounter,
)
from uaw.context.references import References
from uaw.context.repository import ContextRepository
from uaw.context.rules import RuleResolver
from uaw.context.selection import Selector
from uaw.context.sources import Guard, SourceResolver, component_result
from uaw.shared.contracts import Ref, TrustedExecutionContext
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
        repository: ContextRepository | None = None,
        authority: CompositionAuthority | None = None,
    ) -> None:
        self.sources = SourceResolver(readers, Guard(cancellation))
        self.rules = RuleResolver(self.sources, rules)
        self.selection = Selector(self.sources, models, counter)
        self.composer = (
            Composer(self.sources, self.rules, self.selection, repository, authority)
            if repository is not None and authority is not None
            else None
        )
        self.references = References(self.sources, repository) if repository is not None else None

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
        async def operation() -> dict[str, Any]:
            validate_contract("ContextRequest", request)
            if self.composer is None:
                raise CapabilityUnavailable("context.snapshot_composition")
            snapshot = await self.composer.build(from_wire(ContextRequest, request), ctx)
            return {
                "kind": "ok",
                "payload": snapshot,
                "output_refs": [
                    {
                        "kind": "context",
                        "id": snapshot["id"],
                        "version": "1",
                        "content_hash": digest(snapshot),
                    }
                ],
                "revision": 1,
            }

        return await component_result(
            "RuntimeContextruntimeBuildResult", ctx, self.sources.guard, operation
        )

    async def resolve_reference(
        self, request: dict[str, Any], ctx: TrustedExecutionContext
    ) -> dict[str, Any]:
        if self.references is not None:
            return await self.references.resolve_runtime(request, ctx)

        async def operation() -> dict[str, Any]:
            validate_contract("RefRequest", request)
            raise CapabilityUnavailable("context.reference_repository")

        return await component_result(
            "RuntimeContextruntimeResolveReferenceResult", ctx, self.sources.guard, operation
        )

    async def read_snapshot(self, ref: Ref, ctx: TrustedExecutionContext) -> dict[str, Any]:
        async def operation() -> dict[str, Any]:
            if self.composer is None:
                raise CapabilityUnavailable("context.snapshot_composition")
            snapshot = await self.composer.repository.load_snapshot(ref, ctx)
            await self.composer.recheck(snapshot, ctx)
            return {"kind": "ok", "payload": snapshot, "output_refs": [ref.wire()], "revision": 1}

        return await component_result(
            "RuntimeContextruntimeBuildResult", ctx, self.sources.guard, operation
        )
