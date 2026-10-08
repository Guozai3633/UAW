"""Registered sources and bounded semantic advice, checked against live identity."""

from __future__ import annotations

import asyncio
import copy
from dataclasses import replace

from uaw.context.contracts import (
    InstructionRule,
    Reading,
    RuleCandidate,
    RulePlan,
    RulesRequest,
    digest,
    from_wire,
)
from uaw.context.ports import RegisteredRuleAssessor, RuleProvider
from uaw.context.registered import (
    MAX_ENTRIES,
    MAX_REQUEST_BYTES,
    RULES,
    RegisteredContextInputs,
    RegisteredRecipe,
    bounded,
)
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject


class RegisteredContextReader:
    def __init__(self, inputs: RegisteredContextInputs) -> None:
        self.inputs = inputs

    async def check(self, ref: Ref, ctx: TrustedExecutionContext) -> None:
        await self.inputs.read(ref, ctx)

    async def read(self, ref: Ref, revision_policy: str, ctx: TrustedExecutionContext) -> Reading:
        if revision_policy != "pinned":
            raise CapabilityUnavailable("context.registered_latest")
        return await self.inputs.read(ref, ctx)


def assessed_plan(candidates: tuple[RuleCandidate, ...], value: object) -> RulePlan:
    """Validate untrusted semantic advice and rebuild it from actual fixed rules."""
    if (
        type(value) is not RulePlan
        or type(value.assessment_complete) is not bool
        or type(value.candidates) is not tuple
        or type(value.conflict_refs) is not tuple
    ):
        raise reject("context_assessment_invalid", "Invalid semantic plan format", 422)
    if not value.assessment_complete:
        raise CapabilityUnavailable("context.rules.conflict_assessment")
    if len(value.candidates) != len(candidates):
        raise reject("context_assessment_incomplete", "Assessment must retain every candidate", 409)
    actual = {candidate.rule.id: candidate for candidate in candidates}
    proposed: dict[str, RuleCandidate] = {}
    metadata = []
    for candidate in value.candidates:
        if type(candidate) is not RuleCandidate or not isinstance(candidate.rule, InstructionRule):
            raise reject("context_assessment_invalid", "Invalid semantic candidate", 422)
        try:
            rule = from_wire(InstructionRule, candidate.rule.wire())
        except ValueError, TypeError:
            raise reject(
                "context_assessment_invalid", "Invalid candidate rule schema", 422
            ) from None
        original = actual.get(rule.id)
        if rule.id in proposed:
            raise reject("context_assessment_reference_conflict", "Repeated rule identity", 409)
        if (
            original is None
            or rule != original.rule
            or candidate.target_refs != original.target_refs
            or type(candidate.order) is not int
            or candidate.order != original.order
        ):
            raise reject(
                "context_assessment_identity_conflict", "Assessment changed rule identity", 403
            )
        if (
            type(candidate.critical) is not bool
            or (candidate.topic is None) != (candidate.value is None)
            or any(
                v is not None and (type(v) is not str or not v or len(v.encode("utf-8")) > 4096)
                for v in (candidate.topic, candidate.value)
            )
            or type(candidate.supersedes) is not tuple
            or len(candidate.supersedes) > MAX_ENTRIES
            or any(type(target) is not str for target in candidate.supersedes)
            or len(set(candidate.supersedes)) != len(candidate.supersedes)
        ):
            raise reject("context_assessment_invalid", "Invalid semantic metadata", 422)
        if rule.level in ("platform", "capability_policy") and not candidate.critical:
            raise reject("context_assessment_override_denied", "Policy rules remain protected", 403)
        for target in candidate.supersedes:
            prior = actual.get(target)
            if (
                prior is None
                or prior.rule.level != rule.level
                or rule.level != "user_current"
                or prior.order >= original.order
                or candidate.topic is None
            ):
                raise reject("context_assessment_override_denied", "Unsupported rule override", 403)
        proposed[rule.id] = candidate
        metadata.append(
            {
                "id": rule.id,
                "topic": candidate.topic,
                "value": candidate.value,
                "critical": candidate.critical,
                "supersedes": candidate.supersedes,
            }
        )
    if set(proposed) != set(actual):
        raise reject("context_assessment_incomplete", "Assessment omitted a fixed rule", 409)
    for candidate in proposed.values():
        if any(proposed[target].topic != candidate.topic for target in candidate.supersedes):
            raise reject(
                "context_assessment_override_denied", "Override changes semantic topic", 403
            )
    pins = {
        digest(candidate.rule.source_ref.wire()): candidate.rule.source_ref
        for candidate in candidates
    }
    seen = set()
    if len(value.conflict_refs) > MAX_ENTRIES:
        raise reject("context_assessment_invalid", "Too many semantic conflicts", 422)
    for pin in value.conflict_refs:
        if not isinstance(pin, Ref):
            raise reject("context_assessment_invalid", "Invalid conflict reference", 422)
        key = digest(pin.wire())
        if key not in pins or pin != pins[key] or key in seen:
            raise reject(
                "context_assessment_reference_conflict",
                "Conflict Ref is not a unique exact candidate",
                409,
            )
        seen.add(key)
    # Bound semantic text too, without serializing or retaining model/provider output.
    import json

    if len(json.dumps(metadata, ensure_ascii=False).encode("utf-8")) > MAX_REQUEST_BYTES:
        raise reject("context_assessment_invalid", "Assessment metadata exceeds bounds", 413)
    normalized = tuple(
        replace(
            original,
            rule=original.rule.model_copy(deep=True),
            topic=proposed[original.rule.id].topic,
            value=proposed[original.rule.id].value,
            critical=proposed[original.rule.id].critical,
            supersedes=proposed[original.rule.id].supersedes,
        )
        for original in candidates
    )
    return RulePlan(
        normalized, tuple(pin.model_copy(deep=True) for pin in value.conflict_refs), True
    )


