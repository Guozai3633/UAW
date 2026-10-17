"""Only the supplied immutable inventory may identify attempts and their labels."""

from copy import deepcopy

import pytest

from tests.unit.evaluation.factories import add_review, example_files, repin, write_files
from uaw.evaluation.io import EvaluationInputError
from uaw.evaluation.runner import evaluate_files


@pytest.mark.parametrize(
    "target", ["same_attempt", "same_request_number", "same_review_target", "same_review_id"]
)
def test_duplicate_attempts_or_ground_truth_are_rejected_not_double_billed(tmp_path, target):
    data = add_review(example_files(tmp_path))
    if target.startswith("same_review"):
        other = deepcopy(data["reviews"][0])
        if target == "same_review_target":
            other["id"] = "different-review-id"
        data["reviews"].append(other)
    else:
        other = deepcopy(data["observations"][0])
        if target == "same_request_number":
            other["attempt_id"] = "another-attempt-id"
        data["observations"].append(other)
    with pytest.raises(EvaluationInputError, match="duplicate_attempt_or_review"):
        evaluate_files(*write_files(tmp_path, data))


@pytest.mark.parametrize(
    "target",
    [
        "omitted_row",
        "extra_row",
        "sequence_gap",
        "case_version",
        "not_preregistered",
        "inventory_incomplete",
        "dirty",
    ],
)
def test_incomplete_inventory_or_version_remains_incomplete_not_success(tmp_path, target):
    data = example_files(tmp_path)
    manifest = data["manifest"]["candidate"]
    if target == "omitted_row":
        data["observations"] = []
    elif target == "extra_row":
        row = deepcopy(data["observations"][0])
        row.update(attempt_id="extra", logical_request_id="extra-request")
        data["observations"].append(row)
    elif target == "sequence_gap":
        data["observations"][0]["attempt_number"] = 2
        data = repin(data)
    elif target == "case_version":
        data["observations"][0]["case_version"] = "wrong"
        data = repin(data)
    elif target == "not_preregistered":
        data["manifest"]["policy"]["registered_at"] = "2026-10-17T00:00:01Z"
    elif target == "inventory_incomplete":
        manifest["inventory_complete"] = False
    else:
        manifest.update(dirty=True, working_tree_sha256="0" * 64)
    report = evaluate_files(*write_files(tmp_path, data))
    assert report.release_gate.status == "incomplete"
    assert report.integrity_issues


def test_future_review_or_foreign_case_does_not_authorize_a_selected_output(tmp_path):
    data = add_review(example_files(tmp_path), correct=True, acceptable=True)
    data["reviews"][0]["case_id"] = "foreign"
    report = evaluate_files(*write_files(tmp_path, data))
    assert report.candidate.human_reviewed_cases == 0
    assert report.candidate.answer_error.value is None


def test_review_before_actual_output_cannot_grade_a_later_attempt(tmp_path):
    data = add_review(example_files(tmp_path), correct=True, acceptable=True)
    data["reviews"][0]["reviewed_at"] = "2026-10-16T23:59:59Z"
    report = evaluate_files(*write_files(tmp_path, data))
    assert report.candidate.answer_error.value is None
    assert "review_binding_mismatch" in report.release_gate.reasons
