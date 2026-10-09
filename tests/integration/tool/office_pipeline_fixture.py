"""Real office calculations/SQL/blob; provider metadata and current authority controlled.

No chat API, actual LLM choice, local OS/Runner capability or product registration.
"""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from tests.integration.tool.text_pipeline_fixture import (
    ControlledRecoveryAuthority,
    ControlledTextRole,
)
from uaw.infrastructure.blob.filesystem import FSBlobStore
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.run.approval import ApprovalService
from uaw.run.budget import BudgetService
from uaw.run.permissions import ExecutionPolicyResolver
from uaw.shared.contracts import Principal, Ref
from uaw.tool.approval import ToolApprovalAdapter
from uaw.tool.authority import ToolApprovalAuthority
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.facade import ToolFacade
from uaw.tool.invocation.dispatch import ToolInvocation
from uaw.tool.invocation.schema import normalize
from uaw.tool.ledger import ToolLedger
from uaw.tool.parameter_sources import PureParameterRecoveryAccess, PureParameterResourceReader
from uaw.tool.providers.arithmetic import ArithmeticExecutor, ArithmeticVerifier, arithmetic_spec
from uaw.tool.providers.json_data import JsonDataExecutor, JsonDataVerifier, json_data_spec
from uaw.tool.providers.local import local_estimates
from uaw.tool.providers.multiplex import (
    ToolExecutorBinding,
    ToolExecutorRouter,
    ToolOutputVerifierBinding,
    ToolOutputVerifierRouter,
)
from uaw.tool.providers.text import TextInspectExecutor, TextInspectVerifier, text_spec
from uaw.tool.receipt_store import ToolReceiptStore
from uaw.tool.reconciliation import ToolReconciler
from uaw.tool.registry import AdapterBinding, ToolRegistry
from uaw.tool.results import ToolResults

KINDS = ("arithmetic", "json", "text")
FACTORIES = (arithmetic_spec, json_data_spec, text_spec)
EXECUTORS = (ArithmeticExecutor, JsonDataExecutor, TextInspectExecutor)
VERIFIERS = (ArithmeticVerifier, JsonDataVerifier, TextInspectVerifier)
ARGUMENTS = (
    {"operation": "percent", "operands": ["1200.00", "7.5"]},
    {"text": ' {"amount":1200,"label":" exact 原 "}\r\n', "required_keys": ["amount", "missing"]},
    {"text": " 原text\r\nKeep exact "},
)


class ControlledOfficeRole(ControlledTextRole):
    async def snapshot(self, ctx):
        return replace(
            await super().snapshot(ctx), role_categories=frozenset({"arithmetic", "data", "text"})
        )


class CountingOfficeRouter(ToolExecutorRouter):
    def __init__(self, bindings):
        super().__init__(bindings)
        self.calls = 0

    async def execute(self, *args):
        self.calls += 1
        return await super().execute(*args)


def verifier_router(registry, provider_ref):
    bindings = []
    for entry, verifier in zip(registry.snapshot()[1], VERIFIERS, strict=True):
        bindings.append(
            ToolOutputVerifierBinding(
                Ref.model_validate(registry.reference(entry)), provider_ref, verifier(provider_ref)
            )
        )
    return ToolOutputVerifierRouter(tuple(bindings))


