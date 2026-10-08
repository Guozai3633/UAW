"""Actual PostgreSQL coordination and stale-worker fencing, no Runner execution."""

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta, prepared_budget
from uaw.infrastructure.db.transactions import reference
from uaw.run.leases import NAMESPACE, ExecutionLeaseService
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, DomainError
from uaw.shared.schema import ContractViolation
from uaw.shared.stores import StoreConflict, StoreMissing


@pytest.fixture
async def leases(domain, principal):
    record, budgets, ctx, _ = await prepared_budget(domain, principal)
    clock = [datetime.now(UTC)]
    holder = Principal(id="execution-worker", kind="service", auth_session_id="worker-session")
    return SimpleNamespace(
        service=ExecutionLeaseService(budgets.store, clock=lambda: clock[0]),
        ctx=ctx,
        holder=holder,
        clock=clock,
        record=record,
        run=domain[1],
    )


async def acquire(s, request_id="lease-acquire", **request):
    return await s.service.acquire(
        {"lease_ttl_ms": 30000, "expected_revision": 0, **request},
        meta(request_id),
        s.ctx,
        holder=s.holder,
    )


def change(lease, **extra):
    return {
        "lease_ref": reference("lease", lease["id"], lease["revision"]),
        "fencing_token": lease["fencing_token"],
        **extra,
    }


async def test_lease_persistent_restart_current_and_same_request_replay(leases):
    s = leases
    lease = await acquire(s)
    assert lease["revision"] == lease["fencing_token"] == 1
    s.service = ExecutionLeaseService(s.service.store, clock=lambda: s.clock[0])
    assert await acquire(s) == lease
    assert (
        await s.service.current(
            Ref.model_validate(change(lease)["lease_ref"]), 1, s.ctx, holder=s.holder
        )
        == lease
    )


async def test_two_services_compete_for_one_root_lease(leases):
    s = leases
    other = ExecutionLeaseService(s.service.store, clock=lambda: s.clock[0])
    results = await asyncio.gather(
        acquire(s),
        other.acquire(
            {"lease_ttl_ms": 30000, "expected_revision": 0},
            meta("other-acquire"),
            s.ctx,
            holder=s.holder.model_copy(update={"id": "other-worker"}),
        ),
        return_exceptions=True,
    )
    assert sum(isinstance(result, dict) for result in results) == 1
    assert sum(isinstance(result, StoreConflict) for result in results) == 1


async def test_renew_release_takeover_and_old_response_cannot_reauthorize(leases):
    s = leases
    first = await acquire(s)
    request = change(first, lease_ttl_ms=40000)
    renewed = await s.service.renew(request, meta("renew"), s.ctx, holder=s.holder)
    assert renewed["revision"] == 2 and renewed["fencing_token"] == 1
    assert await s.service.renew(request, meta("renew"), s.ctx, holder=s.holder) == renewed
    released = await s.service.release(change(renewed), meta("release"), s.ctx, holder=s.holder)
    assert released["state"] == "released" and released["lease"]["revision"] == 3
    assert (
        await s.service.release(change(renewed), meta("release"), s.ctx, holder=s.holder)
        == released
    )
    s.holder = s.holder.model_copy(update={"id": "new-worker"})
    current = await acquire(s, "takeover", expected_revision=3)
    assert current["revision"] == 4 and current["fencing_token"] == 2
    with pytest.raises(StoreConflict):
        await s.service.renew(
            request,
            meta("renew"),
            s.ctx,
            holder=s.holder.model_copy(update={"id": "execution-worker"}),
        )


async def test_observed_expiry_is_persistent_across_clock_rollback(leases):
    s = leases
    first = await acquire(s, lease_ttl_ms=1000)
    start = s.clock[0]
    s.clock[0] += timedelta(seconds=2)
    with pytest.raises(DomainError) as expired:
        await s.service.renew(
            change(first, lease_ttl_ms=1000), meta("expired-renew"), s.ctx, holder=s.holder
        )
    assert expired.value.failure.code == "lease_expired"
    stored = (await s.service.store.get(s.ctx.principal, NAMESPACE, first["id"])).payload
    assert stored["state"] == "expired"
    s.clock[0] = start
    with pytest.raises(DomainError) as rollback:
        await s.service.current(
            Ref.model_validate(change(stored["lease"])["lease_ref"]), 1, s.ctx, holder=s.holder
        )
    assert rollback.value.failure.code == "lease_expired"
    next_lease = await acquire(s, "expired-takeover", expected_revision=stored["lease"]["revision"])
    assert next_lease["fencing_token"] == 2


async def test_cancel_revokes_current_and_allows_release_without_new_admission(leases):
    s = leases
    first = await acquire(s)
    await s.run.control(
        s.ctx.principal,
        {
            "run_id": s.ctx.run_id,
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop"},
        },
        meta("cancel", 2),
    )
    released = await s.service.release(
        change(first), meta("release-cancelled"), s.ctx, holder=s.holder
    )
    assert released["state"] == "released"
    with pytest.raises(DomainError) as denied:
        await acquire(s, "new-after-cancel", expected_revision=2)
    assert denied.value.failure.code == "lease_revoked"


