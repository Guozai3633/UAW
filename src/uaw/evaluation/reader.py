"""Read only the four explicitly supplied offline files, with no URL/ref expansion."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from uaw.evaluation.contracts import Manifest, NamedHash, Observation, Review, StrictModel, Suite
from uaw.evaluation.io import EvaluationInputError, canonical, parse_json, read_bounded


def record[T: StrictModel](model: type[T], value: object) -> T:
    try:
        return model.model_validate_json(canonical(value))
    except ValidationError as exc:
        locations = [".".join(str(p) for p in e["loc"]) for e in exc.errors(include_input=False)]
        raise EvaluationInputError("invalid_contract:" + ",".join(locations[:8])) from None


def json_lines[T: StrictModel](model: type[T], raw: bytes) -> tuple[T, ...]:
    result: list[T] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        if len(line) > 262144:
            raise EvaluationInputError("jsonl_record_too_large")
        if len(result) >= 4096:
            raise EvaluationInputError("too_many_jsonl_records")
        result.append(record(model, parse_json(line)))
    return tuple(result)


@dataclass(frozen=True)
class Bundle:
    suite: Suite
    manifest: Manifest
    observations: tuple[Observation, ...]
    reviews: tuple[Review, ...]
    input_sha256: tuple[NamedHash, ...]


def load_bundle(suite: Path, manifest: Path, observations: Path, reviews: Path) -> Bundle:
    names = ("suite", "manifest", "observations", "reviews")
    paths = (suite, manifest, observations, reviews)
    raw = tuple(
        read_bounded(path, limit=limit)
        for path, limit in zip(paths, (2**21, 2**21, 2**24, 2**23), strict=True)
    )
    parsed_observations = json_lines(Observation, raw[2])
    parsed_reviews = json_lines(Review, raw[3])
    for values in (
        tuple((o.manifest_id, o.attempt_id) for o in parsed_observations),
        tuple((o.manifest_id, o.logical_request_id, o.attempt_number) for o in parsed_observations),
        tuple((r.manifest_id, r.id) for r in parsed_reviews),
        tuple((r.manifest_id, r.attempt_id, r.basis) for r in parsed_reviews),
    ):
        if len(set(values)) != len(values):
            raise EvaluationInputError("duplicate_attempt_or_review")
    return Bundle(
        record(Suite, parse_json(raw[0])),
        record(Manifest, parse_json(raw[1])),
        parsed_observations,
        parsed_reviews,
        tuple(
            NamedHash(name=name, sha256=hashlib.sha256(data).hexdigest())
            for name, data in zip(names, raw, strict=True)
        ),
    )
