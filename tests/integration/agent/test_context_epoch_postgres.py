from tests.integration.agent.conftest import agent_case as agent_case
from tests.integration.agent.test_root_postgres import decision, request, start
from tests.integration.test_control_plane import meta
from uaw.agent.contracts import identifier
from uaw.context.contracts import ContextRequest, ModelToolSet, PreservationSpec, RulesRequest
from uaw.context.repository import SNAPSHOTS
from uaw.shared.contracts import Ref


async def test_root_uses_actual_snapshot_epoch_after_existing_recipe(agent_case):
    p = agent_case
    root = await start(p)
    view = await p.assembly.sources.current(p.ctx)
    # A real prior Context registration advances its epoch without a root step.
    await p.contexts.inputs.register_recipe(
        ContextRequest(
            purpose="agent_step",
            source_refs=(),
            model_policy_ref=p.ctx.model_policy_ref,
            output_reserve=512,
            tool_reserve=2048,
            expected_epoch=0,
            preserve=PreservationSpec(
                required_refs=(), exact_strings=(), requirement_ids=(), pending_action_refs=()
            ),
        ),
        RulesRequest(
            scope_paths=(),
            user_instruction_refs=(Ref.model_validate(view.role["instructions_ref"]),),
            activated_skill_refs=(),
        ),
        ModelToolSet(run_id=p.ctx.run_id, tools=()),
        p.ctx,
        authenticated_service=p.domain[0].platform,
        expected_revision=0,
        meta=meta("prior-real-recipe", 0),
    )
    raw, ctx = await request(p, root)
    p.model_case.responses[:] = [decision()]
    result = await p.assembly.runtime.step(raw, ctx)
    assert result["kind"] == "ok", result
    instance, _, state = await p.assembly.repository.owned(root.id, ctx)
    operation = await p.assembly.repository.operation(
        identifier("agent-op-", {"agent": root.id, "operation": ctx.operation_id}), ctx
    )
    actual = await p.assembly.repository.store.get(
        ctx.principal, SNAPSHOTS, operation.snapshot_ref.id
    )
    assert state.steps == 1 and actual.payload["epoch"] == 2
    assert instance.context_epoch == operation.context_epoch == actual.payload["epoch"]
    assert len(p.model_case.requests) == 1
