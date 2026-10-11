"""Controlled routing doubles prove delegation only; no execution or real authority."""

import asyncio
from dataclasses import replace
from types import SimpleNamespace

import pytest

from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError, error_result
from uaw.tool.errors import fail
from uaw.tool.facade import ToolFacade
from uaw.tool.invocation.schema import normalize
from uaw.tool.registry import AdapterBinding
from uaw.tool.runtime_router import RoutedToolRuntime, ToolRuntimeRoute


class ControlledLedger:
    def __init__(self, call, spec, ctx):
        self.store = object()
        self.call, self.spec, self.ctx = call, spec, ctx
        self.reads = 0

    async def attempt(self, ctx):
        self.reads += 1
        if ctx != self.ctx:
            raise fail("action_conflict", "Controlled original attempt differs", phase="identity")
        return self.call.copy()

    async def action(self, action_id, ctx):
        if action_id != self.call["action_id"]:
            raise fail("action_conflict", "Controlled original action differs", phase="identity")
        return self.call.copy(), self.spec.copy(), self.ctx


class ControlledFacade(ToolFacade):
    async def invoke(self, request, ctx):
        self.seen = (request, ctx)
        if getattr(self, "entered", None):
            self.entered.set()
            await self.release.wait()
        return error_result(
            fail("controlled_delegate", "Original facade reached", phase="dispatch")
        )

    async def reconcile(self, request, ctx):
        self.seen = (request, ctx)
        return error_result(
            fail("controlled_recovery", "Original reconciler reached", phase="reconcile")
        )

    async def read_outcome(self, action_id, ctx):
        self.seen = (action_id, ctx)
        raise fail("controlled_reader", "Original owning outcome Reader reached", phase="receipt")


class ControlledResults:
    async def read_result(self, action_id, ctx):
        self.seen = (action_id, ctx)
        return error_result(
            fail("controlled_reader", "Original result Reader reached", phase="receipt")
        )


@pytest.fixture
def routing(registry, spec, call, ctx, access):
    ledger = ControlledLedger(normalize(call, registry), spec, ctx)
    invocation = SimpleNamespace(registry=registry, ledger=ledger, access=access)
    facade = ControlledFacade(registry, invocation=invocation)
    results = ControlledResults()
    route = ToolRuntimeRoute(
        Ref.model_validate(call["tool_ref"]),
        Ref.model_validate(spec["provider_ref"]),
        facade,
        results,
    )
    router = RoutedToolRuntime(registry, ledger, (route,), access=access)
    return SimpleNamespace(
        router=router,
        route=route,
        ledger=ledger,
        facade=facade,
        results=results,
        registry=registry,
        access=access,
    )


@pytest.mark.parametrize("routes", [(), [], tuple(None for _ in range(129)), (None,)])
def test_explicit_bounded_routes(routing, routes):
    with pytest.raises(ValueError):
        RoutedToolRuntime(routing.registry, routing.ledger, routes, access=routing.access)


@pytest.mark.parametrize(
    "change", ["missing_hash", "wrong_hash", "wrong_provider", "location", "duplicate"]
)
def test_fixed_pins_reject(routing, change):
    r = routing.route
    if change == "missing_hash":
        r = replace(
            r, tool_ref=Ref(kind="configuration", id=r.tool_ref.id, version=r.tool_ref.version)
        )
    elif change == "wrong_hash":
        r = replace(r, tool_ref=r.tool_ref.model_copy(update={"content_hash": "0" * 64}))
    elif change == "wrong_provider":
        r = replace(r, provider_ref=r.provider_ref.model_copy(update={"version": "other"}))
    elif change == "location":
        r = replace(r, provider_ref=Ref(**r.provider_ref.wire(), location={"kind": "whole"}))
    with pytest.raises(ValueError):
        RoutedToolRuntime(
            routing.registry,
            routing.ledger,
            (r, r) if change == "duplicate" else (r,),
            access=routing.access,
        )


@pytest.mark.parametrize("change", ["registry", "store", "access", "invocation", "results"])
def test_same_original_registry_store_and_agent_access_required(routing, change):
    p = routing
    if change == "registry":
        p.facade.registry = object()
    elif change == "store":
        p.facade.invocation.ledger = SimpleNamespace(store=object())
    elif change == "access":
        p.facade.invocation.access = SimpleNamespace(snapshot=p.access.snapshot)
    elif change == "invocation":
        p.facade.invocation = None
    else:
        p.route = replace(p.route, results=object())
    with pytest.raises(ValueError):
        RoutedToolRuntime(p.registry, p.ledger, (p.route,), access=p.access)


