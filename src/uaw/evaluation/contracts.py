"""MS-E1 v1 offline schemas. These are not HTTP/Runtime permission contracts.

Human assertions must be genuinely supplied by an independent human operator.
Schema/hash validation checks their binding, never authenticates a person's act.
Controlled and model reviews cannot authorize the formal release gate.
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from uaw.evaluation.io import digest

VERSION = "ms-e1.v1"
Identifier = Annotated[
    str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
]
Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Commit = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
Text = Annotated[str, Field(min_length=1, max_length=16384)]
Count = Annotated[int, Field(ge=0, le=10**18)]
InputCount = Annotated[int, Field(ge=0, le=10**12)]
Money = Annotated[str, Field(pattern=r"^(0|[1-9][0-9]{0,17})(\.[0-9]{1,8})?$")]
Fraction = Annotated[str, Field(pattern=r"^(0(\.[0-9]{1,8})?|1(\.0{1,8})?)$")]


def _utc(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("UTC timestamp required")
    return value


Utc = Annotated[str, Field(min_length=20, max_length=40), AfterValidator(_utc)]


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    def wire(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class Evidence(StrictModel):
    id: Identifier
    kind: Literal["provided_material", "primary_source"]
    locator: Text
    captured_at: Utc
    text: Annotated[str, Field(min_length=1, max_length=65536)]
    sha256: Hash
    url: Annotated[str, Field(min_length=1, max_length=2048)] | None = None

    @model_validator(mode="after")
    def exact_source(self) -> Self:
        if self.kind == "primary_source" and (
            self.url is None or not self.url.startswith("https://")
        ):
            raise ValueError("Primary source requires its actual HTTPS location")
        return self


class Rubric(StrictModel):
    expected_behavior: Literal["answer", "clarify", "decline", "deliver", "tool"]
    required_facts: Annotated[tuple[Text, ...], Field(min_length=1, max_length=24)]
    allowed_assumptions: Annotated[tuple[Text, ...], Field(max_length=16)]
    retained_requirements: Annotated[tuple[Text, ...], Field(max_length=24)]
    critical: bool


class HumanVerification(StrictModel):
    reviewer_id: Identifier
    reviewed_at: Utc
    rubric_sha256: Hash
    evidence_sha256: Annotated[tuple[Hash, ...], Field(max_length=16)]
    record_locator: Text


class Case(StrictModel):
    id: Identifier
    version: Identifier
    split: Literal["revision", "holdout"]
    category: Literal[
        "office", "academic", "technical", "missing_material", "reasonable_ambiguity", "correction"
    ]
    prompt: Text
    rubric: Rubric
    evidence: Annotated[tuple[Evidence, ...], Field(max_length=16)]
    review_status: Literal["needs_human_review", "human_verified"]
    human_verification: HumanVerification | None

    @model_validator(mode="after")
    def human_binding(self) -> Self:
        if len({e.id for e in self.evidence}) != len(self.evidence):
            raise ValueError("Duplicate source id")
        verification = self.human_verification
        if self.review_status == "needs_human_review":
            if verification is not None:
                raise ValueError("Unverified sample cannot contain human verification")
        elif (
            verification is None
            or verification.rubric_sha256 != digest(self.rubric.wire())
            or verification.evidence_sha256 != tuple(e.sha256 for e in self.evidence)
        ):
            raise ValueError("Human sample verification must bind exact rubric and evidence")
        return self


class Suite(StrictModel):
    schema_version: Literal["ms-e1.v1"]
    id: Identifier
    version: Identifier
    created_at: Utc
    cases: Annotated[tuple[Case, ...], Field(min_length=1, max_length=128)]

    @model_validator(mode="after")
    def unique_cases(self) -> Self:
        if len({c.id for c in self.cases}) != len(self.cases):
            raise ValueError("Duplicate sample id")
        return self


class NamedHash(StrictModel):
    name: Identifier
    sha256: Hash


class ModelPin(StrictModel):
    provider_id: Identifier
    provider_version: Identifier
    model_id: Identifier
    model_version: Identifier
    configuration_sha256: Hash


class Usage(StrictModel):
    input_tokens: InputCount | None
    output_tokens: InputCount | None
    model_calls: InputCount | None
    tool_calls: InputCount | None
    money: Money | None
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    billing_state: Literal["confirmed", "pending", "unknown"]

    @model_validator(mode="after")
    def known_bill(self) -> Self:
        if self.billing_state == "confirmed" and self.money is None:
            raise ValueError("Unknown money cannot be a confirmed bill")
        return self


class OutputEvidence(StrictModel):
    kind: Literal["content", "artifact", "tool_call", "tool_result", "receipt"]
    id: Identifier
    version: Identifier
    sha256: Hash


class Answer(StrictModel):
    decision: Literal["reply", "ask", "tool", "deliver", "blocked", "none"]
    text: Annotated[str, Field(max_length=65536)]
    evidence: Annotated[tuple[OutputEvidence, ...], Field(max_length=64)]


class ReviewerObservation(StrictModel):
    target_attempt_id: Identifier
    target_output_sha256: Hash
    verdict: Literal["passed", "failed", "not_applicable", "unavailable"]


class Observation(StrictModel):
    schema_version: Literal["ms-e1.v1"]
    manifest_id: Identifier
    case_id: Identifier
    case_version: Identifier
    attempt_id: Identifier
    logical_request_id: Identifier
    attempt_number: Annotated[int, Field(ge=1, le=4096)]
    phase: Literal["answer", "reviewer", "tool", "preparation"]
    status: Literal["succeeded", "failed", "cancelled", "unknown"]
    started_at: Utc
    finished_at: Utc
    active_ms: Count
    wall_ms: Count
    usage: Usage
    output: Answer | None
    reviewer: ReviewerObservation | None
    failure_code: Identifier | None

    @model_validator(mode="after")
    def actual_attempt(self) -> Self:
        start = datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
        end = datetime.fromisoformat(self.finished_at.replace("Z", "+00:00"))
        if (
            end < start
            or self.active_ms > self.wall_ms
            or abs(Decimal(str((end - start).total_seconds())) * 1000 - self.wall_ms) > 1
        ):
            raise ValueError("Attempt active/wall time differs from actual UTC interval")
        if self.status == "succeeded" and self.phase == "answer" and self.output is None:
            raise ValueError("Successful answer requires its actual output")
        if self.status == "succeeded" and self.phase == "reviewer" and self.reviewer is None:
            raise ValueError("Successful Reviewer requires actual bound verdict")
        if self.phase != "reviewer" and self.reviewer is not None:
            raise ValueError("Reviewer verdict belongs to a Reviewer attempt")
        if self.status != "succeeded" and self.failure_code is None:
            raise ValueError("Every failed/cancelled/unknown attempt retains its cause")
        if self.status == "succeeded" and self.failure_code is not None:
            raise ValueError("Success cannot hide a failure")
        return self


class AttemptPin(StrictModel):
    attempt_id: Identifier
    observation_sha256: Hash
    output_sha256: Hash | None


class Selection(StrictModel):
    case_id: Identifier
    answer_attempt_id: Identifier | None
    reviewer_attempt_id: Identifier | None


class CandidateManifest(StrictModel):
    id: Identifier
    provenance: Literal["actual_candidate", "controlled_fixture"]
    source_commit: Commit
    dirty: bool
    working_tree_sha256: Hash | None
    suite_sha256: Hash
    environment_sha256: Hash
    model: ModelPin
    prompts: Annotated[tuple[NamedHash, ...], Field(min_length=1, max_length=64)]
    started_at: Utc
    finished_at: Utc
    inventory_complete: bool
    attempts: Annotated[tuple[AttemptPin, ...], Field(max_length=2048)]
    selections: Annotated[tuple[Selection, ...], Field(max_length=128)]

    @model_validator(mode="after")
    def fixed_manifest(self) -> Self:
        if self.dirty != (self.working_tree_sha256 is not None):
            raise ValueError("Dirty state must bind the actual working tree hash")
        if datetime.fromisoformat(self.finished_at.replace("Z", "+00:00")) < datetime.fromisoformat(
            self.started_at.replace("Z", "+00:00")
        ):
            raise ValueError("Manifest interval runs backwards")
        for values in (
            tuple(p.name for p in self.prompts),
            tuple(a.attempt_id for a in self.attempts),
            tuple(s.case_id for s in self.selections),
        ):
            if len(set(values)) != len(values):
                raise ValueError("Duplicate manifest name/attempt/selection")
        return self


class Policy(StrictModel):
    id: Identifier
    registered_at: Utc
    reviewer_required: bool
    baseline_required: bool
    max_answer_error_rate: Fraction
    max_reviewer_miss_rate: Fraction
    max_unnecessary_block_rate: Fraction
    max_unsupported_execution_rate: Fraction


class Manifest(StrictModel):
    schema_version: Literal["ms-e1.v1"]
    policy: Policy
    candidate: CandidateManifest
    baseline: CandidateManifest | None

    @model_validator(mode="after")
    def distinct_versions(self) -> Self:
        if self.baseline is not None and self.candidate.id == self.baseline.id:
            raise ValueError("Candidate and baseline manifest ids must differ")
        return self


class Labels(StrictModel):
    answer_correct: bool | None
    unnecessary_block: bool | None
    unsupported_execution: bool | None
    requirements_preserved: bool | None
    acceptable: bool | None
    critical_error: bool


class Review(StrictModel):
    schema_version: Literal["ms-e1.v1"]
    id: Identifier
    manifest_id: Identifier
    case_id: Identifier
    case_version: Identifier
    attempt_id: Identifier
    output_sha256: Hash
    case_sha256: Hash
    basis: Literal["human_evidence_review", "model_suggestion", "controlled_test"]
    reviewer_id: Identifier
    reviewed_at: Utc
    evidence_sha256: Annotated[tuple[Hash, ...], Field(max_length=16)]
    evidence_reviewed: bool
    labels: Labels
    notes: Text


class Issue(StrictModel):
    code: Identifier
    manifest_id: Identifier | None
    case_id: Identifier | None
    attempt_id: Identifier | None


class Rate(StrictModel):
    numerator: Count
    denominator: Count
    value: Fraction | None
    status: Literal["measured", "provisional", "not_applicable"]


class Quantity(StrictModel):
    known_total: Count
    unknown_attempts: Count


TotalMoney = Annotated[str, Field(pattern=r"^(0|[1-9][0-9]{0,29})(\.[0-9]{1,8})?$")]


class Cost(StrictModel):
    currency: str
    confirmed: TotalMoney
    pending: TotalMoney
    unknown_estimate: TotalMoney
    unknown_money_attempts: Count
    pending_attempts: Count
    unknown_billing_attempts: Count
    confirmed_per_acceptable_output: TotalMoney | None


class AttemptSummary(StrictModel):
    attempt_id: Identifier
    case_id: Identifier
    phase: str
    status: str
    failure_code: Identifier | None
    observation_sha256: Hash
    output_sha256: Hash | None
    binding_verified: bool
    active_ms: Count
    wall_ms: Count
    usage: Usage


class CandidateReport(StrictModel):
    manifest_id: Identifier
    attempts: Annotated[tuple[AttemptSummary, ...], Field(max_length=2048)]
    attempt_count: Count
    failure_count: Count
    cancelled_count: Count
    unknown_count: Count
    retry_count: Count
    verified_observation_count: Count
    selected_output_count: Count
    acceptable_output_count: Count
    reviewer_na_cases: Count
    human_reviewed_cases: Count
    controlled_reviewed_cases: Count
    model_suggestion_count: Count
    answer_error: Rate
    reviewer_miss: Rate
    unnecessary_block: Rate
    unsupported_execution: Rate
    requirements_lost: Rate
    active_ms: Count
    attempt_wall_ms_sum: Count
    experiment_wall_ms: Count
    input_tokens: Quantity
    output_tokens: Quantity
    model_calls: Quantity
    tool_calls: Quantity
    costs: tuple[Cost, ...]
    unverified_costs: tuple[Cost, ...]


class Gate(StrictModel):
    status: Literal["passed", "blocked", "incomplete"]
    reasons: tuple[Identifier, ...]


class Comparison(StrictModel):
    status: Literal["comparable", "incomparable", "not_available"]
    reasons: tuple[Identifier, ...]
    candidate_minus_baseline: dict[str, str | None]


class Report(StrictModel):
    schema_version: Literal["ms-e1.v1"]
    suite_id: Identifier
    suite_sha256: Hash
    manifests: Manifest
    unassigned_attempts: tuple[AttemptSummary, ...]
    unassigned_costs: tuple[Cost, ...]
    input_sha256: tuple[NamedHash, ...]
    candidate: CandidateReport
    baseline: CandidateReport | None
    comparison: Comparison
    release_gate: Gate
    integrity_issues: tuple[Issue, ...]
    human_verification: Literal["offline_assertions_only_not_identity_authentication"]
