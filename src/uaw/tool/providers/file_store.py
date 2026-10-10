"""File evidence persistence; bridge owns real source/current authority, never resend."""

import hashlib
from typing import cast

from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.db.transactions import RecordTransaction, reference
from uaw.shared.contracts import JsonObject, Location, Principal, Ref, TrustedExecutionContext
from uaw.shared.stores import BlobStorePort
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.errors import fail, validate_dependency
from uaw.tool.ledger import ToolLedger, action_key, immutable
from uaw.tool.ports import ToolOutputVerifierPort, ToolRecoveryAccessPort
from uaw.tool.providers.file_read import (
    MAX_FILE_ENVELOPE_BYTES,
    MAX_RETURN_BYTES,
    FileReadEvidence,
    ToolFileReadBridgePort,
    file_arguments,
    freeze_file_evidence,
    verify_file_evidence,
)
from uaw.tool.receipt_store import ToolReceiptStore
from uaw.tool.schema import canonical
from uaw.workspace.ports import SignaturePort


class FileReceiptStore(ToolReceiptStore):
    """Original signed file observation, separately pinned from normalized ToolResult.

    All bridge/blob/signature calls occur outside ledger transactions. Local CAS
    replay never authorizes sending. Recovery requires current independent data
    authority AND the original bridge registration/journal/snapshot.
    """

    transport_status = "verified_runner_file_read"

    def __init__(
        self,
        ledger: ToolLedger,
        blobs: BlobStorePort,
        *,
        provider_ref: Ref,
        provider: Principal,
        access: ToolRecoveryAccessPort | None = None,
        verifier: ToolOutputVerifierPort | None = None,
        bridge: ToolFileReadBridgePort | None = None,
        signatures: SignaturePort | None = None,
    ) -> None:
        super().__init__(
            ledger,
            blobs,
            provider_ref=provider_ref,
            provider=provider,
            access=access,
            verifier=verifier,
        )
        self.bridge, self.signatures = bridge, signatures

    def ready(self) -> None:
        if self.bridge is None or self.signatures is None:
            raise fail(
                "dependency_unavailable",
                "Actual file bridge/signature source is not wired",
                phase="file_source",
                category="dependency",
                status=503,
            )
        self.bridge.ready()

    def data_bytes(self, data: JsonObject) -> bytes:
        validate_dependency("FileContent", data, "file_source")
        if len(cast(str, data["text"]).encode("utf-8")) > MAX_RETURN_BYTES:
            raise ValueError("Actual FileContent exceeds UTF-8 byte limit")
        return canonical(data, max_bytes=MAX_FILE_ENVELOPE_BYTES)

    async def binding(self, ctx: TrustedExecutionContext) -> tuple[JsonObject, JsonObject]:
        self.ready()
        return await super().binding(ctx)

    @staticmethod
    def observation_ref(evidence: FileReadEvidence, ctx: TrustedExecutionContext) -> Ref:
        """Pin the original observation; this hash helper never grants data access."""
        return Ref(
            kind="content",
            id="file-observation-" + ctx.attempt_id,
            version="1",
            content_hash=hashlib.sha256(
                canonical(
                    {
                        "command_ref": evidence.command_ref.wire(),
                        "receipt_ref": evidence.receipt_ref.wire(),
                        "owner": evidence.source.owner.wire(),
                        "device": evidence.source.device_id,
                        "snapshot": hashlib.sha256(evidence.snapshot).hexdigest(),
                        "selection": evidence.selection,
                    }
                )
            ).hexdigest(),
        )

    async def record(self, evidence: FileReadEvidence, ctx: TrustedExecutionContext) -> JsonObject:
        evidence = freeze_file_evidence(evidence)
        call, spec = await self.binding(ctx)
        assert self.signatures is not None
        data = verify_file_evidence(evidence, call, spec, ctx, self.provider_ref, self.signatures)
        # One immutable pin binds the complete original observation. Every recovery
        # still rechecks bridge data authority, real signatures and actual bytes;
        # a matched pin avoids rewriting all named rows/blobs during each Reader call.
        proof = self.observation_ref(evidence, ctx)
        previous = await self.ledger.get("tool.file.observation.refs", ctx.attempt_id, ctx)
        if previous is not None:
            if previous != proof.wire():
                raise fail(
                    "receipt_binding_conflict",
                    "Original file observation changed",
                    phase="file_source",
                    category="conflict",
                    status=409,
                )
            return data
        snapshot_hash = await self.blobs.put(ctx.principal, evidence.snapshot)
        if snapshot_hash != hashlib.sha256(evidence.snapshot).hexdigest():
            raise ValueError("Original snapshot blob digest mismatch")
        fragment = cast(str, data["text"]).encode("utf-8")
        fragment_hash = await self.blobs.put(ctx.principal, fragment)
        if fragment_hash != hashlib.sha256(fragment).hexdigest():
            raise ValueError("Actual fragment blob digest mismatch")
        await self.binding(ctx)
        records = (
            ("tool.file.command.refs", "Ref", evidence.command_ref.wire()),
            ("tool.file.commands", "RunnerCommand", evidence.source.command.wire()),
            ("tool.file.owners", "Principal", evidence.source.owner.wire()),
            ("tool.file.receipt.refs", "Ref", evidence.receipt_ref.wire()),
            ("tool.file.runner.receipts", "RunnerReceipt", evidence.receipt.wire()),
            (
                "tool.file.snapshot.refs",
                "Ref",
                Ref(
                    kind="content",
                    id="file-snapshot-" + ctx.attempt_id,
                    version="1",
                    content_hash=snapshot_hash,
                ).wire(),
            ),
            ("tool.file.selections", "Location", evidence.selection),
            (
                "tool.file.fragment.refs",
                "Ref",
                Ref(
                    kind="content",
                    id="file-fragment-" + ctx.attempt_id,
                    version="1",
                    content_hash=fragment_hash,
                    location=Location.model_validate(evidence.selection),
                ).wire(),
            ),
            ("tool.file.contents", "FileContent", data),
            ("tool.file.observation.refs", "Ref", proof.wire()),
        )

        async def write(tx: RecordTransaction) -> JsonObject:
            for namespace, schema, value in records:
                await immutable(tx, namespace, ctx.attempt_id, schema, value)
            return data

        await self.ledger.transactions.inspect(ctx.principal, self.ledger.aggregate(ctx), write)
        return data

    async def original(self, ctx: TrustedExecutionContext) -> FileReadEvidence | None:
        call, spec = await self.binding(ctx)
        assert self.bridge is not None
        evidence = await self.bridge.recover(call, spec, ctx)
        if evidence is None:
            return None
        evidence = freeze_file_evidence(evidence)
        await self.record(evidence, ctx)
        await self.binding(ctx)
        return evidence

    async def provider_receipt(self, ctx: TrustedExecutionContext) -> JsonObject | None:
        # Even an already saved response must retain its current source permission.
        actual = await super().provider_receipt(ctx)
        if actual is not None:
            # This is the fixed transport/accounting observation, not file content
            # verification. verified/read/check/publish always invoke the owning
            # verifier, which re-reads the actual bridge journal and signatures.
            return actual
        evidence = await self.original(ctx)
        if evidence is None:
            return None
        assert evidence.receipt.payload is not None
        data = cast(JsonObject, evidence.receipt.payload["result"])  # record verified payload
        saved = await self.save_response(
            data, evidence.receipt.usage, ctx, authenticated_provider=self.provider
        )
        return saved

    async def read_observation(
        self, action_id: str, ctx: TrustedExecutionContext
    ) -> FileReadEvidence:
        """Current authorized, original signed source for Artifact/Verification wiring.

        Returns internal evidence, never a new command, snapshot or public DTO.
        Access to SQL rows/Refs alone is insufficient to consume these file bytes.
        """
        call, _ = await self.binding(ctx)
        if action_id != call["action_id"]:
            raise fail(
                "receipt_binding_conflict",
                "Observation action differs from original",
                phase="file_source",
                category="conflict",
                status=409,
            )
        evidence = await self.original(ctx)
        if evidence is None:
            raise fail(
                "dependency_unavailable",
                "Original file journal is not available",
                phase="file_source",
                category="dependency",
                status=503,
            )
        return evidence

    async def read_raw(self, ref: Ref, ctx: TrustedExecutionContext) -> JsonObject:
        data = await super().read_raw(ref, ctx)
        if self.verifier is None:
            raise fail(
                "dependency_unavailable",
                "Actual file verifier is not wired",
                phase="file_source",
                category="dependency",
                status=503,
            )
        call, spec = await self.binding(ctx)
        before = (self.data_bytes(data), canonical(call), canonical(spec))
        await self.verifier.verify(data, call, spec, ctx)
        if before != (self.data_bytes(data), canonical(call), canonical(spec)):
            raise ValueError("File verifier changed fixed raw observation")
        await self.binding(ctx)
        return data

    async def find(self, action_id: str, ctx: TrustedExecutionContext) -> Ref | None:
        call, _ = await self.binding(ctx)
        if action_id != call["action_id"]:
            raise fail(
                "receipt_binding_conflict",
                "Lookup differs from original file action",
                phase="file_source",
                category="conflict",
                status=409,
            )
        actual = await self.provider_receipt(ctx)
        if actual is not None:
            await self.publish(actual, ctx, authenticated_provider=self.provider)
        return await super().find(action_id, ctx)


