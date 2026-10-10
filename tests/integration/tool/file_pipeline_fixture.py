"""Actual Windows handle/Ed25519/PostgreSQL; explicitly controlled control port.

No native confirmation, production IPC/Runner dispatch, product flags or LLM claim.
The independent SQL command/journal uses named existing contracts; recovery never
opens the temporary file. Pager/current root/provider authority are test components.
"""

import asyncio
import hashlib
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.integration.test_control_plane import meta
from tests.integration.tool.conftest import ControlledRoleEnvironment
from tests.integration.tool.text_pipeline_fixture import ControlledRecoveryAuthority
from tests.unit.tool.file_evidence_fixture import (
    ControlledKeyDirectorySignatures,
    make_evidence,
    resign_evidence,
)
from uaw.infrastructure.blob.filesystem import FSBlobStore
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import reference
from uaw.run.approval import ApprovalService
from uaw.run.budget import BudgetService
from uaw.run.permissions import ExecutionPolicyResolver
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import reject
from uaw.tool.approval import ToolApprovalAdapter
from uaw.tool.authority import ToolApprovalAuthority
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.facade import ToolFacade
from uaw.tool.invocation.dispatch import ToolInvocation
from uaw.tool.invocation.schema import normalize
from uaw.tool.ledger import ToolLedger, action_key, immutable
from uaw.tool.providers.file_read import (
    FileReadEvidence,
    file_estimates,
    file_read_spec,
    select_text,
)
from uaw.tool.providers.file_store import (
    FileReadExecutor,
    FileReadVerifier,
    FileReceiptStore,
    FileResourceReader,
)
from uaw.tool.providers.multiplex import ToolExecutorBinding, ToolExecutorRouter
from uaw.tool.reconciliation import ToolReconciler
from uaw.tool.registry import AdapterBinding, ToolRegistry
from uaw.tool.results import ToolResults
from uaw.tool.schema import canonical, digest
from uaw.workspace.contracts import RegisteredReceiptCommand, RunnerCommand, RunnerReceipt
from uaw.workspace.ports import RootGrant


class ControlledFileConfiguration:
    """Only file flag decision is controlled; actual fixed/current SQL metadata retained.

    No SQL feature flag is opened. A's production scoped flag port must replace this.
    """

    def __init__(self, actual, ctx):
        self.actual, self.ctx, self.allowed = actual, ctx, True

    def __getattr__(self, name):
        return getattr(self.actual, name)

    async def require_capability(self, capability, fixed_ref, scope, **kwargs):
        if capability != "file_access" or not self.allowed or scope != self.ctx.scope.wire():
            raise reject("feature_disabled", "Controlled scoped flag denied", 403, "permission")
        await self.actual.snapshot(fixed_ref)
        await self.actual.current()


class ControlledFileRole(ControlledRoleEnvironment):
    def __init__(self):
        self.allowed = True

    async def snapshot(self, ctx):
        if not self.allowed:
            raise reject("role_revoked", "Controlled role revoked", 403, "authorization")
        return replace(
            await super().snapshot(ctx),
            role_categories=frozenset({"file"}),
            enabled_flags=frozenset({"file_access"}),
        )


