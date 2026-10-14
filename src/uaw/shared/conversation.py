"""Strict consumers of conversation-v1, separate from legacy Run/Agent DTOs.

These types and ports do not resume a Run, renew authorization or execute calls.
Runtime owners must read current sources and commit state atomically.
"""

from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from uaw.shared.contracts import ID, ContractModel, JsonObject, Ref, Timestamp
from uaw.shared.schema import contract_schema, validate_contract

PositiveRevision = Annotated[int, Field(ge=1)]
Protocol = Literal["conversation-v1"]


def _utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ConversationRequestMeta(ContractModel):
    request_id: ID
    schema_version: Literal["0.2"]
    expected_revision: PositiveRevision


class ConversationUnderstanding(ContractModel):
    summary: str
    assumptions: tuple[str, ...]


class ClarificationPrompt(ContractModel):
    text: str
    reason: str
    options: tuple[str, ...]


class ClarificationProposal(ContractModel):
    protocol: Protocol
    run_ref: Ref
    input_revision: PositiveRevision
    decision_record_ref: Ref
    prompt: ClarificationPrompt


class FirstReplyDecision(ContractModel):
    protocol: Protocol
    action: Literal["reply"]
    text: str
    understanding: ConversationUnderstanding | None = None


class FirstToolDecision(ContractModel):
    protocol: Protocol
    action: Literal["tool"]
    calls: tuple[JsonObject, ...]
    understanding: ConversationUnderstanding | None = None


class FirstAskDecision(ContractModel):
    protocol: Protocol
    action: Literal["ask"]
    question: ClarificationPrompt
    understanding: ConversationUnderstanding | None = None


class FirstDeliverDecision(ContractModel):
    protocol: Protocol
    action: Literal["deliver"]
    text: str
    understanding: ConversationUnderstanding | None = None


FirstDecision = Annotated[
    FirstReplyDecision | FirstToolDecision | FirstAskDecision | FirstDeliverDecision,
    Field(discriminator="action"),
]


class FirstDecisionRequest(ContractModel):
    protocol: Protocol
    run_ref: Ref
    original_input_ref: Ref
    patch_refs: tuple[Ref, ...]
    input_revision: PositiveRevision
    context_ref: Ref
    remaining_budget: JsonObject


class FirstDecisionRecord(ContractModel):
    protocol: Protocol
    run_ref: Ref
    input_revision: PositiveRevision
    decision: FirstDecision
    model_output_ref: Ref
    model_policy_ref: Ref
    attempt_id: ID
    usage_ref: Ref


class ConversationProtocolBinding(ContractModel):
    protocol: Protocol
    run_id: ID
    owner_id: ID
    revision: PositiveRevision
    input_revision: PositiveRevision
    completion_mode: Literal["message", "delivery"]
    clock_ref: Ref


class ReplyProposal(ContractModel):
    protocol: Protocol
    run_ref: Ref
    input_revision: PositiveRevision
    decision_record_ref: Ref
    text: str
    source_refs: tuple[Ref, ...]
    unresolved_effect_refs: tuple[Ref, ...]


class ReplyCommitReceipt(ContractModel):
    protocol: Protocol
    run: JsonObject
    item: JsonObject
    input_revision: PositiveRevision
    event_seq: PositiveRevision

    @model_validator(mode="after")
    def check_ownership(self) -> Self:
        if (
            self.item["run_id"] != self.run["id"]
            or self.item["conversation_id"] != self.run["conversation_id"]
        ):
            raise ValueError("Message receipt ownership does not match the original Run")
        return self


class ClarificationQuestion(ContractModel):
    protocol: Protocol
    run_id: ID
    conversation_id: ID
    item_id: ID
    revision: PositiveRevision
    input_revision: PositiveRevision
    prompt: ClarificationPrompt
    decision_record_ref: Ref
    state: Literal["open", "answered", "stale", "cancelled"]
    created_at: Timestamp
    answer_input_ref: Ref | None = None


class ClarificationView(ContractModel):
    question: ClarificationQuestion
    run_revision: PositiveRevision
    run_status: Literal[
        "queued",
        "preparing",
        "running",
        "verifying",
        "waiting_for_user",
        "waiting_for_merge",
        "completed",
        "failed",
        "cancelled",
    ]
    input_revision: PositiveRevision

    @model_validator(mode="after")
    def check_open_input(self) -> Self:
        if self.question.state == "open" and self.question.input_revision != self.input_revision:
            raise ValueError("An open question must refer to the current input revision")
        return self


