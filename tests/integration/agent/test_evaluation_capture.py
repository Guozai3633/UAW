"""Actual PostgreSQL captures preserve success/failure without granting human labels."""

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from tests.integration.agent.test_completion_postgres import review
from tests.integration.agent.test_conversation_postgres import case as case
from tests.integration.agent.test_conversation_postgres import domain as domain
from tests.integration.agent.test_conversation_postgres import output
from tests.integration.agent.test_conversation_postgres import scenario as scenario
from tests.integration.test_control_plane import meta
from uaw.agent.completion.contracts import contract_from_frame
from uaw.evaluation.contracts import Case, Policy
from uaw.evaluation.io import canonical
from uaw.evaluation.runner import evaluate_files
from uaw.run.evaluation_capture import CaptureError, prepare_bundle, read_run, write_bundle

pytestmark = pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)


@pytest.mark.parametrize("mode", ["reply", "failed", "deliver", "failed_review"])
async def test_readonly_capture_retains_every_attempt_and_cannot_pass_without_human(
    scenario, tmp_path, mode
):
    p = scenario
    failed = mode == "failed"
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "deliver" if mode in ("deliver", "failed_review") else "reply",
                **({} if failed else {"text": "A complete response under an explicit assumption."}),
            }
        )
    ]
    if mode in ("deliver", "failed_review"):
        frame = (await p.runs.store.get(p.actor, "intent.frames", p.run["task_id"])).payload
        p.case.responses.append(
            output({"broken": "reviewer"})
            if mode == "failed_review"
            else review(contract_from_frame(frame)["requirements"])
        )
    assert await p.queue.tick()
    if mode == "deliver":
        current = await p.runs.get_run(p.actor, p.run["id"])
        await p.runs.control(
            p.actor,
            {
                "run_id": p.run["id"],
                "control": {
                    "mode": "cancel",
                    "preserve_refs": [],
                    "reason": "End controlled capture case",
                },
            },
            meta("capture-cancel", current["revision"]),
        )
        assert await p.queue.tick()
    with pytest.raises(CaptureError, match="run_owner_missing"):
        await read_run(
            p.runs.store.database, p.actor.model_copy(update={"id": "other-owner"}), p.run["id"]
        )
    rows = await read_run(p.runs.store.database, p.actor, p.run["id"])
    before = [(r.namespace, r.id, r.revision, r.payload) for r in rows]
    state = next(r.payload for r in rows if r.namespace == "run.input_sets")
    original = next(
        r.payload
        for r in rows
        if r.namespace == "inputs" and r.id == state["original_input_ref"]["id"]
    )
    sample = Case.model_validate_json(
        canonical(
            {
                "id": "controlled-original",
                "version": "1",
                "split": "revision",
                "category": "reasonable_ambiguity",
                "prompt": original["text"],
                "rubric": {
                    "expected_behavior": "answer",
                    "required_facts": ["Give a useful answer under an explicit assumption."],
                    "allowed_assumptions": [],
                    "retained_requirements": [],
                    "critical": True,
                },
                "evidence": [],
                "review_status": "needs_human_review",
                "human_verification": None,
            }
        )
    )
    policy = Policy.model_validate_json(
        canonical(
            {
                "id": "retrospective",
                "registered_at": datetime.now(UTC).isoformat(),
                "reviewer_required": False,
                "baseline_required": True,
                "max_answer_error_rate": "0",
                "max_reviewer_miss_rate": "0",
                "max_unnecessary_block_rate": "0",
                "max_unsupported_execution_rate": "0",
            }
        )
    )
    selection = (
        None
        if failed
        else next(r.id for r in rows if r.namespace == "agent.conversation.decisions")
    )
    options = dict(
        candidate_id="controlled-SQL-capture",
        source_commit="a" * 40,
        environment_hash="b" * 64,
        prompt_hash="c" * 64,
        selected_attempt=selection,
    )
    bundle = prepare_bundle(rows, sample, policy, **options)
    path = tmp_path / "captured"
    write_bundle(path, bundle)
    report = evaluate_files(
        path / "suite.json",
        path / "manifest.json",
        path / "observations.jsonl",
        path / "reviews.jsonl",
    )
    assert report.release_gate.status == "incomplete"
    expected_calls = 2 if mode in ("deliver", "failed_review") else 1
    assert report.candidate.attempt_count == expected_calls
    assert report.candidate.model_calls.known_total == expected_calls
    assert report.candidate.failure_count == int(failed or mode == "failed_review")
    assert report.candidate.retry_count == 0
    assert (
        report.candidate.human_reviewed_cases == 0 and report.candidate.answer_error.value is None
    )
    assert bundle["observations"][0]["usage"]["money"] is None
    assert bundle["observations"][0]["usage"]["billing_state"] == "pending"
    if failed:
        assert bundle["observations"][0]["failure_code"] == "provider_structured_output_invalid"
    else:
        tampered = tuple(
            replace(r, payload={**r.payload, "text": "changed"})
            if r.namespace == "model.outputs"
            else r
            for r in rows
        )
        with pytest.raises(CaptureError, match="owning_output_mismatch"):
            prepare_bundle(tampered, sample, policy, **options)
    if mode in ("deliver", "failed_review"):
        observed_review = next(o for o in bundle["observations"] if o["phase"] == "reviewer")
        assert observed_review["reviewer"]["target_attempt_id"] == selection
        assert observed_review["reviewer"]["verdict"] == (
            "unavailable" if mode == "failed_review" else "passed"
        )
        assert (
            bundle["manifest"]["candidate"]["selections"][0]["reviewer_attempt_id"]
            == observed_review["attempt_id"]
        )
        if mode == "failed_review":
            assert observed_review["status"] == "failed"
            assert observed_review["failure_code"] == "provider_structured_output_invalid"
        tampered = tuple(
            replace(
                r,
                payload={
                    **r.payload,
                    "sources": [
                        {**s, "ref": {**s["ref"], "version": "999"}}
                        if s["namespace"] == "model.outputs"
                        else s
                        for s in r.payload["sources"]
                    ],
                },
            )
            if r.namespace == "model.evaluation.inputs"
            else r
            for r in rows
        )
        with pytest.raises(CaptureError, match="reviewer_target_binding_mismatch"):
            prepare_bundle(tampered, sample, policy, **options)
    missing_duration = tuple(
        replace(
            r,
            payload={
                **r.payload,
                "usage": {
                    **r.payload["usage"],
                    "resources": {
                        k: v
                        for k, v in r.payload["usage"]["resources"].items()
                        if k != "wall_time_ms"
                    },
                },
            },
        )
        if r.namespace == "model.attempts"
        else r
        for r in rows
    )
    with pytest.raises(CaptureError, match="active_duration_unobserved"):
        prepare_bundle(missing_duration, sample, policy, **options)
    with pytest.raises(CaptureError, match="case_prompt_differs"):
        prepare_bundle(
            rows, sample.model_copy(update={"prompt": "different task"}), policy, **options
        )
    after = await read_run(p.runs.store.database, p.actor, p.run["id"])
    assert before == [(r.namespace, r.id, r.revision, r.payload) for r in after]
    assert len(p.case.requests) == expected_calls and not await p.queue.tick()
