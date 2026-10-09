"""Actual verifier routing and controlled executor receipt; no provider dispatch claim."""

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import pytest

from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.tool.invocation.schema import normalize
from uaw.tool.parameter_sources import PureParameterRecoveryAccess, PureParameterResourceReader
from uaw.tool.providers.arithmetic import ArithmeticVerifier, arithmetic_spec, calculate
from uaw.tool.providers.json_data import JsonDataVerifier, inspect_json, json_data_spec
from uaw.tool.providers.multiplex import (
    ToolExecutorBinding,
    ToolExecutorRouter,
    ToolOutputVerifierBinding,
    ToolOutputVerifierRouter,
)
from uaw.tool.providers.text import TextInspectVerifier, inspect_text, text_spec
from uaw.tool.registry import AdapterBinding, ToolRegistry

PROVIDER = Ref(kind="provider", id="fixture-provider", version="1")


def office_registry():
    registry = ToolRegistry()
    calls = []
    factories = [arithmetic_spec, json_data_spec, text_spec]
    arguments = [
        {"operation": "add", "operands": ["0.1", "0.2"]},
        {"text": '{"a":1}'},
        {"text": " keep 原 text "},
    ]
    verifiers = [
        ArithmeticVerifier(PROVIDER),
        JsonDataVerifier(PROVIDER),
        TextInspectVerifier(PROVIDER),
    ]
    data = [calculate(arguments[0]), inspect_json(arguments[1]), inspect_text(arguments[2]["text"])]
    bindings = []
    for factory, args, verifier in zip(factories, arguments, verifiers, strict=True):
        spec = factory(PROVIDER)
        registry.register(
            spec,
            expected_revision=registry.revision,
            binding=AdapterBinding(PROVIDER, frozenset({"component-test"}), implemented=True),
        )
        pin = Ref.model_validate(registry.reference(registry.snapshot()[1][-1]))
        call = normalize(
            {"tool_ref": pin.wire(), "action_id": spec["id"], "arguments": args}, registry
        )
        calls.append((call, spec))
        bindings.append(ToolOutputVerifierBinding(pin, PROVIDER, verifier))
    return registry, calls, tuple(bindings), data


async def test_actual_three_verifiers_only_accept_their_bound_tool(ctx):
    registry, calls, bindings, data = office_registry()
    router = ToolOutputVerifierRouter(bindings)
    for (call, spec), output in zip(calls, data, strict=True):
        await router.verify(output, call, spec, ctx)
        for other in data:
            if other != output:
                with pytest.raises(DomainError):
                    await router.verify(other, call, spec, ctx)
    assert registry.revision == 3


@pytest.mark.parametrize(
    "field,value",
    [("version", "2"), ("content_hash", "0" * 64), ("id", "unknown"), ("kind", "content")],
)
async def test_router_rejects_unknown_or_modified_tool_ref(ctx, field, value):
    _, calls, bindings, data = office_registry()
    call, spec = calls[0]
    bad = deepcopy(call)
    bad["tool_ref"][field] = value
    with pytest.raises(DomainError):
        await ToolOutputVerifierRouter(bindings).verify(data[0], bad, spec, ctx)


async def test_provider_and_spec_change_cannot_use_existing_route(ctx):
    _, calls, bindings, data = office_registry()
    call, spec = calls[0]
    bad = {**spec, "provider_ref": {**spec["provider_ref"], "version": "2"}}
    with pytest.raises(DomainError):
        await ToolOutputVerifierRouter(bindings).verify(data[0], call, bad, ctx)
    other = Ref(kind="provider", id="foreign-provider", version="1")
    wrong = (replace(bindings[0], provider_ref=other),)
    with pytest.raises(DomainError):
        await ToolOutputVerifierRouter(wrong).verify(data[0], call, spec, ctx)
    # The real verifier independently rejects a misleading composition binding.
    wrong_impl = (replace(bindings[0], verifier=ArithmeticVerifier(other)),)
    with pytest.raises(DomainError):
        await ToolOutputVerifierRouter(wrong_impl).verify(data[0], call, spec, ctx)


@pytest.mark.parametrize("conflicting_hash", [False, True])
def test_duplicate_version_bindings_rejected_even_with_different_hash(conflicting_hash):
    _, _, bindings, _ = office_registry()
    second = (
        replace(
            bindings[0], tool_ref=bindings[0].tool_ref.model_copy(update={"content_hash": "0" * 64})
        )
        if conflicting_hash
        else bindings[0]
    )
    with pytest.raises(ValueError):
        ToolOutputVerifierRouter((bindings[0], second))


