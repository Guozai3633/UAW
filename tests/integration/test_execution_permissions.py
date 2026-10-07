"""Real SQL policy ancestry and consumer boundaries; no Agent/Runner grant is fabricated."""

import asyncio
import copy
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from tests.integration.intent.test_understanding import understanding as understanding
from tests.integration.model.test_gateway import case as case
from tests.integration.test_approvals import approval_case as approval_case
from tests.integration.test_approvals import approved
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from uaw.composition import compose
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import reference
from uaw.model.adapters import ChatCompletionsAdapter
from uaw.run.context import RunContextSources
from uaw.run.permissions import ExecutionPolicyResolver, require_snapshot
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.shared.schema import validate_contract
from uaw.shared.settings import Settings
from uaw.shared.stores import StoreMissing


async def attach_parent(
    store, ctx, *, parent_id="parent-policy", parent_patch=None, child_patch=None
):
    leaf = await store.get(ctx.principal, "execution.policies", ctx.capability_policy_ref.id)
    parent = {**copy.deepcopy(leaf.payload), "id": parent_id, "revision": 1}
    parent.pop("parent_policy_ref", None)
    parent.update(parent_patch or {})
    await store.put(
        ctx.principal,
        "execution.policies",
        parent_id,
        "CapabilityPolicy",
        parent,
        expected_revision=0,
        request_id="parent-create-" + parent_id,
    )
    child = {
        **leaf.payload,
        "revision": leaf.revision + 1,
        "parent_policy_ref": reference("policy", parent_id),
        **(child_patch or {}),
    }
    await store.put(
        ctx.principal,
        "execution.policies",
        leaf.resource_id,
        "CapabilityPolicy",
        child,
        expected_revision=leaf.revision,
        request_id="child-bind-" + str(leaf.revision),
    )
    ctx = ctx.model_copy(
        update={
            "capability_policy_ref": Ref.model_validate(
                reference("policy", leaf.resource_id, leaf.revision + 1)
            )
        }
    )
    return ctx, parent


async def test_valid_chain_snapshot_restart_and_scope_bound_result(approval_case):
    s = approval_case
    ctx, _ = await attach_parent(
        s.service.store,
        s.ctx,
        parent_patch={
            "network_allowlist": ["approved.example"],
            "allowed_capabilities": ["tool.invoke", "context.build"],
        },
    )
    resolver = ExecutionPolicyResolver(s.service.store)
    snapshot = await resolver.resolve(ctx)
    validate_contract("ExecutionPolicySnapshot", snapshot)
    assert snapshot["scope"] == ctx.scope.wire()
    assert snapshot["allowed_capabilities"] == ["tool.invoke"]
    assert snapshot["network_allowlist"] == []
    assert [r["id"] for r in snapshot["policy_refs"]] == [
        ctx.capability_policy_ref.id,
        "parent-policy",
    ]
    assert all(r["content_hash"] for r in snapshot["policy_refs"])
    assert await ExecutionPolicyResolver(s.service.store).resolve(ctx) == snapshot
    # Returned JSON does not mutate authority, and is never accepted as a grant.
    snapshot["allowed_capabilities"].append("workspace.exec")
    assert (await resolver.resolve(ctx))["allowed_capabilities"] == ["tool.invoke"]


async def test_permission_snapshot_cannot_be_transferred_or_expand_scope(approval_case):
    s = approval_case
    snapshot = await ExecutionPolicyResolver(s.service.store).resolve(s.ctx)
    altered = [
        {**snapshot, "run_id": "other-run"},
        {**snapshot, "scope": {**snapshot["scope"], "principal_id": "other-user"}},
        {**snapshot, "allowed_capabilities": ["tool.invoke", "workspace.exec"]},
        {**snapshot, "denied_capabilities": ["tool.invoke"]},
    ]
    for value in altered:
        with pytest.raises(DomainError) as denied:
            require_snapshot(value, s.ctx)
        assert denied.value.failure.code == "execution_snapshot_scope_denied"


