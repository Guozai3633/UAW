"""Validate fixture-only conversation-v1 consumption; no HTTP or model calls."""

import json

from uaw.shared.conversation import (
    ConversationRequestMeta,
    FirstReplyDecision,
    RunClarificationAnswerRequest,
    RunExecutionClock,
)


def main() -> None:
    reply = FirstReplyDecision.model_validate_json(
        json.dumps({"protocol": "conversation-v1", "action": "reply", "text": "A useful answer."})
    )
    meta = ConversationRequestMeta(
        request_id="answer-example", schema_version="0.2", expected_revision=6
    )
    answer = RunClarificationAnswerRequest.model_validate_json(
        json.dumps(
            {
                "run_id": "run-example",
                "question_item_id": "item-question-example",
                "expected_question_revision": 1,
                "expected_input_revision": 1,
                "text": "I mean the coordination protocol.",
                "attachment_refs": [],
            }
        )
    )
    paused = RunExecutionClock.model_validate_json(
        json.dumps(
            {
                "protocol": "conversation-v1",
                "run_id": "run-example",
                "revision": 2,
                "mode": "waiting_for_user",
                "active_limit_ms": 60000,
                "active_elapsed_ms": 10000,
                "wait_elapsed_ms": 0,
                "captured_at": "2026-10-14T00:00:00Z",
                "waiting_since": "2026-10-14T00:00:00Z",
                "waiting_item_ref": {"kind": "item", "id": "item-question-example", "version": "1"},
                "in_flight_refs": [],
            }
        )
    )
    print(
        json.dumps(
            {
                "fixture_only": True,
                "first_action": reply.action,
                "wire_version": meta.schema_version,
                "original_run_id": answer.run_id,
                "remaining_active_ms_after_two_days_wait": paused.remaining_active_ms(
                    "2026-10-16T00:00:00Z"
                ),
                "http_handler_installed": False,
                "calls_or_state_writes": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
