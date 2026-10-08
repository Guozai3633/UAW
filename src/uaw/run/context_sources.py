"""Current fixed-model and tool-catalogue adapters for registered Context inputs."""

from uaw.context.contracts import ModelToolSet
from uaw.run.context import RunContextSources
from uaw.run.execution_sources import RunExecutionSources
from uaw.run.tool_sources import RunToolAccessSources
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.tool.discovery import check_access, require_entry
from uaw.tool.registry import ToolRegistry
from uaw.tool.schema import digest


class RegisteredRunContextSources(RunContextSources):
    def __init__(self, sources: RunExecutionSources) -> None:
        super().__init__(sources.store, sources.permissions)
        self.current_runs = sources

    async def authorize(self, ctx: TrustedExecutionContext) -> None:
        if not set(ctx.scope.capabilities).intersection(
            {"model.generate", "intent.understand", "context.build"}
        ):
            raise reject("permission_denied", "Current scope denies Context source access", 403)
        # current performs the actual Run/cancellation/deadline and policy checks
        # itself; calling the base gate as well would repeat the same SQL chain.
        await self.current_runs.current(ctx)


class RegisteredToolSetValidator:
    def __init__(self, registry: ToolRegistry | None, access: RunToolAccessSources | None) -> None:
        self.registry, self.access = registry, access

    async def check(self, tools: ModelToolSet, ctx: TrustedExecutionContext) -> None:
        validate_contract("ModelToolSet", tools.wire())
        if tools.run_id != ctx.run_id:
            raise reject("context_tool_scope_denied", "Tools belong to another Run", 403)
        if not tools.tools:
            return
        if self.registry is None or self.access is None:
            raise CapabilityUnavailable("context.registered_tool_validation")
        snapshot = await self.access.snapshot(ctx)
        check_access(snapshot, ctx)
        seen = set()
        for spec in tools.tools:
            pin = {
                "kind": "configuration",
                "id": spec["id"],
                "version": spec["version"],
                "content_hash": digest(spec),
            }
            key = (spec["id"], spec["version"])
            if key in seen:
                raise reject("context_tool_duplicate", "Tool set repeats a fixed tool", 422)
            seen.add(key)
            entry = self.registry.get(pin)
            if entry.spec() != spec:
                raise reject("context_tool_stale", "Tool differs from the actual catalogue", 412)
            require_entry(entry, snapshot)
        # No registration or execution permission is created by this check.
        refreshed = await self.access.snapshot(ctx)
        if refreshed != snapshot:
            raise reject("context_tool_stale", "Current tool authorization changed", 412)