async def test_live_cancel_seals_lease_revocation(leases):
    s = leases
    first = await acquire(s)
    await s.run.control(
        s.ctx.principal,
        {
            "run_id": s.ctx.run_id,
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop"},
        },
        meta("cancel", 2),
    )
    with pytest.raises(DomainError) as denied:
        await s.service.current(
            Ref.model_validate(change(first)["lease_ref"]), 1, s.ctx, holder=s.holder
        )
    assert denied.value.failure.code == "lease_revoked"
    assert (await s.service.store.get(s.ctx.principal, NAMESPACE, first["id"])).payload[
        "state"
    ] == "revoked"


async def test_holder_session_scope_and_foreign_principal_are_not_reusable(leases):
    s = leases
    first = await acquire(s)
    pin = Ref.model_validate(change(first)["lease_ref"])
    with pytest.raises(DomainError) as wrong_holder:
        await s.service.current(
            pin, 1, s.ctx, holder=s.holder.model_copy(update={"auth_session_id": "other-session"})
        )
    assert wrong_holder.value.failure.code == "lease_holder_denied"
    ctx = s.ctx.model_copy(
        update={
            "scope": s.ctx.scope.model_copy(update={"conversation_id": "wrong"}),
            "conversation_id": "wrong",
        }
    )
    with pytest.raises(DomainError) as wrong_scope:
        await s.service.current(pin, 1, ctx, holder=s.holder)
    assert wrong_scope.value.failure.code == "lease_scope_denied"
    other = s.ctx.principal.model_copy(update={"id": "other-user"})
    with pytest.raises(StoreMissing):
        await s.service.current(
            pin,
            1,
            s.ctx.model_copy(
                update={
                    "principal": other,
                    "scope": s.ctx.scope.model_copy(update={"principal_id": other.id}),
                }
            ),
            holder=s.holder,
        )


async def test_lease_deadline_is_capped_and_waiting_lock_rechecks_time(leases):
    s = leases
    deadline = s.clock[0] + timedelta(seconds=1)
    s.ctx = s.ctx.model_copy(update={"deadline": deadline.isoformat()})
    first = await acquire(s, lease_ttl_ms=300000)
    assert first["expires_at"] == deadline.isoformat()
    await s.service.release(change(first), meta("release-before-lock"), s.ctx, holder=s.holder)
    entered, unlock = asyncio.Event(), asyncio.Event()

    async def lock(tx):
        entered.set()
        await unlock.wait()
        return {}

    locking = asyncio.create_task(
        s.service.transactions.inspect(
            s.ctx.principal, f"conversation:{s.ctx.scope.conversation_id}", lock
        )
    )
    await entered.wait()
    queued = asyncio.create_task(acquire(s, "queued-acquire", expected_revision=2))
    await asyncio.sleep(0)
    s.clock[0] = deadline + timedelta(seconds=1)
    unlock.set()
    await locking
    with pytest.raises(DomainError) as too_late:
        await queued
    assert too_late.value.failure.code == "lease_context_expired"
    assert (await s.service.store.get(s.ctx.principal, NAMESPACE, first["id"])).payload[
        "state"
    ] == "released"


@pytest.mark.parametrize("ttl", [0, -1, 300001, True])
async def test_lease_ttl_is_bounded_and_strict(leases, ttl):
    with pytest.raises(ContractViolation):
        await acquire(leases, lease_ttl_ms=ttl)


async def test_user_holder_and_node_lease_are_unavailable(leases):
    s = leases
    with pytest.raises(DomainError) as denied:
        await s.service.acquire(
            {"lease_ttl_ms": 1000, "expected_revision": 0},
            meta("user-holder"),
            s.ctx,
            holder=s.ctx.principal,
        )
    assert denied.value.failure.code == "lease_holder_denied"
    with pytest.raises(CapabilityUnavailable):
        await s.service.acquire(
            {"lease_ttl_ms": 1000, "expected_revision": 0},
            meta("node"),
            s.ctx.model_copy(update={"node_id": "n"}),
            holder=s.holder,
        )


async def test_owned_state_allows_new_holder_to_observe_expiry_and_take_over(leases):
    s = leases
    first = await acquire(s, lease_ttl_ms=1000)
    s.holder = s.holder.model_copy(update={"id": "replacement-worker"})
    state = await s.service.state(s.ctx, holder=s.holder)
    assert state["state"] == "active" and state["lease"] == first
    s.clock[0] += timedelta(seconds=2)
    state = await s.service.state(s.ctx, holder=s.holder)
    assert state["state"] == "expired" and state["lease"]["revision"] == 2
    current = await acquire(s, "resume-worker", expected_revision=state["lease"]["revision"])
    assert current["holder"] == s.holder.wire() and current["fencing_token"] == 2


async def test_expired_caller_cannot_invalidate_another_live_root_lease(leases):
    s = leases
    first = await acquire(s)
    expired_ctx = s.ctx.model_copy(
        update={"deadline": (s.clock[0] - timedelta(seconds=1)).isoformat()}
    )
    replacement = s.holder.model_copy(update={"id": "replacement-worker"})
    state = await s.service.state(expired_ctx, holder=replacement)
    assert state["state"] == "active" and state["lease"] == first
    pin = Ref.model_validate(change(first)["lease_ref"])
    with pytest.raises(DomainError) as expired:
        await s.service.current(pin, 1, expired_ctx, holder=s.holder)
    assert expired.value.failure.code == "lease_context_expired"
    assert await s.service.current(pin, 1, s.ctx, holder=s.holder) == first