async def test_ancestor_deny_and_current_revision_are_both_enforced(approval_case):
    s = approval_case
    ctx, parent = await attach_parent(
        s.service.store, s.ctx, parent_patch={"denied_capabilities": ["tool.invoke"]}
    )
    with pytest.raises(DomainError) as denied:
        await ExecutionPolicyResolver(s.service.store).resolve(ctx)
    assert denied.value.failure.code == "execution_policy_denied"
    await s.service.store.put(
        ctx.principal,
        "execution.policies",
        parent["id"],
        "CapabilityPolicy",
        {**parent, "revision": 2, "denied_capabilities": []},
        expected_revision=1,
        request_id="revise-parent",
    )
    with pytest.raises(DomainError) as stale:
        await ExecutionPolicyResolver(s.service.store).resolve(ctx)
    assert stale.value.failure.code == "execution_policy_stale"


@pytest.mark.parametrize(
    "patch",
    [
        {"allowed_capabilities": ["tool.invoke", "workspace.exec"]},
        {"network_allowlist": ["unapproved.example"]},
        {"resource_scope": {"resource_refs": []}},
        {"resource_scope": {"conversation_id": "other-conversation", "resource_refs": []}},
    ],
    ids=["capabilities", "network", "broader-scope", "different-conversation"],
)
async def test_child_policy_cannot_expand_parent(approval_case, patch):
    s = approval_case
    ctx, _ = await attach_parent(s.service.store, s.ctx, child_patch=patch)
    with pytest.raises(DomainError) as caught:
        await ExecutionPolicyResolver(s.service.store).resolve(ctx)
    assert caught.value.failure.code == "execution_policy_escalation"
    assert caught.value.failure.category == "authorization"


async def test_missing_or_other_owner_parent_never_uses_platform_default(approval_case):
    s = approval_case
    ctx, _ = await attach_parent(s.service.store, s.ctx)
    await s.service.store.delete(
        ctx.principal,
        "execution.policies",
        "parent-policy",
        expected_revision=1,
        request_id="delete-parent",
    )
    with pytest.raises(StoreMissing):
        await ExecutionPolicyResolver(s.service.store).resolve(ctx)


async def test_cycles_and_depth_are_bounded(approval_case):
    s = approval_case
    ctx, parent = await attach_parent(s.service.store, s.ctx)
    # Create a current cycle with both references pointing at revision 2.
    await s.service.store.put(
        ctx.principal,
        "execution.policies",
        parent["id"],
        "CapabilityPolicy",
        {**parent, "revision": 2, "parent_policy_ref": ctx.capability_policy_ref.wire()},
        expected_revision=1,
        request_id="parent-cycle",
    )
    leaf = await s.service.store.get(
        ctx.principal, "execution.policies", ctx.capability_policy_ref.id
    )
    # Keeping the parent's reference to leaf revision 2 detects the cycle before replaying a ref.
    # A separate chain exercises the strict eight-record ceiling.
    await s.service.store.put(
        ctx.principal,
        "execution.policies",
        leaf.resource_id,
        "CapabilityPolicy",
        {**leaf.payload, "revision": 3, "parent_policy_ref": reference("policy", parent["id"], 2)},
        expected_revision=2,
        request_id="leaf-cycle",
    )
    ctx = ctx.model_copy(
        update={
            "capability_policy_ref": Ref.model_validate(reference("policy", leaf.resource_id, 3))
        }
    )
    with pytest.raises(DomainError) as cycle:
        await ExecutionPolicyResolver(s.service.store).resolve(ctx)
    assert cycle.value.failure.code == "execution_policy_cycle"
    for index in range(9):
        payload = {**s.policy, "id": f"depth-{index}", "revision": 1}
        if index < 8:
            payload["parent_policy_ref"] = reference("policy", f"depth-{index + 1}")
        await s.service.store.put(
            ctx.principal,
            "execution.policies",
            payload["id"],
            "CapabilityPolicy",
            payload,
            expected_revision=0,
            request_id=payload["id"],
        )
    deep = ctx.model_copy(
        update={"capability_policy_ref": Ref.model_validate(reference("policy", "depth-0"))}
    )
    with pytest.raises(DomainError) as depth:
        await ExecutionPolicyResolver(s.service.store).resolve(deep)
    assert depth.value.failure.code == "execution_policy_depth"


