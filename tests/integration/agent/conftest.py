"""Actual A sources and SQL/Context/Model/Tool with controlled HTTP replies.

No production authentication, real LLM, IPC or native execution is represented.
"""

from importlib.resources import files
from types import SimpleNamespace

import pytest

from tests.integration.intent.test_understanding import understanding as understanding
from tests.integration.model.test_gateway import case as case
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.test_runtime_sources import profile
from tests.integration.test_stage_wiring import container
from uaw.agent.assembly import assemble_agent_runtime
from uaw.composition import assemble_registered_context, assemble_text_tool
from uaw.context.contracts import InstructionRule
from uaw.shared.contracts import Principal, Ref, ScopeSelector
from uaw.tool.providers.text import text_spec
from uaw.tool.registry import AdapterBinding, ToolRegistry


@pytest.fixture
async def agent_case(understanding, case, domain, tmp_path):
    configuration, run, _ = domain
    understood = await understanding.intent.understand(understanding.request, understanding.ctx)
    assert understood["kind"] == "ok", understood
    policy = await run.store.get(
        case.ctx.principal, "execution.policies", case.ctx.capability_policy_ref.id
    )
    capabilities = [
        "intent.understand",
        "agent.start",
        "agent.step",
        "model.generate",
        "context.build",
        "tool.invoke",
    ]
    await run.store.put(
        case.ctx.principal,
        policy.namespace,
        policy.resource_id,
        "CapabilityPolicy",
        {**policy.payload, "revision": policy.revision + 1, "allowed_capabilities": capabilities},
        expected_revision=policy.revision,
        request_id="agent-fixture-policy",
    )
    admission = (await run.store.get(case.ctx.principal, "run.bindings", case.ctx.run_id)).payload
    ctx = case.ctx.model_copy(
        update={
            "capability_policy_ref": Ref(
                kind="policy", id=policy.resource_id, version=str(policy.revision + 1)
            ),
            "scope": case.ctx.scope.model_copy(
                update={"capabilities": tuple(capabilities), "task_id": case.run["task_id"]}
            ),
            "task_id": case.run["task_id"],
            "model_policy_ref": Ref.model_validate(admission["model_policy_ref"]),
            "operation_id": "root-create",
            "trace_id": "root-trace",
            "attempt_id": "root-model-attempt",
        }
    )
    control = container(run.store, configuration, tmp_path)
    control.model_service = case.model
    registry = ToolRegistry()
    provider_ref = Ref.model_validate(case.request["model_config"]["provider_ref"])
    registry.register(
        text_spec(provider_ref),
        expected_revision=0,
        binding=AdapterBinding(provider_ref, frozenset({"development"}), implemented=True),
    )
    contexts = assemble_registered_context(control, registry=registry)
    text = files("uaw.resources.prompts").joinpath("agent-root-v1.txt").read_text(encoding="utf-8")
    method = await contexts.inputs.register_rule(
        InstructionRule(
            id="root-method",
            source_ref=Ref(kind="rule", id="root-method", version="1"),
            level="platform",
            scope=ScopeSelector(conversation_id=ctx.scope.conversation_id),
            text=text,
        ),
        ctx,
        authenticated_service=configuration.platform,
        expected_revision=0,
        meta=meta("root-method", 0),
    )
    role_payload = {**profile(["text"]), "instructions_ref": method.wire()}
    role = await control.tool_access.register_role(
        role_payload, meta("root-role", 0), authenticated_service=configuration.platform
    )
    await control.tool_access.bind(
        ctx, role, meta("root-role-bind", 0), authenticated_service=configuration.platform
    )
    tool_ref = Ref.model_validate(registry.reference(registry.snapshot()[1][0]))
    tools = assemble_text_tool(
        control,
        registry=registry,
        tool_ref=tool_ref,
        provider=Principal(
            id="root-text-service", kind="service", auth_session_id="root-text-session"
        ),
    )
    assembly = assemble_agent_runtime(control, contexts, tools, registry=registry)
    current = await run.get_run(ctx.principal, ctx.run_id)
    start = {
        "run_ref": {"kind": "run", "id": current["id"], "version": str(current["revision"])},
        "task_frame_ref": understood["output_refs"][0],
        "creation_key": "root-test-create",
        "role_profile_ref": role.wire(),
    }
    case.requests.clear()
    return SimpleNamespace(
        assembly=assembly,
        contexts=contexts,
        tools=tools,
        control=control,
        model_case=case,
        ctx=ctx,
        start=start,
        role=role,
        tool_ref=tool_ref,
        domain=domain,
        understanding=understanding,
    )
