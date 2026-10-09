"""Current task-frame fencing at Tool Runtime's repeated execution gates."""

import json

from uaw.agent.contracts import LoopOperation, identifier
from uaw.agent.repository import OPERATIONS, AgentRepository, pin
from uaw.agent.sources import RegisteredAgentSources, check_pin
from uaw.run.tool_sources import RunToolAccessSources
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.stores import StoreMissing
from uaw.tool.ports import ToolAccess

NAMESPACE = "agent.tool.origins"


def key(ctx: TrustedExecutionContext) -> str:
    return identifier("tool-origin-", {"run": ctx.run_id, "attempt": ctx.attempt_id})


class AgentToolAccess:
    def __init__(
        self,
        base: RunToolAccessSources,
        repository: AgentRepository,
        sources: RegisteredAgentSources,
    ) -> None:
        self.base, self.repository, self.sources = base, repository, sources

    async def register(self, operation: LoopOperation) -> None:
        ctx = operation.tool_context
        if ctx is None or operation.phase not in ("decided", "waiting"):
            raise reject("agent_tool_origin_invalid", "No original tool decision", 412)
        wanted = pin("content", operation.wire())
        try:
            row = await self.repository.store.get(ctx.principal, NAMESPACE, key(ctx))
        except StoreMissing:
            await self.repository.store.put(
                ctx.principal,
                NAMESPACE,
                key(ctx),
                "Ref",
                wanted.wire(),
                expected_revision=0,
                request_id="origin",
            )
        else:
            if row.schema_name != "Ref" or row.payload["id"] != operation.id:
                raise reject("agent_tool_origin_conflict", "Original tool step differs", 409)

    async def snapshot(self, ctx: TrustedExecutionContext) -> ToolAccess:
        access = await self.base.snapshot(ctx)
        marker = await self.repository.store.get(ctx.principal, NAMESPACE, key(ctx))
        if marker.schema_name != "Ref" or marker.revision != 1:
            raise reject(
                "agent_tool_origin_invalid", "No independently registered step origin", 403
            )
        origin = Ref.model_validate(marker.payload)
        row = await self.repository.store.get(
            ctx.principal, OPERATIONS, origin.id, revision=int(origin.version)
        )
        check_pin(origin, "content", row.resource_id, row.revision, row.payload)
        original = LoopOperation.model_validate_json(json.dumps(row.payload))
        current = await self.repository.operation(original.id, ctx)
        _, _, state = await self.repository.owned(current.instance_id, ctx)
        if (
            current.tool_context != ctx
            or original.tool_context != ctx
            or current.proposal != original.proposal
            or current.phase not in ("decided", "waiting")
            or state.active_operation_ref is None
            or state.active_operation_ref.id != current.id
        ):
            raise reject("agent_tool_origin_invalid", "Root no longer owns this tool step", 403)
        run = (await self.repository.store.get(ctx.principal, "runs", ctx.run_id or "")).payload
        frame = await self.sources.frame(ctx, run)
        check_pin(
            Ref.model_validate(original.request["current_frame_ref"]),
            "task_frame",
            frame["task_id"],
            frame["revision"],
            frame,
        )
        return access
