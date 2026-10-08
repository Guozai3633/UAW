"""Injected protocol binding checks; no real SQL or grants are represented."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from uaw.shared.errors import DomainError, reject
from uaw.tool.authority import ToolApprovalAuthority
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.ledger import ToolLedger


class NoPrivateStore:
    async def get(self, principal, namespace, key):
        assert namespace not in {
            "execution.policies",
            "budget.ledgers",
            "budget.accounting",
            "budget.reservations",
        }
        if namespace == "runs":
            return SimpleNamespace(
                payload={"conversation_id": "conversation-c", "task_id": "task-c"}
            )
        if namespace == "run.bindings":
            return SimpleNamespace(
                payload={
                    "model_policy_ref": {
                        "kind": "policy",
                        "id": "fixed-user-model",
                        "version": "1",
                    },
                    "configuration_ref": {
                        "kind": "configuration",
                        "id": "configuration-c",
                        "version": "1",
                    },
                }
            )
        return SimpleNamespace(revision=1, payload={"state": "active"})


def snapshot(ctx):
    return {
        "run_id": ctx.run_id,
        "scope": ctx.scope.wire(),
        "policy_refs": [
            {
                "kind": "policy",
                "id": ctx.capability_policy_ref.id,
                "version": ctx.capability_policy_ref.version,
                "content_hash": "0" * 64,
            }
        ],
        "allowed_capabilities": list(ctx.scope.capabilities),
        "denied_capabilities": [],
        "network_allowlist": [],
        "feature_flag_refs": [],
    }


def authority(ctx, registry, spec, policies):
    config = {"provider_refs": [spec["provider_ref"]]}
    configuration = SimpleNamespace(
        platform=ctx.principal,
        snapshot=AsyncMock(return_value=config),
        current=AsyncMock(return_value=config),
        require_capability=AsyncMock(),
    )
    return ToolApprovalAuthority(
        SimpleNamespace(store=NoPrivateStore()), registry, configuration, policies=policies
    )


async def test_policy_port_is_fresh_and_no_local_parent_or_budget_fallback(ctx, registry, spec):
    port = SimpleNamespace(resolve=AsyncMock(return_value=snapshot(ctx)))
    consumer = authority(ctx, registry, spec, port)
    await consumer._policy(spec, ctx)
    await consumer._policy(spec, ctx)
    assert port.resolve.await_count == 2
    port.resolve.side_effect = reject(
        "execution_policy_denied", "Current parent denies scope", 403, "authorization"
    )
    with pytest.raises(DomainError) as caught:
        await consumer._policy(spec, ctx)
    assert caught.value.failure.code == "execution_policy_denied"


@pytest.mark.parametrize("change", ["run", "scope", "capabilities", "leaf", "denied"])
async def test_policy_snapshot_cannot_replace_trusted_binding(ctx, registry, spec, change):
    value = deepcopy(snapshot(ctx))
    if change == "run":
        value["run_id"] = "wrong-run"
    elif change == "scope":
        value["scope"]["principal_id"] = "wrong-principal"
    elif change == "capabilities":
        value["allowed_capabilities"] = ["process.exec"]
    elif change == "leaf":
        value["policy_refs"][0]["id"] = "wrong-policy"
    else:
        value["denied_capabilities"] = list(ctx.scope.capabilities)
    consumer = authority(
        ctx, registry, spec, SimpleNamespace(resolve=AsyncMock(return_value=value))
    )
    with pytest.raises(DomainError) as caught:
        await consumer._policy(spec, ctx)
    assert caught.value.failure.code == "permission_denied"


async def test_missing_policy_port_does_not_traverse_owned_or_foreign_records(ctx, registry, spec):
    with pytest.raises(DomainError) as caught:
        await authority(ctx, registry, spec, None)._policy(spec, ctx)
    assert caught.value.failure.code == "dependency_unavailable"


async def test_budget_read_port_missing_or_wrong_owner_is_not_a_grant(ctx):
    missing = ToolBudgetAdapter(None, None)
    with pytest.raises(DomainError) as caught:
        await missing.get_ledger(ctx)
    assert caught.value.failure.code == "dependency_unavailable"
    with pytest.raises(DomainError):
        await missing.get_reservation("other", ctx)


async def test_generic_tool_record_reader_cannot_read_budget_private_state(ctx):
    ledger = ToolLedger(SimpleNamespace(database=None))
    for namespace in (
        "budget.ledgers",
        "budget.reservations",
        "budget.accounting",
        "execution.policies",
    ):
        with pytest.raises(DomainError) as caught:
            await ledger.get(namespace, "id", ctx)
        assert caught.value.failure.code == "phase_schema_invalid"
