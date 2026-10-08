"""Actual SQL with controlled owning-source Lookup/Readers, no real execution."""

import asyncio
from copy import deepcopy

import pytest
from sqlalchemy import select

from tests.integration.tool.receipt_fixtures import (
    ControlledEvidenceReader,
    ControlledReceiptReader,
    receipt,
)
from tests.integration.tool.recovery_fixtures import (
    ControlledActionReceiptLookup,
    NoNewExecutionAccess,
    register_lookup,
)
from tests.integration.tool.test_durable import cancel, restarted
from tests.integration.tool.test_tool_reconciliation_postgres import dispatched
from uaw.infrastructure.db.models import RecordRow
from uaw.run.budget import BudgetService
from uaw.shared.contracts import Principal, Scope
from uaw.shared.errors import DomainError
from uaw.shared.schema import validate_contract
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.facade import ToolFacade
from uaw.tool.ledger import action_key
from uaw.tool.reconciliation import ToolReconciler


class RecoveryBudgetOnly:
    """Actual BudgetService settles fees; any new admission/send is a test failure."""

    def __init__(self, actual):
        self.actual = actual

    async def reserve(self, *args, **kwargs):
        raise AssertionError("Recovery cannot reserve")

    async def dispatch(self, *args, **kwargs):
        raise AssertionError("Recovery cannot dispatch")

    async def settle(self, *args, **kwargs):
        return await self.actual.settle(*args, **kwargs)


def facade(case, *, reader=None, evidence=None, lookup=None, budget=None):
    actual = BudgetService(case.ledger.store)
    budget = budget or ToolBudgetAdapter(case.ledger, RecoveryBudgetOnly(actual), state=actual)
    reader = reader or ControlledReceiptReader(case)
    lookup = lookup or ControlledActionReceiptLookup(case, receipts=reader)
    reconciler = ToolReconciler(
        case.ledger, budget, receipts=reader, evidence=evidence or ControlledEvidenceReader(case)
    )
    return ToolFacade(case.registry, NoNewExecutionAccess(), lookup=lookup, reconciler=reconciler)


def request(case, revision):
    return {"action_id": case.call["action_id"], "expected_revision": revision}


async def original_execution_rows(case):
    # Test assertion only: no new Tool attempt/reserve/intent or invocation mutation.
    unchanged = {
        "tool.calls",
        "tool.contexts",
        "tool.specs",
        "tool.effects",
        "tool.attempt.calls",
        "tool.attempt.contexts",
        "tool.attempt.estimates",
        "tool.approval.requests",
        "tool.dispatch.intents",
        "tool.budget.reserved",
        "tool.budget.dispatched",
        "tool.budget.reserve.plans",
        "tool.budget.release.refs",
        "tool.budget.released",
    } - {"tool.effects"}
    async with case.ledger.store.database.sessions() as session:
        rows = (
            (
                await session.execute(
                    select(RecordRow).where(
                        RecordRow.principal_id == case.ctx.principal.id,
                        RecordRow.namespace.in_(unchanged),
                    )
                )
            )
            .scalars()
            .all()
        )
        return sorted((r.namespace, r.resource_id, r.revision, deepcopy(r.payload)) for r in rows)


@pytest.mark.parametrize("outcome,billing", [("not_applied", "confirmed"), ("unknown", "pending")])
async def test_sql_facade_lookup_explicit_outcome_and_independent_fees(tool_case, outcome, billing):
    c = tool_case
    revision = await dispatched(c)
    usage = (
        None
        if billing == "confirmed"
        else {
            "attempt_id": c.ctx.attempt_id,
            "billing_state": "pending",
            "resources": {"currency": "USD"},
        }
    )
    ref = await receipt(c, outcome=outcome, usage=usage)
    await register_lookup(c, ref)
    before = await original_execution_rows(c)
    f = facade(c)
    result = await f.reconcile(request(c, revision), c.ctx)
    validate_contract("RuntimeToolruntimeReconcileResult", result)
    assert result["kind"] == "ok" and result["output_refs"] == [ref.wire()]
    actual = await f.read_outcome(c.call["action_id"], c.ctx)
    validate_contract("ToolReconciliationReceipt", actual)
    assert actual["outcome"] == outcome and actual["attempt_id"] == c.ctx.attempt_id
    assert result["payload"]["state"] == ("unknown" if outcome == "unknown" else "confirmed")
    budget = await c.budget.get_ledger(c.ctx)
    if billing == "confirmed":
        assert budget["used"]["money"] == "0.03" and budget["held"]["money"] == "0.00"
    else:
        assert budget["held"]["money"] == "0.01" and budget["held"]["tool_calls"] == 1
        assert budget["billing_pending"] is True and budget["used"]["tool_calls"] == 0
    actual["outcome"] = "applied"
    assert (await f.read_outcome(c.call["action_id"], c.ctx))["outcome"] == outcome
    assert await original_execution_rows(c) == before


