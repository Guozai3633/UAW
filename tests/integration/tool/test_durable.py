"""Real PostgreSQL + real Approval/Budget services, no actual sends/executor."""

import asyncio
from dataclasses import replace

import pytest
from sqlalchemy import select

from tests.integration.test_control_plane import meta
from tests.integration.tool.conftest import approve, estimates
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.run.approval import ApprovalService
from uaw.run.budget import BudgetService
from uaw.run.permissions import ExecutionPolicyResolver
from uaw.shared.errors import DomainError
from uaw.tool.approval import ToolApprovalAdapter
from uaw.tool.authority import ToolApprovalAuthority
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.facade import ToolFacade
from uaw.tool.ledger import ToolLedger, action_key


def restarted(case):
    ledger = ToolLedger(PostgresRecordStore(case.ledger.store.database))
    authority = ToolApprovalAuthority(
        ledger,
        case.registry,
        case.domain[0],
        case.authority.access,
        case.reader,
        policies=ExecutionPolicyResolver(ledger.store),
    )
    service = ApprovalService(ledger.store, case.domain[0], authority)
    approvals = ToolApprovalAdapter(ledger, authority, service)
    return replace(
        case,
        ledger=ledger,
        authority=authority,
        service=service,
        approvals=approvals,
        budget=ToolBudgetAdapter(
            ledger, BudgetService(ledger.store), approvals, state=BudgetService(ledger.store)
        ),
    )


async def cancel(case):
    run = case.domain[1]
    current = (await run.store.get(case.ctx.principal, "runs", case.ctx.run_id)).payload
    await run.control(
        case.ctx.principal,
        {
            "run_id": case.ctx.run_id,
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "Fixture cancellation"},
        },
        meta("fixture-cancel", current["revision"]),
    )


async def test_sql_action_restart_duplicates_context_and_attempt_boundaries(tool_case):
    case = tool_case
    case = restarted(case)
    key = await case.ledger.bind(case.call, case.spec, case.ctx)
    assert key == action_key(case.ctx, case.call["action_id"])
    assert (await case.ledger.action(case.call["action_id"], case.ctx))[0] == case.call
    next_ctx = case.ctx.model_copy(update={"attempt_id": "attempt-two", "trace_id": "trace-two"})
    assert await case.ledger.bind(case.call, case.spec, next_ctx) == key
    assert await case.ledger.attempt(next_ctx) == case.call
    for changed in (
        {**case.call, "arguments_hash": "0" * 64},
        {**case.call, "action_id": "new-action"},
    ):
        with pytest.raises(DomainError):
            await case.ledger.bind(changed, case.spec, case.ctx)
    with pytest.raises(DomainError):
        await case.ledger.bind(
            case.call, case.spec, case.ctx.model_copy(update={"operation_id": "different"})
        )


async def test_sql_real_wait_approved_restart_missing_executor_no_budget(tool_case):
    case = tool_case
    pending = await case.approvals.precheck(case.call, case.spec, case.ctx)
    assert pending["kind"] == "waiting"
    row = await case.ledger.store.get(case.ctx.principal, "approvals", pending["wait_ref"]["id"])
    assert str(row.revision) == pending["wait_ref"]["version"]
    assert not await case.ledger.get("tool.budget.reserved", case.ctx.attempt_id, case.ctx)
    await approve(case)
    case = restarted(case)
    facade = ToolFacade(
        case.registry, case.authority.access, precheck=case.approvals, recheck=case.approvals
    )
    raw = {k: v for k, v in case.call.items() if k != "arguments_hash"}
    result = await facade.invoke(raw, case.ctx)
    assert result["failure"]["failed_phase"] == "dispatch"
    assert result["failure"]["code"] == "dependency_unavailable"
    assert not await case.ledger.get("tool.budget.reserved", case.ctx.attempt_id, case.ctx)


async def test_sql_pending_does_not_hold_budget_and_unknown_cannot_retry(tool_case):
    case = tool_case
    with pytest.raises(DomainError):
        await case.budget.reserve(estimates(), case.ctx)
    await approve(case)
    reservation = await case.budget.reserve(estimates(), case.ctx)
    results = await asyncio.wait_for(
        asyncio.gather(
            case.budget.mark_dispatch(case.ctx), restarted(case).budget.mark_dispatch(case.ctx)
        ),
        10,
    )
    assert sorted(results) == [False, True]
    case = restarted(case)
    assert (await case.ledger.effect(case.call["action_id"], case.ctx))["state"] == "unknown"
    assert await case.budget.mark_dispatch(case.ctx) is False
    with pytest.raises(DomainError) as caught:
        await case.budget.release(case.ctx)
    assert caught.value.failure.code == "unknown_effect"
    other = case.ctx.model_copy(update={"attempt_id": "retry-attempt", "trace_id": "retry-trace"})
    await case.ledger.bind(case.call, case.spec, other)
    with pytest.raises(DomainError) as caught:
        await case.budget.reserve(estimates(), other)
    assert caught.value.failure.code == "unknown_effect"
    settled = await case.budget.settle_unknown(case.ctx)
    assert settled["billing_pending"] is True
    assert await restarted(case).budget.settle_unknown(case.ctx) == settled
    account = (
        await case.ledger.store.get(case.ctx.principal, "budget.accounting", reservation["id"])
    ).payload
    assert account["held"] == estimates() and account["used"]["tool_calls"] == 0


