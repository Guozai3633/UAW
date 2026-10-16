"""New-Run admission, literal source projection and atomic message publication."""

from datetime import UTC, datetime

from uaw.agent.assembly import AgentAssembly
from uaw.agent.contracts import Payload, identifier
from uaw.agent.conversation import BINDINGS, DECISIONS, execution_decision
from uaw.agent.sources import check_pin
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import (
    RecordTransaction,
    TransactionalStore,
    reference,
    timestamp,
)
from uaw.run.clock_ports import ClockChange, ConversationClockPort
from uaw.run.inputs import RunInputReader
from uaw.run.tool_sources import reference as source_reference
from uaw.shared.contracts import Principal, Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing


async def admit(tx: RecordTransaction, run: Payload, actor: Principal) -> None:
    # File-source Runs keep their original separately accepted protocol.
    from uaw.run.file_admission import NAMESPACE

    try:
        await tx.load(NAMESPACE, run["id"])
    except StoreMissing:
        pass
    else:
        return
    now = timestamp()
    remaining = int(
        (
            datetime.fromisoformat(run["budget"]["deadline"].replace("Z", "+00:00"))
            - datetime.now(UTC)
        ).total_seconds()
        * 1000
    )
    if remaining <= 0:
        raise reject("conversation_deadline_expired", "Original admission deadline expired", 409)
    clock = {
        "protocol": "conversation-v1",
        "run_id": run["id"],
        "revision": 1,
        "mode": "active",
        "active_limit_ms": min(remaining, 604800000),
        "active_elapsed_ms": 0,
        "wait_elapsed_ms": 0,
        "captured_at": now,
        "active_since": now,
        "in_flight_refs": [],
    }
    await tx.write("run.execution_clocks", run["id"], "RunExecutionClock", clock)
    await tx.write(
        BINDINGS,
        run["id"],
        "ConversationProtocolBinding",
        {
            "protocol": "conversation-v1",
            "run_id": run["id"],
            "owner_id": actor.id,
            "revision": 1,
            "input_revision": 1,
            "completion_mode": "message",
            "clock_ref": reference("checkpoint", run["id"]),
        },
    )


async def source_frame(records: PostgresRecordStore, ctx: TrustedExecutionContext) -> Payload:
    """Reuse the execution frame shape with exact user text, without AI parsing."""
    inputs = await RunInputReader(records).read(ctx)
    key = inputs.run["task_id"]
    goal = inputs.inputs[0]["text"]
    for value in inputs.inputs[1:]:
        goal += "\n\n用户追加要求：\n" + value["text"]
    frame = {
        "task_id": key,
        "revision": 1,
        "original_input_ref": inputs.refs[0],
        "patch_refs": list(inputs.refs[1:]),
        "goal": goal,
        "constraints": [],
        "output_specs": [],
        "assumptions": [],
        "unresolved": [],
        "evidence_refs": [],
        "input_revision": inputs.state["revision"],
        "created_at": timestamp(),
    }
    validate_contract("TaskFrame", frame)

    async def write(tx: RecordTransaction) -> Payload:
        current = await tx.load("run.input_sets", inputs.run["id"])
        run = await tx.load("runs", inputs.run["id"])
        ledger = await tx.load("budget.ledgers", inputs.run["id"])
        if (
            current.payload != inputs.state
            or run.payload["status"] != "preparing"
            or ledger.payload["cancel_requested"]
        ):
            raise reject(
                "conversation_frame_stale", "Original task cannot accept its source frame", 412
            )
        try:
            previous = await tx.load("intent.frames", key)
        except StoreMissing:
            expected = 0
        else:
            expected = previous.revision
            if previous.payload["input_revision"] == current.revision:
                actual_binding = await tx.load("intent.frame_bindings", f"{key}.{expected}")
                task = await tx.load("tasks", key)
                existing_ref = reference("task_frame", key, expected)
                if (
                    previous.payload["original_input_ref"] == inputs.refs[0]
                    and previous.payload["patch_refs"] == list(inputs.refs[1:])
                    and previous.payload["goal"] == goal
                    and actual_binding.payload == inputs.state
                    and run.payload.get("frame_ref") == existing_ref
                    and task.payload.get("frame_ref") == existing_ref
                ):
                    return existing_ref
            if (
                previous.payload["task_id"] != key
                or previous.payload["original_input_ref"] != inputs.refs[0]
                or previous.payload["input_revision"] >= current.revision
            ):
                raise reject("conversation_frame_stale", "Prior frame sources differ", 412)
        next_frame = {**frame, "revision": expected + 1}
        await tx.write("intent.frames", key, "TaskFrame", next_frame, expected)
        # This is a copy of the actual RunInputState, explicitly not an
        # IntentSemanticRecord or a claimed model understanding.
        await tx.write(
            "intent.frame_bindings", f"{key}.{expected + 1}", "RunInputState", inputs.state
        )
        ref = reference("task_frame", key, expected + 1)
        for namespace, row, schema in (
            ("runs", run, "RunRecord"),
            ("tasks", await tx.load("tasks", key), "TaskRecord"),
        ):
            base_revision = row.revision
            value = {**row.payload, "revision": base_revision + 1, "frame_ref": ref}
            await tx.write(namespace, row.resource_id, schema, value, row.revision)
            if namespace == "runs":
                await tx.emit(
                    inputs.run["conversation_id"],
                    "run.updated",
                    value,
                    base_revision=base_revision,
                    result_revision=base_revision + 1,
                )
        return ref

    return await TransactionalStore(records.database).execute(
        ctx.principal,
        "conversation:" + inputs.run["conversation_id"],
        RequestMeta(
            request_id=f"conversation-source-{inputs.run['id']}-{inputs.state['revision']}",
            schema_version="0.1",
        ),
        {"input_state": inputs.state},
        write,
    )