async def test_sql_facade_no_registered_source_preserves_unknown_and_holds(tool_case):
    c = tool_case
    revision = await dispatched(c)
    await receipt(c)  # Existence alone does not register an owning-domain source.
    before = await c.budget.get_ledger(c.ctx)
    effect = await c.ledger.effect_from_attempt(c.ctx)
    result = await facade(c).reconcile(request(c, revision), c.ctx)
    assert result["kind"] == "missing" and result["failure"]["code"] == "receipt_missing"
    assert await c.budget.get_ledger(c.ctx) == before
    assert await c.ledger.effect_from_attempt(c.ctx) == effect
    with pytest.raises(DomainError) as error:
        await facade(c).read_outcome(c.call["action_id"], c.ctx)
    assert error.value.failure.code == "receipt_missing"


@pytest.mark.parametrize("missing", ["lookup", "reconciler", "reader", "evidence"])
async def test_sql_facade_missing_ports_fail_without_writes(tool_case, missing):
    c = tool_case
    revision = await dispatched(c)
    ref = await receipt(c)
    await register_lookup(c, ref)
    f = facade(c)
    if missing in {"lookup", "reconciler"}:
        setattr(f, missing, None)
    elif missing == "reader":
        f.reconciler.receipts = None
    else:
        f.reconciler.evidence = None
    before = await c.budget.get_ledger(c.ctx)
    result = await f.reconcile(request(c, revision), c.ctx)
    assert result["failure"]["code"] == "dependency_unavailable"
    assert (await c.ledger.effect_from_attempt(c.ctx))["state"] == "unknown"
    assert await c.budget.get_ledger(c.ctx) == before


async def test_sql_facade_model_receipt_ref_rejected_before_lookup(tool_case):
    c = tool_case
    revision = await dispatched(c)
    ref = await receipt(c)
    await register_lookup(c, ref)
    f = facade(c)
    result = await f.reconcile({**request(c, revision), "receipt_ref": ref.wire()}, c.ctx)
    assert result["failure"]["code"] == "invalid_arguments" and f.lookup.calls == 0
    assert (await c.ledger.effect_from_attempt(c.ctx))["state"] == "unknown"


@pytest.mark.parametrize("binding", ["principal", "attempt", "run", "action"])
async def test_sql_facade_rejects_foreign_context_before_lookup(tool_case, binding):
    c = tool_case
    revision = await dispatched(c)
    ref = await receipt(c)
    await register_lookup(c, ref)
    ctx, req = c.ctx, request(c, revision)
    if binding == "principal":
        ctx = ctx.model_copy(
            update={
                "principal": Principal(
                    id="foreign-principal", kind="user", auth_session_id="foreign-session"
                ),
                "scope": Scope(
                    principal_id="foreign-principal",
                    conversation_id=ctx.conversation_id,
                    task_id=ctx.task_id,
                ),
            }
        )
    elif binding == "attempt":
        ctx = ctx.model_copy(update={"attempt_id": "foreign-attempt"})
    elif binding == "run":
        ctx = ctx.model_copy(update={"run_id": "foreign-run"})
    else:
        req["action_id"] = "foreign-action"
    before = await c.budget.get_ledger(c.ctx)
    f = facade(c)
    assert (await f.reconcile(req, ctx))["kind"] in {"missing", "conflict", "denied"}
    assert f.lookup.calls == 0 and await c.budget.get_ledger(c.ctx) == before


