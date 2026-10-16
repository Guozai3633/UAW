import copy
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as SchemaValidationError
from pydantic import ValidationError

from uaw.agent.contracts import validate_decision
from uaw.run.conversation_protocol import validate_control_boundary
from uaw.shared.contracts import Principal, RequestMeta
from uaw.shared.conversation import (
    ClarificationQuestion,
    ClarificationView,
    ConversationProtocolBinding,
    ConversationRequestMeta,
    FirstDecisionRecord,
    ReplyCommitReceipt,
    RunClarificationAnswerRequest,
    RunContinuationReceipt,
    RunExecutionClock,
    RunInputPatch,
    first_decision_schema,
)
from uaw.shared.errors import DomainError
from uaw.shared.schema import ContractViolation, validate_contract

ROOT = Path(__file__).resolve().parents[3]


def sample(name: str) -> dict:
    examples = json.loads((ROOT / "contracts/examples.json").read_text(encoding="utf-8"))
    return copy.deepcopy(examples["examples"][name])


@pytest.mark.parametrize("action", ["reply", "tool", "ask", "deliver"])
def test_first_decision_has_one_exact_action_without_second_understanding_call(action: str) -> None:
    names = {
        "reply": "FirstReplyDecision",
        "tool": "FirstToolDecision",
        "ask": "FirstAskDecision",
        "deliver": "FirstDeliverDecision",
    }
    decision = sample(names[action])
    validate_contract("FirstDecision", decision)
    validator = Draft202012Validator(first_decision_schema(), format_checker=FormatChecker())
    assert validator.is_valid(decision)
    decision["approved"] = True
    assert not validator.is_valid(decision)
    with pytest.raises(ContractViolation):
        validate_contract("FirstDecision", decision)


@pytest.mark.parametrize(
    "injected",
    [
        {"question": {"text": "which?"}},
        {"calls": []},
        {"principal": "admin"},
        {"model_policy_ref": {}},
    ],
)
def test_reply_rejects_other_actions_and_runtime_authority(injected: dict) -> None:
    with pytest.raises(ContractViolation):
        validate_contract("FirstDecision", {**sample("FirstReplyDecision"), **injected})


def test_source_record_is_strict_and_legacy_actions_remain_separate() -> None:
    value = sample("FirstDecisionRecord")
    actual = FirstDecisionRecord.model_validate_json(json.dumps(value))
    assert actual.decision.action == "reply"
    with pytest.raises(SchemaValidationError):
        validate_decision({"action": "reply", "text": "answer", "proposed_calls": []})
    assert validate_decision({"action": "respond", "text": "answer", "proposed_calls": []})
    with pytest.raises(ContractViolation):
        validate_contract("FirstDecision", {"action": "respond", "text": "answer"})


@pytest.mark.parametrize("revision", [0, True, "1", -1, 1.5, None])
def test_new_control_meta_requires_strict_positive_original_run_cas(revision: object) -> None:
    with pytest.raises(ValidationError):
        ConversationRequestMeta.model_validate(
            {
                "request_id": "answer-1",
                "schema_version": "0.2",
                "expected_revision": revision,
            }
        )


def test_control_versions_cannot_be_sent_to_other_generations() -> None:
    old = {"request_id": "a", "schema_version": "0.1", "expected_revision": 1}
    new = {**old, "schema_version": "0.2"}
    RequestMeta.model_validate(old)
    ConversationRequestMeta.model_validate(new)
    with pytest.raises(ValidationError):
        RequestMeta.model_validate(new)
    with pytest.raises(ValidationError):
        ConversationRequestMeta.model_validate(old)


@pytest.mark.parametrize(
    "extra", [{"approved": True}, {"principal_id": "admin"}, {"deadline": "2030-01-01T00:00:00Z"}]
)
def test_answer_cannot_create_authority_or_extend_deadline(extra: dict) -> None:
    data = {**sample("RunClarificationAnswerRequest"), **extra}
    with pytest.raises(ValidationError):
        RunClarificationAnswerRequest.model_validate_json(json.dumps(data))


def test_answer_requires_text_or_existing_authorized_materials() -> None:
    value = sample("RunClarificationAnswerRequest")
    value.update(text="   ", attachment_refs=[])
    with pytest.raises(ContractViolation):
        validate_contract("RunClarificationAnswerRequest", value)
    value["text"] = "I mean the coordination protocol."
    RunClarificationAnswerRequest.model_validate_json(json.dumps(value))
    value.update(text="", attachment_refs=[{"kind": "input", "id": "input-2", "version": "1"}])
    # Shape acceptance is not a material permission grant; service must recheck the source.
    RunClarificationAnswerRequest.model_validate_json(json.dumps(value))


