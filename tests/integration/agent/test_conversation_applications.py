"""Original controlled model calls prove application; metadata preparation alone cannot."""

import json

import pytest

from tests.integration.agent.test_conversation_controls import (
    case as case,
)
from tests.integration.agent.test_conversation_controls import (
    domain as domain,
)
from tests.integration.agent.test_conversation_controls import (
    scenario as scenario,
)
from tests.integration.agent.test_conversation_postgres import inventory, output
from tests.integration.agent.test_conversation_preparation import prepared
from tests.integration.test_control_plane import meta
from uaw.agent.contracts import identifier
from uaw.agent.repository import pin
from uaw.run.conversation_applications import APPLICATIONS, ConversationApplications
from uaw.run.conversation_entry import publish
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError

pytestmark = pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)


async def actual_step(p):
    control, view, receipt, old, ctx, frame = await prepared(p)
    current = await p.runs.get_run(p.actor, p.run["id"])
    await p.runs.advance(
        p.actor, p.run["id"], "running", meta("run-new-input", current["revision"])
    )
    repo = p.driver.agent.repository
    instance, _, state = await repo.owned(
        p.run["root_agent_ref"]["id"] if "root_agent_ref" in p.run else p.job["instance_ref"]["id"],
        ctx,
    )
    root = pin("agent_instance", instance.wire())
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "reply",
                "text": "I used the original terminology and the second option.",
            }
        )
    ]
    result = await p.driver.agent.runtime.step(
        {
            "instance_ref": root.wire(),
            "observations": [r.wire() for r in state.observation_refs],
            "current_frame_ref": frame,
            "remaining_budget": (await repo.current(root, ctx))[3].remaining_budget,
        },
        ctx,
    )
    return control, receipt, ctx, result


async def test_actual_model_consumption_marks_applied_once_but_does_not_grant_resume(scenario):
    p = scenario
    control, receipt, ctx, result = await actual_step(p)
    assert result["kind"] == "ok", result
    latest = await control.lookup(p.actor, p.run["id"], "answer-1")
    assert latest.patch.state == "applied" and latest.patch.applied_at
    records = await inventory(p, APPLICATIONS)
    assert len(records) == 1 and records[0]["attempt_id"] == ctx.attempt_id
    assert records[0]["patch_input_refs"] == [receipt.patch.input_ref.wire()]
    applications = ConversationApplications(p.runs.store)
    ref = Ref.model_validate(result["payload"]["model_output_ref"])
    assert await applications.consume(ref, ctx) == records[0]
    assert await applications.consume(ref, ctx) == records[0]
    assert len(await inventory(p, APPLICATIONS)) == 1 and len(p.case.requests) == 2
    op_id = identifier(
        "agent-op-", {"agent": p.job["instance_ref"]["id"], "operation": ctx.operation_id}
    )
    # This component fixture has not resumed the owning clock or background job.
    # Actual consumption is evidence of input use, never a grant to publish.
    with pytest.raises(DomainError) as inactive:
        await publish(p.driver.agent, op_id, ctx)
    assert inactive.value.failure.code == "conversation_active_clock_required"
    assert not await inventory(p, "run.conversation.replies")
    assert not await inventory(p, "workspace.artifacts")


async def test_old_response_cannot_be_relabelled_as_the_new_input(scenario):
    p = scenario
    _, _, _, _, ctx, _ = await prepared(p)
    old_op = (
        await p.runs.store.get(
            p.actor,
            "agent.loop.operations",
            identifier(
                "agent-op-",
                {
                    "agent": p.job["instance_ref"]["id"],
                    "operation": p.job["step_context"]["operation_id"],
                },
            ),
        )
    ).payload
    original = old_op["model_result"]
    from uaw.shared.contracts import TrustedExecutionContext

    old_ctx = TrustedExecutionContext.model_validate_json(json.dumps(old_op["context"]))
    with pytest.raises(DomainError) as stale:
        await p.driver.agent.runtime.loop.models.read(original, old_ctx)
    assert stale.value.failure.code == "conversation_model_input_stale"
    assert not await inventory(p, APPLICATIONS)
    assert all(v["state"] == "accepted" for v in await inventory(p, "run.input_patches"))
    assert len(p.case.requests) == 1


async def test_cancel_before_application_leaves_accepted_input_without_false_applied(
    scenario, monkeypatch
):
    p = scenario
    original = ConversationApplications.consume

    async def cancel(self, output_ref, ctx):
        if ctx.attempt_id == "web-step-model-2-" + p.run["id"]:
            current = await p.runs.get_run(p.actor, p.run["id"])
            await p.runs.control(
                p.actor,
                {
                    "run_id": p.run["id"],
                    "control": {
                        "mode": "cancel",
                        "preserve_refs": [],
                        "reason": "Cancel after actual model output, before applying input",
                    },
                },
                meta("cancel-before-application", current["revision"]),
            )
        return await original(self, output_ref, ctx)

    monkeypatch.setattr(ConversationApplications, "consume", cancel)
    _, _, _, result = await actual_step(p)
    assert result["kind"] != "ok"
    assert not await inventory(p, APPLICATIONS)
    assert not any(v["state"] == "applied" for v in await inventory(p, "run.input_patches"))


async def test_application_transaction_rollback_preserves_original_model_and_pending_input(
    scenario, monkeypatch
):
    from uaw.infrastructure.db.models import RecordRow
    from uaw.infrastructure.db.transactions import RecordTransaction

    p = scenario
    original = RecordTransaction.emit

    async def fail(self, stream, event_type, parameters, **kwargs):
        if event_type == "run.updated" and parameters["status"] == "running":
            pending = await self.session.get(
                RecordRow,
                (
                    self.owner,
                    APPLICATIONS,
                    identifier(
                        "input-application-",
                        {"run": p.run["id"], "attempt": "web-step-model-2-" + p.run["id"]},
                    ),
                ),
            )
            if pending:
                raise RuntimeError("injected application event failure")
        return await original(self, stream, event_type, parameters, **kwargs)

    monkeypatch.setattr(RecordTransaction, "emit", fail)
    with pytest.raises(RuntimeError):
        await actual_step(p)
    assert not await inventory(p, APPLICATIONS)
    assert all(v["state"] == "accepted" for v in await inventory(p, "run.input_patches"))
    assert (
        len([v for v in await inventory(p, "model.invocations") if v["run_id"] == p.run["id"]]) == 2
    )
    monkeypatch.setattr(RecordTransaction, "emit", original)
    # Re-read the owning original result; it commits application without resending the model.
    from uaw.shared.contracts import TrustedExecutionContext

    inv = next(
        v
        for v in await inventory(p, "model.invocations")
        if v["run_id"] == p.run["id"] and v["id"].startswith("web-step-model-2-")
    )
    op = next(
        v
        for v in await inventory(p, "agent.loop.operations")
        if v["context"]["attempt_id"] == inv["id"]
    )
    ctx = TrustedExecutionContext.model_validate_json(json.dumps(op["context"]))
    await p.driver.agent.runtime.loop.models.read(inv["result"], ctx)
    assert len(await inventory(p, APPLICATIONS)) == 1 and len(p.case.requests) == 2