@pytest.mark.parametrize("binding", ["action_ref", "attempt_id", "provider_ref", "usage"])
async def test_sql_lookup_independent_registration_binding_rejected(tool_case, binding):
    c = tool_case
    revision = await dispatched(c)
    ref = await receipt(c)
    await register_lookup(c, ref)
    key = action_key(c.ctx, c.call["action_id"])
    row = await c.ledger.store.get(c.ctx.principal, "tool.fixture.lookup", key)
    value = deepcopy(row.payload)
    if binding in {"action_ref", "provider_ref"}:
        value[binding]["id"] = "foreign-source"
    elif binding == "usage":
        value[binding]["attempt_id"] = "foreign-attempt"
    else:
        value[binding] = "foreign-attempt"
    await c.ledger.store.put(
        c.ctx.principal,
        "tool.fixture.lookup",
        key,
        "ToolReconciliationReceipt",
        value,
        expected_revision=row.revision,
        request_id="fixture-corrupt-lookup",
    )
    before = await c.budget.get_ledger(c.ctx)
    result = await facade(c).reconcile(request(c, revision), c.ctx)
    assert result["failure"]["code"] == "lookup_binding_conflict"
    assert await c.budget.get_ledger(c.ctx) == before
    assert (await c.ledger.effect_from_attempt(c.ctx))["state"] == "unknown"


async def test_sql_facade_still_reconciles_provider_binding_after_lookup(tool_case):
    c = tool_case
    revision = await dispatched(c)
    ref = await receipt(c)
    await register_lookup(c, ref)
    real = ControlledReceiptReader(c)
    lookup = ControlledActionReceiptLookup(c, receipts=real)

    class WrongProviderReader:
        async def read(self, ref, ctx):
            result = await real.read(ref, ctx)
            result["provider_ref"]["id"] = "other-provider"
            return result

    result = await facade(c, reader=WrongProviderReader(), lookup=lookup).reconcile(
        request(c, revision), c.ctx
    )
    assert result["failure"]["code"] == "receipt_binding_conflict"
    assert (await c.ledger.effect_from_attempt(c.ctx))["state"] == "unknown"


async def test_sql_facade_duplicate_restart_and_read_outcome_have_one_fee_plan(tool_case):
    c = tool_case
    revision = await dispatched(c)
    ref = await receipt(c, outcome="not_applied")
    await register_lookup(c, ref)
    original = await original_execution_rows(c)
    first = await facade(c).reconcile(request(c, revision), c.ctx)
    assert first["kind"] == "ok"
    before = await c.budget.get_ledger(c.ctx)
    c = restarted(c)
    f = facade(c)
    assert await f.reconcile(request(c, revision), c.ctx) == first
    assert (await f.read_outcome(c.call["action_id"], c.ctx))["outcome"] == "not_applied"
    assert (
        await c.budget.get_ledger(c.ctx) == before and await original_execution_rows(c) == original
    )


async def test_sql_facade_concurrent_reconciliation_uses_original_plan(tool_case):
    c = tool_case
    revision = await dispatched(c)
    ref = await receipt(c)
    await register_lookup(c, ref)
    before = await original_execution_rows(c)
    results = await asyncio.wait_for(
        asyncio.gather(
            *(facade(restarted(c)).reconcile(request(c, revision), c.ctx) for _ in range(3))
        ),
        15,
    )
    assert all(r == results[0] and r["kind"] == "ok" for r in results)
    assert (await c.budget.get_ledger(c.ctx))["used"]["money"] == "0.03"
    assert await original_execution_rows(c) == before


async def test_sql_facade_cancel_and_revoke_execution_allows_current_recovery_data(tool_case):
    c = tool_case
    revision = await dispatched(c)
    ref = await receipt(c, outcome="not_applied")
    await register_lookup(c, ref)
    row = await c.ledger.store.get(
        c.ctx.principal, "execution.policies", c.ctx.capability_policy_ref.id
    )
    await c.ledger.store.put(
        c.ctx.principal,
        "execution.policies",
        row.resource_id,
        "CapabilityPolicy",
        {**row.payload, "revision": row.revision + 1, "denied_capabilities": ["tool.invoke"]},
        expected_revision=row.revision,
        request_id="fixture-recovery-policy-revoked",
    )
    await cancel(c)
    before = await original_execution_rows(c)
    f = facade(restarted(c))
    assert (await f.reconcile(request(c, revision), c.ctx))["kind"] == "ok"
    assert (await f.read_outcome(c.call["action_id"], c.ctx))["outcome"] == "not_applied"
    assert await original_execution_rows(c) == before
    with pytest.raises(DomainError):
        await c.budget.mark_dispatch(c.ctx)