@pytest.fixture(params=KINDS)
async def office_pipeline(tool_case, tmp_path, request):
    c = tool_case
    kind = request.param
    index = KINDS.index(kind)
    ctx = c.ctx.model_copy(update={"attempt_id": kind + "-attempt", "trace_id": kind + "-trace"})
    provider_ref = Ref.model_validate(c.spec["provider_ref"])
    registry = ToolRegistry()
    for factory in FACTORIES:
        registry.register(
            factory(provider_ref),
            expected_revision=registry.revision,
            binding=AdapterBinding(
                provider_ref, frozenset({"sql-component-test"}), implemented=True
            ),
        )
    spec = FACTORIES[index](provider_ref)
    pins = tuple(Ref.model_validate(registry.reference(e)) for e in registry.snapshot()[1])
    raw = {
        "tool_ref": pins[index].wire(),
        "action_id": kind + "-action",
        "arguments": ARGUMENTS[index],
    }
    call = normalize(raw, registry)
    role = ControlledOfficeRole()
    resources = PureParameterResourceReader(registry, role, pins)
    authority = ToolApprovalAuthority(
        c.ledger,
        registry,
        c.domain[0],
        role,
        resources,
        policies=ExecutionPolicyResolver(c.ledger.store),
    )
    service = ApprovalService(c.ledger.store, c.domain[0], authority)
    approvals = ToolApprovalAdapter(c.ledger, authority, service)
    budget_service = BudgetService(c.ledger.store)
    budget = ToolBudgetAdapter(c.ledger, budget_service, approvals, state=budget_service)
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
        id="controlled-local-office-service",
        kind="service",
        auth_session_id="controlled-office-session",
    )
    # This authority reads actual owned SQL Run/model/input. Its role/provider decision is
    # explicitly controlled, not a production registration or self-reported ctx grant.
    current_data = ControlledRecoveryAuthority(c, provider)
    recovery = PureParameterRecoveryAccess(resources, c.ledger, authority=current_data)
    blob = FSBlobStore(tmp_path / "office-blobs")
    source = ToolReceiptStore(
        c.ledger,
        blob,
        provider_ref=provider_ref,
        provider=provider,
        access=recovery,
        verifier=verifier_router(registry, provider_ref),
    )
    implementations = tuple(factory(source, provider=provider) for factory in EXECUTORS)
    bindings = tuple(
        ToolExecutorBinding(pin, provider_ref, executor, executor.check)
        for pin, executor in zip(pins, implementations, strict=True)
    )
    executor = CountingOfficeRouter(bindings)
    reconciler = ToolReconciler(c.ledger, budget, receipts=source, evidence=source)
    results = ToolResults(source, reconciler)
    invocation = ToolInvocation(
        registry,
        c.ledger,
        budget,
        approvals,
        access=role,
        executor=executor,
        estimates=local_estimates(),
        prepare=executor.check,
        results=results,
    )
    facade = ToolFacade(registry, invocation=invocation, lookup=source, reconciler=reconciler)
    return SimpleNamespace(
        case=c,
        raw=raw,
        source=source,
        provider=provider,
        role=role,
        resources=resources,
        recovery=recovery,
        current_data=current_data,
        blob=blob,
        executor=executor,
        invocation=invocation,
        facade=facade,
        results=results,
        reconciler=reconciler,
        pins=pins,
        kind=kind,
    )


def recover_office(p, *, verifier=None, current_data=True):
    ledger = ToolLedger(PostgresRecordStore(p.case.ledger.store.database))
    service = BudgetService(ledger.store)
    budget = ToolBudgetAdapter(ledger, service, state=service)
    resources = PureParameterResourceReader(p.case.registry, None, p.pins)
    recovery = PureParameterRecoveryAccess(
        resources, ledger, authority=p.current_data if current_data else None
    )
    source = ToolReceiptStore(
        ledger,
        FSBlobStore(p.blob.directory),
        provider_ref=p.source.provider_ref,
        provider=p.provider,
        access=recovery,
        verifier=verifier or verifier_router(p.case.registry, p.source.provider_ref),
    )
    reconciler = ToolReconciler(ledger, budget, receipts=source, evidence=source)
    results = ToolResults(source, reconciler)
    invocation = ToolInvocation(p.case.registry, ledger, budget, None, results=results)
    facade = ToolFacade(
        p.case.registry, invocation=invocation, lookup=source, reconciler=reconciler
    )
    return SimpleNamespace(
        ledger=ledger,
        budget=budget,
        source=source,
        results=results,
        reconciler=reconciler,
        facade=facade,
        invocation=invocation,
    )


async def approve_office(p):
    from tests.integration.tool.conftest import approve

    first = await p.facade.invoke(p.raw, p.case.ctx)
    assert first["kind"] == "waiting" and p.executor.calls == 0
    await approve(p.case)
    return p
