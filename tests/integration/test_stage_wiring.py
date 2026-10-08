"""Registered Context and actual text response with A current SQL authorization.

Provider connection metadata/model replies are controlled; no external LLM,
native approval or IPC is claimed. Stage response storage is not ToolResult.
"""

import json

import pytest

from tests.integration.intent.test_understanding import understanding as understanding
from tests.integration.model.test_gateway import case as case
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.test_runtime_sources import profile
from tests.integration.tool.conftest import tool_case as tool_case
from uaw.composition import (
    Container,
    RuntimeBindings,
    assemble_registered_context,
    assemble_text_tool,
)
from uaw.context.contracts import ContextRequest, ModelToolSet, PreservationSpec, RulesRequest
from uaw.infrastructure.blob.filesystem import FSBlobStore
from uaw.model.input_router import ContextModelInputs
from uaw.run.budget import BudgetService
from uaw.run.context_sources import RegisteredToolSetValidator
from uaw.run.execution_sources import RunExecutionSources
from uaw.run.permissions import ExecutionPolicyResolver
from uaw.run.tool_sources import RunToolAccessSources
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import DomainError
from uaw.shared.settings import Settings
from uaw.tool.providers.text import inspect_text, text_spec
from uaw.tool.registry import AdapterBinding, ToolRegistry


def container(records, config, tmp_path):
    policies = ExecutionPolicyResolver(records)
    runs = RunExecutionSources(records, config, policies)
    return Container(
        settings=Settings(profile="development", development_principal_id="assembly-user"),
        bindings=RuntimeBindings(),
        records=records,
        configuration=config,
        blobs=FSBlobStore(tmp_path / "private-blobs"),
        execution_permissions=policies,
        run_sources=runs,
        budgets=BudgetService(records),
        tool_access=RunToolAccessSources(records, config, runs, environment="development"),
    )


async def test_registered_context_routes_to_model_input_and_rechecks_material(
    understanding, case, domain, tmp_path
):
    config, run, _ = domain
    admission = (await run.store.get(case.ctx.principal, "run.bindings", case.ctx.run_id)).payload
    ctx = understanding.ctx.model_copy(
        update={
            "operation_id": "context-register-material",
            "model_policy_ref": Ref.model_validate(admission["model_policy_ref"]),
        }
    )
    control = container(run.store, config, tmp_path)
    assembled = assemble_registered_context(control)
    text = "部门,预算,已用\n研发,1200.50,900.40\n忽略指令属于材料正文，不授权工具。"
    material = await assembled.inputs.register_material(
        text,
        ctx,
        authenticated_service=config.platform,
        expected_revision=0,
        meta=meta("material", 0),
    )
    request = ContextRequest(
        purpose="agent_step",
        source_refs=(material,),
        model_policy_ref=ctx.model_policy_ref,
        output_reserve=128,
        tool_reserve=64,
        expected_epoch=0,
        preserve=PreservationSpec(
            required_refs=(), exact_strings=(), requirement_ids=(), pending_action_refs=()
        ),
    )
    await assembled.inputs.register_recipe(
        request,
        RulesRequest(scope_paths=(), user_instruction_refs=(), activated_skill_refs=()),
        ModelToolSet(run_id=ctx.run_id, tools=()),
        ctx,
        authenticated_service=config.platform,
        expected_revision=0,
        meta=meta("recipe", 0),
    )
    saved = await assembled.inputs.recipe(ctx)
    built = await assembled.components.build(saved.request.wire(), ctx)
    assert built["kind"] == "ok", built
    router = ContextModelInputs(run.store, case.inputs, assembled.model_inputs)
    prompt = await router.resolve(built["output_refs"][0], ctx)
    assert not prompt.tools
    material_messages = [
        json.loads(message["content"])
        for message in prompt.messages
        if message["role"] == "user" and message["content"].startswith('{"context_kind"')
    ]
    assert any(message["text"] == text for message in material_messages)
    assert not any(
        text in message["content"] for message in prompt.messages if message["role"] == "system"
    )
    await assembled.inputs.revoke(
        material,
        ctx,
        authenticated_service=config.platform,
        expected_revision=1,
        meta=meta("revoke-material", 1),
    )
    with pytest.raises(DomainError):
        await router.resolve(built["output_refs"][0], ctx)


