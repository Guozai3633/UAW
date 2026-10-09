import json
import math

import pytest
from jsonschema import ValidationError

from uaw.agent.contracts import validate_decision
from uaw.agent.engines.langgraph import JsonCheckpointSerializer, LangGraphAgentEngine
from uaw.agent.sources import require_role_model
from uaw.shared.errors import CapabilityUnavailable, DomainError


@pytest.mark.parametrize(
    "requirements",
    [
        {"vision": True},
        {"minimum_context_tokens": 4097},
        {"minimum_output_tokens": 513},
        {"tool_calling": True},
    ],
)
def test_role_requirements_never_replace_the_fixed_model(requirements):
    model = {
        "id": "fixed",
        "capabilities": ["json_schema"],
        "context_limit_tokens": 4096,
        "output_limit_tokens": 512,
    }
    with pytest.raises(DomainError) as error:
        require_role_model(
            {"model_capability_requirements": requirements, "auto_model_candidates": ["other"]},
            model,
        )
    assert error.value.failure.code == "agent_fixed_model_capability_missing"
    assert model["id"] == "fixed"


@pytest.mark.parametrize("action", ["respond", "wait", "blocked", "propose_completion"])
def test_non_tool_decisions_have_no_calls(action):
    assert (
        validate_decision({"action": action, "text": "candidate", "proposed_calls": []})["action"]
        == action
    )


def test_decision_has_one_actual_contract_shaped_proposal_and_copy():
    proposed = {
        "action": "call_tools",
        "text": "inspect",
        "proposed_calls": [
            {
                "tool_ref": {"kind": "configuration", "id": "text.inspect", "version": "1"},
                "action_id": "a",
                "arguments": {"text": "unaltered"},
            }
        ],
    }
    result = validate_decision(proposed)
    proposed["proposed_calls"][0]["arguments"]["text"] = "mutated"
    assert result["proposed_calls"][0]["arguments"]["text"] == "unaltered"


@pytest.mark.parametrize(
    "change",
    [
        {"approved": True},
        {"action": "completed"},
        {"text": "x" * 16385},
        {"action": "call_tools"},
        {
            "action": "respond",
            "proposed_calls": [{"tool_ref": {}, "arguments": {}, "action_id": "a"}],
        },
    ],
)
def test_invalid_and_authority_claims_do_not_become_decisions(change):
    with pytest.raises((ValidationError, ValueError)):
        validate_decision({"action": "respond", "text": "", "proposed_calls": [], **change})


@pytest.mark.parametrize(
    "unsafe", [object(), b"secret", math.nan, math.inf, {1: "key"}, ("tuple",)]
)
def test_checkpoints_reject_objects_and_non_json(unsafe):
    with pytest.raises(ValueError):
        JsonCheckpointSerializer().dumps_typed(unsafe)


def test_checkpoints_are_plain_json_and_reject_pickle():
    serializer = JsonCheckpointSerializer()
    value = {"ref": {"kind": "agent_instance", "id": "a", "version": "1"}, "result": []}
    kind, encoded = serializer.dumps_typed(value)
    assert kind == "json" and json.loads(encoded) == value
    assert serializer.loads_typed((kind, encoded)) == value
    with pytest.raises(ValueError):
        serializer.loads_typed(("pickle", b"anything"))


def test_checkpoints_enforce_bytes_and_depth():
    serializer = JsonCheckpointSerializer()
    with pytest.raises(ValueError):
        serializer.dumps_typed("x" * 2097153)
    nested = []
    for _ in range(34):
        nested = [nested]
    with pytest.raises(ValueError):
        serializer.dumps_typed(nested)


def test_missing_checkpoint_is_not_an_implicit_memory_backend():
    with pytest.raises(CapabilityUnavailable):
        LangGraphAgentEngine(None, checkpointer=None)
