"""Shared mechanics for explicitly bound pure-parameter local tools."""

import math
import time
from collections.abc import Callable

from uaw.shared.contracts import JsonObject, Principal, Ref, TrustedExecutionContext
from uaw.tool.errors import fail, validate_dependency
from uaw.tool.receipt_store import ToolResponseStore
from uaw.tool.schema import canonical, digest

SpecFactory = Callable[[Ref], JsonObject]
Calculation = Callable[[JsonObject], JsonObject]


def local_spec(
    tool_id: str,
    description: str,
    category: str,
    provider_ref: Ref,
    inputs: JsonObject,
    outputs: JsonObject,
) -> JsonObject:
    return {
        "id": tool_id,
        "version": "1",
        "description": description,
        "input_schema": inputs,
        "output_schema": outputs,
        "categories": [category],
        "required_capabilities": ["tool.invoke"],
        "effect": "read",
        "provider_ref": provider_ref.wire(),
        "retry_policy_ref": {"kind": "policy", "id": "no-automatic-retry", "version": "1"},
    }


def local_estimates(currency: str = "USD") -> JsonObject:
    """Fixed free local tariff, independent of model charges."""
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "model_calls": 0,
        "tool_calls": 1,
        "child_agents": 0,
        "wall_time_ms": 1000,
        "money": "0.00",
        "currency": currency,
    }


def check_binding(
    call: JsonObject, spec: JsonObject, provider_ref: Ref, factory: SpecFactory
) -> JsonObject:
    validate_dependency("ValidatedCall", call, "local_adapter")
    expected = factory(provider_ref)
    if canonical(spec) != canonical(expected) or call["tool_ref"] != {
        "kind": "configuration",
        "id": expected["id"],
        "version": expected["version"],
        "content_hash": digest(expected),
    }:
        raise fail(
            "executor_binding_conflict",
            "Exact local tool/provider version required",
            phase="local_adapter",
            category="conflict",
            status=409,
        )
    args = call["arguments"]
    if type(args) is not dict or call["arguments_hash"] != digest(args):
        raise ValueError("Arguments differ from the fixed call")
    return args


class LocalExecutor:
    def __init__(
        self,
        source: ToolResponseStore,
        *,
        provider: Principal,
        factory: SpecFactory,
        calculate: Calculation,
        currency: str = "USD",
    ) -> None:
        source.authenticate(provider)
        self.source, self.provider, self.currency = source, provider, currency
        self.factory, self.calculate = factory, calculate

    def check(self, call: JsonObject, spec: JsonObject) -> None:
        self.calculate(check_binding(call, spec, self.source.provider_ref, self.factory))

    async def execute(
        self, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> JsonObject:
        self.check(call, spec)
        await self.source.binding(ctx)
        started = time.perf_counter_ns()
        data = self.calculate(check_binding(call, spec, self.source.provider_ref, self.factory))
        elapsed = math.ceil((time.perf_counter_ns() - started) / 1_000_000)
        usage: JsonObject = {
            "attempt_id": ctx.attempt_id,
            "billing_state": "confirmed",
            "resources": {**local_estimates(self.currency), "wall_time_ms": elapsed},
        }
        return await self.source.save_response(
            data, usage, ctx, authenticated_provider=self.provider
        )


class LocalVerifier:
    def __init__(self, provider_ref: Ref, *, factory: SpecFactory, calculate: Calculation) -> None:
        self.provider_ref, self.factory, self.calculate = provider_ref, factory, calculate

    async def verify(
        self, data: JsonObject, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> None:
        args = check_binding(call, spec, self.provider_ref, self.factory)
        if canonical(data) != canonical(self.calculate(args)):
            raise fail(
                "tool_output_invalid",
                "Stored output differs from actual local calculation",
                phase="normalize_result",
                category="conflict",
                status=409,
            )