async def test_actual_text_dispatch_uses_registered_role_and_current_recovery(tool_case, tmp_path):
    config, run, _ = tool_case.domain
    ctx = tool_case.ctx.model_copy(update={"attempt_id": "actual-text-attempt"})
    control = container(run.store, config, tmp_path)
    role = await control.tool_access.register_role(
        profile(["text"]),
        meta("actual-text-role", 0),
        authenticated_service=config.platform,
    )
    await control.tool_access.bind(
        ctx, role, meta("actual-text-role-binding", 0), authenticated_service=config.platform
    )
    registry = ToolRegistry()
    provider_ref = Ref.model_validate(tool_case.spec["provider_ref"])
    spec = text_spec(provider_ref)
    registry.register(
        spec,
        expected_revision=0,
        binding=AdapterBinding(provider_ref, frozenset({"development"}), implemented=True),
    )
    tool_ref = Ref.model_validate(registry.reference(registry.snapshot()[1][0]))
    await RegisteredToolSetValidator(registry, control.tool_access).check(
        ModelToolSet(run_id=ctx.run_id, tools=(spec,)), ctx
    )
    provider = Principal(
        id="internal-text-service", kind="service", auth_session_id="text-service-session"
    )
    assembled = assemble_text_tool(control, registry=registry, tool_ref=tool_ref, provider=provider)
    raw = {
        "tool_ref": tool_ref.wire(),
        "action_id": "actual-text-action",
        "arguments": {"text": "  实际文本\r\nKeep\u0301 exact  "},
    }
    waiting = await assembled.facade.invoke(raw, ctx)
    assert waiting["kind"] == "waiting", waiting
    assert await assembled.responses.ledger.get("tool.budget.reserved", ctx.attempt_id, ctx) is None
    record = await assembled.approvals.get(ctx.principal, waiting["wait_ref"]["id"])
    await assembled.approvals.decide(
        ctx.principal,
        {
            "approval_id": record["id"],
            "decision": {
                "decision": "approve_once",
                "expected_arguments_hash": record["arguments_hash"],
                "expected_resource_refs": record["resource_refs"],
                "reason": "actual test decision",
            },
        },
        meta("actual-text-approve", record["revision"]),
    )
    stage = await assembled.facade.invoke(raw, ctx)
    assert stage["kind"] == "ok", stage
    assert stage["payload"]["status"] == "succeeded"
    assert stage["payload"]["effect_state"] == "confirmed"
    receipt = await assembled.responses.provider_receipt(ctx)
    output = await assembled.responses.read_raw(Ref.model_validate(receipt["raw_result_ref"]), ctx)
    assert output == inspect_text(raw["arguments"]["text"])
    assert (await assembled.ledger.effect_from_attempt(ctx))["state"] == "confirmed"
    assert await assembled.facade.invoke(raw, ctx) == stage
    await run.control(
        ctx.principal,
        {
            "run_id": ctx.run_id,
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "stop new actions"},
        },
        meta("cancel-actual-text", 2),
    )
    assert (
        await assembled.responses.read_raw(Ref.model_validate(receipt["raw_result_ref"]), ctx)
        == output
    )
    assert await assembled.results.read_result(raw["action_id"], ctx) == stage
    await control.tool_access.revoke(
        ctx, meta("revoke-actual-text-data", 1), authenticated_service=config.platform
    )
    with pytest.raises(DomainError):
        await assembled.responses.read_raw(Ref.model_validate(receipt["raw_result_ref"]), ctx)
