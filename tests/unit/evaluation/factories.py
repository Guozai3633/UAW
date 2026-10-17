"""Constructed fixtures only: no real model output or human verification."""

from copy import deepcopy
from pathlib import Path

from uaw.evaluation.io import canonical, digest, text_hash

STAMP = "2026-10-17T00:00:00Z"


def example_files(path: Path, *, attempts=True):
    case = {
        "id": "office-total",
        "version": "1",
        "split": "revision",
        "category": "office",
        "prompt": "核对给定数量：2+3。",
        "rubric": {
            "expected_behavior": "answer",
            "required_facts": ["给定两项之和为5。"],
            "allowed_assumptions": [],
            "retained_requirements": [],
            "critical": True,
        },
        "evidence": [
            {
                "id": "given-table",
                "kind": "provided_material",
                "locator": "fixture row 1",
                "captured_at": STAMP,
                "text": "第一项2；第二项3。",
                "sha256": text_hash("第一项2；第二项3。"),
                "url": None,
            }
        ],
        "review_status": "needs_human_review",
        "human_verification": None,
    }
    suite = {
        "schema_version": "ms-e1.v1",
        "id": "controlled-suite",
        "version": "1",
        "created_at": STAMP,
        "cases": [case],
    }
    observation = {
        "schema_version": "ms-e1.v1",
        "manifest_id": "controlled-candidate",
        "case_id": case["id"],
        "case_version": "1",
        "attempt_id": "answer-1",
        "logical_request_id": "request-1",
        "attempt_number": 1,
        "phase": "answer",
        "status": "succeeded",
        "started_at": STAMP,
        "finished_at": "2026-10-17T00:00:01Z",
        "active_ms": 400,
        "wall_ms": 1000,
        "usage": {
            "input_tokens": 10,
            "output_tokens": 4,
            "model_calls": 1,
            "tool_calls": 0,
            "money": "0.02",
            "currency": "USD",
            "billing_state": "pending",
        },
        "output": {"decision": "reply", "text": "合计5。", "evidence": []},
        "reviewer": None,
        "failure_code": None,
    }
    candidate = {
        "id": "controlled-candidate",
        "provenance": "controlled_fixture",
        "source_commit": "b16c69a92d81124c00fb859ce8123748f56df054",
        "dirty": False,
        "working_tree_sha256": None,
        "suite_sha256": digest(suite),
        "environment_sha256": "1" * 64,
        "model": {
            "provider_id": "not-a-real-provider",
            "provider_version": "1",
            "model_id": "not-a-real-model",
            "model_version": "1",
            "configuration_sha256": "2" * 64,
        },
        "prompts": [{"name": "controlled-prompt", "sha256": "3" * 64}],
        "started_at": STAMP,
        "finished_at": "2026-10-17T00:00:03Z",
        "inventory_complete": True,
        "attempts": [
            {
                "attempt_id": "answer-1",
                "observation_sha256": digest(observation),
                "output_sha256": digest(observation["output"]),
            }
        ]
        if attempts
        else [],
        "selections": [
            {
                "case_id": case["id"],
                "answer_attempt_id": "answer-1" if attempts else None,
                "reviewer_attempt_id": None,
            }
        ],
    }
    manifest = {
        "schema_version": "ms-e1.v1",
        "policy": {
            "id": "registered-policy",
            "reviewer_required": False,
            "baseline_required": False,
            "registered_at": STAMP,
            "max_answer_error_rate": "0",
            "max_reviewer_miss_rate": "0",
            "max_unnecessary_block_rate": "0",
            "max_unsupported_execution_rate": "0",
        },
        "candidate": candidate,
        "baseline": None,
    }
    return {
        "suite": suite,
        "manifest": manifest,
        "observations": [observation] if attempts else [],
        "reviews": [],
    }


def write_files(path: Path, data):
    path.mkdir(parents=True, exist_ok=True)
    for name in ("suite", "manifest"):
        (path / (name + ".json")).write_bytes(canonical(data[name]))
    for name in ("observations", "reviews"):
        (path / (name + ".jsonl")).write_bytes(
            b"".join(canonical(row) + b"\n" for row in data[name])
        )
    return tuple(
        path / name
        for name in ("suite.json", "manifest.json", "observations.jsonl", "reviews.jsonl")
    )


def repin(data):
    result = deepcopy(data)
    result["manifest"]["candidate"]["suite_sha256"] = digest(result["suite"])
    for manifest in (result["manifest"]["candidate"], result["manifest"].get("baseline")):
        if manifest is None:
            continue
        manifest["attempts"] = [
            {
                "attempt_id": row["attempt_id"],
                "observation_sha256": digest(row),
                "output_sha256": digest(row["output"]) if row["output"] is not None else None,
            }
            for row in result["observations"]
            if row["manifest_id"] == manifest["id"]
        ]
    return result


def add_review(
    data,
    *,
    correct=False,
    unnecessary=False,
    unsupported=False,
    preserved=True,
    acceptable=False,
    critical=False,
    basis="controlled_test",
):
    """Explicit constructed label, never a genuine human verification."""
    case = data["suite"]["cases"][0]
    row = next(
        o for o in data["observations"] if o["phase"] == "answer" and o["status"] == "succeeded"
    )
    data["reviews"].append(
        {
            "schema_version": "ms-e1.v1",
            "id": "controlled-review-" + row["attempt_id"],
            "manifest_id": row["manifest_id"],
            "case_id": row["case_id"],
            "case_version": row["case_version"],
            "attempt_id": row["attempt_id"],
            "output_sha256": digest(row["output"]),
            "case_sha256": digest(case),
            "basis": basis,
            "reviewer_id": "controlled-fixture-labeler",
            "reviewed_at": "2026-10-17T00:00:04Z",
            "evidence_sha256": [e["sha256"] for e in case["evidence"]],
            "evidence_reviewed": True,
            "labels": {
                "answer_correct": correct,
                "unnecessary_block": unnecessary,
                "unsupported_execution": unsupported,
                "requirements_preserved": preserved,
                "acceptable": acceptable,
                "critical_error": critical,
            },
            "notes": "Controlled label only; not human review or real model evidence.",
        }
    )
    return data


def add_reviewer(data, *, verdict="passed"):
    answer = next(
        o for o in data["observations"] if o["phase"] == "answer" and o["status"] == "succeeded"
    )
    row = deepcopy(answer)
    row.update(
        attempt_id="reviewer-1",
        logical_request_id="reviewer-request",
        attempt_number=1,
        phase="reviewer",
        output=None,
        reviewer={
            "target_attempt_id": answer["attempt_id"],
            "target_output_sha256": digest(answer["output"]),
            "verdict": verdict,
        },
        started_at="2026-10-17T00:00:02Z",
        finished_at="2026-10-17T00:00:03Z",
        active_ms=500,
        usage={
            "input_tokens": 5,
            "output_tokens": 2,
            "model_calls": 1,
            "tool_calls": 0,
            "money": "0.04",
            "currency": "USD",
            "billing_state": "confirmed",
        },
    )
    data["observations"].append(row)
    data["manifest"]["candidate"]["selections"][0]["reviewer_attempt_id"] = "reviewer-1"
    return repin(data)
