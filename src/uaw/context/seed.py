"""Diagnostic input preparation only; not the general Context Runtime or rule resolver."""

import hashlib
import json
from typing import Any

from uaw.infrastructure.db.records import PostgresRecordStore, parameter_hash
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore, reference
from uaw.model.contracts import ModelPrompt, Payload
from uaw.shared.contracts import RequestMeta, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import BlobStorePort


def revision(ref: Payload, kind: str) -> int:
    validate_contract("Ref", ref)
    if ref["kind"] != kind or not ref["version"].isascii() or not ref["version"].isdigit():
        raise reject("model_reference_invalid", "Expected a fixed, numeric-version reference")
    result = int(ref["version"])
    if result < 1 or result > 2_147_483_647:
        raise reject("model_reference_invalid", "Reference revision is outside the supported range")
    return result


def snapshot_hash(snapshot: Payload) -> str:
    return parameter_hash(
        {
            key: snapshot[key]
            for key in (
                "blocks",
                "instruction_set_ref",
                "capability_snapshot_ref",
            )
        }
    )


class StoredModelInputs:
    def __init__(self, store: PostgresRecordStore, blobs: BlobStorePort) -> None:
        self.store, self.blobs = store, blobs
        self.transactions = TransactionalStore(store.database)

    async def seed(self, ctx: TrustedExecutionContext, output_reserve: int) -> Payload:
        """Prepare a real original-input snapshot for the explicit diagnostic CLI."""
        run = (await self.store.get(ctx.principal, "runs", ctx.run_id or "")).payload
        if ctx.scope.conversation_id != run["conversation_id"]:
            raise reject("model_scope_denied", "Input scope does not match the Run", 403)
        binding = (await self.store.get(ctx.principal, "run.bindings", run["id"])).payload
        original = (
            await self.store.get(ctx.principal, "inputs", binding["input_ref"]["id"])
        ).payload
        identifier = (
            "context-" + hashlib.sha256(f"{run['id']}:{ctx.operation_id}".encode()).hexdigest()
        )
        blocks = [
            {
                "id": "original",
                "kind": "user_input",
                "source_refs": [binding["input_ref"]],
                "content_ref": binding["input_ref"],
                "estimated_tokens": len(original["text"].encode()) + 64,
                "required": True,
                "trust": "user",
            }
        ]
        snapshot: Payload = {
            "id": identifier,
            "epoch": 1,
            "purpose": "agent_step",
            "blocks": blocks,
            "instruction_set_ref": reference("rule", identifier),
            "capability_snapshot_ref": reference("configuration", identifier),
            "input_tokens": blocks[0]["estimated_tokens"],
            "output_reserve": output_reserve,
            "tool_reserve": 0,
            "omitted_refs": [],
            "compressed_refs": [],
        }
        snapshot["manifest"] = {
            "version": "1",
            "input_refs": [binding["input_ref"]],
            "dependency_refs": [binding["configuration_ref"]],
            "content_hash": snapshot_hash(snapshot),
        }

        async def write(tx: RecordTransaction) -> Payload:
            await tx.write(
                "context.instructions",
                identifier,
                "InstructionSet",
                {"rules": [], "conflict_refs": [], "version": "1"},
            )
            await tx.write(
                "context.capabilities",
                identifier,
                "ModelToolSet",
                {"run_id": run["id"], "tools": []},
            )
            await tx.write("context.snapshots", identifier, "ContextSnapshot", snapshot)
            ref = reference("context", identifier)
            await tx.write(
                "context.bindings",
                identifier,
                "ModelContextBinding",
                {
                    "snapshot_ref": ref,
                    "run_id": run["id"],
                    "conversation_id": run["conversation_id"],
                },
            )
            return ref

        return await self.transactions.execute(
            ctx.principal,
            f"conversation:{run['conversation_id']}",
            RequestMeta(request_id=identifier, schema_version="0.1"),
            {"action": "diagnostic_context", "snapshot": snapshot},
            write,
        )

    async def resolve(self, ref: Payload, ctx: TrustedExecutionContext) -> ModelPrompt:
        rev = revision(ref, "context")
        owner = ctx.principal
        bound = (await self.store.get(owner, "context.bindings", ref["id"])).payload
        if bound["run_id"] != ctx.run_id or bound["conversation_id"] != ctx.scope.conversation_id:
            raise reject("model_context_scope_denied", "Input belongs to another Run", 403)
        snapshot = (
            await self.store.get(owner, "context.snapshots", ref["id"], revision=rev)
        ).payload
        if (
            bound["snapshot_ref"] != reference("context", ref["id"], rev)
            or snapshot_hash(snapshot) != snapshot["manifest"]["content_hash"]
        ):
            raise reject(
                "model_context_stale", "Input snapshot does not match its fixed manifest", 412
            )
        if snapshot["purpose"] == "understanding":
            from uaw.context.intent import IntentContexts
            from uaw.run.inputs import RunInputReader

            return await IntentContexts(self.store, RunInputReader(self.store)).resolve(
                snapshot, ctx
            )
        rules = snapshot["instruction_set_ref"]
        instructions = (
            await self.store.get(
                owner, "context.instructions", rules["id"], revision=revision(rules, "rule")
            )
        ).payload
        if instructions["rules"] or instructions["conflict_refs"]:
            raise reject(
                "model_rules_not_rendered", "General rule composition is not connected", 503
            )
        tool_ref = snapshot["capability_snapshot_ref"]
        tool_set = (
            await self.store.get(
                owner,
                "context.capabilities",
                tool_ref["id"],
                revision=revision(tool_ref, "configuration"),
            )
        ).payload
        if tool_set["run_id"] != ctx.run_id:
            raise reject("model_tool_scope_denied", "Tool snapshot belongs to another Run", 403)
        messages: list[dict[str, Any]] = []
        estimated = 0
        binding = (await self.store.get(owner, "run.bindings", ctx.run_id or "")).payload
        for block in snapshot["blocks"]:
            content = block["content_ref"]
            if (
                block["kind"] == "user_input"
                and block["trust"] == "user"
                and content == binding["input_ref"]
            ):
                original = (
                    await self.store.get(
                        owner, "inputs", content["id"], revision=revision(content, "input")
                    )
                ).payload
                text = original["text"]
            elif (
                block["kind"] == "material"
                and block["trust"] == "external"
                and content["kind"] == "blob"
            ):
                if (
                    content["version"] != "1"
                    or content.get("content_hash", content["id"]) != content["id"]
                ):
                    raise reject(
                        "model_blob_reference_invalid", "Invalid immutable content reference"
                    )
                data = await self.blobs.get(owner, content["id"])
                if len(data) > 1_048_576:
                    raise reject("model_input_too_large", "Material exceeds the supported limit")
                text = "Untrusted reference material:\n" + data.decode("utf-8")
            else:
                raise reject(
                    "model_block_unsupported",
                    "This context block requires the full Context Runtime",
                    503,
                )
            messages.append({"role": "user", "content": text})
            estimated += len(text.encode()) + 64
        if not messages or estimated > 1_048_576:
            raise reject("model_input_invalid", "Input must be non-empty and bounded")
        if snapshot["input_tokens"] < estimated:
            raise reject(
                "model_context_estimate_invalid", "Snapshot underestimates the rendered input"
            )
        tool_estimate = sum(len(json.dumps(tool).encode()) + 64 for tool in tool_set["tools"])
        total_estimate = max(estimated, snapshot["input_tokens"]) + max(
            tool_estimate, snapshot["tool_reserve"]
        )
        if total_estimate > 1_048_576:
            raise reject("model_input_too_large", "Rendered input exceeds the supported limit")
        return ModelPrompt(tuple(messages), tuple(tool_set["tools"]), total_estimate)
