"""Rule ordering enforces origin/scope; it does not interpret arbitrary prose."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from uaw.context.contracts import (
    InstructionSet,
    RuleAssembly,
    RuleCandidate,
    RulesRequest,
    digest,
    from_wire,
    matches_pin,
    ref_key,
)
from uaw.context.ports import RuleProvider
from uaw.context.sources import SourceResolver, component_result
from uaw.shared.contracts import Failure, Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, DomainError, reject
from uaw.shared.schema import validate_contract

# ARCHITECTURE section 14. Policy constraints remain enforced by owning runtimes.
PRIORITY = {
    "platform": 0,
    "capability_policy": 1,
    "user_current": 2,
    "project": 3,
    "skill": 4,
    "role": 5,
    "user_preference": 6,
}
ALLOWED_TRUST = {
    "platform": {"platform"},
    "capability_policy": {"platform"},
    "user_current": {"user"},
    "project": {"project"},
    "skill": {"user", "project", "platform"},
    "role": {"user", "project", "platform"},
    "user_preference": {"user"},
}


def in_scope(candidate: RuleCandidate, request: RulesRequest, ctx: TrustedExecutionContext) -> bool:
    scope = candidate.rule.scope
    for name in ("conversation_id", "task_id", "project_id"):
        value = getattr(scope, name)
        if value is not None and value != getattr(ctx.scope, name):
            return False
    allowed = {ref_key(ref) for ref in ctx.scope.resource_refs}
    if any(ref_key(ref) not in allowed for ref in scope.resource_refs):
        return False
    targets = {ref_key(ref) for ref in candidate.target_refs}
    if candidate.rule.level == "project":
        # The provider proves ancestry and maps each registered rule to a target.
        return (
            bool(targets)
            and bool(request.scope_paths)
            and all(ref_key(ref) in targets for ref in request.scope_paths)
        )
    return not targets or all(ref_key(ref) in targets for ref in request.scope_paths)


def conflict(message: str, refs: tuple[Ref, ...]) -> DomainError:
    return DomainError(
        Failure(
            code="rule_conflict",
            category="conflict",
            message=message,
            retryable=False,
            failed_phase="rule_resolution",
            evidence_refs=refs,
            recover_hint="Clarify important requirements using the fixed model or user input",
        ),
        status_code=409,
    )


class RuleResolver:
    def __init__(self, sources: SourceResolver, provider: RuleProvider | None) -> None:
        self.sources = sources
        self.provider = provider

    async def resolve(self, request: RulesRequest, ctx: TrustedExecutionContext) -> InstructionSet:
        return (await self.assemble(request, ctx)).instructions

    async def assemble(self, request: RulesRequest, ctx: TrustedExecutionContext) -> RuleAssembly:
        await self.sources.guard.check(ctx)
        if self.provider is None:
            raise CapabilityUnavailable("context.rule_provider")
        if len(request.scope_paths) > 1:
            raise CapabilityUnavailable("context.rules.multi_target_partition")
        for ref in request.scope_paths:
            await self.sources.recheck(ref, ctx)
        plan = await self.provider.discover(request, ctx)
        await self.sources.guard.check(ctx)
        if not plan.assessment_complete:
            raise CapabilityUnavailable("context.rules.conflict_assessment")
        candidates = [c for c in plan.candidates if in_scope(c, request, ctx)]
        if len({c.rule.id for c in candidates}) != len(candidates):
            raise reject("rule_conflict", "Duplicate rule identity", 409, "conflict")
        registered = tuple(c.rule.source_ref for c in candidates)
        for requested in (*request.user_instruction_refs, *request.activated_skill_refs):
            if not any(matches_pin(requested, actual) for actual in registered):
                raise reject(
                    "dependency_missing",
                    "A requested instruction source was not registered",
                    404,
                    "dependency",
                )
        fixed: list[RuleCandidate] = []
        for candidate in candidates:
            rule = candidate.rule
            if rule.level in ("user_current", "user_preference"):
                if not any(
                    matches_pin(ref, rule.source_ref) for ref in request.user_instruction_refs
                ):
                    raise reject("permission_denied", "User rule was not requested", 403)
            if rule.level == "skill" and not any(
                matches_pin(ref, rule.source_ref) for ref in request.activated_skill_refs
            ):
                raise reject("permission_denied", "Skill is not activated", 403)
            reading = await self.sources.read(rule.source_ref, "pinned", ctx)
            if reading.trust not in ALLOWED_TRUST[rule.level] or reading.kind not in (
                "instruction",
                "user_input",
                "skill",
            ):
                raise reject("permission_denied", "Unregistered data cannot become a rule", 403)
            if reading.text != rule.text:
                raise reject("source_changed", "Rule text differs from its actual source", 410)
            if (candidate.topic is None) != (candidate.value is None) or candidate.order < 0:
                raise reject("schema_invalid", "Incomplete trusted rule metadata")
            fixed.append(
                replace(candidate, rule=rule.model_copy(update={"source_ref": reading.ref}))
            )
        candidates = fixed

        if plan.conflict_refs:
            actual_refs = tuple(
                [(await self.sources.read(ref, "pinned", ctx)).ref for ref in plan.conflict_refs]
            )
            raise conflict("Important rules require clarification", actual_refs)

        ids = {candidate.rule.id for candidate in candidates}
        if any(set(c.supersedes) - ids for c in candidates):
            raise reject("schema_invalid", "An explicit rule override has no registered target")
        # More specific/later correction wins within a layer; input order breaks ties.
        ranked = sorted(candidates, key=lambda c: (PRIORITY[c.rule.level], -c.order))
        chosen: list[RuleCandidate] = []
        overrides: list[tuple[Ref, Ref]] = []
        topics: dict[str, RuleCandidate] = {}
        for candidate in ranked:
            if candidate.topic is not None:
                previous = topics.get(candidate.topic)
                if previous is not None:
                    correction = (
                        candidate.rule.id in previous.supersedes
                        and previous.rule.level == candidate.rule.level == "user_current"
                        and previous.order > candidate.order
                    )
                    if (
                        previous.value != candidate.value
                        and (previous.critical or candidate.critical)
                        and not correction
                    ):
                        raise conflict(
                            "Important requirements conflict",
                            (previous.rule.source_ref, candidate.rule.source_ref),
                        )
                    overrides.append((candidate.rule.source_ref, previous.rule.source_ref))
                    continue
                topics[candidate.topic] = candidate
            chosen.append(candidate)
        # All dependencies, including overridden rules, stay currently authorized.
        for candidate in candidates:
            await self.sources.recheck(candidate.rule.source_ref, ctx)
        for ref in request.scope_paths:
            await self.sources.recheck(ref, ctx)
        # Preserve deterministic ordering and all source versions in the set's version.
        version = digest(
            {
                "request": request.wire(),
                "scope": ctx.scope.wire(),
                "capability_policy_ref": ctx.capability_policy_ref.wire(),
                "candidates": [
                    {
                        "rule": c.rule.wire(),
                        "order": c.order,
                        "topic": c.topic,
                        "value": c.value,
                        "critical": c.critical,
                        "supersedes": c.supersedes,
                        "targets": [ref.wire() for ref in c.target_refs],
                    }
                    for c in candidates
                ],
            }
        )
        dependencies = tuple(
            {
                ref_key(ref): ref
                for ref in (*(c.rule.source_ref for c in candidates), *request.scope_paths)
            }.values()
        )
        if len(dependencies) > 256:
            raise reject("context_insufficient", "Too many rule dependencies", 422, "budget")
        assembly = RuleAssembly(
            instructions=InstructionSet(
                rules=tuple(c.rule for c in chosen), conflict_refs=(), version=version
            ),
            dependencies=dependencies,
            overrides=tuple(overrides),
        )
        validate_contract("Manifest", assembly.manifest())
        return assembly

    async def handle(self, request: dict[str, Any], ctx: TrustedExecutionContext) -> dict[str, Any]:
        async def operation() -> dict[str, Any]:
            instructions = await self.resolve(from_wire(RulesRequest, request), ctx)
            return {"kind": "ok", "payload": instructions.wire(), "output_refs": []}

        return await component_result(
            "ComponentContextRulesResult", ctx, self.sources.guard, operation
        )
