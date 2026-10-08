"""MS-C5 source/timeout/capacity boundaries. Memory ports are controlled substitutes."""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import replace
from types import SimpleNamespace

import pytest

from tests.unit.context.test_components import context, reading
from uaw.context.contracts import (
    ContextRequest,
    InstructionRule,
    ModelToolSet,
    PreservationSpec,
    RulesRequest,
)
from uaw.context.readers import RegisteredContextReader
from uaw.context.registered import RegisteredContextInputs
from uaw.shared.contracts import Principal, Ref, RequestMeta, ScopeSelector
from uaw.shared.errors import DomainError, reject
from uaw.shared.stores import Record, StoreMissing


class Records:
    def __init__(self, ctx, original):
        self.rows = {
            ("run.bindings", "run"): Record(
                "run.bindings",
                "run",
                1,
                "RunAdmissionBinding",
                {
                    "input_ref": original.ref.wire(),
                    "model_policy_ref": ctx.model_policy_ref.wire(),
                    "configuration_ref": Ref(kind="configuration", id="config", version="1").wire(),
                    "turn_id": "turn",
                },
            ),
            ("run.input_sets", "run"): Record(
                "run.input_sets",
                "run",
                1,
                "RunInputState",
                {
                    "run_id": "run",
                    "conversation_id": ctx.scope.conversation_id,
                    "revision": 1,
                    "original_input_ref": original.ref.wire(),
                    "patch_refs": [],
                },
            ),
        }

    async def get(self, owner, namespace, identifier, *, revision=None):
        if (namespace, identifier) not in self.rows:
            raise StoreMissing()
        return self.rows[(namespace, identifier)]


class Runs:
    cancelled = False
    revoked = False
    stalled = False

    def __init__(self, original):
        self.original = original

    async def authorize(self, ctx):
        if self.revoked:
            raise reject("permission_denied", "Controlled current Run denial", 403)
        if self.stalled:
            await asyncio.Event().wait()

    async def is_cancelled(self, ctx):
        return self.cancelled

    async def read(self, ref, policy, ctx):
        return self.original


class Blobs:
    calls = 0

    async def put(self, owner, value):
        self.calls += 1
        return hashlib.sha256(value).hexdigest()


class NoWrites:
    async def execute(self, *args, **kwargs):
        raise AssertionError("Invalid registration must not enter storage")


def setup():
    ctx = context().model_copy(update={"run_id": "run"})
    original = reading("  Exact original\r\n", kind="user_input", trust="user", required=True)
    controller = Principal(id="controller", kind="service", auth_session_id="controller-session")
    records = Records(ctx, original)
    runs, blobs = Runs(original), Blobs()
    inputs = RegisteredContextInputs(
        controller=controller, records=records, blobs=blobs, transactions=NoWrites(), runs=runs
    )
    return SimpleNamespace(
        inputs=inputs, ctx=ctx, records=records, runs=runs, blobs=blobs, controller=controller
    )


def meta(revision=0):
    return RequestMeta(request_id="fixture", schema_version="0.1", expected_revision=revision)


def request(s, **updates):
    base = ContextRequest(
        purpose="agent_step",
        source_refs=(),
        model_policy_ref=s.ctx.model_policy_ref,
        output_reserve=128,
        tool_reserve=64,
        expected_epoch=0,
        preserve=PreservationSpec(
            required_refs=(), exact_strings=(), requirement_ids=(), pending_action_refs=()
        ),
    )
    return base.model_copy(update=updates)


async def test_actual_run_pin_not_request_text_protects_original_identity():
    s = setup()
    assert (await s.inputs.current(s.ctx))[0] == s.runs.original.ref
    s.runs.original = replace(
        s.runs.original, ref=s.runs.original.ref.model_copy(update={"id": "foreign"})
    )
    with pytest.raises(DomainError) as caught:
        await s.inputs.current(s.ctx)
    assert caught.value.failure.code == "source_changed"


