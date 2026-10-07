"""Bounded understanding context. General Context facade and rule inheritance are still pending."""

import hashlib
import json
from importlib.resources import files

from uaw.context.seed import snapshot_hash
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore, reference
from uaw.model.contracts import ModelPrompt, Payload
from uaw.model.gateway import request_meta
from uaw.run.inputs import InputSet, RunInputReader
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import reject


def understanding_template() -> str:
    return (
        files("uaw.resources")
        .joinpath("prompts/intent-understand-v1.txt")
        .read_text(encoding="utf-8")
    )


def user_message(index: int, text: str) -> str:
    return json.dumps({"source_index": index, "text": text}, ensure_ascii=False)


class IntentContexts:
    def __init__(self, store: PostgresRecordStore, sources: RunInputReader) -> None:
        self.store, self.sources = store, sources
        self.transactions = TransactionalStore(store.database)

    async def _values(
        self, inputs: InputSet, ctx: TrustedExecutionContext, output_reserve: int
    ) -> tuple[Payload, Payload, str]:
        template = understanding_template()
        template_hash = hashlib.sha256(template.encode()).hexdigest()
        context_id = "understanding-" + hashlib.sha256(ctx.attempt_id.encode()).hexdigest()
        rule_ref = reference("rule", context_id)
        rule = {
            "id": "intent-understand-v1",
            "source_ref": {
                **reference("rule", "intent-understand-v1"),
                "content_hash": template_hash,
            },
            "level": "platform",
            "scope": {"conversation_id": inputs.run["conversation_id"]},
            "text": template,
        }
        blocks = [
            {
                "id": "understanding-instructions",
                "kind": "instruction",
                "source_refs": [rule["source_ref"]],
                "content_ref": rule_ref,
                "estimated_tokens": len(template.encode()) + 64,
                "required": True,
                "trust": "platform",
            }
        ]
        for index, (ref, value) in enumerate(zip(inputs.refs, inputs.inputs, strict=True)):
            blocks.append(
                {
                    "id": f"input-{index}",
                    "kind": "user_input",
                    "source_refs": [ref],
                    "content_ref": ref,
                    "estimated_tokens": len(user_message(index, value["text"]).encode()) + 64,
                    "required": True,
                    "trust": "user",
                }
            )
        snapshot: Payload = {
            "id": context_id,
            "epoch": inputs.state["revision"],
            "purpose": "understanding",
            "blocks": blocks,
            "instruction_set_ref": rule_ref,
            "capability_snapshot_ref": reference("configuration", context_id),
            "input_tokens": sum(block["estimated_tokens"] for block in blocks),
            "output_reserve": output_reserve,
            "tool_reserve": 0,
            "omitted_refs": [],
            "compressed_refs": [],
        }
        binding = (await self.store.get(ctx.principal, "run.bindings", inputs.run["id"])).payload
        snapshot["manifest"] = {
            "version": "1",
            "input_refs": list(inputs.refs),
            "dependency_refs": [binding["configuration_ref"], rule["source_ref"]],
            "content_hash": snapshot_hash(snapshot),
        }
        return snapshot, rule, template_hash

    async def prepare(
        self, inputs: InputSet, ctx: TrustedExecutionContext, output_reserve: int
    ) -> Payload:
        snapshot, rule, template_hash = await self._values(inputs, ctx, output_reserve)
        context_id = snapshot["id"]

        async def write(tx: RecordTransaction) -> Payload:
            current = await tx.load("run.input_sets", inputs.run["id"])
            if current.payload != inputs.state:
                raise reject(
                    "intent_input_stale", "User requirements changed before preparation", 412
                )
            await tx.write(
                "context.instructions",
                context_id,
                "InstructionSet",
                {"rules": [rule], "conflict_refs": [], "version": "1"},
            )
            await tx.write(
                "context.capabilities",
                context_id,
                "ModelToolSet",
                {"run_id": inputs.run["id"], "tools": []},
            )
            await tx.write("context.snapshots", context_id, "ContextSnapshot", snapshot)
            await tx.write(
                "context.bindings",
                context_id,
                "ModelContextBinding",
                {
                    "snapshot_ref": reference("context", context_id),
                    "run_id": inputs.run["id"],
                    "conversation_id": inputs.run["conversation_id"],
                },
            )
            await tx.write(
                "context.intent_bindings",
                context_id,
                "IntentContextBinding",
                {
                    "run_id": inputs.run["id"],
                    "input_revision": inputs.state["revision"],
                    "source_refs": list(inputs.refs),
                    "template_hash": template_hash,
                },
            )
            return reference("context", context_id)

        return await self.transactions.execute(
            ctx.principal,
            f"conversation:{inputs.run['conversation_id']}",
            request_meta("intent-context", ctx.attempt_id),
            {"snapshot": snapshot},
            write,
        )

    async def resolve(self, snapshot: Payload, ctx: TrustedExecutionContext) -> ModelPrompt:
        inputs = await self.sources.read(ctx)
        binding = (
            await self.store.get(ctx.principal, "context.intent_bindings", snapshot["id"])
        ).payload
        if (
            binding["run_id"] != ctx.run_id
            or binding["input_revision"] != inputs.state["revision"]
            or binding["source_refs"] != list(inputs.refs)
        ):
            raise reject(
                "intent_input_stale", "User requirements changed after snapshot creation", 412
            )
        expected, rule, template_hash = await self._values(inputs, ctx, snapshot["output_reserve"])
        if snapshot != expected:
            raise reject(
                "intent_context_invalid",
                "Understanding snapshot differs from its source manifest",
                412,
            )
        template = understanding_template()
        if template_hash != binding["template_hash"]:
            raise reject("intent_template_stale", "Understanding template changed", 412)
        rule_set = (
            await self.store.get(ctx.principal, "context.instructions", snapshot["id"])
        ).payload
        tools = (
            await self.store.get(ctx.principal, "context.capabilities", snapshot["id"])
        ).payload
        if rule_set != {"rules": [rule], "conflict_refs": [], "version": "1"} or tools != {
            "run_id": ctx.run_id,
            "tools": [],
        }:
            raise reject(
                "intent_rules_invalid",
                "Only the packaged understanding instruction is supported",
                412,
            )
        messages = [{"role": "system", "content": template}]
        messages.extend(
            {"role": "user", "content": user_message(index, value["text"])}
            for index, value in enumerate(inputs.inputs)
        )
        return ModelPrompt(
            tuple(messages), (), sum(len(message["content"].encode()) + 64 for message in messages)
        )
