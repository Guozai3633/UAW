"""55434 real SQL: original office/file chains and controlled bridge, no native claim."""

import asyncio
from copy import deepcopy
from dataclasses import replace

import pytest

from tests.integration.test_control_plane import meta
from tests.integration.tool.runtime_router_fixture import file_pipeline as file_pipeline
from tests.integration.tool.runtime_router_fixture import mixed_runtime as mixed_runtime
from tests.integration.tool.runtime_router_fixture import office_pipeline as office_pipeline
from tests.integration.tool.runtime_router_fixture import recover_mixed
from tests.integration.tool.test_durable import cancel
from uaw.infrastructure.db.transactions import reference
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.tool.ledger import action_key
from uaw.tool.providers.file_store import recover_file_accounting
from uaw.tool.runtime_router import RoutedToolRuntime


async def approve(runtime, p, *, decision="approve_once"):
    first = await runtime.invoke(p.raw, p.case.ctx)
    assert first["kind"] == "waiting", first
    actual = await p.case.service.get(p.case.ctx.principal, first["wait_ref"]["id"])
    await p.case.service.decide(
        p.case.ctx.principal,
        {
            "approval_id": actual["id"],
            "decision": {
                "decision": decision,
                "expected_arguments_hash": actual["arguments_hash"],
                "expected_resource_refs": actual["resource_refs"],
                "reason": "Controlled SQL decision; no native human approval claim",
            },
        },
        meta("router-decision-" + p.case.ctx.attempt_id, actual["revision"]),
    )
    return actual


async def test_mixed_original_actual_results_and_owning_readers(mixed_runtime):
    m = mixed_runtime
    for p in (m.office, m.file):
        await approve(m.runtime, p)
        result = await m.runtime.invoke(p.raw, p.case.ctx)
        assert result["kind"] == "ok", result
        assert result["payload"]["call_ref"] == reference(
            "tool_call", action_key(p.case.ctx, p.raw["action_id"])
        )
        assert await m.runtime.read_result(p.raw["action_id"], p.case.ctx) == result
        outcome = await m.runtime.read_outcome(p.raw["action_id"], p.case.ctx)
        assert outcome["outcome"] == "applied" and outcome["attempt_id"] == p.case.ctx.attempt_id
        effect = await m.ledger.effect(p.raw["action_id"], p.case.ctx)
        assert (
            await m.runtime.reconcile(
                {"action_id": p.raw["action_id"], "expected_revision": effect["revision"]},
                p.case.ctx,
            )
        )["kind"] == "ok"
    assert m.office.executor.calls == m.file.bridge.calls == m.file.bridge.opens == 1


async def test_discover_only_bound_and_agent_denial_is_not_run_access(mixed_runtime):
    m = mixed_runtime
    result = await m.runtime.discover(
        {
            "query": "arithmetic.calculate data.inspect_json text.inspect file.read",
            "max_candidates": 20,
        },
        m.file.case.ctx,
    )
    assert result["kind"] == "ok", result
    refs = [row["tool_ref"] for row in result["payload"]["tools"]]
    assert len(refs) == 2 and set(r["id"] for r in refs) == {m.office.case.spec["id"], "file.read"}
    m.access.denied.add(m.office.case.ctx.attempt_id)
    assert m.office.role.allowed
    assert (await m.runtime.invoke(m.office.raw, m.office.case.ctx))["kind"] == "denied"
    assert m.office.executor.calls == 0
    assert (
        await m.ledger.get("tool.budget.reserved", m.office.case.ctx.attempt_id, m.office.case.ctx)
        is None
    )
    owner = m.owners[m.office.kind]
    before = owner.facade.invocation.access
    with pytest.raises(ValueError):
        RoutedToolRuntime(m.registry, m.ledger, m.routes, access=m.office.role)
    assert owner.facade.invocation.access is before is m.access


async def test_approval_decline_and_pending_never_send(mixed_runtime):
    m = mixed_runtime
    for p in (m.office, m.file):
        await approve(m.runtime, p, decision="decline")
        result = await m.runtime.invoke(p.raw, p.case.ctx)
        assert result["kind"] == "denied", result
        assert await m.ledger.get("tool.budget.reserved", p.case.ctx.attempt_id, p.case.ctx) is None
    assert m.office.executor.calls == m.file.bridge.calls == m.file.bridge.opens == 0


async def test_approved_but_current_agent_revoke_or_cancel_blocks_send(mixed_runtime):
    m = mixed_runtime
    await approve(m.runtime, m.office)
    await approve(m.runtime, m.file)
    m.access.denied.add(m.office.case.ctx.attempt_id)
    assert (await m.runtime.invoke(m.office.raw, m.office.case.ctx))["kind"] == "denied"
    await cancel(m.file.case)
    assert (await m.runtime.invoke(m.file.raw, m.file.case.ctx))["kind"] != "ok"
    assert m.office.executor.calls == m.file.bridge.calls == m.file.bridge.opens == 0


