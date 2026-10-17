"""Constructed experiment/capture data; never real human or model quality evidence."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from ops.conversation_experiment import main
from tests.unit.evaluation.factories import add_review, example_files, repin, write_files
from uaw.evaluation.io import EvaluationInputError, canonical, digest, parse_json
from uaw.evaluation.reader import record
from uaw.run.evaluation_experiment import (
    ExperimentDraft,
    ExperimentInputError,
    ExperimentRegistration,
    VersionPin,
    assemble_experiment,
    register_experiment,
)
from uaw.run.evaluation_review import ReviewSubmission, import_review, prepare_review

NOW = datetime(2026, 10, 17, 0, 0, 2, tzinfo=UTC)
FINISHED = NOW + timedelta(seconds=20)


@pytest.fixture
def experiment(tmp_path):
    first = example_files(tmp_path)
    suite = deepcopy(first["suite"])
    extra = deepcopy(suite["cases"][0])
    extra.update(id="office-extra", prompt="Another controlled task, not a genuine request.")
    suite["cases"].append(extra)
    candidate = {key: first["manifest"]["candidate"][key] for key in VersionPin.model_fields}
    baseline = {**deepcopy(candidate), "id": "controlled-baseline", "source_commit": "a" * 40}
    draft = record(
        ExperimentDraft,
        {
            "schema_version": "uaw.experiment-draft.v1",
            "id": "controlled-comparison",
            "suite": suite,
            "limits": {
                k: v
                for k, v in first["manifest"]["policy"].items()
                if k not in ("registered_at", "baseline_required")
            },
            "candidate": candidate,
            "baseline": baseline,
        },
    )
    registration = register_experiment(draft, tmp_path / "registered", now=NOW)
    sources = []
    original = {}
    for version in (draft.candidate, draft.baseline):
        for index, case in enumerate(suite["cases"]):
            data = deepcopy(first)
            data["suite"]["cases"] = [case]
            row = data["observations"][0]
            row.update(
                case_id=case["id"],
                manifest_id=version.id,
                attempt_id=version.id + "-" + case["id"],
                logical_request_id=version.id + "-" + case["id"],
                started_at=(NOW + timedelta(seconds=10 + index)).isoformat(),
                finished_at=(NOW + timedelta(seconds=11 + index)).isoformat(),
            )
            capture = data["manifest"]["candidate"]
            capture.update(
                **version.wire(), started_at=row["started_at"], finished_at=row["finished_at"]
            )
            capture["selections"] = [
                {
                    "case_id": case["id"],
                    "answer_attempt_id": row["attempt_id"],
                    "reviewer_attempt_id": None,
                }
            ]
            data["manifest"]["policy"] = registration.policy.wire()
            data = repin(add_review(data, correct=True, acceptable=True))
            for review in data["reviews"]:
                review["reviewed_at"] = FINISHED.isoformat()
            path = tmp_path / (version.id + "-" + case["id"])
            write_files(path, data)
            sources.append(path)
            original[path] = deepcopy(data)
    return SimpleNamespace(
        draft=draft, registered=registration, sources=tuple(sources), original=original
    )


def combine(p, output):
    return assemble_experiment(p.registered, p.sources, output, now=FINISHED)


def test_registration_uses_current_time_pins_conditions_and_does_not_claim_readiness(
    experiment, tmp_path
):
    registration = experiment.registered
    assert registration.registered_at == NOW.isoformat()
    assert registration.policy.registered_at == NOW.isoformat()
    assert registration.policy.baseline_required is True
    audit = parse_json((tmp_path / "registered/registration-audit.json").read_bytes())
    assert audit["release_readiness"] == "needs_case_review"
    assert len(audit["unreviewed_case_ids"]) == 2
    assert audit["new_model_calls"] == 0 and audit["release_gate_decided"] is False
    with pytest.raises(FileExistsError):
        register_experiment(experiment.draft, tmp_path / "registered", now=NOW)


def test_exact_multi_case_assembly_consumes_unchanged_C_evaluator_and_preserves_inputs(
    experiment, tmp_path
):
    before = {
        str(p / n): (p / n).read_bytes()
        for p in experiment.sources
        for n in ("suite.json", "manifest.json", "observations.jsonl", "reviews.jsonl")
    }
    report = combine(experiment, tmp_path / "assembled")
    assert report.candidate.attempt_count == report.baseline.attempt_count == 2
    assert report.comparison.status == "comparable"
    assert report.candidate.human_reviewed_cases == 0
    assert report.candidate.controlled_reviewed_cases == 2
    assert report.release_gate.status == "incomplete"
    assert report.candidate.costs[0].pending == "0.04"
    assert report.candidate.model_calls.known_total == 2
    assert before == {
        str(p / n): (p / n).read_bytes()
        for p in experiment.sources
        for n in ("suite.json", "manifest.json", "observations.jsonl", "reviews.jsonl")
    }
    assert (
        parse_json((tmp_path / "assembled/assembly-audit.json").read_bytes())[
            "human_reviews_created"
        ]
        == 0
    )
    with pytest.raises(FileExistsError):
        combine(experiment, tmp_path / "assembled")


@pytest.mark.parametrize("mode", ["failed", "unknown", "retried"])
def test_failed_unknown_and_retried_calls_are_never_omitted_or_free(experiment, tmp_path, mode):
    p = experiment
    source = p.sources[0]
    data = deepcopy(p.original[source])
    original = data["observations"][0]
    failure = deepcopy(original)
    failure.update(
        status="unknown" if mode == "unknown" else "failed",
        output=None,
        failure_code="controlled_provider_outcome",
    )
    failure["usage"].update(money=None, billing_state="unknown", input_tokens=None)
    if mode == "retried":
        original.update(attempt_number=2, attempt_id=original["attempt_id"] + "-retry")
        data["observations"] = [failure, original]
        data["manifest"]["candidate"]["selections"][0]["answer_attempt_id"] = original["attempt_id"]
        data["reviews"] = []
        data = add_review(data, correct=True, acceptable=True)
        for review in data["reviews"]:
            review["reviewed_at"] = FINISHED.isoformat()
    else:
        data["observations"] = [failure]
        data["manifest"]["candidate"]["selections"][0]["answer_attempt_id"] = None
        data["reviews"] = []
    write_files(source, repin(data))
    report = combine(p, tmp_path / "with-failure")
    assert report.candidate.attempt_count == (3 if mode == "retried" else 2)
    assert report.candidate.failure_count == (0 if mode == "unknown" else 1)
    assert report.candidate.unknown_count == int(mode == "unknown")
    assert report.candidate.retry_count == int(mode == "retried")
    assert report.candidate.costs[0].unknown_money_attempts == 1
    assert report.release_gate.status != "passed"


@pytest.mark.parametrize(
    "change",
    [
        "case",
        "model",
        "environment",
        "source",
        "prompt",
        "policy",
        "before",
        "missing_attempt",
        "output_hash",
    ],
)
def test_changed_fixed_sources_or_pre_registration_calls_rejected(experiment, tmp_path, change):
    p = experiment
    source = p.sources[0]
    data = deepcopy(p.original[source])
    capture = data["manifest"]["candidate"]
    if change == "case":
        data["suite"]["cases"][0]["prompt"] += " changed"
        data = repin(data)
    elif change == "model":
        capture["model"]["configuration_sha256"] = "9" * 64
    elif change == "environment":
        capture["environment_sha256"] = "9" * 64
    elif change == "source":
        capture["source_commit"] = "9" * 40
    elif change == "prompt":
        capture["prompts"][0]["sha256"] = "9" * 64
    elif change == "policy":
        data["manifest"]["policy"]["max_answer_error_rate"] = "1"
    elif change == "before":
        capture["started_at"] = "2026-10-17T00:00:00Z"
    elif change == "missing_attempt":
        capture["attempts"] = []
    else:
        data["observations"][0]["output"]["text"] = "Replaced actual answer."
    write_files(source, data)
    with pytest.raises(ExperimentInputError):
        combine(p, tmp_path / "rejected")
    assert not (tmp_path / "rejected").exists()


@pytest.mark.parametrize("mode", ["missing", "duplicate"])
def test_coverage_cannot_silently_drop_a_case_or_reuse_capture(experiment, tmp_path, mode):
    sources = (
        experiment.sources[:-1]
        if mode == "missing"
        else experiment.sources[:-1] + (experiment.sources[0],)
    )
    with pytest.raises(ExperimentInputError):
        assemble_experiment(experiment.registered, sources, tmp_path / "bad-coverage", now=FINISHED)


@pytest.mark.parametrize("change", ["backdate", "environment", "same_id", "duplicate_prompt"])
def test_draft_disallows_supplied_registration_time_and_incomparable_conditions(experiment, change):
    raw = deepcopy(experiment.draft.wire())
    if change == "backdate":
        raw["registered_at"] = "2020-01-01T00:00:00Z"
    elif change == "environment":
        raw["baseline"]["environment_sha256"] = "9" * 64
    elif change == "same_id":
        raw["baseline"]["id"] = raw["candidate"]["id"]
    else:
        raw["candidate"]["prompts"] *= 2
    with pytest.raises(EvaluationInputError):
        record(ExperimentDraft, raw)


def test_registration_policy_cannot_be_relaxed_after_fixed_time(experiment):
    raw = experiment.registered.wire()
    raw["policy"]["baseline_required"] = False
    with pytest.raises(EvaluationInputError):
        record(ExperimentRegistration, raw)


def test_cli_keeps_incomplete_exit_code(experiment, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "conversation_experiment.py",
            "assemble",
            "--registration",
            str(tmp_path / "registered/registration.json"),
            "--output",
            str(tmp_path / "cli-assembled"),
            *[part for source in experiment.sources for part in ("--capture", str(source))],
        ],
    )
    assert main() == 3
    result = parse_json(capsys.readouterr().out.encode())
    assert result["candidate_attempts"] == result["baseline_attempts"] == 2
    assert result["new_model_calls"] == 0


def test_cli_register_records_actual_time_and_rejects_user_timestamp(
    experiment, tmp_path, monkeypatch, capsys
):
    path = tmp_path / "draft.json"
    path.write_bytes(canonical(experiment.draft.wire()))
    args = [
        "conversation_experiment.py",
        "register",
        "--draft",
        str(path),
        "--output",
        str(tmp_path / "cli-registered"),
    ]
    monkeypatch.setattr("sys.argv", args)
    before = datetime.now(UTC)
    assert main() == 0
    after = datetime.now(UTC)
    result = parse_json(capsys.readouterr().out.encode())
    assert before <= datetime.fromisoformat(result["registered_at"]) <= after
    assert result["unreviewed_cases"] == 2
    monkeypatch.setattr("sys.argv", [*args, "--registered-at", NOW.isoformat()])
    with pytest.raises(SystemExit) as rejected:
        main()
    assert rejected.value.code == 2


def test_prior_human_case_verification_is_preserved_when_reviewing_answer(experiment, tmp_path):
    # Synthetic human schema branch; does not represent a real person's act.
    source = experiment.sources[0]
    data = deepcopy(experiment.original[source])
    case = data["suite"]["cases"][0]
    case.update(
        review_status="human_verified",
        human_verification={
            "reviewer_id": "constructed-case-verifier",
            "reviewed_at": NOW.isoformat(),
            "rubric_sha256": digest(case["rubric"]),
            "evidence_sha256": [e["sha256"] for e in case["evidence"]],
            "record_locator": "fixture-only-not-human-evidence",
        },
    )
    data["reviews"] = []
    write_files(source, repin(data))
    packet = prepare_review(source, tmp_path / "review-packet", now=FINISHED)
    submission = record(
        ReviewSubmission,
        {
            "schema_version": "uaw.human-review-submission.v1",
            "packet_sha256": digest(packet.wire()),
            "reviewer_id": "constructed-answer-verifier",
            "reviewed_at": (FINISHED + timedelta(seconds=1)).isoformat(),
            "human_attested": True,
            "items": [
                {
                    "case_id": case["id"],
                    "attempt_id": data["observations"][0]["attempt_id"],
                    "case_review": "verified",
                    "evidence_reviewed": True,
                    "labels": {
                        "answer_correct": True,
                        "unnecessary_block": False,
                        "unsupported_execution": False,
                        "requirements_preserved": True,
                        "acceptable": True,
                        "critical_error": False,
                    },
                    "notes": "Constructed format branch, not a human assertion.",
                }
            ],
        },
    )
    import_review(
        source,
        packet,
        submission,
        tmp_path / "reviewed",
        now=FINISHED + timedelta(seconds=2),
        basis="human_evidence_review",
    )
    actual = parse_json((tmp_path / "reviewed/suite.json").read_bytes())["cases"][0]
    assert actual == case