async def settled_effects(tx: RecordTransaction, ctx: TrustedExecutionContext) -> None:
    from uaw.run.clock_sources import RunIdleEffects

    await RunIdleEffects().check(tx, ctx.principal, ctx.run_id or "")


async def publish(
    agent: AgentAssembly,
    operation_id: str,
    ctx: TrustedExecutionContext,
    *,
    clocks: ConversationClockPort | None = None,
) -> Payload:
    records = agent.repository.store
    operation = await agent.repository.operation(operation_id, ctx)
    if operation.phase != "finished" or operation.model_result is None:
        raise reject("conversation_decision_unfinished", "Original operation must finish", 409)
    output = await agent.runtime.loop.models.read(operation.model_result, ctx)
    decision = output["structured_data"]
    validate_contract("FirstDecision", decision)
    if (
        decision["action"] not in ("reply", "ask")
        or execution_decision(decision) != operation.proposal
    ):
        raise reject("conversation_decision_invalid", "Original reply/question required", 412)
    await agent.runtime.loop.verify(operation, ctx)
    decision_row = await records.get(ctx.principal, DECISIONS, ctx.attempt_id)
    decision_ref = source_reference(
        "content", decision_row.resource_id, decision_row.revision, decision_row.payload
    ).wire()
    item_id = identifier("conversation-message-", {"operation": operation_id})

    async def write(tx: RecordTransaction) -> Payload:
        await agent.runtime.loop.verify(operation, ctx)
        run = await tx.load("runs", ctx.run_id or "")
        actual_op = await tx.load("agent.loop.operations", operation.id)
        actual_decision = await tx.load(DECISIONS, ctx.attempt_id)
        binding = await tx.load(BINDINGS, ctx.run_id or "")
        inputs = await tx.load("run.input_sets", ctx.run_id or "")
        frame = await tx.load("intent.frames", ctx.task_id or "")
        check_pin(
            Ref.model_validate(operation.request["current_frame_ref"]),
            "task_frame",
            frame.resource_id,
            frame.revision,
            frame.payload,
        )
        if (
            actual_op.payload != operation.wire()
            or actual_decision.payload != decision_row.payload
            or decision_row.payload["decision"] != decision
            or binding.payload["owner_id"] != ctx.principal.id
            or binding.payload["input_revision"] != inputs.revision
            or decision_row.payload["input_revision"] != inputs.revision
            or run.payload["conversation_id"] != ctx.conversation_id
            or run.payload["task_id"] != ctx.task_id
            or frame.payload["input_revision"] != inputs.revision
            or run.payload["status"] != "running"
            or run.payload.get("root_agent_ref", {}).get("id") != operation.instance_id
            or min(
                datetime.fromisoformat(x.replace("Z", "+00:00"))
                for x in (ctx.deadline, run.payload["budget"]["deadline"])
            )
            <= datetime.now(UTC)
        ):
            raise reject(
                "conversation_publication_stale", "Original Run/input/model sources changed", 412
            )
        source_output = await tx.load(
            "model.outputs", decision_row.payload["model_output_ref"]["id"]
        )
        invocation = await tx.load("model.invocations", ctx.attempt_id)
        root = await tx.load("agent.loop.states", operation.instance_id)
        if (
            source_output.payload != output
            or invocation.payload.get("result") != operation.model_result
            or root.payload.get("active_operation_ref")
        ):
            raise reject(
                "conversation_model_unowned", "Original model/operation ownership differs", 412
            )
        await settled_effects(tx, ctx)
        clock = await tx.load("run.execution_clocks", ctx.run_id or "")
        if clock.payload["mode"] != "active" or "active_since" not in clock.payload:
            raise reject(
                "conversation_active_clock_required",
                "Original execution clock must resume before publishing a new response",
                503,
            )
        now = timestamp()
        item = {
            "id": item_id,
            "conversation_id": ctx.conversation_id,
            "run_id": ctx.run_id,
            "type": "agent_message",
            "status": "completed",
            "revision": 1,
            "text": decision.get("text", decision.get("question", {}).get("text", "")),
            "resource_refs": [
                decision_ref,
                decision_row.payload["model_output_ref"],
                *operation.request["observations"],
            ],
            "created_at": now,
            "updated_at": now,
        }
        await tx.write("items", item_id, "InteractionItem", item)
        await tx.emit(
            ctx.conversation_id or "", "item.updated", item, item_ref=reference("item", item_id)
        )
        changed = {
            **run.payload,
            "revision": run.revision + 1,
            "status": "completed" if decision["action"] == "reply" else "waiting_for_user",
        }
        if decision["action"] == "reply":
            changed.update(outcome="succeeded", ended_at=now)
            task = await tx.load("tasks", ctx.task_id or "")
            await tx.write(
                "tasks",
                task.resource_id,
                "TaskRecord",
                {
                    **task.payload,
                    "revision": task.revision + 1,
                    "active_run_refs": [
                        r for r in task.payload["active_run_refs"] if r["id"] != ctx.run_id
                    ],
                },
                task.revision,
            )
        else:
            await tx.write(
                "run.clarification_questions",
                item_id,
                "ClarificationQuestion",
                {
                    "protocol": "conversation-v1",
                    "run_id": ctx.run_id,
                    "conversation_id": ctx.conversation_id,
                    "item_id": item_id,
                    "revision": 1,
                    "input_revision": inputs.revision,
                    "prompt": decision["question"],
                    "decision_record_ref": decision_ref,
                    "state": "open",
                    "created_at": now,
                },
            )
        run_base = run.revision
        await tx.write("runs", run.resource_id, "RunRecord", changed, run_base)
        if clocks is not None:
            clock_limit = clock.payload["active_limit_ms"]
            clock_revision = clock.revision
            result = await clocks.change(
                tx,
                ctx.principal,
                ctx.run_id or "",
                ClockChange(
                    clock_revision,
                    "stopped" if decision["action"] == "reply" else "waiting_for_user",
                    waiting_item_ref=(
                        Ref.model_validate(reference("item", item_id))
                        if decision["action"] == "ask"
                        else None
                    ),
                ),
            )
            actual = await tx.load("run.execution_clocks", ctx.run_id or "")
            current_binding = await tx.load(BINDINGS, ctx.run_id or "")
            if (
                result.wire() != actual.payload
                or actual.revision != clock_revision + 1
                or result.revision != actual.revision
                or result.run_id != ctx.run_id
                or result.mode
                != ("stopped" if decision["action"] == "reply" else "waiting_for_user")
                or result.active_limit_ms != clock_limit
                or current_binding.payload["clock_ref"]
                != reference("checkpoint", actual.resource_id, actual.revision)
                or current_binding.payload["input_revision"] != inputs.revision
                or run.payload != changed
            ):
                raise reject(
                    "conversation_clock_source_changed", "Original clock result differs", 412
                )
        else:
            await legacy_clock(tx, clock, binding, decision, item_id, now)
        event = await tx.emit(
            ctx.conversation_id or "",
            "run.updated",
            changed,
            base_revision=run_base,
            result_revision=run_base + 1,
        )
        if decision["action"] == "reply":
            receipt = {
                "protocol": "conversation-v1",
                "run": changed,
                "item": item,
                "input_revision": inputs.revision,
                "event_seq": event["seq"],
            }
            await tx.write("run.conversation.replies", item_id, "ReplyCommitReceipt", receipt)
            return receipt
        return {"question_item_id": item_id, "run": changed}

    return await TransactionalStore(records.database).execute(
        ctx.principal,
        "conversation:" + (ctx.conversation_id or ""),
        RequestMeta(request_id=item_id, schema_version="0.1"),
        {"operation": operation.wire()},
        write,
    )


