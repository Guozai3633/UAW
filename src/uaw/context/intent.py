"""Bounded understanding context. General Context facade and rule inheritance are still pending."""

import asyncio
import hashlib
import json
from importlib.resources import files

from uaw.context.contracts import (
    InstructionRule,
    PreservationSpec,
    Reading,
    RuleCandidate,
    RulePlan,
    RulesRequest,
    SelectionRequest,
    from_wire,
)
from uaw.context.facade import ContextComponents
from uaw.context.seed import snapshot_hash
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore, reference
from uaw.model.contracts import ModelPrompt, Payload
from uaw.model.gateway import request_meta
from uaw.run.context import RunContextSources
from uaw.run.inputs import InputSet, RunInputReader
from uaw.shared.contracts import Ref, ScopeSelector, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject


def understanding_template() -> str:
    return (
        files("uaw.resources")
        .joinpath("prompts/intent-understand-v1.txt")
        .read_text(encoding="utf-8")
    )


def user_message(index: int, text: str) -> str:
    return json.dumps({"source_index": index, "text": text}, ensure_ascii=False)


class UnderstandingRules:
    """Only the packaged platform rule; project/skill inheritance remains unavailable."""

    def __init__(self, authority: RunContextSources) -> None:
        self.authority = authority

    async def check(self, ref: Ref, ctx: TrustedExecutionContext) -> None:
        await self.authority.authorize(ctx)
        if (ref.kind, ref.id, ref.version) != (
            "rule",
            "intent-understand-v1",
            "1",
        ) or ref.location is not None:
            raise CapabilityUnavailable("context.registered_platform_rule")
        if (
            ref.content_hash is not None
            and ref.content_hash
            != hashlib.sha256(understanding_template().encode("utf-8")).hexdigest()
        ):
            raise reject("source_changed", "Packaged instruction changed", 410)

    async def read(self, ref: Ref, revision_policy: str, ctx: TrustedExecutionContext) -> Reading:
        if revision_policy != "pinned":
            raise CapabilityUnavailable("context.platform_rule_latest")
        await self.check(ref, ctx)
        template = understanding_template()
        actual = from_wire(
            Ref,
            {
                **reference("rule", "intent-understand-v1"),
                "content_hash": hashlib.sha256(template.encode("utf-8")).hexdigest(),
            },
        )
        return Reading(actual, template, kind="instruction", trust="platform", required=True)

    async def discover(self, request: RulesRequest, ctx: TrustedExecutionContext) -> RulePlan:
        await self.authority.authorize(ctx)
        if request.scope_paths or request.user_instruction_refs or request.activated_skill_refs:
            raise CapabilityUnavailable("context.project_skill_user_rule_inheritance")
        reading = await self.read(
            Ref(kind="rule", id="intent-understand-v1", version="1"), "pinned", ctx
        )
        rule = InstructionRule(
            id="intent-understand-v1",
            source_ref=reading.ref,
            level="platform",
            scope=ScopeSelector(conversation_id=ctx.scope.conversation_id),
            text=reading.text,
        )
        # One registered instruction has no competing rule. This is not a semantic assessor.
        return RulePlan((RuleCandidate(rule),), assessment_complete=True)