async def test_hash_scope_capability_and_unsupported_flag_refs_fail_closed(approval_case):
    s = approval_case
    resolver = ExecutionPolicyResolver(s.service.store)
    for ctx in (
        s.ctx.model_copy(
            update={
                "capability_policy_ref": Ref.model_validate(
                    {**s.ctx.capability_policy_ref.wire(), "content_hash": "0" * 64}
                )
            }
        ),
        s.ctx.model_copy(
            update={
                "scope": s.ctx.scope.model_copy(
                    update={
                        "resource_refs": (
                            *s.ctx.scope.resource_refs,
                            Ref(kind="workspace", id="unapproved", version="1"),
                        )
                    }
                )
            }
        ),
        s.ctx.model_copy(
            update={
                "scope": s.ctx.scope.model_copy(
                    update={"capabilities": ("tool.invoke", "workspace.exec")}
                )
            }
        ),
    ):
        with pytest.raises(DomainError):
            await resolver.resolve(ctx)
    await s.service.store.put(
        s.ctx.principal,
        "execution.policies",
        s.policy["id"],
        "CapabilityPolicy",
        {
            **s.policy,
            "revision": 2,
            "feature_flag_refs": [reference("configuration", "unresolved-flag")],
        },
        expected_revision=1,
        request_id="flag-policy",
    )
    ctx = s.ctx.model_copy(
        update={"capability_policy_ref": Ref.model_validate(reference("policy", s.policy["id"], 2))}
    )
    with pytest.raises(DomainError) as unavailable:
        await resolver.resolve(ctx)
    assert unavailable.value.failure.code == "capability_unavailable"


async def test_policy_change_during_traversal_is_detected(approval_case):
    s = approval_case

    class ChangingStore(PostgresRecordStore):
        changed = False

        async def get(self, principal, namespace, resource_id, *, revision=None):
            value = await super().get(principal, namespace, resource_id, revision=revision)
            if namespace == "execution.policies" and not self.changed:
                self.changed = True
                await self.put(
                    principal,
                    namespace,
                    resource_id,
                    "CapabilityPolicy",
                    {**value.payload, "revision": 2, "denied_capabilities": ["tool.invoke"]},
                    expected_revision=1,
                    request_id="concurrent-revoke",
                )
            return value

    with pytest.raises(DomainError) as changed:
        await ExecutionPolicyResolver(ChangingStore(s.service.store.database)).resolve(s.ctx)
    assert changed.value.failure.code == "execution_policy_stale"


async def test_approval_uses_parent_permissions_and_rechecks_revocation(approval_case):
    s = approval_case
    s.ctx, parent = await attach_parent(s.service.store, s.ctx)
    grant = await approved(s)
    assert (
        await s.service.recheck(Ref.model_validate(grant["approval_ref"]), s.request, s.ctx)
        == grant
    )
    await s.service.store.put(
        s.ctx.principal,
        "execution.policies",
        parent["id"],
        "CapabilityPolicy",
        {**parent, "revision": 2, "denied_capabilities": ["tool.invoke"]},
        expected_revision=1,
        request_id="revoke-approved-parent",
    )
    with pytest.raises(DomainError) as stale:
        await s.service.recheck(Ref.model_validate(grant["approval_ref"]), s.request, s.ctx)
    assert stale.value.failure.code == "approval_permission_stale"