@pytest.mark.parametrize("source", ["lookup", "reader", "evidence"])
async def test_sql_facade_current_source_revocation_is_not_cached(tool_case, source):
    c = tool_case
    revision = await dispatched(c)
    ref = await receipt(c)
    await register_lookup(c, ref)
    f = facade(c)
    assert (await f.reconcile(request(c, revision), c.ctx))["kind"] == "ok"
    before = await c.budget.get_ledger(c.ctx)
    port = {"lookup": f.lookup, "reader": f.reconciler.receipts, "evidence": f.reconciler.evidence}[
        source
    ]
    port.allowed = False
    result = await f.reconcile(request(c, revision), c.ctx)
    assert result["kind"] == "denied" and await c.budget.get_ledger(c.ctx) == before
    if source != "lookup":
        with pytest.raises(DomainError) as error:
            await f.read_outcome(c.call["action_id"], c.ctx)
        assert error.value.status_code == 403
    else:
        assert (await f.read_outcome(c.call["action_id"], c.ctx))["outcome"] == "applied"


async def test_sql_outcome_pinned_body_conflict_rejected_after_acceptance(tool_case):
    c = tool_case
    revision = await dispatched(c)
    ref = await receipt(c)
    await register_lookup(c, ref)
    f = facade(c)
    assert (await f.reconcile(request(c, revision), c.ctx))["kind"] == "ok"
    before = await c.budget.get_ledger(c.ctx)
    real = f.reconciler.receipts

    class ChangedSameVersionReader:
        async def read(self, ref, ctx):
            actual = await real.read(ref, ctx)
            actual["usage"]["resources"]["money"] = "0.04"
            return actual

    f.reconciler.receipts = ChangedSameVersionReader()
    with pytest.raises(DomainError) as error:
        await f.read_outcome(c.call["action_id"], c.ctx)
    assert (
        error.value.failure.code == "receipt_conflict"
        and await c.budget.get_ledger(c.ctx) == before
    )


async def test_sql_outcome_readable_before_fee_response_recovery(tool_case):
    c = tool_case
    revision = await dispatched(c)
    ref = await receipt(c, outcome="not_applied")
    await register_lookup(c, ref)
    actual = BudgetService(c.ledger.store)

    class LoseFeeReply:
        async def settle(self, *args, **kwargs):
            await actual.settle(*args, **kwargs)
            raise TimeoutError("Controlled response loss after actual fee commit")

    budget = ToolBudgetAdapter(c.ledger, LoseFeeReply(), state=actual)
    f = facade(c, budget=budget)
    assert (await f.reconcile(request(c, revision), c.ctx))["kind"] == "failed"
    assert (await f.read_outcome(c.call["action_id"], c.ctx))["outcome"] == "not_applied"
    before = await actual.get_ledger(c.ctx)
    assert (await facade(restarted(c)).reconcile(request(c, revision), c.ctx))["kind"] == "ok"
    assert await actual.get_ledger(c.ctx) == before


async def test_sql_facade_read_outcome_does_not_follow_unaccepted_lookup(tool_case):
    c = tool_case
    revision = await dispatched(c)
    old = await receipt(c, name="accepted-source", outcome="unknown")
    await register_lookup(c, old)
    f = facade(c)
    result = await f.reconcile(request(c, revision), c.ctx)
    assert result["kind"] == "ok"
    new = await receipt(c, name="unaccepted-new-source", outcome="applied")
    await register_lookup(c, new)
    actual = await f.read_outcome(c.call["action_id"], c.ctx)
    assert actual["receipt_ref"] == old.wire() and actual["outcome"] == "unknown"
    assert f.lookup.calls == 1


async def test_sql_facade_new_process_looks_up_original_receipt_without_wire_ref(tool_case):
    import json
    import subprocess
    import sys
    from pathlib import Path

    c = tool_case
    revision = await dispatched(c)
    ref = await receipt(c, outcome="not_applied")
    await register_lookup(c, ref)
    first = await facade(c).reconcile(request(c, revision), c.ctx)
    assert first["kind"] == "ok"
    before = await c.budget.get_ledger(c.ctx)
    child = Path(__file__).with_name("recovery_facade_child.py")
    data = json.dumps({"context": c.ctx.wire(), "request": request(c, revision)})
    completed = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-m", "tests.integration.tool.recovery_facade_child"],
        input=data,
        text=True,
        capture_output=True,
        timeout=30,
        cwd=child.parents[3],
    )
    assert completed.returncode == 0
    assert json.loads(completed.stdout) == {
        "kind": "ok",
        "outcome": "not_applied",
        "failure_code": None,
    }
    assert await c.budget.get_ledger(c.ctx) == before