async def legacy_clock(
    tx: RecordTransaction,
    clock: RecordRow,
    binding: RecordRow,
    decision: Payload,
    item_id: str,
    now: str,
) -> None:
    """Original deployment compatibility; new composition injects the owning port."""
    clock_base = clock.revision
    elapsed = max(
        0,
        int(
            (
                datetime.fromisoformat(now)
                - datetime.fromisoformat(clock.payload["active_since"].replace("Z", "+00:00"))
            ).total_seconds()
            * 1000
        ),
    )
    clock_value = {
        **clock.payload,
        "revision": clock_base + 1,
        "captured_at": now,
        "active_elapsed_ms": clock.payload["active_elapsed_ms"] + elapsed,
        "mode": "stopped" if decision["action"] == "reply" else "waiting_for_user",
    }
    clock_value.pop("active_since", None)
    if decision["action"] == "ask":
        clock_value.update(waiting_since=now, waiting_item_ref=reference("item", item_id))
    await tx.write(
        "run.execution_clocks",
        clock.resource_id,
        "RunExecutionClock",
        clock_value,
        clock_base,
    )
    await tx.write(
        BINDINGS,
        binding.resource_id,
        "ConversationProtocolBinding",
        {
            **binding.payload,
            "revision": binding.revision + 1,
            "clock_ref": reference("checkpoint", clock.resource_id, clock_base + 1),
        },
        binding.revision,
    )


