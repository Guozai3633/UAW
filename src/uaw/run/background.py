"""Product single-Agent driver over the existing owning-domain runtimes."""

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from importlib.resources import files
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from uaw.agent.assembly import assemble_agent_runtime
from uaw.agent.completion.assembly import assemble_completion_runtime
from uaw.agent.contracts import identifier as stable_id
from uaw.agent.repository import pin
from uaw.context.contracts import InstructionRule
from uaw.infrastructure.db.context_batch import PostgresContextRecordBatch
from uaw.infrastructure.db.transactions import reference
from uaw.run.inputs import RunInputReader
from uaw.run.jobs import RunJobs
from uaw.shared.contracts import (
    Principal,
    Ref,
    RequestMeta,
    Scope,
    ScopeSelector,
    TrustedExecutionContext,
)
from uaw.shared.errors import CapabilityUnavailable, DomainError, reject
from uaw.shared.stores import StoreMissing
from uaw.tool.providers.arithmetic import arithmetic_spec
from uaw.tool.providers.json_data import json_data_spec
from uaw.tool.providers.text import text_spec
from uaw.tool.registry import AdapterBinding, ToolRegistry

if TYPE_CHECKING:
    from uaw.composition import Container

Payload = dict[str, Any]
CAPABILITIES = (
    "intent.understand",
    "agent.start",
    "agent.step",
    "model.generate",
    "context.build",
    "tool.invoke",
)


def meta(key: str, revision: int | None = None) -> RequestMeta:
    return RequestMeta(request_id=key, schema_version="0.1", expected_revision=revision)


