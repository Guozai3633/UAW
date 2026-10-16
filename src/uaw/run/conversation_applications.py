"""Durable evidence that the actual original model consumed current input patches."""

from typing import Any

from uaw.agent.contracts import identifier
from uaw.agent.conversation import DECISIONS
from uaw.agent.sources import check_pin
from uaw.infrastructure.db.records import PostgresRecordStore, parameter_hash
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore, timestamp
from uaw.run.conversation_control import PATCHES, ConversationControls
from uaw.run.tool_sources import reference
from uaw.shared.contracts import Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract

Payload = dict[str, Any]
APPLICATIONS = "run.conversation.applications"


def input_identity(value: Payload) -> tuple[str, str, str]:
    return value["kind"], value["id"], value["version"]


class ConversationApplications:
    def __init__(self, records: PostgresRecordStore) -> None:
        self.records = records
        self.controls = ConversationControls(records)
        self.transactions = TransactionalStore(records.database)

    async def consume(self, output_ref: Ref, ctx: TrustedExecutionContext) -> Payload:
        if not ctx.run_id or not ctx.task_id:
            raise reject("conversation_application_scope", "Original Run and task required", 403)
        key = identifier("input-application-", {"run": ctx.run_id, "attempt": ctx.attempt_id})

        async def commit(tx: RecordTransaction) -> Payload:
            run = await self.controls.owned(tx, ctx.principal, ctx.run_id or "")
            state = await tx.load("run.input_sets", run["id"])
            ledger = await tx.load("budget.ledgers", run["id"])
            if (
                ledger.payload["cancel_requested"]
                or run["status"] not in ("preparing", "running", "verifying", "waiting_for_user")
                or run["task_id"] != ctx.task_id
                or run["conversation_id"] != ctx.conversation_id
                or ctx.scope.task_id != ctx.task_id
                or ctx.scope.conversation_id != ctx.conversation_id
            ):
                raise reject(
                    "conversation_application_stale", "Current task cannot apply this input", 412
                )
            invocation = await tx.load("model.invocations", ctx.attempt_id)
            output = await tx.load("model.outputs", output_ref.id)
            decision = await tx.load(DECISIONS, ctx.attempt_id)
            check_pin(output_ref, "content", output.resource_id, output.revision, output.payload)
            operation_id = identifier(
                "agent-op-",
                {
                    "agent": run.get("root_agent_ref", {}).get("id"),
                    "operation": ctx.operation_id,
                },
            )
            operation = await tx.load("agent.loop.operations", operation_id)
            request = invocation.payload["request"]
            context_ref = request["context_snapshot_ref"]
            snapshot = await tx.load("context.snapshots", context_ref["id"])
            binding = await tx.load("context.conversation.bindings", context_ref["id"])
            preparation = await tx.load("agent.conversation.preparations", context_ref["id"])
            for row, schema in (
                (invocation, "ModelInvocation"),
                (output, "ModelOutput"),
                (decision, "FirstDecisionRecord"),
                (operation, "AgentLoopOperation"),
                (snapshot, "ContextSnapshot"),
                (preparation, "AgentContextPreparation"),
            ):
                if row.schema_name != schema:
                    raise reject(
                        "conversation_application_unproven", "Original schema differs", 412
                    )
                validate_contract(schema, row.payload)
            check_pin(
                Ref.model_validate(context_ref),
                "context",
                snapshot.resource_id,
                snapshot.revision,
                snapshot.payload,
            )
            source_refs = [state.payload["original_input_ref"], *state.payload["patch_refs"]]
            actual_refs = snapshot.payload["manifest"]["input_refs"]
            if (
                state.revision <= 1
                or not state.payload["patch_refs"]
                or snapshot.payload["epoch"] != state.revision
                or preparation.payload["request"]["expected_epoch"] != state.revision
                or preparation.payload["context"] != ctx.wire()
                or binding.payload
                != {
                    "snapshot_ref": context_ref,
                    "run_id": run["id"],
                    "conversation_id": run["conversation_id"],
                }
                or not {input_identity(ref) for ref in source_refs}
                <= {input_identity(ref) for ref in actual_refs}
                or invocation.payload["state"] != "finished"
                or invocation.payload["run_id"] != run["id"]
                or invocation.payload["operation_id"] != ctx.operation_id
                or invocation.payload["trace_id"] != ctx.trace_id
                or invocation.payload["request_hash"]
                != parameter_hash({"request": request, "context": ctx.wire()})
                or invocation.payload.get("result", {}).get("kind") != "ok"
                or invocation.payload["result"]["payload"] != output.payload
                or invocation.payload["result"]["output_refs"] != [output_ref.wire()]
                or output.payload["attempt_id"] != ctx.attempt_id
                or decision.payload["input_revision"] != state.revision
                or decision.payload["run_ref"]["id"] != run["id"]
                or decision.payload["model_output_ref"] != output_ref.wire()
                or decision.payload["attempt_id"] != ctx.attempt_id
                or ctx.model_policy_ref is None
                or decision.payload["model_policy_ref"] != ctx.model_policy_ref.wire()
                or decision.payload["decision"] != output.payload["structured_data"]
                or operation.payload["context"] != ctx.wire()
                or operation.payload["model_request"] != request
                or operation.payload.get("snapshot_ref") != context_ref
                or operation.payload["context_epoch"] != state.revision
                or operation.payload["phase"] not in ("prepared", "decided", "waiting", "finished")
            ):
                raise reject(
                    "conversation_application_unproven",
                    "Actual model input consumption differs",
                    412,
                )
            for pin in source_refs:
                row = await tx.load("inputs", pin["id"])
                check_pin(
                    Ref.model_validate(pin), "input", row.resource_id, row.revision, row.payload
                )
                if row.payload["conversation_id"] != run["conversation_id"]:
                    raise reject("conversation_application_unproven", "Input owner differs", 412)
            patches = await self.controls.matching(tx, PATCHES, run["id"])
            patches.sort(key=lambda row: row.payload["input_revision"])
            if len(patches) != len(state.payload["patch_refs"]):
                raise reject(
                    "conversation_application_unproven", "Actual patch inventory differs", 412
                )
            now = timestamp()
            applied = []
            for patch in patches:
                if (
                    patch.payload["input_ref"] not in state.payload["patch_refs"]
                    or patch.payload["input_revision"] > state.revision
                    or patch.payload["state"] not in ("accepted", "applied")
                ):
                    raise reject("conversation_application_unproven", "Patch sources changed", 412)
                if patch.payload["state"] == "accepted":
                    applied.append(patch.payload["input_ref"])
                    await tx.write(
                        PATCHES,
                        patch.resource_id,
                        "RunInputPatch",
                        {
                            **patch.payload,
                            "state": "applied",
                            "applied_at": now,
                        },
                        patch.revision,
                    )
            if not applied:
                return {}
            application = {
                "protocol": "conversation-v1",
                "run_id": run["id"],
                "input_revision": state.revision,
                "attempt_id": ctx.attempt_id,
                "context_snapshot_ref": context_ref,
                "model_output_ref": output_ref.wire(),
                "decision_record_ref": reference(
                    "content", decision.resource_id, decision.revision, decision.payload
                ).wire(),
                "source_input_refs": source_refs,
                "patch_input_refs": applied,
                "applied_at": now,
            }
            await tx.write(APPLICATIONS, key, "RunInputApplication", application)
            changed = {**run, "revision": run["revision"] + 1}
            await tx.write("runs", run["id"], "RunRecord", changed, run["revision"])
            await tx.emit(
                run["conversation_id"],
                "run.updated",
                changed,
                base_revision=run["revision"],
                result_revision=changed["revision"],
            )
            return application

        return await self.transactions.execute(
            ctx.principal,
            await self.controls.aggregate(ctx.principal, ctx.run_id),
            RequestMeta(request_id=key, schema_version="0.1"),
            {"context": ctx.wire(), "output_ref": output_ref.wire()},
            commit,
        )
