"""MS-C7 actual owner SQL and blobs; controlled get-port, not production SQL batch."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from tests.integration.context.registered_fixture import ControlledGetBatch, assemble
from tests.integration.context.test_assessment_postgres import ControlledAdvice, setup
from tests.integration.context.test_registered_chain_postgres import child, child_payload
from tests.integration.context.test_registered_postgres import (
    case as case,
)
from tests.integration.context.test_registered_postgres import (
    domain as domain,
)
from tests.integration.context.test_registered_postgres import (
    material,
    register_rule,
    rule,
)
from tests.integration.context.test_registered_postgres import (
    registration as registration,
)
from tests.integration.context.test_registered_postgres import (
    understanding as understanding,
)
from tests.integration.test_control_plane import meta
from uaw.context.cache import PureComputationCache
from uaw.context.contracts import digest, matches_pin
from uaw.context.registered import BINDINGS, MATERIALS, SEALS, RegisteredContextInputs, bounded
from uaw.shared.errors import DomainError, reject


class BaselineInspection(RegisteredContextInputs):
    """Exact C6 inspect expansion order; current real rows/Reader/authority, no grant cache.

    Other helpers use the current fresh metadata pipeline so this oracle only
    isolates removal of redundant original reads; stronger seal checks are shared.
    """

    @bounded
    async def inspect(self, ctx):
        before = await self._access(ctx)
        saved = await self._recipe(ctx)
        original = await self._current(ctx, before[1])
        if any(not any(matches_pin(p, r) for r in saved.request.source_refs) for p in original):
            raise reject("context_dependency_changed", "Originals changed", 410)
        pins = tuple(
            dict.fromkeys((*saved.request.source_refs, *saved.rules.user_instruction_refs))
        )
        first = tuple([await self._read(p, ctx) for p in pins])
        if await self._recipe(ctx) != saved:
            raise reject("context_dependency_changed", "Recipe changed", 410)
        state = await self.records.get(ctx.principal, "run.input_sets", ctx.run_id)
        if await self._current(ctx, state) != original:
            raise reject("context_dependency_changed", "Originals changed", 410)
        if tuple([await self._read(p, ctx) for p in pins]) != first:
            raise reject("source_changed", "Sources changed", 410)
        if await self._recipe(ctx) != saved:
            raise reject("context_dependency_changed", "Recipe changed", 410)
        if await self._access(ctx) != before:
            raise reject("source_changed", "Run changed", 410)
        return saved, original


def wire(s, *, batch=True, kind=RegisteredContextInputs, assessor=None):
    port = ControlledGetBatch(s.records) if batch else None
    cache = PureComputationCache(max_entries=128, max_bytes=2097152)
    inputs, components, model = assemble(
        s.records,
        s.configuration,
        s.blob_directory,
        s.controller,
        cache=cache,
        current_runs=True,
        assessor=assessor or ControlledAdvice(),
        inputs_type=kind,
        record_batch=port,
        batch_required=batch,
    )
    s.ctx = s.ctx.model_copy(
        update={
            "deadline": (datetime.now(UTC) + timedelta(minutes=30)).isoformat(),
        }
    )
    return inputs, components, model, port, cache


async def test_sql_batch_chain_equivalence_reference_and_new_process(registration):
    s = registration
    s.inputs, s.components, s.model, port, _ = wire(s)
    mat, pins, saved, _, _, _ = await setup(s)
    prompts, references, bindings = [], [], []
    for i, (kind, use_port) in enumerate(
        (
            (BaselineInspection, False),
            (RegisteredContextInputs, False),
            (RegisteredContextInputs, True),
        )
    ):
        inputs, components, model, batch, cache = wire(s, batch=use_port, kind=kind)
        ctx = s.ctx.model_copy(update={"operation_id": f"equivalence-{i}"})
        bindings.append(await components.composer.authority.resolve("agent_step", ctx))
        built = await components.build(saved.request.wire(), ctx)
        assert built["kind"] == "ok", built
        prompt = await model.resolve(built["output_refs"][0], ctx)
        assert await model.resolve(built["output_refs"][0], ctx) == prompt
        prompts.append(prompt)
        references.append(await components.references.read({"reference": mat.wire()}, ctx))
        assert cache.stats.hits > 0
        if batch:
            assert max(len(keys) for _, keys in batch.calls) <= 128
            s.ctx = ctx
            payload = child_payload(s)
            payload.update(
                current_runs=True, controlled_assessor=True, controlled_record_batch=True
            )
            code, restored = await child(payload)
            assert code == 0 and restored["messages_hash"] == digest(prompt.messages), restored
            assert restored["snapshot_ref"] == built["output_refs"][0]
    assert bindings[0] == bindings[1] == bindings[2]
    assert prompts[0] == prompts[1] == prompts[2]
    assert references[0] == references[1] == references[2]
    assert s.original["text"] in [m["content"] for m in prompts[0].messages]
    assert not s.case.requests


@pytest.mark.parametrize(
    "change",
    [
        "material-revise",
        "rule-revise",
        "material-delete",
        "recipe-revoke",
        "cancel",
        "policy",
        "model",
        "foreign-session",
        "foreign-subject",
    ],
)
async def test_sql_batch_and_compat_current_rejection_equal(registration, change):
    s = registration
    s.inputs, s.components, s.model, _, _ = wire(s)
    mat, pins, saved, _, _, _ = await setup(s)
    assert (await s.inputs.inspect(s.ctx))[0] == saved
    if change == "material-revise":
        await s.inputs.register_material(
            "revised actual bytes",
            s.ctx,
            authenticated_service=s.controller,
            expected_revision=1,
            meta=meta("batch-material-revise", 1),
        )
    elif change == "rule-revise":
        await register_rule(
            s,
            rule(s, id="format-0", text="Changed actual rule.", revision=1, level="user_current"),
            expected=1,
            name="batch-rule-revise",
        )
    elif change == "material-delete":
        await s.records.delete(
            s.ctx.principal, MATERIALS, mat.id, expected_revision=1, request_id="batch-delete"
        )
    elif change == "recipe-revoke":
        await s.inputs.revoke(
            saved.ref,
            s.ctx,
            authenticated_service=s.controller,
            expected_revision=1,
            meta=meta("batch-revoke", 1),
        )
    elif change in ("cancel", "policy", "model"):
        namespace, identifier = {
            "cancel": ("budget.ledgers", s.ctx.run_id),
            "policy": ("execution.policies", s.ctx.capability_policy_ref.id),
            "model": ("model.policies", s.ctx.model_policy_ref.id),
        }[change]
        row = await s.records.get(s.ctx.principal, namespace, identifier)
        data = dict(row.payload)
        if change == "cancel":
            data["cancel_requested"] = True
        elif change == "policy":
            data["revision"] = row.revision + 1
            data["resource_scope"] = {"conversation_id": "foreign"}
        await s.records.put(
            s.ctx.principal,
            namespace,
            identifier,
            row.schema_name,
            data,
            expected_revision=row.revision,
            request_id=f"batch-{change}",
        )
    else:
        principal = s.ctx.principal.model_copy(
            update={
                "auth_session_id" if change == "foreign-session" else "id": "foreign",
            }
        )
        s.ctx = s.ctx.model_copy(update={"principal": principal})
        if change == "foreign-subject":
            s.ctx = s.ctx.model_copy(
                update={"scope": s.ctx.scope.model_copy(update={"principal_id": "foreign"})}
            )
    codes = []
    for kind, use_port in (
        (BaselineInspection, False),
        (RegisteredContextInputs, False),
        (RegisteredContextInputs, True),
    ):
        inputs, _, _, _, _ = wire(s, batch=use_port, kind=kind)
        with pytest.raises(DomainError) as caught:
            await inputs.inspect(s.ctx)
        codes.append(caught.value.failure.code)
    assert codes[0] == codes[1] == codes[2]


@pytest.mark.parametrize("namespace", [BINDINGS, MATERIALS, SEALS])
async def test_sql_group_deleted_during_real_blob_wait(registration, namespace):
    s = registration
    s.inputs, _, _, _, _ = wire(s)
    pin = await material(s)
    actual = s.inputs.blobs.get

    async def removed(principal, hashed):
        value = await actual(principal, hashed)
        row = await s.records.get(principal, namespace, pin.id)
        await s.records.delete(
            principal,
            namespace,
            pin.id,
            expected_revision=row.revision,
            request_id="delete-during-blob",
        )
        return value

    s.inputs.blobs.get = removed
    with pytest.raises(DomainError) as caught:
        await s.inputs.read(pin, s.ctx)
    assert caught.value.failure.code == "resource_missing"


@pytest.mark.parametrize("failure", ["partial", "order", "exception"])
async def test_sql_batch_incomplete_or_disconnected_never_falls_back(registration, failure):
    s = registration
    s.inputs, _, _, port, _ = wire(s)
    await material(s)
    original = port.read

    async def broken(principal, keys):
        rows = await original(principal, keys)
        if failure == "exception":
            raise reject("source_disconnected", "Controlled batch disconnection", 503)
        return rows[:-1] if failure == "partial" else tuple(reversed(rows))

    port.read = broken
    with pytest.raises(DomainError) as caught:
        await s.inputs.current(s.ctx)
    assert caught.value.failure.code == (
        "source_disconnected" if failure == "exception" else "context_record_batch_invalid"
    )


async def test_sql_batch_required_missing_dependency_explicit(registration):
    s = registration
    inputs, _, _ = assemble(
        s.records,
        s.configuration,
        s.blob_directory,
        s.controller,
        current_runs=True,
        batch_required=True,
    )
    with pytest.raises(DomainError) as caught:
        await inputs.current(s.ctx)
    assert caught.value.failure.code == "capability_unavailable"


async def test_sql_batch_model_wait_rule_revision_and_concurrent_build(registration):
    s = registration
    s.inputs, s.components, s.model, _, _ = wire(s)
    mat, pins, saved, _, _, _ = await setup(s)
    ctx = s.ctx.model_copy(update={"operation_id": "batch-concurrent-build"})
    built = await asyncio.gather(*[s.components.build(saved.request.wire(), ctx) for _ in range(2)])
    assert all(v["kind"] == "ok" for v in built), built
    assert built[0]["output_refs"] == built[1]["output_refs"]
    pin = built[0]["output_refs"][0]
    prompt = await s.model.resolve(pin, ctx)
    assert await s.model.resolve(pin, ctx) == prompt
    from uaw.context.readers import RegisteredRuleProvider

    assessor = ControlledAdvice(wait=True)
    provider = RegisteredRuleProvider(s.inputs, assessor=assessor)
    task = asyncio.create_task(provider.discover(saved.rules, ctx))
    await asyncio.wait_for(assessor.started.wait(), 45)
    try:
        await register_rule(
            s,
            rule(s, id="format-0", text="changed during wait", revision=1, level="user_current"),
            expected=1,
            name="batch-wait-rule",
        )
    finally:
        assessor.release.set()
    with pytest.raises(DomainError):
        await task
    with pytest.raises(DomainError):
        await s.model.resolve(pin, ctx)
    assert not s.case.requests


async def test_sql_final_batch_wait_original_deletion_is_current(registration):
    s = registration
    s.inputs, _, _, port, _ = wire(s)
    mat, _, saved, _, _, _ = await setup(s)
    original = next(p for p in saved.request.source_refs if p.kind == "input")
    actual = port.read
    groups = 0

    async def removed(principal, keys):
        nonlocal groups
        rows = await actual(principal, keys)
        if any(k.namespace == MATERIALS for k in keys):
            groups += 1
            if groups == 3:
                await s.records.delete(
                    principal,
                    "inputs",
                    original.id,
                    expected_revision=int(original.version),
                    request_id="delete-original-in-final-batch",
                )
        return rows

    port.read = removed
    with pytest.raises(DomainError) as caught:
        await s.inputs.inspect(s.ctx)
    assert caught.value.failure.code == "resource_missing"
