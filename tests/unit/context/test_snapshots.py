"""MS-C2 boundary tests. In-memory transactions are controlled test substitutes."""

from __future__ import annotations

import asyncio
import copy
import json
from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest

from tests.unit.context.test_components import (
    Control,
    FixtureModels,
    FixtureReader,
    FixtureRules,
    candidate,
    context,
    reading,
    ref,
)
from uaw.context.contracts import (
    CompositionBinding,
    PreservationSpec,
    RulesRequest,
    digest,
    from_wire,
)
from uaw.context.facade import ContextComponents
from uaw.context.repository import (
    BINDINGS,
    INSTRUCTIONS,
    REFERENCES,
    REQUESTS,
    SCOPES,
    SNAPSHOTS,
    ContextRepository,
)
from uaw.shared.contracts import Location, Principal, Ref
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import Record, StoreConflict, StoreMissing


class MemoryRecords:
    """No SQL claims: emulate detached records and immutable inserts only."""

    def __init__(self) -> None:
        self.data: dict[tuple[str, str, str], Record] = {}
        self.requests: dict[tuple[str, str, str], tuple[str, dict[str, Any]]] = {}
        self.lock = asyncio.Lock()
        self.writes = 0
        self.fail_namespace: str | None = None
        self.after_write = None

    async def get(self, principal, namespace, resource_id, *, revision=None):
        record = self.data.get((principal.id, namespace, resource_id))
        if record is None or (revision is not None and record.revision != revision):
            raise StoreMissing()
        return copy.deepcopy(record)


class MemoryTransaction:
    def __init__(self, records, owner):
        self.records, self.owner = records, owner

    async def load(self, namespace, identifier):
        row = self.records.data.get((self.owner, namespace, identifier))
        if row is None:
            raise StoreMissing()
        return SimpleNamespace(payload=copy.deepcopy(row.payload), schema_name=row.schema_name)

    async def write(self, namespace, identifier, schema, payload, expected=0):
        validate_contract(schema, payload)
        if namespace == self.records.fail_namespace:
            raise reject("fixture_write_failure", "Controlled write failure")
        key = (self.owner, namespace, identifier)
        if key in self.records.data:
            raise StoreConflict()
        self.records.data[key] = Record(namespace, identifier, 1, schema, copy.deepcopy(payload))
        self.records.writes += 1
        if self.records.after_write is not None:
            self.records.after_write(namespace)


class MemoryTransactions:
    def __init__(self, records):
        self.records = records

    async def execute(
        self, owner, aggregate, meta, parameters, action, verify=None, on_replay=None
    ):
        async with self.records.lock:
            key = (owner.id, aggregate, meta.request_id)
            checksum = digest(parameters)
            previous = self.records.requests.get(key)
            if previous:
                if checksum != previous[0]:
                    raise StoreConflict("idempotency_conflict")
                if verify:
                    await verify()
                return copy.deepcopy(previous[1])
            saved = copy.deepcopy(self.records.data)
            writes = self.records.writes
            try:
                if verify:
                    await verify()
                result = await action(MemoryTransaction(self.records, owner.id))
                self.records.requests[key] = (checksum, copy.deepcopy(result))
                return result
            except BaseException:
                self.records.data = saved
                self.records.writes = writes
                raise


class FixtureAuthority:
    def __init__(self, binding):
        self.binding = binding
        self.revoked = False
        self.flip_epoch = False
        self.calls = 0

    async def resolve(self, purpose, ctx):
        if purpose != "agent_step":
            raise reject("fixture_purpose_unavailable", "Fixture has one explicit purpose")
        return self.binding

    async def verify(self, binding, ctx):
        self.calls += 1
        if self.revoked:
            raise reject("permission_denied", "Fixture authority revoked", 403)
        if self.flip_epoch and self.calls > 1:
            self.binding = replace(self.binding, epoch=self.binding.epoch + 1)
        if binding != self.binding:
            raise reject("context_dependency_changed", "Fixture binding changed", 410)


