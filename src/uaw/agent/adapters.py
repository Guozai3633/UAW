"""Current concrete Context/Model/Tool observation adapters, injected by A."""

import json

from uaw.agent.contracts import Payload, decision_schema, frozen, identifier, identity
from uaw.agent.ports import AgentSourcePort, PreparedAgentContext
from uaw.agent.repository import meta
from uaw.agent.sources import check_pin
from uaw.context.contracts import ContextRequest, ModelToolSet, PreservationSpec, RulesRequest
from uaw.context.facade import ContextComponents
from uaw.context.registered import RegisteredContextInputs
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.model.facade import ModelFacade
from uaw.model.policy import PolicyResolver
from uaw.run.tool_sources import RunToolAccessSources, reference
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import DomainError, reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing
from uaw.tool.discovery import require_entry
from uaw.tool.registry import ToolRegistry
from uaw.tool.results import ToolResults

OBSERVATIONS = "agent.observations"


class AgentObservations:
    def __init__(
        self, store: PostgresRecordStore, sources: AgentSourcePort, *, results: ToolResults | None
    ) -> None:
        self.store, self.sources, self.results = store, sources, results

    async def save_tool(self, result: Payload, call: Payload, ctx: TrustedExecutionContext) -> Ref:
        await self.sources.current(ctx)
        validate_contract("RuntimeToolruntimeInvokeResult", result)
        validate_contract("ToolCall", call)
        if result["kind"] == "ok":
            if (
                self.results is None
                or await self.results.read_result(call["action_id"], ctx) != result
            ):
                raise reject(
                    "agent_tool_evidence_invalid", "Tool output has no current actual result", 412
                )
        value = {"context": ctx.wire(), "call": call, "result": result}
        key = identifier("observation-", {"run": ctx.run_id, "attempt": ctx.attempt_id})
        try:
            row = await self.store.get(ctx.principal, OBSERVATIONS, key)
        except StoreMissing:
            await self.store.put(
                ctx.principal,
                OBSERVATIONS,
                key,
                "AgentObservation",
                value,
                expected_revision=0,
                request_id="publish",
            )
            row = await self.store.get(ctx.principal, OBSERVATIONS, key)
        if row.schema_name != "AgentObservation" or row.payload != value or row.revision != 1:
            raise reject("agent_observation_conflict", "Original observation differs", 409)
        await self.sources.current(ctx)
        return reference("content", key, 1, value)

    async def read(self, ref: Ref, ctx: TrustedExecutionContext) -> Payload:
        await self.sources.current(ctx)
        row = await self.store.get(ctx.principal, OBSERVATIONS, ref.id)
        validate_contract("AgentObservation", row.payload)
        check_pin(ref, "content", row.resource_id, row.revision, row.payload)
        original = TrustedExecutionContext.model_validate_json(json.dumps(row.payload["context"]))
        if identity(original) != identity(ctx):
            raise reject(
                "agent_observation_denied", "Observation belongs to another scope/session", 403
            )
        result = row.payload["result"]
        if result["kind"] == "ok":
            if (
                self.results is None
                or await self.results.read_result(row.payload["call"]["action_id"], original)
                != result
            ):
                raise reject("agent_tool_evidence_invalid", "Tool source changed", 412)
        await self.sources.current(ctx)
        return frozen(row.payload)


