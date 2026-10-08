"""Controlled phase/Reader protocol fixtures only, never SQL or provider evidence."""

import asyncio
from copy import deepcopy
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.db.transactions import reference
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError, reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreConflict, StoreMissing
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.invocation.schema import normalize
from uaw.tool.ledger import ToolLedger, action_key
from uaw.tool.reconciliation import ToolReconciler


def resources():
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "model_calls": 0,
        "tool_calls": 1,
        "child_agents": 0,
        "wall_time_ms": 100,
        "money": "0.01",
        "currency": "USD",
    }


class PhaseStoreFixture:
    def __init__(self):
        self.database = None
        self.rows = {}

    async def get(self, principal, namespace, key):
        assert namespace.startswith("tool.")
        if (namespace, key) not in self.rows:
            raise StoreMissing()
        return deepcopy(self.rows[(namespace, key)])

    def put(self, namespace, key, schema, payload, revision=1):
        validate_contract(schema, payload)
        self.rows[(namespace, key)] = SimpleNamespace(
            payload=deepcopy(payload), revision=revision, resource_id=key, schema_name=schema
        )


class TransactionsFixture:
    def __init__(self, store):
        self.store, self.lock = store, asyncio.Lock()

    async def inspect(self, owner, aggregate, callback):
        # Test substitution for transaction rollback/serialization, not PostgreSQL.
        async with self.lock:
            before = deepcopy(self.store.rows)

            async def load(namespace, key):
                return await self.store.get(owner, namespace, key)

            async def write(namespace, key, schema, payload, expected=0):
                previous = self.store.rows.get((namespace, key))
                if (previous.revision if previous else 0) != expected:
                    raise StoreConflict()
                self.store.put(namespace, key, schema, payload, expected + 1)
                return await load(namespace, key)

            try:
                return await callback(SimpleNamespace(load=load, write=write))
            except BaseException:
                self.store.rows = before
                raise


class FeeFixture:
    def __init__(self, ctx):
        self.ctx = ctx
        self.reservation = {
            "id": "unit-reservation",
            "estimates": resources(),
            "settled_usage_refs": [],
            "status": "reserved",
            "revision": 1,
        }
        self.ledger = {
            "id": ctx.run_id,
            "run_id": ctx.run_id,
            "revision": 3,
            "limits": resources(),
            "held": resources(),
            "used": {**resources(), "tool_calls": 0},
            "deadline": ctx.deadline,
            "billing_pending": True,
            "overdrawn": False,
            "cancel_requested": False,
        }
        self.requests, self.calls, self.commits = {}, 0, 0
        self.lose_reply = False
        self.reads = 0

    async def get_ledger(self, ctx):
        self.reads += 1
        return deepcopy(self.ledger)

    async def get_reservation(self, identifier, ctx):
        assert identifier == "unit-reservation" and ctx == self.ctx
        return deepcopy(self.reservation)

    async def reserve(self, *args):
        raise AssertionError("Reconciliation must never reserve a new action")

    async def dispatch(self, *args):
        raise AssertionError("Reconciliation must never dispatch or infer a send")

    async def settle(self, actor, request, meta, ctx, *, status):
        self.calls += 1
        signature = parameter_hash({"request": request, "status": status, "context": ctx.wire()})
        if meta.request_id in self.requests:
            old, result = self.requests[meta.request_id]
            if old != signature:
                raise StoreConflict("idempotency_conflict")
            return deepcopy(result)
        if request["expected_ledger_revision"] != self.ledger["revision"]:
            raise StoreConflict()
        assert request["usage"]["attempt_id"] == ctx.attempt_id
        self.commits += 1
        self.reservation["revision"] += 1
        self.ledger["revision"] += 1
        result = {
            "reservation_ref": reference(
                "reservation", "unit-reservation", self.reservation["revision"]
            ),
            "usage_refs": [reference("usage", "unit-usage", self.commits)],
            "remaining": resources(),
            "revision": self.ledger["revision"],
            "billing_pending": request["usage"]["billing_state"] != "confirmed",
        }
        validate_contract("UsageSettlement", result)
        self.requests[meta.request_id] = (signature, deepcopy(result))
        if self.lose_reply:
            self.lose_reply = False
            raise TimeoutError("Controlled response loss after fixture fee commit")
        return result


