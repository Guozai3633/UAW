"""Pure conversation control boundary checks for the future Run transaction.

The caller must obtain all arguments from current owned repositories under the
same transaction/lease. This module never reads permissions, writes a patch,
renews a deadline or wakes an executor. It is not a fallback for missing sources.
"""

from uaw.shared.contracts import JsonObject, Principal
from uaw.shared.conversation import (
    ClarificationQuestion,
    ConversationProtocolBinding,
    ConversationRequestMeta,
    RunClarificationAnswerRequest,
    RunCorrectionRequest,
)
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract


def validate_control_boundary(
    actor: Principal,
    conversation: JsonObject,
    run: JsonObject,
    binding: ConversationProtocolBinding | None,
    request: RunClarificationAnswerRequest | RunCorrectionRequest,
    meta: ConversationRequestMeta,
    *,
    cancel_requested: bool,
    question: ClarificationQuestion | None = None,
) -> None:
    """Check current identity, protocol, CAS and question; grant no execution right."""
    validate_contract("Conversation", conversation)
    validate_contract("RunRecord", run)
    if (
        actor.kind != "user"
        or conversation["owner_id"] != actor.id
        or run["conversation_id"] != conversation["id"]
        or request.run_id != run["id"]
    ):
        raise reject(
            "conversation_control_denied",
            "Control is outside the current user scope",
            403,
            "permission",
        )
    if binding is None:
        raise reject(
            "conversation_protocol_unavailable",
            "This Run uses the previous protocol; submit a new turn",
            503,
            "dependency",
        )
    if binding.run_id != run["id"] or binding.owner_id != actor.id:
        raise reject(
            "conversation_binding_stale", "Current Run protocol source does not match", 412
        )
    if not isinstance(cancel_requested, bool):
        raise reject(
            "conversation_source_invalid", "Cancellation source is invalid", 503, "dependency"
        )
    if cancel_requested or run["status"] in ("completed", "failed", "cancelled"):
        raise reject("conversation_run_terminal", "This Run cannot be continued", 409, "conflict")
    if meta.expected_revision != run["revision"]:
        raise reject("conversation_revision_conflict", "Run changed; read its current version", 409)
    if request.expected_input_revision != binding.input_revision:
        raise reject("conversation_input_stale", "Inputs changed; read the current version", 412)
    if isinstance(request, RunClarificationAnswerRequest):
        if (
            run["status"] != "waiting_for_user"
            or question is None
            or question.state != "open"
            or question.run_id != run["id"]
            or question.conversation_id != conversation["id"]
            or question.item_id != request.question_item_id
            or question.revision != request.expected_question_revision
            or question.input_revision != binding.input_revision
        ):
            raise reject("conversation_question_stale", "Original question is no longer open", 412)
    elif run["status"] not in ("queued", "preparing", "running", "verifying", "waiting_for_user"):
        raise reject("conversation_control_unavailable", "Run is not at a correction boundary", 409)
