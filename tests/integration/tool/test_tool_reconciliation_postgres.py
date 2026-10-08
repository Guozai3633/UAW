"""Real SQL scenarios with explicitly controlled receipt/evidence sources, no sends."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from tests.integration.tool.conftest import approve, estimates
from tests.integration.tool.receipt_fixtures import (
    ControlledEvidenceReader,
    ControlledReceiptReader,
    confirmed_usage,
    receipt,
)
from tests.integration.tool.test_durable import cancel, restarted
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import TransactionalStore
from uaw.run.budget import BudgetService
from uaw.run.permissions import ExecutionPolicyResolver
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.tool.authority import ToolApprovalAuthority
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.ledger import ToolLedger
from uaw.tool.reconciliation import ToolReconciler


async def dispatched(case):
    await approve(case)
    await case.budget.reserve(estimates(), case.ctx)
    assert await case.budget.mark_dispatch(case.ctx) is True
    return (await case.ledger.effect_from_attempt(case.ctx))["revision"]


def reconciler(case, *, port=None, evidence=None, budget=None):
    return ToolReconciler(
        case.ledger,
        budget or case.budget,
        receipts=port or ControlledReceiptReader(case),
        evidence=evidence or ControlledEvidenceReader(case),
    )


async def test_sql_reconcile_restart_duplicate_and_no_repeated_fees(tool_case):
    case = tool_case
    revision = await dispatched(case)
    ref = await receipt(case)
    first = await reconciler(case).reconcile(ref, case.ctx, expected_revision=revision)
    assert first["kind"] == "ok" and first["payload"]["state"] == "confirmed"
    case = restarted(case)
    again = await reconciler(case).reconcile(ref, case.ctx, expected_revision=revision)
    assert again == first
    ledger = await case.budget.get_ledger(case.ctx)
    assert ledger["used"]["money"] == "0.03" and ledger["held"]["money"] == "0.00"
    assert ledger["used"]["tool_calls"] == 1
    with pytest.raises(DomainError):
        await case.budget.reserve(estimates(), case.ctx)


@pytest.mark.parametrize(
    "outcome,billing",
    [
        ("not_applied", "confirmed"),
        ("applied", "pending"),
        ("unknown", "confirmed"),
        ("unknown", "pending"),
    ],
)
async def test_sql_effect_and_cost_are_independent_and_unknown_dimensions_held(
    tool_case, outcome, billing
):
    case = tool_case
    revision = await dispatched(case)
    usage = (
        confirmed_usage(case.ctx)
        if billing == "confirmed"
        else {
            "attempt_id": case.ctx.attempt_id,
            "billing_state": "pending",
            "resources": {"currency": "USD"},
        }
    )
    ref = await receipt(case, outcome=outcome, usage=usage)
    result = await reconciler(case).reconcile(ref, case.ctx, expected_revision=revision)
    assert result["kind"] == "ok"
    assert result["payload"]["state"] == ("unknown" if outcome == "unknown" else "confirmed")
    budget = await case.budget.get_ledger(case.ctx)
    if billing == "pending":
        assert budget["held"]["money"] == "0.01" and budget["held"]["tool_calls"] == 1
        assert budget["billing_pending"] is True
        assert budget["used"]["tool_calls"] == 0
    else:
        assert budget["used"]["money"] == "0.03"  # not_applied is not a zero bill
        assert budget["billing_pending"] is False
    other = case.ctx.model_copy(update={"attempt_id": "another", "trace_id": "another"})
    await case.ledger.bind(case.call, case.spec, other)
    with pytest.raises(DomainError) as caught:
        await case.budget.reserve(estimates(), other)
    assert caught.value.failure.code == "unknown_effect"


async def test_sql_pending_fee_confirmation_and_same_usage_effect_update_do_not_double_charge(
    tool_case,
):
    case = tool_case
    revision = await dispatched(case)
    pending = {
        "attempt_id": case.ctx.attempt_id,
        "billing_state": "pending",
        "resources": {"currency": "USD"},
    }
    ref = await receipt(case, outcome="unknown", usage=pending)
    result = await reconciler(case).reconcile(ref, case.ctx, expected_revision=revision)
    newer = await receipt(case, name="confirmed-fee", outcome="unknown")
    result = await reconciler(case).reconcile(newer, case.ctx, expected_revision=result["revision"])
    assert result["kind"] == "ok" and result["payload"]["state"] == "unknown"
    budget_before = await case.budget.get_ledger(case.ctx)
    final = await receipt(case, name="applied-proof", outcome="applied")
    result = await reconciler(case).reconcile(final, case.ctx, expected_revision=result["revision"])
    assert result["kind"] == "ok" and result["payload"]["state"] == "confirmed"
    assert await case.budget.get_ledger(case.ctx) == budget_before


async def test_sql_bridge_existing_unknown_settlement_keeps_fee_holds(tool_case):
    case = tool_case
    revision = await dispatched(case)
    await case.budget.settle_unknown(case.ctx)
    before = await case.budget.get_ledger(case.ctx)
    ref = await receipt(
        case,
        outcome="unknown",
        usage={
            "attempt_id": case.ctx.attempt_id,
            "billing_state": "pending",
            "resources": {"currency": "USD"},
        },
    )
    result = await reconciler(case).reconcile(ref, case.ctx, expected_revision=revision)
    assert result["kind"] == "ok" and await case.budget.get_ledger(case.ctx) == before


async def test_sql_fee_reply_loss_replays_fixed_plan_after_restart(tool_case):
    case = tool_case
    revision = await dispatched(case)
    ref = await receipt(case)
    actual = BudgetService(case.ledger.store)

    class LoseReply:
        async def settle(self, *args, **kwargs):
            await actual.settle(*args, **kwargs)
            raise TimeoutError("Controlled reply loss after real SQL fee commit")

    broken = ToolBudgetAdapter(case.ledger, LoseReply(), case.approvals, state=actual)
    result = await reconciler(case, budget=broken).reconcile(
        ref, case.ctx, expected_revision=revision
    )
    assert result["failure"]["code"] == "reconciliation_interrupted"
    assert (await case.ledger.effect_from_attempt(case.ctx))["state"] == "confirmed"
    before = await actual.get_ledger(case.ctx)
    case = restarted(case)
    result = await reconciler(case).reconcile(ref, case.ctx, expected_revision=revision)
    assert result["kind"] == "ok" and await case.budget.get_ledger(case.ctx) == before


async def test_sql_concurrent_receipt_reconciliation_is_idempotent(tool_case):
    case = tool_case
    revision = await dispatched(case)
    ref = await receipt(case)
    results = await asyncio.wait_for(
        asyncio.gather(
            *(
                reconciler(restarted(case)).reconcile(ref, case.ctx, expected_revision=revision)
                for _ in range(3)
            )
        ),
        15,
    )
    assert all(r == results[0] and r["kind"] == "ok" for r in results)
    budget = await case.budget.get_ledger(case.ctx)
    assert budget["used"]["money"] == "0.03" and budget["used"]["tool_calls"] == 1
    assert results[0]["revision"] == revision + 1


async def test_sql_conflicting_receipt_and_effect_reversal_never_overwrite(tool_case):
    case = tool_case
    revision = await dispatched(case)
    ref = await receipt(case)
    first = await reconciler(case).reconcile(ref, case.ctx, expected_revision=revision)
    budget_before = await case.budget.get_ledger(case.ctx)
    conflict = await receipt(case, name="conflicting-proof", outcome="not_applied")
    result = await reconciler(case).reconcile(
        conflict, case.ctx, expected_revision=first["revision"]
    )
    assert result["failure"]["code"] == "receipt_conflict"
    assert (await case.ledger.effect_from_attempt(case.ctx)) == first["payload"]
    assert await case.budget.get_ledger(case.ctx) == budget_before


@pytest.mark.parametrize(
    "field", ["action_ref", "attempt_id", "provider_ref", "receipt_ref", "usage"]
)
async def test_sql_wrong_receipt_binding_rejected_before_effect_or_fee_write(tool_case, field):
    case = tool_case
    revision = await dispatched(case)
    ref = await receipt(case)
    reader = ControlledReceiptReader(case)
    value = await reader.read(ref, case.ctx)
    if field == "usage":
        value["usage"]["attempt_id"] = "wrong-attempt"
    elif field == "attempt_id":
        value[field] = "wrong-attempt"
    else:
        value[field] = {**value[field], "version": "wrong-version"}

    class CorruptControlledReader:
        async def read(self, *args):
            return value

    before = await case.budget.get_ledger(case.ctx)
    result = await reconciler(case, port=CorruptControlledReader()).reconcile(
        ref, case.ctx, expected_revision=revision
    )
    assert result["failure"]["code"] == "receipt_binding_conflict"
    assert (await case.ledger.effect_from_attempt(case.ctx))["state"] == "unknown"
    assert await case.budget.get_ledger(case.ctx) == before


async def test_sql_recovery_after_cancel_and_policy_revoke_does_not_admit_new_action(tool_case):
    case = tool_case
    revision = await dispatched(case)
    ref = await receipt(case, outcome="not_applied")
    policy = await case.ledger.store.get(
        case.ctx.principal, "execution.policies", case.ctx.capability_policy_ref.id
    )
    await case.ledger.store.put(
        case.ctx.principal,
        "execution.policies",
        policy.resource_id,
        "CapabilityPolicy",
        {**policy.payload, "revision": 2, "denied_capabilities": ["tool.invoke"]},
        expected_revision=1,
        request_id="reconciliation-revoke",
    )
    await cancel(case)
    result = await reconciler(restarted(case)).reconcile(ref, case.ctx, expected_revision=revision)
    assert result["kind"] == "ok"
    assert (await case.budget.get_ledger(case.ctx))["used"]["money"] == "0.03"
    with pytest.raises(DomainError):
        await case.budget.mark_dispatch(case.ctx)


async def test_sql_expired_attempt_can_clean_actual_fees_only(tool_case):
    case = tool_case
    revision = await dispatched(case)
    ref = await receipt(case)
    # Root deadline changes after the attempt was already dispatched. Recovery query
    # remains valid; ExecutionPolicyPort denies future admission on the current root.
    run = await case.ledger.store.get(case.ctx.principal, "runs", case.ctx.run_id)
    value = {
        **run.payload,
        "revision": run.revision + 1,
        "budget": {
            **run.payload["budget"],
            "deadline": (datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
        },
    }
    await case.ledger.store.put(
        case.ctx.principal,
        "runs",
        run.resource_id,
        "RunRecord",
        value,
        expected_revision=run.revision,
        request_id="fixture-expired-root",
    )
    assert (await reconciler(case).reconcile(ref, case.ctx, expected_revision=revision))[
        "kind"
    ] == "ok"
    with pytest.raises(DomainError):
        await case.budget.reserve(estimates(), case.ctx)


async def test_sql_missing_or_revoked_readers_keep_unknown_and_all_unobserved_holds(tool_case):
    case = tool_case
    revision = await dispatched(case)
    ref = await receipt(case)
    before = await case.budget.get_ledger(case.ctx)
    for receipts, evidence in ((None, None), (ControlledReceiptReader(case), None)):
        result = await ToolReconciler(
            case.ledger, case.budget, receipts=receipts, evidence=evidence
        ).reconcile(ref, case.ctx, expected_revision=revision)
        assert result["failure"]["code"] == "dependency_unavailable"
    reader = ControlledReceiptReader(case)
    reader.allowed = False
    result = await reconciler(case, port=reader).reconcile(
        ref, case.ctx, expected_revision=revision
    )
    assert result["kind"] == "denied"
    evidence = ControlledEvidenceReader(case)
    evidence.allowed = False
    assert (
        await reconciler(case, evidence=evidence).reconcile(
            ref, case.ctx, expected_revision=revision
        )
    )["kind"] == "denied"
    assert (await case.ledger.effect_from_attempt(case.ctx))["state"] == "unknown"
    assert await case.budget.get_ledger(case.ctx) == before


async def test_sql_missing_budget_state_never_falls_back_to_private_records(tool_case):
    case = tool_case
    await approve(case)
    missing = ToolBudgetAdapter(case.ledger, BudgetService(case.ledger.store), case.approvals)
    with pytest.raises(DomainError) as caught:
        await missing.reserve(estimates(), case.ctx)
    assert caught.value.failure.code == "dependency_unavailable"
    assert caught.value.failure.failed_phase == "budget_state"


async def test_sql_tool_can_run_with_all_private_budget_policy_reads_blocked(tool_case):
    case = tool_case

    class ToolOnlyStore(PostgresRecordStore):
        async def get(self, principal, namespace, *args, **kwargs):
            assert not namespace.startswith("budget.") and namespace != "execution.policies"
            return await super().get(principal, namespace, *args, **kwargs)

    class GuardedTransactions(TransactionalStore):
        async def inspect(self, owner, aggregate, action):
            async def checked(tx):
                original = tx.load

                async def load(namespace, *args):
                    assert not namespace.startswith("budget.") and namespace != "execution.policies"
                    return await original(namespace, *args)

                tx.load = load
                return await action(tx)

            return await super().inspect(owner, aggregate, checked)

    ledger = ToolLedger(ToolOnlyStore(case.ledger.store.database))
    ledger.transactions = GuardedTransactions(case.ledger.store.database)
    case.ledger = ledger
    case.authority.ledger = ledger
    case.approvals.ledger = ledger
    case.budget.ledger = ledger
    revision = await dispatched(case)
    ref = await receipt(case)
    assert (await reconciler(case).reconcile(ref, case.ctx, expected_revision=revision))[
        "kind"
    ] == "ok"


async def test_sql_tool_parent_chain_is_decided_by_execution_policy_port(tool_case):
    case = tool_case
    row = await case.ledger.store.get(
        case.ctx.principal, "execution.policies", case.ctx.capability_policy_ref.id
    )
    parent = {
        **row.payload,
        "id": "tool-parent",
        "revision": 1,
        "denied_capabilities": ["tool.invoke"],
    }
    await case.ledger.store.put(
        case.ctx.principal,
        "execution.policies",
        parent["id"],
        "CapabilityPolicy",
        parent,
        expected_revision=0,
        request_id="fixture-parent",
    )
    child = {
        **row.payload,
        "revision": 2,
        "parent_policy_ref": {"kind": "policy", "id": parent["id"], "version": "1"},
    }
    await case.ledger.store.put(
        case.ctx.principal,
        "execution.policies",
        row.resource_id,
        "CapabilityPolicy",
        child,
        expected_revision=1,
        request_id="fixture-child-parent",
    )
    new = case.ctx.model_copy(
        update={
            "capability_policy_ref": Ref(kind="policy", id=row.resource_id, version="2"),
            "attempt_id": "parent-test",
            "operation_id": "parent-test",
        }
    )
    # A different logical action needs a new operation binding, never changes the old one.
    changed = {**case.call, "action_id": "parent-test"}
    await case.ledger.bind(changed, case.spec, new)
    authority = ToolApprovalAuthority(
        case.ledger,
        case.registry,
        case.domain[0],
        case.authority.access,
        case.reader,
        policies=ExecutionPolicyResolver(case.ledger.store),
    )
    with pytest.raises(DomainError) as caught:
        await authority.current("parent-test", new)
    assert caught.value.failure.code == "execution_policy_denied"


async def test_sql_effect_is_not_rolled_back_by_rejected_fee_update(tool_case):
    case = tool_case
    revision = await dispatched(case)
    pending = {
        "attempt_id": case.ctx.attempt_id,
        "billing_state": "pending",
        "resources": {"currency": "USD"},
    }
    first_ref = await receipt(case, name="first-pending", outcome="unknown", usage=pending)
    first = await reconciler(case).reconcile(first_ref, case.ctx, expected_revision=revision)
    richer = {**pending, "resources": {"currency": "USD", "tool_calls": 1}}
    effect_ref = await receipt(case, name="applied-pending-fees", outcome="applied", usage=richer)
    rejected = await reconciler(case).reconcile(
        effect_ref, case.ctx, expected_revision=first["revision"]
    )
    assert rejected["failure"]["code"] == "usage_reconciliation_denied"
    known = await case.ledger.effect_from_attempt(case.ctx)
    assert known["state"] == "confirmed" and known["receipt_ref"] == effect_ref.wire()
    assert (await case.budget.get_ledger(case.ctx))["held"]["money"] == "0.01"
    final_ref = await receipt(case, name="confirmed-fees", outcome="applied")
    final = await reconciler(restarted(case)).reconcile(
        final_ref, case.ctx, expected_revision=known["revision"]
    )
    assert (
        final["kind"] == "ok"
        and (await case.budget.get_ledger(case.ctx))["used"]["money"] == "0.03"
    )
    # A superseded unfinished bill cannot take over the current accounting plan.
    stale = await reconciler(case).reconcile(
        effect_ref, case.ctx, expected_revision=known["revision"]
    )
    assert stale["kind"] == "stale"


async def test_sql_tool_finish_reply_loss_reuses_completed_receipt(tool_case):
    case = tool_case
    revision = await dispatched(case)
    ref = await receipt(case)

    class LoseToolReply(ToolLedger):
        async def finish_reconciliation(self, *args):
            await super().finish_reconciliation(*args)
            raise TimeoutError("Controlled Tool reply loss after actual finish commit")

    ledger = LoseToolReply(case.ledger.store)
    first = await ToolReconciler(
        ledger,
        case.budget,
        receipts=ControlledReceiptReader(case),
        evidence=ControlledEvidenceReader(case),
    ).reconcile(ref, case.ctx, expected_revision=revision)
    assert first["failure"]["code"] == "reconciliation_interrupted"
    before = await case.budget.get_ledger(case.ctx)
    assert (await reconciler(restarted(case)).reconcile(ref, case.ctx, expected_revision=revision))[
        "kind"
    ] == "ok"
    assert await case.budget.get_ledger(case.ctx) == before


async def test_sql_conflicting_concurrent_receipts_have_one_cas_winner(tool_case):
    case = tool_case
    revision = await dispatched(case)
    one = await receipt(case, name="concurrent-applied", outcome="applied")
    two = await receipt(case, name="concurrent-not-applied", outcome="not_applied")
    results = await asyncio.wait_for(
        asyncio.gather(
            *(
                reconciler(restarted(case)).reconcile(ref, case.ctx, expected_revision=revision)
                for ref in (one, two)
            )
        ),
        15,
    )
    assert sum(r["kind"] == "ok" for r in results) == 1
    assert sum(r["kind"] == "conflict" for r in results) == 1
    assert (await case.budget.get_ledger(case.ctx))["used"]["money"] == "0.03"


async def test_sql_actual_receipt_version_changed_before_read_is_stale(tool_case):
    case = tool_case
    revision = await dispatched(case)
    old = await receipt(case)
    latest = await receipt(case, version=2)
    rejected = await reconciler(case).reconcile(old, case.ctx, expected_revision=revision)
    assert rejected["kind"] == "stale"
    assert (await case.ledger.effect_from_attempt(case.ctx))["state"] == "unknown"
    assert (await reconciler(case).reconcile(latest, case.ctx, expected_revision=revision))[
        "kind"
    ] == "ok"


async def test_sql_new_process_resumes_same_fee_plan_after_lost_reply(tool_case):
    import json
    import subprocess
    import sys
    from pathlib import Path

    case = tool_case
    revision = await dispatched(case)
    ref = await receipt(case)
    actual = BudgetService(case.ledger.store)

    class LostReceipt:
        async def settle(self, *args, **kwargs):
            await actual.settle(*args, **kwargs)
            raise TimeoutError("Actual SQL commit preceded controlled process loss")

    broken = ToolBudgetAdapter(case.ledger, LostReceipt(), state=actual)
    first = await reconciler(case, budget=broken).reconcile(
        ref, case.ctx, expected_revision=revision
    )
    assert first["failure"]["code"] == "reconciliation_interrupted"
    before = await case.budget.get_ledger(case.ctx)
    child = Path(__file__).with_name("reconcile_child.py")
    data = json.dumps(
        {"context": case.ctx.wire(), "receipt_ref": ref.wire(), "expected_revision": revision}
    )
    result = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-m", "tests.integration.tool.reconcile_child"],
        input=data,
        text=True,
        capture_output=True,
        timeout=30,
        cwd=child.parents[3],
    )
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"kind": "ok", "state": "confirmed", "failure_code": None}
    assert await case.budget.get_ledger(case.ctx) == before