async def test_sql_concurrent_budget_reserve_once_and_no_nested_transaction_deadlock(tool_case):
    case = tool_case
    await approve(case)
    receipts = await asyncio.wait_for(
        asyncio.gather(*(restarted(case).budget.reserve(estimates(), case.ctx) for _ in range(3))),
        10,
    )
    assert receipts[0] == receipts[1] == receipts[2]
    budget = (
        await case.ledger.store.get(case.ctx.principal, "budget.ledgers", case.ctx.run_id)
    ).payload
    assert budget["held"]["tool_calls"] == 1
    assert await case.budget.release(case.ctx) == await restarted(case).budget.release(case.ctx)
    with pytest.raises(DomainError):
        await case.budget.reserve(estimates(), case.ctx)
    with pytest.raises(DomainError):
        await case.budget.mark_dispatch(case.ctx)


@pytest.mark.parametrize("phase", ["reserve", "dispatch", "release", "settle"])
async def test_sql_crash_after_service_commit_recovers_same_budget_request(tool_case, phase):
    case = tool_case
    await approve(case)
    actual = BudgetService(case.ledger.store)

    class LoseReceipt:
        def __getattr__(self, name):
            method = getattr(actual, name)

            async def run(*args, **kwargs):
                result = await method(*args, **kwargs)
                if name == phase:
                    raise TimeoutError("Injected response loss after actual SQL commit")
                return result

            return run

    if phase != "reserve":
        await case.budget.reserve(estimates(), case.ctx)
    if phase == "settle":
        await case.budget.mark_dispatch(case.ctx)
    broken = ToolBudgetAdapter(
        case.ledger, LoseReceipt(), case.approvals, state=BudgetService(case.ledger.store)
    )
    methods = {
        "reserve": lambda: broken.reserve(estimates(), case.ctx),
        "dispatch": lambda: broken.mark_dispatch(case.ctx),
        "release": lambda: broken.release(case.ctx),
        "settle": lambda: broken.settle_unknown(case.ctx),
    }
    with pytest.raises(TimeoutError):
        await methods[phase]()
    case = restarted(case)
    if phase == "reserve":
        recovered = await case.budget.reserve(estimates(), case.ctx)
        assert recovered["status"] == "reserved"
    elif phase == "dispatch":
        assert await case.budget.mark_dispatch(case.ctx) is False
        assert (await case.ledger.effect(case.call["action_id"], case.ctx))["state"] == "unknown"
    elif phase == "release":
        assert (await case.budget.release(case.ctx))["status"] == "released"
    else:
        assert (await case.budget.settle_unknown(case.ctx))["billing_pending"] is True


async def test_sql_approval_hash_resource_effect_policy_and_cancel_change(tool_case):
    case = tool_case
    await approve(case)
    request = await case.authority.current(case.call["action_id"], case.ctx)
    for altered in (
        {**request, "arguments_hash": "0" * 64},
        {**request, "resource_refs": []},
        {**request, "effect": "read"},
    ):
        with pytest.raises(DomainError):
            await case.authority.check(altered, case.ctx)
    case.reader.source = {**case.reader.source, "version": "2"}
    with pytest.raises(DomainError):
        await case.approvals.require_approved(case.ctx)
    case.reader.source = request["resource_refs"][0]
    await cancel(case)
    denied = await case.approvals.precheck(case.call, case.spec, case.ctx)
    assert denied["kind"] == "cancelled"
    with pytest.raises(DomainError):
        await case.budget.reserve(estimates(), case.ctx)


async def test_sql_missing_reader_role_port_and_current_provider_revocation(tool_case):
    case = tool_case
    await approve(case)
    request = await case.authority.current(case.call["action_id"], case.ctx)
    for access, reader in ((case.authority.access, None), (None, case.reader)):
        missing = ToolApprovalAuthority(case.ledger, case.registry, case.domain[0], access, reader)
        with pytest.raises(DomainError) as caught:
            await missing.check(request, case.ctx)
        assert caught.value.failure.code == "dependency_unavailable"
    await case.domain[0].revoke_provider(
        case.domain[2], "fixture-provider", meta("fixture-revoke", 2)
    )
    with pytest.raises(DomainError):
        await case.approvals.require_approved(case.ctx)


async def test_sql_cancelled_reserved_attempt_release_recovery(tool_case):
    case = tool_case
    await approve(case)
    await case.budget.reserve(estimates(), case.ctx)
    await cancel(case)
    assert (await restarted(case).budget.release(case.ctx))["status"] == "released"
    budget = (
        await case.ledger.store.get(case.ctx.principal, "budget.ledgers", case.ctx.run_id)
    ).payload
    assert budget["held"]["tool_calls"] == 0


