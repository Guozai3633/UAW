"""Generic immutable Context records over the published PostgreSQL transaction API."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from uaw.context.contracts import PreparedSnapshot, digest, from_wire, matches_pin
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore
from uaw.shared.contracts import Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import RecordStorePort, StoreMissing

SNAPSHOTS = "context.generic.snapshots"
INSTRUCTIONS = "context.generic.instructions"
BINDINGS = "context.generic.bindings"
SCOPES = "context.generic.scopes"
REFERENCES = "context.generic.references"
REQUESTS = "context.generic.requests"


def scope_key(ctx: TrustedExecutionContext) -> dict[str, Any]:
    if not ctx.run_id or not ctx.scope.conversation_id:
        raise reject("dependency_missing", "An admitted Run and conversation are required", 404)
    return {"run_id": ctx.run_id, "scope": ctx.scope.wire()}


def reference_id(ref: Ref, ctx: TrustedExecutionContext) -> str:
    # Optional hash is verified against the stored record, not used to bypass the pin.
    return "ref-" + digest(
        {
            **scope_key(ctx),
            "source": {
                "kind": ref.kind,
                "id": ref.id,
                "version": ref.version,
                "location": ref.location.wire() if ref.location is not None else None,
            },
        }
    )


def snapshot_hash(snapshot: dict[str, Any]) -> str:
    return digest({key: value for key, value in snapshot.items() if key != "manifest"})


class ContextRepository:
    def __init__(self, records: RecordStorePort, transactions: TransactionalStore) -> None:
        self.records, self.transactions = records, transactions

    async def commit(
        self,
        request: dict[str, Any],
        ctx: TrustedExecutionContext,
        prepare: Callable[[str], Awaitable[PreparedSnapshot]],
        verify: Callable[[], Awaitable[None]],
    ) -> dict[str, Any]:
        parameters = {
            "action": "generic_context_build",
            "request": request,
            **scope_key(ctx),
            "model_policy_ref": ctx.model_policy_ref.wire() if ctx.model_policy_ref else None,
            "capability_policy_ref": ctx.capability_policy_ref.wire(),
        }
        aggregate = "generic-context-" + digest(scope_key(ctx))
        identifier = "context-" + digest(
            {
                **scope_key(ctx),
                "request_id": ctx.operation_id,
            }
        )

        async def write(tx: RecordTransaction) -> dict[str, Any]:
            prepared = await prepare(identifier)
            snapshot = prepared.snapshot
            validate_contract("ContextSnapshot", snapshot)
            validate_contract("InstructionSet", prepared.instructions)
            if snapshot["id"] != identifier or snapshot["manifest"][
                "content_hash"
            ] != snapshot_hash(snapshot):
                raise reject("snapshot_invalid", "Invalid immutable Context manifest", 412)
            expected_rule_ref = {
                "kind": "rule",
                "id": identifier,
                "version": "1",
                "content_hash": digest(prepared.instructions),
            }
            if snapshot["instruction_set_ref"] != expected_rule_ref:
                raise reject(
                    "snapshot_invalid", "Instruction set does not match its fixed Ref", 412
                )
            await verify()
            if prepared.request != request:
                raise reject("snapshot_invalid", "Prepared snapshot request changed", 412)
            await tx.write(REQUESTS, identifier, "ContextRequest", request)
            await tx.write(INSTRUCTIONS, identifier, "InstructionSet", prepared.instructions)
            await tx.write(SNAPSHOTS, identifier, "ContextSnapshot", snapshot)
            pin = {
                "kind": "context",
                "id": identifier,
                "version": "1",
                "content_hash": digest(snapshot),
            }
            await tx.write(
                BINDINGS,
                identifier,
                "ModelContextBinding",
                {
                    "snapshot_ref": pin,
                    "run_id": ctx.run_id,
                    "conversation_id": ctx.scope.conversation_id,
                },
            )
            await tx.write(SCOPES, identifier, "Scope", ctx.scope.wire())
            for record in prepared.references:
                validate_contract("ReferenceRecord", record)
                source = from_wire(Ref, record["ref"])
                key = reference_id(source, ctx)
                try:
                    current = await tx.load(REFERENCES, key)
                except StoreMissing:
                    await tx.write(REFERENCES, key, "ReferenceRecord", record)
                else:
                    # First retrieved_at is immutable; subsequent snapshots reuse it.
                    comparable = {
                        name: value for name, value in record.items() if name != "retrieved_at"
                    }
                    previous = {
                        name: value
                        for name, value in current.payload.items()
                        if name != "retrieved_at"
                    }
                    if current.schema_name != "ReferenceRecord" or previous != comparable:
                        raise reject("reference_conflict", "Read source registration changed", 409)
            await verify()
            return {"ref": pin}

        result = await self.transactions.execute(
            ctx.principal,
            aggregate,
            RequestMeta(request_id=ctx.operation_id, schema_version="0.1"),
            parameters,
            write,
            verify=verify,
        )
        # Replays cannot return deleted snapshots or cross-scope cached data.
        return await self.load_snapshot(from_wire(Ref, result["ref"]), ctx)

    async def load_snapshot(self, ref: Ref, ctx: TrustedExecutionContext) -> dict[str, Any]:
        if ref.kind != "context" or ref.version != "1" or ref.location is not None:
            raise reject("snapshot_reference_invalid", "Expected immutable Context revision 1")
        binding = (await self.records.get(ctx.principal, BINDINGS, ref.id)).payload
        saved_scope = (await self.records.get(ctx.principal, SCOPES, ref.id)).payload
        if (
            binding["run_id"] != ctx.run_id
            or binding["conversation_id"] != ctx.scope.conversation_id
            or saved_scope != ctx.scope.wire()
        ):
            raise reject("permission_denied", "Snapshot is outside its bound Run/scope", 403)
        stored = await self.records.get(ctx.principal, SNAPSHOTS, ref.id, revision=1)
        snapshot = stored.payload
        validate_contract("ContextSnapshot", snapshot)
        if (
            stored.revision != 1
            or stored.schema_name != "ContextSnapshot"
            or snapshot["id"] != ref.id
            or snapshot["manifest"]["content_hash"] != snapshot_hash(snapshot)
            or not matches_pin(ref, from_wire(Ref, binding["snapshot_ref"]))
            or binding["snapshot_ref"].get("content_hash") != digest(snapshot)
        ):
            raise reject("snapshot_changed", "Snapshot or its fixed binding changed", 410)
        return snapshot

    async def instructions(
        self, snapshot: dict[str, Any], ctx: TrustedExecutionContext
    ) -> dict[str, Any]:
        ref = from_wire(Ref, snapshot["instruction_set_ref"])
        if (
            ref.kind != "rule"
            or ref.id != snapshot["id"]
            or ref.version != "1"
            or ref.location is not None
        ):
            raise reject("snapshot_changed", "Instruction binding is invalid", 410)
        saved = await self.records.get(ctx.principal, INSTRUCTIONS, ref.id, revision=1)
        validate_contract("InstructionSet", saved.payload)
        if saved.schema_name != "InstructionSet" or ref.content_hash != digest(saved.payload):
            raise reject("snapshot_changed", "Fixed instruction set changed", 410)
        return saved.payload

    async def reference(self, ref: Ref, ctx: TrustedExecutionContext) -> dict[str, Any]:
        saved = await self.records.get(
            ctx.principal, REFERENCES, reference_id(ref, ctx), revision=1
        )
        record = saved.payload
        validate_contract("ReferenceRecord", record)
        if (
            saved.schema_name != "ReferenceRecord"
            or record["access_scope"] != ctx.scope.wire()
            or not matches_pin(ref, from_wire(Ref, record["ref"]))
            or record["ref"] != record["content_ref"]
        ):
            raise reject("permission_denied", "Reference is outside its registered read scope", 403)
        return record

    async def request(self, identifier: str, ctx: TrustedExecutionContext) -> dict[str, Any]:
        saved = await self.records.get(ctx.principal, REQUESTS, identifier, revision=1)
        validate_contract("ContextRequest", saved.payload)
        if saved.schema_name != "ContextRequest":
            raise reject("snapshot_changed", "Snapshot request binding changed", 410)
        return saved.payload
