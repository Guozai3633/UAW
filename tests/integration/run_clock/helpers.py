"""Controlled stored question/decision fixture, NOT actual model or user answer."""

from copy import deepcopy

from tests.integration.test_control_plane import meta
from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.db.transactions import reference
from uaw.shared.contracts import Ref


async def install_question(p, name="clock-question"):
    async def write(tx):
        run = await tx.load("runs", p.run["id"])
        inputs = await tx.load("run.input_sets", p.run["id"])
        prompt = {
            "text": "Paste original material",
            "reason": "Required source is missing",
            "options": [],
        }
        decision = {
            "protocol": "conversation-v1",
            "run_ref": reference("run", run.resource_id, run.revision),
            "input_revision": inputs.revision,
            "decision": {"protocol": "conversation-v1", "action": "ask", "question": prompt},
            "model_output_ref": reference("content", "controlled-output"),
            "model_policy_ref": (await tx.load("run.bindings", p.run["id"])).payload[
                "model_policy_ref"
            ],
            "attempt_id": "controlled-clock-question",
            "usage_ref": reference("usage", "controlled-usage"),
        }
        await tx.write("agent.conversation.decisions", name, "FirstDecisionRecord", decision)
        decision_ref = {**reference("content", name), "content_hash": parameter_hash(decision)}
        await tx.write(
            "items",
            name,
            "InteractionItem",
            {
                "id": name,
                "conversation_id": run.payload["conversation_id"],
                "run_id": run.resource_id,
                "revision": 1,
                "type": "agent_message",
                "status": "completed",
                "text": prompt["text"],
                "resource_refs": [decision_ref],
                "created_at": p.now[0],
                "updated_at": p.now[0],
            },
        )
        await tx.write(
            "run.clarification_questions",
            name,
            "ClarificationQuestion",
            {
                "protocol": "conversation-v1",
                "run_id": run.resource_id,
                "conversation_id": run.payload["conversation_id"],
                "item_id": name,
                "revision": 1,
                "input_revision": inputs.revision,
                "prompt": prompt,
                "decision_record_ref": decision_ref,
                "state": "open",
                "created_at": p.now[0],
            },
        )
        value = {**run.payload, "revision": run.revision + 1, "status": "waiting_for_user"}
        await tx.write("runs", run.resource_id, "RunRecord", value, run.revision)
        return reference("item", name)

    p.serial += 1
    result = await p.transactions.execute(
        p.actor,
        "conversation:" + p.run["conversation_id"],
        meta(f"install-question-{p.serial}"),
        {"question": name},
        write,
    )
    return Ref.model_validate_json(__import__("json").dumps(result))


async def resolve_question(p, pin, state="stale"):
    async def write(tx):
        q = await tx.load("run.clarification_questions", pin.id)
        await tx.write(
            q.namespace,
            q.resource_id,
            q.schema_name,
            {**q.payload, "revision": q.revision + 1, "state": state},
            q.revision,
        )
        run = await tx.load("runs", p.run["id"])
        await tx.write(
            "runs",
            run.resource_id,
            "RunRecord",
            {**run.payload, "revision": run.revision + 1, "status": "preparing"},
            run.revision,
        )
        return {}

    p.serial += 1
    await p.transactions.execute(
        p.actor,
        "conversation:" + p.run["conversation_id"],
        meta(f"resolve-question-{p.serial}"),
        {},
        write,
    )


async def protected_snapshot(p):
    return {
        name: deepcopy((await p.records.get(p.actor, name, p.run["id"])).payload)
        for name in ("runs", "budget.ledgers", "run.bindings", "run.input_sets")
    }
