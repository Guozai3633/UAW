"""Real SQL consent/authority tests. The controlled action reader is not a product tool."""

import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from pydantic import SecretStr

from tests.integration.test_control_plane import admitted, meta
from tests.integration.test_control_plane import domain as domain
from uaw.api.application import create_app
from uaw.composition import Container, RuntimeBindings, compose
from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.db.transactions import reference
from uaw.run.approval import ApprovalService
from uaw.shared.contracts import Principal, Ref, Scope, TrustedExecutionContext
from uaw.shared.errors import DomainError, reject
from uaw.shared.settings import Settings
from uaw.shared.stores import StoreConflict, StoreMissing


class SQLActionReader:
    def __init__(self, store):
        self.store = store

    async def check(self, request, ctx):
        fixed = await self.store.get(ctx.principal, "approval.test.actions", request["action_id"])
        if fixed.payload != request:
            raise reject("action_stale", "Controlled action changed", 412)
        for resource in request["resource_refs"]:
            current = await self.store.get(ctx.principal, "inputs", resource["id"])
            if str(current.revision) != resource["version"]:
                raise reject("resource_stale", "Resource version changed", 412)


@dataclass
class ApprovalCase:
    service: ApprovalService
    ctx: TrustedExecutionContext
    request: dict
    policy: dict


@pytest.fixture
async def approval_case(domain, principal):
    configuration, run, _ = domain
    record = await admitted(domain, principal)
    await run.advance(principal, record["id"], "preparing", meta("prepare", 1))
    source = (await run.store.get(principal, "run.bindings", record["id"])).payload["input_ref"]
    scope = Scope(
        principal_id=principal.id,
        conversation_id=record["conversation_id"],
        task_id=record["task_id"],
        resource_refs=(Ref.model_validate(source),),
        capabilities=("tool.invoke",),
    )
    policy = {
        "id": "execution-test-policy",
        "revision": 1,
        "allowed_capabilities": ["tool.invoke"],
        "denied_capabilities": [],
        "resource_scope": {
            "conversation_id": record["conversation_id"],
            "task_id": record["task_id"],
            "resource_refs": [source],
        },
        "network_allowlist": [],
        "feature_flag_refs": [],
    }
    await run.store.put(
        principal,
        "execution.policies",
        policy["id"],
        "CapabilityPolicy",
        policy,
        expected_revision=0,
        request_id="policy",
    )
    ctx = TrustedExecutionContext(
        principal=principal,
        scope=scope,
        run_id=record["id"],
        conversation_id=record["conversation_id"],
        task_id=record["task_id"],
        operation_id="operation-test",
        trace_id="trace-test",
        attempt_id="attempt-test",
        deadline=record["budget"]["deadline"],
        capability_policy_ref=reference("policy", policy["id"]),
    )
    request = {
        "action_id": "action-test",
        "arguments_hash": parameter_hash({"text": "原文  空白"}),
        "resource_refs": [source],
        "effect": "internal_write",
        "summary": "Controlled fixture action",
        "expires_at": record["budget"]["deadline"],
    }
    await run.store.put(
        principal,
        "approval.test.actions",
        request["action_id"],
        "ApprovalCreateRequest",
        request,
        expected_revision=0,
        request_id="action",
    )
    return ApprovalCase(
        ApprovalService(run.store, configuration, SQLActionReader(run.store)), ctx, request, policy
    )


def decision(case, approval, kind="approve_once"):
    return {
        "approval_id": approval["id"],
        "decision": {
            "decision": kind,
            "expected_arguments_hash": case.request["arguments_hash"],
            "expected_resource_refs": case.request["resource_refs"],
            "reason": "User decision",
        },
    }


async def pending(case):
    return await case.service.request(case.request, meta("approval-create"), case.ctx)


async def approved(case):
    approval = await pending(case)
    return await case.service.decide(
        case.ctx.principal, decision(case, approval), meta("approve", 1)
    )


async def test_durable_decision_restart_events_and_current_request_replay(approval_case, domain):
    case = approval_case
    grant = await approved(case)
    restarted = ApprovalService(
        case.service.store, case.service.configuration, case.service.authority
    )
    current = await restarted.get(case.ctx.principal, grant["approval_ref"]["id"])
    assert current["status"] == "approved" and current["revision"] == 2
    ref = Ref.model_validate(grant["approval_ref"])
    assert await restarted.recheck(ref, case.request, case.ctx) == grant
    assert (
        await restarted.decide(case.ctx.principal, decision(case, current), meta("approve", 1))
        == grant
    )
    assert (await pending(case))["status"] == "approved"  # Never replay obsolete pending status.
    events = await domain[1].events.read(case.ctx.principal, case.ctx.conversation_id, limit=100)
    assert [e["type"] for e in events["items"]].count("approval.required") == 1
    assert [e["type"] for e in events["items"]].count("approval.decided") == 1


