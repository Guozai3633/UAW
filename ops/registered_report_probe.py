"""Bounded diagnostic on an explicitly isolated, pinned UAW runtime.

Launch with PYTHONPATH pointing at the fixed runtime, not the integration tree.
No human review/acceptance, native installation or automatic retry is performed.
"""

import argparse
import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import select

import uaw
from uaw.composition import compose
from uaw.evaluation.contracts import Case, Policy
from uaw.evaluation.io import canonical, digest, parse_json, read_bounded
from uaw.evaluation.reader import record
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.run.background import BackgroundAgent
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.conversation_control import ConversationControls
from uaw.run.deliveries import DeliveryReader
from uaw.run.execution_clock import ExecutionClocks
from uaw.run.execution_segments import ExecutionSegments
from uaw.run.jobs import JOBS
from uaw.shared.contracts import Principal, RequestMeta
from uaw.shared.conversation import ConversationRequestMeta, RunCorrectionRequest
from uaw.shared.settings import Settings
from uaw.shared.stores import StoreMissing

Payload = dict[str, Any]


class ProbeStop(ValueError):
    """Safe bounded diagnostic code from the probe's own guards."""


def scenario_inputs(case: Case) -> tuple[str, str]:
    parts = case.prompt.split("\n\n用户追加要求\n")
    if len(parts) != 2 or not all(part.strip() for part in parts):
        raise ProbeStop("exactly_one_explicit_correction_required")
    return parts[0], parts[1]


def fixed_runtime(runtime: Path) -> bool:
    return Path(uaw.__file__ or "").resolve().is_relative_to(runtime.resolve())


