"""Actual SQL/blob/text pipeline and controlled injected failures/current authority."""

import asyncio
from copy import deepcopy

import pytest

from tests.integration.test_control_plane import meta
from tests.integration.tool.test_durable import cancel
from tests.integration.tool.text_pipeline_fixture import (
    approved_pipeline,
    recover_pipeline,
)
from tests.integration.tool.text_pipeline_fixture import (
    text_pipeline as text_pipeline,
)
from uaw.infrastructure.db.transactions import reference
from uaw.shared.contracts import Principal
from uaw.shared.errors import DomainError
from uaw.tool.providers.text import inspect_text


async def test_actual_text_complete_chain_restart_lookup_outcome_and_result(text_pipeline):
    p = await approved_pipeline(text_pipeline)
    first = await p.facade.invoke(p.raw, p.case.ctx)
    assert first["kind"] == "ok" and first["payload"]["data"] == inspect_text(
        p.raw["arguments"]["text"]
    )
    restored = recover_pipeline(p)
    again = await restored.facade.invoke(p.raw, p.case.ctx)
    assert again == first and p.executor.calls == 1
    ref = await restored.source.find(p.case.call["action_id"], p.case.ctx)
    actual = await restored.source.read(ref, p.case.ctx)
    assert actual["outcome"] == "applied" and actual["provider_ref"] == p.case.spec["provider_ref"]
    assert (await restored.facade.read_outcome(p.case.call["action_id"], p.case.ctx)) == actual
    assert await restored.results.read_result(p.case.call["action_id"], p.case.ctx) == first
    budget = await restored.budget.get_ledger(p.case.ctx)
    assert budget["used"]["tool_calls"] == 1 and budget["used"]["money"] == "0.00"
    assert budget["held"]["tool_calls"] == 0 and budget["billing_pending"] is False


@pytest.mark.parametrize(
    "missing", ["executor", "results", "prepare", "access", "approvals", "recovery", "verifier"]
)
async def test_text_missing_dependency_refused_before_reservation(text_pipeline, missing):
    p = text_pipeline
    if missing in {"executor", "results", "prepare", "access", "approvals"}:
        setattr(p.invocation, missing, None)
    elif missing == "recovery":
        p.source.access = None
    else:
        p.source.verifier = None
    denied = await p.facade.invoke(p.raw, p.case.ctx)
    assert denied["failure"]["code"] == "dependency_unavailable" and p.executor.calls == 0
    assert (
        await p.case.ledger.get("tool.budget.reserved", p.case.ctx.attempt_id, p.case.ctx) is None
    )


async def test_text_denied_approval_never_reserves_or_executes(text_pipeline):
    p = text_pipeline
    waiting = await p.facade.invoke(p.raw, p.case.ctx)
    approval = await p.case.service.get(p.case.ctx.principal, waiting["wait_ref"]["id"])
    await p.case.service.decide(
        p.case.ctx.principal,
        {
            "approval_id": approval["id"],
            "decision": {
                "decision": "decline",
                "expected_arguments_hash": approval["arguments_hash"],
                "expected_resource_refs": approval["resource_refs"],
                "reason": "Controlled explicit denial",
            },
        },
        meta("text-deny", approval["revision"]),
    )
    denied = await p.facade.invoke(p.raw, p.case.ctx)
    assert denied["kind"] == "denied" and p.executor.calls == 0
    assert (
        await p.case.ledger.get("tool.budget.reserved", p.case.ctx.attempt_id, p.case.ctx) is None
    )


async def test_text_cancelled_before_send_never_reserves(text_pipeline):
    p = await approved_pipeline(text_pipeline)
    await cancel(p.case)
    denied = await p.facade.invoke(p.raw, p.case.ctx)
    assert denied["kind"] in {"denied", "cancelled"} and p.executor.calls == 0
    assert (
        await p.case.ledger.get("tool.budget.reserved", p.case.ctx.attempt_id, p.case.ctx) is None
    )


