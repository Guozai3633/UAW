"""Real SQL/web review boundaries; every rating here is a controlled fixture."""

import asyncio
import json
from copy import deepcopy
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from tests.integration.agent.test_completion_postgres import review as semantic_review
from tests.integration.agent.test_conversation_postgres import case as case
from tests.integration.agent.test_conversation_postgres import domain as domain
from tests.integration.agent.test_conversation_postgres import inventory, output
from tests.integration.agent.test_conversation_postgres import scenario as scenario
from tests.integration.test_browser_sessions import ORIGIN, login
from tests.integration.test_browser_sessions import web as web
from tests.integration.test_control_plane import meta
from tests.unit.evaluation.factories import add_reviewer, example_files, write_files
from uaw.agent.completion.contracts import contract_from_frame
from uaw.evaluation.contracts import Case, Policy
from uaw.evaluation.runner import evaluate_files
from uaw.infrastructure.db.models import RecordRow
from uaw.run.evaluation_capture import prepare_bundle, read_run, write_bundle
from uaw.run.quality import QualityReviews, parsed
from uaw.run.quality import write_files as restore_files
from uaw.shared.contracts import Principal
from uaw.shared.errors import DomainError
from uaw.shared.quality import (
    QualityFeedbackSave,
    QualityFiles,
    QualityOrigin,
    QualitySave,
    QualitySubmit,
)


@pytest.fixture
async def review(web, tmp_path):
    container, client = web
    public = await login(client)
    client.headers["Referer"] = ORIGIN + "/"
    actor = Principal.model_validate(public["principal"])
    operator = Principal(id=actor.id, kind="service", auth_session_id="quality-fixture-service")
    source = tmp_path / "original"
    data = add_reviewer(example_files(source))
    write_files(source, data)
    service = QualityReviews(container.records)
    value = await service.register(
        operator,
        actor,
        source,
        QualityOrigin(
            kind="controlled_test",
            principal_id=actor.id,
            run_id="fixture-run",
            run_revision=1,
            input_revision=1,
            source_commit=data["manifest"]["candidate"]["source_commit"],
        ),
        "受控协议样本，不是真人评分",
        meta("quality-register", 0),
    )
    return container, client, actor, public, service, value, source


def save(value, *, complete=False):
    item = deepcopy(value["judgments"][0])
    if complete:
        item.update(
            case_review="verified",
            evidence_reviewed=True,
            answer_correct=True,
            unnecessary_block=False,
            unsupported_execution=False,
            requirements_preserved=True,
            acceptable=True,
            critical_error=False,
            fabricated_evidence=False,
            notes="Controlled protocol test, not a real person's review.",
        )
    return {"review_id": value["id"], "packet_sha256": value["packet_sha256"], "judgments": [item]}


def envelope(request, request_id, expected=1):
    return {
        "meta": meta(request_id, expected).wire(),
        "payload": {k: v for k, v in request.items() if k != "review_id"},
    }


async def test_blank_save_reopen_replay_and_other_owner_denied(review):
    container, _, actor, _, service, value, _ = review
    assert all(
        v is None
        for k, v in value["judgments"][0].items()
        if k not in ("case_id", "attempt_id", "notes")
    )
    request = save(value)
    request["judgments"][0]["notes"] = "Still uncertain; retain draft."
    saved = await service.save(actor, parsed(QualitySave, request), meta("quality-save", 1))
    assert saved["revision"] == 2 and saved["status"] == "draft"
    restarted = QualityReviews(container.records)
    assert await restarted.get(actor, value["id"]) == saved
    async with container.database.sessions() as session:
        events = await session.scalars(
            select(RecordRow.payload).where(
                RecordRow.principal_id == actor.id,
                RecordRow.namespace == "events",
                RecordRow.payload["type"].as_string() == "quality.saved",
            )
        )
        assert [(event["base_revision"], event["result_revision"]) for event in events] == [(1, 2)]
    assert (
        await restarted.save(actor, parsed(QualitySave, request), meta("quality-save", 1)) == saved
    )
    with pytest.raises(DomainError) as caught:
        await restarted.get(actor.model_copy(update={"id": "another-person"}), value["id"])
    assert caught.value.status_code == 404
    with pytest.raises(DomainError):
        await restarted.export(actor, value["id"])


