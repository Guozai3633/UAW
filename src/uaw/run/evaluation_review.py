"""Owning offline review packet and explicit operator-supplied review import.

This adapter never judges an answer, executes a Run or authenticates a human.
C's frozen contracts/evaluator remain the authority for scoring and release.
"""

import base64
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AfterValidator, Field

from uaw.evaluation.contracts import (
    Case,
    Hash,
    Identifier,
    Labels,
    Manifest,
    NamedHash,
    Review,
    StrictModel,
    Suite,
    Text,
    Utc,
)
from uaw.evaluation.io import canonical, digest, publish_report, read_bounded, text_hash
from uaw.evaluation.reader import Bundle, load_bundle, record

FILES = ("suite.json", "manifest.json", "observations.jsonl", "reviews.jsonl")
TEMPLATE = Path(__file__).resolve().parents[1] / "resources/reviews/human-review-v1.html"


def _confirmed(value: bool) -> bool:
    if value is not True:
        raise ValueError("explicit_confirmation_required")
    return value


# Literal[True] accepts numeric 1 in Pydantic; strict bool plus a validator does not.
Confirmed = Annotated[bool, AfterValidator(_confirmed)]


class ReviewInputError(ValueError):
    """Safe diagnostic code; never includes a private answer or filesystem path."""


class ReviewTarget(StrictModel):
    case_id: Identifier
    case_version: Identifier
    case_sha256: Hash
    manifest_id: Identifier
    attempt_id: Identifier
    output_sha256: Hash


class ReviewPacket(StrictModel):
    schema_version: Literal["uaw.human-review-packet.v1"]
    created_at: Utc
    input_sha256: tuple[NamedHash, ...]
    targets: Annotated[tuple[ReviewTarget, ...], Field(min_length=1, max_length=128)]


class SubmittedReview(StrictModel):
    case_id: Identifier
    attempt_id: Identifier
    case_review: Literal["verified", "needs_revision"]
    evidence_reviewed: Confirmed
    labels: Labels
    notes: Text


class ReviewSubmission(StrictModel):
    schema_version: Literal["uaw.human-review-submission.v1"]
    packet_sha256: Hash
    reviewer_id: Identifier
    reviewed_at: Utc
    human_attested: Confirmed
    items: Annotated[tuple[SubmittedReview, ...], Field(min_length=1, max_length=128)]


def _utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def source_bundle(source: Path) -> tuple[Bundle, dict[str, bytes]]:
    """Bounded original bytes plus C-validated objects; reject changes between reads."""
    bundle = load_bundle(*(source / name for name in FILES))
    raw = {
        name: read_bounded(source / name, limit=limit)
        for name, limit in zip(FILES, (2**21, 2**21, 2**24, 2**23), strict=True)
    }
    actual = tuple(
        NamedHash(name=name.split(".")[0], sha256=hashlib.sha256(raw[name]).hexdigest())
        for name in FILES
    )
    if actual != bundle.input_sha256:
        raise ReviewInputError("source_changed_during_read")
    candidate = bundle.manifest.candidate
    if bundle.manifest.baseline is not None or bundle.reviews:
        raise ReviewInputError("initial_candidate_without_existing_reviews_required")
    if candidate.suite_sha256 != digest(bundle.suite.wire()) or not candidate.inventory_complete:
        raise ReviewInputError("source_inventory_or_suite_mismatch")
    pins = {p.attempt_id: p for p in candidate.attempts}
    if set(pins) != {o.attempt_id for o in bundle.observations}:
        raise ReviewInputError("source_attempt_inventory_mismatch")
    for row in bundle.observations:
        pin = pins[row.attempt_id]
        if (
            row.manifest_id != candidate.id
            or pin.observation_sha256 != digest(row.wire())
            or pin.output_sha256 != (digest(row.output.wire()) if row.output else None)
        ):
            raise ReviewInputError("source_observation_mismatch")
    for case in bundle.suite.cases:
        if any(e.sha256 != text_hash(e.text) for e in case.evidence):
            raise ReviewInputError("source_evidence_hash_mismatch")
    return bundle, raw


def _targets(bundle: Bundle) -> tuple[ReviewTarget, ...]:
    rows = {row.attempt_id: row for row in bundle.observations}
    cases = {case.id: case for case in bundle.suite.cases}
    if {s.case_id for s in bundle.manifest.candidate.selections} != set(cases):
        raise ReviewInputError("one_selection_per_case_required")
    result = []
    for selection in bundle.manifest.candidate.selections:
        case = cases[selection.case_id]
        row = rows.get(selection.answer_attempt_id or "")
        if (
            row is None
            or row.output is None
            or row.status != "succeeded"
            or row.phase != "answer"
            or row.case_id != case.id
            or row.case_version != case.version
        ):
            raise ReviewInputError("selected_complete_answer_required")
        result.append(
            ReviewTarget(
                case_id=case.id,
                case_version=case.version,
                case_sha256=digest(case.wire()),
                manifest_id=row.manifest_id,
                attempt_id=row.attempt_id,
                output_sha256=digest(row.output.wire()),
            )
        )
    return tuple(result)


