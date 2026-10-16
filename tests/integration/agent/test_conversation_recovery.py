"""An obsolete failed attempt must not terminate newer accepted user input."""

import pytest

from tests.integration.agent.test_conversation_controls import (
    case as case,
)
from tests.integration.agent.test_conversation_controls import (
    control_meta,
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
from uaw.run.conversation_applications import APPLICATIONS
from uaw.run.conversation_control import ConversationControls
from uaw.run.jobs import JOBS
from uaw.shared.conversation import RunCorrectionRequest

pytestmark = pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)


@pytest.mark.parametrize("cancel_after", [False, True])
async def test_correction_during_original_model_preserves_pending_input_and_cancel(
    scenario, monkeypatch, cancel_after
):
    p = scenario
    control = ConversationControls(p.runs.store)
    models = p.driver.agent.runtime.loop.models
    generate = models.generate
    p.case.responses[:] = [
        output({"protocol": "conversation-v1", "action": "reply", "text": "Obsolete answer"})
    ]

    async def correct_after_actual_model(request, ctx):
        result = await generate(request, ctx)
        view = await control.view(p.actor, p.run["id"])
        await control.correct(
            p.actor,
            RunCorrectionRequest(
                run_id=p.run["id"],
                expected_input_revision=view.input_revision,
                text="Use the new audience, retaining the original evidence.",
                attachment_refs=(),
            ),
            control_meta(view, "correction-during-model"),
        )
        return result

    monkeypatch.setattr(models, "generate", correct_after_actual_model)
    assert await p.queue.tick()
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert job["state"] == "blocked" and job.get("failure"), job
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "running"
    receipt = await control.lookup(p.actor, p.run["id"], "correction-during-model")
    assert receipt.patch.state == "accepted" and receipt.patch.input_revision == 2
    assert not await inventory(p, APPLICATIONS)
    assert not await inventory(p, "run.conversation.replies")
    await p.queue.reconcile_stopped()
    assert (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload == job
    if cancel_after:
        current = await p.runs.get_run(p.actor, p.run["id"])
        await p.runs.control(
            p.actor,
            {
                "run_id": p.run["id"],
                "control": {"mode": "cancel", "preserve_refs": [], "reason": "User stopped"},
            },
            meta("cancel-pending", current["revision"]),
        )
        await p.queue.reconcile_stopped()
        receipt = await control.lookup(p.actor, p.run["id"], "correction-during-model")
        assert receipt.run["status"] == "cancelled" and receipt.patch.state == "cancelled"
        versions = await inventory(p, JOBS)
        assert next(v for v in versions if v["run_id"] == p.run["id"])["failure"] == job["failure"]
    assert len(p.case.requests) == 1


async def test_failure_from_current_input_version_still_terminates(scenario):
    p = scenario
    _, _, _, _, ctx, frame = await prepared(p)
    current = await p.runs.get_run(p.actor, p.run["id"])
    await p.runs.advance(
        p.actor, p.run["id"], "running", meta("current-input-running", current["revision"])
    )
    row = await p.runs.store.get(p.actor, JOBS, p.run["id"])
    # Explicit component setup of a resumed job, not production clock admission.
    await p.runs.store.put(
        p.actor,
        JOBS,
        row.resource_id,
        row.schema_name,
        {
            **row.payload,
            "revision": row.revision + 1,
            "state": "queued",
            "frame_ref": frame,
            "step": 2,
            "step_context": ctx.wire(),
        },
        expected_revision=row.revision,
        request_id="fixture-current-input-job",
    )
    p.case.responses[:] = [output({"protocol": "conversation-v1", "action": "reply"})]
    assert await p.queue.tick()
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert job["failure"]["code"] == "provider_structured_output_invalid", job
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "failed"
    assert not await inventory(p, APPLICATIONS)
    assert len(p.case.requests) == 2
