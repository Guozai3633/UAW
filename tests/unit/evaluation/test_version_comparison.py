"""Do not hide source/model/environment mismatches behind a generic pending flag."""

from copy import deepcopy

import pytest

from tests.unit.evaluation.factories import add_review, example_files, write_files
from uaw.evaluation.runner import evaluate_files


@pytest.mark.parametrize("field", ["model", "environment_sha256", "suite_sha256", "provenance"])
def test_incomparable_baseline_has_its_own_gate_reason_and_no_fake_delta(tmp_path, field):
    data = example_files(tmp_path)
    baseline = deepcopy(data["manifest"]["candidate"])
    baseline.update(id="baseline", attempts=[], selections=[])
    if field == "model":
        baseline["model"]["model_id"] = "another-model"
    elif field == "provenance":
        baseline["provenance"] = "actual_candidate"
    else:
        baseline[field] = "0" * 64
    data["manifest"]["baseline"] = baseline
    report = evaluate_files(*write_files(tmp_path, data))
    assert report.comparison.status == "incomparable"
    assert field + "_differs" in report.comparison.reasons
    assert report.comparison.candidate_minus_baseline == {}
    assert "incomparable_baseline" in report.release_gate.reasons


def test_known_critical_error_is_blocked_while_unreviewed_scope_is_still_visible(tmp_path):
    data = add_review(example_files(tmp_path), correct=False, critical=True)
    report = evaluate_files(*write_files(tmp_path, data))
    assert report.release_gate.status == "blocked"
    assert "sample_needs_human_review" in report.release_gate.reasons
    assert report.candidate.answer_error.status == "provisional"


def test_baseline_known_failure_is_compared_but_does_not_become_candidate_failure(tmp_path):
    data = add_review(example_files(tmp_path), correct=True, acceptable=True)
    baseline = deepcopy(data["manifest"]["candidate"])
    baseline["id"] = "baseline"
    data["manifest"]["baseline"] = baseline
    row = deepcopy(data["observations"][0])
    row.update(manifest_id="baseline", active_ms=800)
    row["output"]["text"] = "构造的旧版错误输出。"
    data["observations"].append(row)
    review = deepcopy(data["reviews"][0])
    review.update(manifest_id="baseline", id="controlled-baseline-review")
    review["labels"].update(answer_correct=False, critical_error=True, acceptable=False)
    from uaw.evaluation.io import digest

    review["output_sha256"] = digest(row["output"])
    data["reviews"].append(review)
    from tests.unit.evaluation.factories import repin

    report = evaluate_files(*write_files(tmp_path, repin(data)))
    assert report.comparison.status == "comparable"
    assert report.comparison.candidate_minus_baseline["answer_error"] == "-1"
    assert report.comparison.candidate_minus_baseline["active_ms"] == "-400"
    assert report.comparison.candidate_minus_baseline["reviewer_miss"] is None
    assert "critical_answer_error" not in report.release_gate.reasons
    assert report.release_gate.status == "incomplete"  # both fixtures, never real human approval


def test_threshold_uses_exact_fraction_not_the_rounded_display_rate(tmp_path):
    from tests.unit.evaluation.factories import repin
    from uaw.evaluation.io import digest

    data = add_review(example_files(tmp_path), correct=False)
    original_case = data["suite"]["cases"][0]
    original_row = data["observations"][0]
    original_review = data["reviews"][0]
    for i in (2, 3):
        case = deepcopy(original_case)
        case["id"] = f"case-{i}"
        data["suite"]["cases"].append(case)
        row = deepcopy(original_row)
        row.update(case_id=case["id"], attempt_id=f"answer-{i}", logical_request_id=f"request-{i}")
        data["observations"].append(row)
        review = deepcopy(original_review)
        review.update(
            id=f"review-{i}",
            case_id=case["id"],
            case_sha256=digest(case),
            attempt_id=row["attempt_id"],
        )
        review["labels"].update(answer_correct=True, acceptable=True)
        data["reviews"].append(review)
        data["manifest"]["candidate"]["selections"].append(
            {
                "case_id": case["id"],
                "answer_attempt_id": row["attempt_id"],
                "reviewer_attempt_id": None,
            }
        )
    data["manifest"]["policy"]["max_answer_error_rate"] = "0.33333333"
    data = repin(data)
    # Every review must also pin its current sample and unchanged output.
    report = evaluate_files(*write_files(tmp_path, data))
    assert report.candidate.answer_error.value == "0.33333333"
    assert (report.candidate.answer_error.numerator, report.candidate.answer_error.denominator) == (
        1,
        3,
    )
    assert "answer_error_threshold_exceeded" in report.release_gate.reasons