class IntentContexts:
    def __init__(
        self, store: PostgresRecordStore, sources: RunInputReader, components: ContextComponents
    ) -> None:
        self.store, self.sources = store, sources
        self.components = components
        self.transactions = TransactionalStore(store.database)

    async def _values(
        self, inputs: InputSet, ctx: TrustedExecutionContext, output_reserve: int
    ) -> tuple[Payload, Payload, str]:
        try:
            async with asyncio.timeout(max(0, self.components.sources.guard.remaining(ctx))):
                return await self._assemble(inputs, ctx, output_reserve)
        except TimeoutError:
            raise reject("deadline_exceeded", "Context deadline expired", 422, "timeout") from None

    async def _assemble(
        self, inputs: InputSet, ctx: TrustedExecutionContext, output_reserve: int
    ) -> tuple[Payload, Payload, str]:
        template = understanding_template()
        template_hash = hashlib.sha256(template.encode()).hexdigest()
        context_id = "understanding-" + hashlib.sha256(ctx.attempt_id.encode()).hexdigest()
        rule_ref = reference("rule", context_id)
        binding = (await self.store.get(ctx.principal, "run.bindings", inputs.run["id"])).payload
        # Optional context metadata is filled only from the persisted user policy.
        if ctx.model_policy_ref is None:
            ctx = ctx.model_copy(
                update={"model_policy_ref": from_wire(Ref, binding["model_policy_ref"])}
            )
        assembly = await self.components.rules.assemble(
            RulesRequest(scope_paths=(), user_instruction_refs=(), activated_skill_refs=()), ctx
        )
        if len(assembly.instructions.rules) != 1 or assembly.instructions.rules[0].text != template:
            raise reject("intent_rules_invalid", "Understanding needs its fixed platform rule", 412)
        models = self.components.selection.models
        if models is None or ctx.model_policy_ref is None:
            raise CapabilityUnavailable("context.fixed_model_window")
        window = await models.resolve(ctx.model_policy_ref, ctx)
        pins = tuple(from_wire(Ref, ref) for ref in inputs.refs)
        allocation = await self.components.selection.allocate(
            SelectionRequest(
                candidate_refs=(*assembly.dependencies, *pins),
                purpose="understanding",
                model_context_limit=window.context_limit,
                output_reserve=output_reserve,
                tool_reserve=0,
            ),
            ctx,
            PreservationSpec(
                required_refs=pins, exact_strings=(), requirement_ids=(), pending_action_refs=()
            ),
        )
        # No compression or dropping of admitted user input at this bounded boundary.
        if allocation.omitted or len(allocation.selected) != len(pins) + 1:
            raise reject(
                "context_insufficient", "Understanding input cannot be dropped", 422, "budget"
            )
        rule = assembly.instructions.rules[0].wire()
        instructions = assembly.instructions.wire()
        selected_inputs = allocation.selected[1:]
        if any(
            reading.text != value["text"]
            for reading, value in zip(selected_inputs, inputs.inputs, strict=True)
        ):
            raise reject("source_changed", "User text changed during context construction", 410)
        if (await self.sources.read(ctx)).state != inputs.state:
            raise reject("intent_input_stale", "User requirements changed during selection", 412)
        blocks = [
            {
                "id": "understanding-instructions",
                "kind": "instruction",
                "source_refs": [rule["source_ref"]],
                "content_ref": rule_ref,
                "estimated_tokens": self.components.selection.counter.count(allocation.selected[0]),
                "required": True,
                "trust": "platform",
            }
        ]
        for index, reading in enumerate(selected_inputs):
            ref = reading.ref.wire()
            blocks.append(
                {
                    "id": f"input-{index}",
                    "kind": "user_input",
                    "source_refs": [ref],
                    "content_ref": ref,
                    "estimated_tokens": self.components.selection.counter.count(reading),
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
        snapshot["manifest"] = {
            "version": "ms-i1",
            "input_refs": [r.ref.wire() for r in selected_inputs],
            "dependency_refs": [
                binding["configuration_ref"],
                binding["model_policy_ref"],
                rule["source_ref"],
            ],
            "content_hash": snapshot_hash(snapshot),
        }
        return snapshot, instructions, template_hash

    async def prepare(
        self, inputs: InputSet, ctx: TrustedExecutionContext, output_reserve: int
    ) -> Payload:
        snapshot, instructions, template_hash = await self._values(inputs, ctx, output_reserve)
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
                instructions,
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
        expected, instructions, template_hash = await self._values(
            inputs, ctx, snapshot["output_reserve"]
        )
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
        if rule_set != instructions or tools != {
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
