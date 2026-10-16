"""Transport compatibility and user-visible failure boundaries."""

import pytest
from jsonschema import ValidationError

from uaw.agent.conversation import execution_decision
from uaw.model.capability import bounded_schema
from uaw.run.background import user_failure
from uaw.shared.conversation import first_decision_schema
from uaw.shared.schema import ContractViolation, validate_contract


def test_plain_reply_needs_no_tool_array_and_provider_schema_is_supported():
    value = {"protocol": "conversation-v1", "action": "reply", "text": "A useful answer"}
    bounded_schema(first_decision_schema()).validate(value)
    validate_contract("FirstDecision", value)
    assert execution_decision(value) == {
        "action": "respond",
        "text": value["text"],
        "proposed_calls": [],
    }


@pytest.mark.parametrize("extra", [{"calls": []}, {"approved": True}, {"model_id": "other"}])
def test_reply_cannot_smuggle_execution_or_authority(extra):
    value = {"protocol": "conversation-v1", "action": "reply", "text": "Answer", **extra}
    with pytest.raises((ContractViolation, ValidationError, ValueError)):
        execution_decision(value)


def test_transport_projection_still_has_canonical_local_nonblank_check():
    value = {"protocol": "conversation-v1", "action": "reply", "text": " "}
    with pytest.raises(ContractViolation):
        execution_decision(value)


def test_failure_text_does_not_expose_internal_receipts_or_urge_unknown_resend():
    text = user_failure(
        {
            "code": "provider_structured_output_invalid",
            "category": "model_protocol",
            "message": "protected receipt",
        }
    )
    assert "响应格式" in text and "protected receipt" not in text
    pending = user_failure(
        {"code": "provider_transport_unknown", "category": "unknown_effect", "message": "internal"}
    )
    assert "不要重复提交" in pending and "稍后重试" not in pending
