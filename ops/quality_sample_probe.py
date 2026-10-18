"""One fixed-source synthetic study Run; preserve all outcomes, never retry the task."""

import argparse
import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Any
from uuid import uuid4

import uaw
from uaw.composition import compose
from uaw.evaluation.contracts import Case, Policy
from uaw.evaluation.io import canonical, digest
from uaw.evaluation.runner import evaluate_files
from uaw.infrastructure.db.transactions import RecordTransaction
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.run.background import BackgroundAgent
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.conversation_control import ConversationControls
from uaw.run.deliveries import DeliveryReader
from uaw.run.evaluation_capture import prepare_bundle, read_run, verify_runtime, write_bundle
from uaw.run.execution_clock import ExecutionClocks
from uaw.run.execution_segments import ExecutionSegments
from uaw.run.jobs import JOBS
from uaw.run.quality import parsed
from uaw.run.review_wait import ReviewWaitSources
from uaw.shared.contracts import Principal, RequestMeta
from uaw.shared.conversation import (
    ConversationRequestMeta,
    RunClarificationAnswerRequest,
    RunConversationView,
    RunCorrectionRequest,
)
from uaw.shared.settings import Settings


def attest(runtime: Path, source: str) -> None:
    if not Path(uaw.__file__ or "").resolve().is_relative_to(runtime.resolve()):
        raise ValueError("fixed_runtime_import_required")
    verify_runtime(Path(__file__).resolve().parents[1], runtime, source)


