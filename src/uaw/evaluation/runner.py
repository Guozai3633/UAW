"""Deterministic offline evaluation; hashes are bindings, never semantic graders."""

from decimal import Decimal
from pathlib import Path
from typing import Literal

from uaw.evaluation.contracts import (
    AttemptSummary,
    CandidateManifest,
    CandidateReport,
    Comparison,
    Gate,
    Issue,
    Observation,
    Report,
    Review,
)
from uaw.evaluation.io import digest, text_hash
from uaw.evaluation.metrics import costs, milliseconds, quantity, rate, utc
from uaw.evaluation.reader import Bundle, load_bundle


def _issue(
    code: str, manifest: str | None = None, case: str | None = None, attempt: str | None = None
) -> Issue:
    return Issue(code=code, manifest_id=manifest, case_id=case, attempt_id=attempt)


def _candidate(bundle: Bundle, manifest: CandidateManifest, issues: list[Issue]) -> CandidateReport:
    row: Observation | None
    review: Review | None
    cases = {case.id: case for case in bundle.suite.cases}
    rows = tuple(o for o in bundle.observations if o.manifest_id == manifest.id)
    pins = {p.attempt_id: p for p in manifest.attempts}
    by_id = {o.attempt_id: o for o in rows}
    verified = {}
    suite_matches = manifest.suite_sha256 == digest(bundle.suite.wire())
    if not suite_matches:
        issues.append(_issue("suite_hash_mismatch", manifest.id))
    if manifest.dirty:
        issues.append(_issue("dirty_candidate", manifest.id))
    if not manifest.inventory_complete:
        issues.append(_issue("incomplete_attempt_inventory", manifest.id))
    if utc(bundle.manifest.policy.registered_at) > utc(manifest.started_at):
        issues.append(_issue("policy_not_preregistered", manifest.id))
    for attempt in sorted(pins.keys() - by_id.keys()):
        issues.append(_issue("missing_observation", manifest.id, attempt=attempt))
    for row in rows:
        pin, case = pins.get(row.attempt_id), cases.get(row.case_id)
        valid = (
            suite_matches
            and pin is not None
            and case is not None
            and row.case_version == case.version
        )
        valid = (
            valid
            and utc(row.started_at) >= utc(manifest.started_at)
            and utc(row.finished_at) <= utc(manifest.finished_at)
        )
        output_hash = digest(row.output.wire()) if row.output is not None else None
        valid = (
            valid
            and pin is not None
            and pin.observation_sha256 == digest(row.wire())
            and pin.output_sha256 == output_hash
        )
        if not valid:
            issues.append(
                _issue("observation_binding_mismatch", manifest.id, row.case_id, row.attempt_id)
            )
        else:
            verified[row.attempt_id] = row
    groups: dict[str, list[int]] = {}
    for row in rows:
        groups.setdefault(row.logical_request_id, []).append(row.attempt_number)
    if any(sorted(numbers) != list(range(1, max(numbers) + 1)) for numbers in groups.values()):
        issues.append(_issue("attempt_sequence_gap", manifest.id))
    reviews: dict[str, Review] = {}
    model_suggestions = 0
    for review in (r for r in bundle.reviews if r.manifest_id == manifest.id):
        row, case = verified.get(review.attempt_id), cases.get(review.case_id)
        if (
            row is None
            or case is None
            or row.case_id != review.case_id
            or row.case_version != review.case_version
            or row.output is None
            or review.output_sha256 != digest(row.output.wire())
            or review.case_sha256 != digest(case.wire())
            or review.evidence_sha256 != tuple(e.sha256 for e in case.evidence)
            or utc(review.reviewed_at) < utc(row.finished_at)
        ):
            issues.append(
                _issue("review_binding_mismatch", manifest.id, review.case_id, review.attempt_id)
            )
            continue
        if review.basis == "model_suggestion":
            model_suggestions += 1
            continue
        if not review.evidence_reviewed:
            issues.append(
                _issue(
                    "review_evidence_not_reviewed", manifest.id, review.case_id, review.attempt_id
                )
            )
            continue
        previous = reviews.get(review.attempt_id)
        if previous is None or review.basis == "human_evidence_review":
            reviews[review.attempt_id] = review
    selected = {selection.case_id: selection for selection in manifest.selections}
    values: dict[str, list[bool]] = {
        name: []
        for name in (
            "answer_correct",
            "unnecessary_block",
            "unsupported_execution",
            "requirements_preserved",
        )
    }
    acceptable = human = controlled = selected_count = reviewer_na = misses = (
        reviewer_denominator
    ) = 0
    for case in bundle.suite.cases:
        selection = selected.get(case.id)
        row = verified.get(selection.answer_attempt_id or "") if selection else None
        if (
            row is None
            or row.case_id != case.id
            or row.phase != "answer"
            or row.status != "succeeded"
            or row.output is None
        ):
            issues.append(_issue("missing_selected_output", manifest.id, case.id))
            reviewer_na += 1
            continue
        selected_count += 1
        review = reviews.get(row.attempt_id)
        if review is None:
            issues.append(
                _issue("missing_independent_review", manifest.id, case.id, row.attempt_id)
            )
        else:
            human += review.basis == "human_evidence_review"
            controlled += review.basis == "controlled_test"
            for name in values:
                value = getattr(review.labels, name)
                if value is not None:
                    values[name].append(value)
            acceptable += review.labels.acceptable is True
            if review.labels.critical_error:
                issues.append(_issue("critical_answer_error", manifest.id, case.id, row.attempt_id))
        reviewer = verified.get(selection.reviewer_attempt_id or "") if selection else None
        actual = (
            reviewer.reviewer
            if reviewer is not None
            and reviewer.phase == "reviewer"
            and reviewer.status == "succeeded"
            else None
        )
        if actual is not None and (
            reviewer is None
            or reviewer.case_id != case.id
            or actual.target_attempt_id != row.attempt_id
            or actual.target_output_sha256 != digest(row.output.wire())
        ):
            issues.append(_issue("reviewer_target_mismatch", manifest.id, case.id))
            actual = None
        if actual is None or actual.verdict in ("not_applicable", "unavailable"):
            reviewer_na += 1
        elif review is not None and review.labels.answer_correct is False:
            reviewer_denominator += 1
            misses += actual.verdict == "passed"
    for extra in selected.keys() - cases.keys():
        issues.append(_issue("unknown_selected_case", manifest.id, extra))
    provisional = controlled > 0
    bound_rows = tuple(verified.values())
    unbound_rows = tuple(r for r in rows if r.attempt_id not in verified)
    return CandidateReport(
        manifest_id=manifest.id,
        attempts=tuple(
            AttemptSummary(
                attempt_id=r.attempt_id,
                case_id=r.case_id,
                phase=r.phase,
                status=r.status,
                failure_code=r.failure_code,
                observation_sha256=digest(r.wire()),
                output_sha256=digest(r.output.wire()) if r.output else None,
                binding_verified=r.attempt_id in verified,
                active_ms=r.active_ms,
                wall_ms=r.wall_ms,
                usage=r.usage,
            )
            for r in rows
        ),
        attempt_count=len(rows),
        failure_count=sum(r.status == "failed" for r in rows),
        cancelled_count=sum(r.status == "cancelled" for r in rows),
        unknown_count=sum(r.status == "unknown" for r in rows),
        retry_count=sum(r.attempt_number > 1 for r in rows),
        verified_observation_count=len(verified),
        selected_output_count=selected_count,
        acceptable_output_count=acceptable,
        reviewer_na_cases=reviewer_na,
        human_reviewed_cases=human,
        controlled_reviewed_cases=controlled,
        model_suggestion_count=model_suggestions,
        answer_error=rate(
            values["answer_correct"].count(False),
            len(values["answer_correct"]),
            provisional=provisional,
        ),
        reviewer_miss=rate(misses, reviewer_denominator, provisional=provisional),
        unnecessary_block=rate(
            values["unnecessary_block"].count(True),
            len(values["unnecessary_block"]),
            provisional=provisional,
        ),
        unsupported_execution=rate(
            values["unsupported_execution"].count(True),
            len(values["unsupported_execution"]),
            provisional=provisional,
        ),
        requirements_lost=rate(
            values["requirements_preserved"].count(False),
            len(values["requirements_preserved"]),
            provisional=provisional,
        ),
        active_ms=sum(r.active_ms for r in rows),
        attempt_wall_ms_sum=sum(r.wall_ms for r in rows),
        experiment_wall_ms=milliseconds(manifest.started_at, manifest.finished_at),
        input_tokens=quantity(bound_rows, "input_tokens"),
        output_tokens=quantity(bound_rows, "output_tokens"),
        model_calls=quantity(bound_rows, "model_calls"),
        tool_calls=quantity(bound_rows, "tool_calls"),
        costs=costs(bound_rows, acceptable),
        unverified_costs=costs(unbound_rows, 0),
    )


