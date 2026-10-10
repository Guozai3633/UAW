"""Actual new-process material recovery; independent current data/keys controlled."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.integration.tool.file_pipeline_fixture import approve_file, recover_file
from tests.integration.tool.file_pipeline_fixture import file_pipeline as file_pipeline
from tests.integration.tool.test_durable import cancel
from uaw.shared.errors import DomainError
from uaw.tool.providers.file_material import FileMaterialAdapter
from uaw.tool.providers.file_store import recover_file_accounting


async def test_new_process_material_ref_original_body_after_delete_cancel_without_open(
    file_pipeline,
):
    p = await approve_file(file_pipeline)
    assert (await p.facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    material = await FileMaterialAdapter(p.source).export(p.case.call["action_id"], p.case.ctx)
    p.path = p.root / "file.txt"
    p.path.unlink()
    await cancel(p.case)
    data = json.dumps(
        {
            "context": p.case.ctx.wire(),
            "material_ref": material.material_ref.wire(),
            "blob_directory": str(p.blob.directory),
            "public_keys": {
                "control": list(p.signatures.control.public_key().public_bytes_raw()),
                "device": list(p.signatures.device.public_key().public_bytes_raw()),
            },
        }
    )
    completed = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-m", "tests.integration.tool.file_recovery_child"],
        input=data,
        text=True,
        capture_output=True,
        timeout=180,
        cwd=Path(__file__).parents[3],
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    actual = json.loads(completed.stdout)
    assert actual == {
        "kind": "material",
        "content": material.content,
        "material_ref": material.material_ref.wire(),
        "observation_ref": material.observation_ref.wire(),
        "usage": material.usage,
        "sends": 0,
        "opens": 0,
    }
    assert p.bridge.calls == p.bridge.opens == 1


async def test_data_revocation_does_not_prevent_original_fee_plan_replay(file_pipeline):
    p = await approve_file(file_pipeline)
    settle = p.case.budget.budgets.settle

    async def lost(*args, **kwargs):
        await settle(*args, **kwargs)
        raise TimeoutError("Controlled actual fee acknowledgement loss")

    p.case.budget.budgets.settle = lost
    failed = await p.facade.invoke(p.raw, p.case.ctx)
    assert failed["failure"]["code"] == "reconciliation_interrupted"
    # Material extraction reads actual original source even when fee reply unknown,
    # and must not call settlement, declare Task success or invent money=0.
    material = await FileMaterialAdapter(p.source).export(p.case.call["action_id"], p.case.ctx)
    assert material.usage["billing_state"] == "pending"
    await cancel(p.case)
    before = await p.case.budget.get_ledger(p.case.ctx)
    p.bridge.allowed = False
    p.signatures.revoked = True
    fresh = recover_file(p)
    with pytest.raises(DomainError):
        await FileMaterialAdapter(fresh.source).read(material.material_ref, p.case.ctx)

    async def forbidden(*args):
        pytest.fail("Original fee cleanup cannot call current file data/journal Reader")

    fresh.bridge.recover = forbidden
    settlement = await recover_file_accounting(fresh.case.ledger, fresh.budget, p.case.ctx)
    assert settlement["usage_refs"] and await fresh.budget.get_ledger(p.case.ctx) == before
    assert before["billing_pending"] and before["held"]["money"] == "0.05"
    assert fresh.bridge.calls == fresh.bridge.opens == 0


@pytest.mark.parametrize("part", ["material", "observation", "owner", "usage"])
async def test_material_sql_metadata_tamper_refuses_and_does_not_heal_source(file_pipeline, part):
    p = await approve_file(file_pipeline)
    assert (await p.facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    material = await FileMaterialAdapter(p.source).export(p.case.call["action_id"], p.case.ctx)
    names = {
        "material": "refs",
        "observation": "observations",
        "owner": "owners",
        "usage": "usages",
    }
    namespace = "tool.file.material." + names[part]
    row = await p.case.ledger.store.get(p.case.ctx.principal, namespace, p.case.ctx.attempt_id)
    payload = dict(row.payload)
    if part in {"material", "observation"}:
        payload["content_hash"] = "0" * 64
    elif part == "owner":
        payload["auth_session_id"] = "foreign-session"
    else:
        payload["resources"] = {**payload["resources"], "wall_time_ms": 999}
    await p.case.ledger.store.put(
        p.case.ctx.principal,
        namespace,
        p.case.ctx.attempt_id,
        row.schema_name,
        payload,
        expected_revision=row.revision,
        request_id="controlled-material-tamper-" + part,
    )
    fresh = recover_file(p)
    with pytest.raises(DomainError):
        await FileMaterialAdapter(fresh.source).read(material.material_ref, p.case.ctx)
    after = await fresh.case.ledger.store.get(
        p.case.ctx.principal, namespace, p.case.ctx.attempt_id
    )
    assert after.payload == payload and after.revision == row.revision + 1
    assert fresh.bridge.calls == fresh.bridge.opens == 0 and p.bridge.opens == 1
