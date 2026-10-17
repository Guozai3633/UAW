"""Explicit offline experiment registration and exact per-Run capture assembly.

No execution, human judgment, mutable registry or extra scoring algorithm lives here.
Registration timestamps are operator-local records, not external attestations.
"""

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, model_validator

from uaw.evaluation.contracts import (
    Commit,
    Fraction,
    Hash,
    Identifier,
    Manifest,
    ModelPin,
    NamedHash,
    Policy,
    Report,
    StrictModel,
    Suite,
    Utc,
)
from uaw.evaluation.io import digest, publish_report, read_bounded, text_hash
from uaw.evaluation.reader import Bundle, load_bundle, record
from uaw.evaluation.runner import evaluate_files
from uaw.run.evaluation_review import FILES


class ExperimentInputError(ValueError):
    """Bounded diagnostic code, never raw answers or filesystem locations."""


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


class VersionPin(StrictModel):
    id: Identifier
    provenance: Literal["actual_candidate", "controlled_fixture"]
    source_commit: Commit
    environment_sha256: Hash
    model: ModelPin
    prompts: Annotated[tuple[NamedHash, ...], Field(min_length=1, max_length=64)]

    @model_validator(mode="after")
    def named_prompts(self) -> VersionPin:
        if len({p.name for p in self.prompts}) != len(self.prompts):
            raise ValueError("duplicate_prompt_name")
        return self


class PolicyLimits(StrictModel):
    id: Identifier
    reviewer_required: bool
    max_answer_error_rate: Fraction
    max_reviewer_miss_rate: Fraction
    max_unnecessary_block_rate: Fraction
    max_unsupported_execution_rate: Fraction


class ExperimentDraft(StrictModel):
    schema_version: Literal["uaw.experiment-draft.v1"]
    id: Identifier
    suite: Suite
    limits: PolicyLimits
    candidate: VersionPin
    baseline: VersionPin

    @model_validator(mode="after")
    def comparable_versions(self) -> ExperimentDraft:
        if self.candidate.id == self.baseline.id:
            raise ValueError("distinct_versions_required")
        # Frozen C comparison semantics: only source/prompt are comparison axes.
        for name in ("environment_sha256", "model", "provenance"):
            if getattr(self.candidate, name) != getattr(self.baseline, name):
                raise ValueError("comparison_conditions_differ")
        return self


class ExperimentRegistration(StrictModel):
    schema_version: Literal["uaw.experiment-registration.v1"]
    registered_at: Utc
    draft: ExperimentDraft
    policy: Policy

    @model_validator(mode="after")
    def original_policy(self) -> ExperimentRegistration:
        expected = {
            **self.draft.limits.wire(),
            "registered_at": self.registered_at,
            "baseline_required": True,
        }
        if self.policy.wire() != expected:
            raise ValueError("registered_policy_differs")
        instant = datetime.fromisoformat(self.registered_at.replace("Z", "+00:00"))
        dates = [self.draft.suite.created_at]
        for case in self.draft.suite.cases:
            if any(source.sha256 != text_hash(source.text) for source in case.evidence):
                raise ValueError("source_evidence_hash_mismatch")
            dates.extend(source.captured_at for source in case.evidence)
            if case.human_verification:
                dates.append(case.human_verification.reviewed_at)
        if any(datetime.fromisoformat(date.replace("Z", "+00:00")) > instant for date in dates):
            raise ValueError("registered_inputs_from_future")
        return self


def register_experiment(
    draft: ExperimentDraft, output: Path, *, now: datetime
) -> ExperimentRegistration:
    if now.tzinfo is None:
        raise ExperimentInputError("aware_current_time_required")
    stamp = now.astimezone(UTC).isoformat()
    registration = record(
        ExperimentRegistration,
        {
            "schema_version": "uaw.experiment-registration.v1",
            "registered_at": stamp,
            "draft": draft.wire(),
            "policy": {
                **draft.limits.wire(),
                "registered_at": stamp,
                "baseline_required": True,
            },
        },
    )
    pending = [case.id for case in draft.suite.cases if case.review_status != "human_verified"]
    output.mkdir(parents=False, exist_ok=False)
    publish_report(output / "registration.json", registration.wire())
    publish_report(output / "suite.json", draft.suite.wire())
    publish_report(output / "policy.json", registration.policy.wire())
    publish_report(
        output / "registration-audit.json",
        {
            "schema_version": "uaw.experiment-registration-audit.v1",
            "registration_sha256": digest(registration.wire()),
            "suite_sha256": digest(draft.suite.wire()),
            "unreviewed_case_ids": pending,
            "release_readiness": "needs_case_review"
            if pending
            else "requires_actual_results_and_reviews",
            "timestamp_basis": "operator_current_UTC_not_external_attestation",
            "human_assertions_authenticated": False,
            "new_model_calls": 0,
            "release_gate_decided": False,
        },
    )
    return registration


def _bundle(source: Path) -> tuple[Bundle, dict[str, bytes]]:
    bundle = load_bundle(*(source / name for name in FILES))
    raw = {
        name: read_bounded(source / name, limit=limit)
        for name, limit in zip(FILES, (2**21, 2**21, 2**24, 2**23), strict=True)
    }
    if [p.sha256 for p in bundle.input_sha256] != [
        hashlib.sha256(raw[name]).hexdigest() for name in FILES
    ]:
        raise ExperimentInputError("source_changed_during_read")
    return bundle, raw


