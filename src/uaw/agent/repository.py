"""Durable root/step CAS. A claimed operation is not permission to resend."""

import json
from collections.abc import Awaitable, Callable

from uaw.agent.contracts import (
    AgentInstance,
    LoopOperation,
    LoopState,
    Payload,
    RootBinding,
    identifier,
    identity,
)
from uaw.agent.ports import AgentSourcePort, AgentView
from uaw.agent.sources import check_pin
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore
from uaw.run.tool_sources import reference
from uaw.shared.contracts import Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import error_result, reject
from uaw.shared.stores import StoreConflict

INSTANCES = "agent.instances"
BINDINGS = "agent.root.bindings"
STATES = "agent.loop.states"
OPERATIONS = "agent.loop.operations"


def meta(action: str, key: str) -> RequestMeta:
    return RequestMeta(request_id=identifier(action + "-", {"key": key}), schema_version="0.1")


def pin(kind: str, value: Payload) -> Ref:
    return reference(kind, value["id"], value["revision"], value)


class AgentRepository:
    def __init__(self, store: PostgresRecordStore, sources: AgentSourcePort) -> None:
        self.store, self.sources = store, sources
        self.transactions = TransactionalStore(store.database)

    async def sync_cancellation(self, key: str, ctx: TrustedExecutionContext) -> None:
        instance, _, _ = await self.owned(key, ctx)
        if not await self.sources.cancelled(ctx):
            return

        async def write(tx: RecordTransaction) -> Payload:
            row = await tx.load(INSTANCES, key)
            if row.payload["status"] != "cancelled":
                before = row.revision
                value = {**row.payload, "status": "cancelled", "revision": before + 1}
                await tx.write(INSTANCES, key, "AgentInstance", value, before)
                await tx.emit(
                    ctx.scope.conversation_id or "",
                    "agent.updated",
                    value,
                    base_revision=before,
                    result_revision=before + 1,
                )
            # Keep active intents for independent side-effect reconciliation.
            return {"instance_id": instance.id}

        await self.transactions.execute(
            ctx.principal,
            "agent-root-" + key,
            meta("cancel", key),
            {"identity": identity(ctx)},
            write,
        )

    async def owned(
        self, identifier: str, ctx: TrustedExecutionContext
    ) -> tuple[AgentInstance, RootBinding, LoopState]:
        row = await self.store.get(ctx.principal, INSTANCES, identifier)
        binding = await self.store.get(ctx.principal, BINDINGS, identifier)
        state = await self.store.get(ctx.principal, STATES, identifier)
        if (
            row.schema_name != "AgentInstance"
            or binding.schema_name != "AgentRootBinding"
            or state.schema_name != "AgentLoopState"
        ):
            raise reject("agent_state_invalid", "Owned record has another schema", 412)
        instance = AgentInstance.model_validate_json(json.dumps(row.payload))
        bound = RootBinding.model_validate_json(json.dumps(binding.payload))
        current = LoopState.model_validate_json(json.dumps(state.payload))
        if (
            instance.id != identifier
            or instance.run_id != ctx.run_id
            or instance.revision != row.revision
            or current.revision != state.revision
            or current.instance_id != identifier
            or binding.revision != 1
            or identity(bound.context) != identity(ctx)
            or instance.model_policy_ref != ctx.model_policy_ref
            or instance.capability_policy_ref != ctx.capability_policy_ref
        ):
            raise reject("agent_owner_denied", "Complete identity/Run/model/scope differs", 403)
        return instance, bound, current

    async def current(
        self, instance_ref: Ref, ctx: TrustedExecutionContext
    ) -> tuple[AgentInstance, RootBinding, LoopState, AgentView]:
        instance, bound, state = await self.owned(instance_ref.id, ctx)
        check_pin(instance_ref, "agent_instance", instance.id, instance.revision, instance.wire())
        view = await self.sources.current(ctx)
        if view.role_ref != bound.role_ref:
            raise reject("agent_role_changed", "Root role changed; no automatic replacement", 412)
        return instance, bound, state, view

    async def claim(
        self, request: Payload, ctx: TrustedExecutionContext
    ) -> tuple[LoopOperation, bool]:
        requested = Ref.model_validate(request["instance_ref"])
        instance, bound, state, view = await self.current(requested, ctx)
        frame_ref = Ref.model_validate(request["current_frame_ref"])
        check_pin(
            frame_ref, "task_frame", view.frame["task_id"], view.frame["revision"], view.frame
        )
        if request["remaining_budget"] != view.remaining_budget:
            raise reject("agent_budget_stale", "Budget must be the current actual remainder", 412)
        if request["observations"] != [ref.wire() for ref in state.observation_refs]:
            raise reject(
                "agent_observation_denied", "Only owned recorded observations are accepted", 403
            )
        key = identifier("agent-op-", {"agent": instance.id, "operation": ctx.operation_id})

        async def verify() -> None:
            now = await self.sources.current(ctx)
            if now.frame != view.frame or now.role_ref != bound.role_ref:
                raise reject("agent_source_changed", "Frame/role changed before claim", 412)

        async def write(tx: RecordTransaction) -> Payload:
            row = await tx.load(INSTANCES, instance.id)
            status = await tx.load(STATES, instance.id)
            if row.payload != instance.wire() or status.payload != state.wire():
                raise StoreConflict()
            if state.active_operation_ref is not None:
                raise reject(
                    "agent_step_in_progress", "Original step must finish or reconcile", 409
                )
            if state.steps >= bound.max_steps or state.steps >= view.run["budget"]["max_steps"]:
                raise reject("agent_step_limit", "Actual root step limit exhausted", 409, "budget")
            op = LoopOperation(
                id=key,
                instance_id=instance.id,
                revision=1,
                step=state.steps + 1,
                request=request,
                context=ctx,
                phase="claimed",
            )
            await tx.write(OPERATIONS, key, "AgentLoopOperation", op.wire())
            value = instance.model_copy(
                update={"revision": instance.revision + 1, "status": "running"}
            )
            current = state.model_copy(
                update={
                    "revision": state.revision + 1,
                    "steps": state.steps + 1,
                    "frame_ref": frame_ref,
                    "active_operation_ref": pin("content", op.wire()),
                }
            )
            await tx.write(INSTANCES, instance.id, "AgentInstance", value.wire(), instance.revision)
            await tx.write(STATES, instance.id, "AgentLoopState", current.wire(), state.revision)
            await verify()
            return {"operation_id": key, "new": True}

        result = await self.transactions.execute(
            ctx.principal,
            "agent-root-" + instance.id,
            meta("claim", key),
            {"request": request, "context": ctx.wire()},
            write,
            verify,
            on_replay=lambda previous: {**previous, "new": False},
        )
        return await self.operation(result["operation_id"], ctx), bool(result["new"])

    async def discard_stale_unsent(self, operation_ref: Ref, ctx: TrustedExecutionContext) -> Ref:
        operation = await self.operation(operation_ref.id, ctx)
        check_pin(operation_ref, "content", operation.id, operation.revision, operation.wire())
        view = await self.sources.current(ctx)
        requested = Ref.model_validate(operation.request["current_frame_ref"])
        if requested.version == str(view.frame["revision"]):
            raise reject("agent_frame_unchanged", "There is no new user task frame", 409)

        async def verify() -> None:
            _, bound, _ = await self.owned(operation.instance_id, ctx)
            current = await self.sources.current(ctx)
            if current.frame != view.frame or current.role_ref != bound.role_ref:
                raise reject(
                    "agent_source_changed", "New task sources changed before invalidation", 412
                )

        async def safe(tx: RecordTransaction) -> None:
            from uaw.shared.stores import StoreMissing

            try:
                invoked = await tx.load("model.invocations", operation.context.attempt_id)
            except StoreMissing:
                invoked = None
            if invoked is not None and invoked.payload["state"] != "finished":
                raise reject(
                    "agent_reconciliation_required",
                    "Original model intent is unresolved",
                    409,
                    "unknown_effect",
                )
            if operation.tool_context is not None:
                for namespace in (
                    "tool.attempt.estimates",
                    "tool.budget.reserve.plans",
                    "tool.budget.reserved",
                ):
                    try:
                        await tx.load(namespace, operation.tool_context.attempt_id)
                    except StoreMissing:
                        continue
                    raise reject(
                        "agent_reconciliation_required",
                        "Original tool reservation/send needs reconciliation",
                        409,
                        "unknown_effect",
                    )

        async def write(tx: RecordTransaction) -> Payload:
            op = await tx.load(OPERATIONS, operation.id)
            state = await tx.load(STATES, operation.instance_id)
            root = await tx.load(INSTANCES, operation.instance_id)
            if (
                op.payload != operation.wire()
                or state.payload.get("active_operation_ref", {}).get("id") != operation.id
            ):
                raise StoreConflict()
            await safe(tx)
            changed_op = {
                **op.payload,
                "revision": op.revision + 1,
                "phase": "failed",
                "result": error_result(
                    reject(
                        "agent_task_changed",
                        "Unsent old decision invalidated by the actual user task frame",
                        412,
                    )
                ),
            }
            changed_state = {
                **state.payload,
                "revision": state.revision + 1,
                "frame_ref": {
                    "kind": "task_frame",
                    "id": view.frame["task_id"],
                    "version": str(view.frame["revision"]),
                },
            }
            changed_state.pop("active_operation_ref", None)
            changed_root = {**root.payload, "revision": root.revision + 1, "status": "ready"}
            await tx.write(OPERATIONS, operation.id, "AgentLoopOperation", changed_op, op.revision)
            await tx.write(
                STATES, operation.instance_id, "AgentLoopState", changed_state, state.revision
            )
            await tx.write(
                INSTANCES, operation.instance_id, "AgentInstance", changed_root, root.revision
            )
            await tx.emit(
                ctx.scope.conversation_id or "",
                "agent.updated",
                changed_root,
                base_revision=changed_root["revision"] - 1,
                result_revision=changed_root["revision"],
            )
            await verify()
            return {"instance_ref": pin("agent_instance", changed_root).wire()}

        result = await self.transactions.execute(
            ctx.principal,
            "agent-root-" + operation.instance_id,
            meta("discard", operation.id + ":" + str(operation.revision)),
            {
                "operation_ref": operation_ref.wire(),
                "new_frame": view.frame,
                "identity": identity(ctx),
            },
            write,
            verify,
        )
        return Ref.model_validate(result["instance_ref"])

    async def operation(self, key: str, ctx: TrustedExecutionContext) -> LoopOperation:
        row = await self.store.get(ctx.principal, OPERATIONS, key)
        value = LoopOperation.model_validate_json(json.dumps(row.payload))
        if (
            row.schema_name != "AgentLoopOperation"
            or value.id != key
            or row.revision != value.revision
        ):
            raise reject("agent_operation_invalid", "Original operation is inconsistent", 412)
        await self.owned(value.instance_id, ctx)
        if identity(value.context) != identity(ctx):
            raise reject("agent_operation_denied", "Original operation owner differs", 403)
        return value

    async def update(
        self,
        operation: LoopOperation,
        changes: Payload,
        ctx: TrustedExecutionContext,
        *,
        verify: Callable[[], Awaitable[None]],
        finish: bool = False,
    ) -> LoopOperation:
        changes = {**changes, "revision": operation.revision + 1}
        next_value = LoopOperation.model_validate_json(json.dumps({**operation.wire(), **changes}))

        async def write(tx: RecordTransaction) -> Payload:
            op = await tx.load(OPERATIONS, operation.id)
            state_row = await tx.load(STATES, operation.instance_id)
            row = await tx.load(INSTANCES, operation.instance_id)
            instance_revision = row.revision
            if (
                op.payload != operation.wire()
                or state_row.payload.get("active_operation_ref", {}).get("id") != operation.id
            ):
                raise StoreConflict()
            state = {**state_row.payload, "revision": state_row.revision + 1}
            if finish:
                state.pop("active_operation_ref", None)
            if (
                next_value.observation_ref is not None
                and next_value.observation_ref.wire() not in state["observation_refs"]
            ):
                if len(state["observation_refs"]) >= 32:
                    raise reject("agent_observation_limit", "Root observation limit reached", 413)
                state["observation_refs"].append(next_value.observation_ref.wire())
            value = {**row.payload, "revision": row.revision + 1}
            if next_value.snapshot_ref is not None:
                if next_value.context_epoch is None:
                    raise reject("agent_context_epoch_missing", "No actual snapshot epoch", 412)
                value["context_epoch"] = next_value.context_epoch
            if finish:
                value["status"] = (
                    "failed"
                    if next_value.phase == "failed"
                    else (
                        "ready"
                        if next_value.proposal and next_value.proposal["action"] == "call_tools"
                        else "waiting"
                    )
                )
            elif next_value.phase == "waiting":
                value["status"] = "waiting"
            if next_value.model_result and next_value.model_result["kind"] == "ok":
                value["result_ref"] = next_value.model_result["output_refs"][0]
            if next_value.result is not None and next_value.result["kind"] == "ok":
                next_value.result["payload"]["instance_ref"] = reference(
                    "agent_instance", row.resource_id, row.revision + 1, value
                ).wire()
            if not finish:
                state["active_operation_ref"] = pin("content", next_value.wire()).wire()
            await tx.write(
                OPERATIONS,
                operation.id,
                "AgentLoopOperation",
                next_value.wire(),
                operation.revision,
            )
            await tx.write(
                STATES, operation.instance_id, "AgentLoopState", state, state_row.revision
            )
            await tx.write(INSTANCES, operation.instance_id, "AgentInstance", value, row.revision)
            await tx.emit(
                ctx.scope.conversation_id or "",
                "agent.updated",
                value,
                base_revision=instance_revision,
                result_revision=instance_revision + 1,
            )
            await verify()
            return {"operation_id": operation.id}

        await self.transactions.execute(
            ctx.principal,
            "agent-root-" + operation.instance_id,
            meta("update", operation.id + ":" + str(operation.revision)),
            {"expected": operation.revision, "changes": changes},
            write,
            verify,
        )
        return await self.operation(operation.id, ctx)