class ControlledFileBridge:
    """Independent registered SQL journal + actual native file read, controlled routing.

    Every original command/receipt is signed with actual Ed25519. No production
    command control endpoint, native human confirmation or IPC is simulated as real.
    """

    def __init__(self, case, provider, blob, signatures, *, root=None):
        self.case, self.provider, self.blob, self.signatures = case, provider, blob, signatures
        self.root = root
        self.calls, self.opens = 0, 0
        self.allowed = True
        self.page_size = None
        self.transform = None
        self.after_journal = None
        self.data_authority = ControlledRecoveryAuthority(case, provider)

    def ready(self):
        if self.signatures is None:
            raise reject(
                "dependency_unavailable", "Controlled key source absent", 503, "dependency"
            )

    async def check(self, call, spec, ctx, *, provider):
        if not self.allowed or provider != self.provider:
            raise reject(
                "root_revoked", "Controlled current root/device revoked", 403, "authorization"
            )
        await self.data_authority.check(call, spec, ctx, provider=provider)
        if call["arguments"]["workspace_ref"] != self.case.ctx.scope.resource_refs[-1].wire():
            raise reject(
                "workspace_denied", "Exact controlled workspace required", 403, "authorization"
            )

    async def resolve(self, call, spec, ctx):
        await self.check(call, spec, ctx, provider=self.provider)
        if "cursor" in call["arguments"]:
            await self.cursor(call["arguments"]["cursor"], call, spec, ctx)
        return tuple(ctx.scope.resource_refs)

    async def put_records(self, records, ctx):
        async def write(tx):
            for namespace, key, schema, value in records:
                await immutable(tx, namespace, key, schema, value)
            return {}

        await self.case.ledger.transactions.inspect(ctx.principal, "controlled-file-control", write)

    async def cursor(self, cursor, call, spec, ctx):
        request = await self.case.ledger.get("tool.test.file.cursor.requests", cursor, ctx)
        owner = await self.case.ledger.get("tool.test.file.cursor.owners", cursor, ctx)
        provider = await self.case.ledger.get("tool.test.file.cursor.providers", cursor, ctx)
        original = {k: v for k, v in call["arguments"].items() if k != "cursor"}
        if request != original or owner != ctx.principal.wire() or provider != spec["provider_ref"]:
            raise reject(
                "cursor_denied",
                "Cursor is outside original file/owner/provider",
                403,
                "authorization",
            )
        snapshot = await self.case.ledger.get("tool.test.file.cursor.snapshots", cursor, ctx)
        selection = await self.case.ledger.get("tool.test.file.cursor.selections", cursor, ctx)
        assert snapshot is not None and selection is not None
        return snapshot, selection

    def read_snapshot(self, call, ctx):
        runner_path = str(Path(__file__).parents[3] / "apps" / "local_runner")
        if runner_path not in sys.path:
            sys.path.insert(0, runner_path)
        from uaw_runner.handle_read import WindowsReadHandle

        assert self.root is not None
        stat = self.root.stat()
        grant = RootGrant(
            ctx.principal.id,
            "controlled-device",
            "controlled-root",
            ctx.scope.resource_refs[-1],
            self.root,
            (stat.st_dev, stat.st_ino),
            frozenset({"read"}),
            owner=ctx.principal,
        )
        handle = WindowsReadHandle(grant, call["arguments"]["path"])
        self.opens += 1
        try:
            # The accepted handle enforces actual root identity/regular file/UTF-8/limits.
            data = handle.read({**call["arguments"], "location": {"kind": "whole"}})
            return data["text"].encode("utf-8")
        finally:
            handle.close()

    async def execute(self, call, spec, ctx):
        self.calls += 1
        await self.check(call, spec, ctx, provider=self.provider)
        command = RunnerCommand.model_validate_json(
            canonical(
                self.signatures.signed(
                    {
                        "command_id": "file-command-" + ctx.attempt_id,
                        "operation_id": ctx.operation_id,
                        "request_ref": {
                            "kind": "tool_call",
                            "id": action_key(ctx, call["action_id"]),
                            "version": "1",
                            "content_hash": digest(call),
                        },
                        "trusted_context": ctx.wire(),
                        "fencing_token": 1,
                        "expires_at": ctx.deadline,
                        "parameters": {"action": "file.read", "parameters": call["arguments"]},
                    },
                    "command",
                )
            )
        )
        # Independent command registration precedes native read (the controlled send).
        await self.put_records(
            [("tool.test.file.commands", ctx.attempt_id, "RunnerCommand", command.wire())], ctx
        )
        snapshot = await asyncio.to_thread(self.read_snapshot, call, ctx)
        text = snapshot.decode("utf-8")
        _, _, _, evidence, _ = make_evidence(
            ctx,
            text=text,
            arguments=call["arguments"],
            signatures=self.signatures,
            provider_ref=Ref.model_validate(spec["provider_ref"]),
            call=call,
        )
        assert evidence.source.command.wire() == command.wire()
        selection = call["arguments"].get("location", {"kind": "whole"})
        start = 0
        if "cursor" in call["arguments"]:
            original, selection = await self.cursor(call["arguments"]["cursor"], call, spec, ctx)
            if original["content_hash"] != hashlib.sha256(snapshot).hexdigest():
                raise reject(
                    "cursor_stale", "Actual file changed from original cursor snapshot", 412
                )
            start = selection["start"]
        next_cursor = None
        if self.page_size is not None:
            assert call["arguments"].get("location", {"kind": "whole"}) == {"kind": "whole"}
            end = min(start + self.page_size, len(text))
            selection = {"kind": "text_span", "start": start, "end": end}
            if end < len(text):
                next_cursor = "controlled-cursor-" + digest(
                    {"call": call, "hash": hashlib.sha256(snapshot).hexdigest(), "end": end}
                )
                original_args = {k: v for k, v in call["arguments"].items() if k != "cursor"}
                snapshot_ref = Ref(
                    kind="content",
                    id="cursor-snapshot-" + ctx.attempt_id,
                    version="1",
                    content_hash=await self.blob.put(ctx.principal, snapshot),
                )
                await self.put_records(
                    [
                        (
                            "tool.test.file.cursor.requests",
                            next_cursor,
                            "ToolFileReadInput",
                            original_args,
                        ),
                        (
                            "tool.test.file.cursor.owners",
                            next_cursor,
                            "Principal",
                            ctx.principal.wire(),
                        ),
                        (
                            "tool.test.file.cursor.providers",
                            next_cursor,
                            "Ref",
                            spec["provider_ref"],
                        ),
                        (
                            "tool.test.file.cursor.snapshots",
                            next_cursor,
                            "Ref",
                            snapshot_ref.wire(),
                        ),
                        (
                            "tool.test.file.cursor.selections",
                            next_cursor,
                            "Location",
                            {"kind": "text_span", "start": end, "end": len(text)},
                        ),
                    ],
                    ctx,
                )
        data = {
            **evidence.receipt.payload["result"],
            "text": select_text(text, selection),
            "location": selection,
        }
        if next_cursor is not None:
            data["next_cursor"] = next_cursor
        evidence = replace(
            resign_evidence(evidence, data, self.signatures),
            selection=selection,
            next_cursor=next_cursor,
        )
        if self.transform:
            evidence = self.transform(evidence)
        snapshot_ref = Ref(
            kind="content",
            id="control-snapshot-" + ctx.attempt_id,
            version="1",
            content_hash=await self.blob.put(ctx.principal, evidence.snapshot),
        )
        await self.put_records(
            [
                (
                    "tool.test.file.receipts",
                    ctx.attempt_id,
                    "RunnerReceipt",
                    evidence.receipt.wire(),
                ),
                ("tool.test.file.command.refs", ctx.attempt_id, "Ref", evidence.command_ref.wire()),
                ("tool.test.file.receipt.refs", ctx.attempt_id, "Ref", evidence.receipt_ref.wire()),
                ("tool.test.file.snapshots", ctx.attempt_id, "Ref", snapshot_ref.wire()),
                ("tool.test.file.selections", ctx.attempt_id, "Location", evidence.selection),
            ],
            ctx,
        )
        if self.after_journal:
            await self.after_journal()
        return evidence

    async def recover(self, call, spec, ctx):
        # CURRENT data authority; no new execution approval/cancel check, no OS reopen.
        await self.check(call, spec, ctx, provider=self.provider)
        receipt = await self.case.ledger.get("tool.test.file.receipts", ctx.attempt_id, ctx)
        if receipt is None:
            return None
        command = await self.case.ledger.get("tool.test.file.commands", ctx.attempt_id, ctx)
        command_ref = await self.case.ledger.get("tool.test.file.command.refs", ctx.attempt_id, ctx)
        receipt_ref = await self.case.ledger.get("tool.test.file.receipt.refs", ctx.attempt_id, ctx)
        snapshot = await self.case.ledger.get("tool.test.file.snapshots", ctx.attempt_id, ctx)
        selection = await self.case.ledger.get("tool.test.file.selections", ctx.attempt_id, ctx)
        actual = RunnerReceipt.model_validate(receipt)
        return FileReadEvidence(
            Ref.model_validate(command_ref),
            Ref.model_validate(receipt_ref),
            RegisteredReceiptCommand(
                RunnerCommand.model_validate_json(canonical(command)),
                "controlled-device",
                ctx.principal,
            ),
            actual,
            await self.blob.get(ctx.principal, snapshot["content_hash"]),
            selection,
            actual.payload["result"].get("next_cursor") if actual.payload else None,
        )


