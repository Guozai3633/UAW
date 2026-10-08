"""Persisted namespace routing, with actual SQL and explicitly controlled Context sources."""

import pytest

from tests.integration.context.test_model_input_postgres import case as case
from tests.integration.context.test_model_input_postgres import domain as domain
from tests.integration.context.test_model_input_postgres import model_inputs as model_inputs
from tests.integration.context.test_model_input_postgres import understanding as understanding
from uaw.model.input_router import ContextModelInputs
from uaw.shared.errors import CapabilityUnavailable, DomainError


async def test_router_preserves_legacy_input_and_routes_actual_generic_namespace(
    model_inputs, case
):
    s = model_inputs
    router = ContextModelInputs(s.store, case.inputs, s.resolver)
    assert await router.resolve(s.pin, s.ctx) == await s.resolver.resolve(s.pin, s.ctx)
    assert await router.resolve(
        case.request["context_snapshot_ref"], case.ctx
    ) == await case.inputs.resolve(case.request["context_snapshot_ref"], case.ctx)
    assert not case.requests


async def test_router_does_not_fallback_when_generic_authority_is_missing(model_inputs, case):
    s = model_inputs
    with pytest.raises(CapabilityUnavailable):
        await ContextModelInputs(s.store, case.inputs).resolve(s.pin, s.ctx)


async def test_router_rejects_namespace_collision_before_resolving(model_inputs, case):
    s = model_inputs
    await s.store.put(
        s.ctx.principal,
        "context.bindings",
        s.pin["id"],
        "ModelContextBinding",
        {
            "snapshot_ref": s.pin,
            "run_id": s.ctx.run_id,
            "conversation_id": s.ctx.scope.conversation_id,
        },
        expected_revision=0,
        request_id="collision",
    )
    with pytest.raises(DomainError) as collision:
        await ContextModelInputs(s.store, case.inputs, s.resolver).resolve(s.pin, s.ctx)
    assert collision.value.failure.code == "model_context_ambiguous"
