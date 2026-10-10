"""Actual SQL/Windows handle material chain; authority/key/pager sources controlled."""

import asyncio
import hashlib

import pytest

from tests.integration.tool.file_pipeline_fixture import approve_file, recover_file
from tests.integration.tool.file_pipeline_fixture import file_pipeline as file_pipeline
from tests.integration.tool.test_durable import cancel
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.tool.invocation.schema import normalize
from uaw.tool.providers.file_material import FileMaterialAdapter, FileMaterialLimits


async def exported(p):
    await approve_file(p)
    first = await p.facade.invoke(p.raw, p.case.ctx)
    assert first["kind"] == "ok", first
    material = await FileMaterialAdapter(p.source).export(p.case.call["action_id"], p.case.ctx)
    assert material.content == first["payload"]["data"]
    return material


async def test_material_exact_original_immutable_refs_and_no_original_reopen(file_pipeline):
    p = file_pipeline
    material = await exported(p)
    original = (p.root / "file.txt").read_bytes()
    assert material.text.encode("utf-8") == original
    assert material.file_hash == hashlib.sha256(original).hexdigest()
    assert material.fragment_ref.content_hash == material.file_hash  # whole only
    assert material.raw_result_ref.content_hash == material.material_ref.content_hash
    assert material.observation_ref != material.material_ref
    assert material.owner == p.case.ctx.principal
    assert (
        material.usage["billing_state"] == "pending" and "money" not in material.usage["resources"]
    )
    material.content["text"] = "consumer does not own mutable original"
    ref_copy = material.fragment_ref.wire()
    ref_copy["location"]["kind"] = "lines"
    assert material.fragment_ref.location.kind == "whole"
    (p.root / "file.txt").unlink()
    await cancel(p.case)
    p.role.allowed = False
    fresh = recover_file(p)
    reader = FileMaterialAdapter(fresh.source)
    assert await reader.read(material.material_ref, p.case.ctx) == material
    assert await reader.export(p.case.call["action_id"], p.case.ctx) == material
    assert p.bridge.calls == p.bridge.opens == 1 and fresh.bridge.calls == fresh.bridge.opens == 0
    assert (await fresh.budget.get_ledger(p.case.ctx))["held"]["money"] == "0.05"


async def test_actual_partial_material_never_uses_fragment_as_whole_hash(file_pipeline):
    p = file_pipeline
    p.raw["arguments"]["location"] = {"kind": "text_span", "start": 2, "end": 10}
    p.case.call = normalize(p.raw, p.case.registry)
    material = await exported(p)
    whole = (p.root / "file.txt").read_bytes()
    assert material.file_hash == hashlib.sha256(whole).hexdigest()
    assert (
        material.fragment_ref.content_hash
        == hashlib.sha256(material.text.encode("utf-8")).hexdigest()
    )
    assert material.fragment_ref.content_hash != material.file_hash
    assert material.content["location"] == p.raw["arguments"]["location"]
    assert not hasattr(material, "snapshot")


@pytest.mark.parametrize("revoke", ["root", "data", "key"])
async def test_current_data_revoke_blocks_material_ref_even_with_cached_bytes(
    file_pipeline, revoke
):
    p = file_pipeline
    material = await exported(p)
    if revoke == "root":
        p.bridge.allowed = False
    elif revoke == "data":
        p.bridge.data_authority.allowed = False
    else:
        p.signatures.revoked = True
    fresh = recover_file(p)
    with pytest.raises(DomainError):
        await FileMaterialAdapter(fresh.source).read(material.material_ref, p.case.ctx)
    assert p.bridge.calls == 1 and fresh.bridge.calls == fresh.bridge.opens == 0


@pytest.mark.parametrize("change", ["session", "project", "attempt", "hash", "location"])
async def test_material_exact_owner_context_and_ref_no_cross_scope(file_pipeline, change):
    p = file_pipeline
    material = await exported(p)
    ref, ctx = material.material_ref, p.case.ctx
    if change == "session":
        ctx = ctx.model_copy(
            update={"principal": ctx.principal.model_copy(update={"auth_session_id": "foreign"})}
        )
    elif change == "project":
        ctx = ctx.model_copy(
            update={"scope": ctx.scope.model_copy(update={"project_id": "foreign"})}
        )
    elif change == "attempt":
        ctx = ctx.model_copy(update={"attempt_id": "foreign-material-attempt"})
    elif change == "hash":
        ref = ref.model_copy(update={"content_hash": "0" * 64})
    else:
        ref = ref.model_copy(update={"location": material.fragment_ref.location})
    with pytest.raises(DomainError):
        await FileMaterialAdapter(p.source).read(ref, ctx)
    assert p.bridge.calls == p.bridge.opens == 1


