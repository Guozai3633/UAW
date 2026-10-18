"""Read-only owning Run evidence -> C's frozen offline format.

No model, execution, human labels or release decision is performed here.
The initial adapter supports one conversation-v1 Run without Tool effects.
"""

import hashlib
import html
import io
import json
import subprocess
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select, text

from uaw.evaluation.contracts import Case, Manifest, Observation, Policy, Suite
from uaw.evaluation.io import canonical, digest, publish_report
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.session import Database
from uaw.shared.contracts import Principal
from uaw.shared.schema import validate_contract

Payload = dict[str, Any]
LIMIT = 512


def environment_hash(environment: Payload) -> str:
    """Keep old environment pins stable; explicitly bind isolated probe overrides."""
    fields = {
        key: environment[key]
        for key in ("dependency_inventory_sha256", "dependency_lock_sha256", "settings_sha256")
    }
    if "evaluation_execution_scope" in environment:
        fields["execution_scope_sha256"] = digest(environment["evaluation_execution_scope"])
    return digest(fields)


class CaptureError(ValueError):
    """Only a bounded code may be printed; never private values."""


@dataclass(frozen=True)
class EvidenceRow:
    namespace: str
    id: str
    revision: int
    updated_at: str
    payload: Payload


def instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise CaptureError("timestamp_without_timezone")
    return parsed.astimezone(UTC)


def verify_runtime(repository: Path, runtime: Path, commit: str) -> Payload:
    """Compare the immutable runtime sources with exact committed bytes."""
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise CaptureError("invalid_commit")
    raw = subprocess.check_output(
        [
            "git",
            "archive",
            "--format=zip",
            commit,
            "src/uaw",
            "apps/local_runner",
            "contracts",
            "pyproject.toml",
            "uv.lock",
        ],
        cwd=repository,
        stderr=subprocess.DEVNULL,
    )
    hashes = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            path = (runtime / entry.filename).resolve(strict=True)
            if not path.is_relative_to(runtime.resolve(strict=True)):
                raise CaptureError("runtime_path_escape")
            expected = hashlib.sha256(archive.read(entry)).hexdigest()
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise CaptureError("runtime_source_changed")
            hashes[entry.filename] = expected
    for package in (runtime / "src/uaw", runtime / "apps/local_runner"):
        if any(p.relative_to(runtime).as_posix() not in hashes for p in package.rglob("*.py")):
            raise CaptureError("runtime_extra_python_source")
    return {"source_commit": commit, "file_count": len(hashes), "files_sha256": digest(hashes)}


async def read_run(database: Database, actor: Principal, run_id: str) -> tuple[EvidenceRow, ...]:
    """One consistent, database-enforced read-only transaction; no platform secrets."""
    async with database.sessions.begin() as session:
        await session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        run = await session.get(RecordRow, (actor.id, "runs", run_id))
        if actor.kind != "user" or run is None or run.deleted:
            raise CaptureError("run_owner_missing")
        conversation = await session.get(
            RecordRow, (actor.id, "conversations", run.payload["conversation_id"])
        )
        if (
            conversation is None
            or conversation.deleted
            or conversation.payload["owner_id"] != actor.id
        ):
            raise CaptureError("conversation_owner_missing")
        inputs = await session.get(RecordRow, (actor.id, "run.input_sets", run_id))
        if inputs is None:
            raise CaptureError("input_set_missing")
        refs = [inputs.payload["original_input_ref"], *inputs.payload["patch_refs"]]
        rows = list(
            await session.scalars(
                select(RecordRow)
                .where(
                    RecordRow.principal_id == actor.id,
                    RecordRow.deleted.is_(False),
                    (RecordRow.payload["run_id"].as_string() == run_id)
                    | (RecordRow.payload["context"]["run_id"].as_string() == run_id)
                    | (RecordRow.payload["run_ref"]["id"].as_string() == run_id)
                    | (
                        RecordRow.namespace.in_(("runs", "run.input_sets", "run.bindings"))
                        & (RecordRow.resource_id == run_id)
                    )
                    | (
                        (RecordRow.namespace == "inputs")
                        & RecordRow.resource_id.in_([r["id"] for r in refs])
                    ),
                )
                .limit(LIMIT + 1)
            )
        )
        if len(rows) > LIMIT:
            raise CaptureError("capture_inventory_limit")
        invocation_ids = [r.resource_id for r in rows if r.namespace == "model.invocations"]
        rows.extend(
            await session.scalars(
                select(RecordRow).where(
                    RecordRow.principal_id == actor.id,
                    RecordRow.deleted.is_(False),
                    RecordRow.namespace == "model.outputs",
                    RecordRow.resource_id.in_(invocation_ids),
                )
            )
        )
        if len(rows) > LIMIT:
            raise CaptureError("capture_inventory_limit")
        return tuple(
            EvidenceRow(
                r.namespace,
                r.resource_id,
                r.revision,
                r.updated_at.astimezone(UTC).isoformat(),
                r.payload,
            )
            for r in rows
        )


