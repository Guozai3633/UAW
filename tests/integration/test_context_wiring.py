"""A's real SQL cross-boundary checks for the adapters shared with B's next package."""

import hashlib
import json

import pytest

from tests.integration.intent.test_understanding import understanding as understanding
from tests.integration.model.test_gateway import case as case
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from uaw.composition import compose
from uaw.context.contracts import RulesRequest, SelectionRequest, from_wire
from uaw.context.seed import StoredModelInputs
from uaw.run.inputs import RunInputReader
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.shared.settings import Settings
from uaw.shared.stores import StoreMissing


async def components(understanding, case):
    contexts = case.inputs.understanding
    assert contexts is understanding.intent.contexts and contexts is not None
    return contexts.components


async def test_real_refs_text_spans_and_source_set_authority(understanding, case, domain):
    component = await components(understanding, case)
    ctx = understanding.ctx
    pin = understanding.request["original_input_ref"]
    source = await component.sources.read(from_wire(Ref, pin), "pinned", ctx)
    assert source.text == understanding.original["text"]
    assert source.kind == "user_input" and source.trust == "user" and source.required
    span = from_wire(Ref, {**pin, "location": {"kind": "text_span", "start": 0, "end": 3}})
    reading = await component.sources.read(span, "pinned", ctx)
    assert reading.text == source.text[:3]
    assert reading.ref.content_hash == hashlib.sha256(reading.text.encode()).hexdigest()
    with pytest.raises(DomainError) as caught:
        await component.sources.read(
            from_wire(Ref, {**pin, "content_hash": "0" * 64}), "pinned", ctx
        )
    assert caught.value.failure.code == "source_changed"
    # The user's model-choice input is owned by the same principal/conversation,
    # but it was not admitted as a task source. Ownership alone grants no access.
    binding = (await domain[1].store.get(ctx.principal, "run.bindings", ctx.run_id)).payload
    policy = (
        await domain[1].store.get(
            ctx.principal, "model.policies", binding["model_policy_ref"]["id"]
        )
    ).payload
    with pytest.raises(DomainError) as denied:
        await component.sources.read(from_wire(Ref, policy["source_input_ref"]), "pinned", ctx)
    assert denied.value.failure.code == "permission_denied"


async def test_persisted_snapshot_rules_hashes_and_injected_model_resolver(
    understanding, case, domain
):
    inputs = await RunInputReader(domain[1].store).read(understanding.ctx)
    contexts = case.inputs.understanding
    assert contexts is not None
    snapshot_ref = await contexts.prepare(inputs, understanding.ctx, 4096)
    snapshot = (
        await domain[1].store.get(
            understanding.ctx.principal, "context.snapshots", snapshot_ref["id"]
        )
    ).payload
    assert snapshot["manifest"]["version"] == "ms-i1"
    assert (
        snapshot["manifest"]["input_refs"][0]["content_hash"]
        == hashlib.sha256(inputs.inputs[0]["text"].encode()).hexdigest()
    )
    assert snapshot["blocks"][1]["required"] and not snapshot["omitted_refs"]
    prompt = await case.inputs.resolve(snapshot_ref, understanding.ctx)
    assert json.loads(prompt.messages[1]["content"])["text"] == inputs.inputs[0]["text"]
    assert understanding.ctx.model_policy_ref is None  # No caller object was modified.
    unbound = StoredModelInputs(domain[1].store, case.inputs.blobs)
    with pytest.raises(DomainError) as missing:
        await unbound.resolve(snapshot_ref, understanding.ctx)
    assert missing.value.failure.code == "capability_unavailable"


async def test_deleted_source_cannot_be_read_from_saved_snapshot(understanding, case, domain):
    store = domain[1].store
    inputs = await RunInputReader(store).read(understanding.ctx)
    contexts = case.inputs.understanding
    assert contexts is not None
    snapshot_ref = await contexts.prepare(inputs, understanding.ctx, 4096)
    ref = inputs.refs[0]
    await store.delete(
        understanding.ctx.principal,
        "inputs",
        ref["id"],
        expected_revision=1,
        request_id="delete-context-source",
    )
    with pytest.raises(StoreMissing):
        await case.inputs.resolve(snapshot_ref, understanding.ctx)
    assert not case.requests


