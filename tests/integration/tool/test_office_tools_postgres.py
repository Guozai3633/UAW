"""Actual three-adapter SQL chain, controlled authorization and failure injection."""

import asyncio
from copy import deepcopy

import pytest

from tests.integration.tool.office_pipeline_fixture import (
    ARGUMENTS,
    KINDS,
    approve_office,
    recover_office,
)
from tests.integration.tool.office_pipeline_fixture import (
    office_pipeline as office_pipeline,
)
from tests.integration.tool.test_durable import cancel
from uaw.shared.errors import DomainError
from uaw.shared.schema import validate_contract
from uaw.tool.invocation.schema import normalize
from uaw.tool.providers.arithmetic import calculate
from uaw.tool.providers.json_data import inspect_json
from uaw.tool.providers.multiplex import ToolOutputVerifierBinding, ToolOutputVerifierRouter
from uaw.tool.providers.text import TextInspectVerifier, inspect_text


def expected(p):
    args = p.raw["arguments"]
    return (
        calculate(args)
        if p.kind == "arithmetic"
        else inspect_json(args)
        if p.kind == "json"
        else (inspect_text(args["text"]))
    )


async def test_office_approved_actual_result_fixed_receipt_fresh_objects(office_pipeline):
    p = await approve_office(office_pipeline)
    actual = await p.facade.invoke(p.raw, p.case.ctx)
    assert actual["kind"] == "ok" and actual["payload"]["data"] == expected(p)
    validate_contract("ToolResult", actual["payload"])
    provider = await p.source.provider_receipt(p.case.ctx)
    validate_contract("ProviderReceipt", provider)
    assert provider["usage"]["resources"]["money"] == "0.00"
    assert provider["usage"]["resources"]["model_calls"] == 0
    assert provider["usage"]["resources"]["tool_calls"] == 1
    fresh = recover_office(p)
    assert await fresh.facade.invoke(p.raw, p.case.ctx) == actual
    assert await fresh.results.read_result(p.case.call["action_id"], p.case.ctx) == actual
    pin = await fresh.source.find(p.case.call["action_id"], p.case.ctx)
    assert pin == await p.source.find(p.case.call["action_id"], p.case.ctx)
    outcome = await fresh.facade.read_outcome(p.case.call["action_id"], p.case.ctx)
    assert outcome["outcome"] == "applied" and outcome["attempt_id"] == p.case.ctx.attempt_id
    assert (
        p.executor.calls == 1
        and (await fresh.budget.get_ledger(p.case.ctx))["held"]["tool_calls"] == 0
    )


