"""Real evaluation persistence/Model/budget with controlled HTTP, not LLM quality."""

import json

import httpx
import pytest

from tests.integration.agent.conftest import agent_case as agent_case
from tests.integration.model.test_gateway import reply
from uaw.context.contracts import RuleCandidate
from uaw.model.evaluation_inputs import (
    EVALUATIONS,
    RULE_SCHEMA,
    EvaluationSource,
    FixedModelEvaluator,
    FixedModelRuleAssessor,
)
from uaw.shared.errors import DomainError

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary"],
    "properties": {"summary": {"type": "string"}},
}


def evaluator(p):
    return FixedModelEvaluator(p.model_case.model.gateway, p.assembly.sources)


def response(data):
    return httpx.Response(200, json=reply(json.dumps(data)))


async def test_fixed_model_evaluation_is_persisted_and_replays_original_attempt(agent_case):
    p = agent_case
    e = evaluator(p)
    p.model_case.responses[:] = [response({"summary": "actual bounded assessment"})]
    result = await e.evaluate(
        "semantic", "Return summary as JSON.", {"text": "office"}, SCHEMA, p.ctx
    )
    assert result.data["summary"] == "actual bounded assessment"
    assert (
        result.output["actual_config"]["model_id"]
        == p.model_case.request["model_config"]["model_id"]
    )
    saved = await p.control.records.get(p.ctx.principal, EVALUATIONS, result.context.operation_id)
    assert saved.payload["frame_ref"]["version"] == p.start["task_frame_ref"]["version"]
    native = json.loads(p.model_case.requests[-1].content)
    assert native["messages"][0]["content"] == "Return summary as JSON."
    assert native.get("tools", []) == []
    assert (
        await e.evaluate("semantic", "Return summary as JSON.", {"text": "office"}, SCHEMA, p.ctx)
        == result
    )
    assert len(p.model_case.requests) == 1
    with pytest.raises(DomainError, match="Original evaluation input changed"):
        await e.evaluate("semantic", "changed", {"text": "office"}, SCHEMA, p.ctx)
    assert len(p.model_case.requests) == 1


async def test_rule_assessment_uses_actual_rows_and_preserves_fixed_candidates(agent_case):
    p = agent_case
    role = await p.control.tool_access._role(p.role)
    from uaw.context.contracts import InstructionRule, from_wire
    from uaw.shared.contracts import Ref

    ref = Ref.model_validate(role["instructions_ref"])
    row = await p.control.records.get(p.ctx.principal, "context.registered.rules", ref.id)
    candidate = RuleCandidate(from_wire(InstructionRule, row.payload), order=3)
    data = {
        "rules": [
            {
                "id": candidate.rule.id,
                "topic": None,
                "value": None,
                "critical": True,
                "supersedes": [],
            }
        ],
        "conflict_ids": [],
    }
    p.model_case.responses[:] = [response(data)]
    plan = await FixedModelRuleAssessor(evaluator(p)).assess((candidate,), p.ctx)
    assert plan.assessment_complete
    assert plan.candidates[0].rule == candidate.rule and plan.candidates[0].order == 3
    assert len(p.model_case.requests) == 1
    assert json.loads(p.model_case.requests[0].content)["response_format"]


async def test_stale_source_denied_before_provider(agent_case):
    p = agent_case
    e = evaluator(p)
    from uaw.shared.contracts import Ref

    pin = Ref.model_validate({**p.role.wire(), "version": "999"})
    with pytest.raises(DomainError):
        await e.evaluate(
            "source",
            "Return summary JSON.",
            {},
            SCHEMA,
            p.ctx,
            sources=(EvaluationSource("roles", pin, "RoleProfile"),),
        )
    assert not p.model_case.requests


async def test_evaluation_bounds_denied_without_sending(agent_case):
    p = agent_case
    with pytest.raises(DomainError, match="96 KiB"):
        await evaluator(p).evaluate(
            "large", "Return summary JSON.", {"text": "x" * 98304}, SCHEMA, p.ctx
        )
    assert not p.model_case.requests


async def test_foreign_session_cannot_resolve_original_evaluation(agent_case):
    p = agent_case
    e = evaluator(p)
    p.model_case.responses[:] = [response({"summary": "ok"})]
    result = await e.evaluate("private", "Return summary JSON.", {}, SCHEMA, p.ctx)
    spoof = result.context.model_copy(
        update={
            "principal": result.context.principal.model_copy(update={"auth_session_id": "foreign"})
        }
    )
    with pytest.raises(DomainError, match="another context"):
        await e.inputs.guard(spoof)


@pytest.mark.parametrize(
    "data",
    [
        {"rules": [], "conflict_ids": ["invented"]},
        {
            "rules": [
                {"id": "invented", "topic": None, "value": None, "critical": True, "supersedes": []}
            ],
            "conflict_ids": [],
        },
    ],
)
async def test_malformed_semantic_identity_does_not_create_rule_authority(agent_case, data):
    p = agent_case
    from uaw.context.contracts import InstructionRule, from_wire

    role = await p.control.tool_access._role(p.role)
    row = await p.control.records.get(
        p.ctx.principal, "context.registered.rules", role["instructions_ref"]["id"]
    )
    candidate = RuleCandidate(from_wire(InstructionRule, row.payload))
    p.model_case.responses[:] = [response(data)]
    with pytest.raises(DomainError):
        await FixedModelRuleAssessor(evaluator(p)).assess((candidate,), p.ctx)
    assert len(p.model_case.requests) == 1
    assert (await p.control.records.get(p.ctx.principal, row.namespace, row.resource_id)) == row


async def test_evaluation_json_schema_is_checked_by_gateway(agent_case):
    p = agent_case
    p.model_case.responses[:] = [response({"unexpected": True})]
    with pytest.raises(DomainError):
        await evaluator(p).evaluate("bad-json", "Return rules JSON.", {}, RULE_SCHEMA, p.ctx)
    assert len(p.model_case.requests) == 1
