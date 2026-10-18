"""Summarize previously captured synthetic web runs without replaying any request.

Inputs are private records-timeline.json exports and immutable HTTP probe receipts.
Output excludes raw prompts, provider protocol bytes, credentials and human ratings.
This reports observed stages, not inferred provider-only time or a sample P95.
"""

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

Payload = dict[str, Any]


def elapsed(start: str | None, end: str | None) -> float | None:
    if start is None or end is None:
        return None
    return round(
        (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds() * 1000, 3
    )


def first_time(rows: list[Payload], namespace: str, **values: Any) -> str | None:
    return next(
        (
            row["created_at"]
            for row in rows
            if row["namespace"] == namespace
            and all(row["payload"].get(k) == v for k, v in values.items())
        ),
        None,
    )


def summary(
    directory: Path,
    extra_probes: list[Path],
    prior_runs: list[Payload],
    browser_runs: list[Payload],
) -> Payload:
    source = directory / "records-timeline.json"
    raw = source.read_bytes()
    data = json.loads(raw)
    rows, versions = data["records"], data["versions"]
    probes: list[Payload] = []
    setup_failures: list[Payload] = []
    for path in [*sorted(directory.glob("http-probe*.json")), *extra_probes]:
        value = json.loads(path.read_bytes())
        cases = value.get("cases", [])
        # One first probe stopped after HTTP202 before saving its Run ID. Match
        # its exact accepted conversation path, never text similarity or timing alone.
        accepted = [
            r
            for r in value.get("requests", [])
            if r["method"] == "POST" and r["path"].endswith("/turns") and r["status"] == 202
        ]
        for case in cases:
            case = {**case, "source_commit": value["source"], "receipt": path.name}
            if not case.get("run_id") and len(cases) == 1 and len(accepted) == 1:
                conversation_id = accepted[0]["path"].split("/")[-2]
                matches = [
                    row["payload"]
                    for row in rows
                    if row["namespace"] == "runs"
                    and row["payload"]["conversation_id"] == conversation_id
                ]
                if len(matches) == 1:
                    case.update(
                        run_id=matches[0]["id"],
                        accepted_ms=accepted[0]["elapsed_ms"],
                        recovered_from_exact_accepted_conversation=True,
                    )
            probes.append(case)
        if value.get("status") == "failed":
            setup_failures.append(
                {
                    "receipt": path.name,
                    "failure_type": value.get("failure_type"),
                    "accepted_cases": len(value.get("cases", [])),
                }
            )
    manifest = json.loads((directory / "environment.json").read_bytes())
    if manifest.get("copied_user_records") != 0 or not manifest.get("synthetic_principal"):
        raise ValueError("Only an explicitly isolated synthetic capture is supported")
    if any(
        row["payload"]["owner_id"] != manifest["synthetic_principal"]
        for row in rows
        if row["namespace"] == "conversations"
    ):
        raise ValueError("Capture conversations differ from the synthetic owner")
    attempts = [row["payload"] for row in rows if row["namespace"] == "model.attempts"]
    runs = []
    for run in (row["payload"] for row in rows if row["namespace"] == "runs"):
        run_id = run["id"]
        own = [
            row
            for row in versions
            if row["payload"].get("run_id", row["payload"].get("run_ref", {}).get("id")) == run_id
        ]

        probe = next((case for case in probes if case.get("run_id") == run_id), {})
        prior = next((row for row in prior_runs if row.get("run_id") == run_id), {})
        browser = next((row for row in browser_runs if row.get("run_id") == run_id), {})
        submit = probe.get("submit_started_at") or browser.get("submit_started_at")
        queued = first_time(own, "run.background.jobs", state="queued", stage="admitted")
        claimed = first_time(own, "run.background.jobs", state="working", stage="admitted")
        step = first_time(own, "run.background.jobs", state="working", stage="step")
        model_claimed = first_time(own, "model.invocations", state="claimed")
        model_prepared = first_time(own, "model.attempts", state="prepared")
        model_received = first_time(own, "model.attempts", state="received")
        model_finished = first_time(own, "model.invocations", state="finished")
        operation: Payload = next(
            (
                row["payload"]
                for row in rows
                if row["namespace"] == "agent.loop.operations"
                and row["payload"].get("context", {}).get("run_id") == run_id
                and row["payload"].get("step") == 1
            ),
            {},
        )
        snapshot_id = operation.get("snapshot_ref", {}).get("id")
        snapshot_created = next(
            (
                row["created_at"]
                for row in versions
                if row["namespace"] == "context.snapshots" and row["resource_id"] == snapshot_id
            ),
            None,
        )
        stream: Payload = next(
            (
                row["payload"]
                for row in rows
                if row["namespace"] == "run.conversation.streams"
                and row["payload"]["run_id"] == run_id
            ),
            {},
        )
        item_id = stream.get("item_id")
        replies = [
            row
            for row in own
            if row["namespace"] == "items"
            and row["payload"].get("type") == "agent_message"
            and (not item_id or row["resource_id"] == item_id)
        ]
        displayed_versions = [
            {
                "item_id": row["resource_id"],
                "revision": row["revision"],
                "at": row["created_at"],
                "status": row["payload"]["status"],
                "characters": len(row["payload"]["text"]),
                "text_sha256": hashlib.sha256(row["payload"]["text"].encode()).hexdigest(),
            }
            for row in replies
        ]
        calls = [attempt for attempt in attempts if attempt["run_id"] == run_id]
        report_models = [attempt for attempt in calls if attempt["id"].startswith("evaluation-")]
        bundle: Payload = next(
            (
                row["payload"]
                for row in rows
                if row["namespace"] == "agent.completion.bundles"
                and row["payload"]["context"]["run_id"] == run_id
            ),
            {},
        )
        delivery = [
            row
            for row in versions
            if row["resource_id"]
            in (bundle.get("artifact_ref", {}).get("id"), bundle.get("report_ref", {}).get("id"))
        ]
        artifact_registered = first_time(delivery, "workspace.artifacts")
        report_registered = first_time(delivery, "agent.completion.reports")
        runs.append(
            {
                "run_id": run_id,
                "source_commit": (
                    probe.get("source_commit")
                    or prior.get("source_commit")
                    or browser.get("source_commit")
                    or manifest["backend_source"]
                ),
                "source_evidence": (
                    "http_probe_receipt"
                    if probe
                    else "prior_frozen_summary"
                    if prior
                    else "browser_dom_observation"
                    if browser
                    else "export_environment_manifest"
                ),
                "http_receipt": probe.get("receipt"),
                "case_id": probe.get("case_id") or browser.get("case_id"),
                "run_status_at_capture": run["status"],
                "submit_started_at": submit,
                "accepted_ms": probe.get("accepted_ms"),
                "queue_wait_ms": elapsed(queued, claimed),
                "claimed_to_step_ms": elapsed(claimed, step),
                "step_to_model_claim_ms": elapsed(step, model_claimed),
                "context_snapshot_id": snapshot_id,
                "first_context_record_at": snapshot_created,
                "step_to_fixed_context_record_ms": elapsed(step, snapshot_created),
                "fixed_context_record_to_model_claim_ms": elapsed(snapshot_created, model_claimed),
                "model_claim_to_attempt_prepared_ms": elapsed(model_claimed, model_prepared),
                "submit_to_first_reply_version_timestamp_ms": elapsed(
                    submit, displayed_versions[0]["at"] if displayed_versions else None
                ),
                "first_provider_content_at": stream.get("provider_first_content_at"),
                "first_displayable_text_at": stream.get("first_text_at"),
                "first_text_to_version_timestamp_ms": elapsed(
                    stream.get("first_text_at"),
                    displayed_versions[0]["at"] if displayed_versions else None,
                ),
                "first_text_to_commit_ack_ms": elapsed(
                    stream.get("first_text_at"), stream.get("first_committed_at")
                ),
                "browser_submit_to_accepted_ms": browser.get("submit_to_accepted_ms"),
                "browser_submit_to_first_render_ms": browser.get("submit_to_first_render_ms"),
                "commit_ack_to_first_render_ms": elapsed(
                    stream.get("first_committed_at"), browser.get("first_rendered_at")
                ),
                "provider_http_to_first_content_ms": elapsed(
                    stream.get("provider_started_at"), stream.get("provider_first_content_at")
                ),
                "provider_content_generation_ms": elapsed(
                    stream.get("provider_first_content_at"), stream.get("provider_last_content_at")
                ),
                "first_content_to_received_checkpoint_ms": elapsed(
                    stream.get("first_provider_at"), stream.get("received_at")
                ),
                "prepared_to_received_ms": elapsed(model_prepared, model_received),
                "model_finished_to_final_reply_commit_ms": elapsed(
                    model_finished,
                    next((v["at"] for v in displayed_versions if v["status"] == "completed"), None),
                ),
                "http_first_item_observed_ms": probe.get("first_item_observed_ms"),
                "http_observed_end_ms": probe.get("end_to_end_ms"),
                "observed_boundary": probe.get("boundary", probe.get("final_state")),
                "submit_to_run_ended_ms": elapsed(submit, run.get("ended_at")),
                "first_reply_version_to_http_observation_ms": (
                    round(
                        probe["first_item_observed_ms"]
                        - elapsed(submit, displayed_versions[0]["at"]),
                        3,
                    )
                    if submit
                    and displayed_versions
                    and probe.get("first_item_observed_ms") is not None
                    else None
                ),
                "model_finished_to_artifact_registration_ms": elapsed(
                    model_finished, artifact_registered
                ),
                "model_finished_to_report_registration_ms": elapsed(
                    model_finished, report_registered
                ),
                "formal_verifier_calls": len(report_models),
                "formal_verifier_gateway_wall_ms": sum(
                    attempt.get("usage", {}).get("resources", {}).get("wall_time_ms", 0)
                    for attempt in report_models
                ),
                "display_versions": displayed_versions,
                "model_calls": len(calls),
                "retry_count": sum(attempt["id"].startswith("retry-") for attempt in calls),
            }
        )
    fees = []
    for attempt in attempts:
        usage = attempt.get("usage", {})
        resources = usage.get("resources", {})
        fees.append(
            {
                "attempt_id": attempt["id"],
                "run_id": attempt["run_id"],
                "state": attempt["state"],
                "failure_code": attempt.get("failure", {}).get("code"),
                "billing_state": usage.get("billing_state"),
                "input_tokens": resources.get("input_tokens"),
                "output_tokens": resources.get("output_tokens"),
                "cached_input_tokens": usage.get("cached_input_tokens"),
                "gateway_wall_ms": resources.get("wall_time_ms"),
                "money": resources.get("money"),
                "currency": resources.get("currency"),
                "original_raw_receipt_saved": bool(attempt.get("response_ref")),
                "provider_receipt_id": usage.get("provider_receipt_id"),
                "fixed_model_id": attempt["actual_config"]["model_id"],
                "provider_model_name": attempt["actual_config"]["provider_model_name"],
                "max_output_tokens": attempt["actual_config"]["max_output_tokens"],
                "reasoning_level": attempt["actual_config"].get("reasoning_level"),
            }
        )
    return {
        "source_commit": manifest["backend_source"],
        "export_sha256": hashlib.sha256(raw).hexdigest(),
        "captured_through": max(row["updated_at"] for row in rows),
        "synthetic_identity_only": True,
        "setup_failures": setup_failures,
        "runs": runs,
        "fees": fees,
        "totals": {
            "model_calls": len(fees),
            "retry_count": sum(fee["attempt_id"].startswith("retry-") for fee in fees),
            "failed_attempts": sum(fee["state"] == "failed" for fee in fees),
            "known_input_tokens": sum(fee["input_tokens"] or 0 for fee in fees),
            "known_output_tokens": sum(fee["output_tokens"] or 0 for fee in fees),
            "attempts_without_token_usage": sum(
                fee["input_tokens"] is None or fee["output_tokens"] is None for fee in fees
            ),
            "pending_billing": sum(fee["billing_state"] == "pending" for fee in fees),
            "unknown_money": sum(fee["money"] is None for fee in fees),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--candidate-http", type=Path, action="append", default=[])
    parser.add_argument("--prior-summary", type=Path)
    parser.add_argument("--browser-observations", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prior = json.loads(args.prior_summary.read_bytes()) if args.prior_summary else {}
    browser = (
        json.loads(args.browser_observations.read_bytes()) if args.browser_observations else {}
    )
    result: Payload = {
        "schema_version": "uaw.a18-latency-observations.v1",
        "baseline": summary(
            args.baseline, [], prior.get("baseline", {}).get("runs", []), browser.get("runs", [])
        ),
        "candidate": summary(
            args.candidate,
            args.candidate_http,
            prior.get("candidate", {}).get("runs", []),
            browser.get("runs", []),
        ),
        "quality_human_judgments": "pending",
        "p95": None,
        "limits": [
            "Few sequential samples; not randomized or a stable P95.",
            "HTTP polling observations are not browser paint measurements.",
            "Gateway wall time includes live checks; provider-only time is not inferred.",
            "Null is unobserved, never zero. Frozen exports are not current service state.",
            "Prior stage calls retain the source recorded by their original HTTP probe receipt.",
            "Case names cold/warm denote sample order, not guaranteed process/cache temperature.",
            "Baseline restarted between first/repeated samples; load was not held constant.",
            "DB version timestamps precede commit acknowledgement; do not call them commit time.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: result[key]["totals"] for key in ("baseline", "candidate")}))


if __name__ == "__main__":
    main()
