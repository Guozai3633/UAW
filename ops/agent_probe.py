"""Bounded live Intent/root-Agent acceptance with protected local development identity.

All model responses come from the configured provider. No test fixtures are used.
Approval flags permit only the exact registered pure text/arithmetic/JSON adapters.
"""

import argparse
import asyncio
import hashlib
import json
import sys
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from uaw.agent.assembly import assemble_agent_runtime
from uaw.agent.completion.assembly import assemble_completion_runtime
from uaw.composition import (
    assemble_office_tools,
    assemble_registered_context,
    assemble_text_tool,
    compose,
)
from uaw.context.contracts import InstructionRule
from uaw.infrastructure.db.context_batch import PostgresContextRecordBatch
from uaw.infrastructure.db.transactions import reference
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.model.gateway import request_meta
from uaw.run.inputs import RunInputReader
from uaw.shared.builtin_tools import publish_builtin_office
from uaw.shared.contracts import Principal, Ref, Scope, ScopeSelector, TrustedExecutionContext
from uaw.shared.errors import DomainError
from uaw.shared.settings import ConfigurationError, Settings
from uaw.shared.stores import StoreMissing
from uaw.tool.invocation.schema import normalize
from uaw.tool.providers.arithmetic import arithmetic_spec
from uaw.tool.providers.json_data import json_data_spec
from uaw.tool.providers.text import text_spec
from uaw.tool.registry import AdapterBinding, ToolRegistry

ROOT = Path(__file__).resolve().parents[1]
Payload = dict[str, Any]


