"""Owner-scoped review/feedback persistence; never mutates execution state."""

import json
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

from sqlalchemy import select

from uaw.evaluation.contracts import Answer, StrictModel
from uaw.evaluation.io import digest
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore, timestamp
from uaw.run.evaluation_capture import prepare_bundle, read_run
from uaw.run.evaluation_review import (
    FILES,
    ReviewPacket,
    ReviewSubmission,
    _targets,
    import_review,
    source_bundle,
)
from uaw.shared.contracts import Principal, RequestMeta
from uaw.shared.errors import reject
from uaw.shared.quality import (
    QualityExport,
    QualityFeedback,
    QualityFeedbackSave,
    QualityFiles,
    QualityJudgment,
    QualityOrigin,
    QualityReviewRecord,
    QualityReviewView,
    QualitySave,
    QualitySubmit,
    QualityTarget,
    QualityVerificationOutput,
)
from uaw.shared.stores import StoreConflict

REVIEWS = "quality.reviews"
FEEDBACK = "quality.feedback"


def parsed[Model: StrictModel](model: type[Model], value: Any) -> Model:
    return model.model_validate_json(json.dumps(value, ensure_ascii=False, allow_nan=False))


def read_files(source: Path) -> QualityFiles:
    return parsed(
        QualityFiles,
        {name.split(".")[0]: (source / name).read_bytes().decode("utf-8") for name in FILES},
    )


def write_files(source: Path, files: QualityFiles) -> None:
    for name in FILES:
        (source / name).write_bytes(getattr(files, name.split(".")[0]).encode("utf-8"))


def view(record: QualityReviewRecord) -> dict[str, Any]:
    return parsed(
        QualityReviewView,
        {k: v for k, v in record.wire().items() if k in QualityReviewView.model_fields},
    ).wire()


def blank(target: QualityTarget) -> QualityJudgment:
    return QualityJudgment(
        case_id=target.binding.case_id,
        attempt_id=target.binding.attempt_id,
        case_review=None,
        evidence_reviewed=None,
        answer_correct=None,
        unnecessary_block=None,
        unsupported_execution=None,
        requirements_preserved=None,
        acceptable=None,
        critical_error=None,
        fabricated_evidence=None,
        notes="",
    )


