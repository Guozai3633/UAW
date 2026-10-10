"""Actual C 55434 SQL, original file handles/crypto; controlled current routing/grants."""

import asyncio
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.integration.tool.file_material_set_fixture import exported_pair, registered_reader
from tests.integration.tool.file_material_set_fixture import material_pair as material_pair
from tests.integration.tool.test_durable import cancel
from uaw.shared.errors import DomainError
from uaw.tool.providers.file_material_set import FileMaterialSetAdapter, FileMaterialSetLimits
from uaw.tool.providers.file_store import recover_file_accounting


async def test_actual_two_original_order_and_restart_cancel_deleted_files_no_send(material_pair):
    p = material_pair
    materials = await exported_pair(p, (" first 中\r\n", "second😀 "))
    reader, _ = registered_reader(p, materials)
    refs = tuple(m.material_ref for m in reversed(materials))
    result = await FileMaterialSetAdapter(reader).read(refs, p.ctx)
    assert result.materials == tuple(reversed(materials)) and result.refs == refs
    assert result.characters == sum(len(m.text) for m in materials)
    assert [r["id"] for r in reader.calls] == [r.id for r in refs] * 2
    for pipe, m in zip(p.pipelines, materials, strict=True):
        assert m.file_hash == hashlib.sha256(m.text.encode()).hexdigest()
        assert m.fragment_ref.content_hash == m.file_hash
        assert m.material_ref.content_hash == m.raw_result_ref.content_hash
        assert m.observation_ref != m.material_ref
        assert m.usage["attempt_id"] == pipe.case.ctx.attempt_id
        assert m.usage["billing_state"] == "pending" and "money" not in m.usage["resources"]
        (pipe.root / "file.txt").unlink()
        pipe.role.allowed = False
    await cancel(p.pipelines[0].case)
    recovered_reader, recovered = registered_reader(p, materials, restart=True)
    assert await FileMaterialSetAdapter(recovered_reader).read(refs, p.ctx) == result
    assert all(x.bridge.calls == x.bridge.opens == 0 for x in recovered)
    assert all(x.bridge.calls == x.bridge.opens == 1 for x in p.pipelines)


async def test_duplicate_complete_ref_rejected_before_reader_io(material_pair):
    p = material_pair
    materials = await exported_pair(p)
    reader, _ = registered_reader(p, materials)
    with pytest.raises(DomainError) as exc:
        await FileMaterialSetAdapter(reader).read((materials[0].material_ref,) * 2, p.ctx)
    assert exc.value.status_code == 409 and reader.calls == []


@pytest.mark.parametrize("revoke", ["data", "root", "key", "version"])
async def test_first_revoked_while_second_awaits_no_partial_original(material_pair, revoke):
    p = material_pair
    materials = await exported_pair(p)
    reader, _ = registered_reader(p, materials)
    waiting, release = asyncio.Event(), asyncio.Event()

    async def blocked(ref, ctx):
        if ref == materials[1].material_ref:
            waiting.set()
            await release.wait()

    reader.before = blocked
    task = asyncio.create_task(
        FileMaterialSetAdapter(reader).read(tuple(m.material_ref for m in materials), p.ctx)
    )
    await asyncio.wait_for(waiting.wait(), 90)
    if revoke == "data":
        p.pipelines[0].bridge.data_authority.allowed = False
    elif revoke == "root":
        p.pipelines[0].bridge.allowed = False
    elif revoke == "key":
        p.pipelines[0].signatures.revoked = True
    else:
        first = p.pipelines[0]
        namespace = "tool.file.material.refs"
        row = await first.case.ledger.store.get(
            first.case.ctx.principal, namespace, first.case.ctx.attempt_id
        )
        await first.case.ledger.store.put(
            first.case.ctx.principal,
            namespace,
            first.case.ctx.attempt_id,
            row.schema_name,
            {**row.payload, "version": "2"},
            expected_revision=row.revision,
            request_id="controlled-set-await-version-change",
        )
    release.set()
    with pytest.raises(DomainError):
        await task
    assert [r["id"] for r in reader.calls] == [m.material_ref.id for m in materials] + [
        materials[0].material_ref.id
    ]
    assert all(x.bridge.opens == 1 for x in p.pipelines)


@pytest.mark.parametrize("changed", ["missing", "version", "provider", "subject"])
async def test_missing_wrong_version_provider_or_subject_denies_entire_set(material_pair, changed):
    p = material_pair
    materials = await exported_pair(p)
    reader, _ = registered_reader(p, materials)
    refs, ctx = tuple(m.material_ref for m in materials), p.ctx
    if changed == "missing":
        reader.entries.pop(materials[1].material_ref.id)
    elif changed == "version":
        refs = (refs[0], refs[1].model_copy(update={"version": "2"}))
    elif changed == "subject":
        ctx = ctx.model_copy(
            update={
                "principal": ctx.principal.model_copy(update={"auth_session_id": "foreign-session"})
            }
        )
    else:
        p.pipelines[1].source.provider = p.pipelines[1].provider.model_copy(
            update={"id": "foreign-provider"}
        )
    with pytest.raises(DomainError):
        await FileMaterialSetAdapter(reader).read(refs, ctx)
    assert all(x.bridge.opens == 1 for x in p.pipelines)