def evaluate(bundle: Bundle) -> Report:
    issues = []
    for case in bundle.suite.cases:
        for source in case.evidence:
            if source.sha256 != text_hash(source.text):
                issues.append(_issue("source_text_hash_mismatch", case=case.id))
        if case.review_status != "human_verified":
            issues.append(_issue("sample_needs_human_review", case=case.id))
    manifests = (bundle.manifest.candidate,) + (
        (bundle.manifest.baseline,) if bundle.manifest.baseline else ()
    )
    ids = {m.id for m in manifests}
    all_records: tuple[Observation | Review, ...] = (*bundle.observations, *bundle.reviews)
    for row in all_records:
        if row.manifest_id not in ids:
            issues.append(_issue("unknown_manifest", row.manifest_id, row.case_id, row.attempt_id))
    candidate = _candidate(bundle, bundle.manifest.candidate, issues)
    baseline = (
        _candidate(bundle, bundle.manifest.baseline, issues) if bundle.manifest.baseline else None
    )
    reasons = {i.code for i in issues}
    if bundle.manifest.candidate.provenance != "actual_candidate":
        reasons.add("controlled_fixture_not_release_evidence")
    if candidate.human_reviewed_cases != len(bundle.suite.cases):
        reasons.add("independent_human_review_incomplete")
    if candidate.failure_count or candidate.cancelled_count or candidate.unknown_count:
        # Keep all failures visible. Retries may produce a valid selected answer;
        # errors remain measured and charged rather than automatically erased.
        reasons.add("attempt_failures_retained")
    metrics = (
        ("answer_error", candidate.answer_error, bundle.manifest.policy.max_answer_error_rate),
        ("reviewer_miss", candidate.reviewer_miss, bundle.manifest.policy.max_reviewer_miss_rate),
        (
            "unnecessary_block",
            candidate.unnecessary_block,
            bundle.manifest.policy.max_unnecessary_block_rate,
        ),
        (
            "unsupported_execution",
            candidate.unsupported_execution,
            bundle.manifest.policy.max_unsupported_execution_rate,
        ),
    )

    exceeded = []
    for name, measure, threshold in metrics:
        if measure.value is None:
            if name != "reviewer_miss" or bundle.manifest.policy.reviewer_required:
                reasons.add(name + "_na")
        elif Decimal(measure.value) > Decimal(threshold):
            exceeded.append(name + "_threshold_exceeded")
    if candidate.requirements_lost.value is None:
        reasons.add("requirements_lost_na")
    if bundle.manifest.baseline is None and bundle.manifest.policy.baseline_required:
        reasons.add("baseline_required")
    if candidate.requirements_lost.numerator:
        exceeded.append("requirements_lost")
    if "critical_answer_error" in reasons:
        exceeded.append("critical_answer_error")
    incomplete = reasons - {"attempt_failures_retained", "critical_answer_error"}
    status: Literal["passed", "blocked", "incomplete"] = (
        "incomplete" if incomplete else "blocked" if exceeded else "passed"
    )
    if exceeded:
        reasons.update(exceeded)
    comparison = Comparison(
        status="not_available", reasons=("baseline_not_supplied",), candidate_minus_baseline={}
    )
    if baseline is not None and bundle.manifest.baseline is not None:
        mismatch = []
        left, right = bundle.manifest.candidate, bundle.manifest.baseline
        for name in ("suite_sha256", "environment_sha256", "model", "provenance"):
            if getattr(left, name) != getattr(right, name):
                mismatch.append(name + "_differs")
        if left.dirty or right.dirty:
            mismatch.append("dirty_source")
        if issues:
            mismatch.append("incomplete_evidence")
        comparison = Comparison(
            status="incomparable" if mismatch else "comparable",
            reasons=tuple(sorted(set(mismatch))),
            candidate_minus_baseline={}
            if mismatch
            else {
                "active_ms": str(candidate.active_ms - baseline.active_ms),
                "experiment_wall_ms": str(
                    candidate.experiment_wall_ms - baseline.experiment_wall_ms
                ),
            },
        )
    return Report(
        schema_version="ms-e1.v1",
        suite_id=bundle.suite.id,
        suite_sha256=digest(bundle.suite.wire()),
        manifests=bundle.manifest,
        unassigned_attempts=tuple(
            AttemptSummary(
                attempt_id=r.attempt_id,
                case_id=r.case_id,
                phase=r.phase,
                status=r.status,
                failure_code=r.failure_code,
                observation_sha256=digest(r.wire()),
                output_sha256=digest(r.output.wire()) if r.output else None,
                binding_verified=False,
                active_ms=r.active_ms,
                wall_ms=r.wall_ms,
                usage=r.usage,
            )
            for r in bundle.observations
            if r.manifest_id not in ids
        ),
        unassigned_costs=costs(
            tuple(r for r in bundle.observations if r.manifest_id not in ids), 0
        ),
        input_sha256=bundle.input_sha256,
        candidate=candidate,
        baseline=baseline,
        comparison=comparison,
        release_gate=Gate(status=status, reasons=tuple(sorted(reasons))),
        integrity_issues=tuple(issues),
        human_verification="offline_assertions_only_not_identity_authentication",
    )


def evaluate_files(suite: Path, manifest: Path, observations: Path, reviews: Path) -> Report:
    return evaluate(load_bundle(suite, manifest, observations, reviews))