async def test_export_bounds_refuse_not_truncate_original_and_default_16384(file_pipeline):
    p = file_pipeline
    (p.root / "file.txt").write_bytes(b"x" * 16385)
    await approve_file(p)
    result = await p.facade.invoke(p.raw, p.case.ctx)
    assert result["kind"] == "ok"
    reader = FileMaterialAdapter(p.source)
    with pytest.raises(DomainError) as too_large:
        await reader.export(p.case.call["action_id"], p.case.ctx)
    assert too_large.value.status_code == 413
    assert (
        await p.case.ledger.get("tool.file.material.refs", p.case.ctx.attempt_id, p.case.ctx)
        is None
    )
    explicit = FileMaterialAdapter(p.source, limits=FileMaterialLimits(max_characters=20000))
    material = await explicit.export(p.case.call["action_id"], p.case.ctx)
    assert len(material.text) == 16385 and p.bridge.opens == 1
    with pytest.raises(DomainError):
        await reader.read(material.material_ref, p.case.ctx)


async def test_concurrent_material_export_cas_dedup_same_source_and_no_lock_io(file_pipeline):
    p = await approve_file(file_pipeline)
    assert (await p.facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    readers = [FileMaterialAdapter(p.source), FileMaterialAdapter(recover_file(p).source)]
    rows = await asyncio.gather(*(r.export(p.case.call["action_id"], p.case.ctx) for r in readers))
    assert rows[0] == rows[1]
    assert p.bridge.calls == p.bridge.opens == 1


async def test_revocation_during_material_publication_cannot_return_stale_body(file_pipeline):
    p = await approve_file(file_pipeline)
    assert (await p.facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    reader = FileMaterialAdapter(p.source)
    fixed = reader._fixed

    async def revoked(*args):
        await fixed(*args)
        p.bridge.allowed = False

    reader._fixed = revoked
    with pytest.raises(DomainError):
        await reader.export(p.case.call["action_id"], p.case.ctx)
    assert (
        await p.case.ledger.get("tool.file.material.refs", p.case.ctx.attempt_id, p.case.ctx)
        is not None
    )
    with pytest.raises(DomainError):
        await FileMaterialAdapter(p.source).read(
            Ref.model_validate(
                await p.case.ledger.get(
                    "tool.file.material.refs", p.case.ctx.attempt_id, p.case.ctx
                )
            ),
            p.case.ctx,
        )
    assert p.bridge.opens == 1


async def test_publication_ack_lost_fixed_material_refs_restore_original_without_send(
    file_pipeline,
):
    p = file_pipeline
    await exported(p)
    reader = FileMaterialAdapter(p.source)
    fixed = reader._fixed

    async def lost(*args):
        await fixed(*args)
        raise TimeoutError("Controlled material CAS acknowledgement lost after actual SQL commit")

    reader._fixed = lost
    with pytest.raises(TimeoutError):
        await reader.export(p.case.call["action_id"], p.case.ctx)
    ref = Ref.model_validate(
        await p.case.ledger.get("tool.file.material.refs", p.case.ctx.attempt_id, p.case.ctx)
    )
    (p.root / "file.txt").unlink()
    fresh = recover_file(p)
    assert (await FileMaterialAdapter(fresh.source).read(ref, p.case.ctx)).text
    assert fresh.bridge.calls == fresh.bridge.opens == 0 and p.bridge.opens == 1


async def test_unknown_original_receipt_cannot_make_material_or_new_attempt(file_pipeline):
    p = await approve_file(file_pipeline)

    async def lost(*args):
        p.bridge.calls += 1
        raise TimeoutError("Controlled original unknown receipt")

    p.executor.execute = lost
    assert (await p.facade.invoke(p.raw, p.case.ctx))["failure"]["code"] == "invocation_interrupted"
    with pytest.raises(DomainError):
        await FileMaterialAdapter(recover_file(p).source).export(
            p.case.call["action_id"], p.case.ctx
        )
    assert (
        await p.case.ledger.get("tool.file.material.refs", p.case.ctx.attempt_id, p.case.ctx)
        is None
    )
    assert (await p.case.budget.get_ledger(p.case.ctx))["held"]["money"] == "0.05"
    assert p.bridge.calls == 1 and p.bridge.opens == 0
