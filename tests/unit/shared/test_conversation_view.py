"""Discovery binds concrete questions to the current Run, not message text."""

import copy
import json

import pytest
from pydantic import ValidationError

from tests.unit.shared.test_conversation_contracts import sample
from uaw.shared.conversation import RunConversationView


def view() -> dict:
    run = sample("RunRecord")
    run.update(revision=4, status="waiting_for_user")
    question = sample("ClarificationView")
    question.update(run_revision=4, run_status="waiting_for_user", input_revision=1)
    question["question"].update(
        run_id=run["id"], conversation_id=run["conversation_id"], input_revision=1, state="open"
    )
    return {
        "protocol": "conversation-v1",
        "run": run,
        "input_revision": 1,
        "question": question,
        "continuation_request_ids": [],
    }


def test_discovery_exposes_the_persisted_question_without_guessing_messages() -> None:
    data = view()
    parsed = RunConversationView.model_validate_json(json.dumps(data))
    assert parsed.question is not None
    assert parsed.question.question.item_id == data["question"]["question"]["item_id"]


@pytest.mark.parametrize(
    "field,value",
    [("run_id", "another-run"), ("conversation_id", "another-conversation"), ("state", "answered")],
)
def test_another_run_or_closed_question_cannot_be_exposed_as_current(field, value) -> None:
    data = view()
    data["question"]["question"][field] = value
    with pytest.raises(ValidationError):
        RunConversationView.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("field,value", [("run_revision", 3), ("input_revision", 2)])
def test_discovery_rejects_mixed_read_versions(field, value) -> None:
    data = view()
    data["question"][field] = value
    with pytest.raises(ValidationError):
        RunConversationView.model_validate_json(json.dumps(data))


def test_no_question_is_omitted_and_not_conflated_with_approval_or_acceptance() -> None:
    data = view()
    data.pop("question")
    data["run"]["status"] = "completed"
    data["run"]["outcome"] = "succeeded"
    data["run"]["ended_at"] = data["run"]["created_at"]
    parsed = RunConversationView.model_validate_json(json.dumps(data))
    assert "question" not in parsed.wire()
    with pytest.raises(ValidationError):
        RunConversationView.model_validate_json(json.dumps({**data, "question": None}))
    data["continuation_request_ids"] = ["request-1", "request-1"]
    with pytest.raises(ValidationError):
        RunConversationView.model_validate_json(json.dumps(copy.deepcopy(data)))