def assemble_experiment(
    registration: ExperimentRegistration, sources: tuple[Path, ...], output: Path, *, now: datetime
) -> Report:
    if now.tzinfo is None or utc(registration.registered_at) > now:
        raise ExperimentInputError("registration_from_future")
    draft = registration.draft
    expected_count = len(draft.suite.cases) * 2
    if len(sources) != expected_count or len({p.resolve() for p in sources}) != len(sources):
        raise ExperimentInputError("one_capture_per_version_and_case_required")
    # Bound aggregate input memory before any bundle parse (also bounded by C).
    if sum((path / name).stat().st_size for path in sources for name in FILES) > 2**26:
        raise ExperimentInputError("aggregate_input_too_large")
    cases = {case.id: case for case in draft.suite.cases}
    versions = {pin.id: pin for pin in (draft.candidate, draft.baseline)}
    captures = {}
    audit = []
    consumed_bytes = 0
    for path in sources:
        bundle, raw = _bundle(path)
        consumed_bytes += sum(len(value) for value in raw.values())
        if consumed_bytes > 2**26:
            raise ExperimentInputError("aggregate_input_changed_or_too_large")
        actual = bundle.manifest.candidate
        if bundle.manifest.baseline is not None or len(bundle.suite.cases) != 1:
            raise ExperimentInputError("single_capture_without_nested_baseline_required")
        case = bundle.suite.cases[0]
        key = (actual.id, case.id)
        pin = versions.get(actual.id)
        if pin is None or key in captures or case.id not in cases:
            raise ExperimentInputError("duplicate_or_unregistered_capture")
        if case != cases[case.id] or actual.suite_sha256 != digest(bundle.suite.wire()):
            raise ExperimentInputError("registered_case_differs")
        if any(getattr(actual, field) != getattr(pin, field) for field in VersionPin.model_fields):
            raise ExperimentInputError("registered_version_differs")
        if actual.dirty or not actual.inventory_complete:
            raise ExperimentInputError("clean_complete_capture_required")
        if bundle.manifest.policy != registration.policy:
            raise ExperimentInputError("registered_policy_differs")
        if utc(actual.started_at) < utc(registration.registered_at):
            raise ExperimentInputError("capture_predates_registration")
        if utc(actual.finished_at) > now + timedelta(minutes=5):
            raise ExperimentInputError("capture_from_future")
        if [selection.case_id for selection in actual.selections] != [case.id]:
            raise ExperimentInputError("capture_selection_inventory_mismatch")
        by_id = {o.attempt_id: o for o in bundle.observations}
        if set(by_id) != {p.attempt_id for p in actual.attempts}:
            raise ExperimentInputError("capture_attempt_inventory_mismatch")
        for attempt in actual.attempts:
            row = by_id[attempt.attempt_id]
            if (
                row.manifest_id != actual.id
                or row.case_id != case.id
                or row.case_version != case.version
                or attempt.observation_sha256 != digest(row.wire())
                or attempt.output_sha256 != (digest(row.output.wire()) if row.output else None)
                or utc(row.started_at) < utc(actual.started_at)
                or utc(row.finished_at) > utc(actual.finished_at)
            ):
                raise ExperimentInputError("capture_observation_binding_mismatch")
        if not actual.attempts:
            raise ExperimentInputError("empty_capture_not_an_executed_case")
        if any(r.manifest_id != actual.id or r.case_id != case.id for r in bundle.reviews):
            raise ExperimentInputError("capture_review_scope_mismatch")
        captures[key] = (bundle, raw)
        audit.append(
            {
                "variant_id": actual.id,
                "case_id": case.id,
                "input_sha256": [pin.wire() for pin in bundle.input_sha256],
            }
        )
    # Exact coverage means failed/unknown cases require their own observations too.
    if set(captures) != {(variant, case) for variant in versions for case in cases}:
        raise ExperimentInputError("registered_case_coverage_incomplete")
    manifests = []
    observations, reviews = bytearray(), bytearray()
    for version in (draft.candidate, draft.baseline):
        included = [captures[(version.id, case.id)] for case in draft.suite.cases]
        manifest = included[0][0].manifest.candidate.wire()
        manifest.update(
            suite_sha256=digest(draft.suite.wire()),
            attempts=[a.wire() for b, _ in included for a in b.manifest.candidate.attempts],
            selections=[s.wire() for b, _ in included for s in b.manifest.candidate.selections],
            started_at=min((b.manifest.candidate.started_at for b, _ in included), key=utc),
            finished_at=max((b.manifest.candidate.finished_at for b, _ in included), key=utc),
        )
        manifests.append(manifest)
        for _, raw in included:
            for name, target in (("observations.jsonl", observations), ("reviews.jsonl", reviews)):
                target.extend(raw[name])
                if raw[name] and not raw[name].endswith(b"\n"):
                    target.extend(b"\n")
    if len(observations) > 2**24 or len(reviews) > 2**23:
        raise ExperimentInputError("aggregate_output_too_large")
    combined = record(
        Manifest,
        {
            "schema_version": "ms-e1.v1",
            "policy": registration.policy.wire(),
            "candidate": manifests[0],
            "baseline": manifests[1],
        },
    )
    output.mkdir(parents=False, exist_ok=False)
    publish_report(output / "suite.json", draft.suite.wire())
    publish_report(output / "manifest.json", combined.wire())
    for name, value in (("observations.jsonl", observations), ("reviews.jsonl", reviews)):
        with (output / name).open("xb") as stream:
            stream.write(value)
    publish_report(output / "registration.json", registration.wire())
    publish_report(
        output / "assembly-audit.json",
        {
            "schema_version": "uaw.experiment-assembly-audit.v1",
            "registration_sha256": digest(registration.wire()),
            "source_captures": audit,
            "capture_count": len(captures),
            "new_model_calls": 0,
            "runtime_writes": 0,
            "human_reviews_created": 0,
            "timestamp_externally_authenticated": False,
        },
    )
    report = evaluate_files(*(output / name for name in FILES))
    publish_report(output / "quality-report.json", report.wire())
    return report
