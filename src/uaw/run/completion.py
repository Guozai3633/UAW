"""Independent terminal commit: a persisted report is evidence, never write authority."""

from decimal import Decimal

from sqlalchemy import select

from uaw.agent.completion.contracts import report_outcome
from uaw.agent.completion.delivery import (
    BUNDLES,
    CONTRACTS,
    REPORTS,
    CompletionCoordinator,
    row_pin,
)
from uaw.agent.contracts import Payload, identity
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore, timestamp
from uaw.shared.contracts import Principal, Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreConflict, StoreMissing


class RunCompletionController:
    def __init__(self, completion: CompletionCoordinator) -> None:
        self.completion = completion
        self.records = completion.records
        self.transactions = TransactionalStore(self.records.database)

    async def accept(
        self,
        actor: Principal,
        bundle_ref: Ref,
        artifact_ref: Ref,
        decision: str,
        ctx: TrustedExecutionContext,
        meta: RequestMeta,
    ) -> Ref:
        if actor != ctx.principal or actor.kind != "user":
            raise reject(
                "completion_user_required", "Independent authenticated user action required", 403
            )
        bundle = await self.completion.bundle(bundle_ref, ctx)
        await self.completion.verify_bundle(bundle, ctx)
        if artifact_ref.wire() != bundle["artifact_ref"]:
            raise reject(
                "completion_acceptance_stale", "User decision names another artifact version", 412
            )
        value = {
            "bundle_ref": bundle_ref.wire(),
            "principal": actor.wire(),
            "decision": decision,
            "created_at": timestamp(),
        }
        validate_contract("CompletionAcceptance", value)

        async def write(tx: RecordTransaction) -> Payload:
            # Serialize with cancel/Run revisions; checks made before taking this lock
            # are insufficient when the user decides during an in-flight cancellation.
            await self.completion.verify_bundle(bundle, ctx)
            await tx.write(
                "run.completion.acceptance", bundle_ref.id, "CompletionAcceptance", value
            )
            return row_pin("content", bundle_ref.id, value).wire()

        result = await self.transactions.execute(
            actor,
            "conversation:" + (ctx.conversation_id or ""),
            meta,
            {
                "bundle_ref": bundle_ref.wire(),
                "artifact_ref": artifact_ref.wire(),
                "decision": decision,
            },
            write,
        )
        return Ref.model_validate(result)

    async def complete(
        self, proposal_ref: Ref, ctx: TrustedExecutionContext, meta: RequestMeta
    ) -> Payload:
        bundle_row = await self.records.get(ctx.principal, BUNDLES, proposal_ref.id)
        bundle = await self.completion.bundle(
            row_pin("content", bundle_row.resource_id, bundle_row.payload), ctx
        )
        if bundle["proposal_ref"] != proposal_ref.wire():
            raise reject("completion_proposal_stale", "Completion proposal version differs", 412)
        import json

        original = TrustedExecutionContext.model_validate_json(json.dumps(bundle["context"]))
        if identity(original) != identity(ctx):
            raise reject("completion_scope_denied", "Completion scope differs", 403)
        assert ctx.run_id is not None
        run_row = await self.records.get(ctx.principal, "runs", ctx.run_id)
        aggregate = "conversation:" + run_row.payload["conversation_id"]

        async def write(tx: RecordTransaction) -> Payload:
            # Same aggregate lock as cancellation, revision and budget dispatch.
            await self.completion.verify_bundle(bundle, ctx)
            run = await tx.load("runs", ctx.run_id or "")
            proposal = await tx.load("agent.completion.proposals", proposal_ref.id)
            contract = (await tx.load(CONTRACTS, bundle["contract_ref"]["id"])).payload
            report = (await tx.load(REPORTS, bundle["report_ref"]["id"])).payload
            validate_contract("DeliveryProposal", proposal.payload)
            expected = proposal.payload["run_ref"]
            if meta.expected_revision != run.revision or expected["version"] != str(run.revision):
                raise StoreConflict()
            if run.payload["status"] not in (
                "preparing",
                "running",
                "verifying",
                "waiting_for_user",
            ):
                raise reject("completion_state_denied", "Run cannot accept completion", 409)
            if (
                proposal.payload["outcome"] != "succeeded"
                or report["outcome"] != report_outcome(contract, report)
                or report["outcome"] != "succeeded"
            ):
                raise reject(
                    "completion_checks_incomplete", "Required checks are not all passed", 409
                )
            if proposal.payload["unresolved_effect_refs"]:
                raise reject("completion_effect_unknown", "External effects are unresolved", 409)
            ledger = await tx.load("budget.ledgers", ctx.run_id or "")
            if ledger.payload["cancel_requested"]:
                raise reject("completion_cancelled", "Run is cancelled", 409)
            if any(
                Decimal(str(v)) != 0
                for k, v in ledger.payload["held"].items()
                if k not in ("currency", "money")
            ):
                raise reject(
                    "completion_budget_active", "Pending reservations need reconciliation", 409
                )
            # Provider billing may remain pending after a known completed call;
            # preserve the money hold. Any still executable reservation blocks.
            accounts = tuple(
                await tx.session.scalars(
                    select(RecordRow).where(
                        RecordRow.principal_id == ctx.principal.id,
                        RecordRow.namespace == "budget.accounting",
                        RecordRow.deleted.is_(False),
                        RecordRow.payload["run_id"].as_string() == ctx.run_id,
                    )
                )
            )
            for account in accounts:
                reservation = await tx.load("budget.reservations", account.resource_id)
                if reservation.payload["status"] not in (
                    "settled",
                    "partially_settled",
                    "released",
                ):
                    raise reject("completion_budget_active", "Reservation remains executable", 409)
            root = await tx.load("agent.loop.states", bundle["instance_id"])
            if root.payload.get("active_operation_ref"):
                raise reject(
                    "completion_agent_active", "Finish the original Agent operation first", 409
                )
            unresolved = await tx.session.scalar(
                select(RecordRow.resource_id)
                .where(
                    RecordRow.principal_id == ctx.principal.id,
                    RecordRow.namespace == "model.invocations",
                    RecordRow.deleted.is_(False),
                    RecordRow.payload["run_id"].as_string() == ctx.run_id,
                    (RecordRow.payload["state"].as_string() != "finished")
                    | (
                        RecordRow.payload["result"]["failure"]["category"].as_string()
                        == "unknown_effect"
                    ),
                )
                .limit(1)
            )
            if unresolved:
                raise reject(
                    "completion_effect_unknown", "Original model invocation is unresolved", 409
                )
            contexts = list(
                await tx.session.scalars(
                    select(RecordRow).where(
                        RecordRow.principal_id == ctx.principal.id,
                        RecordRow.namespace == "tool.contexts",
                        RecordRow.deleted.is_(False),
                        RecordRow.payload["run_id"].as_string() == ctx.run_id,
                    )
                )
            )
            if sorted(c.resource_id for c in contexts) != bundle.get("tool_activity_ids", []):
                raise reject(
                    "completion_activity_changed",
                    "Recorded Tool action inventory changed after review",
                    412,
                )
            for context in contexts:
                try:
                    await tx.load("tool.dispatch.intents", context.resource_id)
                except StoreMissing:
                    continue
                effect = await tx.load("tool.effects", context.resource_id)
                if effect.payload["state"] != "confirmed":
                    raise reject(
                        "completion_effect_unknown",
                        "Original tool effect needs reconciliation",
                        409,
                    )
            if contract.get("acceptance_required", False):
                try:
                    acceptance = await tx.load("run.completion.acceptance", bundle["id"])
                except StoreMissing:
                    raise reject(
                        "completion_user_acceptance_required",
                        "Await authenticated user acceptance",
                        409,
                    ) from None
                expected_bundle = row_pin("content", bundle["id"], bundle).wire()
                if (
                    acceptance.payload["bundle_ref"] != expected_bundle
                    or acceptance.payload["principal"] != ctx.principal.wire()
                    or acceptance.payload["decision"] != "accept"
                ):
                    raise reject(
                        "completion_user_acceptance_required",
                        "User has not accepted this delivery",
                        409,
                    )
            # Re-read authoritative versions in this commit transaction.
            frame = await tx.load("intent.frames", ctx.task_id or "")
            inputs = await tx.load("run.input_sets", ctx.run_id or "")
            if (
                str(frame.revision) != bundle["frame_ref"]["version"]
                or frame.payload.get("input_revision") != inputs.revision
            ):
                raise reject("completion_frame_changed", "Task changed before terminal commit", 412)
            base = run.revision
            value = {
                **run.payload,
                "revision": base + 1,
                "status": "completed",
                "outcome": "succeeded",
                "ended_at": timestamp(),
            }
            await tx.write("runs", run.resource_id, "RunRecord", value, base)
            task = await tx.load("tasks", run.payload["task_id"])
            artifacts = list(task.payload["artifact_refs"])
            if bundle["artifact_ref"] not in artifacts:
                artifacts.append(bundle["artifact_ref"])
            task_value = {
                **task.payload,
                "revision": task.revision + 1,
                "artifact_refs": artifacts,
                "active_run_refs": [
                    r for r in task.payload["active_run_refs"] if r["id"] != ctx.run_id
                ],
            }
            await tx.write("tasks", task.resource_id, "TaskRecord", task_value, task.revision)
            await tx.emit(
                value["conversation_id"],
                "run.updated",
                value,
                base_revision=base,
                result_revision=base + 1,
            )
            return value

        async def replay(value: Payload) -> None:
            current = await self.records.get(ctx.principal, "runs", ctx.run_id or "")
            if current.payload != value or value["status"] != "completed":
                raise reject(
                    "completion_replay_changed", "Committed completion no longer matches", 412
                )

        # The transaction returns an immutable original result on idempotent replay.
        result = await self.transactions.execute(
            ctx.principal,
            aggregate,
            meta,
            {
                "action": "complete",
                "proposal_ref": proposal_ref.wire(),
                "context": ctx.wire(),
                "expected": meta.expected_revision,
            },
            write,
        )
        await replay(result)
        return result
