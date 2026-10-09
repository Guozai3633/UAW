"""Immutable text artifacts and owned provenance, independent of Runner files."""

from uaw.agent.contracts import Payload, identity
from uaw.agent.sources import check_pin
from uaw.infrastructure.db.records import PostgresRecordStore, parameter_hash
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore
from uaw.shared.contracts import Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import BlobStorePort

ARTIFACTS = "workspace.artifacts"
BINDINGS = "workspace.artifact.bindings"


class ArtifactRepository:
    def __init__(self, records: PostgresRecordStore, blobs: BlobStorePort) -> None:
        self.records, self.blobs = records, blobs
        self.transactions = TransactionalStore(records.database)

    async def register(self, value: Payload, binding: Payload, ctx: TrustedExecutionContext) -> Ref:
        validate_contract("ArtifactRecord", value)
        validate_contract("ArtifactSourceBinding", binding)

        async def write(tx: RecordTransaction) -> Payload:
            await tx.write(ARTIFACTS, value["id"], "ArtifactRecord", value)
            await tx.write(BINDINGS, value["id"], "ArtifactSourceBinding", binding)
            return {
                "kind": "artifact",
                "id": value["id"],
                "version": "1",
                "content_hash": parameter_hash(value),
            }

        ref = await self.transactions.execute(
            ctx.principal,
            "artifact-" + value["id"],
            RequestMeta(request_id="register", schema_version="0.1"),
            {"value": value, "binding": binding},
            write,
        )
        return Ref.model_validate(ref)

    async def read(self, ref: Ref, ctx: TrustedExecutionContext) -> tuple[Payload, str, Payload]:
        row = await self.records.get(ctx.principal, ARTIFACTS, ref.id)
        check_pin(ref, "artifact", row.resource_id, row.revision, row.payload)
        validate_contract("ArtifactRecord", row.payload)
        binding = (await self.records.get(ctx.principal, BINDINGS, ref.id)).payload
        validate_contract("ArtifactSourceBinding", binding)
        import json

        original = TrustedExecutionContext.model_validate_json(json.dumps(binding["context"]))
        if identity(original) != identity(ctx):
            raise reject("artifact_scope_denied", "Artifact belongs to another owned scope", 403)
        value = row.payload
        content = value["content_ref"]
        if content != {
            "kind": "blob",
            "id": value["content_hash"],
            "version": "1",
            "content_hash": value["content_hash"],
        }:
            raise reject("artifact_content_invalid", "Artifact content is not a fixed blob", 412)
        raw = await self.blobs.get(ctx.principal, value["content_hash"])
        import hashlib

        if (
            len(raw) != value["size_bytes"]
            or hashlib.sha256(raw).hexdigest() != value["content_hash"]
        ):
            raise reject(
                "artifact_content_invalid", "Artifact bytes differ from their provenance", 412
            )
        if value["format_kind"] not in ("text", "markdown") or len(raw) > 65536:
            raise reject(
                "artifact_format_unavailable", "Only bounded text/Markdown artifacts supported", 422
            )
        return value, raw.decode("utf-8", errors="strict"), binding