async def test_sql_two_attempts_cannot_claim_same_action(tool_case):
    case = tool_case
    await approve(case)
    other = case.ctx.model_copy(
        update={"attempt_id": "competing-attempt", "trace_id": "competing-trace"}
    )
    await case.ledger.bind(case.call, case.spec, other)
    await case.budget.reserve(estimates(), case.ctx)
    await case.budget.reserve(estimates(), other)
    result = await asyncio.wait_for(
        asyncio.gather(
            case.budget.mark_dispatch(case.ctx),
            case.budget.mark_dispatch(other),
            return_exceptions=True,
        ),
        10,
    )
    assert sum(r is True for r in result) == 1
    assert sum(isinstance(r, DomainError) for r in result) == 1
    async with case.ledger.store.database.sessions() as session:
        rows = (
            await session.scalars(
                select(RecordRow).where(
                    RecordRow.principal_id == case.ctx.principal.id,
                    RecordRow.namespace == "tool.dispatch.intents",
                )
            )
        ).all()
    assert len(rows) == 1


async def test_sql_claim_commit_before_accounting_crash_never_reissues_send(tool_case):
    case = tool_case
    await approve(case)
    await case.budget.reserve(estimates(), case.ctx)

    class FailBeforeDispatch(BudgetService):
        async def dispatch(self, *args, **kwargs):
            raise TimeoutError("Injected crash after claim, before budget accounting")

    broken = ToolBudgetAdapter(
        case.ledger,
        FailBeforeDispatch(case.ledger.store),
        case.approvals,
        state=BudgetService(case.ledger.store),
    )
    with pytest.raises(TimeoutError):
        await broken.mark_dispatch(case.ctx)
    case = restarted(case)
    assert (await case.ledger.effect(case.call["action_id"], case.ctx))["state"] == "unknown"
    assert await case.budget.mark_dispatch(case.ctx) is False
    assert (await case.budget.settle_unknown(case.ctx))["billing_pending"] is True


async def test_sql_policy_revision_and_parameter_changes_cannot_reuse_grant(tool_case):
    case = tool_case
    await approve(case)
    changed = {**case.call, "arguments": {"text": "changed original"}}
    from uaw.tool.schema import digest

    changed["arguments_hash"] = digest(changed["arguments"])
    result = await case.approvals.precheck(changed, case.spec, case.ctx)
    assert result["kind"] == "conflict"
    row = await case.ledger.store.get(
        case.ctx.principal, "execution.policies", case.ctx.capability_policy_ref.id
    )
    await case.ledger.store.put(
        case.ctx.principal,
        "execution.policies",
        row.resource_id,
        "CapabilityPolicy",
        {**row.payload, "revision": 2, "denied_capabilities": ["tool.invoke"]},
        expected_revision=1,
        request_id="fixture-revoke-policy",
    )
    with pytest.raises(DomainError):
        await case.approvals.require_approved(case.ctx)


async def test_sql_cancel_after_unknown_preserves_effect_and_unobserved_budget(tool_case):
    case = tool_case
    await approve(case)
    await case.budget.reserve(estimates(), case.ctx)
    await case.budget.mark_dispatch(case.ctx)
    await cancel(case)
    settled = await restarted(case).budget.settle_unknown(case.ctx)
    assert settled["billing_pending"] is True
    assert (await case.ledger.effect(case.call["action_id"], case.ctx))["state"] == "unknown"
    with pytest.raises(DomainError):
        await case.budget.release(case.ctx)
    with pytest.raises(DomainError):
        await case.budget.mark_dispatch(case.ctx)


async def test_sql_cancel_after_lost_reserve_receipt_releases_only_actual_commit(tool_case):
    case = tool_case
    await approve(case)
    real = BudgetService(case.ledger.store)

    class LoseReserveReceipt:
        async def reserve(self, *args, **kwargs):
            await real.reserve(*args, **kwargs)
            raise TimeoutError("Response lost after SQL reserve commit")

    with pytest.raises(TimeoutError):
        await ToolBudgetAdapter(
            case.ledger,
            LoseReserveReceipt(),
            case.approvals,
            state=BudgetService(case.ledger.store),
        ).reserve(estimates(), case.ctx)
    await cancel(case)
    assert (await restarted(case).budget.release(case.ctx))["status"] == "released"


async def test_sql_release_dispatch_race_keeps_exactly_one_persistent_intent(tool_case):
    case = tool_case
    await approve(case)
    await case.budget.reserve(estimates(), case.ctx)
    result = await asyncio.wait_for(
        asyncio.gather(
            case.budget.mark_dispatch(case.ctx),
            case.budget.release(case.ctx),
            return_exceptions=True,
        ),
        10,
    )
    assert sum(isinstance(r, DomainError) for r in result) == 1
    dispatch = await case.ledger.get(
        "tool.dispatch.intents", action_key(case.ctx, case.call["action_id"]), case.ctx
    )
    release = await case.ledger.get("tool.budget.release.refs", case.ctx.attempt_id, case.ctx)
    assert (dispatch is not None) != (release is not None)