async def test_context_and_model_obey_same_parent_and_network(understanding, case, domain):
    ctx, parent = await attach_parent(domain[1].store, understanding.ctx)
    sources = RunContextSources(domain[1].store)
    await sources.authorize(ctx)
    # Explicit network widening is rejected for both data reading and model generation.
    leaf = await domain[1].store.get(
        ctx.principal, "execution.policies", ctx.capability_policy_ref.id
    )
    await domain[1].store.put(
        ctx.principal,
        "execution.policies",
        leaf.resource_id,
        "CapabilityPolicy",
        {
            **leaf.payload,
            "revision": leaf.revision + 1,
            "network_allowlist": ["127.0.0.1", "unapproved.example"],
        },
        expected_revision=leaf.revision,
        request_id="widen-network",
    )
    forged = ctx.model_copy(
        update={
            "capability_policy_ref": Ref.model_validate(
                reference("policy", leaf.resource_id, leaf.revision + 1)
            )
        }
    )
    with pytest.raises(DomainError) as denied:
        await sources.authorize(forged)
    assert denied.value.failure.code == "execution_policy_escalation"
    result = await case.model.generate(case.request, forged)
    assert result["kind"] == "denied" and not case.requests
    assert parent["network_allowlist"] == ["127.0.0.1"]


async def test_inflight_model_parent_revocation_stops_work_and_preserves_unknown_cost(case, domain):
    case.ctx, parent = await attach_parent(domain[1].store, case.ctx)
    started, stopped = asyncio.Event(), asyncio.Event()

    async def pending(request):
        case.requests.append(request)
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            stopped.set()

    await case.model.gateway.adapter.close()
    case.model.gateway.adapter = ChatCompletionsAdapter(
        httpx.AsyncClient(transport=httpx.MockTransport(pending))
    )
    operation = asyncio.create_task(case.model.generate(case.request, case.ctx))
    try:
        await asyncio.wait_for(started.wait(), 15)
        await domain[1].store.put(
            case.ctx.principal,
            "execution.policies",
            parent["id"],
            "CapabilityPolicy",
            {**parent, "revision": 2, "denied_capabilities": ["model.generate"]},
            expected_revision=1,
            request_id="inflight-parent-revoke",
        )
        result = await asyncio.wait_for(operation, 15)
        assert result["failure"]["code"] == "model_capability_changed"
        assert stopped.is_set() and len(case.requests) == 1
        ledger = (
            await domain[1].store.get(case.ctx.principal, "budget.ledgers", case.ctx.run_id)
        ).payload
        assert ledger["billing_pending"] and ledger["held"]["money"] == "0.250000000"
    finally:
        if not operation.done():
            operation.cancel()
            await asyncio.gather(operation, return_exceptions=True)


async def test_scope_cancel_deadline_and_composition_share_actual_resolver(approval_case, domain):
    s = approval_case
    resolver = ExecutionPolicyResolver(s.service.store)
    expired = s.ctx.model_copy(
        update={"deadline": (datetime.now(UTC) - timedelta(seconds=1)).isoformat()}
    )
    with pytest.raises(DomainError) as timeout:
        await resolver.resolve(expired)
    assert timeout.value.failure.category == "timeout"
    outside = s.ctx.model_copy(update={"task_id": "other-task"})
    with pytest.raises(DomainError) as denied:
        await resolver.resolve(outside)
    assert denied.value.failure.code == "execution_scope_denied"
    container = compose(
        Settings(
            profile="development",
            development_principal_id=s.ctx.principal.id,
            database_url=domain[1].store.database.engine.url.render_as_string(hide_password=False),
        )
    )
    try:
        assert container.execution_permissions is not None
        assert (
            container.model_service.gateway.policies.permissions is container.execution_permissions
        )
        assert container.approvals.permissions is container.execution_permissions
        assert (
            container.context_components.sources.readers["input"].permissions
            is container.execution_permissions
        )
        assert not container.bindings.availability()["tool"]
        assert not container.bindings.availability()["workspace"]
    finally:
        await container.close()
    await domain[1].control(
        s.ctx.principal,
        {
            "run_id": s.ctx.run_id,
            "control": {
                "mode": "cancel",
                "preserve_refs": [],
                "reason": "Stop permission reads",
            },
        },
        meta("cancel-permissions", 2),
    )
    with pytest.raises(DomainError) as cancelled:
        await resolver.resolve(s.ctx)
    assert cancelled.value.failure.category == "cancelled"
