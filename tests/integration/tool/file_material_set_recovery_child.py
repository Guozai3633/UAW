"""Fresh SQL process with PUBLIC test keys, no executor/open or production authority."""

import asyncio
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

from tests.integration.tool.conftest import ControlledSQLReader
from tests.integration.tool.file_material_set_fixture import ControlledRegisteredMaterialReader
from tests.integration.tool.file_pipeline_fixture import ControlledFileBridge
from tests.integration.tool.file_recovery_child import ControlledPublicKeyDirectory
from uaw.infrastructure.blob.filesystem import FSBlobStore
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.session import Database
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.tool.ledger import ToolLedger
from uaw.tool.providers.file_material import FileMaterialAdapter
from uaw.tool.providers.file_material_set import FileMaterialSetAdapter
from uaw.tool.providers.file_store import FileReadVerifier, FileReceiptStore


async def main():
    data = json.loads(sys.stdin.read())
    database = Database(os.environ["UAW_TEST_DATABASE_URL"])
    try:
        await database.check()
        entries, bridges, refs = {}, [], []
        for entry in data["entries"]:
            ctx = TrustedExecutionContext.model_validate_json(json.dumps(entry["context"]))
            ledger = ToolLedger(PostgresRecordStore(database))
            call = await ledger.attempt(ctx)
            _, spec, _ = await ledger.action(call["action_id"], ctx)
            provider = Principal(
                kind="service",
                id="controlled-file-service",
                auth_session_id="controlled-file-session",
            )
            case = SimpleNamespace(
                ctx=ctx,
                ledger=ledger,
                reader=ControlledSQLReader(ledger.store, ctx.scope.resource_refs[0].wire()),
            )
            blob = FSBlobStore(Path(entry["blob_directory"]))
            signatures = ControlledPublicKeyDirectory(entry["public_keys"])
            bridge = ControlledFileBridge(case, provider, blob, signatures)
            source = FileReceiptStore(
                ledger,
                blob,
                provider_ref=Ref.model_validate(spec["provider_ref"]),
                provider=provider,
                access=bridge,
                bridge=bridge,
                signatures=signatures,
            )
            source.verifier = FileReadVerifier(source)
            ref = Ref.model_validate(entry["material_ref"])
            entries[ref.id] = (ctx, FileMaterialAdapter(source))
            refs.append(ref)
            bridges.append(bridge)
        current = TrustedExecutionContext.model_validate_json(json.dumps(data["current_context"]))
        result = await FileMaterialSetAdapter(ControlledRegisteredMaterialReader(entries)).read(
            tuple(refs), current
        )
        print(
            json.dumps(
                {
                    "contents": [m.content for m in result.materials],
                    "refs": [r.wire() for r in result.refs],
                    "usages": [m.usage for m in result.materials],
                    "sends": sum(b.calls for b in bridges),
                    "opens": sum(b.opens for b in bridges),
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
