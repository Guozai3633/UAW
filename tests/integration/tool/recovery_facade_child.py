"""Fresh-process SQL facade recovery with controlled source ports, no executor."""

import asyncio
import json
import os
import sys
from types import SimpleNamespace

from tests.integration.tool.receipt_fixtures import (
    ControlledEvidenceReader,
    ControlledReceiptReader,
)
from tests.integration.tool.recovery_fixtures import (
    ControlledActionReceiptLookup,
    NoNewExecutionAccess,
)
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.session import Database
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.run.budget import BudgetService
from uaw.shared.contracts import TrustedExecutionContext
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.facade import ToolFacade
from uaw.tool.ledger import ToolLedger
from uaw.tool.reconciliation import ToolReconciler
from uaw.tool.registry import ToolRegistry


async def main():
    data = json.loads(sys.stdin.read())
    # Inherit configured URL through environment only, never copy/output credentials.
    db = Database(os.environ["UAW_TEST_DATABASE_URL"])
    try:
        await db.check()
        ctx = TrustedExecutionContext.model_validate_json(json.dumps(data["context"]))
        ledger = ToolLedger(PostgresRecordStore(db))
        service = BudgetService(ledger.store)
        case = SimpleNamespace(ctx=ctx, ledger=ledger)
        reader = ControlledReceiptReader(case)
        reconciler = ToolReconciler(
            ledger,
            ToolBudgetAdapter(ledger, service, state=service),
            receipts=reader,
            evidence=ControlledEvidenceReader(case),
        )
        f = ToolFacade(
            ToolRegistry(),
            NoNewExecutionAccess(),
            reconciler=reconciler,
            lookup=ControlledActionReceiptLookup(case, receipts=reader),
        )
        result = await f.reconcile(data["request"], ctx)
        actual = (
            await f.read_outcome(data["request"]["action_id"], ctx)
            if result["kind"] == "ok"
            else None
        )
        print(
            json.dumps(
                {
                    "kind": result["kind"],
                    "outcome": actual["outcome"] if actual else None,
                    "failure_code": result.get("failure", {}).get("code"),
                }
            )
        )
    finally:
        await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main(), loop_factory=control_plane_loop)
    except Exception as exc:
        print(json.dumps({"error_type": type(exc).__name__}))
        raise SystemExit(1) from None
