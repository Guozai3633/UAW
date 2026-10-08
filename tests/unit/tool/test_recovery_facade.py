"""Controlled lookup/Reader fixtures; no SQL, provider or product capability claim."""

import asyncio
from copy import deepcopy

import pytest

from tests.unit.tool.test_reconciliation import reconciliation_case as reconciliation_case
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError, reject
from uaw.shared.schema import validate_contract
from uaw.tool.facade import ToolFacade
from uaw.tool.ledger import action_key
from uaw.tool.reconciliation import ToolReconciler


class RegisteredLookupFixture:
    """Independent controlled registration, never inferred from effect/fee state."""

    def __init__(self, case):
        self.ctx, self.action, self.ref = case.ctx, "action-c", case.ref
        self.allowed, self.found, self.calls = True, True, 0

    async def find(self, action_id, ctx):
        self.calls += 1
        if not self.allowed or ctx != self.ctx or action_id != self.action:
            raise reject(
                "lookup_revoked", "Controlled recovery source denied", 403, "authorization"
            )
        return self.ref if self.found else None


class NoAdmissionFixture:
    async def snapshot(self, ctx):
        raise AssertionError("Recovery must not call new-execution _access")


def facade(case, registry, lookup=None, reconciler=None):
    return ToolFacade(
        registry,
        NoAdmissionFixture(),
        lookup=lookup or RegisteredLookupFixture(case),
        reconciler=reconciler or case.reconciler,
    )


def request(revision=2):
    return {"action_id": "action-c", "expected_revision": revision}


def phases(case):
    return deepcopy(case.store.rows)


async def test_facade_lookup_reconcile_and_explicit_not_applied_outcome(
    reconciliation_case, registry
):
    c = reconciliation_case
    c.reader.value["outcome"] = "not_applied"
    f = facade(c, registry)
    result = await f.reconcile(request(), c.ctx)
    validate_contract("RuntimeToolruntimeReconcileResult", result)
    assert result["kind"] == "ok" and result["payload"]["state"] == "confirmed"
    actual = await f.read_outcome("action-c", c.ctx)
    validate_contract("ToolReconciliationReceipt", actual)
    assert actual["outcome"] == "not_applied" and actual["usage"]["billing_state"] == "pending"
    assert c.fee.commits == 1
    actual["outcome"] = "applied"
    assert (await f.read_outcome("action-c", c.ctx))["outcome"] == "not_applied"
    assert c.fee.commits == 1 and f.lookup.calls == 1


@pytest.mark.parametrize("ports", ["none", "lookup", "reconciler"])
async def test_facade_missing_optional_ports_is_unavailable(reconciliation_case, registry, ports):
    c = reconciliation_case
    f = ToolFacade(
        registry,
        lookup=RegisteredLookupFixture(c) if ports == "lookup" else None,
        reconciler=c.reconciler if ports == "reconciler" else None,
    )
    before = phases(c)
    result = await f.reconcile(request(), c.ctx)
    assert result["failure"]["code"] == "dependency_unavailable" and phases(c) == before
    assert c.fee.calls == 0
    if ports != "reconciler":
        with pytest.raises(DomainError) as error:
            await f.read_outcome("action-c", c.ctx)
        assert error.value.failure.code == "dependency_unavailable"


@pytest.mark.parametrize(
    "bad",
    [
        {**request(), "receipt_ref": {"kind": "trace", "id": "arbitrary", "version": "1"}},
        {**request(), "expected_revision": True},
        {**request(), "expected_revision": 2.0},
        {**request(), "expected_revision": "2"},
        {**request(), "expected_revision": -1},
        {"action_id": "action-c"},
        {**request(), "approved": True},
    ],
)
async def test_facade_strict_request_rejected_before_lookup(reconciliation_case, registry, bad):
    c = reconciliation_case
    f = facade(c, registry)
    before = phases(c)
    result = await f.reconcile(bad, c.ctx)
    assert result["failure"]["code"] == "invalid_arguments" and f.lookup.calls == 0
    assert phases(c) == before and c.fee.calls == 0


async def test_facade_no_readable_source_preserves_unknown_and_existing_fee_plan(
    reconciliation_case, registry
):
    c = reconciliation_case
    f = facade(c, registry)
    before = phases(c)
    f.lookup.found = False
    result = await f.reconcile(request(), c.ctx)
    assert result["kind"] == "missing" and result["failure"]["code"] == "receipt_missing"
    assert phases(c) == before and c.fee.calls == 0
    with pytest.raises(DomainError) as error:
        await f.read_outcome("action-c", c.ctx)
    assert error.value.failure.code == "receipt_missing"


@pytest.mark.parametrize("bad_ref", [{"kind": "trace", "id": "raw", "version": "1"}, "raw"])
async def test_facade_lookup_must_return_ref_not_caller_wire(
    reconciliation_case, registry, bad_ref
):
    c = reconciliation_case
    f = facade(c, registry)
    f.lookup.ref = bad_ref
    result = await f.reconcile(request(), c.ctx)
    assert result["failure"]["code"] == "dependency_protocol_invalid" and c.fee.calls == 0