async def probe(args: argparse.Namespace) -> int:
    settings = Settings.from_file(args.config)
    if not settings.development_user_token:
        raise ConfigurationError("Protected local development user identity required")
    identity = hashlib.sha256(args.request_id.encode()).hexdigest()
    target = ROOT / ".data" / "agent-probes" / f"{identity}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    receipt: Payload = {
        "created_at": datetime.now(UTC).isoformat(),
        "scope": "actual_provider_intent_root_agent_probe",
        "request_id": args.request_id,
        "model_id": args.model_id,
        "max_agent_steps": args.max_steps,
        "max_root_output_tokens": args.max_output_tokens,
        "scripted_text_approval_authorized": args.approve_text_inspection,
        "phases": [],
        "model_outputs": [],
        "model_attempts": [],
        "task_semantic_completion": False,
    }
    # A partially completed probe is not silently rerun with a new send identity.
    with target.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)

    def save() -> None:
        target.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def phase(name: str, result: Payload) -> None:
        receipt["phases"].append({"name": name, "result": result})
        save()
        print(
            json.dumps(
                {
                    "phase": name,
                    "kind": result.get("kind"),
                    "failure_code": result.get("failure", {}).get("code"),
                    "action": result.get("payload", {}).get("action"),
                }
            ),
            flush=True,
        )

    control = compose(settings)
    try:
        await control.start()
        if not (
            control.records
            and control.configuration
            and control.run_service
            and control.intent_service
            and control.model_service
            and control.tool_access
        ):
            raise ConfigurationError("Actual database/Intent/Model runtime required")
        records, configuration, runs = control.records, control.configuration, control.run_service
        local_provider = None
        if args.office_tools:
            if not settings.development_admin_token:
                raise ConfigurationError(
                    "Protected administrator identity required for local catalogue"
                )
            local_provider = await publish_builtin_office(
                configuration,
                Principal(
                    id=settings.development_admin_id,
                    kind="admin",
                    auth_session_id="local-office-admin",
                ),
                "office-" + identity,
            )

        async def model_receipt(attempt: str) -> None:
            if any(item["attempt_id"] == attempt for item in receipt["model_outputs"]):
                return
            try:
                row = await records.get(actor, "model.invocations", attempt)
            except StoreMissing:
                return
            result = row.payload.get("result", {})
            output = result.get("payload", {})
            receipt["model_outputs"].append(
                {
                    "attempt_id": attempt,
                    "invocation_state": row.payload["state"],
                    "kind": result.get("kind"),
                    "actual_config": output.get("actual_config"),
                    "usage": output.get("usage"),
                    "content_ref": output.get("content_ref"),
                    "finish_reason": output.get("finish_reason"),
                    "failure": result.get("failure"),
                }
            )
            for attempt_id in (
                attempt,
                "retry-" + hashlib.sha256(f"{attempt}:1".encode()).hexdigest(),
            ):
                try:
                    attempt_row = await records.get(actor, "model.attempts", attempt_id)
                except StoreMissing:
                    continue
                receipt["model_attempts"].append(attempt_row.payload)
            save()

        original = args.text_file.read_bytes()
        if len(original) > 8192:
            raise ConfigurationError("Diagnostic source exceeds 8192 UTF-8 bytes")
        text = original.decode("utf-8")
        actor = Principal(
            id=settings.development_principal_id, kind="user", auth_session_id="local-agent-probe"
        )
        conversation = await runs.create_conversation(
            actor,
            {
                "title": "Live fixed-model Agent acceptance",
                "model_choice": {"mode": "explicit", "model_id": args.model_id},
                "memory_policy": {
                    "revision": 0,
                    "read_enabled": False,
                    "contribute_enabled": False,
                    "scope": {"resource_refs": []},
                },
            },
            request_meta("agent-probe-conversation", args.request_id),
        )
        run = await runs.submit(
            actor,
            {"conversation_id": conversation["id"], "text": text, "attachment_refs": []},
            request_meta("agent-probe-submit", args.request_id),
        )
        await runs.advance(
            actor,
            run["id"],
            "preparing",
            request_meta("agent-probe-prepare", args.request_id).model_copy(
                update={"expected_revision": 1}
            ),
        )
        receipt.update(
            conversation_id=conversation["id"],
            run_id=run["id"],
            input_sha256=hashlib.sha256(original).hexdigest(),
        )
        admission = (await records.get(actor, "run.bindings", run["id"])).payload
        catalogue = await configuration.require_model(
            args.model_id, await configuration.snapshot(admission["configuration_ref"])
        )
        provider_ref = Ref.model_validate(catalogue["provider_ref"])
        provider = (
            await records.get(
                configuration.platform,
                "provider.configs",
                provider_ref.id,
                revision=int(provider_ref.version),
            )
        ).payload
        capabilities = (
            "intent.understand",
            "agent.start",
            "agent.step",
            "model.generate",
            "context.build",
            "tool.invoke",
        )
        policy_id = "agent-probe-policy-" + identity
        await records.put(
            actor,
            "execution.policies",
            policy_id,
            "CapabilityPolicy",
            {
                "id": policy_id,
                "revision": 1,
                "allowed_capabilities": list(capabilities),
                "denied_capabilities": [],
                "resource_scope": {
                    "conversation_id": conversation["id"],
                    "task_id": run["task_id"],
                },
                "network_allowlist": [urlsplit(provider["endpoint"]).hostname],
                "feature_flag_refs": [],
            },
            expected_revision=0,
            request_id="diagnostic-policy",
        )
        ctx = TrustedExecutionContext(
            principal=actor,
            scope=Scope(
                principal_id=actor.id,
                conversation_id=conversation["id"],
                task_id=run["task_id"],
                capabilities=capabilities,
            ),
            run_id=run["id"],
            conversation_id=conversation["id"],
            task_id=run["task_id"],
            deadline=run["budget"]["deadline"],
            operation_id="probe-understanding-" + identity,
            trace_id="probe-trace-" + identity,
            attempt_id="probe-intent-" + identity,
            capability_policy_ref=Ref(kind="policy", id=policy_id, version="1"),
            model_policy_ref=Ref.model_validate(admission["model_policy_ref"]),
        )
        inputs = await RunInputReader(records).read(ctx)
        understood: Payload = dict(
            await control.intent_service.understand(
                {
                    "original_input_ref": inputs.refs[0],
                    "user_patch_refs": [],
                    "material_refs": [],
                    "expected_revision": 0,
                },
                ctx,
            )
        )
        phase("intent", understood)
        await model_receipt(ctx.attempt_id)
        if understood["kind"] != "ok":
            return 1
        if understood["payload"]["goal"] != text:
            raise ConfigurationError("Published goal changed original source")
        registry = ToolRegistry()
        adapter_provider = local_provider or provider_ref
        for spec in (
            (
                text_spec(adapter_provider),
                arithmetic_spec(adapter_provider),
                json_data_spec(adapter_provider),
            )
            if args.office_tools
            else (text_spec(adapter_provider),)
        ):
            registry.register(
                spec,
                expected_revision=registry.revision,
                binding=AdapterBinding(
                    adapter_provider, frozenset({"development"}), implemented=True
                ),
            )
        tool_refs = tuple(Ref.model_validate(registry.reference(e)) for e in registry.snapshot()[1])
        tool_ref = next(pin for pin in tool_refs if pin.id == "text.inspect")
        contexts = assemble_registered_context(
            control,
            registry=registry,
            record_batch=PostgresContextRecordBatch(records),
            batch_required=True,
        )
        root_ctx = ctx.model_copy(
            update={
                "operation_id": "probe-root-" + identity,
                "attempt_id": "probe-root-model-" + identity,
            }
        )
        method_id = "probe-root-method-" + identity
        method = await contexts.inputs.register_rule(
            InstructionRule(
                id=method_id,
                source_ref=Ref(kind="rule", id=method_id, version="1"),
                level="platform",
                scope=ScopeSelector(conversation_id=conversation["id"]),
                text=files("uaw.resources.prompts")
                .joinpath("agent-root-v1.txt")
                .read_text(encoding="utf-8"),
            ),
            root_ctx,
            authenticated_service=configuration.platform,
            expected_revision=0,
            meta=request_meta("probe-root-rule", args.request_id).model_copy(
                update={"expected_revision": 0}
            ),
        )
        extra_rules = []
        for index, rule_text in enumerate(args.extra_rule):
            rule_id = f"probe-extra-{index}-" + identity
            extra_rules.append(
                await contexts.inputs.register_rule(
                    InstructionRule(
                        id=rule_id,
                        source_ref=Ref(kind="rule", id=rule_id, version="1"),
                        level="user_current",
                        scope=ScopeSelector(conversation_id=conversation["id"]),
                        text=rule_text,
                    ),
                    root_ctx,
                    authenticated_service=configuration.platform,
                    expected_revision=0,
                    meta=request_meta("probe-extra-rule", rule_id).model_copy(
                        update={"expected_revision": 0}
                    ),
                )
            )
        role = await control.tool_access.register_role(
            {
                "id": "probe-root-role-" + identity,
                "version": "1",
                "description": "Bounded live root Agent text acceptance",
                "instructions_ref": method.wire(),
                "tool_categories": ["text", "arithmetic", "data"]
                if args.office_tools
                else ["text"],
                "skill_refs": [],
                "output_contract": {
                    "goal": "Answer original user task using actual evidence",
                    "version": "1",
                    "requirements": [],
                    "outputs": [],
                },
            },
            request_meta("probe-root-role", args.request_id).model_copy(
                update={"expected_revision": 0}
            ),
            authenticated_service=configuration.platform,
        )
        await control.tool_access.bind(
            root_ctx,
            role,
            request_meta("probe-root-bind", args.request_id).model_copy(
                update={"expected_revision": 0}
            ),
            authenticated_service=configuration.platform,
        )
        tool_service = Principal(
            id="development-local-office" if args.office_tools else "development-text-inspect",
            kind="service",
            auth_session_id="internal-local-adapter",
        )
        tools = (
            assemble_office_tools(
                control, registry=registry, tool_refs=tool_refs, provider=tool_service
            )
            if args.office_tools
            else assemble_text_tool(
                control,
                registry=registry,
                tool_ref=tool_ref,
                provider=tool_service,
            )
        )
        assembly = assemble_agent_runtime(
            control,
            contexts,
            tools,
            registry=registry,
            max_output_tokens=args.max_output_tokens,
            instruction_refs=tuple(extra_rules),
        )
        completion = (
            assemble_completion_runtime(
                control, assembly, max_output_tokens=args.max_output_tokens, contexts=contexts
            )
            if args.verify_delivery
            else None
        )
        current = await runs.get_run(actor, run["id"])
        started = await assembly.runtime.start(
            {
                "run_ref": reference("run", current["id"], current["revision"]),
                "task_frame_ref": understood["output_refs"][0],
                "role_profile_ref": role.wire(),
                "creation_key": "live-probe-" + identity,
            },
            root_ctx,
        )
        phase("root_start", started)
        if started["kind"] != "ok":
            return 1
        root = Ref.model_validate(started["output_refs"][0])
        for number in range(1, args.max_steps + 1):
            step_ctx = root_ctx.model_copy(
                update={
                    "operation_id": f"probe-step-{number}-{identity}",
                    "attempt_id": f"probe-step-model-{number}-{identity}",
                    "trace_id": f"probe-step-trace-{number}-{identity}",
                }
            )
            _, _, state, view = await assembly.repository.current(root, step_ctx)
            result = await assembly.runtime.step(
                {
                    "instance_ref": root.wire(),
                    "observations": [r.wire() for r in state.observation_refs],
                    "current_frame_ref": understood["output_refs"][0],
                    "remaining_budget": view.remaining_budget,
                },
                step_ctx,
            )
            phase(f"step_{number}", result)
            await model_receipt(step_ctx.attempt_id)
            if result["kind"] == "waiting" and (
                args.approve_text_inspection or args.approve_office_tools
            ):
                _, _, state = await assembly.repository.owned(root.id, step_ctx)
                if state.active_operation_ref is None:
                    raise ConfigurationError("No persisted original waiting operation")
                operation = await assembly.repository.operation(
                    state.active_operation_ref.id, step_ctx
                )
                if not operation.proposal or not operation.tool_context:
                    raise ConfigurationError("No persisted original tool proposal")
                call = operation.proposal["proposed_calls"][0]
                allowed = tool_refs if args.approve_office_tools else (tool_ref,)
                if call["tool_ref"] not in [pin.wire() for pin in allowed]:
                    raise ConfigurationError("Diagnostic approval limited to exact text.inspect")
                # Validate the original executor binding and byte bound before approval.
                validated = normalize(call, registry)
                spec = registry.get(call["tool_ref"]).spec()
                tools.executor.check(validated, spec)
                approval = await tools.approvals.get(actor, result["wait_ref"]["id"])
                await tools.approvals.decide(
                    actor,
                    {
                        "approval_id": approval["id"],
                        "decision": {
                            "decision": "approve_once",
                            "expected_arguments_hash": approval["arguments_hash"],
                            "expected_resource_refs": approval["resource_refs"],
                            "reason": "Explicit probe approval for text.inspect",
                        },
                    },
                    request_meta("probe-text-approval", operation.id).model_copy(
                        update={"expected_revision": approval["revision"]}
                    ),
                )
                result = await assembly.runtime.loop.resume(state.active_operation_ref, step_ctx)
                phase(f"step_{number}_resume", result)
            if result["kind"] != "ok":
                return 1
            root = Ref.model_validate(result["payload"]["instance_ref"])
            if result["payload"]["action"] == "call_tools":
                observation = await assembly.runtime.loop.observations.read(
                    Ref.model_validate(result["output_refs"][0]), step_ctx
                )
                phase(f"step_{number}_tool_observation", observation["result"])
                if observation["result"]["kind"] != "ok":
                    return 1
                await tools.responses.verifier.verify(
                    observation["result"]["payload"]["data"],
                    normalize(observation["call"], registry),
                    registry.get(observation["call"]["tool_ref"]).spec(),
                    step_ctx,
                )
                receipt["tool_output_exactly_verified"] = True
                save()
                continue
            receipt["terminal_action"] = result["payload"]["action"]
            receipt["final_model_output"] = (
                await records.get(actor, "model.outputs", step_ctx.attempt_id)
            ).payload
            if completion is not None:
                proposal = (
                    Ref.model_validate(result["payload"]["completion_proposal_ref"])
                    if "completion_proposal_ref" in result["payload"]
                    else await completion.coordinator.propose(
                        root,
                        {
                            "kind": "ok",
                            "output_refs": [result["payload"]["model_output_ref"]],
                            "payload": receipt["final_model_output"],
                        },
                        step_ctx,
                    )
                )
                receipt["completion_proposal"] = (
                    await records.get(actor, "agent.completion.proposals", proposal.id)
                ).payload
                receipt["verification_report"] = (
                    await records.get(actor, "agent.completion.reports", proposal.id)
                ).payload
                reviewed = await records.get(actor, "agent.completion.bundles", proposal.id)
                from uaw.agent.contracts import identifier

                evaluation_id = identifier(
                    "evaluation-",
                    {
                        "run": step_ctx.run_id,
                        "operation": step_ctx.operation_id,
                        "purpose": "completion",
                    },
                )
                await model_receipt(evaluation_id)
                receipt["artifact"] = (
                    await records.get(
                        actor, "workspace.artifacts", reviewed.payload["artifact_ref"]["id"]
                    )
                ).payload
                save()
                before = await runs.get_run(actor, run["id"])
                if args.control_after_review:
                    control_meta = request_meta("probe-review-control", args.request_id).model_copy(
                        update={"expected_revision": before["revision"]}
                    )
                    if args.control_after_review == "cancel":
                        await runs.control(
                            actor,
                            {
                                "run_id": run["id"],
                                "control": {
                                    "mode": "cancel",
                                    "preserve_refs": [],
                                    "reason": "Actual post-review cancellation probe",
                                },
                            },
                            control_meta,
                        )
                    else:
                        inputs = await records.get(actor, "run.input_sets", run["id"])
                        await runs.append_requirement(
                            actor,
                            run["id"],
                            "修订要求：只输出一句话，不按旧交付物完成任务。",
                            control_meta.model_copy(update={"expected_revision": inputs.revision}),
                        )
                    try:
                        await completion.controller.complete(
                            proposal,
                            step_ctx,
                            request_meta("probe-stale-complete", args.request_id).model_copy(
                                update={"expected_revision": before["revision"]}
                            ),
                        )
                    except DomainError as denied:
                        final = await runs.get_run(actor, run["id"])
                        receipt["completion_guard_failure"] = denied.failure.wire()
                        receipt["runtime_probe_passed"] = final["status"] != "completed"
                        receipt["final_run_status"] = final["status"]
                        receipt["guard_scenario"] = args.control_after_review
                        save()
                        return 0 if receipt["runtime_probe_passed"] else 1
                    raise ConfigurationError("Completion accepted stale/cancelled actual delivery")
                await completion.controller.complete(
                    proposal,
                    step_ctx,
                    request_meta("probe-complete", args.request_id).model_copy(
                        update={"expected_revision": before["revision"]}
                    ),
                )
            final_run = await runs.get_run(actor, run["id"])
            receipt["final_run_status"] = final_run["status"]
            receipt["runtime_probe_passed"] = (
                final_run["status"] == "completed"
                if completion is not None
                else result["payload"]["action"] == "respond" and final_run["status"] != "completed"
            )
            receipt["task_semantic_completion"] = (
                completion is not None and final_run["status"] == "completed"
            )
            save()
            return 0 if receipt["runtime_probe_passed"] else 1
        receipt["stop_reason"] = "diagnostic_step_limit"
        save()
        return 1
    except Exception as exc:
        receipt["error_type"] = type(exc).__name__
        if isinstance(exc, DomainError):
            receipt["error_code"] = exc.failure.code
        save()
        raise
    finally:
        # Include reviewer/rule attempts even when validation fails before a
        # delivery bundle exists. Never hide charged failed attempts.
        if control.records and receipt.get("run_id") and "actor" in locals():
            from sqlalchemy import select

            from uaw.infrastructure.db.models import RecordRow

            try:
                async with control.records.database.sessions() as session:
                    invocation_ids = tuple(
                        await session.scalars(
                            select(RecordRow.resource_id).where(
                                RecordRow.principal_id == actor.id,
                                RecordRow.namespace == "model.invocations",
                                RecordRow.deleted.is_(False),
                                RecordRow.payload["run_id"].as_string() == receipt["run_id"],
                            )
                        )
                    )
                    attempts = tuple(
                        await session.scalars(
                            select(RecordRow.payload).where(
                                RecordRow.principal_id == actor.id,
                                RecordRow.namespace == "model.attempts",
                                RecordRow.deleted.is_(False),
                                RecordRow.payload["invocation_id"].as_string().in_(invocation_ids),
                            )
                        )
                    )
                for invocation_id in invocation_ids:
                    await model_receipt(invocation_id)
                receipt["model_attempts"] = list(attempts)
                receipt["final_run_status"] = (
                    (await control.run_service.get_run(actor, receipt["run_id"]))["status"]
                    if control.run_service
                    else None
                )
                save()
            except Exception as receipt_error:
                receipt["attempt_collection_error_type"] = type(receipt_error).__name__
                save()
        await control.close()
        print(f"Protected live probe receipt: {target}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "ops/database-development.toml")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--text-file", type=Path, required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--max-steps", type=int, choices=range(1, 5), default=3)
    parser.add_argument(
        "--max-output-tokens", type=int, choices=(512, 1024, 2048, 4096), default=512
    )
    parser.add_argument("--approve-text-inspection", action="store_true")
    parser.add_argument("--office-tools", action="store_true")
    parser.add_argument("--approve-office-tools", action="store_true")
    parser.add_argument("--extra-rule", action="append", default=[])
    parser.add_argument("--control-after-review", choices=("cancel", "steer"))
    parser.add_argument(
        "--verify-delivery",
        action="store_true",
        help="Run actual fixed-model semantic review and independent completion CAS",
    )
    args = parser.parse_args()
    try:
        return asyncio.run(probe(args), loop_factory=control_plane_loop)
    except Exception as exc:
        print(
            f"Live probe stopped ({type(exc).__name__}); inspect protected receipt.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
