"""Actual fresh-process SQL file recovery; controlled PUBLIC key/current data sources.

No private keys, executor, OS file read, native confirmation or production capability.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

from tests.integration.tool.conftest import ControlledSQLReader
from tests.integration.tool.file_pipeline_fixture import ControlledFileBridge
from uaw.infrastructure.blob.filesystem import FSBlobStore
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.session import Database
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.run.budget import BudgetService
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.shared.runner_signatures import VerificationKey, verify
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.facade import ToolFacade
from uaw.tool.invocation.dispatch import ToolInvocation
from uaw.tool.ledger import ToolLedger
from uaw.tool.providers.file_read import file_read_spec
from uaw.tool.providers.file_store import FileReadVerifier, FileReceiptStore
from uaw.tool.reconciliation import ToolReconciler
from uaw.tool.registry import ToolRegistry
from uaw.tool.results import ToolResults


class ControlledPublicKeyDirectory:
    def __init__(self, keys):
        self.keys = keys

    def verify_command(self, command, *, device_id):
        return device_id == "controlled-device" and verify(
            command.wire(),
            command.signature,
            VerificationKey("command", device_id, bytes(self.keys["control"]), "control", False),
            "command",
        )

    def verify_receipt(self, receipt, *, device_id):
        return device_id == "controlled-device" and verify(
            receipt,
            receipt["signature"],
            VerificationKey("receipt", device_id, bytes(self.keys["device"]), "device", False),
            "receipt",
        )


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
            kind="service", id="controlled-file-service", auth_session_id="controlled-file-session"
        )
        case = SimpleNamespace(
            ctx=ctx,
            ledger=ledger,
            reader=ControlledSQLReader(ledger.store, ctx.scope.resource_refs[0].wire()),
        )
        blob = FSBlobStore(Path(data["blob_directory"]))
        signatures = ControlledPublicKeyDirectory(data["public_keys"])
        bridge = ControlledFileBridge(case, provider, blob, signatures)
        source = FileReceiptStore(
            ledger,
            blob,
            provider_ref=provider_ref,
            provider=provider,
            access=bridge,
            bridge=bridge,
            signatures=signatures,
        )
        source.verifier = FileReadVerifier(source)
        service = BudgetService(ledger.store)
        budget = ToolBudgetAdapter(ledger, service, state=service)
        reconciler = ToolReconciler(ledger, budget, receipts=source, evidence=source)
        results = ToolResults(source, reconciler)
        registry = ToolRegistry()
        registry.register(file_read_spec(provider_ref), expected_revision=0)
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
                    "outcome": outcome["outcome"] if outcome else None,
                    "data": result.get("payload", {}).get("data"),
                    "failure_code": result.get("failure", {}).get("code"),
                    "sends": bridge.calls,
                    "opens": bridge.opens,
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
