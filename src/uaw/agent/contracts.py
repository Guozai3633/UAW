"""Strict consumers of published Agent objects and versioned internal records."""

import hashlib
import json
from typing import Any, Literal

from uaw.shared.contracts import (
    ID,
    ContractModel,
    JsonObject,
    Ref,
    Revision,
    TrustedExecutionContext,
)
from uaw.shared.schema import validate_contract

Payload = dict[str, Any]


def frozen(value: Payload) -> Payload:
    return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))  # type: ignore[no-any-return]


def identity(ctx: TrustedExecutionContext) -> Payload:
    value = ctx.wire()
    for name in ("operation_id", "trace_id", "attempt_id", "deadline", "budget_reservation_ref"):
        value.pop(name, None)
    return value


def identifier(prefix: str, value: Payload) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return prefix + hashlib.sha256(raw.encode()).hexdigest()


class AgentStartRequest(ContractModel):
    run_ref: Ref
    task_frame_ref: Ref
    creation_key: ID
    role_profile_ref: Ref | None = None


class AgentStepRequest(ContractModel):
    instance_ref: Ref
    observations: tuple[Ref, ...]
    current_frame_ref: Ref
    remaining_budget: JsonObject


class AgentInstance(ContractModel):
    id: ID
    run_id: ID
    status: Literal["pending", "ready", "running", "waiting", "failed", "stale", "cancelled"]
    model_policy_ref: Ref
    capability_policy_ref: Ref
    context_epoch: Revision
    revision: Revision
    result_ref: Ref | None = None


class RootBinding(ContractModel):
    schema_name = "AgentRootBinding"
    context: TrustedExecutionContext
    start_request: Payload
    role_ref: Ref
    max_steps: Revision


class LoopState(ContractModel):
    schema_name = "AgentLoopState"
    instance_id: ID
    revision: Revision
    steps: Revision
    frame_ref: Ref
    observation_refs: tuple[Ref, ...]
    active_operation_ref: Ref | None = None


class LoopOperation(ContractModel):
    schema_name = "AgentLoopOperation"
    id: ID
    instance_id: ID
    revision: Revision
    step: Revision
    request: Payload
    context: TrustedExecutionContext
    phase: Literal["claimed", "prepared", "decided", "waiting", "finished", "failed"]
    snapshot_ref: Ref | None = None
    context_epoch: Revision | None = None
    model_request: Payload | None = None
    model_result: Payload | None = None
    proposal: Payload | None = None
    tool_context: TrustedExecutionContext | None = None
    observation_ref: Ref | None = None
    result: Payload | None = None


def decision_schema() -> Payload:
    """A compact proposal protocol. These fields grant no execution permissions."""
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "action": {"enum": ["respond", "call_tools", "wait", "propose_completion", "blocked"]},
            "text": {"type": "string", "maxLength": 16384},
            "proposed_calls": {
                "type": "array",
                "maxItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "tool_ref": {"type": "object"},
                        "arguments": {"type": "object"},
                        "action_id": {"type": "string", "minLength": 1, "maxLength": 200},
                    },
                    "required": ["tool_ref", "arguments", "action_id"],
                },
            },
        },
        "required": ["action", "text", "proposed_calls"],
    }


def validate_decision(value: Payload) -> Payload:
    from jsonschema import Draft202012Validator

    result = frozen(value)
    Draft202012Validator(decision_schema()).validate(result)
    if (result["action"] == "call_tools") != (len(result["proposed_calls"]) == 1):
        raise ValueError("Only call_tools has exactly one tool proposal")
    for call in result["proposed_calls"]:
        validate_contract("ToolCall", call)
    return result
