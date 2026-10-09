"""One current root per Run. Creation does not call Model or launch a graph."""

from uaw.agent.contracts import (
    AgentInstance,
    AgentStartRequest,
    LoopState,
    Payload,
    RootBinding,
    identifier,
)
from uaw.agent.repository import BINDINGS, INSTANCES, STATES, AgentRepository, meta, pin
from uaw.agent.sources import check_pin
from uaw.infrastructure.db.transactions import RecordTransaction
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.stores import StoreConflict, StoreMissing


class AgentFactory:
    def __init__(self, repository: AgentRepository, *, max_steps: int = 32) -> None:
        if type(max_steps) is not int or not 1 <= max_steps <= 32:
            raise ValueError("Root step cap must be 1..32")
        self.repository = repository
        self.max_steps = max_steps

    async def create(self, request: Payload, ctx: TrustedExecutionContext) -> Payload:
        import json

        proposed = AgentStartRequest.model_validate_json(json.dumps(request))
        repo = self.repository
        view = await repo.sources.current(ctx)
        if ctx.model_policy_ref is None:
            raise reject("agent_model_missing", "Root requires the Run's fixed model", 403)
        model_policy_ref = ctx.model_policy_ref
        check_pin(
            proposed.task_frame_ref,
            "task_frame",
            view.frame["task_id"],
            view.frame["revision"],
            view.frame,
        )
        if proposed.role_profile_ref is not None and proposed.role_profile_ref != view.role_ref:
            raise reject("agent_role_denied", "Start cannot substitute the bound role", 403)
        maximum = min(self.max_steps, view.run["budget"]["max_steps"])
        if maximum < 1:
            raise reject("agent_step_limit", "No root steps available", 409, "budget")
        key = identifier("root-", {"run": view.run["id"]})
        bound = RootBinding(
            context=ctx, start_request=request, role_ref=view.role_ref, max_steps=maximum
        )

        async def verify() -> None:
            actual = await repo.sources.current(ctx)
            if actual.frame != view.frame or actual.role_ref != view.role_ref:
                raise reject("agent_source_changed", "Root sources changed", 412)

        async def write(tx: RecordTransaction) -> Payload:
            run = await tx.load("runs", view.run["id"])
            try:
                existing = await tx.load(BINDINGS, key)
            except StoreMissing:
                existing = None
            if existing is not None:
                if existing.payload != bound.wire():
                    raise StoreConflict("idempotency_conflict")
                return {"instance_id": key}
            check_pin(proposed.run_ref, "run", run.resource_id, run.revision, run.payload)
            if "root_agent_ref" in run.payload:
                raise reject("agent_root_exists", "Run already has another root", 409)
            value = AgentInstance(
                id=key,
                run_id=run.resource_id,
                status="ready",
                model_policy_ref=model_policy_ref,
                capability_policy_ref=ctx.capability_policy_ref,
                context_epoch=0,
                revision=1,
            )
            state = LoopState(
                instance_id=key,
                revision=1,
                steps=0,
                frame_ref=proposed.task_frame_ref,
                observation_refs=(),
            )
            await tx.write(BINDINGS, key, "AgentRootBinding", bound.wire())
            await tx.write(INSTANCES, key, "AgentInstance", value.wire())
            await tx.write(STATES, key, "AgentLoopState", state.wire())
            changed = {
                **run.payload,
                "revision": run.revision + 1,
                "root_agent_ref": pin("agent_instance", value.wire()).wire(),
            }
            await tx.write("runs", run.resource_id, "RunRecord", changed, run.revision)
            await tx.emit(
                ctx.scope.conversation_id or "",
                "agent.updated",
                value.wire(),
                base_revision=0,
                result_revision=1,
            )
            await verify()
            return {"instance_id": key}

        await repo.transactions.execute(
            ctx.principal,
            "conversation:" + (ctx.scope.conversation_id or ""),
            meta("create", proposed.creation_key),
            {"request": request, "identity": bound.context.wire()},
            write,
            verify,
        )
        instance, _, _ = await repo.owned(key, ctx)
        return {
            "kind": "ok",
            "payload": instance.wire(),
            "revision": instance.revision,
            "output_refs": [pin("agent_instance", instance.wire()).wire()],
        }
