"""Strict web-review DTOs; C's scoring contracts and A11 imports stay authoritative."""

from typing import Annotated, Literal

from pydantic import Field

from uaw.evaluation.contracts import Answer, Case, Hash, Identifier, Observation, StrictModel, Utc
from uaw.run.evaluation_review import ReviewPacket, ReviewSubmission, ReviewTarget

Revision = Annotated[int, Field(ge=1)]
Note = Annotated[str, Field(max_length=4000)]
FileText = Annotated[str, Field(max_length=2**21)]


class QualityFiles(StrictModel):
    suite: FileText
    manifest: FileText
    observations: FileText
    reviews: FileText


class QualityOrigin(StrictModel):
    kind: Literal["actual_run", "controlled_test"]
    principal_id: Identifier
    run_id: Identifier
    run_revision: Revision
    input_revision: Revision
    source_commit: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]


class QualityVerificationOutput(StrictModel):
    attempt_id: Identifier
    output_sha256: Hash
    text: Annotated[str, Field(max_length=65536)]


class QualityTarget(StrictModel):
    binding: ReviewTarget
    case: Case
    answer: Answer
    verifications: Annotated[tuple[Observation, ...], Field(max_length=32)]
    verification_outputs: Annotated[
        tuple[QualityVerificationOutput, ...], Field(max_length=32)
    ] = ()


class QualityJudgment(StrictModel):
    case_id: Identifier
    attempt_id: Identifier
    case_review: Literal["verified", "needs_revision"] | None
    evidence_reviewed: bool | None
    answer_correct: bool | None
    unnecessary_block: bool | None
    unsupported_execution: bool | None
    requirements_preserved: bool | None
    acceptable: bool | None
    critical_error: bool | None
    fabricated_evidence: bool | None
    notes: Note


class QualitySave(StrictModel):
    review_id: Identifier
    packet_sha256: Hash
    judgments: Annotated[tuple[QualityJudgment, ...], Field(min_length=1, max_length=8)]


class QualitySubmit(QualitySave):
    human_attested: bool


class QualityReviewView(StrictModel):
    id: Identifier
    revision: Revision
    title: Annotated[str, Field(min_length=1, max_length=200)]
    created_at: Utc
    updated_at: Utc
    origin: QualityOrigin
    packet: ReviewPacket
    packet_sha256: Hash
    targets: Annotated[tuple[QualityTarget, ...], Field(min_length=1, max_length=8)]
    status: Literal["draft", "submitted"]
    judgments: Annotated[tuple[QualityJudgment, ...], Field(min_length=1, max_length=8)]
    submission: ReviewSubmission | None


class QualityReviewRecord(QualityReviewView):
    files: QualityFiles
    exported_files: QualityFiles | None
    basis: Literal["human_evidence_review", "controlled_test"]
    registered_by: Identifier


class QualityReviewSummary(StrictModel):
    id: Identifier
    revision: Revision
    title: str
    status: Literal["draft", "submitted"]
    updated_at: Utc
    origin: QualityOrigin


class QualityReviewPage(StrictModel):
    items: Annotated[tuple[QualityReviewSummary, ...], Field(max_length=25)]
    next_cursor: Identifier | None


class QualityExport(StrictModel):
    review_id: Identifier
    revision: Revision
    packet_sha256: Hash
    submission_sha256: Hash
    authenticated_reviewer_id: Identifier
    basis: Literal["human_evidence_review", "controlled_test"]
    files: QualityFiles


class QualityFeedback(StrictModel):
    id: Identifier
    revision: Revision
    run_id: Identifier
    run_revision: Revision
    input_revision: Revision
    category: Literal["latency", "clarification", "correction", "presentation", "content", "other"]
    notes: Annotated[str, Field(min_length=1, max_length=4000, pattern=r"\S")]
    created_at: Utc
    updated_at: Utc


class QualityFeedbackSave(StrictModel):
    run_id: Identifier
    feedback_id: Identifier
    run_revision: Revision
    input_revision: Revision
    category: Literal["latency", "clarification", "correction", "presentation", "content", "other"]
    notes: Annotated[str, Field(min_length=1, max_length=4000, pattern=r"\S")]


class QualityFeedbackPage(StrictModel):
    items: Annotated[tuple[QualityFeedback, ...], Field(max_length=100)]


ROOTS = (
    QualityFiles,
    QualityOrigin,
    QualityTarget,
    QualityJudgment,
    QualitySave,
    QualitySubmit,
    QualityReviewView,
    QualityReviewRecord,
    QualityReviewSummary,
    QualityReviewPage,
    QualityExport,
    QualityFeedback,
    QualityFeedbackSave,
    QualityFeedbackPage,
)