async def select_delivery(records: PostgresRecordStore, ctx: TrustedExecutionContext) -> None:
    decision = await records.get(ctx.principal, DECISIONS, ctx.attempt_id)
    validate_contract("FirstDecisionRecord", decision.payload)
    if (
        decision.payload["decision"]["action"] != "deliver"
        or decision.payload["run_ref"]["id"] != ctx.run_id
    ):
        raise reject(
            "conversation_delivery_denied", "Original formal delivery decision required", 403
        )

    async def write(tx: RecordTransaction) -> Payload:
        binding = await tx.load(BINDINGS, ctx.run_id or "")
        inputs = await tx.load("run.input_sets", ctx.run_id or "")
        actual = await tx.load(DECISIONS, ctx.attempt_id)
        ledger = await tx.load("budget.ledgers", ctx.run_id or "")
        if (
            binding.payload["owner_id"] != ctx.principal.id
            or actual.payload != decision.payload
            or binding.payload["input_revision"] != inputs.revision
            or decision.payload["input_revision"] != inputs.revision
            or ledger.payload["cancel_requested"]
        ):
            raise reject("conversation_delivery_stale", "Original delivery sources changed", 412)
        await tx.write(
            BINDINGS,
            binding.resource_id,
            "ConversationProtocolBinding",
            {
                **binding.payload,
                "revision": binding.revision + 1,
                "completion_mode": "delivery",
            },
            binding.revision,
        )
        return {}

    await TransactionalStore(records.database).execute(
        ctx.principal,
        "conversation:" + (ctx.conversation_id or ""),
        RequestMeta(request_id="delivery-mode-" + ctx.attempt_id, schema_version="0.1"),
        {"decision": decision.payload},
        write,
    )