async def test_discover_unbound_tools_do_not_crowd_bound_selection(routing, spec, ctx):
    p = routing
    unbound = {**spec, "id": "aaa.unbound"}
    p.registry.register(
        unbound,
        expected_revision=p.registry.revision,
        binding=AdapterBinding(
            p.route.provider_ref, frozenset({"component-test"}), implemented=True
        ),
    )
    result = await p.router.discover({"query": "content", "max_candidates": 1}, ctx)
    assert [r["tool_ref"] for r in result["payload"]["tools"]] == [p.route.tool_ref.wire()]
    assert p.ledger.reads == 0 and not hasattr(p.facade, "seen")


@pytest.mark.parametrize("change", ["cancelled", "role", "provider", "environment"])
async def test_discover_current_access_filter(routing, ctx, change):
    p = routing
    p.access.changes = {
        "cancelled": {"cancelled": True},
        "role": {"role_categories": frozenset()},
        "provider": {"active_provider_refs": ()},
        "environment": {"environment": "unavailable"},
    }[change]
    result = await p.router.discover({"query": "content", "max_candidates": 5}, ctx)
    assert result["kind"] != "ok"


async def test_invoke_original_request_frozen_and_same_context(routing, call, ctx):
    p = routing
    p.facade.entered, p.facade.release = asyncio.Event(), asyncio.Event()
    before = call["arguments"]["text"]
    pending = asyncio.create_task(p.router.invoke(call, ctx))
    await p.facade.entered.wait()
    call["arguments"]["text"] = "caller mutation"
    p.facade.release.set()
    result = await pending
    assert result["failure"]["code"] == "controlled_delegate"
    assert p.facade.seen[0]["arguments"]["text"] == before and p.facade.seen[1] is ctx
    assert "arguments_hash" not in p.facade.seen[0] and p.ledger.reads == 0


async def test_changed_agent_access_cannot_be_replaced_after_construction(routing, call, ctx):
    p = routing
    p.facade.invocation.access = SimpleNamespace(snapshot=p.access.snapshot)
    result = await p.router.invoke(call, ctx)
    assert result["failure"]["code"] == "runtime_binding_conflict"
    assert not hasattr(p.facade, "seen")


async def test_original_recovery_does_not_snapshot_execution_access(routing, call, ctx):
    p = routing
    p.access.changes = {"cancelled": True, "role_categories": frozenset()}
    result = await p.router.reconcile({"action_id": call["action_id"], "expected_revision": 1}, ctx)
    assert result["failure"]["code"] == "controlled_recovery"
    assert (await p.router.read_result(call["action_id"], ctx))["failure"][
        "code"
    ] == "controlled_reader"
    with pytest.raises(DomainError, match="Original owning outcome"):
        await p.router.read_outcome(call["action_id"], ctx)
    assert p.access.calls == 0 and p.facade.seen == (call["action_id"], ctx)


@pytest.mark.parametrize("change", ["attempt", "session", "provider", "spec", "unregister"])
async def test_recovery_rejects_changed_original_binding(routing, call, ctx, change):
    p = routing
    if change == "attempt":
        ctx = ctx.model_copy(update={"attempt_id": "other"})
    elif change == "session":
        ctx = ctx.model_copy(
            update={"principal": ctx.principal.model_copy(update={"auth_session_id": "other"})}
        )
    elif change == "provider":
        p.ledger.spec = {
            **p.ledger.spec,
            "provider_ref": {**p.ledger.spec["provider_ref"], "version": "other"},
        }
    elif change == "spec":
        p.ledger.spec = {**p.ledger.spec, "description": "modified"}
    else:
        p.registry.unregister(p.route.tool_ref.wire(), expected_revision=p.registry.revision)
    result = await p.router.reconcile({"action_id": call["action_id"], "expected_revision": 1}, ctx)
    assert result["kind"] != "ok" and not hasattr(p.facade, "seen")
    with pytest.raises(DomainError):
        await p.router.read_result(call["action_id"], ctx)


async def test_reconcile_extra_receipt_ref_rejected_before_ledger(routing, call, ctx):
    result = await routing.router.reconcile(
        {"action_id": call["action_id"], "expected_revision": 1, "receipt_ref": call["tool_ref"]},
        ctx,
    )
    assert result["failure"]["code"] == "invalid_arguments" and routing.ledger.reads == 0