class RegisteredAgentContexts:
    def __init__(
        self,
        inputs: RegisteredContextInputs,
        components: ContextComponents,
        sources: AgentSourcePort,
        observations: AgentObservations,
        *,
        registry: ToolRegistry,
        access: RunToolAccessSources,
        output_reserve: int = 512,
    ) -> None:
        self.inputs, self.components = inputs, components
        self.sources, self.observations = sources, observations
        self.registry, self.access, self.output_reserve = registry, access, output_reserve

    async def prepare(
        self, operation_id: str, observations: tuple[Ref, ...], ctx: TrustedExecutionContext
    ) -> PreparedAgentContext:
        view = await self.sources.current(ctx)
        rule = Ref.model_validate(view.role["instructions_ref"])
        reading = await self.inputs.read(rule, ctx)
        if reading.kind != "instruction" or reading.ref != rule:
            raise reject(
                "agent_role_instructions_missing", "Role method needs a real registered rule", 503
            )
        data: Payload = {"task_frame": view.frame, "observations": []}
        if ctx.model_policy_ref is None or ctx.run_id is None:
            raise reject("agent_context_missing", "Actual Run/model required", 403)
        for ref in observations:
            data["observations"].append(await self.observations.read(ref, ctx))
        material_ctx = ctx.model_copy(update={"operation_id": operation_id})
        material = await self.inputs.register_material(
            json.dumps(data, ensure_ascii=False, allow_nan=False, sort_keys=True),
            material_ctx,
            authenticated_service=self.inputs.controller,
            expected_revision=0,
            meta=meta("agent-material", operation_id),
        )
        access = await self.access.snapshot(ctx)
        revision, entries = self.registry.snapshot()
        tools = []
        for entry in entries:
            try:
                require_entry(entry, access)
            except DomainError:
                continue
            tools.append(entry.spec())
        if len(tools) > 64:
            raise reject(
                "agent_tool_selection_required",
                "Use a bounded trusted retriever for larger tool sets",
                503,
            )
        key = identifier("agent-context-", {"run": ctx.run_id, "operation": operation_id})
        try:
            prepared = await self.inputs.records.get(
                ctx.principal, "agent.context.preparations", key
            )
        except StoreMissing:
            prepared = None
        if prepared is not None:
            validate_contract("AgentContextPreparation", prepared.payload)
            if (
                prepared.schema_name != "AgentContextPreparation"
                or prepared.payload["context"] != ctx.wire()
            ):
                raise reject("agent_context_conflict", "Original context preparation differs", 409)
            request = ContextRequest.model_validate_json(json.dumps(prepared.payload["request"]))
            rule_selection = RulesRequest.model_validate_json(json.dumps(prepared.payload["rules"]))
            offered = ModelToolSet.model_validate_json(json.dumps(prepared.payload["tools"]))
            epoch = request.expected_epoch
        else:
            try:
                previous = await self.inputs.recipe(ctx)
                epoch = previous.request.expected_epoch
            except StoreMissing:
                epoch = 0
            request = ContextRequest(
                purpose="agent_step",
                source_refs=(material,),
                model_policy_ref=ctx.model_policy_ref,
                output_reserve=self.output_reserve,
                tool_reserve=2048,
                expected_epoch=epoch,
                preserve=PreservationSpec(
                    required_refs=(), exact_strings=(), requirement_ids=(), pending_action_refs=()
                ),
            )
            rule_selection = RulesRequest(
                scope_paths=(), user_instruction_refs=(rule,), activated_skill_refs=()
            )
            offered = ModelToolSet(run_id=ctx.run_id, tools=tuple(tools))
            value = {
                "context": ctx.wire(),
                "request": request.wire(),
                "rules": rule_selection.wire(),
                "tools": offered.wire(),
                "revision": 1,
            }
            await self.inputs.records.put(
                ctx.principal,
                "agent.context.preparations",
                key,
                "AgentContextPreparation",
                value,
                expected_revision=0,
                request_id="intent",
            )
        await self.inputs.register_recipe(
            request,
            rule_selection,
            offered,
            ctx,
            authenticated_service=self.inputs.controller,
            expected_revision=epoch,
            meta=meta("agent-recipe", operation_id),
        )
        saved = await self.inputs.recipe(ctx)
        built = await self.components.build(saved.request.wire(), ctx)
        if built["kind"] != "ok":
            from uaw.shared.contracts import Failure

            raise DomainError(Failure.model_validate_json(json.dumps(built["failure"])))
        if (
            revision != self.registry.snapshot()[0]
            or (await self.sources.current(ctx)).frame != view.frame
        ):
            raise reject(
                "agent_context_changed", "Tool catalogue/frame changed while building", 412
            )
        snapshot = Ref.model_validate(built["output_refs"][0])
        current = await self.inputs.records.get(ctx.principal, "agent.context.preparations", key)
        if "snapshot_ref" not in current.payload:
            await self.inputs.records.put(
                ctx.principal,
                current.namespace,
                key,
                "AgentContextPreparation",
                {
                    **current.payload,
                    "revision": current.revision + 1,
                    "snapshot_ref": snapshot.wire(),
                },
                expected_revision=current.revision,
                request_id="snapshot",
            )
        elif current.payload["snapshot_ref"] != snapshot.wire():
            raise reject("agent_context_conflict", "Original context snapshot differs", 409)
        return PreparedAgentContext(snapshot, built["payload"]["epoch"])


class RegisteredAgentModels:
    def __init__(
        self,
        model: ModelFacade,
        policies: PolicyResolver,
        sources: AgentSourcePort,
        *,
        max_output_tokens: int = 512,
    ) -> None:
        self.model, self.policies, self.sources = model, policies, sources
        self.max_output_tokens = max_output_tokens

    async def request(self, snapshot: Ref, ctx: TrustedExecutionContext) -> Payload:
        await self.sources.current(ctx)
        if ctx.model_policy_ref is None or ctx.run_id is None:
            raise reject("agent_context_missing", "Actual Run/model required", 403)
        row = await self.policies.store.get(
            ctx.principal, "model.policies", ctx.model_policy_ref.id
        )
        admission = (
            await self.policies.store.get(ctx.principal, "run.bindings", ctx.run_id)
        ).payload
        fixed = await self.policies.configuration.snapshot(admission["configuration_ref"])
        model = await self.policies.configuration.require_model(
            row.payload["fixed_model_id"], fixed
        )
        config = {
            "model_id": model["id"],
            "catalog_revision": model["revision"],
            "provider_ref": model["provider_ref"],
            "policy_ref": ctx.model_policy_ref.wire(),
            "max_output_tokens": min(self.max_output_tokens, model["output_limit_tokens"]),
        }
        selection = await self.policies.resolve(config, ctx)
        return {
            "context_snapshot_ref": snapshot.wire(),
            "model_config": selection.config,
            "output_protocol": "json_schema",
            "output_schema": decision_schema(),
            "attempt_id": ctx.attempt_id,
        }

    async def generate(self, request: Payload, ctx: TrustedExecutionContext) -> Payload:
        return await self.model.generate(request, ctx)

    async def read(self, result: Payload, ctx: TrustedExecutionContext) -> Payload:
        await self.sources.current(ctx)
        validate_contract("RuntimeModelruntimeGenerateResult", result)
        if result["kind"] != "ok" or len(result.get("output_refs", [])) != 1:
            raise reject("agent_model_evidence_missing", "No actual model output", 412)
        ref = Ref.model_validate(result["output_refs"][0])
        row = await self.policies.store.get(ctx.principal, "model.outputs", ref.id)
        check_pin(ref, "content", row.resource_id, row.revision, row.payload)
        if row.schema_name != "ModelOutput" or row.payload != result["payload"]:
            raise reject(
                "agent_model_evidence_invalid", "Actual output differs from proposal source", 412
            )
        invocation = await self.policies.store.get(
            ctx.principal, "model.invocations", ctx.attempt_id
        )
        if invocation.payload.get("result") != result or invocation.payload["state"] != "finished":
            raise reject(
                "agent_model_evidence_invalid",
                "Original invocation did not finish with this output",
                412,
            )
        await self.sources.current(ctx)
        return frozen(row.payload)
