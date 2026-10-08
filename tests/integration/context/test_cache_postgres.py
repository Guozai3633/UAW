"""MS-C4 real SQL regression with opt-in pure cache; fixture tools remain controlled.

The filename deliberately differs from tests/unit/context/test_cache.py.
No model requests or Runner execution are performed.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.integration.context.model_input_fixture import EPOCHS, MATERIALS, RULES, TOOLS
from tests.integration.context.test_model_input_postgres import (
    case as case,
)
from tests.integration.context.test_model_input_postgres import (
    domain as domain,
)
from tests.integration.context.test_model_input_postgres import (
    model_inputs as model_inputs,
)
from tests.integration.context.test_model_input_postgres import (
    understanding as understanding,
)
from tests.integration.test_control_plane import meta
from uaw.context.cache import PureComputationCache
from uaw.context.model_input import GenericModelInputs
from uaw.shared.errors import DomainError


class CountingSQLInputs(GenericModelInputs):
    calls = 0

    def _format(self, *args):
        self.calls += 1
        return super()._format(*args)


@pytest.fixture
async def cached_inputs(model_inputs):
    s = model_inputs
    s.cache = PureComputationCache(max_entries=32, max_bytes=256000)
    s.component.selection.cache = s.cache
    s.resolver = CountingSQLInputs(s.component.composer, cache=s.cache)
    return s


async def test_sql_c4_repeat_reuses_only_pure_format_and_results_are_detached(cached_inputs, case):
    s = cached_inputs
    first = await s.resolver.resolve(s.pin, s.ctx)
    first.messages[0]["content"] = "caller mutation"
    first.tools[0]["description"] = "caller mutation"
    second = await s.resolver.resolve(
        s.pin, s.ctx.model_copy(update={"operation_id": "next-input"})
    )
    assert s.resolver.calls == 1
    assert second.messages[0]["content"] == s.generic_text
    assert second.messages[1]["content"] == s.original["text"]
    assert second.tools[0]["description"] != "caller mutation"
    assert s.cache.stats.hits > 0 and not case.requests


@pytest.mark.parametrize("change", ["rule", "tools", "material", "epoch"])
async def test_sql_c4_warm_cache_rejects_current_dependency_changes(cached_inputs, change):
    s = cached_inputs
    await s.resolver.resolve(s.pin, s.ctx)
    namespace, identifier = {
        "rule": (RULES, f"rule-{s.ctx.run_id}"),
        "tools": (TOOLS, f"configuration-{s.ctx.run_id}"),
        "material": (MATERIALS, s.material.id),
        "epoch": (EPOCHS, s.ctx.run_id),
    }[change]
    current = await s.store.get(s.ctx.principal, namespace, identifier)
    payload = dict(current.payload)
    if change == "rule":
        payload["text"] = "Current registered rule changed"
    elif change == "material":
        payload["text"] = "New actual material"
    elif change == "tools":
        payload["tools"] = []  # A legitimate actual source update, not missing-Reader fallback.
    else:
        payload["expected_epoch"] = 1
    await s.store.put(
        s.ctx.principal,
        namespace,
        identifier,
        current.schema_name,
        payload,
        expected_revision=current.revision,
        request_id=f"c4-change-{change}",
    )
    with pytest.raises(DomainError) as caught:
        await s.resolver.resolve(s.pin, s.ctx)
    assert caught.value.status_code == 410 and s.resolver.calls == 1


async def test_sql_c4_revoked_actual_policy_blocks_warm_cache(cached_inputs):
    s = cached_inputs
    await s.resolver.resolve(s.pin, s.ctx)
    policy = await s.store.get(
        s.ctx.principal, "execution.policies", s.ctx.capability_policy_ref.id
    )
    await s.store.put(
        s.ctx.principal,
        policy.namespace,
        policy.resource_id,
        "CapabilityPolicy",
        {**policy.payload, "revision": 3, "denied_capabilities": ["intent.understand"]},
        expected_revision=policy.revision,
        request_id="c4-revoke-policy",
    )
    with pytest.raises(DomainError) as caught:
        await s.resolver.resolve(s.pin, s.ctx)
    assert caught.value.failure.code == "context_capability_stale" and s.resolver.calls == 1


async def test_sql_c4_actual_cancel_after_warm_cache(cached_inputs, domain):
    s = cached_inputs
    await s.resolver.resolve(s.pin, s.ctx)
    await domain[1].control(
        s.ctx.principal,
        {
            "run_id": s.ctx.run_id,
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "C4 test"},
        },
        meta("c4-cancel", 2),
    )
    with pytest.raises(DomainError) as caught:
        await s.resolver.resolve(s.pin, s.ctx)
    assert caught.value.failure.category == "cancelled" and s.resolver.calls == 1


async def test_sql_c4_deleted_actual_original_blocks_warm_cache(cached_inputs):
    s = cached_inputs
    await s.resolver.resolve(s.pin, s.ctx)
    await s.store.delete(
        s.ctx.principal,
        "inputs",
        s.source.id,
        expected_revision=int(s.source.version),
        request_id="c4-delete-original",
    )
    with pytest.raises(DomainError) as caught:
        await s.resolver.resolve(s.pin, s.ctx)
    assert caught.value.failure.code == "resource_missing" and s.resolver.calls == 1


async def test_sql_c4_cache_clear_and_new_cache_recompute(cached_inputs):
    s = cached_inputs
    first = await s.resolver.resolve(s.pin, s.ctx)
    cold = CountingSQLInputs(
        s.component.composer, cache=PureComputationCache(max_entries=32, max_bytes=256000)
    )
    assert await cold.resolve(s.pin, s.ctx) == first and cold.calls == 1
    s.cache.clear()
    assert await s.resolver.resolve(s.pin, s.ctx) == first and s.resolver.calls == 2


async def test_sql_c4_window_change_recomputes_then_rejects_insufficient_space(cached_inputs):
    s = cached_inputs
    first = await s.resolver.resolve(s.pin, s.ctx)
    actual = s.component.selection.models

    class ChangedWindow:
        delta = 1

        async def resolve(self, pin, ctx):
            window = await actual.resolve(pin, ctx)
            return replace(window, context_limit=window.context_limit + self.delta)

    changed = ChangedWindow()
    s.component.selection.models = changed
    assert await s.resolver.resolve(s.pin, s.ctx) == first and s.resolver.calls == 2
    changed.delta = -1000000
    with pytest.raises(DomainError) as caught:
        await s.resolver.resolve(s.pin, s.ctx)
    assert caught.value.failure.category == "budget"


async def test_sql_c4_other_run_cannot_read_warm_cache(cached_inputs):
    s = cached_inputs
    await s.resolver.resolve(s.pin, s.ctx)
    with pytest.raises(DomainError):
        await s.resolver.resolve(s.pin, s.ctx.model_copy(update={"run_id": "c4-other-run"}))
    assert s.resolver.calls == 1
