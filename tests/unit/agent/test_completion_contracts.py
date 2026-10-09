import pytest

from uaw.agent.completion.contracts import contract_from_frame, report_outcome
from uaw.agent.completion.evidence import external_links


def frame():
    return {
        "task_id": "task",
        "revision": 1,
        "original_input_ref": {"kind": "input", "id": "input", "version": "1"},
        "patch_refs": [],
        "goal": "Explain uncertainty using the supplied material.",
        "constraints": [],
        "output_specs": [],
        "assumptions": [],
        "unresolved": [],
        "evidence_refs": [],
        "created_at": "2026-10-09T00:00:00Z",
    }


def report(state="passed", check_state="passed"):
    pin = {"kind": "artifact", "id": "artifact", "version": "1"}
    return {
        "id": "report",
        "contract_ref": pin,
        "target_refs": [pin],
        "outcome": "blocked",
        "limitations": [],
        "created_at": "2026-10-09T00:00:00Z",
        "checks": [
            {
                "id": "check",
                "kind": "structure",
                "requirement_ids": [],
                "state": check_state,
                "target_refs": [pin],
                "evidence_refs": [pin],
                "summary": "Actual check",
            }
        ],
        "verdicts": [
            {
                "requirement_id": "original-request",
                "state": state,
                "evidence_refs": [pin],
                "reason": "Observed result",
                "limitations": [],
            }
        ],
    }


def test_contract_keeps_original_goal_and_explicit_acceptance():
    value = frame()
    contract = contract_from_frame(value, acceptance_required=True)
    assert contract["goal"] == value["goal"]
    assert contract["requirements"][0]["source_refs"] == [value["original_input_ref"]]
    assert contract["acceptance_required"]


@pytest.mark.parametrize(
    ("state", "expected"),
    [("passed", "succeeded"), ("failed", "failed"), ("not_run", "blocked"), ("blocked", "blocked")],
)
def test_missing_or_failed_evidence_never_passes(state, expected):
    assert report_outcome(contract_from_frame(frame()), report(state)) == expected


def test_missing_coverage_and_unexecuted_check_block_completion():
    value = report()
    value["verdicts"] = []
    assert report_outcome(contract_from_frame(frame()), value) == "blocked"
    assert report_outcome(contract_from_frame(frame()), report(check_state="not_run")) == "blocked"


def test_unresolved_web_link_detection_is_not_a_semantic_pass():
    assert external_links("[source](https://example.org/paper) https://example.org/paper") == (
        "https://example.org/paper",
    )


def test_free_text_output_is_a_reviewed_requirement_not_an_unknown_format():
    value = frame()
    value["output_specs"] = [
        {"id": "todos", "kind": "三条简短待办", "description": "保留星期", "required": True}
    ]
    contract = contract_from_frame(value)
    assert contract["requirements"][-1]["id"] == "output-todos"
    assert contract["requirements"][-1]["mandatory"]
    assert "保留星期" in contract["requirements"][-1]["text"]