@pytest.fixture
async def file_pipeline(tool_case, tmp_path):
    c = tool_case
    workspace = Ref(kind="workspace", id="controlled-workspace-" + c.ctx.principal.id, version="1")
    refs = (*c.ctx.scope.resource_refs, workspace)
    policy = {
        "id": "file-sql-policy",
        "revision": 1,
        "allowed_capabilities": ["tool.invoke", "workspace.process"],
        "denied_capabilities": [],
        "resource_scope": {
            "conversation_id": c.ctx.conversation_id,
            "task_id": c.ctx.task_id,
            "resource_refs": [r.wire() for r in refs],
        },
        "network_allowlist": [],
        "feature_flag_refs": [],
    }
    await c.ledger.store.put(
        c.ctx.principal,
        "execution.policies",
        policy["id"],
        "CapabilityPolicy",
        policy,
        expected_revision=0,
        request_id="file-fixture-policy",
    )
    ctx = c.ctx.model_copy(
        update={
            "attempt_id": "file-attempt",
            "trace_id": "file-trace",
            "capability_policy_ref": Ref.model_validate(reference("policy", policy["id"])),
            "scope": c.ctx.scope.model_copy(
                update={"capabilities": ("tool.invoke", "workspace.process"), "resource_refs": refs}
            ),
        }
    )
    provider_ref = Ref.model_validate(c.spec["provider_ref"])
    spec = file_read_spec(provider_ref)
    registry = ToolRegistry()
    registry.register(
        spec,
        expected_revision=0,
        binding=AdapterBinding(provider_ref, frozenset({"sql-component-test"}), implemented=True),
    )
    raw = {
        "tool_ref": registry.reference(registry.snapshot()[1][0]),
        "action_id": "file-action",
        "arguments": {"workspace_ref": workspace.wire(), "path": "file.txt"},
    }
    c = replace(c, ctx=ctx, spec=spec, call=normalize(raw, registry), registry=registry)
    root = tmp_path / "authorized-test-root"
    root.mkdir()
    (root / "file.txt").write_bytes("  第一行́\r\nsecond😀\nlast  ".encode())
    provider = Principal(
        kind="service", id="controlled-file-service", auth_session_id="controlled-file-session"
    )
    signatures = ControlledKeyDirectorySignatures()
    blob = FSBlobStore(tmp_path / "file-blobs")
    bridge = ControlledFileBridge(c, provider, blob, signatures, root=root)
    role = ControlledFileRole()
    configuration = ControlledFileConfiguration(c.domain[0], ctx)
    resources = FileResourceReader(provider_ref, bridge)
    authority = ToolApprovalAuthority(
        c.ledger,
        registry,
        configuration,
        role,
        resources,
        policies=ExecutionPolicyResolver(c.ledger.store),
    )
    service = ApprovalService(c.ledger.store, configuration, authority)
    approvals = ToolApprovalAdapter(c.ledger, authority, service)
    budget_service = BudgetService(c.ledger.store)
    budget = ToolBudgetAdapter(c.ledger, budget_service, approvals, state=budget_service)
    c = replace(c, authority=authority, service=service, approvals=approvals, budget=budget)
    bridge.case = c
    bridge.data_authority.case = c
    source = FileReceiptStore(
        c.ledger,
        blob,
        provider_ref=provider_ref,
        provider=provider,
        access=bridge,
        bridge=bridge,
        signatures=signatures,
    )
    source.verifier = FileReadVerifier(source)
    executor = FileReadExecutor(source, provider=provider)
    router = ToolExecutorRouter(
        (
            ToolExecutorBinding(
                Ref.model_validate(raw["tool_ref"]), provider_ref, executor, executor.check
            ),
        )
    )
    reconciler = ToolReconciler(c.ledger, budget, receipts=source, evidence=source)
    results = ToolResults(source, reconciler)
    invocation = ToolInvocation(
        registry,
        c.ledger,
        budget,
        approvals,
        access=role,
        executor=router,
        estimates=file_estimates(money_ceiling="0.05"),
        prepare=router.check,
        results=results,
    )
    facade = ToolFacade(registry, invocation=invocation, lookup=source, reconciler=reconciler)
    return SimpleNamespace(
        case=c,
        raw=raw,
        root=root,
        bridge=bridge,
        source=source,
        signatures=signatures,
        provider=provider,
        blob=blob,
        role=role,
        configuration=configuration,
        resources=resources,
        executor=router,
        facade=facade,
        results=results,
        reconciler=reconciler,
        invocation=invocation,
    )