async def test_text_role_revoked_after_reserve_releases_only_unsent_reservation(text_pipeline):
    p = await approved_pipeline(text_pipeline)
    original = p.case.budget.reserve

    async def revoked(*args):
        actual = await original(*args)
        p.role.allowed = False
        return actual

    p.case.budget.reserve = revoked
    denied = await p.facade.invoke(p.raw, p.case.ctx)
    assert denied["kind"] == "denied" and p.executor.calls == 0
    effect = await p.case.ledger.effect_from_attempt(p.case.ctx)
    assert effect["attempt_ids"] == [] and effect["state"] == "pending"
    reserved = await p.case.ledger.get("tool.budget.reserved", p.case.ctx.attempt_id, p.case.ctx)
    state = await p.case.budget.get_reservation(reserved["id"], p.case.ctx)
    assert state["status"] == "released"


async def test_text_cancel_after_intent_never_turns_replay_into_send_right(text_pipeline):
    p = await approved_pipeline(text_pipeline)
    original = p.case.budget.mark_dispatch

    async def cancelled(ctx):
        owned = await original(ctx)
        await cancel(p.case)
        return owned

    p.case.budget.mark_dispatch = cancelled
    denied = await p.facade.invoke(p.raw, p.case.ctx)
    assert denied["kind"] in {"denied", "cancelled"} and p.executor.calls == 0
    assert (await p.case.ledger.effect_from_attempt(p.case.ctx))["state"] == "unknown"
    restored = recover_pipeline(p)
    again = await restored.facade.invoke(p.raw, p.case.ctx)
    assert again["failure"]["code"] == "unknown_effect" and p.executor.calls == 0
    assert (await restored.budget.get_ledger(p.case.ctx))["held"]["tool_calls"] == 1


@pytest.mark.parametrize("saved", [False, True])
async def test_text_executor_timeout_keeps_intent_never_resends_and_restores_only_actual_saved_data(
    text_pipeline, saved
):
    p = await approved_pipeline(text_pipeline)
    original = p.executor.execute
    calls = 0

    async def lost(*args):
        nonlocal calls
        calls += 1
        if saved:
            await original(*args)
        raise TimeoutError("Controlled executor response loss")

    p.executor.execute = lost
    interrupted = await p.facade.invoke(p.raw, p.case.ctx)
    assert interrupted["failure"]["code"] == "invocation_interrupted"
    assert (await p.case.ledger.effect_from_attempt(p.case.ctx))["state"] == "unknown"
    restored = recover_pipeline(p)
    result = await restored.facade.invoke(p.raw, p.case.ctx)
    if saved:
        assert result["kind"] == "ok" and result["payload"]["data"] == inspect_text(
            p.raw["arguments"]["text"]
        )
    else:
        assert result["failure"]["code"] == "unknown_effect"
        state = await restored.budget.get_ledger(p.case.ctx)
        assert state["held"]["tool_calls"] == 1 and state["billing_pending"] is True
    assert calls == 1
    new_ctx = p.case.ctx.model_copy(
        update={"attempt_id": "forbidden-retry", "trace_id": "retry-trace"}
    )
    denied = await p.facade.invoke(p.raw, new_ctx)
    assert denied["failure"]["code"] == "unknown_effect" and calls == 1
    assert await p.case.ledger.get("tool.attempt.contexts", "forbidden-retry", p.case.ctx) is None


@pytest.mark.parametrize("saved", [False, True])
async def test_text_async_cancel_after_send_retains_truth_and_original_attempt(
    text_pipeline, saved
):
    p = await approved_pipeline(text_pipeline)
    original = p.executor.execute

    async def cancelled(*args):
        if saved:
            await original(*args)
        raise asyncio.CancelledError()

    p.executor.execute = cancelled
    with pytest.raises(asyncio.CancelledError):
        await p.facade.invoke(p.raw, p.case.ctx)
    assert (await p.case.ledger.effect_from_attempt(p.case.ctx))["state"] == "unknown"
    restored = recover_pipeline(p)
    result = await restored.facade.invoke(p.raw, p.case.ctx)
    assert result["kind"] == "ok" if saved else result["failure"]["code"] == "unknown_effect"
    assert p.executor.calls == (1 if saved else 0)