async def test_current_policy_revocation_and_cancellation_rechecked(understanding, case, domain):
    component = await components(understanding, case)
    ctx, store = understanding.ctx, domain[1].store
    pin = from_wire(Ref, understanding.request["original_input_ref"])
    await component.sources.read(pin, "pinned", ctx)
    policy = await store.get(ctx.principal, "execution.policies", ctx.capability_policy_ref.id)
    await store.put(
        ctx.principal,
        policy.namespace,
        policy.resource_id,
        "CapabilityPolicy",
        {**policy.payload, "revision": 3, "denied_capabilities": ["intent.understand"]},
        expected_revision=2,
        request_id="revoke-context-policy",
    )
    with pytest.raises(DomainError) as revoked:
        await component.sources.read(pin, "pinned", ctx)
    assert revoked.value.failure.code == "context_capability_stale"
    await domain[1].control(
        ctx.principal,
        {
            "run_id": ctx.run_id,
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop"},
        },
        meta("cancel-context", 2),
    )
    with pytest.raises(DomainError) as cancelled:
        await component.sources.read(pin, "pinned", ctx)
    assert cancelled.value.failure.category == "cancelled"
    assert not case.requests


@pytest.mark.parametrize(
    "case", [{"context_limit_tokens": 5000, "output_limit_tokens": 4096}], indirect=True
)
async def test_actual_model_window_cannot_drop_required_input(understanding, case, domain):
    result = await understanding.intent.understand(understanding.request, understanding.ctx)
    assert result["failure"]["code"] == "context_insufficient", result
    assert not case.requests
    identifier = (
        "understanding-" + hashlib.sha256(understanding.ctx.attempt_id.encode()).hexdigest()
    )
    with pytest.raises(StoreMissing):
        await domain[1].store.get(understanding.ctx.principal, "context.snapshots", identifier)


async def test_fixed_window_rejects_spoofing_and_unknown_rules(understanding, case, domain):
    component = await components(understanding, case)
    binding = (
        await domain[1].store.get(understanding.ctx.principal, "run.bindings", case.run["id"])
    ).payload
    ctx = understanding.ctx.model_copy(
        update={"model_policy_ref": from_wire(Ref, binding["model_policy_ref"])}
    )
    with pytest.raises(DomainError) as spoofed:
        await component.selection.allocate(
            SelectionRequest(
                candidate_refs=(from_wire(Ref, understanding.request["original_input_ref"]),),
                purpose="understanding",
                model_context_limit=999999,
                output_reserve=128,
                tool_reserve=0,
            ),
            ctx,
        )
    assert spoofed.value.failure.code == "model_window_conflict"
    with pytest.raises(DomainError) as unavailable:
        await component.rules.assemble(
            RulesRequest(
                scope_paths=(),
                user_instruction_refs=(),
                activated_skill_refs=(Ref(kind="skill", id="unregistered", version="1"),),
            ),
            ctx,
        )
    assert unavailable.value.failure.code == "capability_unavailable"


async def test_composition_shares_components_without_enabling_general_build(domain):
    container = compose(
        Settings(
            profile="development",
            development_principal_id="context-composition-test",
            database_url=domain[1].store.database.engine.url.render_as_string(hide_password=False),
        )
    )
    try:
        assert container.context_components is not None
        assert container.intent_service is not None and container.model_service is not None
        assert container.intent_service.contexts.components is container.context_components
        assert (
            container.model_service.gateway.inputs.understanding
            is container.intent_service.contexts
        )
        assert not container.bindings.availability()["context"]
        assert not container.bindings.availability()["tool"]
        assert not container.bindings.availability()["workspace"]
    finally:
        await container.close()


@pytest.mark.parametrize(
    "case", [{"context_limit_tokens": 1024, "output_limit_tokens": 1024}], indirect=True
)
async def test_gateway_recounts_native_body_before_claim_or_dispatch(case, domain):
    prompt = await case.inputs.resolve(case.request["context_snapshot_ref"], case.ctx)
    call = {
        **case.request,
        "model_config": {**case.request["model_config"], "max_output_tokens": 900},
    }
    assert prompt.estimated_tokens + 900 <= 1024  # Message-only estimate would fit.
    result = await case.model.generate(call, case.ctx)
    assert result["failure"]["code"] == "model_context_limit", result
    assert not case.requests
    with pytest.raises(StoreMissing):
        await domain[1].store.get(case.ctx.principal, "model.invocations", case.ctx.attempt_id)
