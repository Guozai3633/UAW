"""Fresh process, real SQL, only original controlled sources/public verification keys.

No executor, native window, send, file open or executable directory permission.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

from tests.integration.tool.conftest import ControlledSQLReader
from tests.integration.tool.file_pipeline_fixture import ControlledFileBridge
from tests.integration.tool.file_recovery_child import ControlledPublicKeyDirectory
from tests.integration.tool.office_pipeline_fixture import FACTORIES, VERIFIERS
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
from uaw.tool.providers.file_read import file_read_spec
from uaw.tool.providers.file_store import FileReadVerifier, FileReceiptStore
from uaw.tool.providers.multiplex import ToolOutputVerifierBinding, ToolOutputVerifierRouter
from uaw.tool.receipt_store import ToolReceiptStore
from uaw.tool.reconciliation import ToolReconciler
from uaw.tool.registry import AdapterBinding, ToolRegistry
from uaw.tool.results import ToolResults
from uaw.tool.runtime_router import RoutedToolRuntime, ToolRuntimeRoute


class NoNewExecutionAccess:
    async def snapshot(self, ctx):
        raise AssertionError("Recovery must not request new execution admission")


async def main():
    data = json.loads(sys.stdin.read())
    database = Database(os.environ["UAW_TEST_DATABASE_URL"])
    try:
        await database.check()
        ledger = ToolLedger(PostgresRecordStore(database))
        contexts = tuple(
            TrustedExecutionContext.model_validate_json(json.dumps(d["context"]))
            for d in data["sources"]
        )
        originals = [
            await ledger.action((await ledger.attempt(ctx))["action_id"], ctx) for ctx in contexts
        ]
        registry = ToolRegistry()
        provider_ref = Ref.model_validate(originals[0][1]["provider_ref"])
        for factory in (*FACTORIES, file_read_spec):
            registry.register(
                factory(provider_ref),
                expected_revision=registry.revision,
                binding=AdapterBinding(
                    provider_ref, frozenset({"sql-component-test"}), implemented=True
                ),
            )
        office_pins = tuple(
            Ref.model_validate(registry.reference(e)) for e in registry.snapshot()[1][:-1]
        )
        access = NoNewExecutionAccess()
        service = BudgetService(ledger.store)
        budget = ToolBudgetAdapter(ledger, service, state=service)
        routes, bridges = [], []
        for d, ctx, original in zip(data["sources"], contexts, originals, strict=True):
            call, spec, _ = original
            provider = Principal.model_validate(d["provider"])
            case = SimpleNamespace(
                ctx=ctx,
                ledger=ledger,
                reader=ControlledSQLReader(ledger.store, ctx.scope.resource_refs[0].wire()),
            )
            blob = FSBlobStore(Path(d["blob_directory"]))
            if spec["id"] == "file.read":
                signatures = ControlledPublicKeyDirectory(d["public_keys"])
                bridge = ControlledFileBridge(case, provider, blob, signatures)
                bridges.append(bridge)
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
            else:
                resources = PureParameterResourceReader(registry, None, office_pins)
                recovery = PureParameterRecoveryAccess(
                    resources, ledger, authority=ControlledRecoveryAuthority(case, provider)
                )
                verifier = ToolOutputVerifierRouter(
                    tuple(
                        ToolOutputVerifierBinding(pin, provider_ref, factory(provider_ref))
                        for pin, factory in zip(office_pins, VERIFIERS, strict=True)
                    )
                )
                source = ToolReceiptStore(
                    ledger,
                    blob,
                    provider_ref=provider_ref,
                    provider=provider,
                    access=recovery,
                    verifier=verifier,
                )
            reconciler = ToolReconciler(ledger, budget, receipts=source, evidence=source)
            results = ToolResults(source, reconciler)
            invocation = ToolInvocation(
                registry, ledger, budget, None, access=access, results=results
            )
            facade = ToolFacade(
                registry, invocation=invocation, lookup=source, reconciler=reconciler
            )
            routes.append(
                ToolRuntimeRoute(
                    Ref.model_validate(call["tool_ref"]), provider_ref, facade, results
                )
            )
        runtime = RoutedToolRuntime(registry, ledger, tuple(routes), access=access)
        output = []
        for d, ctx in zip(data["sources"], contexts, strict=True):
            call = await ledger.attempt(ctx)
            effect = await ledger.effect(call["action_id"], ctx)
            reconciled = await runtime.reconcile(
                {"action_id": call["action_id"], "expected_revision": effect["revision"]}, ctx
            )
            assert reconciled["kind"] == "ok", reconciled
            normalized = await runtime.invoke(d["request"], ctx)
            assert normalized["kind"] == "ok", normalized
            result = await runtime.read_result(call["action_id"], ctx)
            outcome = await runtime.read_outcome(call["action_id"], ctx)
            output.append(
                {
                    "tool_ref": call["tool_ref"],
                    "data": result["payload"]["data"],
                    "outcome": outcome["outcome"],
                    "usage_ref": result["usage_ref"],
                }
            )
        print(
            json.dumps(
                {
                    "results": output,
                    "sends": sum(b.calls for b in bridges),
                    "opens": sum(b.opens for b in bridges),
                    "executors": 0,
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
