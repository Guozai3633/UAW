"""Actual Run/TaskFrame/fixed model/role/remaining-budget sources for root Agents."""

from decimal import Decimal

from uaw.agent.contracts import Payload
from uaw.agent.ports import AgentView
from uaw.infrastructure.db.records import parameter_hash
from uaw.run.budget import BudgetService
from uaw.run.execution_sources import RunExecutionSources
from uaw.run.tool_sources import RunToolAccessSources
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract


def check_pin(ref: Ref, kind: str, identifier: str, revision: int, payload: Payload) -> None:
    if (
        ref.kind != kind
        or ref.id != identifier
        or ref.version != str(revision)
        or ref.location is not None
        or ref.access_scope is not None
        or (ref.content_hash is not None and ref.content_hash != parameter_hash(payload))
    ):
        raise reject("agent_source_stale", "Actual owned source differs from its fixed pin", 412)


def require_role_model(role: Payload, model: Payload) -> None:
    capabilities = set(model["capabilities"])
    requirements = role.get("model_capability_requirements", {})
    required = {"json_schema"}
    for field, capability in (("tool_calling", "tool_calls"), ("vision", "vision")):
        if requirements.get(field, False):
            required.add(capability)
    if (
        not required <= capabilities
        or requirements.get("minimum_context_tokens", 0) > model["context_limit_tokens"]
        or requirements.get("minimum_output_tokens", 0) > model["output_limit_tokens"]
    ):
        raise reject(
            "agent_fixed_model_capability_missing",
            "User's fixed model cannot satisfy this role; select an explicit model",
            409,
        )


class RegisteredAgentSources:
    def __init__(
        self, runs: RunExecutionSources, access: RunToolAccessSources, budgets: BudgetService
    ) -> None:
        self.runs, self.access, self.budgets = runs, access, budgets
        self.store = runs.store

    async def cancelled(self, ctx: TrustedExecutionContext) -> bool:
        await self.runs.data(ctx)
        await self.access._binding(ctx)
        run = await self.store.get(ctx.principal, "runs", ctx.run_id or "")
        ledger = await self.budgets.get_ledger(ctx)
        return bool(run.payload["status"] == "cancelled" or ledger["cancel_requested"])

    async def frame(self, ctx: TrustedExecutionContext, run: Payload) -> Payload:
        task = await self.store.get(ctx.principal, "tasks", run["task_id"])
        frame = await self.store.get(ctx.principal, "intent.frames", run["task_id"])
        bound = await self.store.get(
            ctx.principal, "intent.frame_bindings", f"{run['task_id']}.{frame.revision}"
        )
        inputs = await self.store.get(ctx.principal, "run.input_sets", run["id"])
        validate_contract("TaskFrame", frame.payload)
        validate_contract("IntentFrameBinding", bound.payload)
        if (
            frame.schema_name != "TaskFrame"
            or bound.schema_name != "IntentFrameBinding"
            or frame.payload["task_id"] != run["task_id"]
            or frame.payload["revision"] != frame.revision
            or frame.payload.get("input_revision") != inputs.revision
            or frame.payload["original_input_ref"] != inputs.payload["original_input_ref"]
            or frame.payload["patch_refs"] != inputs.payload["patch_refs"]
        ):
            raise reject("agent_frame_stale", "Frame payload/source revision differs", 412)
        expected = {"kind": "task_frame", "id": frame.resource_id, "version": str(frame.revision)}
        if (
            task.payload.get("frame_ref") != expected
            or run.get("frame_ref") != expected
            or bound.payload["run_id"] != run["id"]
            or bound.payload["input_revision"] != inputs.revision
            or bound.payload["source_refs"]
            != [inputs.payload["original_input_ref"], *inputs.payload["patch_refs"]]
        ):
            raise reject("agent_frame_stale", "Actual task understanding requires refresh", 412)
        if (
            await self.store.get(ctx.principal, "intent.frames", run["task_id"]) != frame
            or await self.store.get(ctx.principal, "run.input_sets", run["id"]) != inputs
        ):
            raise reject("agent_frame_stale", "Task inputs changed during frame read", 412)
        return frame.payload

    async def current(self, ctx: TrustedExecutionContext) -> AgentView:
        if ctx.agent_id is not None or ctx.node_id is not None:
            raise reject("agent_root_only", "Subagent/graph contexts require separate sources", 403)
        sources = await self.runs.current(ctx)
        required = {"agent.start", "agent.step", "model.generate", "context.build"}
        if not required <= set(sources.permissions["allowed_capabilities"]):
            raise reject("agent_capability_denied", "Current scope cannot run a root Agent", 403)
        binding = await self.access._binding(ctx)
        role_ref = Ref.model_validate(binding["role_ref"])
        role = await self.access._role(role_ref)
        assert ctx.model_policy_ref is not None
        policy = (
            await self.store.get(ctx.principal, "model.policies", ctx.model_policy_ref.id)
        ).payload
        model = await self.runs.configuration.require_model(
            policy["fixed_model_id"], sources.fixed_configuration
        )
        require_role_model(role, model)
        row = await self.store.get(ctx.principal, "runs", ctx.run_id or "")
        validate_contract("RunRecord", row.payload)
        if ctx.task_id != row.payload["task_id"] or ctx.scope.task_id != row.payload["task_id"]:
            raise reject(
                "agent_task_scope_missing",
                "Root context must include its owned Task in both scope and identity",
                403,
            )
        if row.payload["status"] not in ("preparing", "running", "waiting_for_user", "verifying"):
            raise reject("agent_run_unavailable", "Run does not accept root Agent work", 409)
        frame = await self.frame(ctx, row.payload)
        if row.payload.get("frame_ref") != {
            "kind": "task_frame",
            "id": frame["task_id"],
            "version": str(frame["revision"]),
        }:
            raise reject("agent_frame_stale", "Run and Task have different understanding", 412)
        ledger = await self.budgets.get_ledger(ctx)
        remaining = dict(row.payload["budget"])
        limits = dict(ledger["limits"])
        for key in limits:
            if key == "currency":
                continue
            if key == "money":
                amount = (
                    Decimal(limits[key])
                    - Decimal(ledger["used"][key])
                    - Decimal(ledger["held"][key])
                )
                limits[key] = str(max(Decimal(0), amount))
            else:
                limits[key] = max(0, limits[key] - ledger["used"][key] - ledger["held"][key])
        remaining["limits"] = limits
        validate_contract("Budget", remaining)
        again = await self.runs.current(ctx)
        if (
            again != sources
            or await self.access._binding(ctx) != binding
            or await self.access._role(role_ref) != role
        ):
            raise reject("agent_source_changed", "Run/model/role sources changed during read", 412)
        if (
            await self.store.get(ctx.principal, "runs", row.resource_id)
        ) != row or await self.frame(ctx, row.payload) != frame:
            raise reject("agent_source_changed", "Run/frame changed during read", 412)
        return AgentView(row.payload, frame, role_ref, role, remaining)