@pytest.mark.parametrize("change", ["old_hash", "duplicate", "missing", "other_attempt"])
async def test_wrong_target_never_saves(review, change):
    _, _, actor, _, service, value, _ = review
    request = save(value)
    if change == "old_hash":
        request["packet_sha256"] = "f" * 64
    elif change == "duplicate":
        request["judgments"].append(deepcopy(request["judgments"][0]))
    elif change == "missing":
        request["judgments"][0]["case_id"] = "different-case"
    else:
        request["judgments"][0]["attempt_id"] = "different-answer"
    with pytest.raises(DomainError) as caught:
        await service.save(actor, parsed(QualitySave, request), meta("wrong", 1))
    assert caught.value.status_code == 412
    assert (await service.get(actor, value["id"]))["revision"] == 1


async def test_cross_process_style_cas_only_one_writer(review):
    container, _, actor, _, service, value, _ = review
    request = parsed(QualitySave, save(value))
    outputs = await asyncio.gather(
        service.save(actor, request, meta("race-one", 1)),
        QualityReviews(container.records).save(actor, request, meta("race-two", 1)),
        return_exceptions=True,
    )
    assert sum(isinstance(result, dict) for result in outputs) == 1
    assert (
        sum(isinstance(result, DomainError) and result.status_code == 409 for result in outputs)
        == 1
    )


async def test_submission_exports_original_attempts_to_original_evaluator(review, tmp_path):
    _, _, actor, _, service, value, source = review
    request = parsed(QualitySubmit, {**save(value, complete=True), "human_attested": True})
    submitted = await service.save(actor, request, meta("submit-controlled", 1))
    assert submitted["status"] == "submitted" and submitted["submission"]["reviewer_id"] == actor.id
    exported = await service.export(actor, value["id"])
    assert exported["basis"] == "controlled_test"
    output = tmp_path / "export"
    output.mkdir()
    restore_files(output, parsed(QualityFiles, exported["files"]))
    assert (source / "observations.jsonl").read_bytes() == (
        output / "observations.jsonl"
    ).read_bytes()
    assert (
        json.loads((output / "suite.json").read_bytes())["cases"][0]["review_status"]
        == "needs_human_review"
    )
    report = evaluate_files(
        *(
            output / name
            for name in ("suite.json", "manifest.json", "observations.jsonl", "reviews.jsonl")
        )
    )
    assert report.candidate.human_reviewed_cases == 0
    assert report.candidate.controlled_reviewed_cases == 1
    assert report.candidate.model_calls.known_total == 2
    assert report.release_gate.status != "passed"
    assert await service.save(actor, request, meta("submit-controlled", 1)) == submitted
    with pytest.raises(DomainError):
        await service.save(actor, parsed(QualitySave, save(value)), meta("late-save", 2))


async def test_http_auth_csrf_origin_and_unknown_judgment(review):
    _, client, _, public, _, value, _ = review
    path = "/v1/quality/reviews/" + value["id"]
    loaded = await client.get(path)
    assert loaded.status_code == 200, loaded.json()
    assert loaded.json()["payload"]["targets"][0]["answer"]["text"] == "合计5。"
    assert (await client.get("/v1/quality/reviews")).json()["payload"]["items"][0]["id"] == value[
        "id"
    ]
    body = envelope(save(value), "http-save")
    assert (
        await client.post(path + "/draft", headers={"Origin": ORIGIN}, json=body)
    ).status_code == 403
    headers = {"Origin": ORIGIN, "X-UAW-CSRF": public["csrf_token"]}
    assert (
        await client.post(
            path + "/draft", headers={**headers, "Origin": "http://evil.invalid"}, json=body
        )
    ).status_code == 403
    response = await client.post(path + "/draft", headers=headers, json=body)
    assert response.status_code == 200, response.json()
    invalid = envelope({**save(value), "human_attested": True}, "incomplete-submit", 2)
    assert (
        await client.post(path + "/submission", headers=headers, json=invalid)
    ).status_code == 422
    assert (await client.get(path)).json()["payload"]["status"] == "draft"
    client.cookies.clear()
    assert (await client.get(path)).status_code == 401


async def test_http_inconsistent_acceptable_is_rejected_without_commit(review):
    _, client, _, public, _, value, _ = review
    request = {**save(value, complete=True), "human_attested": True}
    request["judgments"][0]["critical_error"] = True
    response = await client.post(
        "/v1/quality/reviews/" + value["id"] + "/submission",
        headers={"Origin": ORIGIN, "X-UAW-CSRF": public["csrf_token"]},
        json=envelope(request, "contradiction"),
    )
    assert (
        response.status_code == 422
        and response.json()["failure"]["code"] == "quality_judgment_invalid"
    )


@pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)
async def test_feedback_is_run_bound_reopenable_and_does_not_touch_execution(scenario):
    p = scenario
    service = QualityReviews(p.runs.store)
    run = await p.runs.get_run(p.actor, p.run["id"])
    before = {
        name: await inventory(p, name)
        for name in (
            "runs",
            "run.background.jobs",
            "budget.ledgers",
            "run.execution_clocks",
            "items",
        )
    }
    request = QualityFeedbackSave(
        run_id=run["id"],
        feedback_id="feedback-fixture",
        run_revision=run["revision"],
        input_revision=1,
        category="presentation",
        notes="Controlled feedback: the expected progress label is unclear.",
    )
    saved = await service.save_feedback(p.actor, request, meta("feedback-save", 0))
    assert saved["revision"] == 1
    assert await QualityReviews(p.runs.store).feedback(p.actor, run["id"]) == {"items": [saved]}
    assert await service.save_feedback(p.actor, request, meta("feedback-save", 0)) == saved
    changed = request.model_copy(update={"notes": "Controlled updated feedback."})
    updated = await service.save_feedback(p.actor, changed, meta("feedback-update", 1))
    assert updated["revision"] == 2 and updated["created_at"] == saved["created_at"]
    with pytest.raises(DomainError):
        await service.save_feedback(p.actor, changed, meta("feedback-stale", 1))
    with pytest.raises(DomainError):
        await service.feedback(p.actor.model_copy(update={"id": "another-person"}), run["id"])
    for name, data in before.items():
        assert await inventory(p, name) == data
    assert len(p.case.requests) == 0


@pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)
async def test_actual_sql_source_is_rebuilt_and_includes_original_reviewer_limits(
    scenario, tmp_path
):
    p = scenario
    frame = (await p.runs.store.get(p.actor, "intent.frames", p.run["task_id"])).payload
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "deliver",
                "text": "Controlled complete report.",
            }
        ),
        semantic_review(contract_from_frame(frame)["requirements"]),
    ]
    assert await p.queue.tick()
    current = await p.runs.get_run(p.actor, p.run["id"])
    await p.runs.control(
        p.actor,
        {
            "run_id": current["id"],
            "control": {
                "mode": "cancel",
                "preserve_refs": [],
                "reason": "End controlled source capture",
            },
        },
        meta("source-cancel", current["revision"]),
    )
    assert await p.queue.tick()
    rows = await read_run(p.runs.store.database, p.actor, current["id"])
    state = next(row for row in rows if row.namespace == "run.input_sets")
    source_input = next(
        row.payload["text"]
        for row in rows
        if row.namespace == "inputs" and row.id == state.payload["original_input_ref"]["id"]
    )
    case = parsed(
        Case,
        {
            "id": "actual-sql-capture",
            "version": "1",
            "split": "revision",
            "category": "office",
            "prompt": source_input,
            "rubric": {
                "expected_behavior": "deliver",
                "required_facts": ["Preserve request"],
                "allowed_assumptions": [],
                "retained_requirements": [],
                "critical": True,
            },
            "evidence": [],
            "review_status": "needs_human_review",
            "human_verification": None,
        },
    )
    policy = parsed(
        Policy,
        {
            "id": "retrospective-test",
            "registered_at": datetime.now(UTC).isoformat(),
            "reviewer_required": False,
            "baseline_required": True,
            "max_answer_error_rate": "0",
            "max_reviewer_miss_rate": "0",
            "max_unnecessary_block_rate": "0",
            "max_unsupported_execution_rate": "0",
        },
    )
    selection = next(row.id for row in rows if row.namespace == "agent.conversation.decisions")
    bundle = prepare_bundle(
        rows,
        case,
        policy,
        candidate_id="controlled-sql-source",
        source_commit="a" * 40,
        environment_hash="b" * 64,
        prompt_hash="c" * 64,
        selected_attempt=selection,
    )
    directory = tmp_path / "actual-capture"
    write_bundle(directory, bundle)
    origin = QualityOrigin(
        kind="actual_run",
        principal_id=p.actor.id,
        run_id=current["id"],
        run_revision=next(row.revision for row in rows if row.namespace == "runs"),
        input_revision=state.revision,
        source_commit="a" * 40,
    )
    operator = p.actor.model_copy(update={"kind": "service"})
    registered = await QualityReviews(p.runs.store).register(
        operator,
        p.actor,
        directory,
        origin,
        "Controlled persisted model source",
        meta("register-actual", 0),
    )
    details = registered["targets"][0]["verification_outputs"]
    assert len(details) == 1 and '"limitations"' in details[0]["text"]
    before = [(row.namespace, row.id, row.revision, row.payload) for row in rows]
    after = await read_run(p.runs.store.database, p.actor, current["id"])
    assert before == [(row.namespace, row.id, row.revision, row.payload) for row in after]
