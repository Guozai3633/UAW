"""Real SQL/office calculations/Windows read; explicitly controlled Agent access/bridge.

The file bridge and local provider metadata are test components, not native consent
or production installed-file sources. New facades are composed before routing.
"""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from tests.integration.tool.file_pipeline_fixture import ControlledFileBridge
from tests.integration.tool.file_pipeline_fixture import file_pipeline as file_pipeline
from tests.integration.tool.office_pipeline_fixture import office_pipeline as office_pipeline
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.run.budget import BudgetService
from uaw.shared.contracts import Ref
from uaw.shared.errors import reject
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.facade import ToolFacade
from uaw.tool.invocation.dispatch import ToolInvocation
from uaw.tool.ledger import ToolLedger
from uaw.tool.parameter_sources import PureParameterRecoveryAccess, PureParameterResourceReader
from uaw.tool.providers.file_store import FileReadVerifier, FileReceiptStore
from uaw.tool.receipt_store import ToolReceiptStore
from uaw.tool.reconciliation import ToolReconciler
from uaw.tool.registry import ToolRegistry
from uaw.tool.results import ToolResults
from uaw.tool.runtime_router import RoutedToolRuntime, ToolRuntimeRoute


class ControlledAgentAccess:
    """A-injection substitute only; effective Agent denial is narrower than Run role."""

    def __init__(self, office, file):
        self.pipelines = (office, file)
        self.denied = set()
        self.calls = 0

    async def snapshot(self, ctx):
        self.calls += 1
        selected = next((p for p in self.pipelines if p.case.ctx == ctx), None)
        if selected is None or ctx.attempt_id in self.denied:
            raise reject(
                "agent_tool_denied", "Controlled effective Agent access denied", 403, "permission"
            )
        current = await selected.role.snapshot(ctx)
        return replace(current, role_categories=frozenset({"arithmetic", "data", "text", "file"}))


def composed_facade(p, registry, ledger, access, *, source=None, budget=None):
    if source is None:
        results, reconciler = p.results, p.reconciler
        invocation = ToolInvocation(
            registry,
            ledger,
            p.case.budget,
            p.case.approvals,
            access=access,
            executor=p.executor,
            estimates=p.invocation.estimates,
            results=results,
            prepare=p.invocation.prepare,
        )
        source = p.source
    else:
        reconciler = ToolReconciler(ledger, budget, receipts=source, evidence=source)
        results = ToolResults(source, reconciler)
        # An effective Agent access is still injected; it grants no new sends.
        invocation = ToolInvocation(registry, ledger, budget, None, access=access, results=results)
    facade = ToolFacade(registry, invocation=invocation, lookup=source, reconciler=reconciler)
    return SimpleNamespace(facade=facade, results=results, source=source, budget=budget)


@pytest.fixture
async def mixed_runtime(file_pipeline, office_pipeline):
    file, office = file_pipeline, office_pipeline
    ledger = file.case.ledger
    assert ledger.store is office.case.ledger.store
    registry = ToolRegistry()
    for old in (office.case.registry, file.case.registry):
        for entry in old.snapshot()[1]:
            registry.register(
                entry.spec(), expected_revision=registry.revision, binding=entry.binding
            )
    access = ControlledAgentAccess(office, file)
    owners, routes = {}, []
    for p in (office, file):
        owner = composed_facade(p, registry, ledger, access)
        owners[p.kind if p is office else "file"] = owner
        routes.append(
            ToolRuntimeRoute(
                Ref.model_validate(p.raw["tool_ref"]),
                p.source.provider_ref,
                owner.facade,
                owner.results,
            )
        )
    runtime = RoutedToolRuntime(registry, ledger, tuple(routes), access=access)
    return SimpleNamespace(
        office=office,
        file=file,
        ledger=ledger,
        registry=registry,
        access=access,
        owners=owners,
        routes=tuple(routes),
        runtime=runtime,
    )


def recover_mixed(m):
    ledger = ToolLedger(PostgresRecordStore(m.ledger.store.database))
    service = BudgetService(ledger.store)
    budget = ToolBudgetAdapter(ledger, service, state=service)
    file = m.file
    bridge = ControlledFileBridge(
        replace(file.case, ledger=ledger), file.provider, file.blob, file.signatures
    )
    bridge.allowed = file.bridge.allowed
    bridge.data_authority.allowed = file.bridge.data_authority.allowed
    file_source = FileReceiptStore(
        ledger,
        file.blob,
        provider_ref=file.source.provider_ref,
        provider=file.provider,
        access=bridge,
        bridge=bridge,
        signatures=file.signatures,
    )
    file_source.verifier = FileReadVerifier(file_source)
    office = m.office
    resources = PureParameterResourceReader(m.registry, None, office.pins)
    recovery = PureParameterRecoveryAccess(resources, ledger, authority=office.current_data)
    office_source = ToolReceiptStore(
        ledger,
        office.blob,
        provider_ref=office.source.provider_ref,
        provider=office.provider,
        access=recovery,
        verifier=office.source.verifier,
    )
    owners, routes = {}, []
    for p, source in ((office, office_source), (file, file_source)):
        owner = composed_facade(p, m.registry, ledger, m.access, source=source, budget=budget)
        owners[p.kind if p is office else "file"] = owner
        routes.append(
            ToolRuntimeRoute(
                Ref.model_validate(p.raw["tool_ref"]),
                source.provider_ref,
                owner.facade,
                owner.results,
            )
        )
    return SimpleNamespace(
        runtime=RoutedToolRuntime(m.registry, ledger, tuple(routes), access=m.access),
        ledger=ledger,
        budget=budget,
        bridge=bridge,
        owners=owners,
    )
