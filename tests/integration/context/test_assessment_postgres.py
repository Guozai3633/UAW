"""MS-C6 actual PostgreSQL/FS reads; controlled advice is not LLM evidence."""

from __future__ import annotations

import asyncio
from dataclasses import replace

import pytest

from tests.integration.context.test_registered_postgres import (
    case as case,
)
from tests.integration.context.test_registered_postgres import (
    domain as domain,
)
from tests.integration.context.test_registered_postgres import (
    material,
    recipe,
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
from uaw.context.contracts import RulePlan
from uaw.context.readers import RegisteredRuleProvider
from uaw.context.registered import TOOLS, recipe_id
from uaw.shared.errors import CapabilityUnavailable, DomainError
from uaw.shared.stores import StoreMissing


class ControlledAdvice:
    """Explicit semantic fixture; no text parsing, network or model quality claim."""

    def __init__(self, *, conflict=False, wait=False):
        self.calls = 0
        self.conflict = conflict
        self.wait = wait
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def assess(self, candidates, ctx):
        self.calls += 1
        self.started.set()
        if self.wait:
            await self.release.wait()
        return RulePlan(
            tuple(replace(c, topic="format", value="plain", critical=True) for c in candidates),
            conflict_refs=tuple(c.rule.source_ref for c in candidates) if self.conflict else (),
            assessment_complete=True,
        )


async def setup(s, *, wait=False, conflict=False):
    mat = await material(s)
    pins = tuple(
        [
            await register_rule(
                s,
                rule(s, id=f"format-{i}", text=text, level="user_current"),
                name=f"register-format-{i}",
            )
            for i, text in enumerate(
                ("Use plain sentences.", "Preserve user requirements and citations.")
            )
        ]
    )
    saved, ref = await recipe(s, (mat,), pins)
    assessor = ControlledAdvice(wait=wait, conflict=conflict)
    provider = RegisteredRuleProvider(s.inputs, assessor=assessor)
    s.components.rules.provider = provider
    return mat, pins, saved, ref, assessor, provider


async def test_sql_stage_fixed_candidates_and_old_constructor(registration):
    s = registration
    _, pins, saved, _, assessor, provider = await setup(s)
    plan = await provider.discover(saved.rules, s.ctx)
    assert tuple(c.rule.source_ref for c in plan.candidates) == pins
    assert [c.rule.text for c in plan.candidates] == [
        "Use plain sentences.",
        "Preserve user requirements and citations.",
    ]
    assert assessor.calls == 1 and plan.assessment_complete
    with pytest.raises(CapabilityUnavailable):
        await RegisteredRuleProvider(s.inputs).discover(saved.rules, s.ctx)


async def test_sql_stage_semantic_conflict_has_exact_registered_evidence(registration):
    s = registration
    _, pins, saved, _, _, _ = await setup(s, conflict=True)
    with pytest.raises(DomainError) as caught:
        await s.components.rules.assemble(saved.rules, s.ctx)
    assert (
        caught.value.failure.code == "rule_conflict" and caught.value.failure.evidence_refs == pins
    )


@pytest.mark.parametrize(
    "change", ["rule-revision", "rule-revoke", "material-revoke", "recipe-epoch", "tools", "policy"]
)
async def test_sql_stage_wait_rechecks_current_sources(registration, change):
    s = registration
    mat, pins, saved, _, assessor, provider = await setup(s, wait=True)
    task = asyncio.create_task(provider.discover(saved.rules, s.ctx))
    await asyncio.wait_for(assessor.started.wait(), 30)
    try:
        if change == "rule-revision":
            await register_rule(
                s,
                rule(
                    s,
                    id="format-0",
                    text="Actual changed instruction.",
                    revision=1,
                    level="user_current",
                ),
                expected=1,
                name="revise-during-model",
            )
        elif change in ("rule-revoke", "material-revoke"):
            await s.inputs.revoke(
                pins[0] if change == "rule-revoke" else mat,
                s.ctx,
                authenticated_service=s.controller,
                expected_revision=1,
                meta=meta("revoke-during-model", 1),
            )
        elif change == "recipe-epoch":
            await recipe(s, (mat,), pins, expected=1, name="recipe-during-model")
        elif change == "tools":
            row = await s.records.get(s.ctx.principal, TOOLS, recipe_id(s.ctx))
            await s.records.put(
                s.ctx.principal,
                TOOLS,
                row.resource_id,
                row.schema_name,
                row.payload,
                expected_revision=row.revision,
                request_id="tools-during-model",
            )
        else:
            row = await s.records.get(
                s.ctx.principal, "execution.policies", s.ctx.capability_policy_ref.id
            )
            payload = dict(row.payload)
            payload["revision"] = row.revision + 1
            await s.records.put(
                s.ctx.principal,
                row.namespace,
                row.resource_id,
                row.schema_name,
                payload,
                expected_revision=row.revision,
                request_id="policy-during-model",
            )
    finally:
        assessor.release.set()
    with pytest.raises((DomainError, StoreMissing)):
        await task