async def test_facade_action_or_original_attempt_mismatch_rejected_before_lookup(
    reconciliation_case, registry
):
    c = reconciliation_case
    f = facade(c, registry)
    for req, ctx in (
        ({**request(), "action_id": "other-action"}, c.ctx),
        (request(), c.ctx.model_copy(update={"attempt_id": "other-attempt"})),
        (request(), c.ctx.model_copy(update={"run_id": "other-run"})),
    ):
        result = await f.reconcile(req, ctx)
        assert result["kind"] in {"conflict", "missing"}
    assert f.lookup.calls == 0 and c.fee.calls == 0


@pytest.mark.parametrize("field", ["action_ref", "attempt_id", "provider_ref", "usage"])
async def test_facade_lookup_never_authorizes_bad_receipt_binding(
    reconciliation_case, registry, field
):
    c = reconciliation_case
    if field in {"action_ref", "provider_ref"}:
        c.reader.value[field]["id"] = "other"
    elif field == "usage":
        c.reader.value[field]["attempt_id"] = "other"
    else:
        c.reader.value[field] = "other"
    result = await facade(c, registry).reconcile(request(), c.ctx)
    assert result["failure"]["code"] == "receipt_binding_conflict" and c.fee.calls == 0


async def test_facade_replay_after_response_loss_keeps_original_attempt_and_fixed_plan(
    reconciliation_case, registry
):
    c = reconciliation_case
    before = set(c.store.rows)
    c.fee.lose_reply = True
    first = await facade(c, registry).reconcile(request(), c.ctx)
    assert first["failure"]["code"] == "reconciliation_interrupted"
    fresh = ToolReconciler(c.ledger, c.budget, receipts=c.reader, evidence=c.evidence)
    f = facade(c, registry, reconciler=fresh)
    assert (await f.read_outcome("action-c", c.ctx))["outcome"] == "applied"
    assert (await f.reconcile(request(), c.ctx))["kind"] == "ok"
    assert c.fee.commits == 1 and c.fee.calls == 2
    new_keys = set(c.store.rows) - before
    assert all(namespace.startswith("tool.reconciliation.") for namespace, _ in new_keys)
    calls = c.fee.calls
    result = await f.reconcile(request(), c.ctx)
    assert result["kind"] == "ok" and c.fee.calls == calls


@pytest.mark.parametrize("source", ["lookup", "reader", "evidence"])
async def test_facade_current_source_revocation_never_uses_cached_permission(
    reconciliation_case, registry, source
):
    c = reconciliation_case
    f = facade(c, registry)
    assert (await f.reconcile(request(), c.ctx))["kind"] == "ok"
    before = phases(c)
    port = {"lookup": f.lookup, "reader": c.reader, "evidence": c.evidence}[source]
    port.allowed = False
    result = await f.reconcile(request(), c.ctx)
    assert result["kind"] == "denied" and phases(c) == before
    if source != "lookup":
        with pytest.raises(DomainError) as error:
            await f.read_outcome("action-c", c.ctx)
        assert error.value.status_code == 403
    else:
        # Accepted outcome reading is pinned to the receipt, not new lookup availability.
        assert (await f.read_outcome("action-c", c.ctx))["outcome"] == "applied"
    assert c.fee.commits == 1


async def test_facade_cancelled_run_recovery_never_calls_admission(reconciliation_case, registry):
    c = reconciliation_case
    c.fee.ledger["cancel_requested"] = True
    f = facade(c, registry)
    assert (await f.reconcile(request(), c.ctx))["kind"] == "ok"
    assert (await f.read_outcome("action-c", c.ctx))["attempt_id"] == c.ctx.attempt_id


async def test_outcome_no_accepted_receipt_is_not_inferred_from_confirmed(reconciliation_case):
    c = reconciliation_case
    key = action_key(c.ctx, "action-c")
    c.store.rows[("tool.effects", key)].payload["state"] = "confirmed"
    with pytest.raises(DomainError) as error:
        await c.reconciler.read_outcome("action-c", c.ctx)
    assert error.value.failure.code == "receipt_missing" and c.reader.reads == 0


@pytest.mark.parametrize("change", ["body", "binding", "evidence", "active", "no_reader"])
async def test_outcome_rechecks_exact_accepted_body_sources_and_binding(
    reconciliation_case, change
):
    c = reconciliation_case
    assert (await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2))["kind"] == "ok"
    if change == "body":
        c.reader.value["usage"]["resources"]["tool_calls"] = 1
    elif change == "binding":
        c.reader.value["provider_ref"]["id"] = "other-provider"
    elif change == "evidence":
        c.evidence.version = "changed"
    elif change == "active":
        c.store.rows[("tool.reconciliation.active", c.ctx.attempt_id)].payload["outcome"] = (
            "unknown"
        )
    else:
        c.reconciler.receipts = None
    with pytest.raises(DomainError) as error:
        await c.reconciler.read_outcome("action-c", c.ctx)
    assert error.value.failure.code in {
        "receipt_conflict",
        "receipt_binding_conflict",
        "receipt_version_stale",
        "dependency_unavailable",
    }
    assert c.fee.commits == 1


