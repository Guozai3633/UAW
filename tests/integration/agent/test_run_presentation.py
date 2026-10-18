"""Consistent owned read-only UI projection; model responses are controlled HTTP."""

import json
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy import text

from tests.integration.agent.test_completion_postgres import review
from tests.integration.agent.test_conversation_postgres import (
    case as case,
)
from tests.integration.agent.test_conversation_postgres import (
    domain as domain,
)
from tests.integration.agent.test_conversation_postgres import inventory, output
from tests.integration.agent.test_conversation_postgres import (
    scenario as scenario,
)
from tests.integration.test_control_plane import meta
from uaw.agent.completion.contracts import contract_from_frame
from uaw.api.application import create_app
from uaw.run.conversation_control import ConversationControls
from uaw.run.jobs import JOBS
from uaw.run.presentation import RunPresentationReader
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.shared.conversation import ConversationRequestMeta, RunCorrectionRequest
from uaw.shared.errors import DomainError

pytestmark = pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)


async def report_ready(p, *, summary=True):
    frame = (await p.runs.store.get(p.actor, "intent.frames", p.run["task_id"])).payload
    value = {
        "protocol": "conversation-v1",
        "action": "deliver",
        "text": "A completed requested report.",
    }
    if summary:
        value["understanding"] = {"summary": "The actual model summary", "assumptions": []}
    p.case.responses[:] = [output(value), review(contract_from_frame(frame)["requirements"])]
    assert await p.queue.tick()
    assert (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload["stage"] == "delivery"
    assert await p.queue.tick()
    return RunPresentationReader(p.runs.store)


async def test_current_report_understanding_and_wait_are_one_readonly_snapshot(scenario):
    p = scenario
    reader = await report_ready(p)
    run = await p.runs.get_run(p.actor, p.run["id"])
    before = {
        namespace: await inventory(p, namespace)
        for namespace in (
            "runs",
            "intent.frames",
            "agent.completion.proposals",
            "items",
            "run.execution_clocks",
            "run.protocol_bindings",
            "budget.ledgers",
        )
    }
    view = await reader.read(p.actor, p.run["id"])
    assert view["run"] == run and run["status"] == "running"
    assert view["phase"] == "awaiting_acceptance"
    assert view["delivery"]["run_revision"] == run["revision"]
    assert view["understanding"]["state"] == "available"
    assert view["understanding"]["value"]["summary"] == "The actual model summary"
    assert view["understanding"]["input_revision"] == view["input_revision"] == 1
    assert (await reader.read(p.actor, p.run["id"]))["delivery"] == view["delivery"]
    for namespace, values in before.items():
        assert await inventory(p, namespace) == values
    assert len(p.case.requests) == 2


async def test_finished_model_without_summary_is_not_pending_understanding(scenario):
    p = scenario
    reader = await report_ready(p, summary=False)
    view = await reader.read(p.actor, p.run["id"])
    assert view["phase"] == "awaiting_acceptance"
    assert view["understanding"] == {"state": "not_provided", "input_revision": 1}


async def test_pending_first_model_and_new_correction_do_not_show_old_delivery(scenario):
    p = scenario
    reader = RunPresentationReader(p.runs.store)
    initial = await reader.read(p.actor, p.run["id"])
    assert initial["understanding"]["state"] == "pending" and "delivery" not in initial
    await report_ready(p)
    controls = ConversationControls(p.runs.store)
    view = await controls.view(p.actor, p.run["id"])
    await controls.correct(
        p.actor,
        RunCorrectionRequest(
            run_id=p.run["id"],
            expected_input_revision=1,
            text="Focus on a new audience.",
            attachment_refs=(),
        ),
        ConversationRequestMeta(
            request_id="presentation-correction",
            schema_version="0.2",
            expected_revision=view.run["revision"],
        ),
    )
    changed = await reader.read(p.actor, p.run["id"])
    assert changed["input_revision"] == 2
    assert changed["understanding"] == {"state": "pending", "input_revision": 2}
    assert changed["phase"] != "awaiting_acceptance" and "delivery" not in changed
    assert len(p.case.requests) == 2


async def test_acceptance_projects_finalizing_then_actual_completed_only(scenario):
    p = scenario
    reader = await report_ready(p)
    view = await reader.read(p.actor, p.run["id"])
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    await p.control.completion_controller.accept(
        p.actor,
        Ref.model_validate(view["delivery"]["bundle_ref"]),
        Ref.model_validate(view["delivery"]["artifact_ref"]),
        "accept",
        TrustedExecutionContext.model_validate_json(json.dumps(job["step_context"])),
        meta("presentation-owner-test-accept"),
    )
    assert (await reader.read(p.actor, p.run["id"]))["phase"] == "finalizing"
    row = await p.runs.store.get(p.actor, JOBS, p.run["id"])
    await p.runs.store.put(
        p.actor,
        JOBS,
        row.resource_id,
        row.schema_name,
        {**row.payload, "revision": row.revision + 1, "ready_at": datetime.now(UTC).isoformat()},
        expected_revision=row.revision,
        request_id="presentation-wake-test",
    )
    assert await p.queue.tick()
    completed = await reader.read(p.actor, p.run["id"])
    assert completed["phase"] == completed["run"]["status"] == "completed"
    assert len(p.case.requests) == 2


async def test_cancelled_report_never_presents_ready_or_completes(scenario):
    p = scenario
    reader = await report_ready(p)
    current = await p.runs.get_run(p.actor, p.run["id"])
    await p.runs.control(
        p.actor,
        {
            "run_id": p.run["id"],
            "control": {
                "mode": "cancel",
                "preserve_refs": [],
                "reason": "Controlled test cancel",
            },
        },
        meta("presentation-cancel", current["revision"]),
    )
    view = await reader.read(p.actor, p.run["id"])
    assert view["phase"] == "stopping" and "delivery" not in view
    assert view["run"]["status"] != "cancelled"  # Cancellation is accepted, not yet settled.


async def test_unknown_original_effect_is_not_ready_for_acceptance(scenario):
    p = scenario
    reader = await report_ready(p)
    row = await p.runs.store.get(p.actor, "model.invocations", p.job["step_context"]["attempt_id"])
    value = {**row.payload, "state": "claimed"}
    value.pop("result")
    await p.runs.store.put(
        p.actor,
        row.namespace,
        row.resource_id,
        row.schema_name,
        value,
        expected_revision=row.revision,
        request_id="presentation-unknown",
    )
    with pytest.raises(DomainError):
        await reader.read(p.actor, p.run["id"])


async def test_read_snapshot_cannot_mix_cancellation_committed_during_read(scenario, monkeypatch):
    p = scenario
    reader = await report_ready(p)
    original = reader.understanding
    before = await p.runs.get_run(p.actor, p.run["id"])

    async def cancel_after_snapshot(tx, run, revision):
        assert (await tx.session.execute(text("SHOW transaction_read_only"))).scalar() == "on"
        await p.runs.control(
            p.actor,
            {
                "run_id": run["id"],
                "control": {
                    "mode": "cancel",
                    "preserve_refs": [],
                    "reason": "Concurrent controlled cancel",
                },
            },
            meta("presentation-concurrent-cancel", before["revision"]),
        )
        return await original(tx, run, revision)

    monkeypatch.setattr(reader, "understanding", cancel_after_snapshot)
    view = await reader.read(p.actor, p.run["id"])
    assert view["run"] == before and view["phase"] == "awaiting_acceptance"
    monkeypatch.setattr(reader, "understanding", original)
    assert (await reader.read(p.actor, p.run["id"]))["phase"] == "stopping"


async def test_owned_HTTP_projection_uses_02_and_rejects_foreign_or_unexpected_query(scenario):
    p = scenario
    await report_ready(p)
    url = f"/v1/runs/{p.run['id']}/presentation"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(p.control)),
        base_url="http://test",
        headers={"Authorization": "Bearer " + "u" * 40},
    ) as client:
        result = await client.get(url, headers={"X-UAW-Schema-Version": "0.2"})
        assert result.status_code == 200, result.json()
        assert result.json()["payload"]["phase"] == "awaiting_acceptance"
        assert result.headers["cache-control"] == "no-store"
        assert (await client.get(url, headers={"X-UAW-Schema-Version": "0.1"})).status_code == 422
        assert (await client.get(url + "?run_id=foreign")).status_code == 422
    reader = RunPresentationReader(p.runs.store)
    with pytest.raises(DomainError):
        await reader.read(
            Principal(id="foreign", kind="user", auth_session_id="other"), p.run["id"]
        )
