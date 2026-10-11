"""Original file SQL decisions routed to the owning authority; no native read claimed."""

import pytest

from tests.integration.agent.test_installed_file_authority import (
    domain as domain,
)
from tests.integration.agent.test_installed_file_authority import (
    file_data_case as file_data_case,
)
from tests.integration.agent.test_installed_file_authority import (
    original_file_gate as original_file_gate,
)
from tests.integration.agent.test_installed_file_authority import (
    tool_case as tool_case,
)
from tests.integration.test_control_plane import meta
from uaw.run.approval_router import RoutedApprovals, ToolApprovalRoute
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError


@pytest.mark.parametrize("decision", ["approve_once", "decline"])
async def test_routes_original_pending_decision_and_recheck(original_file_gate, decision):
    gate, service, _, ctx, c = original_file_gate
    authority = gate.approvals.authority
    call, spec, _ = await gate.ledger.action("actual-file-action", ctx)
    router = RoutedApprovals(
        authority.registry,
        gate.ledger,
        (
            ToolApprovalRoute(
                Ref.model_validate(call["tool_ref"]),
                Ref.model_validate(spec["provider_ref"]),
                service,
            ),
        ),
    )
    waiting = await gate.approvals.precheck(call, spec, ctx)
    record = await router.get(ctx.principal, waiting["wait_ref"]["id"])
    assert record["status"] == "pending"
    with pytest.raises(DomainError) as owner:
        await router.get(
            ctx.principal.model_copy(update={"auth_session_id": "other-session"}), record["id"]
        )
    assert owner.value.failure.code == "approval_route_owner_denied"
    await router.decide(
        ctx.principal,
        {
            "approval_id": record["id"],
            "decision": {
                "decision": decision,
                "expected_arguments_hash": record["arguments_hash"],
                "expected_resource_refs": record["resource_refs"],
                "reason": "Controlled SQL decision",
            },
        },
        meta("router-decision", record["revision"]),
    )
    current = await router.get(ctx.principal, record["id"])
    assert current["status"] == {"approve_once": "approved", "decline": "declined"}[decision]
    binding = (await c.records.get(ctx.principal, "approval.bindings", record["id"])).payload
    if decision == "approve_once":
        assert await router.recheck(
            Ref(kind="approval", id=record["id"], version=str(current["revision"])),
            binding["request"],
            ctx,
        )
    else:
        with pytest.raises(DomainError):
            await router.recheck(
                Ref(kind="approval", id=record["id"], version=str(current["revision"])),
                binding["request"],
                ctx,
            )
    with pytest.raises(DomainError) as forged:
        await router.request(
            {**binding["request"], "arguments_hash": "a" * 64}, meta("forged-route"), ctx
        )
    assert forged.value.failure.code == "approval_route_action_denied"


async def test_constructor_rejects_changed_hash_and_duplicate_services(original_file_gate):
    gate, service, _, ctx, _ = original_file_gate
    call, spec, _ = await gate.ledger.action("actual-file-action", ctx)
    route = ToolApprovalRoute(
        Ref.model_validate(call["tool_ref"]), Ref.model_validate(spec["provider_ref"]), service
    )
    with pytest.raises(ValueError):
        RoutedApprovals(gate.approvals.authority.registry, gate.ledger, (route, route))
    with pytest.raises((ValueError, DomainError)):
        RoutedApprovals(
            gate.approvals.authority.registry,
            gate.ledger,
            (
                ToolApprovalRoute(
                    route.tool_ref.model_copy(update={"content_hash": "b" * 64}),
                    route.provider_ref,
                    service,
                ),
            ),
        )
