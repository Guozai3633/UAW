"""Effective Agent access cloning must preserve independent original gates and Readers."""

from types import SimpleNamespace

import pytest

from uaw.agent.assembly import bind_agent_tool_facade
from uaw.shared.contracts import Ref
from uaw.shared.settings import ConfigurationError
from uaw.tool.facade import ToolFacade
from uaw.tool.invocation.dispatch import ToolInvocation
from uaw.tool.providers.text import text_spec
from uaw.tool.registry import AdapterBinding, ToolRegistry
from uaw.tool.runtime_router import RoutedToolRuntime, ToolRuntimeRoute


def test_mixed_routes_keep_original_permissions_and_result_readers():
    registry = ToolRegistry()
    provider = Ref(kind="provider", id="original-provider", version="1")
    spec = text_spec(provider)
    registry.register(
        spec,
        expected_revision=0,
        binding=AdapterBinding(provider, frozenset({"development"}), implemented=True),
    )
    tool = Ref.model_validate(registry.reference(registry.snapshot()[1][0]))
    store = object()
    ledger = SimpleNamespace(store=store)
    original_access = object()
    original = ToolInvocation(
        registry,
        ledger,
        object(),
        object(),
        access=original_access,
        executor=object(),
        results=object(),
        prepare=lambda a, b: None,
    )
    facade = ToolFacade(registry, invocation=original)

    async def snapshot(ctx):
        raise AssertionError("Construction never acquires or grants execution permissions")

    async def read_result(action, ctx):
        raise AssertionError("Construction never reads a result body")

    agent_access = SimpleNamespace(snapshot=snapshot)
    bound = bind_agent_tool_facade(facade, registry, agent_access)
    assert original.access is original_access and bound.invocation is not original
    assert bound.invocation.access is agent_access
    for name in ("ledger", "budgets", "approvals", "executor", "results", "prepare"):
        assert getattr(bound.invocation, name) is getattr(original, name)
    reader = SimpleNamespace(read_result=read_result)
    runtime = RoutedToolRuntime(
        registry, ledger, (ToolRuntimeRoute(tool, provider, bound, reader),), access=agent_access
    )
    assert runtime.access is agent_access
    with pytest.raises(ValueError):
        RoutedToolRuntime(
            registry,
            ledger,
            (ToolRuntimeRoute(tool, provider, facade, reader),),
            access=agent_access,
        )


def test_wrong_registry_or_missing_invocation_is_rejected_before_dispatch():
    registry = ToolRegistry()
    facade = ToolFacade(registry)
    with pytest.raises(ConfigurationError):
        bind_agent_tool_facade(facade, registry, object())
    original = ToolInvocation(registry, object(), object(), None)
    facade = ToolFacade(registry, invocation=original)
    with pytest.raises(ConfigurationError):
        bind_agent_tool_facade(facade, ToolRegistry(), object())
