"""Publish safe attempt/cost metadata; protected prompts/responses stay local."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def summarize(directory: Path, prefix: str) -> dict:
    rows = []
    for path in sorted(directory.glob("*.json")):
        raw = path.read_bytes()
        data = json.loads(raw)
        if not data.get("request_id", "").startswith(prefix):
            continue
        attempts = {a["id"]: a for a in data.get("model_attempts", [])}
        resources = [a.get("usage", {}).get("resources", {}) for a in attempts.values()]
        report = data.get("verification_report", {})
        rows.append(
            {
                "request_id": data["request_id"],
                "receipt_file": path.name,
                "receipt_sha256": hashlib.sha256(raw).hexdigest(),
                "model_id": data["model_id"],
                "recorded_attempts": len(attempts),
                "attempt_states": dict(Counter(a["state"] for a in attempts.values())),
                "billing_states": dict(
                    Counter(
                        a.get("usage", {}).get("billing_state", "unavailable")
                        for a in attempts.values()
                    )
                ),
                "known_input_tokens": sum(r.get("input_tokens", 0) for r in resources),
                "known_output_tokens": sum(r.get("output_tokens", 0) for r in resources),
                "known_cached_input_tokens": sum(
                    a.get("usage", {}).get("cached_input_tokens", 0) for a in attempts.values()
                ),
                "runtime_probe_passed": data.get("runtime_probe_passed", False),
                "task_semantic_completion": data.get("task_semantic_completion", False),
                "run_status": data.get("final_run_status"),
                "guard_scenario": data.get("guard_scenario"),
                "guard_failure": data.get("completion_guard_failure", {}).get("code"),
                "error_type": data.get("error_type"),
                "error_code": data.get("error_code"),
                "phase_failures": [
                    p["result"]["failure"]["code"]
                    for p in data.get("phases", [])
                    if p["result"].get("failure")
                ],
                "report_outcome": report.get("outcome"),
                "requirement_states": dict(Counter(v["state"] for v in report.get("verdicts", []))),
                "check_states": dict(Counter(c["state"] for c in report.get("checks", []))),
                "attempt_collection_error": data.get("attempt_collection_error"),
            }
        )
    return {
        "scope": "actual provider probes, including original failed attempts",
        "prefix": prefix,
        "recorded_attempts": sum(r["recorded_attempts"] for r in rows),
        "known_input_tokens": sum(r["known_input_tokens"] for r in rows),
        "known_output_tokens": sum(r["known_output_tokens"] for r in rows),
        "known_cached_input_tokens": sum(r["known_cached_input_tokens"] for r in rows),
        "confirmed_monetary_cost": None,
        "cost_note": "Token counts are actual known usage, not monetary invoices. Pending "
        "billing and unknown usage remain unresolved; money holds are retained.",
        "probes": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(".data/agent-probes"))
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(
        json.dumps(summarize(args.directory, args.prefix), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
