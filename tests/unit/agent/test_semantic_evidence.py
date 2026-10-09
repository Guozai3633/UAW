"""Even a faulty assessor adapter cannot substitute unknown IDs for actual evidence."""

from types import SimpleNamespace

import pytest

from uaw.agent.completion.evidence import CompletionEvidence
from uaw.agent.completion.semantic import SemanticVerifier
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError


@pytest.mark.parametrize(
    ("identity", "evidence_ids", "failure"),
    [
        ("wanted", ["invented"], "completion_evidence_invented"),
        ("wanted", ["input-0"], "completion_evidence_missing"),
        ("another", ["artifact"], "completion_coverage_missing"),
    ],
)
async def test_assessor_adapter_cannot_bypass_exact_coverage_and_artifact(
    identity, evidence_ids, failure
):
    artifact = Ref(kind="artifact", id="actual-artifact", version="1")
    original = Ref(kind="input", id="actual-original", version="1")

    class AssessorFixture:
        async def evaluate(self, purpose, instruction, data, schema, ctx, **kwargs):
            assert schema["properties"]["verdicts"]["minItems"] == 1
            assert schema["properties"]["verdicts"]["items"]["properties"]["evidence_ids"]["items"][
                "enum"
            ] == ["artifact", "input-0"]
            return SimpleNamespace(
                data={
                    "verdicts": [
                        {
                            "requirement_id": identity,
                            "state": "passed",
                            "evidence_ids": evidence_ids,
                            "reason": "Controlled faulty adapter",
                            "limitations": [],
                        }
                    ]
                },
                output_ref=Ref(kind="content", id="actual-review", version="1"),
            )

    evidence = CompletionEvidence({}, {"artifact": artifact, "input-0": original}, (), ())
    with pytest.raises(DomainError) as exc:
        await SemanticVerifier(AssessorFixture()).verify(
            {"requirements": [{"id": "wanted"}]}, artifact, evidence, None
        )
    assert exc.value.failure.code == failure