def test_open_question_must_match_current_run_wait_and_input_version() -> None:
    value = sample("ClarificationView")
    ClarificationView.model_validate_json(json.dumps(value))
    with pytest.raises(ValidationError):
        ClarificationView.model_validate_json(json.dumps({**value, "run_status": "cancelled"}))
    with pytest.raises(ValidationError):
        ClarificationView.model_validate_json(json.dumps({**value, "input_revision": 2}))


def patch() -> dict:
    value = sample("RunInputPatch")
    value.update(
        base_input_revision=1,
        input_revision=2,
        question_item_id="question-1",
        question_revision=1,
        state="accepted",
    )
    return value


def test_patch_is_append_only_and_acceptance_does_not_claim_application() -> None:
    value = patch()
    RunInputPatch.model_validate_json(json.dumps(value))
    for bad in [
        dict(value, input_revision=1),
        dict(value, input_revision=3),
        dict(value, state="applied"),
        dict(value, applied_at=value["created_at"]),
        dict(value, kind="correction"),
    ]:
        with pytest.raises(ValidationError):
            RunInputPatch.model_validate_json(json.dumps(bad))


def test_reply_and_continuation_receipts_do_not_cross_runs_or_conversations() -> None:
    reply = sample("ReplyCommitReceipt")
    reply["item"].update(run_id=reply["run"]["id"])
    ReplyCommitReceipt.model_validate_json(json.dumps(reply))
    for field in ("run_id", "conversation_id"):
        bad = copy.deepcopy(reply)
        bad["item"][field] = "other"
        with pytest.raises(ValidationError):
            ReplyCommitReceipt.model_validate_json(json.dumps(bad))
    continuation = sample("RunContinuationReceipt")
    continuation["patch"] = {
        **patch(),
        "run_id": continuation["run"]["id"],
        "conversation_id": continuation["run"]["conversation_id"],
    }
    RunContinuationReceipt.model_validate_json(json.dumps(continuation))
    continuation["patch"]["run_id"] = "other"
    with pytest.raises(ValidationError):
        RunContinuationReceipt.model_validate_json(json.dumps(continuation))


def clock() -> dict:
    return {
        "protocol": "conversation-v1",
        "run_id": "run-1",
        "revision": 1,
        "mode": "active",
        "active_limit_ms": 60000,
        "active_elapsed_ms": 10000,
        "wait_elapsed_ms": 0,
        "captured_at": "2026-10-14T00:00:00Z",
        "active_since": "2026-10-14T00:00:00Z",
        "in_flight_refs": [],
    }


def test_active_clock_charges_elapsed_time_and_never_renews_allowance() -> None:
    value = RunExecutionClock.model_validate_json(json.dumps(clock()))
    assert value.remaining_active_ms("2026-10-14T00:00:15.999Z") == 34001
    assert value.remaining_active_ms("2026-10-14T00:01:00Z") == 0
    with pytest.raises(ValueError):
        value.remaining_active_ms("2026-10-13T23:59:59Z")
    actual_overrun = RunExecutionClock.model_validate_json(
        json.dumps({**clock(), "active_elapsed_ms": 60001})
    )
    assert actual_overrun.active_elapsed_ms == 60001
    assert actual_overrun.remaining_active_ms("2026-10-14T00:00:00Z") == 0


def test_user_wait_does_not_charge_active_time_but_cannot_hide_an_inflight_call() -> None:
    data = clock()
    data.pop("active_since")
    data.update(
        mode="waiting_for_user",
        waiting_since=data["captured_at"],
        waiting_item_ref={"kind": "item", "id": "question-1", "version": "1"},
    )
    value = RunExecutionClock.model_validate_json(json.dumps(data))
    later = (datetime(2026, 10, 14, tzinfo=UTC) + timedelta(days=2)).isoformat()
    assert value.remaining_active_ms(later) == 50000
    data["in_flight_refs"] = [{"kind": "tool_call", "id": "sent-1", "version": "1"}]
    with pytest.raises(ValidationError):
        RunExecutionClock.model_validate_json(json.dumps(data))


@pytest.mark.parametrize(
    "invalid",
    [
        {"active_elapsed_ms": -1},
        {"active_since": "2026-10-14T00:00:01Z"},
        {"mode": "stopped"},
        {"active_limit_ms": True},
    ],
)
def test_invalid_clock_cannot_create_time_or_coerce_budget(invalid: dict) -> None:
    with pytest.raises(ValidationError):
        RunExecutionClock.model_validate_json(json.dumps({**clock(), **invalid}))