async def approve_file(p):
    waiting = await p.facade.invoke(p.raw, p.case.ctx)
    assert waiting["kind"] == "waiting", waiting
    actual = await p.case.service.get(p.case.ctx.principal, waiting["wait_ref"]["id"])
    await p.case.service.decide(
        p.case.ctx.principal,
        {
            "approval_id": actual["id"],
            "decision": {
                "decision": "approve_once",
                "expected_arguments_hash": actual["arguments_hash"],
                "expected_resource_refs": actual["resource_refs"],
                "reason": "Controlled SQL user approval; no native human confirmation claim",
            },
        },
        meta("file-fixture-approve-" + p.case.ctx.attempt_id, actual["revision"]),
    )
    return p


def recover_file(p):
    ledger = ToolLedger(PostgresRecordStore(p.case.ledger.store.database))
    case = replace(p.case, ledger=ledger)
    bridge = ControlledFileBridge(case, p.provider, p.blob, p.signatures)
    bridge.allowed = p.bridge.allowed
    bridge.data_authority.allowed = p.bridge.data_authority.allowed
    source = FileReceiptStore(
        ledger,
        p.blob,
        provider_ref=p.source.provider_ref,
        provider=p.provider,
        access=bridge,
        bridge=bridge,
        signatures=p.signatures,
    )
    source.verifier = FileReadVerifier(source)
    service = BudgetService(ledger.store)
    budget = ToolBudgetAdapter(ledger, service, state=service)
    reconciler = ToolReconciler(ledger, budget, receipts=source, evidence=source)
    results = ToolResults(source, reconciler)
    # No executor/approval/new execution role installed after restart.
    invocation = ToolInvocation(p.case.registry, ledger, budget, None, results=results)
    facade = ToolFacade(
        p.case.registry, invocation=invocation, lookup=source, reconciler=reconciler
    )
    return SimpleNamespace(
        case=case, source=source, bridge=bridge, budget=budget, results=results, facade=facade
    )