@pytest.mark.parametrize("output", ["schema", "semantics"])
async def test_text_saved_bad_output_is_not_success_even_with_confirmed_provider_receipt(
    text_pipeline, output
):
    p = await approved_pipeline(text_pipeline)
    original = p.source.save_response

    async def corrupted(data, *args, **kwargs):
        changed = (
            {**data, "extra": "not in schema"}
            if output == "schema"
            else {**data, "sha256": "0" * 64}
        )
        return await original(changed, *args, **kwargs)

    p.source.save_response = corrupted
    result = await p.facade.invoke(p.raw, p.case.ctx)
    assert result["failure"]["code"] == "tool_output_invalid" and p.executor.calls == 1
    assert (await p.case.ledger.effect_from_attempt(p.case.ctx))["state"] == "unknown"
    assert await p.source.find(p.case.call["action_id"], p.case.ctx) is None
    assert await p.case.ledger.get("tool.results", p.case.ctx.attempt_id, p.case.ctx) is None
    assert (await p.case.budget.get_ledger(p.case.ctx))["held"]["tool_calls"] == 1


async def test_text_provider_return_wrong_receipt_cannot_replace_actual_saved_source(text_pipeline):
    p = await approved_pipeline(text_pipeline)
    original = p.executor.execute

    async def wrong(*args):
        actual = await original(*args)
        return {**actual, "raw_result_ref": reference("content", "wrong-saved-response")}

    p.executor.execute = wrong
    rejected = await p.facade.invoke(p.raw, p.case.ctx)
    assert rejected["failure"]["code"] == "receipt_binding_conflict"
    assert (await p.case.ledger.effect_from_attempt(p.case.ctx))["state"] == "unknown"


async def test_text_fee_response_lost_after_real_commit_recovers_same_plan(text_pipeline):
    p = await approved_pipeline(text_pipeline)
    actual = p.case.budget.budgets
    original = actual.settle

    async def lost(*args, **kwargs):
        await original(*args, **kwargs)
        raise TimeoutError("Controlled fee response loss after actual SQL commit")

    actual.settle = lost
    first = await p.facade.invoke(p.raw, p.case.ctx)
    assert first["failure"]["code"] == "reconciliation_interrupted" and p.executor.calls == 1
    assert (await p.facade.read_outcome(p.case.call["action_id"], p.case.ctx))[
        "outcome"
    ] == "applied"
    before = await p.case.budget.get_ledger(p.case.ctx)
    result = await recover_pipeline(p).facade.invoke(p.raw, p.case.ctx)
    assert result["kind"] == "ok" and p.executor.calls == 1
    assert await p.case.budget.get_ledger(p.case.ctx) == before