async def run(args: argparse.Namespace) -> int:
    environment = parse_json(read_bounded(args.environment, limit=2**21))
    runtime = args.environment.parent / "runtime"
    if not fixed_runtime(runtime):
        raise ProbeStop("fixed_runtime_import_required")
    registration = parse_json(read_bounded(args.registration, limit=2**21))
    if digest(registration) != args.registration_sha256:
        raise ProbeStop("registered_file_changed")
    variants = {
        registration["draft"][key]["id"]: registration["draft"][key]
        for key in ("candidate", "baseline")
    }
    variant = variants[args.variant_id]
    if environment["backend_source"] != variant["source_commit"]:
        raise ProbeStop("runtime_source_differs")
    scope = {
        "schema_version": "uaw.a13-isolated-execution.v1",
        "queue_mode": "manual_owning_queue",
        "database_namespace": "new_empty_database_per_variant",
        "blob_namespace": "new_empty_blob_store_per_variant",
        "native_installed": False,
    }
    if environment.get("evaluation_execution_scope") != scope:
        raise ProbeStop("execution_scope_not_pinned")
    fields = {
        key: environment[key]
        for key in ("dependency_inventory_sha256", "dependency_lock_sha256", "settings_sha256")
    }
    fields["execution_scope_sha256"] = digest(scope)
    if digest(fields) != variant["environment_sha256"]:
        raise ProbeStop("runtime_environment_differs")
    case = record(Case, registration["draft"]["suite"]["cases"][0])
    if len(registration["draft"]["suite"]["cases"]) != 1:
        raise ProbeStop("single_explicit_case_required")
    record(Policy, registration["policy"])
    original, correction = scenario_inputs(case)
    original_settings = Settings.from_file(args.config)
    # Isolated storage namespace and manual queue mode are pinned in the new
    # experiment's execution-scope digest, shared by both variants.
    settings = original_settings.model_copy(
        update={
            "agent_execution_enabled": False,
            "blob_directory": args.environment.parent / "blobs",
        }
    )
    if settings.installed_state_directory is not None or not settings.development_user_token:
        raise ProbeStop("isolated_non_native_development_required")
    actor = Principal(
        id=settings.development_principal_id,
        kind="user",
        auth_session_id="session-"
        + hashlib.sha256(settings.development_user_token.get_secret_value().encode()).hexdigest()[
            :24
        ],
    )
    control = compose(settings)
    report: Payload = {
        "schema_version": "uaw.registered-report-probe.v1",
        "status": "started",
        "started_at": datetime.now(UTC).isoformat(),
        "variant_id": args.variant_id,
        "source_commit": environment["backend_source"],
        "registration_sha256": args.registration_sha256,
        "synthetic_diagnostic_not_human_task": True,
        "human_acceptance_performed": False,
        "phase_observations": [],
        "request_ids": [],
    }
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(report, stream)

    def save() -> None:
        args.report.write_bytes(canonical(report) + b"\n")

    def meta(name: str) -> RequestMeta:
        identifier = name + "-" + uuid4().hex
        report["request_ids"].append(identifier)
        return RequestMeta(request_id=identifier, schema_version="0.1")

    run_record = None
    driver = queue = None
    started = monotonic()
    try:
        await control.start()
        assert control.records and control.run_service and control.blobs
        records, runs = control.records, control.run_service
        async with records.database.sessions() as session:
            existing = await session.scalar(
                select(RecordRow.resource_id).where(RecordRow.principal_id == actor.id).limit(1)
            )
        if existing is not None:
            raise ProbeStop("fresh_isolated_user_inventory_required")
        driver = BackgroundAgent(
            control,
            conversation_clocks=ExecutionClocks(records, effects=RunIdleEffects()),
            conversation_segments=ExecutionSegments(records),
        )
        queue = await driver.prepare()
        conversation = await runs.create_conversation(
            actor,
            {
                "title": "A13 registered report diagnostic (not a human task)",
                "model_choice": {"mode": "explicit", "model_id": variant["model"]["model_id"]},
                "memory_policy": {
                    "revision": 0,
                    "read_enabled": False,
                    "contribute_enabled": False,
                    "scope": {"resource_refs": []},
                },
            },
            meta("registered-conversation"),
        )

        async def enqueue(tx: Any, value: Payload) -> None:
            await queue.enqueue(tx, value, actor)

        run_record = await runs.submit(
            actor,
            {
                "conversation_id": conversation["id"],
                "text": original,
                "attachment_refs": [],
            },
            meta("registered-submit"),
            on_admitted=enqueue,
        )
        report.update(run_id=run_record["id"], conversation_id=conversation["id"])
        save()
        reader, controls = DeliveryReader(records, control.blobs), ConversationControls(records)

        async def delivery(epoch: int) -> Payload:
            phase_started = monotonic()
            while monotonic() - phase_started < 100:
                value = await controls.view(actor, run_record["id"])
                if value.run["status"] in ("failed", "cancelled", "completed"):
                    raise ProbeStop("unexpected_terminal_before_diagnostic_delivery")
                try:
                    result, _ = await reader.read(actor, run_record["id"])
                except StoreMissing:
                    result = None
                if (
                    result
                    and value.input_revision == epoch
                    and not result["stale"]
                    and result["requires_acceptance"]
                    and result["proposal"]["run_ref"]["version"] == str(value.run["revision"])
                    and (
                        epoch == 1
                        or result["artifact_ref"] != report["original_delivery"]["artifact_ref"]
                    )
                ):
                    if result["report"]["outcome"] != "succeeded":
                        raise ProbeStop("completion_verification_not_succeeded")
                    report["phase_observations"].append(
                        {
                            "input_revision": epoch,
                            "elapsed_ms": round((monotonic() - phase_started) * 1000),
                        }
                    )
                    save()
                    return result
                if value.question is not None:
                    raise ProbeStop("unexpected_question_not_automatically_answered")
                job = (await records.get(actor, JOBS, run_record["id"])).payload
                if job["state"] == "blocked":
                    resumed = await driver.resume_conversation(actor, run_record["id"])
                    if not resumed:
                        raise ProbeStop("owning_continuation_not_available")
                async with records.database.sessions() as session:
                    invocations = list(
                        await session.scalars(
                            select(RecordRow.resource_id).where(
                                RecordRow.principal_id == actor.id,
                                RecordRow.namespace == "model.invocations",
                            )
                        )
                    )
                if len(invocations) >= 4 and job["stage"] != "delivery":
                    raise ProbeStop("four_call_diagnostic_limit_reached")
                await asyncio.wait_for(queue.tick(), timeout=90)
                await asyncio.sleep(0.2)
            raise TimeoutError("diagnostic_delivery_timeout")

        report["original_delivery"] = await delivery(1)
        view = await controls.view(actor, run_record["id"])
        request_id = "registered-correction-" + uuid4().hex
        report["request_ids"].append(request_id)
        receipt = await controls.correct(
            actor,
            RunCorrectionRequest(
                run_id=run_record["id"],
                expected_input_revision=view.input_revision,
                text=correction,
                attachment_refs=(),
            ),
            ConversationRequestMeta(
                request_id=request_id,
                schema_version="0.2",
                expected_revision=cast(int, view.run["revision"]),
            ),
        )
        report["correction_receipt"] = receipt.wire()
        save()
        report["corrected_delivery"] = await delivery(2)
        receipt = await controls.lookup(actor, run_record["id"], request_id)
        report["correction_receipt"] = receipt.wire()
        if receipt.patch.state != "applied":
            raise ProbeStop("correction_not_applied")
        report["status"] = "engineering_scenario_passed_no_human_acceptance"
    except Exception as exc:
        report.update(
            status="diagnostic_failed",
            error_type=type(exc).__name__,
            error_code=str(exc)
            if isinstance(exc, ProbeStop)
            else getattr(getattr(exc, "failure", None), "code", None),
        )
    finally:
        if run_record and control.records and control.run_service:
            try:
                current = await control.run_service.get_run(actor, run_record["id"])
                if current["status"] not in ("completed", "failed", "cancelled"):
                    await control.run_service.control(
                        actor,
                        {
                            "run_id": run_record["id"],
                            "control": {
                                "mode": "cancel",
                                "preserve_refs": [],
                                "reason": "End isolated diagnostic; no human acceptance performed",
                            },
                        },
                        meta("registered-cancel").model_copy(
                            update={"expected_revision": current["revision"]}
                        ),
                    )
                    if queue is not None:
                        for _ in range(24):
                            await queue.tick()
                            current = await control.run_service.get_run(actor, run_record["id"])
                            if current["status"] in ("completed", "failed", "cancelled"):
                                break
                            await asyncio.sleep(0.25)
                report["terminal_run"] = await control.run_service.get_run(actor, run_record["id"])
                async with control.records.database.sessions() as session:
                    rows = list(
                        await session.scalars(
                            select(RecordRow).where(
                                RecordRow.principal_id == actor.id, RecordRow.deleted.is_(False)
                            )
                        )
                    )
                report["owning_evidence"] = [
                    {
                        "namespace": r.namespace,
                        "id": r.resource_id,
                        "revision": r.revision,
                        "updated_at": r.updated_at.isoformat(),
                        "payload": r.payload,
                    }
                    for r in rows
                ]
                report["model_invocations"] = [
                    r.payload for r in rows if r.namespace == "model.invocations"
                ]
                report["model_attempts"] = [
                    r.payload for r in rows if r.namespace == "model.attempts"
                ]
            except Exception as exc:
                report["cleanup_error_type"] = type(exc).__name__
        report.update(
            finished_at=datetime.now(UTC).isoformat(),
            elapsed_ms=round((monotonic() - started) * 1000),
        )
        save()
        await control.close()
    print(
        json.dumps(
            {
                "status": report["status"],
                "run_id": report.get("run_id"),
                "model_attempts": len(report.get("model_attempts", [])),
                "human_acceptance": False,
            }
        )
    )
    return 0 if report["status"] == "engineering_scenario_passed_no_human_acceptance" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("environment", "config", "registration", "report"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--registration-sha256", required=True)
    parser.add_argument("--variant-id", required=True)
    args = parser.parse_args()
    try:
        return asyncio.run(run(args), loop_factory=control_plane_loop)
    except Exception as exc:
        print(json.dumps({"error": "probe_preparation_rejected", "error_type": type(exc).__name__}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
