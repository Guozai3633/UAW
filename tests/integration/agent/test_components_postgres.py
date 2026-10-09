"""Current SQL component assembly; HTTP and numeric embeddings are controlled."""

import json

import pytest

from tests.integration.agent.conftest import agent_case as agent_case
from tests.integration.agent.test_root_postgres import decision, request, start
from tests.integration.context.test_assessment_postgres import ControlledAdvice
from tests.integration.test_control_plane import meta
from tests.unit.tool.test_retrieval import NumericalEmbedding
from uaw.composition import assemble_registered_context
from uaw.context.contracts import (
    ContextRequest,
    InstructionRule,
    ModelToolSet,
    PreservationSpec,
    RulesRequest,
)
from uaw.shared.contracts import Ref, ScopeSelector
from uaw.tool.index import SQLiteVectorIndex
from uaw.tool.retrieval import ToolRetriever

pytestmark = pytest.mark.parametrize(
    "case",
    [{"active_provider_for_tools": True, "json_object_mode": True}],
    indirect=True,
)


async def test_assembled_multirule_context_keeps_actual_rules_and_fixed_input(agent_case):
    p = agent_case
    assessor = ControlledAdvice()
    wired = assemble_registered_context(
        p.control,
        registry=p.assembly.runtime.loop.contexts.registry,
        rule_assessor=assessor,
    )
    pins = []
    for i, text in enumerate(("Preserve original user requirements.", "Quote actual sources.")):
        pins.append(
            await wired.inputs.register_rule(
                InstructionRule(
                    id=f"i2h-rule-{i}",
                    source_ref=Ref(kind="rule", id=f"i2h-rule-{i}", version="1"),
                    level="user_current",
                    text=text,
                    scope=ScopeSelector(conversation_id=p.ctx.scope.conversation_id),
                ),
                p.ctx,
                authenticated_service=p.domain[0].platform,
                expected_revision=0,
                meta=meta(f"i2h-rule-{i}", 0),
            )
        )
    await wired.inputs.register_recipe(
        ContextRequest(
            purpose="agent_step",
            source_refs=(),
            model_policy_ref=p.ctx.model_policy_ref,
            output_reserve=128,
            tool_reserve=64,
            expected_epoch=0,
            preserve=PreservationSpec(
                required_refs=(),
                exact_strings=(),
                requirement_ids=(),
                pending_action_refs=(),
            ),
        ),
        RulesRequest(scope_paths=(), user_instruction_refs=tuple(pins), activated_skill_refs=()),
        ModelToolSet(run_id=p.ctx.run_id, tools=()),
        p.ctx,
        authenticated_service=p.domain[0].platform,
        expected_revision=0,
        meta=meta("i2h-multirule-recipe", 0),
    )
    saved = await wired.inputs.recipe(p.ctx)
    result = await wired.components.build(saved.request.wire(), p.ctx)
    assert result["kind"] == "ok", result
    prompt = await wired.model_inputs.resolve(result["output_refs"][0], p.ctx)
    assert "Preserve original user requirements." in str(prompt.messages)
    assert "Quote actual sources." in str(prompt.messages) and assessor.calls >= 2
    assert not p.model_case.requests  # Controlled advice is not LLM acceptance.


async def test_root_retrieval_json_object_keeps_user_model_and_budget(agent_case, tmp_path):
    p = agent_case
    adapter = p.assembly.runtime.loop.contexts
    embeddings = NumericalEmbedding()
    adapter.retriever = ToolRetriever(
        adapter.registry,
        p.control.tool_access,
        embeddings=embeddings,
        index=SQLiteVectorIndex(tmp_path / "actual-cache.sqlite"),
    )
    root = await start(p)
    raw, ctx = await request(p, root)
    p.model_case.responses[:] = [decision("respond", "Current retrieved tool set was supplied")]
    result = await p.assembly.runtime.step(raw, ctx)
    assert result["kind"] == "ok", result
    native = json.loads(p.model_case.requests[-1].content)
    assert native["model"] == "fixture-model"
    assert native["response_format"] == {"type": "json_object"}
    assert native["reasoning_effort"] == "none" and "n" not in native
    assert "text.inspect" in str(native["messages"])
    assert len(embeddings.requests) == 1 and len(p.model_case.requests) == 1
    assert (await p.domain[1].get_run(ctx.principal, ctx.run_id))["status"] != "completed"