class ReaderFixture:
    def __init__(self, receipt):
        self.value = receipt
        self.allowed = True
        self.reads = 0

    async def read(self, ref, ctx):
        self.reads += 1
        if not self.allowed:
            raise reject("source_revoked", "Source no longer accessible", 403, "authorization")
        return deepcopy(self.value)


class EvidenceFixture:
    def __init__(self):
        self.allowed = True
        self.version = None
        self.checks = 0

    async def check(self, ref, ctx):
        self.checks += 1
        if not self.allowed:
            raise reject("evidence_revoked", "Evidence no longer accessible", 403, "authorization")
        return ref if self.version is None else ref.model_copy(update={"version": self.version})


@pytest.fixture
def reconciliation_case(ctx, registry, call, spec):
    fixed = normalize(call, registry)
    key = action_key(ctx, fixed["action_id"])
    store = PhaseStoreFixture()
    store.put("tool.calls", key, "ValidatedCall", fixed)
    store.put("tool.specs", key, "ToolSpec", spec)
    store.put("tool.contexts", key, "TrustedExecutionContext", ctx.wire())
    store.put("tool.attempt.calls", ctx.attempt_id, "ValidatedCall", fixed)
    store.put("tool.attempt.contexts", ctx.attempt_id, "TrustedExecutionContext", ctx.wire())
    store.put(
        "tool.effects",
        key,
        "EffectRecord",
        {
            "action_id": fixed["action_id"],
            "arguments_hash": fixed["arguments_hash"],
            "provider_ref": spec["provider_ref"],
            "attempt_ids": [ctx.attempt_id],
            "state": "unknown",
            "revision": 2,
        },
        revision=2,
    )
    store.put(
        "tool.dispatch.intents",
        key,
        "InternalToolInvocationDispatchRequest",
        {
            "validated_action_ref": reference("tool_call", key),
            "reservation_ref": reference("reservation", "unit-reservation"),
            "provider_binding_ref": spec["provider_ref"],
        },
    )
    fee = FeeFixture(ctx)
    store.put("tool.budget.reserved", ctx.attempt_id, "BudgetReservation", fee.reservation)
    ledger = ToolLedger(store)
    ledger.transactions = TransactionsFixture(store)
    receipt_ref = Ref(kind="trace", id="unit-receipt", version="1")
    actual = {
        "action_ref": reference("tool_call", key),
        "attempt_id": ctx.attempt_id,
        "provider_ref": spec["provider_ref"],
        "receipt_ref": receipt_ref.wire(),
        "outcome": "applied",
        "evidence_refs": [{"kind": "input", "id": "unit-evidence", "version": "1"}],
        "usage": {
            "attempt_id": ctx.attempt_id,
            "billing_state": "pending",
            "resources": {"currency": "USD"},
        },
        "observed_at": datetime.now(UTC).isoformat(),
    }
    reader, evidence = ReaderFixture(actual), EvidenceFixture()
    budget = ToolBudgetAdapter(ledger, fee, state=fee)
    reconciler = ToolReconciler(ledger, budget, receipts=reader, evidence=evidence)
    return SimpleNamespace(
        ctx=ctx,
        ledger=ledger,
        store=store,
        fee=fee,
        ref=receipt_ref,
        receipt=actual,
        reader=reader,
        evidence=evidence,
        reconciler=reconciler,
        budget=budget,
    )


async def test_fixture_receipt_repeated_and_concurrent_calls_use_one_fee_plan(reconciliation_case):
    c = reconciliation_case
    results = await asyncio.gather(
        *(c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2) for _ in range(3))
    )
    assert all(r["kind"] == "ok" and r == results[0] for r in results)
    assert c.fee.commits == 1 and results[0]["revision"] == 3
    validate_contract("RuntimeToolruntimeReconcileResult", results[0])
    assert c.evidence.checks >= 3