async def test_decision_cas_race_has_one_winner(approval_case):
    case = approval_case
    approval = await pending(case)
    results = await asyncio.gather(
        case.service.decide(case.ctx.principal, decision(case, approval), meta("approve-a", 1)),
        case.service.decide(
            case.ctx.principal, decision(case, approval, "decline"), meta("decline-b", 1)
        ),
        return_exceptions=True,
    )
    assert sum(isinstance(r, dict) for r in results) == 1
    assert sum(isinstance(r, StoreConflict) for r in results) == 1


@pytest.mark.parametrize("kind", ["decline", "cancel"])
async def test_negative_decision_cannot_be_reused_or_recreated(approval_case, kind):
    case = approval_case
    approval = await pending(case)
    grant = await case.service.decide(
        case.ctx.principal, decision(case, approval, kind), meta("decide", 1)
    )
    with pytest.raises(DomainError):
        await case.service.recheck(
            Ref.model_validate(grant["approval_ref"]), case.request, case.ctx
        )
    with pytest.raises(StoreConflict):
        await case.service.request(case.request, meta("new-request-id"), case.ctx)


async def test_hash_resource_and_context_tampering_never_approve(approval_case):
    case = approval_case
    approval = await pending(case)
    request = decision(case, approval)
    for field, value in (("expected_arguments_hash", "0" * 64), ("expected_resource_refs", [])):
        altered = json.loads(json.dumps(request))
        altered["decision"][field] = value
        with pytest.raises(DomainError) as caught:
            await case.service.decide(case.ctx.principal, altered, meta("bad-" + field, 1))
        assert caught.value.status_code == 412
    grant = await case.service.decide(case.ctx.principal, request, meta("approve", 1))
    for altered in (
        case.ctx.model_copy(update={"operation_id": "other-operation"}),
        case.ctx.model_copy(
            update={"deadline": (datetime.now(UTC) + timedelta(days=1)).isoformat()}
        ),
    ):
        with pytest.raises(DomainError):
            await case.service.recheck(
                Ref.model_validate(grant["approval_ref"]), case.request, altered
            )


async def test_current_policy_revocation_and_missing_action_adapter(approval_case):
    case = approval_case
    grant = await approved(case)
    await case.service.store.put(
        case.ctx.principal,
        "execution.policies",
        case.policy["id"],
        "CapabilityPolicy",
        {**case.policy, "revision": 2, "denied_capabilities": ["tool.invoke"]},
        expected_revision=1,
        request_id="revoke",
    )
    with pytest.raises(DomainError) as caught:
        await case.service.recheck(
            Ref.model_validate(grant["approval_ref"]), case.request, case.ctx
        )
    assert caught.value.failure.code == "approval_permission_stale"


async def test_live_resource_deletion_and_action_change(approval_case):
    case = approval_case
    grant = await approved(case)
    await case.service.store.delete(
        case.ctx.principal,
        "inputs",
        case.request["resource_refs"][0]["id"],
        expected_revision=1,
        request_id="delete-source",
    )
    with pytest.raises(StoreMissing):
        await case.service.recheck(
            Ref.model_validate(grant["approval_ref"]), case.request, case.ctx
        )


async def test_cancel_expiry_and_no_default_adapter(approval_case, domain):
    case = approval_case
    unbound = ApprovalService(case.service.store, case.service.configuration)
    with pytest.raises(DomainError) as caught:
        await unbound.request(case.request, meta("unbound"), case.ctx)
    assert caught.value.failure.code == "capability_unavailable"
    grant = await approved(case)
    await domain[1].control(
        case.ctx.principal,
        {
            "run_id": case.ctx.run_id,
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop"},
        },
        meta("cancel", 2),
    )
    current = await case.service.get(case.ctx.principal, grant["approval_ref"]["id"])
    assert current["status"] == "cancelled" and current["revision"] == 3
    with pytest.raises(DomainError):
        await case.service.recheck(
            Ref.model_validate(grant["approval_ref"]), case.request, case.ctx
        )


