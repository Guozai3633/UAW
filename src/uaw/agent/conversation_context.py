"""Bounded conversation Context built from actual owned sources, without rule arbitration.

Only an explicitly admitted conversation-v1 Run uses this adapter. The single
registered platform method, current role/tool permissions and every input are
rechecked; there is no semantic rule-selection call or cached authorization.
"""

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from uaw.agent.contracts import Payload, identifier
from uaw.agent.conversation import enabled
from uaw.agent.ports import PreparedAgentContext
from uaw.agent.sources import check_pin
from uaw.context.seed import snapshot_hash
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import RecordTransaction, reference
from uaw.model.contracts import ModelPrompt
from uaw.run.inputs import RunInputReader
from uaw.run.tool_sources import reference as source_reference
from uaw.shared.contracts import Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import contract_validation_scope, validate_contract
from uaw.shared.stores import StoreMissing
from uaw.tool.discovery import require_entry

if TYPE_CHECKING:
    from uaw.agent.adapters import RegisteredAgentContexts

NAMESPACE = "context.conversation.bindings"
PREPARATIONS = "agent.conversation.preparations"


class ConversationContexts:
    def __init__(self, legacy: RegisteredAgentContexts) -> None:
        self.legacy = legacy
        if not isinstance(legacy.inputs.records, PostgresRecordStore):
            raise TypeError("Actual PostgreSQL conversation sources required")
        self.records = legacy.inputs.records

    async def prepare(
        self, operation_id: str, observations: tuple[Ref, ...], ctx: TrustedExecutionContext
    ) -> PreparedAgentContext:
        if (
            not await enabled(self.records, ctx)
            or self.legacy.instruction_refs
            or self.legacy.retriever is not None
        ):
            return await self.legacy.prepare(operation_id, observations, ctx)
        async with self.records.current_reads(), contract_validation_scope():
            return await self._prepare(operation_id, observations, ctx)

    async def _prepare(
        self, operation_id: str, observations: tuple[Ref, ...], ctx: TrustedExecutionContext
    ) -> PreparedAgentContext:
        key = identifier("conversation-context-", {"run": ctx.run_id, "operation": operation_id})
        try:
            existing = await self.records.get(ctx.principal, PREPARATIONS, key)
        except StoreMissing:
            existing = None
        if existing is not None:
            await self.resolve(reference("context", key), ctx)
            return PreparedAgentContext(
                Ref.model_validate(reference("context", key)),
                existing.payload["request"]["expected_epoch"],
            )
        view = await self.legacy.sources.current(ctx)
        inputs = await RunInputReader(self.records).read(ctx)
        async with self.records.database.sessions() as sql:
            history = list(
                await sql.scalars(
                    select(RecordRow)
                    .where(
                        RecordRow.principal_id == ctx.principal.id,
                        RecordRow.namespace == "items",
                        RecordRow.deleted.is_(False),
                        RecordRow.payload["conversation_id"].as_string() == ctx.conversation_id,
                        RecordRow.payload["run_id"].as_string() != ctx.run_id,
                        RecordRow.payload["type"]
                        .as_string()
                        .in_(("user_message", "agent_message")),
                        RecordRow.payload["status"].as_string() == "completed",
                    )
                    .order_by(RecordRow.updated_at.desc(), RecordRow.resource_id)
                    .limit(8)
                )
            )
        history_refs = [
            source_reference("item", r.resource_id, r.revision, r.payload).wire()
            for r in reversed(history)
        ]
        access = await self.legacy.access.snapshot(ctx)
        revision, entries = self.legacy.registry.snapshot()
        tools = []
        from uaw.shared.errors import DomainError

        for entry in entries:
            try:
                require_entry(entry, access)
            except DomainError:
                continue
            tools.append(entry.spec())
        if len(tools) > 64:
            raise reject("conversation_tools_unbounded", "Bounded tool selection required", 503)
        key = identifier("conversation-context-", {"run": ctx.run_id, "operation": operation_id})
        recipe: Payload = {
            "context": ctx.wire(),
            "revision": 1,
            "request": {
                "purpose": "agent_step",
                "source_refs": [*inputs.refs, *history_refs, *[r.wire() for r in observations]],
                "model_policy_ref": ctx.model_policy_ref.wire() if ctx.model_policy_ref else {},
                "output_reserve": self.legacy.output_reserve,
                "tool_reserve": 0,
                "expected_epoch": inputs.state["revision"],
                "preserve": {
                    "required_refs": list(inputs.refs),
                    "exact_strings": [],
                    "requirement_ids": [],
                    "pending_action_refs": [],
                },
            },
            "rules": {
                "scope_paths": [],
                "user_instruction_refs": [view.role["instructions_ref"]],
                "activated_skill_refs": [],
            },
            "tools": {"run_id": ctx.run_id, "tools": tools},
        }
        validate_contract("AgentContextPreparation", recipe)
        prompt, dependencies = await self._prompt(recipe, ctx)
        snapshot = self._snapshot(key, recipe, prompt, dependencies)
        validate_contract("ContextSnapshot", snapshot)

        async def write(tx: RecordTransaction) -> Payload:
            actual = await tx.load("run.input_sets", ctx.run_id or "")
            if (
                actual.payload != inputs.state
                or (await self.legacy.sources.current(ctx)).frame != view.frame
            ):
                raise reject(
                    "conversation_context_stale", "Original inputs changed before preparation", 412
                )
            await tx.write(PREPARATIONS, key, "AgentContextPreparation", recipe)
            await tx.write("context.snapshots", key, "ContextSnapshot", snapshot)
            await tx.write("context.capabilities", key, "ModelToolSet", recipe["tools"])
            await tx.write(
                NAMESPACE,
                key,
                "ModelContextBinding",
                {
                    "snapshot_ref": reference("context", key),
                    "run_id": ctx.run_id,
                    "conversation_id": ctx.conversation_id,
                },
            )
            return reference("context", key)

        from uaw.infrastructure.db.transactions import TransactionalStore

        ref = await TransactionalStore(self.records.database).execute(
            ctx.principal,
            "conversation:" + (ctx.conversation_id or ""),
            RequestMeta(request_id=key, schema_version="0.1"),
            {"recipe": recipe, "snapshot": snapshot},
            write,
        )
        if revision != self.legacy.registry.snapshot()[0]:
            raise reject("conversation_catalogue_changed", "Tool catalogue changed", 412)
        return PreparedAgentContext(Ref.model_validate(ref), snapshot["epoch"])

    @staticmethod
    def _snapshot(
        key: str, recipe: Payload, prompt: ModelPrompt, dependencies: list[Payload]
    ) -> Payload:
        inputs = [r for r in recipe["request"]["source_refs"] if r["kind"] == "input"]
        snapshot: Payload = {
            "id": key,
            "epoch": recipe["request"]["expected_epoch"],
            "purpose": "agent_step",
            "blocks": [
                {
                    "id": "original-input",
                    "kind": "user_input",
                    "source_refs": inputs,
                    "content_ref": inputs[0],
                    "estimated_tokens": prompt.estimated_tokens,
                    "required": True,
                    "trust": "user",
                }
            ],
            "instruction_set_ref": dependencies[0],
            "capability_snapshot_ref": reference("configuration", key),
            "input_tokens": prompt.estimated_tokens,
            "output_reserve": recipe["request"]["output_reserve"],
            "tool_reserve": 0,
            "omitted_refs": [],
            "compressed_refs": [],
        }
        snapshot["manifest"] = {
            "version": "conversation-v1",
            "input_refs": recipe["request"]["source_refs"],
            "dependency_refs": dependencies,
            "content_hash": snapshot_hash(snapshot),
        }
        return snapshot

    async def _prompt(
        self, recipe: Payload, ctx: TrustedExecutionContext
    ) -> tuple[ModelPrompt, list[Payload]]:
        if recipe["context"] != ctx.wire() or not await enabled(self.records, ctx):
            raise reject("conversation_context_denied", "Original Context owner differs", 403)
        if recipe["rules"]["scope_paths"] or recipe["rules"]["activated_skill_refs"]:
            raise reject(
                "conversation_rules_unsupported", "Additional rules require full Context", 503
            )
        before = await self.legacy.sources.current(ctx)
        inputs = await RunInputReader(self.records).read(ctx)
        expected_inputs = [r for r in recipe["request"]["source_refs"] if r["kind"] == "input"]
        if (
            expected_inputs != list(inputs.refs)
            or recipe["request"]["expected_epoch"] != inputs.state["revision"]
        ):
            raise reject("conversation_context_stale", "Input revision changed", 412)
        rule = Ref.model_validate(before.role["instructions_ref"])
        if recipe["rules"]["user_instruction_refs"] != [rule.wire()]:
            raise reject("conversation_role_changed", "Original method changed", 412)
        reading = await self.legacy.inputs.read(rule, ctx)
        if reading.kind != "instruction" or reading.ref != rule or reading.trust != "platform":
            raise reject("conversation_rule_denied", "Registered platform method required", 403)
        access = await self.legacy.access.snapshot(ctx)
        available = []
        for spec in recipe["tools"]["tools"]:
            entry = self.legacy.registry.get(
                {"kind": "configuration", "id": spec["id"], "version": spec["version"]}
            )
            require_entry(entry, access)
            if entry.spec() != spec:
                raise reject(
                    "conversation_catalogue_changed", "Original tool specification changed", 412
                )
            available.append(
                {
                    "tool_ref": self.legacy.registry.reference(entry),
                    "description": spec["description"],
                    "input_schema": spec["input_schema"],
                }
            )
        data: Payload = {
            "task": before.frame["goal"],
            "inputs": inputs.inputs,
            "history": [],
            "observations": [],
            "available_tools": available,
        }
        for raw in recipe["request"]["source_refs"]:
            ref = Ref.model_validate(raw)
            if ref.kind == "item":
                row = await self.records.get(ctx.principal, "items", ref.id)
                check_pin(ref, "item", row.resource_id, row.revision, row.payload)
                value = row.payload
                if (
                    value["conversation_id"] != ctx.conversation_id
                    or value.get("run_id") == ctx.run_id
                    or value["type"] not in ("user_message", "agent_message")
                    or value["status"] != "completed"
                ):
                    raise reject(
                        "conversation_history_denied", "History belongs to another scope", 403
                    )
                text = value.get("text", "")
                data["history"].append(
                    {
                        "ref": raw,
                        "type": value["type"],
                        "text": text[:2000],
                        "truncated": len(text) > 2000,
                    }
                )
            elif ref.kind == "content":
                data["observations"].append(await self.legacy.observations.read(ref, ctx))
        messages = (
            {"role": "system", "content": reading.text},
            {"role": "user", "content": json.dumps(data, ensure_ascii=False, allow_nan=False)},
        )
        prompt = ModelPrompt(
            messages,
            tuple(recipe["tools"]["tools"]),
            sum(len(m["content"].encode()) + 64 for m in messages),
        )
        if (await self.legacy.sources.current(ctx)) != before:
            raise reject(
                "conversation_context_stale", "Current task changed during Context read", 412
            )
        return prompt, [rule.wire(), before.role_ref.wire(), *[e["tool_ref"] for e in available]]

    async def resolve(self, raw: Payload, ctx: TrustedExecutionContext) -> ModelPrompt:
        async with self.records.current_reads(), contract_validation_scope():
            return await self._resolve(raw, ctx)

    async def _resolve(self, raw: Payload, ctx: TrustedExecutionContext) -> ModelPrompt:
        ref = Ref.model_validate(raw)
        binding = await self.records.get(ctx.principal, NAMESPACE, ref.id)
        row = await self.records.get(ctx.principal, "context.snapshots", ref.id)
        check_pin(ref, "context", row.resource_id, row.revision, row.payload)
        if binding.schema_name != "ModelContextBinding" or binding.payload != {
            "snapshot_ref": reference("context", ref.id),
            "run_id": ctx.run_id,
            "conversation_id": ctx.conversation_id,
        }:
            raise reject("conversation_context_denied", "Original snapshot binding differs", 403)
        recipe = await self.records.get(ctx.principal, PREPARATIONS, ref.id)
        validate_contract("AgentContextPreparation", recipe.payload)
        prompt, dependencies = await self._prompt(recipe.payload, ctx)
        snapshot = row.payload
        capabilities = await self.records.get(ctx.principal, "context.capabilities", ref.id)
        if (
            snapshot != self._snapshot(ref.id, recipe.payload, prompt, dependencies)
            or snapshot.get("manifest", {}).get("content_hash") != snapshot_hash(snapshot)
            or snapshot["manifest"]["input_refs"] != recipe.payload["request"]["source_refs"]
            or snapshot["manifest"]["dependency_refs"] != dependencies
            or snapshot["epoch"] != recipe.payload["request"]["expected_epoch"]
            or snapshot["output_reserve"] != recipe.payload["request"]["output_reserve"]
            or capabilities.payload != recipe.payload["tools"]
        ):
            raise reject("conversation_snapshot_changed", "Original Context manifest differs", 412)
        return prompt
