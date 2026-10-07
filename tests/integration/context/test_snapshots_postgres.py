"""Real PostgreSQL MS-C2 tests for A to run; capability/epoch adapters are controlled.

No real LLM/Runner/Tool capability is asserted. Run input, current policy, cancellation,
model metadata and the transaction store use the actual ms-i1 adapters.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from tests.integration.intent.test_understanding import understanding as understanding
from tests.integration.model.test_gateway import case as case
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from uaw.context.contracts import (
    CompositionBinding,
    PreservationSpec,
    Reading,
    RulesRequest,
    from_wire,
)
from uaw.context.facade import ContextComponents
from uaw.context.repository import SNAPSHOTS, ContextRepository
from uaw.infrastructure.db.transactions import TransactionalStore
from uaw.run.context import RunContextSources
from uaw.shared.contracts import Ref
from uaw.shared.errors import reject
from uaw.shared.stores import StoreMissing


class ControlledCapabilities:
    """Approved only inside this fixture: empty capability JSON, not product discovery."""

    def __init__(self, authority, ctx):
        self.authority = authority
        text = json.dumps({"run_id": ctx.run_id, "tools": []})
        pin = Ref(
            kind="configuration",
            id="controlled-capabilities",
            version="1",
            content_hash=hashlib.sha256(text.encode()).hexdigest(),
        )
        self.value = Reading(pin, text, trust="platform", required=True)

    async def check(self, pin, ctx):
        await self.authority.authorize(ctx)
        if pin != self.value.ref:
            raise reject("fixture_source_changed", "Controlled capability pin changed", 410)

    async def read(self, pin, revision_policy, ctx):
        await self.check(pin, ctx)
        return self.value


class ControlledBinding:
    """Epoch/purpose binding is controlled; the SQL cancellation/ACL checks are real."""

    def __init__(self, authority, capability, source):
        self.authority = authority
        self.value = CompositionBinding(
            epoch=0,
            rules=RulesRequest(scope_paths=(), user_instruction_refs=(), activated_skill_refs=()),
            capability_ref=capability,
            preserve=PreservationSpec(
                required_refs=(source,),
                exact_strings=(),
                requirement_ids=(),
                pending_action_refs=(),
            ),
        )

    async def resolve(self, purpose, ctx):
        await self.authority.authorize(ctx)
        if purpose != "understanding":
            raise reject("fixture_purpose_unavailable", "Fixture supports only understanding")
        return self.value

    async def verify(self, binding, ctx):
        await self.authority.authorize(ctx)
        if binding != self.value:
            raise reject("context_dependency_changed", "Controlled epoch changed", 410)


@pytest.fixture
async def snapshots(understanding, case, domain):
    store = domain[1].store
    ctx = understanding.ctx
    bound = (await store.get(ctx.principal, "run.bindings", ctx.run_id)).payload
    ctx = ctx.model_copy(
        update={
            "operation_id": "generic-snapshot-test",
            "model_policy_ref": from_wire(Ref, bound["model_policy_ref"]),
        }
    )
    baseline = case.inputs.understanding.components
    source = from_wire(Ref, understanding.request["original_input_ref"])
    run_authority = RunContextSources(store)
    capability = ControlledCapabilities(run_authority, ctx)
    authority = ControlledBinding(run_authority, capability.value.ref, source)
    components = ContextComponents(
        readers={**baseline.sources.readers, "configuration": capability},
        cancellation=run_authority,
        rules=baseline.rules.provider,
        models=baseline.selection.models,
        repository=ContextRepository(store, TransactionalStore(store.database)),
        authority=authority,
    )
    request = {
        "purpose": "understanding",
        "source_refs": [source.wire()],
        "model_policy_ref": ctx.model_policy_ref.wire(),
        "output_reserve": 128,
        "tool_reserve": 0,
        "expected_epoch": 0,
        "preserve": {
            "required_refs": [source.wire()],
            "exact_strings": [],
            "requirement_ids": [],
            "pending_action_refs": [],
        },
    }
    return SimpleNamespace(
        component=components,
        store=store,
        ctx=ctx,
        request=request,
        source=source,
        authority=authority,
        original=understanding.original,
    )


async def built(s):
    result = await s.component.build(s.request, s.ctx)
    assert result["kind"] == "ok", result
    return result


async def test_sql_atomic_snapshot_actual_original_and_reference_open(snapshots, case):
    s = snapshots
    result = await built(s)
    snapshot = result["payload"]
    assert snapshot["manifest"]["version"] == "ms-c2"
    record = await s.store.get(s.ctx.principal, SNAPSHOTS, snapshot["id"], revision=1)
    assert record.payload == snapshot
    assert snapshot["instruction_set_ref"]["content_hash"]
    opened = await s.component.read_snapshot(from_wire(Ref, result["output_refs"][0]), s.ctx)
    assert opened["payload"] == snapshot
    reference = await s.component.resolve_reference({"ref": s.source.wire()}, s.ctx)
    assert reference["kind"] == "ok" and reference["payload"]["citations"] == []
    text = await s.component.references.handle(
        {
            "action": "read",
            "parameters": {"reference": s.source.wire()},
        },
        s.ctx,
    )
    assert text["payload"]["result"]["text"] == s.original["text"]
    assert not case.requests


async def test_sql_idempotent_replay_and_parameter_conflict(snapshots):
    s = snapshots
    first = await built(s)
    retry = await s.component.build(s.request, s.ctx.model_copy(update={"attempt_id": "retry"}))
    assert retry == first
    changed = await s.component.build({**s.request, "output_reserve": 129}, s.ctx)
    assert changed["failure"]["code"] == "idempotency_conflict"
    assert (await s.store.get(s.ctx.principal, SNAPSHOTS, first["payload"]["id"])).revision == 1


async def test_sql_concurrent_calls_share_one_snapshot(snapshots):
    s = snapshots
    values = await asyncio.gather(*(s.component.build(s.request, s.ctx) for _ in range(3)))
    assert values[0]["kind"] == "ok", values[0]
    assert values == [values[0]] * 3
    assert (await s.store.get(s.ctx.principal, SNAPSHOTS, values[0]["payload"]["id"])).revision == 1


async def test_sql_new_epoch_keeps_old_snapshot_immutable(snapshots):
    s = snapshots
    old = await built(s)
    s.authority.value = replace(s.authority.value, epoch=1)
    s.request = {**s.request, "expected_epoch": 1}
    s.ctx = s.ctx.model_copy(update={"operation_id": "new-epoch"})
    new = await built(s)
    assert old["payload"]["id"] != new["payload"]["id"]
    assert (await s.store.get(s.ctx.principal, SNAPSHOTS, old["payload"]["id"])).payload == old[
        "payload"
    ]
    reopened = await s.component.read_snapshot(from_wire(Ref, old["output_refs"][0]), s.ctx)
    assert reopened["kind"] == "stale"


async def test_sql_deleted_source_blocks_replay_snapshot_and_reference(snapshots):
    s = snapshots
    first = await built(s)
    await s.store.delete(
        s.ctx.principal,
        "inputs",
        s.source.id,
        expected_revision=int(s.source.version),
        request_id="delete-generic-source",
    )
    assert (await s.component.build(s.request, s.ctx))["kind"] == "missing"
    assert (await s.component.read_snapshot(from_wire(Ref, first["output_refs"][0]), s.ctx))[
        "kind"
    ] == "missing"
    assert (await s.component.resolve_reference({"ref": s.source.wire()}, s.ctx))[
        "kind"
    ] == "missing"


async def test_sql_current_policy_revocation_blocks_saved_reference(snapshots):
    s = snapshots
    await built(s)
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
        request_id="revoke-generic-policy",
    )
    result = await s.component.resolve_reference({"ref": s.source.wire()}, s.ctx)
    assert result["kind"] == "stale"
    assert result["failure"]["code"] == "context_capability_stale"


async def test_sql_cancellation_blocks_snapshot_and_ref(snapshots, domain):
    s = snapshots
    first = await built(s)
    await domain[1].control(
        s.ctx.principal,
        {
            "run_id": s.ctx.run_id,
            "control": {
                "mode": "cancel",
                "preserve_refs": [],
                "reason": "Stop test",
            },
        },
        meta("cancel-generic-context", 2),
    )
    assert (await s.component.read_snapshot(from_wire(Ref, first["output_refs"][0]), s.ctx))[
        "kind"
    ] == "cancelled"
    assert (await s.component.resolve_reference({"ref": s.source.wire()}, s.ctx))[
        "kind"
    ] == "cancelled"


async def test_sql_unavailable_workspace_does_not_commit(snapshots):
    s = snapshots
    request = {
        **s.request,
        "source_refs": [
            {
                "kind": "workspace",
                "id": "unconnected",
                "version": "1",
            }
        ],
    }
    result = await s.component.build(request, s.ctx)
    assert result["failure"]["code"] == "capability_unavailable"
    from uaw.context.contracts import digest
    from uaw.context.repository import scope_key

    identifier = "context-" + digest(
        {
            **scope_key(s.ctx),
            "request_id": s.ctx.operation_id,
        }
    )
    with pytest.raises(StoreMissing):
        await s.store.get(s.ctx.principal, SNAPSHOTS, identifier)


async def test_sql_reference_conflict_rolls_back_whole_snapshot(snapshots):
    from uaw.context.contracts import digest
    from uaw.context.repository import (
        INSTRUCTIONS,
        REFERENCES,
        reference_id,
        scope_key,
    )

    s = snapshots
    await built(s)
    registered = await s.store.get(s.ctx.principal, REFERENCES, reference_id(s.source, s.ctx))
    # Deliberate fixture corruption through the generic store; no Context API permits this.
    await s.store.put(
        s.ctx.principal,
        REFERENCES,
        registered.resource_id,
        "ReferenceRecord",
        {**registered.payload, "title": "corrupted registration"},
        expected_revision=1,
        request_id="fixture-reference-conflict",
    )
    s.ctx = s.ctx.model_copy(update={"operation_id": "conflicting-registration"})
    result = await s.component.build(s.request, s.ctx)
    assert result["failure"]["code"] == "reference_conflict"
    identifier = "context-" + digest(
        {
            **scope_key(s.ctx),
            "request_id": s.ctx.operation_id,
        }
    )
    for namespace in (SNAPSHOTS, INSTRUCTIONS):
        with pytest.raises(StoreMissing):
            await s.store.get(s.ctx.principal, namespace, identifier)
