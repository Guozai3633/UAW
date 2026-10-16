"""Owned conversation controls: durable acceptance, never a claimed execution grant."""

import hashlib
import json
from typing import Any

from sqlalchemy import func, select

from uaw.agent.conversation import BINDINGS, DECISIONS
from uaw.agent.sources import check_pin
from uaw.infrastructure.db.models import OutboxRow, RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import (
    RecordTransaction,
    TransactionalStore,
    identifier,
    reference,
    timestamp,
)
from uaw.run.conversation_protocol import validate_control_boundary
from uaw.run.history import append_input
from uaw.shared.contracts import Principal, Ref, RequestMeta
from uaw.shared.conversation import (
    ClarificationQuestion,
    ClarificationView,
    ConversationProtocolBinding,
    ConversationRequestMeta,
    RunClarificationAnswerRequest,
    RunContinuationReceipt,
    RunConversationView,
    RunCorrectionRequest,
)
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing

Payload = dict[str, Any]
PATCHES = "run.input_patches"
RECEIPTS = "run.continuation.receipts"
QUESTIONS = "run.clarification_questions"
TERMINAL = ("completed", "failed", "cancelled")


def patch_id(actor: Principal, run_id: str, request_id: str) -> str:
    raw = "\0".join((actor.id, run_id, request_id)).encode()
    return "patch-" + hashlib.sha256(raw).hexdigest()


