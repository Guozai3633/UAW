"""Explicit pure-parameter resource Reader and current recovery authority adapter.

Only the three exact local read specifications are resource-free. No generic
empty Reader or execution snapshot grants recovery data access. A supplies the
independent current Run/owner/model/role/provider authority at composition.
"""

from typing import cast

from uaw.shared.contracts import JsonObject, Principal, Ref, TrustedExecutionContext
from uaw.tool.discovery import check_access, require_entry
from uaw.tool.errors import fail
from uaw.tool.invocation.schema import normalize
from uaw.tool.ledger import ToolLedger
from uaw.tool.ports import ToolAccessPort, ToolRecoveryAccessPort
from uaw.tool.providers.arithmetic import arithmetic_spec, calculate
from uaw.tool.providers.json_data import inspect_json, json_data_spec
from uaw.tool.providers.local import check_binding
from uaw.tool.providers.text import check_text_binding, inspect_text, text_spec
from uaw.tool.registry import RegistryEntry, ToolRegistry
from uaw.tool.schema import canonical


class PureParameterResourceReader:
    def __init__(
        self, registry: ToolRegistry, access: ToolAccessPort | None, tool_refs: tuple[Ref, ...]
    ) -> None:
        if type(tool_refs) is not tuple or not 1 <= len(tool_refs) <= 3:
            raise ValueError("Explicit 1..3 pure local tool versions required")
        pins = tuple(canonical(pin.wire()) for pin in tool_refs)
        if len(set(pins)) != len(pins):
            raise ValueError("Duplicate resource tool binding")
        self.registry, self.access, self._pins = registry, access, pins
        for pin in tool_refs:
            entry = registry.get(pin.wire())
            if canonical(registry.reference(entry)) != canonical(pin.wire()):
                raise ValueError("Complete tool hash required for resource binding")
            self._check(entry.spec(), {}, metadata_only=True)

    @staticmethod
    def _check(spec: JsonObject, call: JsonObject, *, metadata_only: bool = False) -> None:
        provider = Ref.model_validate(spec["provider_ref"])
        tool = spec["id"]
        if tool == "arithmetic.calculate":
            expected = arithmetic_spec(provider)
        elif tool == "data.inspect_json":
            expected = json_data_spec(provider)
        elif tool == "text.inspect":
            expected = text_spec(provider)
        else:
            raise ValueError("No pure-parameter implementation for this tool")
        if canonical(spec) != canonical(expected):
            raise ValueError("Resource Reader only implements exact local versions")
        if not metadata_only:
            if tool == "text.inspect":
                inspect_text(check_text_binding(call, spec, provider))
            elif tool == "arithmetic.calculate":
                calculate(check_binding(call, spec, provider, arithmetic_spec))
            else:
                inspect_json(check_binding(call, spec, provider, json_data_spec))

    def entry(self, call: JsonObject, spec: JsonObject) -> RegistryEntry:
        if canonical(call.get("tool_ref")) not in self._pins:
            raise fail(
                "dependency_unavailable",
                "No resource Reader for this fixed tool",
                phase="authority",
                category="dependency",
                status=503,
            )
        entry = self.registry.get(cast(JsonObject, call["tool_ref"]))
        if (
            entry.spec() != spec
            or normalize({k: v for k, v in call.items() if k != "arguments_hash"}, self.registry)
            != call
        ):
            raise fail(
                "executor_binding_conflict",
                "Resource source differs from fixed call",
                phase="authority",
                category="conflict",
                status=409,
            )
        self._check(spec, call)
        return entry

    async def resolve(
        self, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> tuple[Ref, ...]:
        if self.access is None:
            raise fail(
                "dependency_unavailable",
                "Current Tool access source is not wired",
                phase="authority",
                category="dependency",
                status=503,
            )
        entry = self.entry(call, spec)
        snapshot = await self.access.snapshot(ctx)
        check_access(snapshot, ctx)
        current_entry = self.entry(call, spec)
        if current_entry != entry:
            raise fail(
                "stale_resource",
                "Pure tool binding changed during current access read",
                phase="authority",
                category="conflict",
                status=412,
            )
        require_entry(current_entry, snapshot)
        return ()


class PureParameterRecoveryAccess:
    def __init__(
        self,
        resources: PureParameterResourceReader,
        ledger: ToolLedger,
        *,
        authority: ToolRecoveryAccessPort | None = None,
    ) -> None:
        self.resources, self.ledger, self.authority = resources, ledger, authority

    def ready(self) -> None:
        """Dependency readiness only; never a cached current permission grant."""
        if self.authority is None:
            raise fail(
                "dependency_unavailable",
                "Independent current recovery authority missing",
                phase="recovery_source",
                category="dependency",
                status=503,
            )

    async def check(
        self,
        call: JsonObject,
        spec: JsonObject,
        ctx: TrustedExecutionContext,
        *,
        provider: Principal,
    ) -> None:
        if self.authority is None:
            raise fail(
                "dependency_unavailable",
                "Independent current recovery authority missing",
                phase="recovery_source",
                category="dependency",
                status=503,
            )
        self.resources.entry(call, spec)
        fixed_call, fixed_spec, _ = await self.ledger.action(str(call["action_id"]), ctx)
        if fixed_call != call or fixed_spec != spec or await self.ledger.attempt(ctx) != call:
            raise fail(
                "receipt_binding_conflict",
                "Original registered attempt/action differs",
                phase="recovery_source",
                category="conflict",
                status=409,
            )
        # No access.snapshot/resolve here: cancellation stops execution, not owned data recovery.
        await self.authority.check(call, spec, ctx, provider=provider)
        self.resources.entry(call, spec)
        if await self.ledger.attempt(ctx) != fixed_call or (
            await self.ledger.action(str(call["action_id"]), ctx)
        )[:2] != (fixed_call, fixed_spec):
            raise fail(
                "receipt_binding_conflict",
                "Recovery binding changed during authority check",
                phase="recovery_source",
                category="conflict",
                status=409,
            )
