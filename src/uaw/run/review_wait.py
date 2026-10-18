"""Owned artifact review waits. A stable Item is evidence, never an execution grant."""

import json

from uaw.agent.completion.contracts import report_outcome
from uaw.agent.completion.delivery import BUNDLES, CONTRACTS, PROPOSALS, REPORTS
from uaw.agent.contracts import Payload, identifier, identity
from uaw.agent.sources import check_pin
from uaw.infrastructure.db.models import RecordVersionRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.conversation_control import TERMINAL, ConversationControls
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing
from uaw.workspace.artifact_repository import ARTIFACTS


class ReviewWaitSources:
    def __init__(self, records: PostgresRecordStore) -> None:
        self.records = records

    async def check(
        self,
        tx: RecordTransaction,
        actor: Principal,
        run_id: str,
        item_ref: Ref,
        *,
        opened: bool,
    ) -> None:
        await self.read(tx, actor, run_id, item_ref, current=opened, undecided=opened)

    async def read(
        self,
        tx: RecordTransaction,
        actor: Principal,
        run_id: str,
        item_ref: Ref,
        *,
        current: bool,
        undecided: bool = False,
    ) -> Payload:
        run = await ConversationControls(self.records).owned(tx, actor, run_id)
        item = await tx.load("items", item_ref.id)
        validate_contract("InteractionItem", item.payload)
        check_pin(item_ref, "item", item.resource_id, item.revision, item.payload)
        refs = item.payload["resource_refs"]
        if (
            item.schema_name != "InteractionItem"
            or item.payload["id"] != item.resource_id
            or item.payload["revision"] != item.revision
            or item.payload["type"] != "artifact"
            or item.payload["status"] != "completed"
            or item.payload.get("run_id") != run_id
            or item.payload["conversation_id"] != run["conversation_id"]
            or len(refs) != 4
        ):
            raise reject("review_wait_source_changed", "Original artifact Item differs", 412)
        bundle_pin = Ref.model_validate(refs[1])
        row = await tx.load(BUNDLES, bundle_pin.id)
        check_pin(bundle_pin, "content", row.resource_id, row.revision, row.payload)
        bundle = row.payload
        validate_contract("CompletionBundle", bundle)
        ctx = TrustedExecutionContext.model_validate_json(json.dumps(bundle["context"]))
        if (
            row.schema_name != "CompletionBundle"
            or ctx.principal != actor
            or ctx.run_id != run_id
            or ctx.conversation_id != run["conversation_id"]
            or ctx.task_id != run["task_id"]
            or item.resource_id
            != identifier("artifact-item-", {"proposal": bundle["proposal_ref"]})
            or refs
            != [
                bundle["artifact_ref"],
                bundle_pin.wire(),
                bundle["report_ref"],
                bundle["contract_ref"],
            ]
        ):
            raise reject("review_wait_owner_denied", "Original review scope differs", 403)
        loaded = {}
        for name, namespace, schema, kind in (
            ("contract", CONTRACTS, "Contract", "content"),
            ("report", REPORTS, "VerificationReport", "verification"),
            ("proposal", PROPOSALS, "DeliveryProposal", "content"),
            ("artifact", ARTIFACTS, "ArtifactRecord", "artifact"),
        ):
            pin = Ref.model_validate(bundle[name + "_ref"])
            source = await tx.load(namespace, pin.id)
            check_pin(pin, kind, source.resource_id, source.revision, source.payload)
            validate_contract(schema, source.payload)
            if source.schema_name != schema:
                raise reject("review_wait_source_changed", "Original delivery schema differs", 412)
            loaded[name] = source.payload
        contract, report, proposal = (loaded[k] for k in ("contract", "report", "proposal"))
        if (
            not contract.get("acceptance_required")
            or report["outcome"] != "succeeded"
            or report_outcome(contract, report) != "succeeded"
            or proposal["outcome"] != "succeeded"
            or proposal["unresolved_effect_refs"]
            or report["contract_ref"] != bundle["contract_ref"]
            or bundle["artifact_ref"] not in report["target_refs"]
            or proposal["contract_ref"] != bundle["contract_ref"]
            or proposal["report_ref"] != bundle["report_ref"]
            or proposal["artifact_refs"] != [bundle["artifact_ref"]]
            or proposal["run_ref"]["id"] != run_id
        ):
            raise reject("review_wait_incomplete", "Successful reviewable delivery required", 409)
        if current:
            job = await tx.load("run.background.jobs", run_id)
            if run["status"] in TERMINAL or job.payload["principal"] != actor.wire():
                raise reject(
                    "review_wait_inactive", "Current original session and Run required", 409
                )
            if identity(
                TrustedExecutionContext.model_validate_json(json.dumps(job.payload["context"]))
            ) != identity(ctx):
                raise reject("review_wait_owner_denied", "Original job context differs", 403)
            if proposal["run_ref"] != {
                "kind": "run",
                "id": run_id,
                "version": str(run["revision"]),
            }:
                raise reject("review_wait_stale", "Proposal names an old Run revision", 412)
            frame = await tx.load("intent.frames", run["task_id"])
            inputs = await tx.load("run.input_sets", run_id)
            check_pin(
                Ref.model_validate(bundle["frame_ref"]),
                "task_frame",
                frame.resource_id,
                frame.revision,
                frame.payload,
            )
            if frame.payload.get("input_revision") != inputs.revision:
                raise reject("review_wait_stale", "Review input changed", 412)
            await RunIdleEffects().check(tx, actor, run_id)
            root = await tx.load("agent.loop.states", bundle["instance_id"])
            if root.payload.get("active_operation_ref"):
                raise reject("review_wait_active", "Original Agent operation remains active", 409)
            if undecided:
                try:
                    await tx.load("run.completion.acceptance", bundle_pin.id)
                except StoreMissing:
                    pass
                else:
                    raise reject(
                        "review_wait_decided", "Original delivery already has a decision", 409
                    )
        return bundle

    async def paused(
        self, ctx: TrustedExecutionContext, bundle: Payload, *, tx: RecordTransaction | None = None
    ) -> bool:
        """Current, idle delivery proof, including after original execution expiry."""
        aggregate = await ConversationControls(self.records).aggregate(
            ctx.principal, ctx.run_id or ""
        )

        async def read(tx: RecordTransaction) -> Payload:
            try:
                clock = await tx.load("run.execution_clocks", ctx.run_id or "")
            except StoreMissing:
                return {"paused": False}
            if clock.payload["mode"] != "waiting_for_user":
                return {"paused": False}
            validate_contract("RunExecutionClock", clock.payload)
            binding = await tx.load("run.protocol_bindings", ctx.run_id or "")
            initial = await tx.session.get(
                RecordVersionRow, (tx.owner, "run.execution_clocks", ctx.run_id, 1)
            )
            if (
                clock.schema_name != "RunExecutionClock"
                or clock.payload["run_id"] != ctx.run_id
                or clock.payload["revision"] != clock.revision
                or clock.payload["in_flight_refs"]
                or binding.payload["clock_ref"]
                != {"kind": "checkpoint", "id": ctx.run_id, "version": str(clock.revision)}
                or initial is None
                or initial.schema_name != "RunExecutionClock"
                or initial.payload["run_id"] != ctx.run_id
                or initial.payload["revision"] != 1
                or clock.payload["active_limit_ms"] != initial.payload["active_limit_ms"]
                or clock.payload["active_elapsed_ms"] >= clock.payload["active_limit_ms"]
            ):
                raise reject("review_wait_clock_changed", "Original paused clock differs", 412)
            pin = Ref.model_validate(clock.payload["waiting_item_ref"])
            item = await tx.load("items", pin.id)
            if item.payload["type"] != "artifact":
                return {"paused": False}
            original = await self.read(tx, ctx.principal, ctx.run_id or "", pin, current=True)
            if original != bundle:
                raise reject("review_wait_stale", "Paused delivery differs from request", 412)
            return {"paused": True}

        if tx is not None:
            return bool((await read(tx))["paused"])
        return bool(
            (
                await TransactionalStore(self.records.database).inspect(
                    ctx.principal, aggregate, read
                )
            )["paused"]
        )
