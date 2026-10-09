"""Actual new-process office recovery and no-response/missing source boundaries."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.integration.tool.office_pipeline_fixture import (
    approve_office,
    recover_office,
)
from tests.integration.tool.office_pipeline_fixture import (
    office_pipeline as office_pipeline,
)
from tests.integration.tool.test_office_tools_postgres import expected
from uaw.shared.errors import DomainError


async def test_office_actual_new_process_recovers_saved_response_without_executor(office_pipeline):
    p = await approve_office(office_pipeline)
    original = p.executor.execute

    async def lost(*args):
        await original(*args)
        raise TimeoutError("Controlled reply loss after real output was durable")

    p.executor.execute = lost
    result = await p.facade.invoke(p.raw, p.case.ctx)
    assert result["failure"]["code"] == "invocation_interrupted" and p.executor.calls == 1
    before = await p.case.budget.get_ledger(p.case.ctx)
    payload = json.dumps(
        {"context": p.case.ctx.wire(), "request": p.raw, "blob_directory": str(p.blob.directory)}
    )
    completed = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-m", "tests.integration.tool.office_recovery_child"],
        input=payload,
        text=True,
        capture_output=True,
        timeout=90,
        cwd=Path(__file__).parents[3],
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    actual = json.loads(completed.stdout)
    assert actual == {"kind": "ok", "outcome": "applied", "failure_code": None, "data": expected(p)}
    after = await p.case.budget.get_ledger(p.case.ctx)
    assert before["held"]["tool_calls"] == 1 and after["held"]["tool_calls"] == 0
    assert after["used"]["tool_calls"] == 1 and p.executor.calls == 1


async def test_office_no_saved_response_keeps_unknown_hold_no_new_attempt(office_pipeline):
    p = await approve_office(office_pipeline)
    entered = 0

    async def absent(*args):
        nonlocal entered
        entered += 1
        raise TimeoutError("Controlled unknown send with no actual saved output")

    p.executor.execute = absent
    assert (await p.facade.invoke(p.raw, p.case.ctx))["failure"]["code"] == "invocation_interrupted"
    fresh = recover_office(p)
    result = await fresh.facade.invoke(p.raw, p.case.ctx)
    assert result["failure"]["code"] == "unknown_effect" and entered == 1
    state = await fresh.budget.get_ledger(p.case.ctx)
    assert state["held"]["tool_calls"] == 1 and state["billing_pending"]
    new = p.case.ctx.model_copy(update={"attempt_id": "another-attempt", "trace_id": "new-trace"})
    assert (await p.facade.invoke(p.raw, new))["failure"]["code"] == "unknown_effect"
    assert await p.case.ledger.get("tool.attempt.contexts", new.attempt_id, p.case.ctx) is None
    assert entered == 1


async def test_office_actual_bounded_prepare_rejects_before_approval_reserve(office_pipeline):
    p = office_pipeline
    if p.kind == "arithmetic":
        args = {"operation": "divide", "operands": ["1", "0"]}
    elif p.kind == "json":
        args = {"text": '{"x":1,"x":2}'}
    else:
        args = {"text": "原" * 12000}
    result = await p.facade.invoke({**p.raw, "arguments": args}, p.case.ctx)
    assert result["failure"]["code"] == "invalid_arguments" and p.executor.calls == 0
    assert (
        await p.case.ledger.get("tool.budget.reserved", p.case.ctx.attempt_id, p.case.ctx) is None
    )


async def test_office_resource_reader_missing_is_not_an_empty_resource_grant(office_pipeline):
    p = office_pipeline
    p.case.authority.resources = None
    result = await p.facade.invoke(p.raw, p.case.ctx)
    assert result["failure"]["code"] == "dependency_unavailable" and p.executor.calls == 0
    assert (
        await p.case.ledger.get("tool.budget.reserved", p.case.ctx.attempt_id, p.case.ctx) is None
    )


async def test_office_foreign_principal_session_attempt_and_provider_cannot_read(office_pipeline):
    p = await approve_office(office_pipeline)
    assert (await p.facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    pin = await p.source.find(p.case.call["action_id"], p.case.ctx)
    for context in (
        p.case.ctx.model_copy(update={"attempt_id": "foreign-attempt"}),
        p.case.ctx.model_copy(
            update={
                "principal": p.case.ctx.principal.model_copy(
                    update={"auth_session_id": "foreign-session"}
                )
            }
        ),
    ):
        with pytest.raises(DomainError):
            await recover_office(p).source.read(pin, context)
    actual = await p.source.provider_receipt(p.case.ctx)
    with pytest.raises(DomainError):
        await p.source.publish(
            actual,
            p.case.ctx,
            authenticated_provider=p.provider.model_copy(
                update={"auth_session_id": "wrong-provider-session"}
            ),
        )
    assert p.executor.calls == 1
