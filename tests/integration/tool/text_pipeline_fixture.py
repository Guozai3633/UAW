"""Actual text adapter/SQL/blob with controlled role and recovery data authority.

Only access/metadata are controlled. Calculations and persistence use real code;
no LLM, external provider, Runner, IPC or product capability is represented.
"""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from tests.integration.tool.conftest import ControlledRoleEnvironment
from uaw.infrastructure.blob.filesystem import FSBlobStore
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
from uaw.tool.providers.text import TextInspectExecutor, text_estimates, text_spec
from uaw.tool.receipt_store import ToolResponseStore
from uaw.tool.registry import AdapterBinding, ToolRegistry


class ControlledTextRole(ControlledRoleEnvironment):
    def __init__(self):
        self.allowed = True

    async def snapshot(self, ctx):
        if not self.allowed:
            raise reject("role_revoked", "Controlled text role revoked", 403, "authorization")
        return replace(await super().snapshot(ctx), role_categories=frozenset({"text"}))


class ControlledRecoveryAuthority:
    def __init__(self, case, provider):
        self.case, self.provider, self.allowed = case, provider, True

    async def check(self, call, spec, ctx, *, provider):
        if not self.allowed or ctx != self.case.ctx or provider != self.provider:
            raise reject(
                "result_source_revoked",
                "Current recovery data identity/access denied",
                403,
                "authorization",
            )
        run = (await self.case.ledger.store.get(ctx.principal, "runs", ctx.run_id)).payload
        if run["conversation_id"] != ctx.conversation_id or run["task_id"] != ctx.task_id:
            raise reject("result_scope_denied", "Actual owned Run changed", 403, "authorization")
        binding = (
            await self.case.ledger.store.get(ctx.principal, "run.bindings", ctx.run_id)
        ).payload
        if binding["model_policy_ref"] != ctx.model_policy_ref.wire():
            raise reject("result_scope_denied", "Original user model changed", 403, "authorization")
        # Uses actual current source record/version, not old approval as data access.
        await self.case.reader.resolve(call, spec, ctx)


class CountingTextExecutor(TextInspectExecutor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calls = 0

    async def execute(self, *args):
        self.calls += 1
        return await super().execute(*args)


class StageResponseOnly:
    """First two milestones deliberately lack normalized ToolResult, no fake ok."""

    def __init__(self, source):
        self.source = source

    async def resume(self, call, ctx):
        receipt = await self.source.provider_receipt(ctx)
        if receipt is not None:
            await self.source.read_raw(Ref.model_validate(receipt["raw_result_ref"]), ctx)
        raise reject(
            "dependency_unavailable", "Stage normalization not yet wired", 503, "dependency"
        )


@pytest.fixture
async def text_pipeline(tool_case, tmp_path):
    c = tool_case
    ctx = c.ctx.model_copy(update={"attempt_id": "text-attempt", "trace_id": "text-trace"})
    spec = text_spec(Ref.model_validate(c.spec["provider_ref"]))
    registry = ToolRegistry()
    registry.register(
        spec,
        expected_revision=0,
        binding=AdapterBinding(
            Ref.model_validate(spec["provider_ref"]),
            frozenset({"sql-component-test"}),
            implemented=True,
        ),
    )
    raw = {
        "tool_ref": registry.reference(registry.snapshot()[1][0]),
        "action_id": "text-action",
        "arguments": {"text": "  实际文本\r\nKeep\u0301 exact  "},
    }
    call = normalize(raw, registry)
    role = ControlledTextRole()
    authority = ToolApprovalAuthority(
        c.ledger,
        registry,
        c.domain[0],
        role,
        c.reader,
        policies=ExecutionPolicyResolver(c.ledger.store),
    )
    service = ApprovalService(c.ledger.store, c.domain[0], authority)
    approvals = ToolApprovalAdapter(c.ledger, authority, service)
    budget = ToolBudgetAdapter(
        c.ledger, BudgetService(c.ledger.store), approvals, state=BudgetService(c.ledger.store)
    )
    c = replace(
        c,
        registry=registry,
        authority=authority,
        service=service,
        approvals=approvals,
        budget=budget,
        ctx=ctx,
        call=call,
        spec=spec,
    )
    provider = Principal(
        id="internal-text-service", kind="service", auth_session_id="text-provider-session"
    )
    recovery = ControlledRecoveryAuthority(c, provider)
    blob = FSBlobStore(tmp_path / "text-blobs")
    source = ToolResponseStore(
        c.ledger,
        blob,
        provider_ref=Ref.model_validate(spec["provider_ref"]),
        provider=provider,
        access=recovery,
    )
    executor = CountingTextExecutor(source, provider=provider)
    invocation = ToolInvocation(
        registry,
        c.ledger,
        budget,
        approvals,
        access=role,
        executor=executor,
        estimates=text_estimates(),
        prepare=executor.check,
        results=StageResponseOnly(source),
    )
    facade = ToolFacade(registry, invocation=invocation)
    return SimpleNamespace(
        case=c,
        facade=facade,
        source=source,
        executor=executor,
        invocation=invocation,
        raw=raw,
        provider=provider,
        recovery=recovery,
        role=role,
        blob=blob,
    )