def test_published_endpoints_record_exact_acceptance_scope_not_full_continuation() -> None:
    catalog = json.loads((ROOT / "contracts/interfaces.json").read_text(encoding="utf-8"))
    new = [op for op in catalog["operations"] if op.get("protocol") == "conversation-v1"]
    assert {op["id"] for op in new} == {
        "runs.conversation.get",
        "runs.clarification.get",
        "runs.clarification.answer",
        "runs.correction.create",
        "runs.continuation.get",
        "AgentRuntime.first_decision",
        "RunRuntime.commit_reply",
        "RunRuntime.commit_question",
    }
    for op in new:
        if op["channel"] == "http":
            assert op["implemented"]
            assert (
                op["implementation"]["scope"]
                == "development_conversation_control_acceptance_only_no_resume"
            )
        else:
            assert not op["implemented"]
    api = json.loads((ROOT / "contracts/openapi.json").read_text(encoding="utf-8"))
    for op in new:
        if op["channel"] == "http" and op["method"] == "POST":
            wire = api["paths"][op["path"]]["post"]
            assert wire["x-uaw-cas-required"]
            assert wire["requestBody"]["content"]["application/json"]["schema"]["properties"][
                "meta"
            ]["allOf"][0]["$ref"].endswith("ConversationRequestMeta")


def boundary_sources() -> dict:
    actor = Principal(id="user-1", kind="user", auth_session_id="session-1")
    conversation = sample("Conversation")
    conversation.update(id="conversation-1", owner_id=actor.id)
    run = sample("RunRecord")
    run.update(
        id="run-1", conversation_id=conversation["id"], status="waiting_for_user", revision=3
    )
    binding = sample("ConversationProtocolBinding")
    binding.update(run_id=run["id"], owner_id=actor.id)
    request = sample("RunClarificationAnswerRequest")
    request.update(run_id=run["id"], question_item_id="question-1")
    question = sample("ClarificationQuestion")
    question.update(run_id=run["id"], conversation_id=conversation["id"], item_id="question-1")
    return {
        "actor": actor,
        "conversation": conversation,
        "run": run,
        "binding": ConversationProtocolBinding.model_validate_json(json.dumps(binding)),
        "request": RunClarificationAnswerRequest.model_validate_json(json.dumps(request)),
        "meta": ConversationRequestMeta(
            request_id="answer-1", schema_version="0.2", expected_revision=3
        ),
        "cancel_requested": False,
        "question": ClarificationQuestion.model_validate_json(json.dumps(question)),
    }


def test_pure_boundary_accepts_current_question_but_does_not_write_or_wake_run() -> None:
    sources = boundary_sources()
    before = copy.deepcopy(sources["run"])
    assert validate_control_boundary(**sources) is None
    assert sources["run"] == before


@pytest.mark.parametrize("status", ["completed", "failed", "cancelled"])
def test_terminal_question_answer_never_revives_original_run(status: str) -> None:
    sources = boundary_sources()
    sources["run"]["status"] = status
    with pytest.raises(DomainError) as error:
        validate_control_boundary(**sources)
    assert error.value.failure.code == "conversation_run_terminal"


@pytest.mark.parametrize(
    "case,code",
    [
        ("cancel", "conversation_run_terminal"),
        ("foreign_owner", "conversation_control_denied"),
        ("old_run", "conversation_protocol_unavailable"),
        ("run_revision", "conversation_revision_conflict"),
        ("input_revision", "conversation_input_stale"),
        ("question_revision", "conversation_question_stale"),
        ("answered", "conversation_question_stale"),
    ],
)
def test_original_scope_cas_and_question_sources_fail_closed(case: str, code: str) -> None:
    sources = boundary_sources()
    if case == "cancel":
        sources["cancel_requested"] = True
    elif case == "foreign_owner":
        sources["conversation"]["owner_id"] = "other"
    elif case == "old_run":
        sources["binding"] = None
    elif case == "run_revision":
        sources["meta"] = ConversationRequestMeta(
            request_id="answer-1", schema_version="0.2", expected_revision=2
        )
    elif case == "input_revision":
        data = sources["request"].wire()
        data["expected_input_revision"] = 2
        sources["request"] = RunClarificationAnswerRequest.model_validate_json(json.dumps(data))
    else:
        data = sources["question"].wire()
        if case == "question_revision":
            data["revision"] = 2
        else:
            data.update(
                state="answered", answer_input_ref={"kind": "input", "id": "answer", "version": "1"}
            )
        sources["question"] = ClarificationQuestion.model_validate_json(json.dumps(data))
    with pytest.raises(DomainError) as error:
        validate_control_boundary(**sources)
    assert error.value.failure.code == code