def setup():
    original = reading("  原文 123.40\r\n", id="original", kind="user_input", trust="user")
    rule = reading("Follow the user", id="registered", kind="instruction", trust="platform")
    cap = reading(
        json.dumps({"run_id": "run", "tools": []}), id="capability", trust="platform", required=True
    )
    ctx = context().model_copy(update={"run_id": "run"})
    reader = FixtureReader(original, rule, cap)
    binding = CompositionBinding(
        epoch=0,
        rules=RulesRequest(scope_paths=(), user_instruction_refs=(), activated_skill_refs=()),
        capability_ref=cap.ref,
        preserve=PreservationSpec(
            required_refs=(original.ref,),
            exact_strings=(),
            requirement_ids=(),
            pending_action_refs=(),
        ),
    )
    authority = FixtureAuthority(binding)
    records = MemoryRecords()
    repository = ContextRepository(records, MemoryTransactions(records))  # type: ignore[arg-type]
    control, models = Control(), FixtureModels(100000)
    component = ContextComponents(
        readers={"input": reader},
        cancellation=control,
        rules=FixtureRules(candidate(rule, "platform")),
        models=models,
        repository=repository,
        authority=authority,
    )
    request = {
        "purpose": "agent_step",
        "source_refs": [original.ref.wire()],
        "model_policy_ref": ctx.model_policy_ref.wire(),
        "output_reserve": 256,
        "tool_reserve": 128,
        "expected_epoch": 0,
        "preserve": {
            "required_refs": [],
            "exact_strings": ["123.40"],
            "requirement_ids": [],
            "pending_action_refs": [],
        },
    }
    return SimpleNamespace(
        component=component,
        ctx=ctx,
        reader=reader,
        authority=authority,
        records=records,
        request=request,
        control=control,
        models=models,
        original=original,
        rule=rule,
        cap=cap,
    )


async def build(case):
    result = await case.component.build(case.request, case.ctx)
    assert result["kind"] == "ok", result
    return result


async def test_generic_snapshot_atomic_manifest_and_original_text():
    c = setup()
    result = await build(c)
    snapshot = result["payload"]
    assert snapshot["epoch"] == 0 and snapshot["manifest"]["version"] == "ms-c2"
    assert snapshot["instruction_set_ref"]["content_hash"]
    assert snapshot["capability_snapshot_ref"] == c.cap.ref.wire()
    assert {key[1] for key in c.records.data} == {
        SNAPSHOTS,
        INSTRUCTIONS,
        BINDINGS,
        SCOPES,
        REQUESTS,
        REFERENCES,
    }
    validate_contract("RuntimeContextruntimeBuildResult", result)
    pin = from_wire(Ref, result["output_refs"][0])
    assert (await c.component.read_snapshot(pin, c.ctx))["payload"] == snapshot
    reference = await c.component.resolve_reference({"ref": c.original.ref.wire()}, c.ctx)
    assert reference["kind"] == "ok" and reference["payload"]["citations"] == []
    read = await c.component.references.handle(
        {
            "action": "read",
            "parameters": {"reference": c.original.ref.wire()},
        },
        c.ctx,
    )
    assert read["payload"]["result"]["text"] == c.original.text


async def test_durable_component_replay_and_changed_request_conflict():
    c = setup()
    first = await build(c)
    before = copy.deepcopy(c.records.data)
    second = await c.component.build(c.request, c.ctx.model_copy(update={"attempt_id": "retry"}))
    assert first == second and c.records.data == before
    changed = {**c.request, "tool_reserve": 129}
    result = await c.component.build(changed, c.ctx)
    assert result["failure"]["code"] == "idempotency_conflict"
    assert c.records.data == before


async def test_parallel_same_operation_has_one_immutable_snapshot():
    c = setup()
    results = await asyncio.gather(*(c.component.build(c.request, c.ctx) for _ in range(4)))
    assert all(result == results[0] for result in results)
    assert len(c.records.requests) == 1
    assert len([key for key in c.records.data if key[1] == SNAPSHOTS]) == 1