@pytest.mark.parametrize("missing", ["hash", "wrong_kind", "empty", "list", "many"])
def test_trusted_router_requires_bounded_complete_pins(missing):
    _, _, bindings, _ = office_registry()
    pin = bindings[0].tool_ref
    bad = {
        "hash": pin.model_copy(update={"content_hash": None}),
        "wrong_kind": pin.model_copy(update={"kind": "content"}),
    }
    value = (
        ()
        if missing == "empty"
        else list(bindings)
        if missing == "list"
        else (
            bindings * 43 if missing == "many" else (replace(bindings[0], tool_ref=bad[missing]),)
        )
    )
    with pytest.raises(ValueError):
        ToolOutputVerifierRouter(value)


class ControlledExecutor:
    def __init__(self):
        self.calls = 0
        self.prepared = 0

    def check(self, call, spec):
        self.prepared += 1
        calculate(call["arguments"])

    async def execute(self, call, spec, ctx):
        self.calls += 1
        return {
            "attempt_id": ctx.attempt_id,
            "effect_state": "unknown",
            "transport_status": "controlled_unit_receipt",
            "usage": {
                "attempt_id": ctx.attempt_id,
                "billing_state": "pending",
                "resources": {"currency": "USD"},
            },
            "raw_result_ref": {"kind": "content", "id": "controlled-receipt", "version": "1"},
        }


async def test_routed_executor_is_exact_and_receipt_does_not_claim_success(ctx):
    _, calls, bindings, _ = office_registry()
    executor = ControlledExecutor()
    router = ToolExecutorRouter(
        (ToolExecutorBinding(bindings[0].tool_ref, PROVIDER, executor, executor.check),)
    )
    router.check(*calls[0])
    receipt = await router.execute(*calls[0], ctx)
    assert receipt["effect_state"] == "unknown" and executor.calls == 1
    for call, spec in calls[1:]:
        with pytest.raises(DomainError):
            await router.execute(call, spec, ctx)
    assert executor.calls == 1 and executor.prepared == 2
    router_missing = ToolExecutorBinding(bindings[0].tool_ref, PROVIDER, executor, None)
    with pytest.raises(ValueError):
        ToolExecutorRouter((router_missing,))


@pytest.mark.parametrize("tamper", ["attempt", "usage", "schema"])
async def test_routed_receipt_requires_strict_original_attempt(ctx, tamper):
    _, calls, bindings, _ = office_registry()
    executor = ControlledExecutor()
    original = executor.execute

    async def wrong(call, spec, ctx):
        receipt = await original(call, spec, ctx)
        if tamper == "schema":
            return {"ok": True}
        if tamper == "usage":
            receipt["usage"]["attempt_id"] = "foreign-attempt"
        else:
            receipt["attempt_id"] = "foreign-attempt"
        return receipt

    executor.execute = wrong
    router = ToolExecutorRouter(
        (ToolExecutorBinding(bindings[0].tool_ref, PROVIDER, executor, executor.check),)
    )
    with pytest.raises(DomainError):
        await router.execute(*calls[0], ctx)


async def test_pure_parameter_resource_reader_requires_current_access(ctx, access):
    registry, calls, bindings, _ = office_registry()
    ctx = ctx.model_copy(
        update={"scope": ctx.scope.model_copy(update={"capabilities": ("tool.invoke",)})}
    )
    access.value = replace(
        access.value,
        scope=ctx.scope,
        allowed_capabilities=frozenset({"tool.invoke"}),
        role_categories=frozenset({"arithmetic", "data", "text"}),
    )
    reader = PureParameterResourceReader(registry, access, tuple(b.tool_ref for b in bindings))
    for call, spec in calls:
        assert await reader.resolve(call, spec, ctx) == ()
    access.changes = {"cancelled": True}
    with pytest.raises(DomainError):
        await reader.resolve(*calls[0], ctx)
    missing = PureParameterResourceReader(registry, None, (bindings[0].tool_ref,))
    with pytest.raises(DomainError):
        await missing.resolve(*calls[0], ctx)


async def test_recovery_adapter_has_no_implicit_authority_and_never_uses_execute_access(ctx):
    registry, calls, bindings, _ = office_registry()
    reader = PureParameterResourceReader(registry, None, tuple(b.tool_ref for b in bindings))
    call, spec = calls[0]

    class ControlledLedger:
        async def action(self, action, context):
            assert context == ctx
            return call, spec, ctx

        async def attempt(self, context):
            assert context == ctx
            return call

    ledger = ControlledLedger()
    recovery = PureParameterRecoveryAccess(reader, ledger)
    with pytest.raises(DomainError):
        await recovery.check(call, spec, ctx, provider=ctx.principal)
    checked = []

    async def check(call, spec, context, *, provider):
        checked.append((context, provider))

    recovery.authority = SimpleNamespace(check=check)
    await recovery.check(call, spec, ctx, provider=ctx.principal)
    assert checked == [(ctx, ctx.principal)]