def prepare_bundle(
    rows: tuple[EvidenceRow, ...],
    case: Case,
    policy: Policy,
    *,
    candidate_id: str,
    source_commit: str,
    environment_hash: str,
    prompt_hash: str,
    selected_attempt: str | None,
) -> Payload:
    index = {(r.namespace, r.id): r for r in rows}
    if len(index) != len(rows):
        raise CaptureError("duplicate_record")
    runs = [r for r in rows if r.namespace == "runs"]
    if len(runs) != 1:
        raise CaptureError("exactly_one_run_required")
    run = runs[0].payload
    validate_contract("RunRecord", run)
    run_id = run["id"]
    if run["status"] not in ("completed", "failed", "cancelled"):
        raise CaptureError("capture_requires_terminal_run")
    if any(r.namespace in ("tool.contexts", "tool.effects", "tool.dispatch.intents") for r in rows):
        raise CaptureError("tool_capture_not_supported")
    state = index[("run.input_sets", run_id)].payload
    refs = [state["original_input_ref"], *state["patch_refs"]]
    originals = []
    for ref in refs:
        row = index[("inputs", ref["id"])]
        if (
            str(row.revision) != ref["version"]
            or (ref.get("content_hash") and digest(row.payload) != ref["content_hash"])
            or row.payload["conversation_id"] != run["conversation_id"]
        ):
            raise CaptureError("input_binding_mismatch")
        originals.append(row.payload["text"])
    # Explicit documented transcript format; no summary or reconstructed wording.
    actual_prompt = originals[0] + "".join("\n\n用户追加要求\n" + s for s in originals[1:])
    if case.prompt != actual_prompt:
        raise CaptureError("case_prompt_differs_from_original_inputs")
    invocations = sorted(
        (r for r in rows if r.namespace == "model.invocations"),
        key=lambda r: (r.payload["created_at"], r.id),
    )
    attempts = {r.id: r for r in rows if r.namespace == "model.attempts"}
    if not invocations or set(attempts) - {r.id for r in invocations}:
        raise CaptureError("invocation_inventory_mismatch")
    pins, observations, answers, model_pins = [], [], {}, set()
    configs = {}
    logical_counts: dict[str, int] = {}
    for inv in invocations:
        value = inv.payload
        validate_contract("ModelInvocation", value)
        if value["run_id"] != run_id:
            raise CaptureError("invocation_run_mismatch")
        logical = value["operation_id"]
        logical_counts[logical] = logical_counts.get(logical, 0) + 1
        number = logical_counts[logical]
        meta = attempts.get(inv.id)
        if meta is not None:
            validate_contract("ModelAttemptRecord", meta.payload)
            if meta.payload["run_id"] != run_id or meta.payload["invocation_id"] != inv.id:
                raise CaptureError("attempt_run_mismatch")
        config = value["request"]["model_config"]
        normalized = {k: v for k, v in config.items() if k != "policy_ref"}
        configs[digest(normalized)] = normalized
        provider = config["provider_ref"]
        model_pins.add(
            (
                config["model_id"],
                str(config["catalog_revision"]),
                provider["id"],
                provider["version"],
            )
        )
        result = value.get("result", {})
        output = result.get("payload") if result.get("kind") == "ok" else None
        evaluation = index.get(("model.evaluation.inputs", inv.id))
        phase = "reviewer" if evaluation else "answer"
        usage = meta.payload.get("usage", {}) if meta else {}
        resources = usage.get("resources", {})
        start = instant(value["created_at"])
        end = instant(meta.updated_at if meta else inv.updated_at)
        wall = int((end - start).total_seconds() * 1000)
        active = resources.get("wall_time_ms")
        # v1 requires a measured duration. Reject an unsupported inventory as a
        # whole rather than silently omitting a call or inventing zero duration.
        if active is None:
            raise CaptureError("active_duration_unobserved")
        if end < start or type(active) is not int or not 0 <= active <= wall + 1:
            raise CaptureError("attempt_interval_unproven")
        failure = result.get("failure") or (meta.payload.get("failure") if meta else None)
        status = "unknown" if value["state"] != "finished" else "failed"
        answer = None
        if output is not None:
            validate_contract("ModelOutput", output)
            actual_row = index.get(("model.outputs", inv.id))
            if actual_row is None or actual_row.payload != output:
                raise CaptureError("owning_output_mismatch")
            actual = output["actual_config"]
            if any(actual.get(k) != v for k, v in config.items()):
                raise CaptureError("output_model_config_mismatch")
            if meta is None or output["usage"] != usage:
                raise CaptureError("output_usage_unproven")
            if output["finish_reason"] == "stop" and not output["tool_calls"]:
                if phase == "answer":
                    decision = output.get("structured_data", {})
                    validate_contract("FirstDecision", decision)
                    if decision["action"] == "tool":
                        raise CaptureError("tool_capture_not_supported")
                    source = index.get(("agent.conversation.decisions", inv.id))
                    if source is None or source.payload["decision"] != decision:
                        raise CaptureError("decision_evidence_missing")
                    answer = {
                        "decision": decision["action"],
                        "text": decision.get("text", decision.get("question", {}).get("text", "")),
                        "evidence": [
                            {
                                "kind": "content",
                                "id": inv.id,
                                "version": "1",
                                "sha256": digest(output),
                            }
                        ],
                    }
                    answers[inv.id] = answer
                status = "succeeded"
            else:
                failure = {
                    "code": "agent_output_truncated"
                    if output["finish_reason"] == "length"
                    else "agent_decision_invalid"
                }
        code = (
            None
            if status == "succeeded"
            else (
                failure.get("code", "model_outcome_unknown") if failure else "model_outcome_unknown"
            )
        )
        observation = (
            Observation.model_validate_json(
                canonical(
                    {
                        "schema_version": "ms-e1.v1",
                        "manifest_id": candidate_id,
                        "case_id": case.id,
                        "case_version": case.version,
                        "attempt_id": inv.id,
                        "logical_request_id": logical,
                        "attempt_number": number,
                        "phase": phase,
                        "status": status,
                        "started_at": start.isoformat(),
                        "finished_at": end.isoformat(),
                        "active_ms": min(active, wall),
                        "wall_ms": wall,
                        "usage": {
                            "input_tokens": resources.get("input_tokens"),
                            "output_tokens": resources.get("output_tokens"),
                            "model_calls": resources.get("model_calls"),
                            "tool_calls": resources.get("tool_calls"),
                            "money": resources.get("money"),
                            "currency": resources.get("currency", "USD"),
                            "billing_state": usage.get("billing_state", "unknown"),
                        },
                        "output": answer,
                        "reviewer": None,
                        "failure_code": code,
                    }
                )
            )
            if phase != "reviewer"
            else None
        )
        # Reviewer targets are resolved after every actual answer has been collected.
        observations.append(
            observation.wire()
            if observation
            else {
                "review_pending": True,
                "invocation": inv,
                "meta": meta,
                "usage": usage,
                "resources": resources,
                "start": start,
                "end": end,
                "wall": wall,
                "active": min(active, wall),
                "status": status,
                "code": code,
                "output": output,
                "evaluation": evaluation,
                "number": number,
                "logical": logical,
            }
        )
    for i, obs in enumerate(observations):
        if not obs.get("review_pending"):
            continue
        evaluation = obs["evaluation"].payload
        targets = [s for s in evaluation["sources"] if s["namespace"] == "model.outputs"]
        if len(targets) != 1 or targets[0]["ref"]["id"] not in answers:
            raise CaptureError("reviewer_target_unproven")
        ref = targets[0]["ref"]
        target = ref["id"]
        target_row = index[("model.outputs", target)]
        if (
            evaluation["context"]["run_id"] != run_id
            or str(target_row.revision) != ref["version"]
            or (ref.get("content_hash") and digest(target_row.payload) != ref["content_hash"])
        ):
            raise CaptureError("reviewer_target_binding_mismatch")
        verdict = "unavailable"
        if obs["status"] == "succeeded":
            verdicts = obs["output"].get("structured_data", {}).get("verdicts", [])
            if not verdicts:
                raise CaptureError("reviewer_verdict_missing")
            verdict = "passed" if all(v["state"] == "passed" for v in verdicts) else "failed"
        observations[i] = Observation.model_validate_json(
            canonical(
                {
                    "schema_version": "ms-e1.v1",
                    "manifest_id": candidate_id,
                    "case_id": case.id,
                    "case_version": case.version,
                    "attempt_id": obs["invocation"].id,
                    "logical_request_id": obs["logical"],
                    "attempt_number": obs["number"],
                    "phase": "reviewer",
                    "status": obs["status"],
                    "started_at": obs["start"].isoformat(),
                    "finished_at": obs["end"].isoformat(),
                    "active_ms": obs["active"],
                    "wall_ms": obs["wall"],
                    "usage": {
                        "input_tokens": obs["resources"].get("input_tokens"),
                        "output_tokens": obs["resources"].get("output_tokens"),
                        "model_calls": obs["resources"].get("model_calls"),
                        "tool_calls": obs["resources"].get("tool_calls"),
                        "money": obs["resources"].get("money"),
                        "currency": obs["resources"].get("currency", "USD"),
                        "billing_state": obs["usage"].get("billing_state", "unknown"),
                    },
                    "output": None,
                    "reviewer": {
                        "target_attempt_id": target,
                        "target_output_sha256": digest(answers[target]),
                        "verdict": verdict,
                    },
                    "failure_code": obs["code"],
                }
            )
        ).wire()
    if len(model_pins) != 1 or selected_attempt is not None and selected_attempt not in answers:
        raise CaptureError("selected_output_or_fixed_model_unproven")
    if selected_attempt is not None:
        selected = index[("agent.conversation.decisions", selected_attempt)].payload
        validate_contract("FirstDecisionRecord", selected)
        if selected["input_revision"] != state["revision"]:
            raise CaptureError("selected_output_is_old_input")
    reviewers = [
        o["attempt_id"]
        for o in observations
        if o["reviewer"] and o["reviewer"]["target_attempt_id"] == selected_attempt
    ]
    model, version, provider_id, provider_version = next(iter(model_pins))
    suite = Suite.model_validate_json(
        canonical(
            {
                "schema_version": "ms-e1.v1",
                "id": candidate_id + "-suite",
                "version": "1",
                "created_at": policy.registered_at,
                "cases": [case.wire()],
            }
        )
    )
    for obs in observations:
        pins.append(
            {
                "attempt_id": obs["attempt_id"],
                "observation_sha256": digest(obs),
                "output_sha256": digest(obs["output"]) if obs["output"] else None,
            }
        )
    manifest = Manifest.model_validate_json(
        canonical(
            {
                "schema_version": "ms-e1.v1",
                "policy": policy.wire(),
                "baseline": None,
                "candidate": {
                    "id": candidate_id,
                    "provenance": "actual_candidate",
                    "source_commit": source_commit,
                    "dirty": False,
                    "working_tree_sha256": None,
                    "suite_sha256": digest(suite.wire()),
                    "environment_sha256": environment_hash,
                    "model": {
                        "model_id": model,
                        "model_version": version,
                        "provider_id": provider_id,
                        "provider_version": provider_version,
                        "configuration_sha256": digest(
                            {
                                "consumed_configs": sorted(configs),
                                "admission": index[("run.bindings", run_id)].payload[
                                    "configuration_ref"
                                ],
                            }
                        ),
                    },
                    "prompts": [{"name": "conversation-v1", "sha256": prompt_hash}],
                    "started_at": min((o["started_at"] for o in observations), key=instant),
                    "finished_at": max((o["finished_at"] for o in observations), key=instant),
                    "inventory_complete": True,
                    "attempts": pins,
                    "selections": [
                        {
                            "case_id": case.id,
                            "answer_attempt_id": selected_attempt,
                            "reviewer_attempt_id": reviewers[-1] if reviewers else None,
                        }
                    ],
                },
            }
        )
    )
    return {
        "suite": suite.wire(),
        "manifest": manifest.wire(),
        "observations": observations,
        "reviews": [],
        "audit": {
            "scope": "one_explicit_Run_all_model_invocations_no_Tool",
            "run_id": run_id,
            "input_refs": refs,
            "record_hashes": [
                {
                    "namespace": r.namespace,
                    "id": r.id,
                    "revision": r.revision,
                    "sha256": digest(r.payload),
                }
                for r in rows
            ],
            "human_review_created": False,
            "baseline_created": False,
            "timestamps": "invocation_created_to_observed_attempt_record_update",
            "active_ms": "provider_observed_duration_not_user_total_wait",
            "active_ms_unobserved_attempts": [
                r.id
                for r in invocations
                if r.id not in attempts
                or "wall_time_ms"
                not in attempts[r.id].payload.get("usage", {}).get("resources", {})
            ],
            "consumed_model_configs": [configs[k] for k in sorted(configs)],
        },
    }