class ConversationControls:
    def __init__(self, records: PostgresRecordStore) -> None:
        self.records = records
        self.transactions = TransactionalStore(records.database)

    async def aggregate(self, actor: Principal, run_id: str) -> str:
        validate_contract("Principal", actor.wire())
        validate_contract("ID", run_id)
        if actor.kind != "user":
            raise reject("conversation_control_denied", "User identity required", 403)
        run = await self.records.get(actor, "runs", run_id)
        return "conversation:" + str(run.payload["conversation_id"])

    async def owned(self, tx: RecordTransaction, actor: Principal, run_id: str) -> Payload:
        if actor.kind != "user" or tx.owner != actor.id:
            raise reject("conversation_control_denied", "Original user transaction required", 403)
        run = await tx.load("runs", run_id)
        conversation = await tx.load("conversations", run.payload["conversation_id"])
        if conversation.payload["owner_id"] != actor.id:
            raise reject("conversation_control_denied", "Conversation owner differs", 403)
        try:
            binding = await tx.load(BINDINGS, run_id)
        except StoreMissing:
            raise CapabilityUnavailable("run.conversation_protocol") from None
        state = await tx.load("run.input_sets", run_id)
        admission = await tx.load("run.bindings", run_id)
        for row, schema in (
            (run, "RunRecord"),
            (conversation, "Conversation"),
            (binding, "ConversationProtocolBinding"),
            (state, "RunInputState"),
            (admission, "RunAdmissionBinding"),
        ):
            if row.schema_name != schema:
                raise reject("conversation_binding_stale", "Original source schema differs", 412)
            validate_contract(schema, row.payload)
        if (
            run.payload["id"] != run.resource_id
            or run.payload["revision"] != run.revision
            or conversation.payload["revision"] != conversation.revision
            or binding.payload["revision"] != binding.revision
            or state.payload["revision"] != state.revision
            or binding.payload["owner_id"] != actor.id
            or binding.payload["run_id"] != run_id
            or binding.payload["input_revision"] != state.revision
            or state.payload["run_id"] != run_id
            or state.payload["conversation_id"] != conversation.resource_id
            or state.payload["original_input_ref"] != admission.payload["input_ref"]
        ):
            raise reject("conversation_binding_stale", "Original conversation sources differ", 412)
        return run.payload

    @staticmethod
    async def matching(tx: RecordTransaction, namespace: str, run_id: str) -> list[RecordRow]:
        return list(
            await tx.session.scalars(
                select(RecordRow).where(
                    RecordRow.principal_id == tx.owner,
                    RecordRow.namespace == namespace,
                    RecordRow.deleted.is_(False),
                    RecordRow.payload["run_id"].as_string() == run_id,
                )
            )
        )

    async def question_value(
        self, tx: RecordTransaction, run: Payload, item_id: str
    ) -> ClarificationView:
        question = await tx.load(QUESTIONS, item_id)
        state = await tx.load("run.input_sets", run["id"])
        value = ClarificationQuestion.model_validate_json(json.dumps(question.payload))
        item = await tx.load("items", item_id)
        decision = await tx.load(DECISIONS, value.decision_record_ref.id)
        check_pin(
            value.decision_record_ref,
            "content",
            decision.resource_id,
            decision.revision,
            decision.payload,
        )
        if (
            value.run_id != run["id"]
            or value.conversation_id != run["conversation_id"]
            or item.payload.get("run_id") != run["id"]
            or item.payload["conversation_id"] != run["conversation_id"]
            or item.payload["text"] != value.prompt.text
            or decision.payload["run_ref"]["id"] != run["id"]
            or decision.payload["decision"].get("action") != "ask"
            or decision.payload["decision"]["question"] != value.prompt.wire()
            or decision.payload["input_revision"] != value.input_revision
        ):
            raise reject("conversation_question_stale", "Original question sources differ", 412)
        return ClarificationView(
            question=value,
            run_revision=run["revision"],
            run_status=run["status"],
            input_revision=state.revision,
        )

    async def view(self, actor: Principal, run_id: str) -> RunConversationView:
        async def read(tx: RecordTransaction) -> Payload:
            run = await self.owned(tx, actor, run_id)
            state = await tx.load("run.input_sets", run_id)
            patches = await self.matching(tx, PATCHES, run_id)
            patches.sort(key=lambda row: row.payload["input_revision"])
            result: Payload = {
                "protocol": "conversation-v1",
                "run": run,
                "input_revision": state.revision,
                "continuation_request_ids": [row.payload["request_id"] for row in patches],
            }
            questions = await self.matching(tx, QUESTIONS, run_id)
            opened = [row for row in questions if row.payload["state"] == "open"]
            if len(opened) > 1:
                raise reject("conversation_question_ambiguous", "Multiple open questions", 412)
            if opened and run["status"] not in TERMINAL:
                result["question"] = (
                    await self.question_value(tx, run, opened[0].resource_id)
                ).wire()
            return result

        value = await self.transactions.inspect(actor, await self.aggregate(actor, run_id), read)
        return RunConversationView.model_validate_json(json.dumps(value))

    async def question(
        self, actor: Principal, run_id: str, question_item_id: str
    ) -> ClarificationView:
        async def read(tx: RecordTransaction) -> Payload:
            run = await self.owned(tx, actor, run_id)
            return (await self.question_value(tx, run, question_item_id)).wire()

        value = await self.transactions.inspect(actor, await self.aggregate(actor, run_id), read)
        return ClarificationView.model_validate_json(json.dumps(value))

    async def lookup(
        self, actor: Principal, run_id: str, request_id: str
    ) -> RunContinuationReceipt:
        validate_contract("ID", request_id)
        key = patch_id(actor, run_id, request_id)

        async def read(tx: RecordTransaction) -> Payload:
            run = await self.owned(tx, actor, run_id)
            row = await tx.load(RECEIPTS, key)
            patch = await tx.load(PATCHES, key)
            if (
                row.payload["patch"]["request_id"] != request_id
                or patch.payload["run_id"] != run_id
                or patch.payload["conversation_id"] != run["conversation_id"]
            ):
                raise reject("conversation_receipt_stale", "Original receipt sources differ", 412)
            seq = await tx.session.scalar(
                select(func.max(OutboxRow.seq)).where(
                    OutboxRow.principal_id == actor.id,
                    OutboxRow.stream_id == run["conversation_id"],
                )
            )
            return {
                "protocol": "conversation-v1",
                "run": run,
                "patch": patch.payload,
                "event_seq": seq or row.payload["event_seq"],
            }

        value = await self.transactions.inspect(actor, await self.aggregate(actor, run_id), read)
        return RunContinuationReceipt.model_validate_json(json.dumps(value))

    async def answer(
        self,
        actor: Principal,
        request: RunClarificationAnswerRequest,
        meta: ConversationRequestMeta,
    ) -> RunContinuationReceipt:
        return await self.accept(actor, request, meta)

    async def correct(
        self, actor: Principal, request: RunCorrectionRequest, meta: ConversationRequestMeta
    ) -> RunContinuationReceipt:
        return await self.accept(actor, request, meta)

    async def accept(
        self,
        actor: Principal,
        request: RunClarificationAnswerRequest | RunCorrectionRequest,
        meta: ConversationRequestMeta,
    ) -> RunContinuationReceipt:
        validate_contract(type(request).__name__, request.wire())
        validate_contract("ConversationRequestMeta", meta.wire())
        if request.attachment_refs:
            raise CapabilityUnavailable("conversation.authorized_attachment_ingestion")
        aggregate = await self.aggregate(actor, request.run_id)
        key = patch_id(actor, request.run_id, meta.request_id)
        kind = (
            "clarification_answer"
            if isinstance(request, RunClarificationAnswerRequest)
            else "correction"
        )

        async def write(tx: RecordTransaction) -> Payload:
            run = await self.owned(tx, actor, request.run_id)
            conversation = await tx.load("conversations", run["conversation_id"])
            binding = await tx.load(BINDINGS, run["id"])
            state = await tx.load("run.input_sets", run["id"])
            ledger = await tx.load("budget.ledgers", run["id"])
            question = None
            if isinstance(request, RunClarificationAnswerRequest):
                question = (await self.question_value(tx, run, request.question_item_id)).question
            validate_control_boundary(
                actor,
                conversation.payload,
                run,
                ConversationProtocolBinding.model_validate_json(json.dumps(binding.payload)),
                request,
                meta,
                cancel_requested=ledger.payload["cancel_requested"],
                question=question,
            )
            if len(state.payload["patch_refs"]) >= 16:
                raise reject("input_patch_limit", "Requirement update limit reached", 409)
            base_input_revision = state.revision
            size = len(request.text.encode())
            for pin in (state.payload["original_input_ref"], *state.payload["patch_refs"]):
                source = await tx.load("inputs", pin["id"])
                check_pin(
                    Ref.model_validate(pin),
                    "input",
                    source.resource_id,
                    source.revision,
                    source.payload,
                )
                if source.payload["conversation_id"] != run["conversation_id"]:
                    raise reject("conversation_input_stale", "Input owner differs", 412)
                size += len(source.payload["text"].encode())
            if size > 65536:
                raise reject(
                    "intent_input_too_large", "Conversation source set exceeds 64 KiB", 413
                )
            appended = await append_input(
                tx,
                run["conversation_id"],
                identifier("patch-turn"),
                request.text,
                [],
                run_id=run["id"],
            )
            ref = reference("input", appended["id"])
            now = timestamp()
            patch: Payload = {
                "protocol": "conversation-v1",
                "run_id": run["id"],
                "conversation_id": run["conversation_id"],
                "request_id": meta.request_id,
                "input_ref": ref,
                "kind": kind,
                "base_input_revision": base_input_revision,
                "input_revision": base_input_revision + 1,
                "state": "accepted",
                "created_at": now,
            }
            if question is not None:
                patch.update(question_item_id=question.item_id, question_revision=question.revision)
            await tx.write(PATCHES, key, "RunInputPatch", patch)
            await tx.write(
                "run.input_sets",
                run["id"],
                "RunInputState",
                {
                    **state.payload,
                    "revision": base_input_revision + 1,
                    "patch_refs": [*state.payload["patch_refs"], ref],
                },
                state.revision,
            )
            await tx.write(
                BINDINGS,
                run["id"],
                "ConversationProtocolBinding",
                {
                    **binding.payload,
                    "revision": binding.revision + 1,
                    "input_revision": base_input_revision + 1,
                },
                binding.revision,
            )
            for row in await self.matching(tx, QUESTIONS, run["id"]):
                if row.payload["state"] != "open":
                    continue
                value = {**row.payload, "revision": row.revision + 1, "state": "stale"}
                if question is not None and row.resource_id == question.item_id:
                    value.update(state="answered", answer_input_ref=ref)
                await tx.write(
                    QUESTIONS, row.resource_id, "ClarificationQuestion", value, row.revision
                )
            changed = {**run, "revision": run["revision"] + 1}
            changed.pop("frame_ref", None)
            await tx.write("runs", run["id"], "RunRecord", changed, run["revision"])
            task = await tx.load("tasks", run["task_id"])
            task_value = {**task.payload, "revision": task.revision + 1}
            task_value.pop("frame_ref", None)
            await tx.write("tasks", task.resource_id, "TaskRecord", task_value, task.revision)
            event = await tx.emit(
                run["conversation_id"],
                "run.updated",
                changed,
                base_revision=run["revision"],
                result_revision=changed["revision"],
            )
            receipt = {
                "protocol": "conversation-v1",
                "run": changed,
                "patch": patch,
                "event_seq": event["seq"],
            }
            await tx.write(RECEIPTS, key, "RunContinuationReceipt", receipt)
            return receipt

        await self.transactions.execute(
            actor,
            aggregate,
            RequestMeta(request_id=key, schema_version="0.1"),
            {"operation": kind, "meta": meta.wire(), "request": request.wire()},
            write,
            verify=lambda: self.verify_owned(actor, request.run_id),
        )
        return await self.lookup(actor, request.run_id, meta.request_id)

    async def verify_owned(self, actor: Principal, run_id: str) -> None:
        # Authentication is checked by ingress. Replay still verifies actual owner,
        # while deliberately allowing the original receipt to be read after cancel.
        run = await self.records.get(actor, "runs", run_id)
        conversation = await self.records.get(
            actor, "conversations", run.payload["conversation_id"]
        )
        if actor.kind != "user" or conversation.payload["owner_id"] != actor.id:
            raise reject("conversation_control_denied", "Conversation owner differs", 403)


async def cancel_pending_controls(tx: RecordTransaction, run_id: str) -> None:
    """Invalidate accepted controls under the same original cancel transaction."""
    for namespace, schema in ((QUESTIONS, "ClarificationQuestion"), (PATCHES, "RunInputPatch")):
        for row in await ConversationControls.matching(tx, namespace, run_id):
            if row.payload["state"] not in ("open", "accepted"):
                continue
            await tx.write(
                namespace,
                row.resource_id,
                schema,
                {**row.payload, "revision": row.revision + 1, "state": "cancelled"}
                if namespace == QUESTIONS
                else {**row.payload, "state": "cancelled"},
                row.revision,
            )
