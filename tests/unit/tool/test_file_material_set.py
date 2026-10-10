"""Controlled owning values prove set logic only, not production file authorization."""

import asyncio
from dataclasses import FrozenInstanceError, replace

import pytest

from tests.unit.tool.file_evidence_fixture import make_evidence
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.tool.providers.file_material import FileMaterial
from uaw.tool.providers.file_material_set import (
    FileMaterialSet,
    FileMaterialSetAdapter,
    FileMaterialSetLimits,
)


def material(ctx, suffix, text=" original 中😀 "):
    _, _, _, evidence, _ = make_evidence(ctx, text=text)
    names = (
        "material",
        "observation",
        "fragment",
        "command",
        "runner_receipt",
        "raw_result",
        "provider",
        "call",
    )
    refs = {name: evidence.receipt_ref for name in names}
    refs["material"] = evidence.receipt_ref.model_copy(update={"id": "file-material-" + suffix})
    return FileMaterial._from_verified(
        evidence.receipt.payload["result"], evidence.receipt.usage, ctx.principal, refs
    )


class ControlledReader:
    def __init__(self, values):
        self.values = values
        self.calls = []
        self.after = None

    async def read(self, ref, ctx):
        self.calls.append((ref.wire(), ctx))
        if self.after:
            await self.after(ref, ctx)
        return self.values[ref.id]


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_characters", 0),
        ("max_characters", 16385),
        ("max_characters", True),
        ("max_characters", 1.0),
        ("max_utf8_bytes", 0),
        ("max_utf8_bytes", 65537),
        ("max_utf8_bytes", False),
    ],
)
def test_set_limits_only_reduce_positive_defaults(field, value):
    with pytest.raises(ValueError):
        FileMaterialSetLimits(**{field: value})


async def test_order_frozen_values_and_two_current_reads_per_original(ctx):
    a, b = material(ctx, "a"), material(ctx, "b", "second\r\n")
    reader = ControlledReader({a.material_ref.id: a, b.material_ref.id: b})
    result = await FileMaterialSetAdapter(reader).read((b.material_ref, a.material_ref), ctx)
    assert result.materials == (b, a) and result.refs == (b.material_ref, a.material_ref)
    assert result.characters == len(a.text) + len(b.text)
    assert result.utf8_bytes == len((a.text + b.text).encode())
    assert [r[0]["id"] for r in reader.calls] == [b.material_ref.id, a.material_ref.id] * 2
    result.materials[0].content["text"] = "mutation"
    assert result.materials[0] == b
    with pytest.raises(FrozenInstanceError):
        result.materials = (a,)


@pytest.mark.parametrize(
    "invalid",
    ["list", "empty", "nine", "wire", "no_hash", "wrong_kind", "duplicate", "bad_version"],
)
async def test_invalid_complete_tuple_refused_before_owning_io(ctx, invalid):
    a = material(ctx, "a")
    ref = a.material_ref
    cases = {
        "list": [ref],
        "empty": (),
        "nine": (ref,) * 9,
        "wire": (ref.wire(),),
        "no_hash": (Ref(kind="content", id="unfixed", version="1"),),
        "wrong_kind": (ref.model_copy(update={"kind": "provider"}),),
        "duplicate": (ref, Ref.model_validate(ref.wire())),
        "bad_version": (ref.model_copy(update={"version": ""}),),
    }
    reader = ControlledReader({ref.id: a})
    with pytest.raises(DomainError):
        await FileMaterialSetAdapter(reader).read(cases[invalid], ctx)
    assert reader.calls == []


async def test_missing_reader_explicit_unavailable(ctx):
    with pytest.raises(DomainError) as exc:
        await FileMaterialSetAdapter(None).read((material(ctx, "a").material_ref,), ctx)
    assert exc.value.status_code == 503


@pytest.mark.parametrize("change", ["ref", "owner", "value_type"])
async def test_owning_response_binding_and_type_required(ctx, change):
    a = material(ctx, "a")
    if change == "ref":
        value = material(ctx, "b")
    elif change == "owner":
        value = material(
            ctx.model_copy(
                update={
                    "principal": ctx.principal.model_copy(update={"auth_session_id": "foreign"})
                }
            ),
            "a",
        )
    else:
        value = a.content
    with pytest.raises(DomainError):
        await FileMaterialSetAdapter(ControlledReader({a.material_ref.id: value})).read(
            (a.material_ref,), ctx
        )


@pytest.mark.parametrize("bound", ["characters", "bytes"])
async def test_total_bound_refuses_without_truncation_or_partial_return(ctx, bound):
    a, b = material(ctx, "a", "中😀"), material(ctx, "b", "中😀")
    limits = (
        FileMaterialSetLimits(max_characters=3)
        if bound == "characters"
        else FileMaterialSetLimits(max_utf8_bytes=13)
    )
    reader = ControlledReader({a.material_ref.id: a, b.material_ref.id: b})
    with pytest.raises(DomainError) as exc:
        await FileMaterialSetAdapter(reader, limits=limits).read(
            (a.material_ref, b.material_ref), ctx
        )
    assert exc.value.status_code == 413 and len(reader.calls) == 2
    assert a.text == b.text == "中😀"


async def test_changed_original_full_value_on_final_recheck_refuses(ctx):
    a, b = material(ctx, "a"), material(ctx, "b")
    reader = ControlledReader({a.material_ref.id: a, b.material_ref.id: b})

    async def changed(ref, context):
        if len(reader.calls) == 3:
            reader.values[a.material_ref.id] = replace(a, _usage=b'{"controlled":"changed"}')

    reader.after = changed
    with pytest.raises(DomainError) as exc:
        await FileMaterialSetAdapter(reader).read((a.material_ref, b.material_ref), ctx)
    assert exc.value.status_code == 412


async def test_second_await_task_cancel_returns_no_collection(ctx):
    a, b = material(ctx, "a"), material(ctx, "b")
    reader = ControlledReader({a.material_ref.id: a, b.material_ref.id: b})
    waiting = asyncio.Event()

    async def blocked(ref, context):
        if ref == b.material_ref:
            waiting.set()
            await asyncio.Event().wait()

    reader.after = blocked
    task = asyncio.create_task(
        FileMaterialSetAdapter(reader).read((a.material_ref, b.material_ref), ctx)
    )
    await waiting.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert len(reader.calls) == 2


@pytest.mark.parametrize("values", [(), [], (object(),)])
def test_collection_requires_immutable_tuple(values):
    with pytest.raises(ValueError):
        FileMaterialSet(values)


async def test_eight_sources_exact_total_bound_preserves_separate_bodies(ctx):
    values = tuple(material(ctx, str(i), "中😀") for i in range(8))
    reader = ControlledReader({m.material_ref.id: m for m in values})
    limits = FileMaterialSetLimits(max_characters=16, max_utf8_bytes=56)
    result = await FileMaterialSetAdapter(reader, limits=limits).read(
        tuple(m.material_ref for m in values), ctx
    )
    assert result.materials == values and result.characters == 16 and result.utf8_bytes == 56
    assert len(reader.calls) == 16
