"""Fresh process of actual office result recovery with controlled current data authority."""

import asyncio
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

from tests.integration.tool.conftest import ControlledSQLReader
from tests.integration.tool.office_pipeline_fixture import FACTORIES, verifier_router
from tests.integration.tool.text_pipeline_fixture import ControlledRecoveryAuthority
from uaw.infrastructure.blob.filesystem import FSBlobStore
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.session import Database
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.run.budget import BudgetService
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.facade import ToolFacade
from uaw.tool.invocation.dispatch import ToolInvocation
from uaw.tool.ledger import ToolLedger
from uaw.tool.parameter_sources import PureParameterRecoveryAccess, PureParameterResourceReader
from uaw.tool.receipt_store import ToolReceiptStore
from uaw.tool.reconciliation import ToolReconciler
from uaw.tool.registry import ToolRegistry
from uaw.tool.results import ToolResults


async def main():
    data = json.loads(sys.stdin.read())
    database = Database(os.environ["UAW_TEST_DATABASE_URL"])
    try:
        await database.check()
        ctx = TrustedExecutionContext.model_validate_json(json.dumps(data["context"]))
        ledger = ToolLedger(PostgresRecordStore(database))
        call = await ledger.attempt(ctx)
        _, spec, _ = await ledger.action(call["action_id"], ctx)
        provider_ref = Ref.model_validate(spec["provider_ref"])
        provider = Principal(
            id="controlled-local-office-service",
            kind="service",
            auth_session_id="controlled-office-session",
        )
        case = SimpleNamespace(
            ctx=ctx,
            ledger=ledger,
            reader=ControlledSQLReader(ledger.store, ctx.scope.resource_refs[0].wire()),
        )
        registry = ToolRegistry()
        for factory in FACTORIES:
            registry.register(factory(provider_ref), expected_revision=registry.revision)
        pins = tuple(Ref.model_validate(registry.reference(e)) for e in registry.snapshot()[1])
        resources = PureParameterResourceReader(registry, None, pins)
        recovery = PureParameterRecoveryAccess(
            resources, ledger, authority=ControlledRecoveryAuthority(case, provider)
        )
        source = ToolReceiptStore(
            ledger,
            FSBlobStore(Path(data["blob_directory"])),
            provider_ref=provider_ref,
            provider=provider,
            access=recovery,
            verifier=verifier_router(registry, provider_ref),
        )
        service = BudgetService(ledger.store)
        budget = ToolBudgetAdapter(ledger, service, state=service)
        reconciler = ToolReconciler(ledger, budget, receipts=source, evidence=source)
        results = ToolResults(source, reconciler)
        # No executor, no admission/approval: only the persisted original send is read.
        invocation = ToolInvocation(registry, ledger, budget, None, results=results)
        facade = ToolFacade(registry, invocation=invocation, lookup=source, reconciler=reconciler)
        result = await facade.invoke(data["request"], ctx)
        outcome = (
            await facade.read_outcome(call["action_id"], ctx) if result["kind"] == "ok" else None
        )
        print(
            json.dumps(
                {
                    "kind": result["kind"],
                    "data": result.get("payload", {}).get("data"),
                    "outcome": outcome["outcome"] if outcome else None,
                    "failure_code": result.get("failure", {}).get("code"),
                }
            )
        )
    finally:
        await database.close()


if __name__ == "__main__":
    try:
        asyncio.run(main(), loop_factory=control_plane_loop)
    except Exception as exc:
        print(json.dumps({"error_type": type(exc).__name__}))
        raise SystemExit(1) from None