async def test_new_epoch_creates_new_snapshot_and_old_becomes_stale():
    c = setup()
    first = await build(c)
    c.authority.binding = replace(c.authority.binding, epoch=1)
    c.request = {**c.request, "expected_epoch": 1}
    c.ctx = c.ctx.model_copy(update={"operation_id": "new-operation"})
    second = await build(c)
    assert first["payload"]["id"] != second["payload"]["id"]
    old = await c.component.read_snapshot(from_wire(Ref, first["output_refs"][0]), c.ctx)
    assert old["kind"] == "stale"
    assert len([key for key in c.records.data if key[1] == SNAPSHOTS]) == 2


@pytest.mark.parametrize("change", ["source", "rule", "capability"])
async def test_saved_reads_detect_changed_content(change):
    c = setup()
    first = await build(c)
    source = {"source": c.original, "rule": c.rule, "capability": c.cap}[change]
    c.reader.records[source.ref.id] = replace(source, text=source.text + "changed")
    result = await c.component.read_snapshot(from_wire(Ref, first["output_refs"][0]), c.ctx)
    assert result["kind"] == "stale"


async def test_deleted_source_not_replayed_from_snapshot():
    c = setup()
    first = await build(c)
    del c.reader.records[c.original.ref.id]
    result = await c.component.build(c.request, c.ctx)
    assert result["kind"] == "missing"
    opened = await c.component.read_snapshot(from_wire(Ref, first["output_refs"][0]), c.ctx)
    assert opened["kind"] == "missing"


async def test_revocation_blocks_saved_snapshot_and_reference():
    c = setup()
    first = await build(c)
    c.reader.revoked = True
    assert (await c.component.read_snapshot(from_wire(Ref, first["output_refs"][0]), c.ctx))[
        "kind"
    ] == "denied"
    assert (await c.component.resolve_reference({"ref": c.original.ref.wire()}, c.ctx))[
        "kind"
    ] == "denied"


async def test_scope_and_run_binding_cannot_be_bypassed():
    c = setup()
    first = await build(c)
    pin = from_wire(Ref, first["output_refs"][0])
    other = c.ctx.model_copy(update={"run_id": "other-run"})
    assert (await c.component.read_snapshot(pin, other))["kind"] == "denied"
    other = c.ctx.model_copy(
        update={
            "scope": c.ctx.scope.model_copy(update={"task_id": "other-task"}),
            "task_id": "other-task",
        }
    )
    assert (await c.component.read_snapshot(pin, other))["kind"] == "denied"
    other = c.ctx.model_copy(
        update={
            "principal": Principal(id="other", kind="user", auth_session_id="other-session"),
            "scope": c.ctx.scope.model_copy(update={"principal_id": "other"}),
        }
    )
    assert (await c.component.read_snapshot(pin, other))["kind"] == "missing"


async def test_registered_reference_required_no_url_evidence_fabrication():
    c = setup()
    result = await c.component.resolve_reference({"ref": c.original.ref.wire()}, c.ctx)
    assert result["kind"] == "missing"  # Read access alone is not registration.
    web = await c.component.resolve_reference({"ref": ref("web").wire()}, c.ctx)
    assert web["failure"]["code"] == "capability_unavailable"
    assert "payload" not in web


async def test_missing_workspace_reader_blocks_build_without_partial_records():
    c = setup()
    c.request = {**c.request, "source_refs": [ref("workspace").wire()]}
    result = await c.component.build(c.request, c.ctx)
    assert result["failure"]["code"] == "capability_unavailable"
    assert not c.records.data and not c.records.requests


@pytest.mark.parametrize("failure", ["write", "budget", "epoch", "requirements", "authority"])
async def test_failed_build_leaves_no_component_records(failure):
    c = setup()
    if failure == "write":
        c.records.fail_namespace = BINDINGS
    elif failure == "budget":
        c.models.limit = 1200
    elif failure == "epoch":
        c.authority.flip_epoch = True
    elif failure == "requirements":
        c.request["preserve"]["requirement_ids"] = ["unbound-requirement"]
    else:
        c.authority.revoked = True
    result = await c.component.build(c.request, c.ctx)
    assert result["kind"] != "ok"
    assert not c.records.data and not c.records.requests