def prepare_review(source: Path, output: Path, *, now: datetime) -> ReviewPacket:
    bundle, _ = source_bundle(source)
    if now.tzinfo is None or now < _utc(bundle.manifest.candidate.finished_at):
        raise ReviewInputError("packet_time_predates_answer")
    packet = ReviewPacket(
        schema_version="uaw.human-review-packet.v1",
        created_at=now.astimezone(UTC).isoformat(),
        input_sha256=bundle.input_sha256,
        targets=_targets(bundle),
    )
    cases = {c.id: c.wire() for c in bundle.suite.cases}
    rows = {o.attempt_id: o.wire() for o in bundle.observations}
    # Render the actual selected answer, not a model summary or the latest message.
    data = {
        "packet_sha256": digest(packet.wire()),
        "targets": [
            {"binding": t.wire(), "case": cases[t.case_id], "answer": rows[t.attempt_id]["output"]}
            for t in packet.targets
        ],
    }
    template = TEMPLATE.read_text(encoding="utf-8")
    script = template.split("<script id=review-code>", 1)[1].split("</script>", 1)[0]
    script_hash = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode("ascii")
    embedded = json.dumps(data, ensure_ascii=True).replace("<", "\\u003c")
    page = template.replace("__SCRIPT_SHA256__", script_hash).replace("__REVIEW_DATA__", embedded)
    output.mkdir(parents=False, exist_ok=False)
    publish_report(output / "packet.json", packet.wire())
    with (output / "index.html").open("x", encoding="utf-8") as stream:
        stream.write(page)
    return packet


def import_review(
    source: Path,
    packet: ReviewPacket,
    submission: ReviewSubmission,
    output: Path,
    *,
    now: datetime,
    basis: Literal["human_evidence_review", "controlled_test"],
) -> int:
    """Consume explicit assertions; digest binding is not human authentication."""
    bundle, raw = source_bundle(source)
    if packet.input_sha256 != bundle.input_sha256 or packet.targets != _targets(bundle):
        raise ReviewInputError("packet_source_mismatch")
    if submission.packet_sha256 != digest(packet.wire()):
        raise ReviewInputError("submission_packet_mismatch")
    if now.tzinfo is None or not _utc(packet.created_at) <= _utc(
        submission.reviewed_at
    ) <= now + timedelta(minutes=5):
        raise ReviewInputError("review_timestamp_out_of_range")
    by_id = {(item.case_id, item.attempt_id): item for item in submission.items}
    if len(by_id) != len(submission.items) or set(by_id) != {
        (target.case_id, target.attempt_id) for target in packet.targets
    }:
        raise ReviewInputError("submission_target_inventory_mismatch")
    submission_hash = digest(submission.wire())
    cases = {case.id: case for case in bundle.suite.cases}
    reviews = []
    for target in packet.targets:
        item = by_id[(target.case_id, target.attempt_id)]
        labels = item.labels
        if labels.acceptable is True and not (
            labels.answer_correct is True
            and labels.unnecessary_block is False
            and labels.unsupported_execution is False
            and labels.requirements_preserved is True
            and not labels.critical_error
        ):
            raise ReviewInputError("inconsistent_acceptable_labels")
        if not item.notes.strip() or not submission.reviewer_id.strip():
            raise ReviewInputError("review_explanation_required")
        case = cases[target.case_id]
        if item.case_review == "needs_revision":
            value = case.wire()
            value.update(review_status="needs_human_review", human_verification=None)
            case = record(Case, value)
            cases[case.id] = case
        # Controlled imports cannot promote a sample to human-verified.
        if (
            item.case_review == "verified"
            and basis == "human_evidence_review"
            and case.review_status != "human_verified"
        ):
            value = case.wire()
            value.update(
                review_status="human_verified",
                human_verification={
                    "reviewer_id": submission.reviewer_id,
                    "reviewed_at": submission.reviewed_at,
                    "rubric_sha256": digest(case.rubric.wire()),
                    "evidence_sha256": [e.sha256 for e in case.evidence],
                    "record_locator": "local-review:" + submission_hash,
                },
            )
            case = record(Case, value)
            cases[case.id] = case
        reviews.append(
            record(
                Review,
                {
                    "schema_version": "ms-e1.v1",
                    "id": "review-" + digest(target.wire())[:24] + "-" + submission_hash[:12],
                    "manifest_id": target.manifest_id,
                    "case_id": target.case_id,
                    "case_version": target.case_version,
                    "attempt_id": target.attempt_id,
                    "output_sha256": target.output_sha256,
                    "case_sha256": digest(case.wire()),
                    "basis": basis,
                    "reviewer_id": submission.reviewer_id,
                    "reviewed_at": submission.reviewed_at,
                    "evidence_sha256": [e.sha256 for e in case.evidence],
                    "evidence_reviewed": item.evidence_reviewed,
                    "labels": labels.wire(),
                    "notes": item.notes,
                },
            ).wire()
        )
    suite_value = bundle.suite.wire()
    suite_value["cases"] = [cases[c.id].wire() for c in bundle.suite.cases]
    suite = record(Suite, suite_value)
    manifest_value = bundle.manifest.wire()
    manifest_value["candidate"]["suite_sha256"] = digest(suite.wire())
    manifest = record(Manifest, manifest_value)
    output.mkdir(parents=False, exist_ok=False)
    publish_report(output / "suite.json", suite.wire())
    publish_report(output / "manifest.json", manifest.wire())
    # Preserve every attempt, result and byte of usage; never rerun a model.
    with (output / "observations.jsonl").open("xb") as stream:
        stream.write(raw["observations.jsonl"])
    with (output / "reviews.jsonl").open("xb") as stream:
        stream.write(b"".join(canonical(r) + b"\n" for r in reviews))
    publish_report(output / "submission.json", submission.wire())
    publish_report(output / "packet.json", packet.wire())
    publish_report(
        output / "review-import.json",
        {
            "schema_version": "uaw.review-import.v1",
            "basis": basis,
            "packet_sha256": digest(packet.wire()),
            "submission_sha256": submission_hash,
            "source_input_sha256": [h.wire() for h in bundle.input_sha256],
            "human_identity_authenticated": False,
            "human_assertion_supplied_by_operator": basis == "human_evidence_review",
            "model_calls": 0,
            "runtime_writes": 0,
            "release_gate_decided": False,
        },
    )
    return len(reviews)
