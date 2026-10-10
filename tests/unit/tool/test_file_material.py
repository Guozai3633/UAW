"""Immutable existing named material DTOs; no grants, Runner or LLM represented."""

from dataclasses import FrozenInstanceError

import pytest

from tests.unit.tool.file_evidence_fixture import make_evidence
from uaw.shared.contracts import Ref
from uaw.tool.providers.file_material import FileMaterial, FileMaterialLimits


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_characters", 0),
        ("max_utf8_bytes", 0),
        ("max_characters", 65537),
        ("max_utf8_bytes", 65537),
        ("max_characters", True),
    ],
)
def test_material_limits_do_not_expand_actual_file_maximum(field, value):
    with pytest.raises(ValueError):
        FileMaterialLimits(**{field: value})


def test_material_is_immutable_selected_text_and_fresh_named_copies(ctx):
    _, _, _, evidence, _ = make_evidence(ctx)
    content = evidence.receipt.payload["result"]
    references = {
        name: evidence.receipt_ref
        for name in [
            "material",
            "observation",
            "fragment",
            "command",
            "runner_receipt",
            "raw_result",
            "provider",
            "call",
        ]
    }
    material = FileMaterial._from_verified(
        content, evidence.receipt.usage, ctx.principal, references
    )
    copy = material.content
    copy["text"] = "consumer mutation"
    material.usage["resources"]["wall_time_ms"] = 999
    assert material.text == content["text"]
    assert material.usage["resources"]["wall_time_ms"] == 1
    assert material.file_hash == content["content_hash"] and material.owner == ctx.principal
    assert material.observation_ref == evidence.receipt_ref
    assert isinstance(material.material_ref, Ref)
    assert not hasattr(material, "snapshot")
    with pytest.raises(FrozenInstanceError):
        material._content = b"changed"


async def test_missing_owning_reader_refuses_export_and_ref_reuse(ctx):
    from uaw.shared.errors import DomainError
    from uaw.tool.providers.file_material import FileMaterialAdapter

    reader = FileMaterialAdapter(None)
    with pytest.raises(DomainError) as unavailable:
        await reader.export("file-action", ctx)
    assert unavailable.value.status_code == 503
    with pytest.raises(DomainError):
        await reader.read(Ref(kind="content", id="claimed-material", version="1"), ctx)


@pytest.mark.parametrize("missing", ["access", "verifier", "bridge", "signatures"])
def test_material_source_metadata_is_not_a_reader_grant(ctx, missing):
    from tests.unit.tool.test_file_ports import ControlledBridge, store
    from uaw.shared.errors import DomainError
    from uaw.tool.providers.file_material import FileMaterialAdapter

    source, _, _, _, signatures = store(ctx, bridge=ControlledBridge())
    source.signatures = signatures
    source.access = object()
    source.verifier = object()
    setattr(source, missing, None)
    with pytest.raises(DomainError) as unavailable:
        FileMaterialAdapter(source).ready()
    assert unavailable.value.status_code == 503