async def test_text_publish_response_loss_recovers_original_fixed_receipt(text_pipeline):
    p = await approved_pipeline(text_pipeline)
    original = p.source.publish

    async def lost(*args, **kwargs):
        await original(*args, **kwargs)
        raise TimeoutError("Controlled publish response loss after real source commit")

    p.source.publish = lost
    first = await p.facade.invoke(p.raw, p.case.ctx)
    assert first["failure"]["code"] == "invocation_interrupted"
    ref = await p.source.find(p.case.call["action_id"], p.case.ctx)
    assert ref is not None and p.executor.calls == 1
    assert (await recover_pipeline(p).facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    assert (
        await p.source.find(p.case.call["action_id"], p.case.ctx) == ref and p.executor.calls == 1
    )


async def test_text_current_recovery_revocation_blocks_old_result_and_reconcile(text_pipeline):
    p = await approved_pipeline(text_pipeline)
    assert (await p.facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    before = await p.case.budget.get_ledger(p.case.ctx)
    p.recovery.allowed = False
    with pytest.raises(DomainError) as error:
        await p.results.read_result(p.case.call["action_id"], p.case.ctx)
    assert error.value.status_code == 403
    with pytest.raises(DomainError):
        await p.facade.read_outcome(p.case.call["action_id"], p.case.ctx)
    refused = await p.facade.invoke(p.raw, p.case.ctx)
    assert refused["kind"] == "denied" and p.executor.calls == 1
    assert await p.case.budget.get_ledger(p.case.ctx) == before


async def test_text_cancel_and_execution_role_revoke_allows_actual_recovery_data(text_pipeline):
    p = await approved_pipeline(text_pipeline)
    first = await p.facade.invoke(p.raw, p.case.ctx)
    assert first["kind"] == "ok"
    await cancel(p.case)
    p.role.allowed = False
    restored = recover_pipeline(p)
    assert await restored.facade.invoke(p.raw, p.case.ctx) == first
    assert await restored.results.read_result(p.case.call["action_id"], p.case.ctx) == first
    assert p.executor.calls == 1


async def test_text_publish_uses_full_authenticated_provider_and_fixed_version(text_pipeline):
    p = await approved_pipeline(text_pipeline)
    assert (await p.facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    actual = await p.source.provider_receipt(p.case.ctx)
    for foreign in (
        p.provider.model_copy(update={"auth_session_id": "foreign-session"}),
        Principal(id="foreign-service", kind="service", auth_session_id="foreign-session"),
    ):
        with pytest.raises(DomainError) as error:
            await p.source.publish(actual, p.case.ctx, authenticated_provider=foreign)
        assert error.value.status_code == 403
    bad = {**actual, "usage": {**actual["usage"], "attempt_id": "foreign-attempt"}}
    with pytest.raises(DomainError):
        await p.source.publish(bad, p.case.ctx, authenticated_provider=p.provider)
    ref = await p.source.find(p.case.call["action_id"], p.case.ctx)
    assert ref == await p.source.publish(actual, p.case.ctx, authenticated_provider=p.provider)
    with pytest.raises(DomainError):
        await p.source.read(ref.model_copy(update={"version": "2"}), p.case.ctx)


async def test_text_accepted_result_tamper_does_not_get_returned_as_success(text_pipeline):
    p = await approved_pipeline(text_pipeline)
    assert (await p.facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    row = await p.case.ledger.store.get(p.case.ctx.principal, "tool.results", p.case.ctx.attempt_id)
    changed = deepcopy(row.payload)
    changed["data"]["characters"] += 1
    await p.case.ledger.store.put(
        p.case.ctx.principal,
        "tool.results",
        p.case.ctx.attempt_id,
        "ToolResult",
        changed,
        expected_revision=row.revision,
        request_id="controlled-result-tamper",
    )
    with pytest.raises(DomainError) as error:
        await p.results.read_result(p.case.call["action_id"], p.case.ctx)
    assert error.value.failure.code == "receipt_binding_conflict" and p.executor.calls == 1


async def test_text_conflicting_request_cannot_release_original_unsent_hold(text_pipeline):
    p = await approved_pipeline(text_pipeline)
    original = await p.case.budget.reserve(p.invocation.estimates, p.case.ctx)
    changed = deepcopy(p.raw)
    changed["arguments"]["text"] += " changed input"
    denied = await p.facade.invoke(changed, p.case.ctx)
    assert denied["failure"]["code"] == "action_conflict" and p.executor.calls == 0
    state = await p.case.budget.get_reservation(original["id"], p.case.ctx)
    assert state["status"] == "reserved"
    assert (
        await p.case.ledger.get("tool.budget.release.refs", p.case.ctx.attempt_id, p.case.ctx)
        is None
    )
    legitimate = await p.facade.invoke(p.raw, p.case.ctx)
    assert legitimate["kind"] == "ok" and p.executor.calls == 1
