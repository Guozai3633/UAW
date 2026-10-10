"""User-owned delivery reads, separate from permission to execute or accept."""

import json
from typing import Any

from sqlalchemy import select

from uaw.agent.completion.delivery import BUNDLES, CONTRACTS, PROPOSALS, REPORTS, row_pin
from uaw.agent.contracts import identity
from uaw.agent.sources import check_pin
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.shared.errors import DomainError, reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import BlobStorePort, StoreMissing
from uaw.workspace.artifact_repository import ARTIFACTS, BINDINGS, ArtifactRepository

Payload = dict[str, Any]


class DeliveryReader:
    def __init__(self, records: PostgresRecordStore, blobs: BlobStorePort) -> None:
        self.records, self.artifacts = records, ArtifactRepository(records, blobs)

    async def artifact(
        self, actor: Principal, artifact_id: str, version: str | None = None
    ) -> tuple[Payload, str]:
        # Fresh HTTP identity authorizes the owner read. The saved context below only
        # verifies immutable provenance; it is never presented as current authentication.
        row = await self.records.get(actor, ARTIFACTS, artifact_id)
        validate_contract("ArtifactRecord", row.payload)
        if version is not None and version != row.payload["version"]:
            raise reject("artifact_version_stale", "Artifact version differs", 412)
        binding = (await self.records.get(actor, BINDINGS, artifact_id)).payload
        validate_contract("ArtifactSourceBinding", binding)
        original = TrustedExecutionContext.model_validate_json(json.dumps(binding["context"]))
        await self._owner(actor, original)
        pin = row_pin("artifact", row.resource_id, row.payload)
        value, content, _ = await self.artifacts.read(pin, original)
        return value, content

    async def _owner(self, actor: Principal, original: TrustedExecutionContext) -> Payload:
        if (
            actor.kind != "user"
            or original.principal.kind != "user"
            or original.principal.id != actor.id
        ):
            raise reject("delivery_owner_denied", "Delivery belongs to another user", 403)
        run = (await self.records.get(actor, "runs", original.run_id or "")).payload
        if run["conversation_id"] != original.conversation_id or run["task_id"] != original.task_id:
            raise reject("delivery_scope_denied", "Original delivery Run scope differs", 403)
        await self.records.get(actor, "conversations", run["conversation_id"])
        return run

    async def read(self, actor: Principal, run_id: str) -> tuple[Payload, TrustedExecutionContext]:
        run = (await self.records.get(actor, "runs", run_id)).payload
        validate_contract("RunRecord", run)
        async with self.records.database.sessions() as session:
            rows = list(
                await session.scalars(
                    select(RecordRow)
                    .where(
                        RecordRow.principal_id == actor.id,
                        RecordRow.namespace == BUNDLES,
                        RecordRow.deleted.is_(False),
                        RecordRow.payload["context"]["run_id"].astext == run_id,
                    )
                    .order_by(RecordRow.updated_at.desc(), RecordRow.resource_id)
                    .limit(1)
                )
            )
        if not rows:
            raise StoreMissing()
        bundle = rows[0].payload
        validate_contract("CompletionBundle", bundle)
        original = TrustedExecutionContext.model_validate_json(json.dumps(bundle["context"]))
        await self._owner(actor, original)
        artifact, content = await self.artifact(
            actor, bundle["artifact_ref"]["id"], bundle["artifact_ref"]["version"]
        )
        check_pin(
            Ref.model_validate(bundle["artifact_ref"]), "artifact", artifact["id"], 1, artifact
        )
        artifact_binding = (await self.records.get(actor, BINDINGS, artifact["id"])).payload
        artifact_context = TrustedExecutionContext.model_validate_json(
            json.dumps(artifact_binding["context"])
        )
        if identity(artifact_context) != identity(original):
            raise reject("delivery_artifact_scope_invalid", "Artifact and bundle scope differ", 412)
        loaded = {}
        for name, namespace, schema in (
            ("contract", CONTRACTS, "Contract"),
            ("report", REPORTS, "VerificationReport"),
            ("proposal", PROPOSALS, "DeliveryProposal"),
        ):
            pin = Ref.model_validate(bundle[name + "_ref"])
            row = await self.records.get(actor, namespace, pin.id)
            check_pin(
                pin,
                "verification" if name == "report" else "content",
                row.resource_id,
                row.revision,
                row.payload,
            )
            validate_contract(schema, row.payload)
            loaded[name] = row.payload
        if (
            loaded["report"]["contract_ref"] != bundle["contract_ref"]
            or bundle["artifact_ref"] not in loaded["report"]["target_refs"]
            or loaded["proposal"]["report_ref"] != bundle["report_ref"]
            or loaded["proposal"]["contract_ref"] != bundle["contract_ref"]
            or loaded["proposal"]["artifact_refs"] != [bundle["artifact_ref"]]
            or loaded["proposal"]["run_ref"]["id"] != run_id
        ):
            raise reject("delivery_binding_invalid", "Delivery sources disagree", 412)
        current_frame = await self.records.get(actor, "intent.frames", run["task_id"])
        try:
            check_pin(
                Ref.model_validate(bundle["frame_ref"]),
                "task_frame",
                current_frame.resource_id,
                current_frame.revision,
                current_frame.payload,
            )
        except DomainError:
            stale = True
        else:
            stale = False
        value = {
            "run_id": run_id,
            "bundle_ref": row_pin("content", rows[0].resource_id, bundle).wire(),
            "artifact_ref": bundle["artifact_ref"],
            "artifact": artifact,
            "content": content,
            "contract_ref": bundle["contract_ref"],
            "report_ref": bundle["report_ref"],
            "proposal_ref": bundle["proposal_ref"],
            **loaded,
            "requires_acceptance": loaded["contract"].get("acceptance_required", False),
            "stale": stale,
        }
        try:
            acceptance = (
                await self.records.get(actor, "run.completion.acceptance", rows[0].resource_id)
            ).payload
        except StoreMissing:
            pass
        else:
            validate_contract("CompletionAcceptance", acceptance)
            if (
                acceptance["bundle_ref"] != value["bundle_ref"]
                or acceptance["principal"] != original.principal.wire()
            ):
                raise reject("delivery_acceptance_invalid", "Acceptance scope differs", 412)
            value["acceptance"] = acceptance
        validate_contract("RunDeliveryView", value)
        return value, original
