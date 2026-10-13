"""Actual original SQL decision in a closed metadata bracket; roots controlled."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import event

from tests.integration.agent.test_installed_file_authority import (
    file_data_case as file_data_case,
)
from tests.integration.agent.test_installed_file_authority import (
    original_file_gate as original_file_gate,
)
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.tool.conftest import tool_case as tool_case
from uaw.infrastructure.installed_file_approval import InstalledFileApprovalAuthority
from uaw.infrastructure.installed_file_decision import InstalledFileDecision
from uaw.infrastructure.installed_tool_authority import InstalledFileResources
from uaw.run.approval import ApprovalService
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError, reject


@pytest.fixture
async def decision_case(original_file_gate, domain):
    gate, original, _, ctx, c = original_file_gate
    call, spec, _ = await gate.ledger.action("actual-file-action", ctx)
    waiting = await gate.approvals.precheck(call, spec, ctx)
    approval = await original.get(ctx.principal, waiting["wait_ref"]["id"])
    grant = await original.decide(
        ctx.principal,
        {
            "approval_id": approval["id"],
            "decision": {
                "decision": "approve_once",
                "expected_arguments_hash": approval["arguments_hash"],
                "expected_resource_refs": approval["resource_refs"],
                "reason": "Controlled SQL decision; not human native consent",
            },
        },
        meta("flat-test-decision", approval["revision"]),
    )
    workspace = ctx.scope.resource_refs[0]
    resources = InstalledFileResources(
        object(),
        "controlled-root-device",
        observed={
            "owner": ctx.principal.wire(),
            "device_id": "controlled-root-device",
            "workspace_ref": workspace.wire(),
            "root_handle": "controlled-root-handle",
            "binding_revision": 1,
            "allowed_actions": ["file.read"],
            "expires_at": ctx.deadline,
        },
    )
    previous = original.authority
    authority = InstalledFileApprovalAuthority(
        previous.ledger,
        previous.registry,
        previous.configuration,
        previous.access,
        resources,
        policies=previous.policies,
    )
    service = InstalledFileDecision(
        original.store, original.configuration, authority, permissions=original.permissions
    )
    request = (await c.records.get(ctx.principal, "approval.bindings", approval["id"])).payload[
        "request"
    ]
    return SimpleNamespace(
        service=service,
        old=ApprovalService(
            original.store, original.configuration, authority, permissions=original.permissions
        ),
        c=c,
        ctx=ctx,
        request=request,
        grant=grant,
        ref=Ref.model_validate(grant["approval_ref"]),
        resources=resources,
        run=domain[1],
    )


async def test_same_original_grant_with_fewer_actual_sql_reads(decision_case, tmp_path):
    p = decision_case
    count, owner = 0, asyncio.current_task()

    def sql(conn, cursor, statement, parameters, context, many):
        nonlocal count
        if asyncio.current_task() is owner and statement.lstrip().upper().startswith("SELECT"):
            count += 1

    engine = p.service.store.database.engine.sync_engine
    event.listen(engine, "before_cursor_execute", sql)
    try:
        results, samples = [], {}
        for name, service in (("old", p.old), ("closed", p.service)):
            count = 0
            results.append(await service.recheck(p.ref, p.request, p.ctx))
            samples[name] = count
        assert results[0] == results[1] == p.grant
        assert 0 < samples["closed"] < samples["old"]
        (tmp_path / "file-decision-measurement.json").write_text(
            json.dumps(samples), encoding="utf-8"
        )
    finally:
        event.remove(engine, "before_cursor_execute", sql)


@pytest.mark.parametrize(
    "change", ["cancel", "decision", "binding", "grant", "mode", "expiry", "policy", "role"]
)
async def test_await_time_changes_never_return_original_grant(decision_case, change):
    p = decision_case
    started, release = asyncio.Event(), asyncio.Event()
    resolve = p.resources.resolve

    async def waiting(*args, **kwargs):
        result = await resolve(*args, **kwargs)
        started.set()
        await release.wait()
        return result

    p.resources.resolve = waiting
    task = asyncio.create_task(p.service.recheck(p.ref, p.request, p.ctx))
    try:
        await asyncio.wait_for(started.wait(), 5)
        if change == "cancel":
            run = await p.run.get_run(p.ctx.principal, p.ctx.run_id)
            await asyncio.wait_for(
                p.run.control(
                    p.ctx.principal,
                    {
                        "run_id": p.ctx.run_id,
                        "control": {
                            "mode": "cancel",
                            "preserve_refs": [],
                            "reason": "Test original Run stop",
                        },
                    },
                    meta("closed-cancel", run["revision"]),
                ),
                5,
            )
        elif change == "role":
            await p.c.tool_access.revoke(
                p.ctx, meta("closed-role", 1), authenticated_service=p.c.configuration.platform
            )
        else:
            namespace, identifier = {
                "decision": ("approvals", p.ref.id),
                "binding": ("approval.bindings", p.ref.id),
                "grant": ("approval.grants", p.ref.id),
                "mode": ("conversations", p.ctx.conversation_id),
                "expiry": ("budget.ledgers", p.ctx.run_id),
                "policy": ("execution.policies", p.ctx.capability_policy_ref.id),
            }[change]
            row = await p.c.records.get(p.ctx.principal, namespace, identifier)
            value = dict(row.payload)
            if change == "decision":
                value.update(revision=row.revision + 1, status="cancelled")
            elif change == "binding":
                value["context"] = {**value["context"], "operation_id": "changed-original-action"}
            elif change == "grant":
                value["decision"] = {**value["decision"], "reason": "Changed recorded grant"}
            elif change == "mode":
                value.update(revision=row.revision + 1, approval_mode="automatic")
            elif change == "expiry":
                value.update(
                    revision=row.revision + 1,
                    deadline=(datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
                )
            else:
                value.update(revision=row.revision + 1, denied_capabilities=["file.read"])
            await p.c.records.put(
                p.ctx.principal,
                namespace,
                identifier,
                row.schema_name,
                value,
                expected_revision=row.revision,
                request_id="closed-change-" + change,
            )
        release.set()
        with pytest.raises(DomainError):
            await asyncio.wait_for(task, 5)
    finally:
        release.set()
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        p.resources.resolve = resolve


@pytest.mark.parametrize("mode", ["denied", "cancelled", "caller_expired"])
async def test_original_reader_failure_cancel_and_earlier_deadline(decision_case, mode):
    p = decision_case
    ctx = p.ctx

    async def interrupted(*args, **kwargs):
        if mode == "cancelled":
            raise asyncio.CancelledError()
        if mode == "denied":
            raise reject("original_root_denied", "Original metadata root unavailable", 403)
        remaining = (datetime.fromisoformat(ctx.deadline) - datetime.now(UTC)).total_seconds()
        await asyncio.sleep(max(0, remaining) + 0.02)
        return p.ctx.scope.resource_refs

    if mode == "caller_expired":
        ctx = ctx.model_copy(
            update={"deadline": (datetime.now(UTC) + timedelta(seconds=1)).isoformat()}
        )
    p.resources.resolve = interrupted
    with pytest.raises((DomainError, asyncio.CancelledError, TimeoutError)):
        await p.service.recheck(p.ref, p.request, ctx)
    assert (await p.old.get(p.ctx.principal, p.ref.id))["revision"] == 2


@pytest.mark.parametrize("change", ["grant", "authority", "authentication", "ledger", "registry"])
async def test_comparison_point_and_memory_changes_during_cleanup(
    decision_case, monkeypatch, change
):
    p = decision_case
    store = p.service.store
    witness = store._witness_rows
    authority, authentication = p.service.authority, p.service.permissions.authentication_check
    ledger, registry = authority.ledger, authority.registry

    async def changed(*args, **kwargs):
        result = await witness(*args, **kwargs)
        if change == "grant":
            row = await store.get(p.ctx.principal, "approval.grants", p.ref.id)
            await store.delete(
                p.ctx.principal,
                "approval.grants",
                p.ref.id,
                expected_revision=row.revision,
                request_id="late-grant-delete",
            )
        elif change == "authority":
            p.service.authority = None
        elif change == "ledger":
            authority.ledger = object()
        elif change == "registry":
            authority.registry = object()
        else:

            async def replacement(principal):
                return None

            p.service.permissions.authentication_check = replacement
        return result

    monkeypatch.setattr(store, "_witness_rows", changed)
    try:
        if change == "grant":
            # A change after the SQL comparison point is outside that witness.
            # Recovery/execution still needs its own next current checkpoint.
            assert await p.service.recheck(p.ref, p.request, p.ctx) == p.grant
            with pytest.raises(DomainError):
                await p.service.recheck(p.ref, p.request, p.ctx)
        else:
            with pytest.raises(DomainError):
                await p.service.recheck(p.ref, p.request, p.ctx)
    finally:
        p.service.authority = authority
        p.service.permissions.authentication_check = authentication
        authority.ledger, authority.registry = ledger, registry
