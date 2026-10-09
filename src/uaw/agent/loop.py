"""Bounded decisions with persisted original attempts and explicit recovery."""

import json

from jsonschema import ValidationError

from uaw.agent.contracts import (
    AgentStepRequest,
    LoopOperation,
    Payload,
    identifier,
    validate_decision,
)
from uaw.agent.ports import (
    AgentCompletionPort,
    AgentContextPort,
    AgentModelPort,
    AgentObservationPort,
)
from uaw.agent.repository import AgentRepository
from uaw.agent.sources import check_pin
from uaw.agent.tool_access import AgentToolAccess
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, error_result, reject
from uaw.shared.ports import ToolPort
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing


class AgentLoop:
    def __init__(
        self,
        repository: AgentRepository,
        contexts: AgentContextPort,
        models: AgentModelPort,
        observations: AgentObservationPort,
        *,
        tools: ToolPort | None,
        completion: AgentCompletionPort | None = None,
        tool_access: AgentToolAccess | None = None,
    ) -> None:
        self.repository, self.contexts, self.models = repository, contexts, models
        self.observations, self.tools, self.completion = observations, tools, completion
        self.tool_access = tool_access

    async def step(self, request: Payload, ctx: TrustedExecutionContext) -> Payload:
        validate_contract("AgentStepRequest", request)
        parsed = AgentStepRequest.model_validate_json(json.dumps(request))
        key = identifier(
            "agent-op-", {"agent": parsed.instance_ref.id, "operation": ctx.operation_id}
        )
        try:
            previous = await self.repository.operation(key, ctx)
        except StoreMissing:
            previous = None
        if previous is not None:
            if previous.request != request or previous.context != ctx:
                raise reject("agent_idempotency_conflict", "Original request/attempt changed", 409)
            await self.verify(previous, ctx)
            if previous.phase in ("finished", "failed") and previous.result is not None:
                if previous.model_result and previous.model_result["kind"] == "ok":
                    await self.models.read(previous.model_result, previous.context)
                return previous.result
            raise reject("agent_step_in_progress", "Use explicit original-operation recovery", 409)
        operation, owned = await self.repository.claim(request, ctx)
        if not owned:
            raise reject("agent_step_in_progress", "Another caller owns the original step", 409)
        return await self.advance(operation, ctx)

    async def verify(self, operation: LoopOperation, ctx: TrustedExecutionContext) -> None:
        _, binding, _ = await self.repository.owned(operation.instance_id, ctx)
        current = await self.repository.sources.current(ctx)
        requested = Ref.model_validate(operation.request["current_frame_ref"])
        check_pin(
            requested,
            "task_frame",
            current.frame["task_id"],
            current.frame["revision"],
            current.frame,
        )
        if current.role_ref != binding.role_ref:
            raise reject("agent_role_changed", "Bound role changed before next action", 412)

    async def resume(self, operation_ref: Ref, ctx: TrustedExecutionContext) -> Payload:
        operation = await self.repository.operation(operation_ref.id, ctx)
        check_pin(operation_ref, "content", operation.id, operation.revision, operation.wire())
        await self.verify(operation, ctx)
        if operation.phase in ("finished", "failed") and operation.result is not None:
            if operation.model_result and operation.model_result["kind"] == "ok":
                await self.models.read(operation.model_result, operation.context)
            return operation.result
        # Recover only this persisted original context/request. No new model or
        # Tool attempt, changed arguments, or automatic old graph replay.
        return await self.advance(operation, operation.context)

    async def advance(self, operation: LoopOperation, ctx: TrustedExecutionContext) -> Payload:
        repo = self.repository

        async def verify() -> None:
            await self.verify(operation, ctx)

        if operation.phase == "claimed":
            prepared = await self.contexts.prepare(
                operation.id,
                tuple(Ref.model_validate(r) for r in operation.request["observations"]),
                ctx,
            )
            await verify()
            request = await self.models.request(prepared.snapshot_ref, ctx)
            validate_contract("ModelCall", request)
            operation = await repo.update(
                operation,
                {
                    "phase": "prepared",
                    "snapshot_ref": prepared.snapshot_ref.wire(),
                    "context_epoch": prepared.epoch,
                    "model_request": request,
                },
                ctx,
                verify=verify,
            )
        if operation.phase == "prepared":
            await verify()
            if operation.model_request is None:
                raise reject("agent_operation_invalid", "No original model request", 412)
            result = await self.models.generate(operation.model_request, ctx)
            validate_contract("RuntimeModelruntimeGenerateResult", result)
            await verify()
            if result["kind"] != "ok":
                # The Model domain preserves the send intent/billing. An unknown
                # invocation remains active for explicit reconciliation.
                unknown = result["failure"]["category"] == "unknown_effect"
                operation = await repo.update(
                    operation,
                    {
                        "phase": "prepared" if unknown else "failed",
                        "result": result,
                    },
                    ctx,
                    verify=verify,
                    finish=not unknown,
                )
                return result
            output = await self.models.read(result, ctx)
            try:
                if output["finish_reason"] != "stop" or output["tool_calls"]:
                    raise ValueError("Only complete structured proposals are supported")
                proposal = validate_decision(output["structured_data"])
            except KeyError, TypeError, ValueError, ValidationError:
                failure = error_result(
                    reject(
                        "agent_decision_invalid",
                        "Model proposal is incomplete or inconsistent",
                        409,
                    )
                )
                await repo.update(
                    operation,
                    {"phase": "failed", "model_result": result, "result": failure},
                    ctx,
                    verify=verify,
                    finish=True,
                )
                return failure
            changes: Payload = {"phase": "decided", "model_result": result, "proposal": proposal}
            if proposal["action"] == "call_tools":
                changes["tool_context"] = ctx.model_copy(
                    update={
                        "operation_id": identifier("tool-op-", {"step": operation.id}),
                        "trace_id": identifier("tool-trace-", {"step": operation.id}),
                        "attempt_id": identifier("tool-attempt-", {"step": operation.id}),
                    }
                ).wire()
            operation = await repo.update(operation, changes, ctx, verify=verify)
        await verify()
        if operation.proposal is None or operation.model_result is None:
            raise reject("agent_operation_invalid", "No saved model decision", 412)
        model_result = operation.model_result
        await self.models.read(model_result, ctx)
        proposal = validate_decision(operation.proposal)
        result = {
            "kind": "ok",
            "output_refs": [],
            "payload": {
                "action": proposal["action"],
                "model_output_ref": operation.model_result["output_refs"][0],
                "proposed_calls": proposal["proposed_calls"],
                "instance_ref": operation.request["instance_ref"],
            },
        }
        changes = {"phase": "finished"}
        if proposal["action"] == "call_tools":
            call = proposal["proposed_calls"][0]
            tool_context = operation.tool_context
            if self.tools is None or tool_context is None:
                raise CapabilityUnavailable("agent.tool_runtime")
            if self.tool_access is not None:
                await self.tool_access.register(operation)
            tool_result = json.loads(json.dumps(await self.tools.invoke(call, tool_context)))
            validate_contract("RuntimeToolruntimeInvokeResult", tool_result)
            await verify()
            if tool_result["kind"] == "waiting" or (
                tool_result.get("failure", {}).get("category") == "unknown_effect"
            ):
                waiting = {**tool_result, "output_refs": tool_result.get("output_refs", [])}
                operation = await repo.update(
                    operation, {"phase": "waiting", "result": waiting}, ctx, verify=verify
                )
                return waiting
            observation = await self.observations.save_tool(tool_result, call, tool_context)
            changes["observation_ref"] = observation.wire()
            result["output_refs"] = [observation.wire()]
        elif proposal["action"] == "propose_completion":
            if self.completion is None:
                failure = error_result(CapabilityUnavailable("agent.current_completion_verifier"))
                await repo.update(
                    operation,
                    {"phase": "failed", "result": failure},
                    ctx,
                    verify=verify,
                    finish=True,
                )
                return failure
            delivered = await self.completion.propose(
                Ref.model_validate(operation.request["instance_ref"]), model_result, ctx
            )
            result["payload"]["completion_proposal_ref"] = delivered.wire()
            result["output_refs"] = [delivered.wire()]
        changes["result"] = result
        operation = await repo.update(operation, changes, ctx, verify=verify, finish=True)
        assert operation.result is not None
        validate_contract("RuntimeAgentruntimeStepResult", operation.result)
        return operation.result