class RegisteredRuleProvider(RuleProvider):
    """Actual fixed candidates; optional Model assessor provides only semantic advice."""

    def __init__(
        self, inputs: RegisteredContextInputs, *, assessor: RegisteredRuleAssessor | None = None
    ) -> None:
        self.inputs, self.assessor = inputs, assessor

    @bounded
    async def discover(self, request: RulesRequest, ctx: TrustedExecutionContext) -> RulePlan:
        recipe = await self.inputs.recipe(ctx)
        if request != recipe.rules:
            raise reject(
                "context_dependency_changed", "Rule selection differs from current recipe", 410
            )
        if request.scope_paths or request.activated_skill_refs:
            raise CapabilityUnavailable("context.registered_path_or_skill_rules")
        if len(request.user_instruction_refs) > MAX_ENTRIES:
            raise reject("context_assessment_invalid", "Too many fixed rule candidates", 413)
        if len(request.user_instruction_refs) > 1 and self.assessor is None:
            raise CapabilityUnavailable("context.rules.conflict_assessment")
        candidates = []
        seen_ids, seen_refs = set(), set()
        for order, pin in enumerate(request.user_instruction_refs):
            reading = await self.inputs.read(pin, ctx)
            row = await self.inputs.records.get(ctx.principal, RULES, pin.id)
            rule = from_wire(InstructionRule, row.payload)
            if (
                row.schema_name != "InstructionRule"
                or rule.source_ref != reading.ref
                or rule.text != reading.text
            ):
                raise reject("source_changed", "Registered rule metadata changed", 410)
            if rule.id in seen_ids or digest(rule.source_ref.wire()) in seen_refs:
                raise reject(
                    "context_assessment_reference_conflict", "Repeated registered candidate", 409
                )
            seen_ids.add(rule.id)
            seen_refs.add(digest(rule.source_ref.wire()))
            candidates.append(RuleCandidate(rule, order=order))
        fixed = tuple(candidates)
        await self._verify(recipe, fixed, ctx)
        if len(fixed) < 2:
            return RulePlan(fixed, assessment_complete=True)
        assert self.assessor is not None
        offered, offered_ctx = copy.deepcopy(fixed), ctx.model_copy(deep=True)
        try:
            assessed = await self.assessor.assess(offered, offered_ctx)
        except asyncio.CancelledError:
            raise
        except Exception:
            await self._verify(recipe, fixed, ctx)
            raise
        await self._verify(recipe, fixed, ctx)
        if offered != fixed or offered_ctx != ctx:
            raise reject("context_assessment_identity_conflict", "Assessor mutated its input", 403)
        return assessed_plan(fixed, assessed)

    async def _verify(
        self,
        recipe: RegisteredRecipe,
        candidates: tuple[RuleCandidate, ...],
        ctx: TrustedExecutionContext,
    ) -> None:
        current_recipe, _ = await self.inputs.inspect(ctx)
        if current_recipe != recipe:
            raise reject("context_dependency_changed", "Rule recipe changed during assessment", 410)
        for candidate in candidates:
            row = await self.inputs.records.get(ctx.principal, RULES, candidate.rule.source_ref.id)
            if (
                row.schema_name != "InstructionRule"
                or from_wire(InstructionRule, row.payload) != candidate.rule
            ):
                raise reject("source_changed", "Fixed rule changed during assessment", 410)
        if await self.inputs.recipe(ctx) != recipe:
            raise reject("context_dependency_changed", "Assessment final authority changed", 410)