async def test_outcome_returns_accepted_version_without_using_new_lookup(
    reconciliation_case, registry
):
    c = reconciliation_case
    f = facade(c, registry)
    assert (await f.reconcile(request(), c.ctx))["kind"] == "ok"
    f.lookup.ref = Ref(kind="trace", id="unaccepted-new-source", version="2")
    assert (await f.read_outcome("action-c", c.ctx))["receipt_ref"] == c.ref.wire()
    assert f.lookup.calls == 1


async def test_outcome_source_revocation_during_evidence_read_is_denied(reconciliation_case):
    c = reconciliation_case
    assert (await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2))["kind"] == "ok"
    original = c.evidence.check

    async def revoked(ref, ctx):
        actual = await original(ref, ctx)
        c.reader.allowed = False
        return actual

    c.evidence.check = revoked
    with pytest.raises(DomainError) as error:
        await c.reconciler.read_outcome("action-c", c.ctx)
    assert error.value.status_code == 403 and c.fee.commits == 1


async def test_lookup_timeout_or_cancellation_never_infers_outcome(reconciliation_case, registry):
    c = reconciliation_case
    f = facade(c, registry)
    before = phases(c)

    async def timed_out(*args):
        raise TimeoutError("Controlled unresolved lookup")

    f.lookup.find = timed_out
    result = await f.reconcile(request(), c.ctx)
    assert result["failure"]["code"] == "reconciliation_interrupted"

    async def cancelled(*args):
        raise asyncio.CancelledError()

    f.lookup.find = cancelled
    with pytest.raises(asyncio.CancelledError):
        await f.reconcile(request(), c.ctx)
    assert phases(c) == before and c.fee.calls == 0


async def test_request_is_fixed_before_lookup_await(reconciliation_case, registry):
    c = reconciliation_case
    f = facade(c, registry)
    req = request()
    original = f.lookup.find

    async def mutate(action_id, ctx):
        req["action_id"], req["expected_revision"] = "other-action", 100
        return await original(action_id, ctx)

    f.lookup.find = mutate
    assert (await f.reconcile(req, c.ctx))["kind"] == "ok"


async def test_outcome_concurrent_effect_update_refuses_superseded_observation(reconciliation_case):
    c = reconciliation_case
    assert (await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2))["kind"] == "ok"
    original = c.evidence.check

    async def supersede(ref, ctx):
        actual = await original(ref, ctx)
        c.store.rows[("tool.effects", action_key(ctx, "action-c"))].payload["revision"] += 1
        return actual

    c.evidence.check = supersede
    with pytest.raises(DomainError) as error:
        await c.reconciler.read_outcome("action-c", c.ctx)
    assert error.value.failure.code == "receipt_version_stale"


async def test_outcome_read_does_not_touch_budget_or_require_catalogue(reconciliation_case):
    from uaw.tool.registry import ToolRegistry

    c = reconciliation_case
    c.reader.value["outcome"], c.reader.value["evidence_refs"] = "unknown", []
    assert (await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2))["kind"] == "ok"
    reads, calls, before = c.fee.reads, c.fee.calls, phases(c)
    # Even billing recovery needs no new product catalogue or flag activation.
    f = ToolFacade(ToolRegistry(), reconciler=c.reconciler)
    actual = await f.read_outcome("action-c", c.ctx)
    assert actual["outcome"] == "unknown" and actual["usage"]["billing_state"] == "pending"
    assert c.fee.reads == reads and c.fee.calls == calls and phases(c) == before


async def test_outcome_fee_rejection_keeps_accepted_effect_readable(reconciliation_case, registry):
    c = reconciliation_case
    c.reader.value["outcome"] = "not_applied"

    async def denied_fees(*args, **kwargs):
        raise reject("usage_reconciliation_denied", "Controlled definite fee rejection", 409)

    c.fee.settle = denied_fees
    f = facade(c, registry)
    rejected = await f.reconcile(request(), c.ctx)
    assert rejected["failure"]["code"] == "usage_reconciliation_denied"
    effect = await c.ledger.effect_from_attempt(c.ctx)
    assert effect["state"] == "confirmed" and c.fee.commits == 0
    actual = await f.read_outcome("action-c", c.ctx)
    assert actual["outcome"] == "not_applied" and actual["usage"]["billing_state"] == "pending"


async def test_outcome_timeout_does_not_change_accepted_effect_or_fees(reconciliation_case):
    c = reconciliation_case
    assert (await c.reconciler.reconcile(c.ref, c.ctx, expected_revision=2))["kind"] == "ok"
    before = phases(c)

    async def timed_out(*args):
        raise TimeoutError("Controlled source response loss")

    c.reader.read = timed_out
    with pytest.raises(DomainError) as error:
        await c.reconciler.read_outcome("action-c", c.ctx)
    assert error.value.failure.code == "reconciliation_interrupted"
    assert phases(c) == before and c.fee.commits == 1