async def test_approval_expiration_is_persisted(approval_case):
    case = approval_case
    approval = await pending(case)
    ledger = await case.service.store.get(case.ctx.principal, "budget.ledgers", case.ctx.run_id)
    await case.service.store.put(
        case.ctx.principal,
        "budget.ledgers",
        ledger.resource_id,
        "RootBudgetLedger",
        {
            **ledger.payload,
            "revision": 2,
            "deadline": (datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
        },
        expected_revision=1,
        request_id="expire",
    )
    current = await case.service.get(case.ctx.principal, approval["id"])
    assert current["status"] == "expired" and current["revision"] == 2
    assert await case.service.get(case.ctx.principal, approval["id"]) == current


async def test_only_authenticated_owner_can_decide(approval_case):
    case = approval_case
    approval = await pending(case)
    for actor in (
        Principal(id="other-user", kind="user", auth_session_id="s"),
        case.ctx.principal.model_copy(update={"kind": "service"}),
        case.ctx.principal.model_copy(update={"delegated_by": "agent"}),
    ):
        with pytest.raises(DomainError):
            await case.service.decide(actor, decision(case, approval), meta("forged", 1))
    with pytest.raises(DomainError):
        await case.service.decide(case.ctx.principal, decision(case, approval), meta("no-cas"))


async def test_http_approval_read_and_decide_are_authenticated(approval_case, domain):
    case = approval_case
    approval = await pending(case)
    settings = Settings(
        profile="development",
        development_principal_id=case.ctx.principal.id,
        development_user_token=SecretStr("u" * 40),
        cursor_signing_key=SecretStr("k" * 40),
    )
    container = Container(
        settings,
        RuntimeBindings(),
        records=case.service.store,
        configuration=domain[0],
        run_service=domain[1],
        approvals=case.service,
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(container)),
        base_url="http://127.0.0.1",
    ) as client:
        path = "/v1/approvals/" + approval["id"]
        assert (await client.get(path)).status_code == 401
        headers = {"Authorization": "Bearer " + "u" * 40}
        response = await client.get(path, headers=headers)
        assert response.status_code == 200 and response.json()["payload"]["status"] == "pending"
        payload = decision(case, approval)
        del payload["approval_id"]
        response = await client.post(
            path + "/decisions",
            headers=headers,
            json={"meta": meta("http-decide", 1).wire(), "payload": payload},
        )
        assert response.status_code == 200 and response.json()["payload"]["actor"]["kind"] == "user"


def test_default_composition_exposes_consent_service_but_no_product_tool():
    container = compose(
        Settings(
            profile="development",
            development_principal_id="fixture-user",
            database_url=SecretStr("postgresql+psycopg://unused@localhost/unused"),
        )
    )
    assert container.approvals is not None and container.approvals.authority is None
    assert not container.bindings.availability()["tool"]


async def test_current_action_effect_change_and_policy_revision_are_denied(approval_case, domain):
    case = approval_case
    grant = await approved(case)
    await case.service.store.put(
        case.ctx.principal,
        "approval.test.actions",
        case.request["action_id"],
        "ApprovalCreateRequest",
        {**case.request, "effect": "external_write"},
        expected_revision=1,
        request_id="action-change",
    )
    with pytest.raises(DomainError) as caught:
        await case.service.recheck(
            Ref.model_validate(grant["approval_ref"]), case.request, case.ctx
        )
    assert caught.value.failure.code == "action_stale"
    configuration, _, admin = domain
    await configuration.register(
        admin,
        "policy",
        {
            "draft": {
                "name": "manual-policy",
                "payload": {
                    "id": "manual-policy",
                    "revision": 1,
                    "default_mode": "manual",
                    "allowed_modes": ["manual"],
                    "rules": [],
                },
            }
        },
        meta("change-approval-policy", 1),
    )
    with pytest.raises(DomainError) as stale:
        await case.service.recheck(
            Ref.model_validate(grant["approval_ref"]), case.request, case.ctx
        )
    assert stale.value.failure.code == "approval_policy_stale"


async def test_scoped_grants_and_scope_escalation_are_unavailable(approval_case):
    case = approval_case
    approval = await pending(case)
    request = decision(case, approval, "approve_scoped")
    request["decision"].update(
        scope_selector={"resource_refs": case.request["resource_refs"]},
        expires_at=case.ctx.deadline,
    )
    with pytest.raises(DomainError) as caught:
        await case.service.decide(case.ctx.principal, request, meta("scope-grant", 1))
    assert caught.value.failure.code == "capability_unavailable"
    forged = case.ctx.model_copy(
        update={
            "scope": case.ctx.scope.model_copy(
                update={"capabilities": ("tool.invoke", "workspace.exec")}
            )
        }
    )
    with pytest.raises(DomainError):
        await case.service.request(case.request, meta("forged-capability"), forged)