async def probe(args: argparse.Namespace) -> dict[str, Any]:
    environment = json.loads(args.environment.read_bytes())
    runtime = args.environment.parent / "runtime"
    await asyncio.to_thread(attest, runtime, environment["backend_source"])
    study = json.loads(args.study.read_bytes())
    if digest(study) != environment["study_sha256"]:
        raise ValueError("study_changed")
    scenario = next(item for item in study["scenarios"] if item["case_id"] == args.case_id)
    case = parsed(
        Case, next(item for item in study["suite"]["cases"] if item["id"] == args.case_id)
    )
    policy = parsed(Policy, environment["policy"])
    settings = Settings.from_file(args.config).model_copy(
        update={
            "development_principal_id": "a17-" + environment["study_id"] + "-" + args.case_id,
            "agent_execution_enabled": False,
            "installed_state_directory": None,
            "installed_workspace_id": None,
            "blob_directory": args.environment.parent / "blobs",
        }
    )
    assert settings.development_user_token is not None
    actor = Principal(
        id=settings.development_principal_id,
        kind="user",
        auth_session_id="session-"
        + hashlib.sha256(settings.development_user_token.get_secret_value().encode()).hexdigest()[
            :24
        ],
    )
    control = compose(settings)
    output = args.output
    output.mkdir(parents=False, exist_ok=False)
    report: dict[str, Any] = {
        "case_id": args.case_id,
        "started_at": datetime.now(UTC).isoformat(),
        "status": "started",
        "synthetic_not_user_task": True,
        "human_acceptance": False,
        "human_reviews": 0,
        "source_commit": environment["backend_source"],
        "source_principal_id": actor.id,
        "boundaries": [],
        "deliveries": [],
        "patches": [],
    }

    def save() -> None:
        (output / "probe.json").write_bytes(canonical(report) + b"\n")

    def meta(name: str, revision: int | None = None) -> RequestMeta:
        return RequestMeta(
            request_id=name + "-" + uuid4().hex, schema_version="0.1", expected_revision=revision
        )

    save()
    run = queue = driver = None
    started = monotonic()
    try:
        await control.start()
        records, runs = control.records, control.run_service
        assert records and runs and control.blobs
        driver = BackgroundAgent(
            control,
            conversation_clocks=ExecutionClocks(
                records, effects=RunIdleEffects(), reviews=ReviewWaitSources(records)
            ),
            conversation_segments=ExecutionSegments(records),
        )
        queue = await driver.prepare()
        conversation = await runs.create_conversation(
            actor,
            {
                "title": "A17 " + args.case_id,
                "model_choice": {"mode": "explicit", "model_id": environment["model_id"]},
                "memory_policy": {
                    "revision": 0,
                    "read_enabled": False,
                    "contribute_enabled": False,
                    "scope": {"resource_refs": []},
                },
            },
            meta("study-conversation"),
        )

        async def enqueue(tx: RecordTransaction, value: dict[str, Any]) -> None:
            await queue.enqueue(tx, value, actor)

        run = await runs.submit(
            actor,
            {
                "conversation_id": conversation["id"],
                "text": scenario["inputs"][0],
                "attachment_refs": [],
            },
            meta("study-submit"),
            on_admitted=enqueue,
        )
        report.update(run_id=run["id"], conversation_id=conversation["id"])
        run_key = run["id"]
        save()
        controls = ConversationControls(records)
        reader = DeliveryReader(records, control.blobs)

        async def boundary(epoch: int) -> tuple[str, RunConversationView]:
            assert records is not None
            for _ in range(24):
                current = await controls.view(actor, run_key)
                job = (await records.get(actor, JOBS, run_key)).payload
                if current.run["status"] in ("completed", "failed", "cancelled"):
                    return "terminal", current
                if current.question is not None:
                    return "question", current
                if job["stage"] == "delivery":
                    delivery, _ = await reader.read(actor, run_key)
                    if not delivery["stale"] and current.input_revision == epoch:
                        report["deliveries"].append(delivery)
                        save()
                        return "delivery", current
                if job["state"] == "blocked":
                    if not await driver.resume_conversation(actor, run_key):
                        raise ValueError("original_continuation_not_available")
                if monotonic() - started > 360:
                    raise TimeoutError("bounded_study_case_timeout")
                await asyncio.wait_for(queue.tick(), timeout=100)
            raise ValueError("bounded_study_step_limit")

        kind, current = await boundary(1)
        report["boundaries"].append(
            {
                "kind": kind,
                "input_revision": current.input_revision,
                "run_revision": current.run["revision"],
            }
        )
        save()
        if scenario["mode"] in ("clarification", "correction"):
            q = current.question
            expected_kind = "question" if scenario["mode"] == "clarification" else "delivery"
            if kind != expected_kind:
                raise ValueError("expected_" + expected_kind + "_not_observed")
            request_id = "study-patch-" + uuid4().hex
            common: dict[str, Any] = {
                "run_id": run["id"],
                "expected_input_revision": current.input_revision,
                "text": scenario["inputs"][1],
                "attachment_refs": (),
            }
            cm = ConversationRequestMeta(
                request_id=request_id,
                schema_version="0.2",
                expected_revision=int(str(current.run["revision"])),
            )
            if scenario["mode"] == "clarification":
                assert q is not None
                receipt = await controls.answer(
                    actor,
                    RunClarificationAnswerRequest(
                        **common,
                        question_item_id=q.question.item_id,
                        expected_question_revision=q.question.revision,
                    ),
                    cm,
                )
            else:
                receipt = await controls.correct(actor, RunCorrectionRequest(**common), cm)
            report["patches"].append(receipt.wire())
            save()
            if not await driver.resume_conversation(actor, run["id"]):
                raise ValueError("original_resume_rejected")
            kind, current = await boundary(2)
            report["boundaries"].append(
                {
                    "kind": kind,
                    "input_revision": current.input_revision,
                    "run_revision": current.run["revision"],
                }
            )
            report["patches"][-1] = (await controls.lookup(actor, run["id"], request_id)).wire()
        report["status"] = "observed_" + kind
    except Exception as exc:
        report.update(
            status="scenario_failed",
            error_type=type(exc).__name__,
            error_code=str(exc)
            if isinstance(exc, (ValueError, TimeoutError))
            else "owning_receipt_required",
        )
    finally:
        if run is not None and control.run_service and control.records:
            runs, records = control.run_service, control.records
            final_run = await runs.get_run(actor, run["id"])
            if final_run["status"] not in ("completed", "failed", "cancelled"):
                await runs.control(
                    actor,
                    {
                        "run_id": run["id"],
                        "control": {
                            "mode": "cancel",
                            "preserve_refs": [],
                            "reason": "End isolated synthetic study; no human acceptance",
                        },
                    },
                    meta("study-cancel", final_run["revision"]),
                )
                if queue is not None:
                    for _ in range(12):
                        await queue.tick()
                        final_run = await runs.get_run(actor, run["id"])
                        if final_run["status"] in ("completed", "failed", "cancelled"):
                            break
            rows = await read_run(records.database, actor, run["id"])
            (output / "owning-evidence.json").write_bytes(
                canonical(
                    [
                        {
                            "namespace": r.namespace,
                            "id": r.id,
                            "revision": r.revision,
                            "updated_at": r.updated_at,
                            "payload": r.payload,
                        }
                        for r in rows
                    ]
                )
                + b"\n"
            )
            try:
                state = next(r for r in rows if r.namespace == "run.input_sets")
                decisions = [
                    r
                    for r in rows
                    if r.namespace == "agent.conversation.decisions"
                    and r.payload["input_revision"] == state.revision
                ]
                selection = decisions[-1].id if decisions else None
                original_inputs = [
                    next(
                        r.payload["text"]
                        for r in rows
                        if r.namespace == "inputs" and r.id == ref["id"]
                    )
                    for ref in [state.payload["original_input_ref"], *state.payload["patch_refs"]]
                ]
                actual_prompt = original_inputs[0] + "".join(
                    "\n\n用户追加要求\n" + text for text in original_inputs[1:]
                )
                if actual_prompt != case.prompt:
                    case = parsed(
                        Case,
                        {
                            **case.wire(),
                            "version": case.version + "-incomplete",
                            "prompt": actual_prompt,
                        },
                    )
                    report["planned_input_complete"] = False
                else:
                    report["planned_input_complete"] = True
                bundle = prepare_bundle(
                    rows,
                    case,
                    policy,
                    candidate_id="a17-" + args.case_id,
                    source_commit=environment["backend_source"],
                    environment_hash=environment["condition_sha256"],
                    prompt_hash=environment["prompt_sha256"],
                    selected_attempt=selection,
                )
                write_bundle(output / "capture", bundle)
                evaluation = evaluate_files(
                    *(
                        output / "capture" / name
                        for name in (
                            "suite.json",
                            "manifest.json",
                            "observations.jsonl",
                            "reviews.jsonl",
                        )
                    )
                )
                (output / "evaluation.json").write_bytes(canonical(evaluation.wire()) + b"\n")
                report.update(
                    captured=True,
                    selected_attempt=selection,
                    run_revision=next(r.revision for r in rows if r.namespace == "runs"),
                    input_revision=state.revision,
                    model_calls=len(bundle["observations"]),
                    release_gate=evaluation.release_gate.status,
                )
            except Exception as exc:
                report.update(captured=False, capture_error_type=type(exc).__name__)
            report["terminal_run"] = await runs.get_run(actor, run["id"])
        report.update(
            finished_at=datetime.now(UTC).isoformat(),
            elapsed_ms=round((monotonic() - started) * 1000),
        )
        save()
        await control.close()
    print(
        json.dumps(
            {
                key: report.get(key)
                for key in (
                    "case_id",
                    "status",
                    "captured",
                    "model_calls",
                    "elapsed_ms",
                    "error_code",
                )
            }
        )
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("config", "environment", "study", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--case-id", required=True)
    args = parser.parse_args()
    asyncio.run(probe(args), loop_factory=control_plane_loop)


if __name__ == "__main__":
    main()
