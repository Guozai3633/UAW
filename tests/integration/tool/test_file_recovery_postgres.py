"""Real child process/file SQL boundaries; all control/native authority explicit tests."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.integration.tool.file_pipeline_fixture import approve_file
from tests.integration.tool.file_pipeline_fixture import file_pipeline as file_pipeline
from tests.integration.tool.test_durable import cancel


async def test_actual_fresh_process_restores_original_independent_journal_no_executor(
    file_pipeline,
):
    p = await approve_file(file_pipeline)
    original_text = (p.root / "file.txt").read_bytes().decode("utf-8")

    async def lost():
        raise TimeoutError("Controlled reply loss after real SQL journal saved")

    p.bridge.after_journal = lost
    first = await p.facade.invoke(p.raw, p.case.ctx)
    assert first["failure"]["code"] == "invocation_interrupted"
    (p.root / "file.txt").unlink()
    await cancel(p.case)
    payload = json.dumps(
        {
            "context": p.case.ctx.wire(),
            "request": p.raw,
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
        input=payload,
        text=True,
        capture_output=True,
        timeout=180,
        cwd=Path(__file__).parents[3],
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    actual = json.loads(completed.stdout)
    assert actual["kind"] == "ok" and actual["outcome"] == "applied", actual
    assert actual["data"]["text"] == original_text and actual["sends"] == actual["opens"] == 0
    assert p.bridge.calls == p.bridge.opens == 1
    assert (await p.case.budget.get_ledger(p.case.ctx))["billing_pending"]


@pytest.mark.parametrize("content", [b"x" * 65536, b"\n" * 65536], ids=["ascii-64k", "escaped-64k"])
async def test_actual_file_64k_saved_without_generic_input_expansion(file_pipeline, content):
    p = file_pipeline
    (p.root / "file.txt").write_bytes(content)
    await approve_file(p)
    result = await p.facade.invoke(p.raw, p.case.ctx)
    assert result["kind"] == "ok", {k: v for k, v in result.items() if k != "payload"}
    assert result["payload"]["data"]["text"].encode("utf-8") == content
    saved = await p.case.ledger.get("tool.results", p.case.ctx.attempt_id, p.case.ctx)
    assert saved["data"] == result["payload"]["data"]


@pytest.mark.parametrize(
    "content", [b"x" * 65537, b"\xff", b"x\x00y"], ids=["over-64k", "bad-utf8", "binary"]
)
async def test_actual_windows_file_read_invalid_content_never_claims_success(
    file_pipeline, content
):
    p = file_pipeline
    (p.root / "file.txt").write_bytes(content)
    await approve_file(p)
    denied = await p.facade.invoke(p.raw, p.case.ctx)
    assert denied["kind"] != "ok" and p.bridge.calls == 1
    assert await p.case.ledger.get("tool.results", p.case.ctx.attempt_id, p.case.ctx) is None
    assert (await p.case.budget.get_ledger(p.case.ctx))["held"]["tool_calls"] == 1


async def test_permissions_change_during_resource_await_prevents_approval_and_dispatch(
    file_pipeline,
):
    p = file_pipeline
    resolve = p.bridge.resolve

    async def revoked(*args):
        actual = await resolve(*args)
        p.role.allowed = False
        return actual

    p.bridge.resolve = revoked
    result = await p.facade.invoke(p.raw, p.case.ctx)
    assert result["kind"] != "ok" and result["kind"] != "waiting"
    assert p.bridge.calls == p.bridge.opens == 0
    assert (
        await p.case.ledger.get("tool.budget.reserved", p.case.ctx.attempt_id, p.case.ctx) is None
    )


async def test_cancel_after_intent_does_not_make_replay_a_new_send_right(file_pipeline):
    p = await approve_file(file_pipeline)
    mark = p.case.budget.mark_dispatch

    async def cancelled(ctx):
        owned = await mark(ctx)
        await cancel(p.case)
        return owned

    p.case.budget.mark_dispatch = cancelled
    first = await p.facade.invoke(p.raw, p.case.ctx)
    assert first["kind"] != "ok" and p.bridge.calls == p.bridge.opens == 0
    second = await p.facade.invoke(p.raw, p.case.ctx)
    assert second["failure"]["code"] == "unknown_effect"
    assert p.bridge.calls == p.bridge.opens == 0


async def test_port_mutation_during_blob_await_cannot_rewrite_original_observation(file_pipeline):
    p = await approve_file(file_pipeline)
    actual = {}

    def observed(evidence):
        actual["evidence"] = evidence
        return evidence

    p.bridge.transform = observed
    put = p.blob.put
    changed = False

    async def mutating(owner, content):
        nonlocal changed
        value = await put(owner, content)
        if not changed and "evidence" in actual:
            # SQL journal gets the strict wire first; mutate only after the bridge
            # returns. The source executor/record snapshot must own independent JSON.
            journal = await p.case.ledger.get(
                "tool.test.file.receipts", p.case.ctx.attempt_id, p.case.ctx
            )
            if journal is not None:
                changed = True
                actual["evidence"].receipt.payload["result"]["text"] = "mutable port corruption"
                actual["evidence"].receipt.usage["resources"]["wall_time_ms"] = 999
        return value

    p.blob.put = mutating
    result = await p.facade.invoke(p.raw, p.case.ctx)
    assert result["kind"] == "ok", result
    assert changed and result["payload"]["data"]["text"] == (
        p.root / "file.txt"
    ).read_bytes().decode("utf-8")
    raw = await p.source.provider_receipt(p.case.ctx)
    assert raw["usage"]["resources"]["wall_time_ms"] == 1
    observation = await p.source.read_observation(p.case.call["action_id"], p.case.ctx)
    assert observation.receipt.usage["resources"]["wall_time_ms"] == 1
    assert p.bridge.calls == p.bridge.opens == 1


async def test_original_fee_plan_recovers_after_root_and_key_revoke_without_reading_file(
    file_pipeline,
):
    from tests.integration.tool.file_pipeline_fixture import recover_file
    from uaw.shared.errors import DomainError
    from uaw.tool.providers.file_store import recover_file_accounting

    p = await approve_file(file_pipeline)
    settle = p.case.budget.budgets.settle

    async def lost(*args, **kwargs):
        await settle(*args, **kwargs)
        raise TimeoutError("Controlled original file fee commit acknowledgement loss")

    p.case.budget.budgets.settle = lost
    failed = await p.facade.invoke(p.raw, p.case.ctx)
    assert failed["failure"]["code"] == "reconciliation_interrupted", failed
    await cancel(p.case)
    before = await p.case.budget.get_ledger(p.case.ctx)
    p.bridge.allowed = False
    p.signatures.revoked = True
    fresh = recover_file(p)

    async def no_body(*args):
        pytest.fail("Accounting replay must not read root/journal/file bytes")

    fresh.bridge.recover = no_body
    result = await recover_file_accounting(fresh.case.ledger, fresh.budget, p.case.ctx)
    assert result["usage_refs"] and await fresh.budget.get_ledger(p.case.ctx) == before
    assert await recover_file_accounting(fresh.case.ledger, fresh.budget, p.case.ctx) == result
    assert (await fresh.facade.invoke(p.raw, p.case.ctx))["kind"] != "ok"
    with pytest.raises(DomainError):
        await recover_file_accounting(
            fresh.case.ledger,
            fresh.budget,
            p.case.ctx.model_copy(update={"attempt_id": "foreign-file-attempt"}),
        )
    assert p.bridge.calls == p.bridge.opens == 1 and fresh.bridge.calls == fresh.bridge.opens == 0


async def test_no_original_accounting_plan_cannot_become_fee_or_send_grant(file_pipeline):
    from uaw.shared.errors import DomainError
    from uaw.tool.providers.file_store import recover_file_accounting

    p = await approve_file(file_pipeline)
    with pytest.raises(DomainError) as error:
        await recover_file_accounting(p.case.ledger, p.case.budget, p.case.ctx)
    assert error.value.failure.code == "dependency_unavailable"
    assert p.bridge.calls == p.bridge.opens == 0
    assert (
        await p.case.ledger.get("tool.budget.reserved", p.case.ctx.attempt_id, p.case.ctx) is None
    )