class BackgroundAgent:
    def __init__(self, control: Container) -> None:
        self.control = control

    async def prepare(self) -> RunJobs:
        from uaw.composition import assemble_office_tools, assemble_registered_context

        c = self.control
        if not (
            c.records
            and c.configuration
            and c.run_service
            and c.intent_service
            and c.tool_access
            and c.blobs
        ):
            raise CapabilityUnavailable("background.actual_runtime_sources")
        current = await c.configuration.current()
        candidates = [r for r in current["provider_refs"] if r["id"] == "builtin-office-v1"]
        if len(candidates) != 1:
            raise CapabilityUnavailable("background.admin_registered_office_provider")
        provider = Ref.model_validate(candidates[0])
        configured = (
            await c.records.get(c.configuration.platform, "providers", provider.id)
        ).payload
        draft = (
            await c.records.get(
                c.configuration.platform,
                "provider.configs",
                provider.id,
                revision=int(provider.version),
            )
        ).payload
        if (
            configured["state"] != "active"
            or configured["revision"] != int(provider.version)
            or draft["profile_ref"] != reference("provider_profile", "tool.builtin.office")
        ):
            raise CapabilityUnavailable("background.current_builtin_provider")
        registry = ToolRegistry()
        for spec in (text_spec(provider), arithmetic_spec(provider), json_data_spec(provider)):
            registry.register(
                spec,
                expected_revision=registry.revision,
                binding=AdapterBinding(provider, frozenset({"development"}), implemented=True),
            )
        refs = tuple(Ref.model_validate(registry.reference(e)) for e in registry.snapshot()[1])
        self.contexts = assemble_registered_context(
            c,
            registry=registry,
            record_batch=PostgresContextRecordBatch(c.records),
            batch_required=True,
        )
        self.tools = assemble_office_tools(
            c,
            registry=registry,
            tool_refs=refs,
            provider=Principal(
                id="development-local-office",
                kind="service",
                auth_session_id="internal-local-adapter",
            ),
        )
        self.agent = assemble_agent_runtime(
            c,
            self.contexts,
            self.tools,
            registry=registry,
            max_output_tokens=c.settings.agent_max_output_tokens,
        )
        self.completion = assemble_completion_runtime(
            c,
            self.agent,
            contexts=self.contexts,
            max_output_tokens=c.settings.agent_max_output_tokens,
            acceptance_required=c.settings.agent_acceptance_required,
        )
        c.completion_controller = self.completion.controller
        c.approvals = self.tools.approvals
        c.bindings = replace(c.bindings, agent=self.agent.runtime)
        return RunJobs(
            c.records,
            Principal(
                id=c.settings.development_principal_id,
                kind="user",
                auth_session_id="background-queue",
            ),
            capacity=c.settings.agent_queue_capacity,
            concurrency=c.settings.agent_worker_count,
            advance=self.advance,
            finalize=self.finalize,
        )

    async def guard(self, job: Payload) -> tuple[Principal, Payload]:
        c = self.control
        assert c.run_service and c.records
        actor = Principal.model_validate(job["principal"])
        if actor.auth_session_id.startswith("web-session-"):
            if c.browser_sessions is None:
                raise CapabilityUnavailable("background.current_web_identity")
            await c.browser_sessions.principal(actor)
        else:
            token = c.settings.development_user_token
            expected = (
                "session-" + hashlib.sha256(token.get_secret_value().encode()).hexdigest()[:24]
                if token
                else None
            )
            if actor.auth_session_id != expected or actor.id != c.settings.development_principal_id:
                raise reject(
                    "background_identity_revoked", "Original authenticated identity changed", 401
                )
        run = await c.run_service.get_run(actor, job["run_id"])
        ledger = (await c.records.get(actor, "budget.ledgers", run["id"])).payload
        if run["status"] in ("completed", "failed", "cancelled"):
            return actor, run
        if ledger["cancel_requested"]:
            raise reject(
                "background_cancel_requested",
                "Original Run cancellation requested",
                409,
                "cancelled",
            )
        if datetime.fromisoformat(run["budget"]["deadline"]) <= datetime.now(UTC):
            raise reject(
                "background_deadline_expired", "Original Run deadline passed", 409, "timeout"
            )
        return actor, run

    async def advance(self, job: Payload) -> Payload:
        c = self.control
        assert (
            c.records and c.run_service and c.configuration and c.intent_service and c.tool_access
        )
        actor, run = await self.guard(job)
        if run["status"] in ("completed", "failed", "cancelled"):
            return {**job, "state": "finished", "stage": "finished"}
        base = {**job, "state": "queued", "ready_at": datetime.now(UTC).isoformat()}
        key = run["id"]
        if job["stage"] == "admitted":
            admission = (await c.records.get(actor, "run.bindings", key)).payload
            configuration = await c.configuration.snapshot(admission["configuration_ref"])
            policy = (
                await c.records.get(
                    actor,
                    "model.policies",
                    admission["model_policy_ref"]["id"],
                    revision=int(admission["model_policy_ref"]["version"]),
                )
            ).payload
            model = await c.configuration.require_model(policy["fixed_model_id"], configuration)
            model_provider = Ref.model_validate(model["provider_ref"])
            draft = (
                await c.records.get(
                    c.configuration.platform,
                    "provider.configs",
                    model_provider.id,
                    revision=int(model_provider.version),
                )
            ).payload
            policy_id = "web-policy-" + key
            capability = {
                "id": policy_id,
                "revision": 1,
                "allowed_capabilities": list(CAPABILITIES),
                "denied_capabilities": [],
                "resource_scope": {
                    "conversation_id": run["conversation_id"],
                    "task_id": run["task_id"],
                },
                "network_allowlist": [urlsplit(draft["endpoint"]).hostname],
                "feature_flag_refs": [],
            }
            await c.records.put(
                actor,
                "execution.policies",
                policy_id,
                "CapabilityPolicy",
                capability,
                expected_revision=0,
                request_id="web-admission-policy",
            )
            ctx = TrustedExecutionContext(
                principal=actor,
                scope=Scope(
                    principal_id=actor.id,
                    conversation_id=run["conversation_id"],
                    task_id=run["task_id"],
                    capabilities=CAPABILITIES,
                ),
                run_id=key,
                conversation_id=run["conversation_id"],
                task_id=run["task_id"],
                deadline=run["budget"]["deadline"],
                operation_id="web-intent-" + key,
                trace_id="web-trace-" + key,
                attempt_id="web-intent-model-" + key,
                capability_policy_ref=Ref(kind="policy", id=policy_id, version="1"),
                model_policy_ref=Ref.model_validate(admission["model_policy_ref"]),
            )
            if run["status"] == "queued":
                await c.run_service.advance(
                    actor, key, "preparing", meta("web-prepare-" + key, run["revision"])
                )
            return {**base, "stage": "prepared", "context": ctx.wire()}
        ctx = TrustedExecutionContext.model_validate_json(json.dumps(job["context"]))
        if job["stage"] == "prepared":
            inputs = await RunInputReader(c.records).read(ctx)
            result: Payload = dict(
                await c.intent_service.understand(
                    {
                        "original_input_ref": inputs.refs[0],
                        "user_patch_refs": [],
                        "material_refs": [],
                        "expected_revision": 0,
                    },
                    ctx,
                )
            )
            if result["kind"] != "ok":
                return await self.failure(base, result)
            await self.message(
                actor,
                run,
                "understanding",
                result["payload"]["summary"],
                "web-understanding-" + key,
            )
            return {**base, "stage": "understood", "frame_ref": result["output_refs"][0]}
        if job["stage"] == "understood":
            method_id = "web-method-" + key
            method = await self.contexts.inputs.register_rule(
                InstructionRule(
                    id=method_id,
                    source_ref=Ref(kind="rule", id=method_id, version="1"),
                    level="platform",
                    scope=ScopeSelector(conversation_id=run["conversation_id"]),
                    text=files("uaw.resources.prompts")
                    .joinpath("agent-root-v1.txt")
                    .read_text(encoding="utf-8"),
                ),
                ctx,
                authenticated_service=c.configuration.platform,
                expected_revision=0,
                meta=meta("web-method-" + key, 0),
            )
            role = await c.tool_access.register_role(
                {
                    "id": "web-role-" + key,
                    "version": "1",
                    "description": "Single general office and academic Agent; evidence required",
                    "instructions_ref": method.wire(),
                    "tool_categories": ["text", "arithmetic", "data"],
                    "skill_refs": [],
                    "output_contract": {
                        "goal": "Deliver the original user task using actual evidence",
                        "version": "1",
                        "requirements": [],
                        "outputs": [],
                    },
                },
                meta("web-role-" + key, 0),
                authenticated_service=c.configuration.platform,
            )
            await c.tool_access.bind(
                ctx,
                role,
                meta("web-role-bind-" + key, 0),
                authenticated_service=c.configuration.platform,
            )
            return {**base, "stage": "started", "role_ref": role.wire()}
        if job["stage"] == "started":
            root = run.get("root_agent_ref")
            if root is None:
                result = await self.agent.runtime.start(
                    {
                        "run_ref": reference("run", key, run["revision"]),
                        "task_frame_ref": job["frame_ref"],
                        "role_profile_ref": job["role_ref"],
                        "creation_key": "web-root-" + key,
                    },
                    ctx,
                )
                if result["kind"] != "ok":
                    return await self.failure(base, result)
                root = result["output_refs"][0]
            run = await c.run_service.get_run(actor, key)
            if run["status"] in ("preparing", "waiting_for_user"):
                await c.run_service.advance(
                    actor, key, "running", meta("web-running-" + key, run["revision"])
                )
            return {
                **base,
                "stage": "step",
                "step": 1,
                "instance_ref": root,
                "step_context": self.step_context(ctx, 1).wire(),
            }
        if job["stage"] == "step":
            step_ctx = TrustedExecutionContext.model_validate_json(json.dumps(job["step_context"]))
            root_id = job["instance_ref"]["id"]
            operation_id = stable_id(
                "agent-op-", {"agent": root_id, "operation": step_ctx.operation_id}
            )
            try:
                operation = await self.agent.repository.operation(operation_id, step_ctx)
            except StoreMissing:
                instance, _, state = await self.agent.repository.owned(root_id, step_ctx)
                root = pin("agent_instance", instance.wire())
                _, _, _, view = await self.agent.repository.current(root, step_ctx)
                result = await self.agent.runtime.step(
                    {
                        "instance_ref": root.wire(),
                        "observations": [r.wire() for r in state.observation_refs],
                        "current_frame_ref": job["frame_ref"],
                        "remaining_budget": view.remaining_budget,
                    },
                    step_ctx,
                )
            else:
                result = await self.agent.runtime.loop.resume(
                    pin("content", operation.wire()), operation.context
                )
            if result["kind"] == "waiting":
                await self.waiting(actor, run)
                return {
                    **base,
                    "state": "waiting",
                    "ready_at": (datetime.now(UTC) + timedelta(seconds=2)).isoformat(),
                }
            if result["kind"] != "ok":
                return await self.failure(base, result)
            if result["payload"]["action"] == "call_tools":
                if job["step"] >= min(64, run["budget"]["max_steps"]):
                    raise reject(
                        "background_step_limit",
                        "Agent reached its original step budget",
                        409,
                        "budget",
                    )
                step = job["step"] + 1
                return {**base, "step": step, "step_context": self.step_context(ctx, step).wire()}
            if result["payload"]["action"] in ("wait", "blocked"):
                await self.waiting(actor, run)
                return {**base, "state": "blocked"}
            operation = await self.agent.repository.operation(operation_id, step_ctx)
            proposal = (
                Ref.model_validate(result["payload"]["completion_proposal_ref"])
                if "completion_proposal_ref" in result["payload"]
                else await self.completion.coordinator.propose(
                    Ref.model_validate(result["payload"]["instance_ref"]),
                    operation.model_result or {},
                    step_ctx,
                )
            )
            await self.publish_preview(actor, run, proposal)
            return {**base, "stage": "delivery", "proposal_ref": proposal.wire()}
        if job["stage"] == "delivery":
            step_ctx = TrustedExecutionContext.model_validate_json(json.dumps(job["step_context"]))
            proposal = Ref.model_validate(job["proposal_ref"])
            current = await c.run_service.get_run(actor, key)
            try:
                await self.completion.controller.complete(
                    proposal, step_ctx, meta("web-complete-" + key, current["revision"])
                )
            except DomainError as exc:
                if exc.failure.code == "completion_user_acceptance_required":
                    # Run revision is pinned by the proposal; do not advance it while
                    # awaiting acceptance or invent a second completion proposal.
                    return {
                        **base,
                        "state": "waiting",
                        "ready_at": (datetime.now(UTC) + timedelta(seconds=2)).isoformat(),
                    }
                return await self.failure(base, {"kind": "failed", "failure": exc.failure.wire()})
            return {**base, "stage": "finished", "state": "finished"}
        raise reject("background_stage_invalid", "Original background stage is invalid", 412)

    async def finalize(self, job: Payload) -> None:
        from uaw.run.termination import RunTerminationController

        assert self.control.records
        await RunTerminationController(self.control.records).settle(
            Principal.model_validate(job["principal"]), job["run_id"]
        )

    @staticmethod
    def step_context(ctx: TrustedExecutionContext, number: int) -> TrustedExecutionContext:
        return ctx.model_copy(
            update={
                "operation_id": f"web-step-{number}-{ctx.run_id}",
                "attempt_id": f"web-step-model-{number}-{ctx.run_id}",
                "trace_id": f"web-step-trace-{number}-{ctx.run_id}",
            }
        )

    async def waiting(self, actor: Principal, run: Payload) -> None:
        assert self.control.run_service
        current = await self.control.run_service.get_run(actor, run["id"])
        if current["status"] in ("preparing", "running", "verifying"):
            await self.control.run_service.advance(
                actor,
                run["id"],
                "waiting_for_user",
                meta("web-wait-" + str(current["revision"]) + run["id"], current["revision"]),
            )

    async def message(self, actor: Principal, run: Payload, kind: str, text: str, key: str) -> None:
        assert self.control.run_service
        item = await self.control.run_service.create_execution_item(
            actor, run["id"], kind, meta(key)
        )
        await self.control.run_service.update_execution_item(
            actor, item["id"], "in_progress", "", meta(key + "-start", 1)
        )
        await self.control.run_service.update_execution_item(
            actor, item["id"], "completed", text, meta(key + "-end", 2)
        )

    async def failure(self, job: Payload, result: Payload) -> Payload:
        actor = Principal.model_validate(job["principal"])
        assert self.control.run_service
        run = await self.control.run_service.get_run(actor, job["run_id"])
        failure = (
            result.get("failure")
            or reject(
                "background_result_unavailable", "No valid owning-domain result", 409
            ).failure.wire()
        )
        await self.waiting(actor, run)
        await self.message(
            actor,
            run,
            "agent_message",
            failure["message"],
            "web-failure-" + run["id"] + "-" + str(job["step"]),
        )
        return {**job, "state": "blocked", "failure": failure}

    async def publish_preview(self, actor: Principal, run: Payload, proposal: Ref) -> None:
        from uaw.infrastructure.db.transactions import RecordTransaction
        from uaw.run.deliveries import DeliveryReader

        c = self.control
        assert c.records and c.blobs and c.run_service
        view, original = await DeliveryReader(c.records, c.blobs).read(actor, run["id"])
        if view["proposal_ref"] != proposal.wire() or view["stale"]:
            raise reject(
                "background_delivery_stale", "Actual delivery changed before publication", 412
            )
        key = stable_id("artifact-item-", {"proposal": proposal.wire()})

        async def write(tx: RecordTransaction) -> Payload:
            current = await tx.load("runs", run["id"])
            if current.payload["conversation_id"] != original.conversation_id:
                raise reject("background_delivery_scope", "Delivery conversation differs", 403)
            now = view["artifact"]["created_at"]
            item = {
                "id": key,
                "conversation_id": run["conversation_id"],
                "run_id": run["id"],
                "type": "artifact",
                "status": "completed",
                "revision": 1,
                "text": view["artifact"]["title"] + "\n正文与逐项核验可在成果栏查看。",
                "resource_refs": [
                    view["artifact_ref"],
                    view["bundle_ref"],
                    view["report_ref"],
                    view["contract_ref"],
                ],
                "created_at": now,
                "updated_at": now,
            }
            await tx.write("items", key, "InteractionItem", item)
            await tx.emit(
                run["conversation_id"], "item.updated", item, item_ref=reference("item", key)
            )
            return item

        await c.run_service.transactions.execute(
            actor,
            "conversation:" + run["conversation_id"],
            meta("preview-" + proposal.id),
            {"action": "delivery.preview", "proposal_ref": proposal.wire()},
            write,
        )
