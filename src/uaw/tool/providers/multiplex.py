"""Finite trusted adapter routing, pinned to complete ToolRef and provider versions."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from uaw.shared.contracts import JsonObject, Ref, TrustedExecutionContext
from uaw.shared.schema import validate_contract
from uaw.tool.errors import fail, validate_dependency
from uaw.tool.ports import ToolExecutorPort, ToolOutputVerifierPort
from uaw.tool.schema import canonical, compile_schema, digest

MAX_BINDINGS = 128


@dataclass(frozen=True)
class ToolExecutorBinding:
    tool_ref: Ref
    provider_ref: Ref
    executor: ToolExecutorPort
    prepare: Callable[[JsonObject, JsonObject], None]


@dataclass(frozen=True)
class ToolOutputVerifierBinding:
    tool_ref: Ref
    provider_ref: Ref
    verifier: ToolOutputVerifierPort


def _pins(tool: Ref, provider: Ref) -> tuple[bytes, bytes]:
    validate_contract("Ref", tool.wire())
    validate_contract("Ref", provider.wire())
    if (
        tool.kind != "configuration"
        or tool.content_hash is None
        or tool.location is not None
        or tool.access_scope is not None
        or provider.kind != "provider"
        or provider.location is not None
        or provider.access_scope is not None
    ):
        raise ValueError("Router requires complete fixed tool hash and exact provider Ref")
    return canonical(tool.wire()), canonical(provider.wire())


class _Routes:
    def __init__(
        self, bindings: tuple[ToolExecutorBinding, ...] | tuple[ToolOutputVerifierBinding, ...]
    ) -> None:
        if type(bindings) is not tuple or not 1 <= len(bindings) <= MAX_BINDINGS:
            raise ValueError("Expected an explicit bounded tuple of trusted adapter bindings")
        self._routes: dict[bytes, tuple[bytes, object]] = {}
        versions = set()
        for binding in bindings:
            tool, provider = _pins(binding.tool_ref, binding.provider_ref)
            version = (binding.tool_ref.id, binding.tool_ref.version)
            if version in versions:
                raise ValueError("Duplicate tool version binding, including conflicting hashes")
            versions.add(version)
            self._routes[tool] = (provider, binding)

    def _select(self, call: JsonObject, spec: JsonObject) -> object:
        validate_dependency("ValidatedCall", call, "adapter_route")
        validate_dependency("ToolSpec", spec, "adapter_route")
        tool = {
            "kind": "configuration",
            "id": spec["id"],
            "version": spec["version"],
            "content_hash": digest(spec),
        }
        selected = self._routes.get(canonical(call["tool_ref"]))
        if (
            call["tool_ref"] != tool
            or selected is None
            or selected[0] != canonical(spec["provider_ref"])
        ):
            raise fail(
                "executor_binding_conflict",
                "No exact trusted tool/provider adapter binding",
                phase="adapter_route",
                category="conflict",
                status=409,
            )
        if call["arguments_hash"] != digest(call["arguments"]):
            raise ValueError("Fixed arguments hash differs")
        if not compile_schema(cast(JsonObject, spec["input_schema"]), arguments=True).is_valid(
            call["arguments"]
        ):
            raise ValueError("Arguments violate the exact routed input schema")
        return selected[1]


class ToolExecutorRouter(_Routes):
    def __init__(self, bindings: tuple[ToolExecutorBinding, ...]) -> None:
        if type(bindings) is not tuple or not 1 <= len(bindings) <= MAX_BINDINGS:
            raise ValueError("Trusted bindings must be a bounded tuple")
        if any(
            not isinstance(binding, ToolExecutorBinding)
            or not callable(binding.prepare)
            or not callable(getattr(binding.executor, "execute", None))
            for binding in bindings
        ):
            raise ValueError("Explicit executor and synchronous prepare are required")
        super().__init__(bindings)

    def check(self, call: JsonObject, spec: JsonObject) -> None:
        selected = self._select(call, spec)
        assert isinstance(selected, ToolExecutorBinding)
        selected.prepare(call, spec)

    async def execute(
        self, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> JsonObject:
        selected = self._select(call, spec)
        assert isinstance(selected, ToolExecutorBinding)
        selected.prepare(call, spec)
        receipt = await selected.executor.execute(call, spec, ctx)
        validate_dependency("ProviderReceipt", receipt, "adapter_route")
        if (
            receipt["attempt_id"] != ctx.attempt_id
            or cast(JsonObject, receipt.get("usage", {})).get("attempt_id") != ctx.attempt_id
        ):
            raise fail(
                "receipt_binding_conflict",
                "Provider receipt belongs to another attempt",
                phase="adapter_route",
                category="conflict",
                status=409,
            )
        return receipt


class ToolOutputVerifierRouter(_Routes):
    def __init__(self, bindings: tuple[ToolOutputVerifierBinding, ...]) -> None:
        if type(bindings) is not tuple or not 1 <= len(bindings) <= MAX_BINDINGS:
            raise ValueError("Trusted bindings must be a bounded tuple")
        if any(
            not isinstance(binding, ToolOutputVerifierBinding)
            or not callable(getattr(binding.verifier, "verify", None))
            for binding in bindings
        ):
            raise ValueError("Explicit result verifier is required")
        super().__init__(bindings)

    async def verify(
        self, data: JsonObject, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> None:
        selected = self._select(call, spec)
        assert isinstance(selected, ToolOutputVerifierBinding)
        if not compile_schema(cast(JsonObject, spec["output_schema"])).is_valid(data):
            raise fail(
                "tool_output_invalid",
                "Routed output violates the exact output schema",
                phase="normalize_result",
                category="conflict",
                status=409,
            )
        await selected.verifier.verify(data, call, spec, ctx)
