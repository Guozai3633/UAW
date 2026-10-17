"""Assess only supplied independent labels; missing evidence never becomes success."""

from tests.unit.evaluation.factories import example_files, write_files
from uaw.evaluation.runner import evaluate_files


def test_unreviewed_sample_with_pending_cost_is_incomplete_and_has_no_fake_zero_error(tmp_path):
    files = write_files(tmp_path, example_files(tmp_path))
    report = evaluate_files(*files)
    assert report.release_gate.status == "incomplete"
    assert report.candidate.answer_error.value is None
    assert report.candidate.reviewer_miss.status == "not_applicable"
    assert report.candidate.costs[0].confirmed == "0"
    assert report.candidate.costs[0].pending == "0.02"
    assert report.candidate.costs[0].confirmed_per_acceptable_output is None