async def test_office_concurrent_original_attempt_has_one_dispatch_owner(office_pipeline):
    p = await approve_office(office_pipeline)
    result = await asyncio.wait_for(
        asyncio.gather(*(p.facade.invoke(p.raw, p.case.ctx) for _ in range(3))), 90
    )
    assert p.executor.calls == 1 and any(row["kind"] == "ok" for row in result)
    assert all(
        row["kind"] == "ok"
        or row["failure"]["code"] in {"unknown_effect", "reconciliation_pending"}
        for row in result
    )
    assert (await recover_office(p).facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"


async def test_office_parameters_changed_during_approval_do_not_reserve(office_pipeline):
    p = await approve_office(office_pipeline)
    changed = deepcopy(p.raw)
    if p.kind == "arithmetic":
        changed["arguments"]["operands"][0] = "1"
    else:
        changed["arguments"]["text"] += " "
    refused = await p.facade.invoke(changed, p.case.ctx)
    assert refused["failure"]["code"] == "action_conflict" and p.executor.calls == 0
    assert (
        await p.case.ledger.get("tool.budget.reserved", p.case.ctx.attempt_id, p.case.ctx) is None
    )


async def test_office_cancel_after_intent_unknown_is_not_retry_permission(office_pipeline):
    p = await approve_office(office_pipeline)
    original = p.case.budget.mark_dispatch

    async def cancelled(ctx):
        owner = await original(ctx)
        await cancel(p.case)
        return owner

    p.case.budget.mark_dispatch = cancelled
    result = await p.facade.invoke(p.raw, p.case.ctx)
    assert result["kind"] in {"denied", "cancelled"} and p.executor.calls == 0
    fresh = recover_office(p)
    result = await fresh.facade.invoke(p.raw, p.case.ctx)
    assert result["failure"]["code"] == "unknown_effect"
    assert (await fresh.budget.get_ledger(p.case.ctx))["held"]["tool_calls"] == 1
    new = p.case.ctx.model_copy(update={"attempt_id": "forbidden-new", "trace_id": "forbidden"})
    assert (await p.facade.invoke(p.raw, new))["failure"]["code"] == "unknown_effect"
    assert await p.case.ledger.get("tool.attempt.contexts", new.attempt_id, p.case.ctx) is None


async def test_office_saved_response_loss_cancel_recovers_without_execute_access(office_pipeline):
    p = await approve_office(office_pipeline)
    original = p.executor.execute

    async def lost(*args):
        await original(*args)
        raise TimeoutError("Controlled loss after real SQL/blob response save")

    p.executor.execute = lost
    assert (await p.facade.invoke(p.raw, p.case.ctx))["failure"]["code"] == "invocation_interrupted"
    await cancel(p.case)
    p.role.allowed = False
    fresh = recover_office(p)
    result = await fresh.facade.invoke(p.raw, p.case.ctx)
    assert result["kind"] == "ok" and result["payload"]["data"] == expected(p)
    assert p.executor.calls == 1


async def test_office_current_data_revocation_blocks_saved_outcome(office_pipeline):
    p = await approve_office(office_pipeline)
    assert (await p.facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    before = await p.case.budget.get_ledger(p.case.ctx)
    p.current_data.allowed = False
    with pytest.raises(DomainError):
        await recover_office(p).results.read_result(p.case.call["action_id"], p.case.ctx)
    with pytest.raises(DomainError):
        await recover_office(p).facade.read_outcome(p.case.call["action_id"], p.case.ctx)
    assert p.executor.calls == 1 and await p.case.budget.get_ledger(p.case.ctx) == before


async def test_office_missing_production_dependencies_fail_before_reserve(office_pipeline):
    p = office_pipeline
    for missing in ("executor", "access"):
        old = getattr(p.invocation, missing)
        setattr(p.invocation, missing, None)
        result = await p.facade.invoke(p.raw, p.case.ctx)
        assert result["failure"]["code"] == "dependency_unavailable"
        setattr(p.invocation, missing, old)
    p.recovery.authority = None
    result = await p.facade.invoke(p.raw, p.case.ctx)
    assert result["failure"]["code"] == "dependency_unavailable" and p.executor.calls == 0
    assert (
        await p.case.ledger.get("tool.budget.reserved", p.case.ctx.attempt_id, p.case.ctx) is None
    )


async def test_office_fee_commit_reply_loss_original_plan_and_effect_independent(office_pipeline):
    p = await approve_office(office_pipeline)
    original = p.case.budget.budgets.settle

    async def lost(*args, **kwargs):
        await original(*args, **kwargs)
        raise TimeoutError("Controlled accounting reply loss after SQL commit")

    p.case.budget.budgets.settle = lost
    failed = await p.facade.invoke(p.raw, p.case.ctx)
    assert failed["failure"]["code"] == "reconciliation_interrupted"
    assert (await p.facade.read_outcome(p.case.call["action_id"], p.case.ctx))[
        "outcome"
    ] == "applied"
    before = await p.case.budget.get_ledger(p.case.ctx)
    fresh = recover_office(p)
    assert (await fresh.facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    assert await fresh.budget.get_ledger(p.case.ctx) == before and p.executor.calls == 1


async def test_office_persisted_output_tamper_is_not_verifier_success(office_pipeline):
    p = await approve_office(office_pipeline)
    save = p.source.save_response

    async def corrupted(data, *args, **kwargs):
        data = (
            {**data, "value": "42"}
            if p.kind == "arithmetic"
            else ({**data, "nodes": 999} if p.kind == "json" else {**data, "characters": 999})
        )
        return await save(data, *args, **kwargs)

    p.source.save_response = corrupted
    failed = await p.facade.invoke(p.raw, p.case.ctx)
    assert failed["failure"]["code"] == "tool_output_invalid"
    assert (
        p.executor.calls == 1 and await p.source.find(p.case.call["action_id"], p.case.ctx) is None
    )
    assert (await p.case.budget.get_ledger(p.case.ctx))["held"]["tool_calls"] == 1


async def test_office_recovery_cannot_substitute_other_tool_verifier(office_pipeline):
    p = await approve_office(office_pipeline)
    assert (await p.facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    wrong = ToolOutputVerifierRouter(
        (
            ToolOutputVerifierBinding(
                p.pins[2], p.source.provider_ref, TextInspectVerifier(p.source.provider_ref)
            ),
        )
    )
    fresh = recover_office(p, verifier=wrong)
    if p.kind == "text":
        assert (await fresh.facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    else:
        failed = await fresh.facade.invoke(p.raw, p.case.ctx)
        assert failed["failure"]["code"] == "executor_binding_conflict"
    assert p.executor.calls == 1


async def test_office_mixed_registry_discovery_and_foreign_provider_ref(office_pipeline):
    p = office_pipeline
    discovered = await p.facade.discover({"query": "inspect", "max_candidates": 8}, p.case.ctx)
    # This facade's discovery access is separately injected, never inferred from invocation.
    assert discovered["failure"]["code"] == "dependency_unavailable"
    p.facade.access = p.role
    discovered = await p.facade.discover({"query": "inspect", "max_candidates": 8}, p.case.ctx)
    assert discovered["kind"] == "ok" and len(discovered["payload"]["tools"]) == 2
    arithmetic = await p.facade.discover(
        {"query": "arithmetic.calculate", "max_candidates": 8}, p.case.ctx
    )
    assert arithmetic["kind"] == "ok" and len(arithmetic["payload"]["tools"]) == 1
    changed = {**p.raw, "tool_ref": {**p.raw["tool_ref"], "content_hash": "0" * 64}}
    assert (await p.facade.invoke(changed, p.case.ctx))["kind"] != "ok"
    spec = {**p.case.spec, "provider_ref": {**p.case.spec["provider_ref"], "version": "99"}}
    with pytest.raises(DomainError):
        p.executor.check(p.case.call, spec)
    assert p.executor.calls == 0


async def test_office_another_tool_for_same_attempt_cannot_release_original_hold(office_pipeline):
    p = await approve_office(office_pipeline)
    hold = await p.case.budget.reserve(p.invocation.estimates, p.case.ctx)
    other = (KINDS.index(p.kind) + 1) % 3
    raw = {
        "tool_ref": p.pins[other].wire(),
        "action_id": p.case.call["action_id"],
        "arguments": ARGUMENTS[other],
    }
    assert normalize(raw, p.case.registry)["tool_ref"] != p.case.call["tool_ref"]
    assert (await p.facade.invoke(raw, p.case.ctx))["failure"]["code"] == "action_conflict"
    assert (await p.case.budget.get_reservation(hold["id"], p.case.ctx))["status"] == "reserved"
    assert p.executor.calls == 0


async def test_office_actual_provider_revoked_during_budget_wait_never_sends(office_pipeline):
    from tests.integration.test_control_plane import meta

    p = await approve_office(office_pipeline)
    original = p.case.budget.reserve

    async def revoked(*args):
        held = await original(*args)
        await p.case.domain[0].revoke_provider(
            p.case.domain[2], "fixture-provider", meta("office-provider-revoke", 2)
        )
        return held

    p.case.budget.reserve = revoked
    result = await p.facade.invoke(p.raw, p.case.ctx)
    assert result["failure"]["code"] == "dependency_unavailable" and p.executor.calls == 0
    hold = await p.case.ledger.get("tool.budget.reserved", p.case.ctx.attempt_id, p.case.ctx)
    assert (await p.case.budget.get_reservation(hold["id"], p.case.ctx))["status"] == "released"
    assert (await p.case.ledger.effect_from_attempt(p.case.ctx))["attempt_ids"] == []
