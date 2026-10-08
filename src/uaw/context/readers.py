"""Current registered sources; no fixture authority, cached Reading or ACL result."""

from __future__ import annotations

from uaw.context.contracts import Reading, RuleCandidate, RulePlan, RulesRequest, from_wire
from uaw.context.ports import RuleProvider
from uaw.context.registered import RULES, RegisteredContextInputs
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


class RegisteredRuleProvider(RuleProvider):
    """Only explicitly selected, registered rules. No invented semantic assessment.

    Empty/singleton instruction sets need no pairwise prose conflict assessment.
    Multiple registered rules remain unavailable until a real fixed-model assessor
    is supplied in a future package; they are never falsely marked assessed here.
    """

    def __init__(self, inputs: RegisteredContextInputs) -> None:
        self.inputs = inputs

    async def discover(self, request: RulesRequest, ctx: TrustedExecutionContext) -> RulePlan:
        recipe = await self.inputs.recipe(ctx)
        if request != recipe.rules:
            raise reject(
                "context_dependency_changed", "Rule selection differs from current recipe", 410
            )
        if request.scope_paths or request.activated_skill_refs:
            raise CapabilityUnavailable("context.registered_path_or_skill_rules")
        if len(request.user_instruction_refs) > 1:
            raise CapabilityUnavailable("context.rules.conflict_assessment")
        candidates = []
        for pin in request.user_instruction_refs:
            reading = await self.inputs.read(pin, ctx)
            row = await self.inputs.records.get(ctx.principal, RULES, pin.id)
            from uaw.context.contracts import InstructionRule

            rule = from_wire(InstructionRule, row.payload)
            if (
                row.schema_name != "InstructionRule"
                or rule.source_ref != reading.ref
                or rule.text != reading.text
            ):
                raise reject("source_changed", "Registered rule metadata changed", 410)
            candidates.append(RuleCandidate(rule))
        if await self.inputs.recipe(ctx) != recipe:
            raise reject("context_dependency_changed", "Rule recipe changed during read", 410)
        return RulePlan(tuple(candidates), assessment_complete=True)
