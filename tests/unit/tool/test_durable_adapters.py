"""Unit protocol substitutions only; these tests are not SQL persistence evidence."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from uaw.infrastructure.db.records import parameter_hash
from uaw.shared.errors import DomainError, reject
from uaw.shared.schema import validate_contract
from uaw.tool.approval import ToolApprovalAdapter
from uaw.tool.authority import ToolApprovalAuthority
from uaw.tool.budget import ToolBudgetAdapter, step_meta
from uaw.tool.ledger import ToolLedger, action_key, stable_context


def fixture_request(ctx):
    return {
        "action_id": "action-c",
        "arguments_hash": parameter_hash({"text": "Original"}),
        "resource_refs": [],
        "effect": "external_write",
        "summary": "Unit protocol fixture",
        "expires_at": ctx.deadline,
    }


def fixture_adapter(ctx):
    request = fixture_request(ctx)
    ledger = SimpleNamespace(
        save=AsyncMock(side_effect=lambda ns, key, schema, value, context: value),
        action=AsyncMock(return_value=({}, {}, ctx)),
        bind=AsyncMock(return_value=action_key(ctx, "action-c")),
    )
    authority = SimpleNamespace(current=AsyncMock(return_value=request), check=AsyncMock())
    pending = {
        **request,
        "id": "approval-unit",
        "revision": 1,
        "mode": "manual",
        "status": "pending",
    }
    service = SimpleNamespace(
        request=AsyncMock(return_value=pending),
        get=AsyncMock(return_value=pending),
        recheck=AsyncMock(),
    )
    return ToolApprovalAdapter(ledger, authority, service), service, authority, request


async def test_adapter_wait_ref_comes_from_returned_record_and_not_a_generated_placeholder(ctx):
    adapter, service, _, request = fixture_adapter(ctx)
    result = await adapter.precheck({"action_id": "action-c"}, {}, ctx)
    assert result == {
        "kind": "waiting",
        "output_refs": [],
        "wait_ref": {"kind": "approval", "id": "approval-unit", "version": "1"},
    }
    validate_contract("ComponentToolInvocationPrecheckResult", result)
    service.recheck.assert_not_awaited()
    service.request.assert_awaited_once()
    assert service.request.await_args.args[0] == request


async def test_adapter_reads_current_approval_instead_of_replayed_pending_and_rechecks(ctx):
    adapter, service, authority, request = fixture_adapter(ctx)
    approved = {
        **request,
        "id": "approval-unit",
        "revision": 2,
        "mode": "manual",
        "status": "approved",
    }
    service.get.return_value = approved
    grant = {
        "id": "grant-unit",
        "approval_ref": {"kind": "approval", "id": "approval-unit", "version": "2"},
        "actor": ctx.principal.wire(),
        "decision": {
            "decision": "approve_once",
            "expected_arguments_hash": request["arguments_hash"],
            "expected_resource_refs": [],
            "reason": "Unit decision",
        },
        "issued_at": "2026-10-07T00:00:00Z",
    }
    service.recheck.return_value = grant
    result = await adapter.precheck({"action_id": "action-c"}, {}, ctx)
    assert result["kind"] == "ok" and result["payload"]["allowed"]
    assert service.recheck.await_args.args[0].version == "2"
    authority.check.assert_awaited_once_with(request, ctx)


@pytest.mark.parametrize(
    "status,kind",
    [
        ("declined", "denied"),
        ("cancelled", "cancelled"),
        ("expired", "denied"),
        ("stale", "denied"),
    ],
)
async def test_adapter_negative_current_approval_cannot_become_permission(ctx, status, kind):
    adapter, service, _, request = fixture_adapter(ctx)
    service.get.return_value = {
        **request,
        "id": "approval-unit",
        "revision": 2,
        "mode": "manual",
        "status": status,
    }
    assert (await adapter.precheck({"action_id": "action-c"}, {}, ctx))["kind"] == kind
    service.recheck.assert_not_awaited()


@pytest.mark.parametrize("phase", ["request", "get"])
async def test_invalid_approval_dto_is_dependency_failure_without_secret_values(ctx, phase):
    adapter, service, _, _ = fixture_adapter(ctx)
    getattr(service, phase).return_value = {"secret": "must-not-leak"}
    result = await adapter.precheck({"action_id": "action-c"}, {}, ctx)
    assert result["failure"]["code"] == "dependency_protocol_invalid"
    assert "must-not-leak" not in str(result)


async def test_adapter_current_resource_or_authority_failure_propagates(ctx):
    adapter, service, authority, _ = fixture_adapter(ctx)
    authority.current.side_effect = reject("resource_stale", "Resource changed", 412)
    result = await adapter.precheck({"action_id": "action-c"}, {}, ctx)
    assert result["kind"] == "stale"
    service.request.assert_not_awaited()


async def test_no_budget_approval_dependency_cannot_reserve_or_mark_dispatch(ctx):
    port = SimpleNamespace(reserve=AsyncMock(), dispatch=AsyncMock())
    adapter = ToolBudgetAdapter(None, port)
    resources = {
        "input_tokens": 0,
        "output_tokens": 0,
        "model_calls": 0,
        "tool_calls": 1,
        "child_agents": 0,
        "wall_time_ms": 0,
        "money": "0",
        "currency": "USD",
    }
    for operation in (adapter.reserve(resources, ctx), adapter.mark_dispatch(ctx)):
        with pytest.raises(DomainError) as caught:
            await operation
        assert caught.value.failure.code == "dependency_unavailable"
    port.reserve.assert_not_awaited()
    port.dispatch.assert_not_awaited()


async def test_no_reader_or_role_dependency_does_not_self_authorize(ctx, registry):
    ledger = SimpleNamespace(action=AsyncMock(return_value=({}, {}, ctx)))
    authority = ToolApprovalAuthority(ledger, registry, None)
    with pytest.raises(DomainError) as caught:
        await authority.current("action-c", ctx)
    assert caught.value.failure.code == "dependency_unavailable"


def test_action_identity_and_budget_step_id_preserve_fixed_boundaries(ctx):
    assert stable_context(ctx) == stable_context(
        ctx.model_copy(update={"attempt_id": "new", "trace_id": "new"})
    )
    assert stable_context(ctx) != stable_context(ctx.model_copy(update={"operation_id": "new"}))
    assert action_key(ctx, "action-c") != action_key(
        ctx.model_copy(update={"run_id": "new"}), "action-c"
    )
    assert step_meta("reserve", "a") == step_meta("reserve", "a")
    assert step_meta("reserve", "a") != step_meta("release", "a")


async def test_persistence_helper_cannot_write_other_domain_or_untyped_blob(ctx):
    ledger = ToolLedger(SimpleNamespace(database=None))
    for namespace, schema in (
        ("budget.ledgers", "RootBudgetLedger"),
        ("tool.budget.reserved", "Object"),
    ):
        with pytest.raises(DomainError) as caught:
            await ledger.save(namespace, "key", schema, {}, ctx)
        assert caught.value.failure.code == "phase_schema_invalid"


async def test_recheck_refuses_missing_or_negative_precheck_before_service_calls(ctx):
    adapter, service, _, _ = fixture_adapter(ctx)
    for previous in (
        {
            "kind": "waiting",
            "output_refs": [],
            "wait_ref": {"kind": "approval", "id": "unit", "version": "1"},
        },
        {
            "kind": "ok",
            "output_refs": [],
            "payload": {
                "allowed": False,
                "approval_required": True,
                "policy_ref": ctx.capability_policy_ref.wire(),
                "resource_refs": [],
                "violations": [],
            },
        },
    ):
        result = await adapter.recheck({"action_id": "action-c"}, {}, previous, ctx)
        assert result["kind"] == "stale"
    service.request.assert_not_awaited()
