from tests.integration.agent.conftest import agent_case as agent_case
from tests.integration.agent.test_root_postgres import request, start
from tests.integration.intent.test_understanding import proposal, response
from tests.integration.test_control_plane import meta
from uaw.agent.repository import pin
from uaw.run.inputs import RunInputReader


async def test_new_user_frame_invalidates_unsent_original_step(agent_case):
    p = agent_case
    root = await start(p)
    raw, ctx = await request(p, root)
    operation, _ = await p.assembly.repository.claim(raw, ctx)
    assert not p.model_case.requests
    state = await p.domain[1].store.get(ctx.principal, "run.input_sets", ctx.run_id)
    await p.domain[1].append_requirement(
        ctx.principal,
        ctx.run_id,
        "请只给当前材料的结论，不调用工具。",
        meta("root-user-correction", state.revision),
    )
    refreshed_ctx = ctx.model_copy(
        update={
            "operation_id": "refresh-understanding",
            "attempt_id": "refresh-model",
            "trace_id": "refresh-trace",
        }
    )
    inputs = await RunInputReader(p.domain[1].store).read(refreshed_ctx)
    p.model_case.responses[:] = [response(proposal(inputs.inputs[0]["text"]))]
    understood = await p.understanding.intent.understand(
        {
            "original_input_ref": inputs.refs[0],
            "user_patch_refs": list(inputs.refs[1:]),
            "material_refs": [],
            "expected_revision": 1,
        },
        refreshed_ctx,
    )
    assert understood["kind"] == "ok", understood
    shifted = await p.assembly.repository.discard_stale_unsent(
        pin("content", operation.wire()), ctx
    )
    instance, _, current = await p.assembly.repository.owned(root.id, ctx)
    assert current.active_operation_ref is None and current.steps == 1
    assert shifted.id == root.id and instance.status == "ready"
    old = await p.assembly.repository.operation(operation.id, ctx)
    assert old.phase == "failed" and old.result["failure"]["code"] == "agent_task_changed"
    assert len(p.model_case.requests) == 1  # Only the actual new understanding call.