def write_bundle(directory: Path, bundle: Payload) -> None:
    """Exclusive output directory; partial failure is retained, never overwritten."""
    directory.mkdir(parents=False, exist_ok=False)
    for name in ("suite", "manifest", "audit"):
        publish_report(directory / (name + ".json"), bundle[name])
    for name in ("observations", "reviews"):
        with (directory / (name + ".jsonl")).open("xb") as stream:
            for value in bundle[name]:
                stream.write(canonical(value) + b"\n")
    body = "<!doctype html><meta charset=utf-8><title>UAW 待人工核对</title>"
    body += (
        '<meta http-equiv="Content-Security-Policy" '
        "content=\"default-src 'none'; style-src 'unsafe-inline'\">"
    )
    body += (
        "<style>body{max-width:900px;margin:40px auto;font:16px/1.7 sans-serif}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f5fa;padding:20px}</style>"
    )
    body += (
        "<h1>待人工核对：实际任务与回答</h1><p>没有人工评分。模型核验不是事实真值；"
        "历史采集不代表预登记实验或版本对比。</p>"
    )
    case = bundle["suite"]["cases"][0]
    for label, value in (("原任务及实际追加输入", case["prompt"]), ("待核对标准", case["rubric"])):
        body += (
            "<h2>"
            + label
            + "</h2><pre>"
            + html.escape(
                value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
            )
            + "</pre>"
        )
    for obs in bundle["observations"]:
        body += "<h2>" + html.escape(obs["phase"] + " · " + obs["attempt_id"]) + "</h2><pre>"
        body += html.escape(json.dumps(obs, ensure_ascii=False, indent=2)) + "</pre>"
    (directory / "review.html").write_text(body, encoding="utf-8")
