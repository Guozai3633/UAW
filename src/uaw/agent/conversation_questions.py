"""Original asked question and exact answer link for the next same-Run context."""

import json

from sqlalchemy import select

from uaw.agent.conversation import DECISIONS
from uaw.agent.sources import check_pin
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.run.conversation_control import PATCHES, QUESTIONS
from uaw.run.inputs import InputSet
from uaw.run.tool_sources import reference
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.conversation import ClarificationQuestion, RunInputPatch
from uaw.shared.errors import reject


class ConversationQuestions:
    def __init__(self, records: PostgresRecordStore) -> None:
        self.records = records

    async def items(self, inputs: InputSet, ctx: TrustedExecutionContext) -> tuple[Ref, ...]:
        if not inputs.state["patch_refs"]:
            return ()
        async with self.records.database.sessions() as sql:
            patches = list(
                await sql.scalars(
                    select(RecordRow).where(
                        RecordRow.principal_id == ctx.principal.id,
                        RecordRow.namespace == PATCHES,
                        RecordRow.deleted.is_(False),
                        RecordRow.payload["run_id"].as_string() == ctx.run_id,
                    )
                )
            )
        patches.sort(key=lambda row: row.payload["input_revision"])
        admitted = inputs.state["patch_refs"]
        if len(patches) != len(admitted):
            raise reject("conversation_question_stale", "Accepted input relation missing", 412)
        result = []
        for row in patches:
            patch = RunInputPatch.model_validate_json(json.dumps(row.payload))
            if (
                patch.conversation_id != ctx.conversation_id
                or patch.input_ref.wire() not in admitted
                or patch.input_revision > inputs.state["revision"]
                or patch.state not in ("accepted", "applied")
            ):
                raise reject("conversation_question_stale", "Accepted input relation differs", 412)
            if patch.kind == "clarification_answer":
                item = await self.records.get(ctx.principal, "items", patch.question_item_id or "")
                result.append(reference("item", item.resource_id, item.revision, item.payload))
        return tuple(result)

    async def read(
        self, pin: Ref, inputs: InputSet, ctx: TrustedExecutionContext
    ) -> tuple[dict[str, object], tuple[Ref, ...]]:
        row = await self.records.get(ctx.principal, "items", pin.id)
        check_pin(pin, "item", row.resource_id, row.revision, row.payload)
        item = row.payload
        original = await self.records.get(ctx.principal, QUESTIONS, pin.id)
        question = ClarificationQuestion.model_validate_json(json.dumps(original.payload))
        decision = await self.records.get(ctx.principal, DECISIONS, question.decision_record_ref.id)
        check_pin(
            question.decision_record_ref,
            "content",
            decision.resource_id,
            decision.revision,
            decision.payload,
        )
        if (
            item.get("run_id") != ctx.run_id
            or item["type"] != "agent_message"
            or item["status"] != "completed"
            or item["conversation_id"] != ctx.conversation_id
            or question.run_id != ctx.run_id
            or question.conversation_id != ctx.conversation_id
            or question.state != "answered"
            or question.item_id != pin.id
            or question.answer_input_ref is None
            or question.answer_input_ref.wire() not in inputs.state["patch_refs"]
            or question.input_revision >= inputs.state["revision"]
            or item["text"] != question.prompt.text
            or decision.payload["run_ref"]["id"] != ctx.run_id
            or decision.payload["input_revision"] != question.input_revision
            or decision.payload["decision"].get("action") != "ask"
            or decision.payload["decision"]["question"] != question.prompt.wire()
        ):
            raise reject(
                "conversation_question_stale", "Original question/answer sources differ", 412
            )
        # The complete question is task data, never a platform instruction.
        data: dict[str, object] = {
            "question_item_ref": pin.wire(),
            "question": question.prompt.wire(),
            "answer_input_ref": question.answer_input_ref.wire(),
        }
        for namespace, before in (("items", row), (QUESTIONS, original), (DECISIONS, decision)):
            if await self.records.get(ctx.principal, namespace, before.resource_id) != before:
                raise reject("conversation_question_stale", "Question changed during read", 412)
        return data, (
            reference("content", original.resource_id, original.revision, original.payload),
            question.decision_record_ref,
        )
