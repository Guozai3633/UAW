"""MS-C6 advice validation; assessors here are controlled, never LLM quality evidence."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from tests.unit.context.test_components import FixtureReader, context, reading
from uaw.context.contracts import InstructionRule, RuleCandidate, RulePlan, RulesRequest
from uaw.context.readers import RegisteredRuleProvider, assessed_plan
from uaw.context.rules import RuleResolver
from uaw.context.sources import Guard, SourceResolver
from uaw.shared.contracts import Ref, ScopeSelector
from uaw.shared.errors import CapabilityUnavailable, DomainError, reject


def candidates(levels=("user_current", "user_current")):
    return tuple(
        RuleCandidate(
            InstructionRule(
                id=f"rule-{i}",
                source_ref=Ref(kind="rule", id=f"rule-{i}", version="1", content_hash=str(i) * 64),
                text=f"Actual instruction {i}",
                level=level,
                scope=ScopeSelector(conversation_id="conversation"),
            ),
            order=i,
        )
        for i, level in enumerate(levels)
    )


def plan(fixed, **kwargs):
    return RulePlan(
        tuple(replace(c, topic="answer", value="plain", critical=True) for c in fixed),
        assessment_complete=True,
        **kwargs,
    )


def test_valid_plan_canonical_identity_and_copied_refs():
    fixed = candidates()
    result = assessed_plan(
        fixed, replace(plan(fixed), candidates=tuple(reversed(plan(fixed).candidates)))
    )
    assert result == plan(fixed)
    assert result.candidates[0].rule is not fixed[0].rule
    fixed[0].rule.source_ref.__dict__["version"] = "2"
    assert result.candidates[0].rule.source_ref.version == "1"


@pytest.mark.parametrize(
    "field,value",
    [
        ("text", "invented"),
        ("level", "platform"),
        ("scope", ScopeSelector(conversation_id="foreign")),
        ("id", "unknown"),
        ("source_ref", Ref(kind="rule", id="rule-0", version="2")),
    ],
)
def test_assessor_cannot_change_registered_rule(field, value):
    fixed = candidates()
    changed = replace(
        plan(fixed).candidates[0], rule=fixed[0].rule.model_copy(update={field: value})
    )
    with pytest.raises(DomainError) as caught:
        assessed_plan(fixed, replace(plan(fixed), candidates=(changed, plan(fixed).candidates[1])))
    assert caught.value.failure.code == "context_assessment_identity_conflict"


@pytest.mark.parametrize(
    "field,value",
    [
        ("order", 9),
        ("order", True),
        ("target_refs", (Ref(kind="content", id="foreign", version="1"),)),
        ("critical", "yes"),
        ("topic", ""),
        ("topic", "x" * 4097),
        ("topic", None),
        ("supersedes", ("foreign",)),
        ("supersedes", ("rule-1",)),
        ("supersedes", ["rule-0"]),
    ],
)
def test_invalid_semantic_metadata(field, value):
    fixed = candidates()
    changed = replace(plan(fixed).candidates[0], **{field: value})
    with pytest.raises(DomainError):
        assessed_plan(fixed, replace(plan(fixed), candidates=(changed, plan(fixed).candidates[1])))


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        {},
        RulePlan((), assessment_complete=True),
        RulePlan(candidates(), assessment_complete=False),
        RulePlan((candidates()[0], candidates()[0]), assessment_complete=True),
    ],
)
def test_bad_incomplete_duplicate_plan(invalid):
    with pytest.raises((DomainError, CapabilityUnavailable)):
        assessed_plan(candidates(), invalid)


@pytest.mark.parametrize(
    "refs",
    [
        (Ref(kind="rule", id="foreign", version="1"),),
        (candidates()[0].rule.source_ref.model_copy(update={"content_hash": None}),),
        (candidates()[0].rule.source_ref, candidates()[0].rule.source_ref),
    ],
)
def test_conflict_refs_must_be_unique_exact_candidates(refs):
    with pytest.raises(DomainError) as caught:
        assessed_plan(candidates(), plan(candidates(), conflict_refs=refs))
    assert caught.value.failure.code == "context_assessment_reference_conflict"


def test_explicit_later_user_correction_and_cross_topic_rejection():
    fixed = candidates()
    advice = plan(fixed)
    correction = replace(advice.candidates[1], value="bullets", supersedes=("rule-0",))
    assert assessed_plan(
        fixed, replace(advice, candidates=(advice.candidates[0], correction))
    ).candidates[1].supersedes == ("rule-0",)
    with pytest.raises(DomainError):
        assessed_plan(
            fixed,
            replace(advice, candidates=(advice.candidates[0], replace(correction, topic="other"))),
        )


@pytest.mark.parametrize(
    "levels", [("platform", "user_current"), ("capability_policy", "user_current")]
)
def test_policy_cannot_be_downgraded_or_superseded(levels):
    fixed = candidates(levels)
    advice = plan(fixed)
    for bad in (
        replace(advice.candidates[0], critical=False),
        replace(advice.candidates[1], supersedes=("rule-0",)),
    ):
        changed = list(advice.candidates)
        changed[bad.order] = bad
        with pytest.raises(DomainError):
            assessed_plan(fixed, replace(advice, candidates=tuple(changed)))


class ControlledInputs:
    def __init__(self):
        self.ctx = context()
        self.fixed = candidates()
        self.request = RulesRequest(
            scope_paths=(),
            user_instruction_refs=tuple(c.rule.source_ref for c in self.fixed),
            activated_skill_refs=(),
        )
        self.recipe_value = SimpleNamespace(
            rules=self.request,
            request=SimpleNamespace(source_refs=(Ref(kind="input", id="original", version="1"),)),
        )
        self.records = self
        self.denied = False
        self.generation = 0
        self.calls = 0

    async def recipe(self, ctx):
        if self.denied:
            raise reject("permission_denied", "Controlled current authority denial", 403)
        return SimpleNamespace(
            rules=self.request, request=self.recipe_value.request, generation=self.generation
        )

    async def inspect(self, ctx):
        saved = await self.recipe(ctx)
        for pin in (*saved.request.source_refs, *saved.rules.user_instruction_refs):
            await self.read(pin, ctx)
        return saved, await self.current(ctx)

    async def current(self, ctx):
        return self.recipe_value.request.source_refs

    async def read(self, pin, ctx):
        await Guard(SimpleNamespace(is_cancelled=self.cancelled)).check(ctx)
        if self.denied:
            raise reject("permission_denied", "Controlled Reader denial", 403)
        self.calls += 1
        for c in self.fixed:
            if c.rule.source_ref == pin:
                return SimpleNamespace(ref=pin, text=c.rule.text)
        return SimpleNamespace(ref=pin, text="original")

    async def cancelled(self, ctx):
        return False

    async def get(self, principal, namespace, identifier):
        return SimpleNamespace(
            schema_name="InstructionRule",
            payload=next(c.rule.wire() for c in self.fixed if c.rule.id == identifier),
        )


class ControlledAssessor:
    def __init__(self, callback=None):
        self.callback = callback
        self.started = asyncio.Event()
        self.calls = 0

    async def assess(self, fixed, ctx):
        self.calls += 1
        self.started.set()
        if self.callback:
            await self.callback(fixed, ctx)
        return plan(fixed)


async def test_optional_assessor_missing_multiple_unavailable():
    s = ControlledInputs()
    with pytest.raises(CapabilityUnavailable):
        await RegisteredRuleProvider(s).discover(s.request, s.ctx)
    assert s.calls == 0


@pytest.mark.parametrize("change", ["authority", "recipe", "rule", "context", "mutation"])
async def test_wait_boundary_cannot_return_changed_sources_or_identity(change):
    s = ControlledInputs()

    async def alter(fixed, ctx):
        if change == "authority":
            s.denied = True
        if change == "recipe":
            s.generation += 1
        if change == "rule":
            s.fixed = (
                replace(s.fixed[0], rule=s.fixed[0].rule.model_copy(update={"text": "changed"})),
                s.fixed[1],
            )
        if change == "context":
            ctx.__dict__["run_id"] = "foreign"
        if change == "mutation":
            fixed[0].rule.__dict__["text"] = "changed"

    with pytest.raises(DomainError):
        await RegisteredRuleProvider(s, assessor=ControlledAssessor(alter)).discover(
            s.request, s.ctx
        )


async def test_deadline_and_task_cancel_stalled_assessor():
    s = ControlledInputs()

    async def stall(fixed, ctx):
        await asyncio.Event().wait()

    assessor = ControlledAssessor(stall)
    short = s.ctx.model_copy(
        update={"deadline": (datetime.now(UTC) + timedelta(milliseconds=70)).isoformat()}
    )
    with pytest.raises(DomainError) as caught:
        await RegisteredRuleProvider(s, assessor=assessor).discover(s.request, short)
    assert caught.value.failure.code == "deadline_exceeded"
    assessor = ControlledAssessor(stall)
    task = asyncio.create_task(
        RegisteredRuleProvider(s, assessor=assessor).discover(s.request, s.ctx)
    )
    await assessor.started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.parametrize(
    "mode", ["same-policy", "important-conflict", "later-correction", "priority"]
)
async def test_assessment_to_existing_resolver_semantics(mode):
    levels = (
        ("platform", "capability_policy")
        if mode == "same-policy"
        else (
            ("user_current", "user_preference")
            if mode == "priority"
            else ("user_current", "user_current")
        )
    )
    fixed = candidates(levels)
    reads = []
    for c in fixed:
        actual = reading(
            c.rule.text,
            id=c.rule.id,
            kind="instruction",
            trust="platform" if c.rule.level in ("platform", "capability_policy") else "user",
            required=True,
        )
        c.rule.__dict__["source_ref"] = actual.ref
        reads.append(actual)
    advice = plan(fixed)
    if mode != "same-policy":
        advice = replace(
            advice,
            candidates=(
                replace(advice.candidates[0], critical=mode != "priority"),
                replace(
                    advice.candidates[1],
                    value="bullets",
                    critical=mode != "priority",
                    supersedes=("rule-0",) if mode == "later-correction" else (),
                ),
            ),
        )

    class Provider:
        async def discover(self, request, ctx):
            return assessed_plan(fixed, advice)

    s = ControlledInputs()
    resolver = RuleResolver(
        SourceResolver(
            {"input": FixtureReader(*reads)}, Guard(SimpleNamespace(is_cancelled=s.cancelled))
        ),
        Provider(),
    )
    request = RulesRequest(
        scope_paths=(),
        user_instruction_refs=tuple(c.rule.source_ref for c in fixed),
        activated_skill_refs=(),
    )
    if mode == "important-conflict":
        with pytest.raises(DomainError) as caught:
            await resolver.assemble(request, context())
        assert caught.value.failure.evidence_refs == (
            fixed[1].rule.source_ref,
            fixed[0].rule.source_ref,
        )
    else:
        result = await resolver.assemble(request, context())
        assert len(result.dependencies) == 2
        assert len(result.instructions.rules) == (2 if mode == "same-policy" else 1)
        assert result.instructions.rules[0].id == (
            "rule-1" if mode == "later-correction" else "rule-0"
        )
