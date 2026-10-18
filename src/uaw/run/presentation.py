"""One read-only snapshot for display; no Run/frame/proposal or execution mutations."""

from sqlalchemy import select, text

from uaw.agent.completion.delivery import BUNDLES, CONTRACTS, PROPOSALS, REPORTS, row_pin
from uaw.agent.contracts import Payload
from uaw.agent.conversation import DECISIONS
from uaw.agent.sources import check_pin
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import RecordTransaction, timestamp
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.conversation_control import TERMINAL, ConversationControls
from uaw.run.jobs import JOBS
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import DomainError, reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing
from uaw.workspace.artifact_repository import ARTIFACTS


class RunPresentationReader:
    def __init__(self, records: PostgresRecordStore) -> None:
        self.records = records

    @staticmethod
    async def rows(tx: RecordTransaction, namespace: str, run_id: str) -> list[RecordRow]:
        return list(
            await tx.session.scalars(
                select(RecordRow)
                .where(
                    RecordRow.principal_id == tx.owner,
                    RecordRow.namespace == namespace,
                    RecordRow.deleted.is_(False),
                    (RecordRow.payload["run_id"].as_string() == run_id)
                    | (RecordRow.payload["run_ref"]["id"].as_string() == run_id),
                )
                .order_by(RecordRow.updated_at.desc(), RecordRow.resource_id)
                .limit(65)
            )
        )

    async def understanding(
        self, tx: RecordTransaction, run: Payload, input_revision: int
    ) -> Payload:
        decisions = await self.rows(tx, DECISIONS, run["id"])
        if len(decisions) > 64:
            raise reject("presentation_inventory_limit", "Decision inventory exceeds limit", 503)
        current = [r for r in decisions if r.payload.get("input_revision") == input_revision]
        for row in current[:1]:
            value = row.payload
            validate_contract("FirstDecisionRecord", value)
            if row.schema_name != "FirstDecisionRecord" or value["run_ref"]["id"] != run["id"]:
                raise reject("presentation_decision_unowned", "Original decision differs", 412)
            pin = Ref.model_validate(value["model_output_ref"])
            output = await tx.load("model.outputs", pin.id)
            check_pin(pin, "content", output.resource_id, output.revision, output.payload)
            validate_contract("ModelOutput", output.payload)
            invocation = await tx.load("model.invocations", value["attempt_id"])
            result = invocation.payload.get("result", {})
            if (
                output.schema_name != "ModelOutput"
                or output.payload.get("structured_data") != value["decision"]
                or output.payload["attempt_id"] != value["attempt_id"]
                or invocation.payload["run_id"] != run["id"]
                or invocation.payload["state"] != "finished"
                or result.get("kind") != "ok"
                or result.get("payload") != output.payload
                or value["model_output_ref"] not in result.get("output_refs", [])
            ):
                raise reject("presentation_model_unowned", "Original model output differs", 412)
            summary = value["decision"].get("understanding")
            if summary is not None:
                validate_contract("ConversationUnderstanding", summary)
                return {
                    "state": "available",
                    "input_revision": input_revision,
                    "value": summary,
                    "decision_record_ref": row_pin("content", row.resource_id, value).wire(),
                    "model_output_ref": value["model_output_ref"],
                }
        return {
            "state": "not_provided" if current or run["status"] in TERMINAL else "pending",
            "input_revision": input_revision,
        }

    async def delivery(
        self, tx: RecordTransaction, run: Payload, input_revision: int, job: Payload
    ) -> tuple[Payload | None, str | None]:
        if job.get("stage") != "delivery" or "proposal_ref" not in job:
            return None, None
        proposal_pin = Ref.model_validate(job["proposal_ref"])
        bundle = (await tx.load(BUNDLES, proposal_pin.id)).payload
        validate_contract("CompletionBundle", bundle)
        context = bundle["context"]
        if (
            context["principal"]["id"] != tx.owner
            or context["run_id"] != run["id"]
            or context["conversation_id"] != run["conversation_id"]
            or context["task_id"] != run["task_id"]
            or bundle["proposal_ref"] != proposal_pin.wire()
        ):
            raise reject("presentation_delivery_unowned", "Original delivery scope differs", 412)
        frame = await tx.load("intent.frames", run["task_id"])
        if frame.payload.get("input_revision") != input_revision:
            return None, None
        try:
            check_pin(
                Ref.model_validate(bundle["frame_ref"]),
                "task_frame",
                frame.resource_id,
                frame.revision,
                frame.payload,
            )
        except DomainError:
            return None, None
        loaded = {}
        for name, namespace, schema, kind in (
            ("contract", CONTRACTS, "Contract", "content"),
            ("report", REPORTS, "VerificationReport", "verification"),
            ("proposal", PROPOSALS, "DeliveryProposal", "content"),
            ("artifact", ARTIFACTS, "ArtifactRecord", "artifact"),
        ):
            pin = Ref.model_validate(bundle[name + "_ref"])
            row = await tx.load(namespace, pin.id)
            if row.schema_name != schema:
                raise reject("presentation_delivery_unowned", "Delivery schema differs", 412)
            check_pin(pin, kind, row.resource_id, row.revision, row.payload)
            validate_contract(schema, row.payload)
            loaded[name] = row.payload
        proposal = loaded["proposal"]
        if proposal["run_ref"] != {"kind": "run", "id": run["id"], "version": str(run["revision"])}:
            return None, None
        if (
            loaded["report"]["contract_ref"] != bundle["contract_ref"]
            or bundle["artifact_ref"] not in loaded["report"]["target_refs"]
            or proposal["report_ref"] != bundle["report_ref"]
            or proposal["contract_ref"] != bundle["contract_ref"]
            or proposal["artifact_refs"] != [bundle["artifact_ref"]]
            or proposal["outcome"] != loaded["report"]["outcome"]
        ):
            raise reject("presentation_delivery_unowned", "Delivery sources disagree", 412)
        try:
            acceptance = (await tx.load("run.completion.acceptance", proposal_pin.id)).payload
        except StoreMissing:
            decision = None
        else:
            validate_contract("CompletionAcceptance", acceptance)
            if (
                acceptance["bundle_ref"] != row_pin("content", proposal_pin.id, bundle).wire()
                or acceptance["principal"] != context["principal"]
            ):
                raise reject("presentation_acceptance_unowned", "Acceptance scope differs", 412)
            decision = acceptance["decision"]
        return {
            **{name + "_ref": bundle[name + "_ref"] for name in ("artifact", "report", "proposal")},
            "bundle_ref": row_pin("content", proposal_pin.id, bundle).wire(),
            "input_revision": input_revision,
            "run_revision": run["revision"],
            "outcome": loaded["report"]["outcome"],
            "requires_acceptance": loaded["contract"].get("acceptance_required", False),
        }, decision

    async def read(self, actor: Principal, run_id: str) -> Payload:
        async with self.records.database.sessions.begin() as session:
            await session.execute(
                text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            )
            tx = RecordTransaction(session, actor.id)
            run = await ConversationControls(self.records).owned(tx, actor, run_id)
            inputs = await tx.load("run.input_sets", run_id)
            value: Payload = {
                "protocol": "conversation-v1",
                "run": run,
                "input_revision": inputs.revision,
                "understanding": await self.understanding(tx, run, inputs.revision),
                "captured_at": timestamp(),
            }
            try:
                job = (await tx.load(JOBS, run_id)).payload
            except StoreMissing:
                phase = "unavailable"
            else:
                validate_contract("BackgroundRunJob", job)
                if job["run_id"] != run_id or job["principal"]["id"] != actor.id:
                    raise reject("presentation_job_unowned", "Original job owner differs", 412)
                phase = "preparing" if run["status"] in ("queued", "preparing") else "working"
                delivery, decision = await self.delivery(tx, run, inputs.revision, job)
                if delivery is not None:
                    value["delivery"] = delivery
                    phase = "needs_revision" if delivery["outcome"] != "succeeded" else "finalizing"
                    ledger = (await tx.load("budget.ledgers", run_id)).payload
                    try:
                        await RunIdleEffects().check(tx, actor, run_id)
                    except DomainError, StoreMissing:
                        idle = False
                        phase = "unavailable"
                    else:
                        idle = True
                    if (
                        phase == "finalizing"
                        and decision is None
                        and idle
                        and job["state"] in ("waiting", "working")
                        and delivery["requires_acceptance"]
                        and not ledger["cancel_requested"]
                        and not ledger["overdrawn"]
                    ):
                        phase = "awaiting_acceptance"
                    if decision is not None and decision != "accept":
                        phase = "needs_revision"
            if run["status"] in TERMINAL:
                phase = run["status"]
            elif (await tx.load("budget.ledgers", run_id)).payload["cancel_requested"]:
                phase = "stopping"
                value.pop("delivery", None)
            elif run["status"] == "waiting_for_user" and "delivery" not in value:
                phase = "waiting_for_user"
            elif run["status"] == "verifying" and "delivery" not in value:
                phase = "verifying"
            value["phase"] = phase
            validate_contract("RunPresentationView", value)
            return value