class FileReadVerifier:
    def __init__(self, source: FileReceiptStore) -> None:
        self.source = source

    async def verify(
        self, data: JsonObject, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> None:
        file_arguments(call, spec, self.source.provider_ref)
        fixed_call, fixed_spec = await self.source.binding(ctx)
        if call != fixed_call or spec != fixed_spec:
            raise ValueError("Original file call/spec changed")
        evidence = await self.source.original(ctx)
        if evidence is None:
            raise fail(
                "dependency_unavailable",
                "No original file evidence Reader",
                phase="file_verify",
                category="dependency",
                status=503,
            )
        assert self.source.signatures is not None
        actual = verify_file_evidence(
            evidence, call, spec, ctx, self.source.provider_ref, self.source.signatures
        )
        if self.source.data_bytes(data) != self.source.data_bytes(actual):
            raise ValueError("Raw file content differs from original signed observation")


class FileReadExecutor:
    def __init__(self, source: FileReceiptStore, *, provider: Principal) -> None:
        source.authenticate(provider)
        self.source, self.provider = source, provider

    def check(self, call: JsonObject, spec: JsonObject) -> None:
        self.source.ready()
        file_arguments(call, spec, self.source.provider_ref)

    async def execute(
        self, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> JsonObject:
        self.check(call, spec)
        fixed_call, fixed_spec = await self.source.binding(ctx)
        if call != fixed_call or spec != fixed_spec:
            raise ValueError("File dispatch differs from original attempt")
        assert self.source.bridge is not None
        evidence = freeze_file_evidence(await self.source.bridge.execute(call, spec, ctx))
        data = await self.source.record(evidence, ctx)
        return await self.source.save_response(
            data, evidence.receipt.usage, ctx, authenticated_provider=self.provider
        )


class FileResourceReader:
    def __init__(self, provider_ref: Ref, bridge: ToolFileReadBridgePort | None = None) -> None:
        self.provider_ref, self.bridge = provider_ref, bridge

    async def resolve(
        self, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> tuple[Ref, ...]:
        file_arguments(call, spec, self.provider_ref)
        if self.bridge is None:
            raise fail(
                "dependency_unavailable",
                "Actual current file resource Reader is not wired",
                phase="file_resource",
                category="dependency",
                status=503,
            )
        self.bridge.ready()
        refs = await self.bridge.resolve(call, spec, ctx)
        workspace = Ref.model_validate(cast(JsonObject, call["arguments"])["workspace_ref"])
        if workspace not in refs or any(ref not in ctx.scope.resource_refs for ref in refs):
            raise fail(
                "resource_scope_denied",
                "Actual file workspace/source is outside current scope",
                phase="file_resource",
                category="authorization",
                status=403,
            )
        return refs


async def recover_file_accounting(
    ledger: ToolLedger, budgets: ToolBudgetAdapter, ctx: TrustedExecutionContext
) -> JsonObject:
    """Replay ONLY an already accepted file observation's existing accounting plan.

    Current BudgetStatePort/BudgetPort authorize accounting. Does not read file
    content, old grants, bridge or signatures, and returns only UsageSettlement.
    No new source observation, bill revision, admission, reserve or send is created.
    Missing fixed plan is unavailable, not a fabricated zero-cost settlement.
    """
    if budgets.ledger is not ledger:
        raise ValueError("Accounting recovery must share the original Tool ledger")
    call = await ledger.attempt(ctx)
    _, spec, _ = await ledger.action(str(call["action_id"]), ctx)
    file_arguments(call, spec, Ref.model_validate(spec["provider_ref"]))
    await budgets.get_ledger(ctx)  # Current accounting authority; NOT a data/read/send grant.
    active = await ledger.get("tool.reconciliation.active", ctx.attempt_id, ctx)
    if active is None:
        raise fail(
            "dependency_unavailable",
            "No original accepted file accounting observation",
            phase="file_accounting",
            category="dependency",
            status=503,
        )
    validate_dependency("ToolReconciliationReceipt", active, "file_accounting")
    key = ledger.receipt_key(active)
    accepted = await ledger.get("tool.reconciliation.receipts", key, ctx)
    effect = await ledger.effect_from_attempt(ctx)
    intent = await ledger.get("tool.dispatch.intents", action_key(ctx, str(call["action_id"])), ctx)
    if (
        accepted != active
        or active["attempt_id"] != ctx.attempt_id
        or active["usage"]["attempt_id"] != ctx.attempt_id
        or active["action_ref"] != reference("tool_call", action_key(ctx, str(call["action_id"])))
        or active["provider_ref"] != spec["provider_ref"]
        or effect.get("receipt_ref") != active["receipt_ref"]
        or effect["attempt_ids"] != [ctx.attempt_id]
        or intent is None
        or intent["provider_binding_ref"] != spec["provider_ref"]
    ):
        raise fail(
            "receipt_binding_conflict",
            "Original file accounting binding changed",
            phase="file_accounting",
            category="conflict",
            status=409,
        )
    saved = await ledger.get("tool.reconciliation.settled", key, ctx)
    if saved is not None:
        validate_dependency("UsageSettlement", saved, "file_accounting")
        return saved
    plans = []
    for index in range(4):
        plan_key = "reconcile-plan-" + parameter_hash({"receipt": key, "index": index})
        plan = await ledger.get("tool.reconciliation.budget.plans", plan_key, ctx)
        if plan is not None:
            validate_dependency("BudgetSettleRequest", plan, "file_accounting")
            if plan["usage"] != active["usage"]:
                raise fail(
                    "receipt_binding_conflict",
                    "Fixed file fee Usage differs",
                    phase="file_accounting",
                    category="conflict",
                    status=409,
                )
            plans.append(plan)
    if not plans:
        raise fail(
            "dependency_unavailable",
            "Original file accounting plan is not persisted",
            phase="file_accounting",
            category="dependency",
            status=503,
        )
    # The owning service's existing bounded CAS recovery replays fixed request IDs.
    # No Tool transaction is held around accounting IO.
    settlement = await budgets.settle_receipt(active, key, ctx)
    await ledger.finish_reconciliation(active, settlement, ctx)
    return settlement
