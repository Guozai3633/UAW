"""Quality handlers called only after normal cookie/bearer/CSRF authentication."""

from typing import Any

from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.run.evaluation_review import ReviewInputError
from uaw.run.quality import QualityReviews, parsed
from uaw.shared.contracts import Principal, RequestMeta
from uaw.shared.errors import reject
from uaw.shared.quality import QualityFeedbackSave, QualitySave, QualitySubmit

ROUTES = (
    (
        "quality.reviews.list",
        "GET",
        "/v1/quality/reviews",
        "QualityReviewsListRequest",
        "QualityReviewPage",
    ),
    (
        "quality.reviews.get",
        "GET",
        "/v1/quality/reviews/{review_id}",
        "QualityReviewsGetRequest",
        "QualityReviewView",
    ),
    (
        "quality.reviews.save",
        "POST",
        "/v1/quality/reviews/{review_id}/draft",
        "QualityReviewsSaveRequest",
        "QualityReviewView",
    ),
    (
        "quality.reviews.submit",
        "POST",
        "/v1/quality/reviews/{review_id}/submission",
        "QualityReviewsSubmitRequest",
        "QualityReviewView",
    ),
    (
        "quality.reviews.export",
        "GET",
        "/v1/quality/reviews/{review_id}/export",
        "QualityReviewsExportRequest",
        "QualityExport",
    ),
    (
        "quality.feedback.list",
        "GET",
        "/v1/runs/{run_id}/feedback",
        "QualityFeedbackListRequest",
        "QualityFeedbackPage",
    ),
    (
        "quality.feedback.save",
        "POST",
        "/v1/runs/{run_id}/feedback",
        "QualityFeedbackSaveRequest",
        "QualityFeedback",
    ),
)


async def endpoint(
    records: PostgresRecordStore,
    actor: Principal,
    operation: str,
    payload: dict[str, Any],
    meta: RequestMeta | None,
) -> dict[str, Any]:
    if actor.kind != "user":
        raise reject("quality_user_required", "Authenticated review owner required", 403)
    service = QualityReviews(records)
    if operation == "quality.reviews.list":
        return await service.list(actor, payload.get("cursor"))
    if operation == "quality.reviews.get":
        return await service.get(actor, payload["review_id"])
    if operation == "quality.reviews.export":
        return await service.export(actor, payload["review_id"])
    if operation == "quality.feedback.list":
        return await service.feedback(actor, payload["run_id"])
    assert meta is not None
    if meta.expected_revision is None:
        raise reject("quality_revision_required", "Expected review/feedback revision required")
    if operation == "quality.feedback.save":
        return await service.save_feedback(actor, parsed(QualityFeedbackSave, payload), meta)
    try:
        request = (
            parsed(QualitySubmit, payload)
            if operation == "quality.reviews.submit"
            else parsed(QualitySave, payload)
        )
        return await service.save(actor, request, meta)
    except ReviewInputError:
        raise reject(
            "quality_judgment_invalid", "Judgments conflict or differ from the original packet"
        ) from None
