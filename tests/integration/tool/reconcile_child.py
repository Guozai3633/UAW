"""Subprocess SQL recovery with controlled component Readers, never a real executor."""

import asyncio
import json
import os
import sys
from types import SimpleNamespace

from tests.integration.tool.receipt_fixtures import (
    ControlledEvidenceReader,
    ControlledReceiptReader,
)
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.session import Database
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.run.budget import BudgetService
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.ledger import ToolLedger
from uaw.tool.reconciliation import ToolReconciler


async def main() -> None:
    data = json.loads(sys.stdin.read())
    # Test URL is inherited only through the configured environment, never argv/output.
    database = Database(os.environ["UAW_TEST_DATABASE_URL"])
    try:
        await database.check()
        ctx = TrustedExecutionContext.model_validate_json(json.dumps(data["context"]))
        ref = Ref.model_validate_json(json.dumps(data["receipt_ref"]))
        ledger = ToolLedger(PostgresRecordStore(database))
        service = BudgetService(ledger.store)
        case = SimpleNamespace(ctx=ctx, ledger=ledger)
        reconciler = ToolReconciler(
            ledger,
            ToolBudgetAdapter(ledger, service, state=service),
            receipts=ControlledReceiptReader(case),
            evidence=ControlledEvidenceReader(case),
        )
        result = await reconciler.reconcile(ref, ctx, expected_revision=data["expected_revision"])
        print(
            json.dumps(
                {
                    "kind": result["kind"],
                    "state": result.get("payload", {}).get("state"),
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
