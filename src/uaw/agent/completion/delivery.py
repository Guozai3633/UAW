"""Persist real artifacts, requirement verdicts and an immutable delivery bundle."""

from uaw.agent.completion.activity import tool_activity
from uaw.agent.completion.contracts import contract_from_frame, report_outcome
from uaw.agent.completion.evidence import (
    CompletionEvidence,
    EvidenceRead,
    check,
    checked_reading,
    external_links,
)
from uaw.agent.completion.semantic import SemanticVerifier
from uaw.agent.contracts import Payload, identifier, identity
from uaw.agent.ports import AgentObservationPort
from uaw.agent.repository import AgentRepository
from uaw.agent.sources import check_pin
from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore, timestamp
from uaw.model.evaluation_inputs import EvaluationSource
from uaw.shared.contracts import Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing
from uaw.workspace.artifact_repository import ARTIFACTS
from uaw.workspace.artifacts import TextArtifacts

BUNDLES = "agent.completion.bundles"
CONTRACTS = "agent.completion.contracts"
REPORTS = "agent.completion.reports"
PROPOSALS = "agent.completion.proposals"


def row_pin(kind: str, key: str, value: Payload) -> Ref:
    return Ref(kind=kind, id=key, version="1", content_hash=parameter_hash(value))


class CompletionCoordinator:
    def __init__(
        self,
        agents: AgentRepository,
        artifacts: TextArtifacts,
        semantic: SemanticVerifier,
        *,
        read_evidence: EvidenceRead | None = None,
        observations: AgentObservationPort | None = None,
        acceptance_required: bool = False,
    ) -> None:
        self.agents, self.artifacts, self.semantic = agents, artifacts, semantic
        self.records = agents.store
        self.transactions = TransactionalStore(self.records.database)
        self.read_evidence, self.acceptance_required = read_evidence, acceptance_required
        self.observations = observations

    async def bundle(self, ref: Ref, ctx: TrustedExecutionContext) -> Payload:
        row = await self.records.get(ctx.principal, BUNDLES, ref.id)
        check_pin(ref, "content", row.resource_id, row.revision, row.payload)
        validate_contract("CompletionBundle", row.payload)
        import json

        original = TrustedExecutionContext.model_validate_json(json.dumps(row.payload["context"]))
        if identity(original) != identity(ctx):
            raise reject("completion_scope_denied", "Bundle belongs to another session/Run", 403)
        return row.payload

    async def verify_bundle(self, value: Payload, ctx: TrustedExecutionContext) -> None:
        view = await self.agents.sources.current(ctx)
        check_pin(
            Ref.model_validate(value["frame_ref"]),
            "task_frame",
            view.frame["task_id"],
            view.frame["revision"],
            view.frame,
        )
        for source in value["source_pins"]:
            pin = Ref.model_validate(source["ref"])
            row = await self.records.get(ctx.principal, source["namespace"], pin.id)
            check_pin(pin, pin.kind, row.resource_id, row.revision, row.payload)
            if row.schema_name != source["schema_name"]:
                raise reject("completion_source_changed", "Completion source schema changed", 412)
        _, _, binding = await self.artifacts.repository.read(
            Ref.model_validate(value["artifact_ref"]), ctx
        )
        for ref in binding["observation_refs"]:
            if self.observations is None:
                raise CapabilityUnavailable("completion.actual_tool_observations")
            await self.observations.read(Ref.model_validate(ref), ctx)
        if self.read_evidence is not None:
            for ref in view.frame["evidence_refs"]:
                pin = Ref.model_validate(ref)
                checked_reading(pin, await self.read_evidence(pin, ctx))
        elif view.frame["evidence_refs"]:
            raise CapabilityUnavailable("completion.actual_evidence_reader")
        if (await self.agents.sources.current(ctx)).frame != view.frame:
            raise reject("completion_frame_changed", "Task changed before delivery", 412)

    async def propose(
        self, instance_ref: Ref, model_result: Payload, ctx: TrustedExecutionContext
    ) -> Ref:
        instance, bound, state = await self.agents.owned(instance_ref.id, ctx)
        view = await self.agents.sources.current(ctx)
        if bound.role_ref != view.role_ref:
            raise reject("completion_role_changed", "Root role changed", 412)
        op_id = identifier("agent-op-", {"agent": instance.id, "operation": ctx.operation_id})
        operation = await self.agents.operation(op_id, ctx)
        if (
            operation.context != ctx
            or operation.model_result != model_result
            or operation.phase not in ("decided", "finished")
        ):
            raise reject(
                "completion_model_unowned",
                "Proposal needs its original decided Agent operation",
                403,
            )
        check_pin(
            Ref.model_validate(operation.request["current_frame_ref"]),
            "task_frame",
            view.frame["task_id"],
            view.frame["revision"],
            view.frame,
        )
        key = identifier("completion-", {"operation": op_id})
        try:
            previous = await self.records.get(ctx.principal, BUNDLES, key)
        except StoreMissing:
            previous = None
        if previous is not None:
            value = await self.bundle(row_pin("content", key, previous.payload), ctx)
            await self.verify_bundle(value, ctx)
            return Ref.model_validate(value["proposal_ref"])
        if model_result["kind"] != "ok" or len(model_result["output_refs"]) != 1:
            raise reject("completion_output_missing", "No actual model output", 412)
        output = Ref.model_validate(model_result["output_refs"][0])
        model_row = await self.records.get(ctx.principal, "model.outputs", output.id)
        check_pin(output, "content", model_row.resource_id, model_row.revision, model_row.payload)
        if model_row.payload != model_result["payload"]:
            raise reject("completion_model_unowned", "Model result differs from actual output", 412)
        observations = tuple(Ref.model_validate(r) for r in operation.request["observations"])
        artifact = await self.artifacts.from_model(output, observations, ctx)
        value, text, _ = await self.artifacts.repository.read(artifact, ctx)
        contract = contract_from_frame(view.frame, acceptance_required=self.acceptance_required)
        contract_id = identifier(
            "contract-",
            {"run": ctx.run_id, "frame": view.frame, "acceptance": self.acceptance_required},
        )
        contract_ref = row_pin("content", contract_id, contract)
        data: Payload = {
            "artifact": {
                "id": "artifact",
                "ref": artifact.wire(),
                "text": text,
                "format_kind": value["format_kind"],
                "media_type": value["media_type"],
            },
            "sources": [],
            "observations": [],
        }
        offered = {"artifact": artifact}
        pins = [
            EvaluationSource(ARTIFACTS, artifact, "ArtifactRecord"),
            EvaluationSource("model.outputs", output, "ModelOutput"),
        ]
        source_refs = [view.frame["original_input_ref"], *view.frame["patch_refs"]]
        for index, ref in enumerate(source_refs):
            row = await self.records.get(ctx.principal, "inputs", ref["id"])
            check_pin(Ref.model_validate(ref), "input", row.resource_id, row.revision, row.payload)
            pin = Ref(
                kind="input",
                id=row.resource_id,
                version=str(row.revision),
                content_hash=parameter_hash(row.payload),
            )
            offered[f"input-{index}"] = pin
            pins.append(EvaluationSource("inputs", pin, "InputRecord"))
            data["sources"].append(
                {"id": f"input-{index}", "ref": ref, "text": row.payload["text"]}
            )
        for index, ref in enumerate(view.frame["evidence_refs"]):
            if self.read_evidence is None:
                raise CapabilityUnavailable("completion.actual_evidence_reader")
            reading = await self.read_evidence(Ref.model_validate(ref), ctx)
            checked_reading(Ref.model_validate(ref), reading)
            offered[f"source-{index}"] = reading.ref
            data["sources"].append(
                {"id": f"source-{index}", "ref": reading.ref.wire(), "text": reading.text}
            )
        for index, ref in enumerate(observations):
            if self.observations is None:
                raise CapabilityUnavailable("completion.actual_tool_observations")
            observed = await self.observations.read(ref, ctx)
            row = await self.records.get(ctx.principal, "agent.observations", ref.id)
            check_pin(ref, "content", row.resource_id, row.revision, row.payload)
            if row.payload != observed:
                raise reject(
                    "completion_observation_unowned", "Observation belongs to another Run", 403
                )
            offered[f"observation-{index}"] = ref
            pins.append(EvaluationSource(row.namespace, ref, row.schema_name))
            data["observations"].append(
                {"id": f"observation-{index}", "ref": ref.wire(), "result": row.payload["result"]}
            )
        activity, activity_pins, activity_offered, activity_ids = await tool_activity(
            self.records, ctx
        )
        data["tool_activity"] = activity
        pins.extend(activity_pins)
        offered.update(activity_offered)
        checks = [
            check(
                "artifact-bytes",
                "structure",
                "passed",
                artifact,
                (artifact,),
                "Actual UTF-8 blob, hash, size and provenance checked",
            ),
            check(
                "fixed-sources",
                "reference",
                "passed",
                artifact,
                tuple(offered.values()),
                "Actual owned source versions read",
            ),
        ]
        links = external_links(text)
        if links:
            checks.append(
                check(
                    "unresolved-web-links",
                    "reference",
                    "not_run",
                    artifact,
                    (),
                    "Live web link validation is unavailable",
                )
            )
        if view.frame["unresolved"]:
            checks.append(
                check(
                    "unresolved-task",
                    "semantic",
                    "blocked",
                    artifact,
                    (),
                    "Task still contains unresolved questions",
                )
            )
        for spec in contract["outputs"]:
            # OutputSpec.kind is free text, not a file-format enum. Content and
            # requested deliverable compatibility are reviewed per requirement.
            if spec["required"] and "schema_ref" in spec:
                checks.append(
                    check(
                        "output-" + spec["id"],
                        "structure",
                        "blocked",
                        artifact,
                        (),
                        "Required output type/schema not implemented",
                    )
                )
        for req in contract["requirements"]:
            for kind in req.get("evidence_kinds", []):
                if kind not in ("structure", "reference", "semantic"):
                    checks.append(
                        check(
                            identifier("check-", {"requirement": req["id"], "kind": kind}),
                            "command" if kind == "command" else "manual",
                            "not_run",
                            artifact,
                            (),
                            "No actual execution/manual evidence source",
                            (req["id"],),
                        )
                    )
        evidence = CompletionEvidence(data, offered, tuple(pins), tuple(checks))
        verdicts, reviewed = await self.semantic.verify(contract, artifact, evidence, ctx)
        report = {
            "id": key,
            "contract_ref": contract_ref.wire(),
            "target_refs": [artifact.wire()],
            "checks": checks,
            "verdicts": verdicts,
            "outcome": "blocked",
            "limitations": reviewed.data["limitations"],
            "reviewer_model_config_ref": {
                "kind": "configuration",
                "id": reviewed.output["actual_config"]["model_id"],
                "version": str(reviewed.output["actual_config"]["catalog_revision"]),
            },
            "created_at": timestamp(),
        }
        report["outcome"] = report_outcome(contract, report)
        report_ref = row_pin("verification", key, report)
        proposal = {
            "run_ref": {"kind": "run", "id": view.run["id"], "version": str(view.run["revision"])},
            "contract_ref": contract_ref.wire(),
            "outcome": report["outcome"],
            "artifact_refs": [artifact.wire()],
            "report_ref": report_ref.wire(),
            "unresolved_effect_refs": [],
            "created_at": timestamp(),
        }
        proposal_ref = row_pin("content", key, proposal)
        bundle = {
            "id": key,
            "context": ctx.wire(),
            "instance_id": instance.id,
            "frame_ref": {
                "kind": "task_frame",
                "id": view.frame["task_id"],
                "version": str(view.frame["revision"]),
                "content_hash": parameter_hash(view.frame),
            },
            "contract_ref": contract_ref.wire(),
            "artifact_ref": artifact.wire(),
            "report_ref": report_ref.wire(),
            "proposal_ref": proposal_ref.wire(),
            "tool_activity_ids": list(activity_ids),
            "source_pins": [
                p.wire()
                for p in (
                    *pins,
                    EvaluationSource("model.outputs", reviewed.output_ref, "ModelOutput"),
                    EvaluationSource(CONTRACTS, contract_ref, "Contract"),
                    EvaluationSource(REPORTS, report_ref, "VerificationReport"),
                    EvaluationSource(PROPOSALS, proposal_ref, "DeliveryProposal"),
                )
            ],
        }

        async def verify() -> None:
            current = await self.agents.sources.current(ctx)
            if current.frame != view.frame or current.run != view.run:
                raise reject(
                    "completion_source_changed", "Run/frame changed during verification", 412
                )
            await self.semantic.evaluator.inputs.guard(reviewed.context)
            await self.artifacts.repository.read(artifact, ctx)

        async def write(tx: RecordTransaction) -> Payload:
            try:
                prior = await tx.load(CONTRACTS, contract_id)
            except StoreMissing:
                prior = None
            if prior is None:
                await tx.write(CONTRACTS, contract_id, "Contract", contract)
            elif prior.payload != contract:
                raise reject("completion_contract_conflict", "Contract changed", 409)
            await tx.write(REPORTS, key, "VerificationReport", report)
            await tx.write(PROPOSALS, key, "DeliveryProposal", proposal)
            await tx.write(BUNDLES, key, "CompletionBundle", bundle)
            return proposal_ref.wire()

        result = await self.transactions.execute(
            ctx.principal,
            "completion:" + key,
            RequestMeta(request_id="publish", schema_version="0.1"),
            {"bundle": bundle},
            write,
            verify=verify,
        )
        await self.verify_bundle(bundle, ctx)
        return Ref.model_validate(result)
