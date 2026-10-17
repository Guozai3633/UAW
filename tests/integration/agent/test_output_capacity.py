"""Real SQL + recorded provider output boundaries, not live quality assertions."""

import asyncio
import json

import httpx
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
from tests.integration.model.test_gateway import reply
from uaw.run.background import BackgroundAgent
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.conversation_control import ConversationControls
from uaw.run.execution_clock import ExecutionClocks
from uaw.run.execution_segments import ExecutionSegments
from uaw.run.jobs import JOBS
from uaw.shared.conversation import RunCorrectionRequest

pytestmark = pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)


@pytest.mark.parametrize("complete_json", [False, True])
async def test_length_output_has_owning_failure_and_never_registers_partial_artifact(
    scenario, complete_json
):
    p = scenario
    text = json.dumps(
        {"protocol": "conversation-v1", "action": "deliver", "text": "Partial report"}
    )
    body = reply(text if complete_json else text[:-8])
    body["choices"][0]["finish_reason"] = "length"
    p.case.responses[:] = [httpx.Response(200, json=body)]
    assert await p.queue.tick()
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    assert job["failure"]["code"] == "agent_output_truncated", job.get("failure")
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "failed"
    messages = [v["text"] for v in await inventory(p, "items") if v["type"] == "agent_message"]
    assert any("输出上限" in text for text in messages)
    assert not await inventory(p, "workspace.artifacts")
    assert not await inventory(p, "agent.conversation.decisions")
    operation = (await inventory(p, "agent.loop.operations"))[0]
    assert operation["phase"] == "failed" and operation["model_result"]["kind"] == "ok"
    assert operation["result"]["failure"]["code"] == "agent_output_truncated"
    invocations = await inventory(p, "model.invocations")
    assert len(invocations) == 1 and invocations[0]["state"] == "finished"
    assert invocations[0]["result"]["payload"]["finish_reason"] == "length"
    assert len(p.case.requests) == 1 and not await p.queue.tick()


async def test_report_then_correction_keeps_old_artifact_and_applies_only_complete_new_report(
    scenario,
):
    from tests.integration.agent.test_completion_postgres import review
    from uaw.agent.completion.contracts import contract_from_frame
    from uaw.run.deliveries import DeliveryReader

    p = scenario
    p.driver = BackgroundAgent(
        p.control,
        conversation_clocks=ExecutionClocks(p.runs.store, effects=RunIdleEffects()),
        conversation_segments=ExecutionSegments(p.runs.store),
    )
    p.queue = await p.driver.prepare()
    frame = (await p.runs.store.get(p.actor, "intent.frames", p.run["task_id"])).payload
    original_text = "Original general employment report."
    p.case.responses[:] = [
        output({"protocol": "conversation-v1", "action": "deliver", "text": original_text}),
        review(contract_from_frame(frame)["requirements"]),
    ]
    assert await p.queue.tick()
    reader = DeliveryReader(p.runs.store, p.control.blobs)
    original, _ = await reader.read(p.actor, p.run["id"])
    control = ConversationControls(p.runs.store)
    view = await control.view(p.actor, p.run["id"])
    receipt = await control.correct(
        p.actor,
        RunCorrectionRequest(
            run_id=p.run["id"],
            expected_input_revision=view.input_revision,
            text="Focus especially on university graduates and entry-level employment.",
            attachment_refs=(),
        ),
        control_meta(view, "report-correction"),
    )
    assert receipt.patch.state == "accepted"
    # The running delivery poll must first observe its now-stale frame and
    # block the owning old job, just as the actual background queue does.
    await asyncio.sleep(2.1)
    assert await p.queue.tick()
    assert await p.driver.resume_conversation(p.actor, p.run["id"])
    for _ in range(3):
        assert await p.queue.tick()
    frame = (await p.runs.store.get(p.actor, "intent.frames", p.run["task_id"])).payload
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "deliver",
                "text": "# University graduates\n" + "Entry-level employment.\n" * 160,
            }
        ),
        review(contract_from_frame(frame)["requirements"]),
    ]
    assert await p.queue.tick()
    latest = await control.lookup(p.actor, p.run["id"], "report-correction")
    assert latest.patch.state == "applied", latest
    current, _ = await reader.read(p.actor, p.run["id"])
    assert not current["stale"] and current["artifact_ref"] != original["artifact_ref"]
    assert len(await inventory(p, "workspace.artifacts")) == 2
    assert not await inventory(p, "run.completion.acceptance")
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] != "completed"
    assert len(p.case.requests) == 4
    assert all(
        json.loads(p.case.requests[i].content)["max_completion_tokens"] > 2048 for i in (0, 2)
    )
    assert all(
        json.loads(p.case.requests[i].content)["max_completion_tokens"] == 2048 for i in (1, 3)
    )