async def test_wrong_hash_provider_and_session_never_fallback(mixed_runtime):
    m = mixed_runtime
    for p in (m.office, m.file):
        raw = deepcopy(p.raw)
        raw["tool_ref"]["content_hash"] = "0" * 64
        assert (await m.runtime.invoke(raw, p.case.ctx))["kind"] != "ok"
        bad = replace(
            m.routes[0], provider_ref=Ref(kind="provider", id="wrong-provider", version="1")
        )
        with pytest.raises(ValueError):
            RoutedToolRuntime(m.registry, m.ledger, (bad,), access=m.access)
        await approve(m.runtime, p)
        assert (await m.runtime.invoke(p.raw, p.case.ctx))["kind"] == "ok"
        changed = p.case.ctx.model_copy(
            update={
                "principal": p.case.ctx.principal.model_copy(
                    update={"auth_session_id": "other-session"}
                )
            }
        )
        assert (
            await m.runtime.reconcile(
                {"action_id": p.raw["action_id"], "expected_revision": 0}, changed
            )
        )["kind"] != "ok"
        with pytest.raises(DomainError):
            await m.runtime.read_result(p.raw["action_id"], changed)
        with pytest.raises(DomainError):
            await m.runtime.read_outcome(p.raw["action_id"], changed)
    assert m.office.executor.calls == m.file.bridge.calls == 1


async def test_concurrent_mixed_attempts_and_durable_restart(mixed_runtime):
    m = mixed_runtime
    for p in (m.office, m.file):
        await approve(m.runtime, p)
    replies = await asyncio.wait_for(
        asyncio.gather(
            *(m.runtime.invoke(p.raw, p.case.ctx) for p in (m.office, m.file) for _ in range(3))
        ),
        90,
    )
    assert sum(row["kind"] == "ok" for row in replies) >= 2
    assert m.office.executor.calls == m.file.bridge.calls == m.file.bridge.opens == 1
    fresh = recover_mixed(m)
    m.access.denied.update(p.case.ctx.attempt_id for p in (m.office, m.file))
    before = m.access.calls
    for p in (m.office, m.file):
        # Normalize/save the original result if a concurrent loser interrupted it.
        assert (await fresh.runtime.invoke(p.raw, p.case.ctx))["kind"] == "ok"
        assert (await fresh.runtime.read_result(p.raw["action_id"], p.case.ctx))["kind"] == "ok"
        assert (await fresh.runtime.read_outcome(p.raw["action_id"], p.case.ctx))[
            "outcome"
        ] == "applied"
    assert m.access.calls == before and fresh.bridge.calls == fresh.bridge.opens == 0


async def test_lost_original_reply_cancel_and_revoke_execute_access_restore_no_send(mixed_runtime):
    m = mixed_runtime
    for p in (m.office, m.file):
        await approve(m.runtime, p)
    execute = m.office.executor.execute

    async def office_lost(*args):
        await execute(*args)
        raise TimeoutError("Controlled office reply loss after real saved response")

    async def file_lost():
        raise TimeoutError("Controlled file reply loss after independent SQL journal")

    m.office.executor.execute = office_lost
    m.file.bridge.after_journal = file_lost
    for p in (m.office, m.file):
        assert (await m.runtime.invoke(p.raw, p.case.ctx))["failure"][
            "code"
        ] == "invocation_interrupted"
    (m.file.root / "file.txt").unlink()
    await cancel(m.file.case)
    m.access.denied.update(p.case.ctx.attempt_id for p in (m.office, m.file))
    fresh = recover_mixed(m)
    before = m.access.calls
    for p in (m.office, m.file):
        effect = await fresh.ledger.effect(p.raw["action_id"], p.case.ctx)
        assert (
            await fresh.runtime.reconcile(
                {"action_id": p.raw["action_id"], "expected_revision": effect["revision"]},
                p.case.ctx,
            )
        )["kind"] == "ok"
        assert (await fresh.runtime.invoke(p.raw, p.case.ctx))["kind"] == "ok"
        assert (await fresh.runtime.read_result(p.raw["action_id"], p.case.ctx))["kind"] == "ok"
    assert m.access.calls == before and fresh.bridge.calls == fresh.bridge.opens == 0
    assert m.office.executor.calls == m.file.bridge.opens == 1


async def test_data_body_revoke_does_not_block_original_accounting(mixed_runtime):
    m = mixed_runtime
    p = m.file
    await approve(m.runtime, p)
    settle = p.case.budget.budgets.settle

    async def lost(*args, **kwargs):
        await settle(*args, **kwargs)
        raise TimeoutError("Controlled fee commit acknowledgement loss")

    p.case.budget.budgets.settle = lost
    assert (await m.runtime.invoke(p.raw, p.case.ctx))["failure"][
        "code"
    ] == "reconciliation_interrupted"
    await cancel(p.case)
    p.bridge.allowed = False
    p.signatures.revoked = True
    fresh = recover_mixed(m)
    with pytest.raises(DomainError):
        await fresh.runtime.read_result(p.raw["action_id"], p.case.ctx)
    with pytest.raises(DomainError):
        await fresh.runtime.read_outcome(p.raw["action_id"], p.case.ctx)
    before = await fresh.budget.get_ledger(p.case.ctx)
    actual = await recover_file_accounting(fresh.ledger, fresh.budget, p.case.ctx)
    assert actual["usage_refs"]
    assert await recover_file_accounting(fresh.ledger, fresh.budget, p.case.ctx) == actual
    assert await fresh.budget.get_ledger(p.case.ctx) == before
    assert fresh.bridge.calls == fresh.bridge.opens == 0 and p.bridge.opens == 1