class QualityReviews:
    def __init__(self, records: PostgresRecordStore) -> None:
        self.records = records
        self.transactions = TransactionalStore(records.database)

    async def register(
        self,
        operator: Principal,
        owner: Principal,
        source: Path,
        origin: QualityOrigin,
        title: str,
        meta: RequestMeta,
        *,
        source_records: PostgresRecordStore | None = None,
    ) -> dict[str, Any]:
        """Trusted composition/CLI only. Public browser has no registration route."""
        if operator.kind not in ("admin", "service") or owner.kind != "user":
            raise reject("quality_registration_denied", "Trusted source registration required", 403)
        bundle, raw = source_bundle(source)
        original_outputs = {}
        if len(bundle.suite.cases) != 1:
            raise reject("quality_origin_inventory", "One original Run per registered packet")
        if bundle.manifest.candidate.source_commit != origin.source_commit:
            raise reject("quality_origin_mismatch", "Original source version required")
        if origin.kind == "actual_run":
            if bundle.manifest.candidate.provenance != "actual_candidate":
                raise reject("quality_origin_mismatch", "Actual source required")
            actor = Principal(
                id=origin.principal_id, kind="user", auth_session_id=operator.auth_session_id
            )
            rows = await read_run((source_records or self.records).database, actor, origin.run_id)
            index = {(row.namespace, row.id): row for row in rows}
            original_outputs = {
                row.id: row.payload for row in rows if row.namespace == "model.outputs"
            }
            run = index[("runs", origin.run_id)]
            inputs = index[("run.input_sets", origin.run_id)]
            refs = [inputs.payload["original_input_ref"], *inputs.payload["patch_refs"]]
            texts = [index[("inputs", ref["id"])].payload["text"] for ref in refs]
            prompt = texts[0] + "".join("\n\n用户追加要求\n" + text for text in texts[1:])
            if (
                run.revision != origin.run_revision
                or inputs.revision != origin.input_revision
                or run.payload["status"] not in ("completed", "cancelled", "failed")
                or prompt != bundle.suite.cases[0].prompt
                or {row.id for row in rows if row.namespace == "model.invocations"}
                != {row.attempt_id for row in bundle.observations}
            ):
                raise reject(
                    "quality_origin_mismatch", "Run/input/invocation inventory differs", 412
                )
            candidate = bundle.manifest.candidate
            rebuilt = prepare_bundle(
                rows,
                bundle.suite.cases[0],
                bundle.manifest.policy,
                candidate_id=candidate.id,
                source_commit=origin.source_commit,
                environment_hash=candidate.environment_sha256,
                prompt_hash=candidate.prompts[0].sha256,
                selected_attempt=candidate.selections[0].answer_attempt_id,
            )
            if (
                rebuilt["observations"] != [row.wire() for row in bundle.observations]
                or rebuilt["manifest"] != bundle.manifest.wire()
            ):
                raise reject(
                    "quality_capture_mismatch", "Original model/usage evidence differs", 412
                )
        elif bundle.manifest.candidate.provenance != "controlled_fixture":
            raise reject("quality_origin_mismatch", "Controlled fixture source required")
        packet = ReviewPacket(
            schema_version="uaw.human-review-packet.v1",
            created_at=timestamp(),
            input_sha256=bundle.input_sha256,
            targets=_targets(bundle),
        )
        cases = {case.id: case for case in bundle.suite.cases}
        observations = {row.attempt_id: row for row in bundle.observations}
        targets = tuple(
            QualityTarget(
                binding=target,
                case=cases[target.case_id],
                answer=cast(Answer, observations[target.attempt_id].output),
                verifications=tuple(
                    row
                    for row in bundle.observations
                    if row.reviewer is not None
                    and row.reviewer.target_attempt_id == target.attempt_id
                ),
                verification_outputs=tuple(
                    QualityVerificationOutput(
                        attempt_id=row.attempt_id,
                        output_sha256=digest(original_outputs[row.attempt_id]),
                        text=original_outputs[row.attempt_id]["text"],
                    )
                    for row in bundle.observations
                    if row.reviewer is not None
                    and row.reviewer.target_attempt_id == target.attempt_id
                    and row.attempt_id in original_outputs
                ),
            )
            for target in packet.targets
        )
        key = (
            "quality-"
            + digest(
                {
                    "owner": owner.id,
                    "origin": origin.wire(),
                    "source": [pin.wire() for pin in bundle.input_sha256],
                }
            )[:40]
        )
        record = QualityReviewRecord(
            id=key,
            revision=1,
            title=title,
            created_at=packet.created_at,
            updated_at=packet.created_at,
            origin=origin,
            packet=packet,
            packet_sha256=digest(packet.wire()),
            targets=targets,
            status="draft",
            judgments=tuple(blank(target) for target in targets),
            submission=None,
            files=parsed(
                QualityFiles,
                {name.split(".")[0]: value.decode("utf-8") for name, value in raw.items()},
            ),
            exported_files=None,
            registered_by=operator.id,
            basis="controlled_test"
            if origin.kind == "controlled_test"
            else "human_evidence_review",
        )

        async def action(tx: RecordTransaction) -> dict[str, Any]:
            if meta.expected_revision != 0:
                raise StoreConflict()
            await tx.write(REVIEWS, key, "QualityReviewRecord", record.wire())
            await tx.emit(key, "quality.registered", {"review_id": key, "operator_id": operator.id})
            return view(record)

        return await self.transactions.execute(
            owner,
            key,
            meta,
            {
                "operation": "register",
                "origin": origin.wire(),
                "source": record.files.wire(),
                "title": title,
            },
            action,
        )

    async def get(self, actor: Principal, key: str) -> dict[str, Any]:
        stored = await self.records.get(actor, REVIEWS, key)
        return view(parsed(QualityReviewRecord, stored.payload))

    async def list(self, actor: Principal, cursor: str | None = None) -> dict[str, Any]:
        async with self.records.database.sessions() as session:
            query = select(RecordRow).where(
                RecordRow.principal_id == actor.id,
                RecordRow.namespace == REVIEWS,
                RecordRow.deleted.is_(False),
            )
            if cursor is not None:
                query = query.where(RecordRow.resource_id > cursor)
            rows = list(await session.scalars(query.order_by(RecordRow.resource_id).limit(26)))
            return {
                "items": [
                    {
                        k: row.payload[k]
                        for k in ("id", "revision", "title", "status", "updated_at", "origin")
                    }
                    for row in rows[:25]
                ],
                "next_cursor": rows[24].resource_id if len(rows) > 25 else None,
            }

    async def save(
        self,
        actor: Principal,
        request: QualitySave | QualitySubmit,
        meta: RequestMeta,
    ) -> dict[str, Any]:
        submitting = isinstance(request, QualitySubmit)

        async def action(tx: RecordTransaction) -> dict[str, Any]:
            row = await tx.load(REVIEWS, request.review_id)
            original = parsed(QualityReviewRecord, row.payload)
            if meta.expected_revision != row.revision or original.status != "draft":
                raise StoreConflict("quality_review_revision_conflict")
            supplied = [(item.case_id, item.attempt_id) for item in request.judgments]
            expected = {
                (target.binding.case_id, target.binding.attempt_id) for target in original.targets
            }
            if (
                request.packet_sha256 != original.packet_sha256
                or len(supplied) != len(set(supplied))
                or set(supplied) != expected
            ):
                raise reject(
                    "quality_target_mismatch",
                    "Original packet and complete target inventory required",
                    412,
                )
            data = original.wire()
            data.update(
                revision=row.revision + 1,
                updated_at=timestamp(),
                judgments=[item.wire() for item in request.judgments],
            )
            if isinstance(request, QualitySubmit):
                if request.human_attested is not True:
                    raise reject(
                        "quality_attestation_required", "Explicit reviewer declaration required"
                    )
                items = []
                for item in request.judgments:
                    if (
                        item.critical_error is None
                        or item.evidence_reviewed is not True
                        or item.case_review is None
                        or not item.notes.strip()
                    ):
                        raise reject(
                            "quality_judgment_incomplete",
                            "Save a draft until evidence and required judgments are complete",
                        )
                    items.append(
                        {
                            "case_id": item.case_id,
                            "attempt_id": item.attempt_id,
                            "case_review": item.case_review,
                            "evidence_reviewed": True,
                            "labels": {
                                key: getattr(item, key)
                                for key in (
                                    "answer_correct",
                                    "unnecessary_block",
                                    "unsupported_execution",
                                    "requirements_preserved",
                                    "acceptable",
                                    "critical_error",
                                )
                            },
                            "notes": item.notes
                            + "\n[web fabricated_evidence="
                            + json.dumps(item.fabricated_evidence)
                            + "]",
                        }
                    )
                submission = parsed(
                    ReviewSubmission,
                    {
                        "schema_version": "uaw.human-review-submission.v1",
                        "packet_sha256": original.packet_sha256,
                        "reviewer_id": actor.id,
                        "reviewed_at": data["updated_at"],
                        "human_attested": True,
                        "items": items,
                    },
                )
                with TemporaryDirectory(prefix="uaw-quality-") as directory:
                    base = Path(directory)
                    source = base / "source"
                    source.mkdir()
                    write_files(source, original.files)
                    import_review(
                        source,
                        original.packet,
                        submission,
                        base / "export",
                        now=datetime.now(UTC),
                        basis=original.basis,
                    )
                    data.update(
                        status="submitted",
                        submission=submission.wire(),
                        exported_files=read_files(base / "export").wire(),
                    )
            updated = parsed(QualityReviewRecord, data)
            previous_revision = row.revision
            await tx.write(REVIEWS, updated.id, "QualityReviewRecord", updated.wire(), row.revision)
            await tx.emit(
                updated.id,
                "quality.submitted" if submitting else "quality.saved",
                {
                    "review_id": updated.id,
                    "revision": updated.revision,
                    "auth_session_id": actor.auth_session_id,
                    "basis": updated.basis,
                },
                base_revision=previous_revision,
                result_revision=updated.revision,
            )
            return view(updated)

        return await self.transactions.execute(
            actor,
            request.review_id,
            meta,
            {
                "operation": "submit" if submitting else "save",
                "request": request.wire(),
                "expected_revision": meta.expected_revision,
            },
            action,
        )

    async def export(self, actor: Principal, key: str) -> dict[str, Any]:
        row = await self.records.get(actor, REVIEWS, key)
        data = parsed(QualityReviewRecord, row.payload)
        if data.submission is None or data.exported_files is None:
            raise reject(
                "quality_submission_required", "Only submitted reviews can be exported", 409
            )
        return QualityExport(
            review_id=key,
            revision=data.revision,
            packet_sha256=data.packet_sha256,
            submission_sha256=digest(data.submission.wire()),
            authenticated_reviewer_id=data.submission.reviewer_id,
            basis=data.basis,
            files=data.exported_files,
        ).wire()

    async def feedback(self, actor: Principal, run_id: str) -> dict[str, Any]:
        await self.records.get(actor, "runs", run_id)
        async with self.records.database.sessions() as session:
            rows = list(
                await session.scalars(
                    select(RecordRow)
                    .where(
                        RecordRow.principal_id == actor.id,
                        RecordRow.namespace == FEEDBACK,
                        RecordRow.deleted.is_(False),
                        RecordRow.payload["run_id"].as_string() == run_id,
                    )
                    .order_by(RecordRow.resource_id)
                    .limit(101)
                )
            )
            if len(rows) > 100:
                raise reject(
                    "quality_feedback_capacity", "Feedback inventory exceeds page capacity", 409
                )
            return {"items": [row.payload for row in rows]}

    async def save_feedback(
        self,
        actor: Principal,
        request: QualityFeedbackSave,
        meta: RequestMeta,
    ) -> dict[str, Any]:
        run = await self.records.get(actor, "runs", request.run_id, revision=request.run_revision)
        inputs = await self.records.get(
            actor, "run.input_sets", request.run_id, revision=request.input_revision
        )
        conversation = await self.records.get(
            actor, "conversations", run.payload["conversation_id"]
        )
        if (
            actor.kind != "user"
            or conversation.payload["owner_id"] != actor.id
            or inputs.payload["run_id"] != request.run_id
            or inputs.payload["conversation_id"] != conversation.resource_id
        ):
            raise reject("quality_feedback_origin_denied", "Original owned Run/input required", 403)

        async def action(tx: RecordTransaction) -> dict[str, Any]:
            now, expected = timestamp(), meta.expected_revision
            if expected is None:
                raise StoreConflict("quality_feedback_revision_required")
            created = now
            if expected > 0:
                previous = await tx.load(FEEDBACK, request.feedback_id)
                if any(
                    previous.payload[key] != getattr(request, key)
                    for key in ("run_id", "run_revision", "input_revision")
                ):
                    raise reject(
                        "quality_feedback_origin_changed",
                        "Feedback remains bound to its original version",
                        412,
                    )
                created = previous.payload["created_at"]
            data = QualityFeedback(
                id=request.feedback_id,
                revision=expected + 1,
                run_id=request.run_id,
                run_revision=request.run_revision,
                input_revision=request.input_revision,
                category=request.category,
                notes=request.notes,
                created_at=created,
                updated_at=now,
            ).wire()
            await tx.write(FEEDBACK, request.feedback_id, "QualityFeedback", data, expected)
            await tx.emit(
                request.feedback_id,
                "quality.feedback.saved",
                {
                    "feedback_id": request.feedback_id,
                    "run_id": request.run_id,
                    "auth_session_id": actor.auth_session_id,
                },
                base_revision=expected,
                result_revision=expected + 1,
            )
            return data

        return await self.transactions.execute(
            actor,
            "feedback-" + request.feedback_id,
            meta,
            {
                "operation": "feedback",
                "request": request.wire(),
                "expected_revision": meta.expected_revision,
            },
            action,
        )
