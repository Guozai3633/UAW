"""LangGraph local loop; non-null fresh input, UAW gates, JSON-only checkpoints."""

import json
import math
from typing import Any, TypedDict

from uaw.agent.contracts import Payload, identifier, identity
from uaw.agent.facade import AgentRuntime
from uaw.agent.repository import pin
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject


def json_value(value: Any, depth: int = 0) -> None:
    if depth > 32:
        raise ValueError("Checkpoint exceeds JSON depth")
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) is list:
        for item in value:
            json_value(item, depth + 1)
        return
    if type(value) is dict and all(type(key) is str for key in value):
        for item in value.values():
            json_value(item, depth + 1)
        return
    raise ValueError("Only JSON primitives can enter a checkpoint")


class JsonCheckpointSerializer:
    def dumps_typed(self, value: Any) -> tuple[str, bytes]:
        json_value(value)
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
        if len(encoded) > 2097152:
            raise ValueError("Checkpoint exceeds 2MiB")
        return "json", encoded

    def loads_typed(self, data: tuple[str, bytes]) -> Any:
        kind, value = data
        if kind != "json" or len(value) > 2097152:
            raise ValueError("Only bounded JSON checkpoints are readable")
        result = json.loads(value)
        json_value(result)
        return result


class GraphState(TypedDict):
    instance_ref: Payload
    cycles: int
    result: Payload


class LangGraphAgentEngine:
    def __init__(self, runtime: AgentRuntime, *, checkpointer: Any) -> None:
        if checkpointer is None:
            raise CapabilityUnavailable("agent.local_checkpoint_backend")
        self.runtime, self.checkpointer = runtime, checkpointer

    async def run(
        self, instance_ref: Ref, ctx: TrustedExecutionContext, *, max_cycles: int = 8
    ) -> Payload:
        if type(max_cycles) is not int or not 1 <= max_cycles <= 32:
            raise reject("agent_cycle_limit_invalid", "Cycles must be 1..32")
        from langgraph.graph import END, START, StateGraph

        repo = self.runtime.loop.repository
        await repo.current(instance_ref, ctx)

        async def cycle(state: GraphState) -> GraphState:
            current_ref = Ref.model_validate(state["instance_ref"])
            _, _, current, view = await repo.current(current_ref, ctx)
            call_ctx = ctx.model_copy(
                update={
                    "operation_id": identifier(
                        "agent-cycle-", {"agent": current_ref.id, "step": current.steps + 1}
                    ),
                    "attempt_id": identifier(
                        "model-attempt-", {"agent": current_ref.id, "step": current.steps + 1}
                    ),
                    "trace_id": identifier(
                        "agent-trace-", {"agent": current_ref.id, "step": current.steps + 1}
                    ),
                }
            )
            result = await self.runtime.step(
                {
                    "instance_ref": current_ref.wire(),
                    "observations": [r.wire() for r in current.observation_refs],
                    "current_frame_ref": {
                        "kind": "task_frame",
                        "id": view.frame["task_id"],
                        "version": str(view.frame["revision"]),
                    },
                    "remaining_budget": view.remaining_budget,
                },
                call_ctx,
            )
            instance, _, _ = await repo.owned(current_ref.id, ctx)
            return {
                "instance_ref": pin("agent_instance", instance.wire()).wire(),
                "cycles": state["cycles"] + 1,
                "result": result,
            }

        def route(state: GraphState) -> str:
            result = state["result"]
            if (
                state["cycles"] < max_cycles
                and result["kind"] == "ok"
                and result["payload"]["action"] == "call_tools"
            ):
                return "cycle"
            return END

        graph = StateGraph(GraphState)
        graph.add_node("cycle", cycle)
        graph.add_edge(START, "cycle")
        graph.add_conditional_edges("cycle", route, {"cycle": "cycle", END: END})
        compiled = graph.compile(checkpointer=self.checkpointer)
        thread = identifier(
            "graph-",
            {"owner": identity(ctx), "agent": instance_ref.wire(), "operation": ctx.operation_id},
        )
        state = await compiled.ainvoke(
            {"instance_ref": instance_ref.wire(), "cycles": 0, "result": {}},
            {
                "configurable": {"thread_id": thread, "checkpoint_ns": ""},
                "recursion_limit": max_cycles + 4,
            },
        )
        # END is an execution boundary, never proof of Run completion. UAW state
        # and actual side-effect receipts remain authoritative after restart.
        return dict(state["result"])
