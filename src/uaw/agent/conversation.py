"""Explicit conversation-v1 admission and interpretation of actual model outputs.

The legacy loop stores its existing action DTO. This projection never rewrites
the original ModelOutput: the versioned decision and owning references remain
separately recorded and are checked again before publication.
"""

from uaw.agent.contracts import Payload, validate_decision
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing

BINDINGS = "run.protocol_bindings"
DECISIONS = "agent.conversation.decisions"


async def enabled(records: PostgresRecordStore, ctx: TrustedExecutionContext) -> bool:
    try:
        row = await records.get(ctx.principal, BINDINGS, ctx.run_id or "")
    except StoreMissing:
        return False
    validate_contract("ConversationProtocolBinding", row.payload)
    inputs = await records.get(ctx.principal, "run.input_sets", ctx.run_id or "")
    if (
        row.schema_name != "ConversationProtocolBinding"
        or row.payload["owner_id"] != ctx.principal.id
        or row.payload["run_id"] != ctx.run_id
        or row.payload["input_revision"] != inputs.revision
    ):
        raise reject("conversation_binding_stale", "Original protocol/input owner differs", 412)
    return True


def execution_decision(value: Payload) -> Payload:
    """Project an explicitly versioned decision into the unchanged loop DTO."""
    if value.get("protocol") != "conversation-v1":
        return validate_decision(value)
    validate_contract("FirstDecision", value)
    action = value["action"]
    projected = {
        "action": {"reply": "respond", "deliver": "respond", "tool": "call_tools", "ask": "wait"}[
            action
        ],
        "text": value.get("text", value.get("question", {}).get("text", "")),
        "proposed_calls": value.get("calls", []),
    }
    return validate_decision(projected)