@pytest.mark.parametrize("field", ["kind", "trust", "required", "hash"])
async def test_bad_run_reading_identity_rejected(field):
    s = setup()
    values = {
        "kind": {"kind": "material"},
        "trust": {"trust": "external"},
        "required": {"required": False},
        "hash": {"ref": s.runs.original.ref.model_copy(update={"content_hash": "0" * 64})},
    }
    s.runs.original = replace(s.runs.original, **values[field])
    with pytest.raises(DomainError):
        await s.inputs.current(s.ctx)


@pytest.mark.parametrize(
    "text", ["", "x" * 65537, "材" * 22000], ids=["empty", "ascii-limit", "utf8-limit"]
)
async def test_capacity_fails_before_blob_or_sql(text):
    s = setup()
    with pytest.raises(DomainError) as caught:
        await s.inputs.register_material(
            text, s.ctx, authenticated_service=s.controller, expected_revision=0, meta=meta()
        )
    assert caught.value.status_code == 413 and s.blobs.calls == 0


@pytest.mark.parametrize("expected", [-1, True, 1])
async def test_meta_cas_mismatch_fails_before_write(expected):
    s = setup()
    with pytest.raises(DomainError):
        await s.inputs.register_material(
            "text",
            s.ctx,
            authenticated_service=s.controller,
            expected_revision=expected,
            meta=meta(),
        )
    assert s.blobs.calls == 0


@pytest.mark.parametrize("change", ["session", "kind", "id", "delegation"])
async def test_complete_controller_identity_not_id_only(change):
    s = setup()
    updates = {
        "session": {"auth_session_id": "other"},
        "kind": {"kind": "admin"},
        "id": {"id": "other"},
        "delegation": {"delegated_by": "other"},
    }
    with pytest.raises(DomainError) as caught:
        await s.inputs.register_material(
            "text",
            s.ctx,
            authenticated_service=s.controller.model_copy(update=updates[change]),
            expected_revision=0,
            meta=meta(),
        )
    assert caught.value.status_code == 403 and s.blobs.calls == 0


async def test_missing_run_and_revoked_cancelled_sources_are_not_defaults():
    s = setup()
    s.inputs.runs = None
    s.inputs.guard.cancellation = None
    with pytest.raises(DomainError) as caught:
        await s.inputs.current(s.ctx)
    assert caught.value.failure.code == "capability_unavailable"
    s = setup()
    s.runs.revoked = True
    with pytest.raises(DomainError):
        await s.inputs.current(s.ctx)
    s.runs.revoked = False
    s.runs.cancelled = True
    with pytest.raises(DomainError) as caught:
        await s.inputs.current(s.ctx)
    assert caught.value.failure.category == "cancelled"


async def test_stalled_current_source_deadline_and_task_cancel():
    from datetime import UTC, datetime, timedelta

    s = setup()
    s.runs.stalled = True
    short = s.ctx.model_copy(
        update={"deadline": (datetime.now(UTC) + timedelta(milliseconds=50)).isoformat()}
    )
    with pytest.raises(DomainError) as caught:
        await s.inputs.current(short)
    assert caught.value.failure.category == "timeout"
    task = asyncio.create_task(s.inputs.current(s.ctx))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.parametrize("change", ["purpose", "epoch", "model", "pending", "skill", "path"])
async def test_unsupported_recipe_dependencies_and_untrusted_epoch_fail(change):
    s = setup()
    value = request(s)
    rules = RulesRequest(scope_paths=(), user_instruction_refs=(), activated_skill_refs=())
    if change == "purpose":
        value = value.model_copy(update={"purpose": "understanding"})
    elif change == "epoch":
        value = value.model_copy(update={"expected_epoch": 4})
    elif change == "model":
        value = value.model_copy(
            update={"model_policy_ref": Ref(kind="policy", id="other", version="1")}
        )
    elif change == "pending":
        value = value.model_copy(
            update={"preserve": value.preserve.model_copy(update={"requirement_ids": ("unknown",)})}
        )
    elif change == "skill":
        rules = rules.model_copy(
            update={"activated_skill_refs": (Ref(kind="skill", id="unknown", version="1"),)}
        )
    else:
        rules = rules.model_copy(
            update={"scope_paths": (Ref(kind="workspace", id="unknown", version="1"),)}
        )
    with pytest.raises(DomainError):
        await s.inputs.register_recipe(
            value,
            rules,
            ModelToolSet(run_id="run", tools=()),
            s.ctx,
            authenticated_service=s.controller,
            expected_revision=0,
            meta=meta(),
        )