async def test_user_and_authority_preservation_cannot_be_silently_dropped():
    c = setup()
    c.request["source_refs"] = []
    result = await build(c)
    assert any(
        b["content_ref"] == c.original.ref.wire() and b["required"]
        for b in result["payload"]["blocks"]
    )
    c.request["preserve"]["exact_strings"] = ["unread important text"]
    c.ctx = c.ctx.model_copy(update={"operation_id": "missing-preservation"})
    result = await c.component.build(c.request, c.ctx)
    assert result["kind"] == "missing"


async def test_reference_text_span_and_location_boundaries():
    c = setup()
    await build(c)
    location = {"kind": "text_span", "start": 2, "end": 4}
    result = await c.component.references.handle(
        {
            "action": "read",
            "parameters": {"reference": c.original.ref.wire(), "location": location},
        },
        c.ctx,
    )
    assert result["payload"]["result"]["text"] == c.original.text[2:4]
    for invalid in ({"kind": "page", "start": 1}, {"kind": "text_span", "start": 0, "end": 9999}):
        result = await c.component.references.handle(
            {
                "action": "read",
                "parameters": {"reference": c.original.ref.wire(), "location": invalid},
            },
            c.ctx,
        )
        assert result["kind"] in ("stale", "failed")


async def test_registered_slice_cannot_expand_to_whole_source():
    c = setup()
    loc = Location(kind="text_span", start=2, end=4)
    fragment = reading(c.original.text[2:4], id="fragment", kind="user_input", trust="user")
    fragment = replace(fragment, ref=fragment.ref.model_copy(update={"location": loc}))
    c.reader.records[fragment.ref.id] = fragment
    c.authority.binding = replace(
        c.authority.binding,
        preserve=PreservationSpec(
            required_refs=(fragment.ref,),
            exact_strings=(),
            requirement_ids=(),
            pending_action_refs=(),
        ),
    )
    c.request["source_refs"] = [fragment.ref.wire()]
    c.request["preserve"]["exact_strings"] = []
    await build(c)
    result = await c.component.references.handle(
        {
            "action": "read",
            "parameters": {
                "reference": fragment.ref.wire(),
                "location": {"kind": "whole"},
            },
        },
        c.ctx,
    )
    assert result["kind"] == "stale"


async def test_cancelled_build_does_not_write():
    c = setup()
    c.control.cancelled = True
    result = await c.component.build(c.request, c.ctx)
    assert result["kind"] == "cancelled" and not c.records.data


async def test_missing_general_composition_ports_keep_existing_baseline_unavailable():
    c = setup()
    component = ContextComponents(
        readers={"input": c.reader},
        cancellation=c.control,
        rules=c.component.rules.provider,
        models=c.models,
        repository=c.component.composer.repository,
    )
    result = await component.build(c.request, c.ctx)
    assert result["failure"]["code"] == "capability_unavailable"
    assert not c.records.data


async def test_snapshot_hash_and_revision_boundary():
    c = setup()
    first = await build(c)
    pin = from_wire(Ref, first["output_refs"][0])
    for invalid in (
        pin.model_copy(update={"version": "2"}),
        pin.model_copy(update={"content_hash": "0" * 64}),
    ):
        assert (await c.component.read_snapshot(invalid, c.ctx))["kind"] != "ok"


async def test_registration_and_pagination_remain_explicitly_unavailable():
    c = setup()
    await build(c)
    result = await c.component.references.handle(
        {
            "action": "read",
            "parameters": {"reference": c.original.ref.wire(), "cursor": "unsupported"},
        },
        c.ctx,
    )
    assert result["failure"]["code"] == "capability_unavailable"


async def test_cancel_after_partial_writes_rolls_back_component_transaction():
    c = setup()

    def cancel_after_binding(namespace):
        if namespace == BINDINGS:
            c.control.cancelled = True

    c.records.after_write = cancel_after_binding
    result = await c.component.build(c.request, c.ctx)
    assert result["kind"] == "cancelled"
    assert not c.records.data and not c.records.requests