class RunClarificationAnswerRequest(ContractModel):
    run_id: ID
    question_item_id: ID
    expected_question_revision: PositiveRevision
    expected_input_revision: PositiveRevision
    text: str
    attachment_refs: tuple[Ref, ...]


class RunCorrectionRequest(ContractModel):
    run_id: ID
    expected_input_revision: PositiveRevision
    text: str
    attachment_refs: tuple[Ref, ...]


class RunInputPatch(ContractModel):
    protocol: Protocol
    run_id: ID
    conversation_id: ID
    request_id: ID
    input_ref: Ref
    kind: Literal["clarification_answer", "correction"]
    base_input_revision: PositiveRevision
    input_revision: PositiveRevision
    state: Literal["accepted", "applied", "superseded", "cancelled"]
    created_at: Timestamp
    question_item_id: ID | None = None
    question_revision: PositiveRevision | None = None
    applied_at: Timestamp | None = None

    @model_validator(mode="after")
    def check_revision_and_time(self) -> Self:
        if self.input_revision != self.base_input_revision + 1:
            raise ValueError("A patch must increment the original input revision exactly once")
        if self.applied_at and _utc(self.applied_at) < _utc(self.created_at):
            raise ValueError("Patch application cannot predate acceptance")
        return self


class RunContinuationReceipt(ContractModel):
    protocol: Protocol
    run: JsonObject
    patch: RunInputPatch
    event_seq: PositiveRevision

    @model_validator(mode="after")
    def check_ownership(self) -> Self:
        if (
            self.patch.run_id != self.run["id"]
            or self.patch.conversation_id != self.run["conversation_id"]
        ):
            raise ValueError("Patch receipt ownership does not match the original Run")
        return self


class RunExecutionClock(ContractModel):
    protocol: Protocol
    run_id: ID
    revision: PositiveRevision
    mode: Literal["active", "waiting_for_user", "stopped"]
    active_limit_ms: Annotated[int, Field(ge=1, le=604800000)]
    active_elapsed_ms: Annotated[int, Field(ge=0, le=9007199254740991)]
    wait_elapsed_ms: Annotated[int, Field(ge=0, le=9007199254740991)]
    captured_at: Timestamp
    in_flight_refs: tuple[Ref, ...]
    active_since: Timestamp | None = None
    waiting_since: Timestamp | None = None
    waiting_item_ref: Ref | None = None

    @model_validator(mode="after")
    def check_clock(self) -> Self:
        captured = _utc(self.captured_at)
        for start in (self.active_since, self.waiting_since):
            if start and _utc(start) > captured:
                raise ValueError("An execution or waiting segment cannot start in the future")
        return self

    def remaining_active_ms(self, now: Timestamp) -> int:
        """Pure reading of a trusted persisted clock, not an execution grant."""
        validate_contract("Timestamp", now)
        current = _utc(now)
        if current < _utc(self.captured_at):
            raise ValueError("Current service time cannot predate the clock snapshot")
        elapsed = self.active_elapsed_ms
        if self.mode == "active" and self.active_since:
            delta = current - _utc(self.active_since)
            elapsed += (delta.days * 86400 + delta.seconds) * 1000 + delta.microseconds // 1000
        return max(0, self.active_limit_ms - elapsed)


def first_decision_schema() -> dict[str, object]:
    """Isolated model-output schema from the authoritative catalog, no second shape."""
    import copy

    source = contract_schema()
    definitions: dict[str, object] = {}
    pending = ["FirstDecision"]

    def references(value: object) -> list[str]:
        if isinstance(value, dict):
            names = [value["$ref"].split("/")[-1]] if "$ref" in value else []
            return names + [n for child in value.values() for n in references(child)]
        if isinstance(value, list):
            return [n for child in value for n in references(child)]
        return []

    while pending:
        name = pending.pop()
        if name in definitions:
            continue
        value = copy.deepcopy(source["$defs"][name])
        definitions[name] = value
        pending.extend(references(value))
    return {"$schema": source["$schema"], "$ref": "#/$defs/FirstDecision", "$defs": definitions}