@pytest.mark.parametrize("change", ["scope", "source", "level", "id"])
async def test_rule_never_borrows_material_or_other_scope(change):
    s = setup()
    value = InstructionRule(
        id="rule",
        source_ref=Ref(kind="rule", id="rule", version="1"),
        scope=ScopeSelector(conversation_id=s.ctx.scope.conversation_id),
        text="fixture registered rule",
        level="platform",
    )
    if change == "scope":
        value = value.model_copy(update={"scope": ScopeSelector(conversation_id="other")})
    elif change == "source":
        value = value.model_copy(
            update={"source_ref": Ref(kind="content", id="material", version="1")}
        )
    elif change == "level":
        value = value.model_copy(update={"level": "skill"})
    else:
        value = value.model_copy(update={"id": "recipe-forged"})
    with pytest.raises(DomainError):
        await s.inputs.register_rule(
            value, s.ctx, authenticated_service=s.controller, expected_revision=0, meta=meta()
        )
    assert s.blobs.calls == 0


async def test_tool_validation_missing_and_mutating_source_rejects():
    from tests.unit.context.test_model_input import tool

    s = setup()
    tools = ModelToolSet(run_id="run", tools=(tool(),))
    with pytest.raises(DomainError) as caught:
        await s.inputs.check_tools(tools, s.ctx)
    assert caught.value.failure.code == "capability_unavailable"

    class Mutates:
        async def check(self, tools, ctx):
            tools.tools[0]["description"] = "changed after validation"

    s.inputs.tool_validator = Mutates()
    with pytest.raises(DomainError) as caught:
        await s.inputs.check_tools(tools, s.ctx)
    assert caught.value.failure.code == "source_changed"
    assert tools.tools[0]["description"] == tool()["description"]


async def test_latest_and_unknown_sources_unavailable():
    s = setup()
    with pytest.raises(DomainError):
        await s.inputs.read(Ref(kind="memory", id="unknown", version="1"), s.ctx)
    with pytest.raises(DomainError) as caught:
        await RegisteredContextReader(s.inputs).read(s.runs.original.ref, "latest_required", s.ctx)
    assert caught.value.failure.code == "capability_unavailable"


async def test_run_model_and_source_set_changes_after_read_fail():
    s = setup()
    old = s.runs.read

    async def changed(pin, policy, ctx):
        result = await old(pin, policy, ctx)
        before = s.records.rows[("run.bindings", "run")]
        s.records.rows[("run.bindings", "run")] = replace(before, revision=2)
        return result

    s.runs.read = changed
    with pytest.raises(DomainError) as caught:
        await s.inputs.current(s.ctx)
    assert caught.value.failure.code == "source_changed"


@pytest.mark.parametrize(
    "text", ["", "x" * 65537, "材" * 22000], ids=["empty", "ascii-limit", "utf8-limit"]
)
async def test_invalid_rule_text_is_rejected_before_blob_write(text):
    s = setup()
    # A caller can construct an invalid internal object without Pydantic validation.
    # Registration must revalidate it before any blob/SQL write.
    value = InstructionRule.model_construct(
        id="rule",
        source_ref=Ref(kind="rule", id="rule", version="1"),
        level="platform",
        scope=ScopeSelector(conversation_id=s.ctx.scope.conversation_id),
        text=text,
    )
    with pytest.raises(ValueError):
        await s.inputs.register_rule(
            value, s.ctx, authenticated_service=s.controller, expected_revision=0, meta=meta()
        )
    assert s.blobs.calls == 0


async def test_actual_input_set_capacity_is_bounded_before_reading():
    s = setup()
    row = s.records.rows[("run.input_sets", "run")]
    s.records.rows[("run.input_sets", "run")] = replace(
        row, payload={**row.payload, "patch_refs": [s.runs.original.ref.wire()] * 64}
    )
    with pytest.raises(DomainError) as caught:
        await s.inputs.current(s.ctx)
    assert caught.value.status_code == 413
