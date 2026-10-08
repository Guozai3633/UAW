"""Genuine approvals/budget, actual local text computation and normalized results."""

import asyncio

from tests.integration.tool.conftest import approve
from tests.integration.tool.text_pipeline_fixture import text_pipeline as text_pipeline
from uaw.shared.contracts import Ref
from uaw.shared.schema import validate_contract
from uaw.tool.providers.text import inspect_text


async def test_text_stage_approved_once_send_actual_response_durable(text_pipeline):
    p = text_pipeline
    c = p.case
    waiting = await p.facade.invoke(p.raw, c.ctx)
    assert waiting["kind"] == "waiting" and p.executor.calls == 0
    assert await c.ledger.get("tool.budget.reserved", c.ctx.attempt_id, c.ctx) is None
    await approve(c)
    stage = await p.facade.invoke(p.raw, c.ctx)
    assert stage["kind"] == "ok" and stage["payload"]["status"] == "succeeded"
    actual = await p.source.provider_receipt(c.ctx)
    validate_contract("ProviderReceipt", actual)
    output = await p.source.read_raw(Ref.model_validate(actual["raw_result_ref"]), c.ctx)
    assert output == inspect_text(p.raw["arguments"]["text"])
    assert (
        p.executor.calls == 1
        and (await c.ledger.effect_from_attempt(c.ctx))["state"] == "confirmed"
    )
    await p.facade.invoke(p.raw, c.ctx)
    assert p.executor.calls == 1


async def test_text_stage_concurrent_invocation_has_one_send_owner(text_pipeline):
    p = text_pipeline
    await p.facade.invoke(p.raw, p.case.ctx)
    await approve(p.case)
    # This bounds a stuck SQL race, not product latency. The result recovery
    # includes current authorization reads and can exceed 20s under suite load.
    # Execution still obeys the actual Run/attempt deadlines inside the facade.
    results = await asyncio.wait_for(
        asyncio.gather(*(p.facade.invoke(p.raw, p.case.ctx) for _ in range(3))), 60
    )
    assert len(results) == 3 and p.executor.calls == 1
    assert any(r["kind"] == "ok" for r in results)
    assert all(
        r["kind"] == "ok" or r["failure"]["code"] in {"unknown_effect", "reconciliation_pending"}
        for r in results
    )
    assert await p.source.provider_receipt(p.case.ctx) is not None


async def test_text_stage_missing_executor_or_invalid_bytes_never_reserves(text_pipeline):
    p = text_pipeline
    p.invocation.executor = None
    result = await p.facade.invoke(p.raw, p.case.ctx)
    assert result["failure"]["code"] == "dependency_unavailable"
    assert (
        await p.case.ledger.get("tool.budget.reserved", p.case.ctx.attempt_id, p.case.ctx) is None
    )
    p.invocation.executor = p.executor
    invalid = {**p.raw, "arguments": {"text": "原" * 12000}}
    result = await p.facade.invoke(invalid, p.case.ctx)
    assert result["failure"]["code"] == "invalid_arguments" and p.executor.calls == 0
    assert (
        await p.case.ledger.get("tool.budget.reserved", p.case.ctx.attempt_id, p.case.ctx) is None
    )
