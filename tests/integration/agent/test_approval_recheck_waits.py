"""Real SQL: external authority waits release the lock, final guards remain fresh."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from tests.integration.test_approvals import approval_case as approval_case
from tests.integration.test_approvals import approved
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError, reject


class WaitingAuthority:
    def __init__(self, original):
        self.original = original
        self.started = asyncio.Queue()
        self.release = asyncio.Event()

    async def check(self, request, ctx):
        await self.original.check(request, ctx)
        await self.started.put(True)
        await self.release.wait()


async def waiting_recheck(case, grant, ctx=None):
    waiter = WaitingAuthority(case.service.authority)
    case.service.authority = waiter
    task = asyncio.create_task(
        case.service.recheck(
            Ref.model_validate(grant["approval_ref"]), case.request, ctx or case.ctx
        )
    )
    try:
        await asyncio.wait_for(waiter.started.get(), 5)
    except BaseException:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        raise
    return waiter, task


async def test_two_rechecks_can_wait_together_without_holding_conversation_lock(approval_case):
    case = approval_case
    grant = await approved(case)
    waiter, first = await waiting_recheck(case, grant)
    second = asyncio.create_task(
        case.service.recheck(Ref.model_validate(grant["approval_ref"]), case.request, case.ctx)
    )
    try:
        await asyncio.wait_for(waiter.started.get(), 5)
        aggregate = await case.service._aggregate(case.ctx.principal, case.ctx.run_id)
        async with case.service.store.database.sessions.begin() as session:
            assert (
                await session.scalar(
                    select(
                        func.pg_try_advisory_xact_lock(
                            func.hashtextextended(f"{case.ctx.principal.id}:{aggregate}", 0)
                        )
                    )
                )
                is True
            )
        waiter.release.set()
        assert await asyncio.wait_for(first, 5) == grant
        assert await asyncio.wait_for(second, 5) == grant
    finally:
        waiter.release.set()
        for task in (first, second):
            task.cancel()
        await asyncio.gather(first, second, return_exceptions=True)


@pytest.mark.parametrize("change", ["cancel", "policy", "binding", "grant", "mode", "expiry"])
async def test_changes_during_external_wait_never_return_old_grant(approval_case, domain, change):
    case = approval_case
    grant = await approved(case)
    waiter, task = await waiting_recheck(case, grant)
    try:
        if change == "cancel":
            await asyncio.wait_for(
                domain[1].control(
                    case.ctx.principal,
                    {
                        "run_id": case.ctx.run_id,
                        "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop"},
                    },
                    meta("cancel-during-authority", 2),
                ),
                5,
            )
        else:
            namespace, resource_id = {
                "policy": ("execution.policies", case.policy["id"]),
                "binding": ("approval.bindings", grant["approval_ref"]["id"]),
                "grant": ("approval.grants", grant["approval_ref"]["id"]),
                "mode": ("conversations", case.ctx.conversation_id),
                "expiry": ("budget.ledgers", case.ctx.run_id),
            }[change]
            record = await case.service.store.get(case.ctx.principal, namespace, resource_id)
            payload = dict(record.payload)
            if change == "policy":
                payload.update(revision=2, denied_capabilities=["tool.invoke"])
            elif change == "binding":
                payload["context"] = {**payload["context"], "operation_id": "changed"}
            elif change == "grant":
                payload["decision"] = {**payload["decision"], "reason": "Changed grant"}
            elif change == "mode":
                payload.update(revision=record.revision + 1, approval_mode="automatic")
            else:
                payload.update(
                    revision=record.revision + 1,
                    deadline=(datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
                )
            await case.service.store.put(
                case.ctx.principal,
                namespace,
                resource_id,
                record.schema_name,
                payload,
                expected_revision=record.revision,
                request_id="change-during-authority",
            )
        waiter.release.set()
        with pytest.raises(DomainError):
            await asyncio.wait_for(task, 5)
    finally:
        waiter.release.set()
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


async def test_authority_failure_and_cancellation_do_not_publish_or_lock_grant(approval_case):
    case = approval_case
    grant = await approved(case)
    waiter, task = await waiting_recheck(case, grant)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    waiter.release.set()

    class Denied:
        async def check(self, request, ctx):
            raise reject("live_native_denied", "Live native authority denied", 403)

    case.service.authority = Denied()
    with pytest.raises(DomainError) as caught:
        await case.service.recheck(
            Ref.model_validate(grant["approval_ref"]), case.request, case.ctx
        )
    assert caught.value.failure.code == "live_native_denied"
    assert (await case.service.get(case.ctx.principal, grant["approval_ref"]["id"]))[
        "revision"
    ] == 2
    case.service.authority = waiter.original
    assert (
        await case.service.recheck(
            Ref.model_validate(grant["approval_ref"]), case.request, case.ctx
        )
        == grant
    )


async def test_shorter_caller_deadline_remains_expired_after_external_wait(approval_case):
    case = approval_case
    grant = await approved(case)
    ctx = case.ctx.model_copy(
        update={"deadline": (datetime.now(UTC) + timedelta(seconds=2)).isoformat()}
    )
    waiter, task = await waiting_recheck(case, grant, ctx)
    try:
        remaining = (datetime.fromisoformat(ctx.deadline) - datetime.now(UTC)).total_seconds()
        await asyncio.sleep(max(0, remaining) + 0.02)
        waiter.release.set()
        with pytest.raises(DomainError) as caught:
            await asyncio.wait_for(task, 5)
        assert caught.value.failure.code == "approval_action_stale"
    finally:
        waiter.release.set()
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
