"""Synthetic assertions only; no genuine human review or actual quality claim."""

import base64
import hashlib
from copy import deepcopy
from datetime import UTC, datetime, timedelta

import pytest

from ops.conversation_review import main
from tests.unit.evaluation.factories import example_files, repin, write_files
from uaw.evaluation.io import EvaluationInputError, canonical, digest, parse_json
from uaw.evaluation.reader import load_bundle, record
from uaw.evaluation.runner import evaluate_files
from uaw.run.evaluation_review import (
    ReviewInputError,
    ReviewSubmission,
    import_review,
    prepare_review,
)

NOW = datetime(2026, 10, 17, 12, tzinfo=UTC)


@pytest.fixture
def prepared(tmp_path):
    source = tmp_path / "source"
    data = example_files(source)
    write_files(source, data)
    packet = prepare_review(source, tmp_path / "packet", now=NOW)
    submission = {
        "schema_version": "uaw.human-review-submission.v1",
        "packet_sha256": digest(packet.wire()),
        "reviewer_id": "controlled-unit-fixture-not-a-person",
        "reviewed_at": (NOW + timedelta(seconds=1)).isoformat(),
        "human_attested": True,
        "items": [
            {
                "case_id": "office-total",
                "attempt_id": "answer-1",
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
                "notes": "Synthetic protocol assertion, not actual human evidence review.",
            }
        ],
    }
    return source, data, packet, submission


def consume(prepared, output, *, basis="controlled_test", submission=None):
    source, _, packet, raw = prepared
    return import_review(
        source,
        packet,
        record(ReviewSubmission, submission or raw),
        output,
        now=NOW + timedelta(seconds=2),
        basis=basis,
    )


def test_prepare_binds_actual_selected_answer_without_creating_or_prefilling_reviews(
    prepared, tmp_path
):
    source, _, packet, _ = prepared
    assert len(packet.targets) == 1 and (source / "reviews.jsonl").read_bytes() == b""
    page = (tmp_path / "packet/index.html").read_text(encoding="utf-8")
    script = page.split("<script id=review-code>", 1)[1].split("</script>", 1)[0]
    expected = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    assert "script-src 'sha256-" + expected + "'" in page
    assert 'value="true" selected' not in page and "checked>" not in page
    assert "不上传材料" in page and "form-action 'none'" in page
    assert "fetch(" not in script and "innerHTML" not in script
    assert not (tmp_path / "packet/reviews.jsonl").exists()
    with pytest.raises(FileExistsError):
        prepare_review(source, tmp_path / "packet", now=NOW)


def test_controlled_import_preserves_every_attempt_and_cannot_grant_human_status(
    prepared, tmp_path
):
    source = prepared[0]
    before = {p.name: p.read_bytes() for p in source.iterdir()}
    output = tmp_path / "imported"
    assert consume(prepared, output) == 1
    bundle = load_bundle(
        *(
            output / n
            for n in ("suite.json", "manifest.json", "observations.jsonl", "reviews.jsonl")
        )
    )
    report = evaluate_files(
        *(
            output / n
            for n in ("suite.json", "manifest.json", "observations.jsonl", "reviews.jsonl")
        )
    )
    assert bundle.suite.cases[0].review_status == "needs_human_review"
    assert report.candidate.human_reviewed_cases == 0
    assert report.candidate.controlled_reviewed_cases == 1
    assert report.release_gate.status != "passed"
    assert (output / "observations.jsonl").read_bytes() == before["observations.jsonl"]
    assert before == {p.name: p.read_bytes() for p in source.iterdir()}
    with pytest.raises(FileExistsError):
        consume(prepared, output)


def test_synthetic_human_contract_branch_rebinds_suite_and_exact_answer(prepared, tmp_path):
    # Exercise a format branch using constructed data only; not a product human act.
    output = tmp_path / "synthetic-human-format"
    consume(prepared, output, basis="human_evidence_review")
    bundle = load_bundle(
        *(
            output / n
            for n in ("suite.json", "manifest.json", "observations.jsonl", "reviews.jsonl")
        )
    )
    case, review = bundle.suite.cases[0], bundle.reviews[0]
    assert case.review_status == "human_verified"
    assert review.case_sha256 == digest(case.wire())
    assert review.output_sha256 == prepared[2].targets[0].output_sha256
    assert bundle.manifest.candidate.suite_sha256 == digest(bundle.suite.wire())
    audit = parse_json((output / "review-import.json").read_bytes())
    assert audit["human_identity_authenticated"] is False