async def test_fixture_lost_fee_response_resumes_persisted_inputs_without_new_admission(
    reconciliation_case,
):
    c = reconciliation_case
    c.fee.lose_reply = True
    first = await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2)
    assert first["failure"]["code"] == "reconciliation_interrupted"
    assert (await c.ledger.effect_from_attempt(c.ctx))["state"] == "confirmed"
    second = await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2)
    assert second["kind"] == "ok" and c.fee.commits == 1 and c.fee.calls == 2


@pytest.mark.parametrize(
    "field", ["action_ref", "attempt_id", "provider_ref", "receipt_ref", "usage"]
)
async def test_fixture_binding_tampering_has_no_effect_or_fee_commit(reconciliation_case, field):
    c = reconciliation_case
    if field == "usage":
        c.reader.value["usage"]["attempt_id"] = "untrusted"
    elif field == "attempt_id":
        c.reader.value[field] = "untrusted"
    else:
        c.reader.value[field]["version"] = "untrusted"
    result = await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2)
    assert result["failure"]["code"] == "receipt_binding_conflict"
    assert (await c.ledger.effect_from_attempt(c.ctx))["state"] == "unknown"
    assert c.fee.commits == 0


async def test_fixture_unreadable_or_changed_evidence_never_confirms_effect(reconciliation_case):
    c = reconciliation_case
    c.evidence.allowed = False
    assert (await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2))["kind"] == "denied"
    c.evidence.allowed, c.evidence.version = True, "changed"
    assert (await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2))["kind"] == "stale"
    assert c.fee.commits == 0


async def test_fixture_receipt_contents_conflict_at_same_version_and_known_effect_cannot_reverse(
    reconciliation_case,
):
    c = reconciliation_case
    first = await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2)
    c.reader.value["outcome"] = "not_applied"
    conflict = await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=first["revision"])
    assert conflict["failure"]["code"] == "receipt_conflict"
    ref = c.ref.model_copy(update={"version": "2"})
    c.reader.value["receipt_ref"] = ref.wire()
    conflict = await c.reconciler.reconcile(ref, c.ctx, expected_revision=first["revision"])
    assert conflict["failure"]["code"] == "receipt_conflict"
    assert (await c.ledger.effect_from_attempt(c.ctx)) == first["payload"] and c.fee.commits == 1


async def test_fixture_new_effect_proof_with_identical_fees_reuses_actual_settlement(
    reconciliation_case,
):
    c = reconciliation_case
    c.reader.value["outcome"], c.reader.value["evidence_refs"] = "unknown", []
    first = await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2)
    c.reader.value["outcome"] = "applied"
    c.reader.value["evidence_refs"] = [{"kind": "input", "id": "unit-evidence", "version": "1"}]
    ref = c.ref.model_copy(update={"version": "2"})
    c.reader.value["receipt_ref"] = ref.wire()
    result = await c.reconciler.reconcile(ref, c.ctx, expected_revision=first["revision"])
    assert result["payload"]["state"] == "confirmed" and c.fee.commits == 1


async def test_fixture_pending_plan_blocks_other_receipt_until_response_recovery(
    reconciliation_case,
):
    c = reconciliation_case
    c.fee.lose_reply = True
    assert (await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2))["kind"] == "failed"
    second = c.ref.model_copy(update={"version": "2"})
    c.reader.value["receipt_ref"] = second.wire()
    result = await c.reconciler.reconcile(second, c.ctx, expected_revision=3)
    assert result["failure"]["code"] == "reconciliation_pending" and c.fee.commits == 1


@pytest.mark.parametrize("revision", [True, -1, "2", 2.0])
async def test_fixture_effect_cas_revision_is_strict(reconciliation_case, revision):
    c = reconciliation_case
    result = await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=revision)
    assert result["failure"]["code"] == "invalid_arguments" and c.fee.commits == 0


