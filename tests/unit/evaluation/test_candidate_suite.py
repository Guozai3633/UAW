"""The candidate corpus is not a real run or a human-reviewed gold dataset."""

from pathlib import Path

from uaw.evaluation.reader import load_bundle
from uaw.evaluation.runner import evaluate

ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "evaluation" / "ms-e1-candidates"


def test_sixteen_candidates_keep_disjoint_splits_and_explicit_unreviewed_status():
    bundle = load_bundle(
        *(
            ROOT / name
            for name in ("suite.json", "manifest.json", "observations.jsonl", "reviews.jsonl")
        )
    )
    cases = bundle.suite.cases
    assert len(cases) == 16
    assert sum(c.split == "revision" for c in cases) == 8
    assert sum(c.split == "holdout" for c in cases) == 8
    assert all(
        c.review_status == "needs_human_review" and c.human_verification is None for c in cases
    )
    assert {c.category for c in cases} == {
        "office",
        "academic",
        "technical",
        "missing_material",
        "reasonable_ambiguity",
        "correction",
    }
    assert any(c.id == "technical-tcc-zk" for c in cases)
    report = evaluate(bundle)
    assert report.release_gate.status == "incomplete"
    assert report.candidate.attempt_count == 0 and report.candidate.answer_error.value is None


def test_m1_published_input_and_report_schemas_do_not_drift_during_m3():
    import json

    from uaw.evaluation.contracts import Manifest, Observation, Report, Review, Suite

    root = Path(__file__).resolve().parents[3]
    frozen = json.loads(
        (root / "docs/implementation/evaluation/MS-E1-schemas.json").read_text(encoding="utf-8")
    )
    assert frozen["schema_version"] == "ms-e1.v1"
    for model in (Suite, Manifest, Observation, Review, Report):
        assert model.model_json_schema() == frozen["types"][model.__name__]