@pytest.mark.parametrize("bound", ["characters", "utf8"])
async def test_actual_unicode_total_bounds_reject_whole_set_without_truncate(material_pair, bound):
    p = material_pair
    texts = ("中😀" * 4000, "中😀" * 4000) if bound == "utf8" else ("x" * 9000, "y" * 9000)
    materials = await exported_pair(p, texts)
    reader, _ = registered_reader(p, materials)
    limits = (
        FileMaterialSetLimits(max_utf8_bytes=50000) if bound == "utf8" else FileMaterialSetLimits()
    )
    with pytest.raises(DomainError) as exc:
        await FileMaterialSetAdapter(reader, limits=limits).read(
            tuple(m.material_ref for m in materials), p.ctx
        )
    assert exc.value.status_code == 413
    assert tuple(m.text for m in materials) == texts
    assert all(x.bridge.opens == 1 for x in p.pipelines)


async def test_lost_set_reply_replay_and_concurrent_reads_do_not_settle_or_open(material_pair):
    p = material_pair
    materials = await exported_pair(p)
    reader, _ = registered_reader(p, materials)
    adapter = FileMaterialSetAdapter(reader)
    refs = tuple(m.material_ref for m in materials)

    async def lost():
        await adapter.read(refs, p.ctx)
        raise TimeoutError("Controlled consumer reply loss after actual original reads")

    before = await p.pipelines[0].case.budget.get_ledger(p.ctx)
    with pytest.raises(TimeoutError):
        await lost()
    fresh, recovered = registered_reader(p, materials, restart=True)
    again = FileMaterialSetAdapter(fresh)
    values = await asyncio.gather(again.read(refs, p.ctx), again.read(refs, p.ctx))
    assert values[0] == values[1] and values[0].materials == materials
    assert await p.pipelines[0].case.budget.get_ledger(p.ctx) == before
    assert all(x.bridge.calls == x.bridge.opens == 0 for x in recovered)


async def test_data_denied_original_fee_cleanup_does_not_gain_collection(material_pair):
    p = material_pair
    materials = await exported_pair(p)
    p.pipelines[0].bridge.data_authority.allowed = False
    await cancel(p.pipelines[0].case)
    # Cancellation legitimately changes revision/cancel_requested; fee replay must
    # preserve the actual post-cancel financial state, not a pre-cancel snapshot.
    before = await p.pipelines[0].case.budget.get_ledger(p.ctx)
    reader, recovered = registered_reader(p, materials, restart=True)
    with pytest.raises(DomainError):
        await FileMaterialSetAdapter(reader).read(tuple(m.material_ref for m in materials), p.ctx)
    first = recovered[0]

    async def forbidden(*args):
        pytest.fail("Fee recovery must not request current material/journal data")

    first.bridge.recover = forbidden
    receipt = await recover_file_accounting(first.case.ledger, first.budget, p.ctx)
    assert receipt["usage_refs"]
    assert await first.budget.get_ledger(p.ctx) == before
    assert before["billing_pending"] and before["held"]["money"] == "0.10"
    assert all(x.bridge.calls == x.bridge.opens == 0 for x in recovered)


async def test_cancel_current_wait_propagates_no_partial_set_and_no_reader_task(material_pair):
    p = material_pair
    materials = await exported_pair(p)
    reader, _ = registered_reader(p, materials)
    waiting = asyncio.Event()

    async def blocked(ref, ctx):
        if ref == materials[1].material_ref:
            waiting.set()
            await asyncio.Event().wait()

    reader.before = blocked
    task = asyncio.create_task(
        FileMaterialSetAdapter(reader).read(tuple(m.material_ref for m in materials), p.ctx)
    )
    await asyncio.wait_for(waiting.wait(), 90)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert all(x.bridge.opens == 1 for x in p.pipelines)


async def test_missing_owning_port_even_with_original_materials_is_unavailable(material_pair):
    p = material_pair
    materials = await exported_pair(p)
    with pytest.raises(DomainError) as exc:
        await FileMaterialSetAdapter(None).read(tuple(m.material_ref for m in materials), p.ctx)
    assert exc.value.status_code == 503


async def test_fresh_process_restores_two_original_material_refs_without_open(material_pair):
    p = material_pair
    materials = await exported_pair(p, ("first原\r\n", "second😀\n"))
    entries = []
    for pipe, material in zip(reversed(p.pipelines), reversed(materials), strict=True):
        (pipe.root / "file.txt").unlink()
        entries.append(
            {
                "context": pipe.case.ctx.wire(),
                "material_ref": material.material_ref.wire(),
                "blob_directory": str(pipe.blob.directory),
                "public_keys": {
                    "control": list(pipe.signatures.control.public_key().public_bytes_raw()),
                    "device": list(pipe.signatures.device.public_key().public_bytes_raw()),
                },
            }
        )
    await cancel(p.pipelines[0].case)
    completed = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-m", "tests.integration.tool.file_material_set_recovery_child"],
        input=json.dumps({"entries": entries, "current_context": p.ctx.wire()}),
        text=True,
        capture_output=True,
        timeout=180,
        cwd=Path(__file__).parents[3],
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    actual = json.loads(completed.stdout)
    assert actual == {
        "contents": [m.content for m in reversed(materials)],
        "refs": [m.material_ref.wire() for m in reversed(materials)],
        "usages": [m.usage for m in reversed(materials)],
        "sends": 0,
        "opens": 0,
    }
    assert all(x.bridge.opens == 1 for x in p.pipelines)