async def test_fixture_wrong_effect_cas_and_unclaimed_receipt_do_not_settle(reconciliation_case):
    c = reconciliation_case
    result = await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=8)
    assert result["failure"]["code"] == "revision_conflict"
    c.store.rows.pop(("tool.dispatch.intents", action_key(c.ctx, "action-c")))
    result = await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2)
    assert result["failure"]["code"] == "receipt_binding_conflict" and c.fee.commits == 0


async def test_fixture_missing_receipt_evidence_or_budget_state_is_unavailable(reconciliation_case):
    c = reconciliation_case
    no_receipt = ToolReconciler(c.ledger, c.budget)
    assert (await no_receipt.reconcile(c.ref, c.ctx, expected_revision=2))["failure"][
        "code"
    ] == "dependency_unavailable"
    no_evidence = ToolReconciler(c.ledger, c.budget, receipts=c.reader)
    assert (await no_evidence.reconcile(c.ref, c.ctx, expected_revision=2))["failure"][
        "code"
    ] == "dependency_unavailable"
    missing_state = ToolBudgetAdapter(c.ledger, c.fee)
    no_state = ToolReconciler(c.ledger, missing_state, receipts=c.reader, evidence=c.evidence)
    assert (await no_state.reconcile(c.ref, c.ctx, expected_revision=2))["failure"][
        "code"
    ] == "dependency_unavailable"
    assert c.fee.commits == 0


async def test_fixture_cancelled_recovery_read_is_not_an_admission(reconciliation_case):
    c = reconciliation_case
    c.fee.ledger["cancel_requested"] = True
    result = await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2)
    assert result["kind"] == "ok"
    with pytest.raises(DomainError):
        await c.budget.reserve(resources(), c.ctx)


async def test_fixture_receipt_contract_does_not_allow_self_reported_approval_or_empty_proof(
    reconciliation_case,
):
    c = reconciliation_case
    c.reader.value["approved"] = True
    result = await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2)
    assert result["failure"]["code"] == "dependency_protocol_invalid"
    c.reader.value.pop("approved")
    c.reader.value["evidence_refs"] = []
    assert (await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2))["kind"] == "failed"
    assert c.fee.commits == 0


async def test_fixture_source_revoked_during_evidence_await_does_not_commit(reconciliation_case):
    c = reconciliation_case
    original = c.evidence.check

    async def revoke(ref, ctx):
        actual = await original(ref, ctx)
        c.reader.allowed = False
        return actual

    c.evidence.check = revoke
    result = await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2)
    assert result["kind"] == "denied" and c.fee.commits == 0
    assert (await c.ledger.effect_from_attempt(c.ctx))["state"] == "unknown"


async def test_fixture_task_cancellation_retains_fixed_plan_and_effect_truth(reconciliation_case):
    c = reconciliation_case
    original = c.fee.settle

    async def interrupted(*args, **kwargs):
        raise asyncio.CancelledError()

    c.fee.settle = interrupted
    with pytest.raises(asyncio.CancelledError):
        await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2)
    assert (await c.ledger.effect_from_attempt(c.ctx))["state"] == "confirmed"
    assert c.fee.commits == 0
    c.fee.settle = original
    assert (await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2))["kind"] == "ok"
    assert c.fee.commits == 1


async def test_fixture_foreign_settlement_ref_is_not_saved_as_own_fee_completion(
    reconciliation_case,
):
    c = reconciliation_case
    original = c.fee.settle

    async def cross_response(*args, **kwargs):
        result = await original(*args, **kwargs)
        return {**result, "reservation_ref": reference("reservation", "other-reservation", 2)}

    c.fee.settle = cross_response
    result = await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2)
    assert result["failure"]["code"] == "dependency_protocol_invalid"
    key = c.ledger.receipt_key(c.receipt)
    assert await c.ledger.get("tool.reconciliation.settled", key, c.ctx) is None
    assert (await c.ledger.effect_from_attempt(c.ctx))["state"] == "confirmed"
    c.fee.settle = original
    assert (await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2))["kind"] == "ok"
    assert c.fee.commits == 1