@pytest.mark.parametrize("change", ["packet", "case", "duplicate", "acceptable", "future", "blank"])
def test_submission_rejects_wrong_binding_inconsistent_or_invented_records(
    prepared, tmp_path, change
):
    submitted = deepcopy(prepared[3])
    if change == "packet":
        submitted["packet_sha256"] = "0" * 64
    elif change == "case":
        submitted["items"][0]["case_id"] = "another-case"
    elif change == "duplicate":
        submitted["items"] *= 2
    elif change == "acceptable":
        submitted["items"][0]["labels"]["answer_correct"] = False
    elif change == "future":
        submitted["reviewed_at"] = (NOW + timedelta(hours=1)).isoformat()
    else:
        submitted["items"][0]["notes"] = "  "
    with pytest.raises(ReviewInputError):
        consume(prepared, tmp_path / "rejected", submission=submitted)
    assert not (tmp_path / "rejected").exists()


def test_changed_source_cannot_reuse_previous_packet(prepared, tmp_path):
    source, data, _, _ = prepared
    changed = deepcopy(data)
    changed["observations"][0]["output"]["text"] = "Different actual response."
    write_files(source, repin(changed))
    with pytest.raises(ReviewInputError, match="packet_source_mismatch"):
        consume(prepared, tmp_path / "wrong-source")


def test_disputed_criteria_remain_unverified_and_unknown_facts_remain_unknown(prepared, tmp_path):
    value = deepcopy(prepared[3])
    value["items"][0]["case_review"] = "needs_revision"
    value["items"][0]["labels"].update(answer_correct=None, acceptable=None)
    output = tmp_path / "disputed"
    consume(prepared, output, basis="human_evidence_review", submission=value)
    suite = parse_json((output / "suite.json").read_bytes())
    review = parse_json((output / "reviews.jsonl").read_bytes().strip())
    assert suite["cases"][0]["human_verification"] is None
    assert review["labels"]["answer_correct"] is None


@pytest.mark.parametrize("change", ["script", "source_hash", "answer_hash", "no_answer"])
def test_source_injection_and_integrity_guards(tmp_path, change):
    source = tmp_path / "source"
    data = example_files(source)
    if change == "script":
        data["observations"][0]["output"]["text"] = '</script><script>fetch("bad")</script>'
        data = repin(data)
    elif change == "source_hash":
        data["suite"]["cases"][0]["evidence"][0]["text"] = "Changed source"
        data = repin(data)
    elif change == "answer_hash":
        data["observations"][0]["output"]["text"] = "Changed answer"
    else:
        data["manifest"]["candidate"]["selections"][0]["answer_attempt_id"] = None
    write_files(source, data)
    if change != "script":
        with pytest.raises(ReviewInputError):
            prepare_review(source, tmp_path / "packet", now=NOW)
        return
    prepare_review(source, tmp_path / "packet", now=NOW)
    page = (tmp_path / "packet/index.html").read_text(encoding="utf-8")
    embedded = page.split('<script id=review-data type="application/json">', 1)[1].split(
        "</script>", 1
    )[0]
    assert "<script>" not in embedded and "\\u003c/script>" in embedded


@pytest.mark.parametrize("mode", ["without_human_ack", "controlled_import"])
def test_cli_refuses_unacknowledged_human_input_and_consumes_controlled_fixture(
    prepared, tmp_path, monkeypatch, capsys, mode
):
    source = prepared[0]
    submission = tmp_path / "synthetic-submission.json"
    submission.write_bytes(canonical(prepared[3]))
    output = tmp_path / "cli-output"
    monkeypatch.setattr(
        "sys.argv",
        [
            "conversation_review.py",
            "import",
            "--source",
            str(source),
            "--packet",
            str(tmp_path / "packet/packet.json"),
            "--submission",
            str(submission),
            "--output",
            str(output),
            "--basis",
            "human_evidence_review" if mode == "without_human_ack" else "controlled_test",
        ],
    )
    code = main()
    result = parse_json(capsys.readouterr().out.encode())
    if mode == "without_human_ack":
        assert code == 2 and result["error"] == "review_operation_rejected"
        assert result["code"] == "explicit_operator_acknowledgement_required"
        assert not output.exists()
    else:
        assert code == 0 and result["basis"] == "controlled_test"
        assert result["human_identity_authenticated"] is False
        assert result["new_model_calls"] == 0
    assert "notes" not in result and "reviewer_id" not in result


@pytest.mark.parametrize(
    "change",
    ["attestation", "evidence", "numeric_attestation", "numeric_evidence", "critical", "extra"],
)
def test_incomplete_assertions_do_not_validate_as_human_submission(prepared, change):
    raw = deepcopy(prepared[3])
    if change == "attestation":
        raw["human_attested"] = False
    elif change == "evidence":
        raw["items"][0]["evidence_reviewed"] = False
    elif change == "numeric_attestation":
        raw["human_attested"] = 1
    elif change == "numeric_evidence":
        raw["items"][0]["evidence_reviewed"] = 1
    elif change == "critical":
        raw["items"][0]["labels"]["critical_error"] = None
    else:
        raw["approve_release"] = True
    with pytest.raises(EvaluationInputError):
        record(ReviewSubmission, raw)
