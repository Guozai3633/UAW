"""Real PostgreSQL domain transactions and the development authentication boundary."""

import asyncio
import json
import secrets
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import delete, select

from uaw.api.application import create_app
from uaw.composition import Container, RuntimeBindings
from uaw.infrastructure.credentials import WindowsCredentialStore
from uaw.infrastructure.db.models import OutboxRow, RecordRow, RecordVersionRow, RequestRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.session import Database
from uaw.infrastructure.db.transactions import reference
from uaw.run.budget import BudgetService
from uaw.run.events import EventReader
from uaw.run.facade import DEFAULT_LIMITS, RunFacade
from uaw.shared.configuration import DEFAULT_DISABLED, ConfigurationService
from uaw.shared.contracts import Principal, RequestMeta, Scope, TrustedExecutionContext
from uaw.shared.errors import DomainError
from uaw.shared.schema import ContractViolation, validate_contract
from uaw.shared.settings import Settings

Payload = dict[str, Any]


def meta(name: str, revision: int | None = None) -> RequestMeta:
    return RequestMeta(request_id=name, schema_version="0.1", expected_revision=revision)


@pytest.fixture
async def domain(
    database: Database, principal: Principal
) -> AsyncIterator[tuple[ConfigurationService, RunFacade, Principal]]:
    platform = Principal(
        id=f"platform-{principal.id}", kind="service", auth_session_id="platform-session"
    )
    admin = Principal(id=f"admin-{principal.id}", kind="admin", auth_session_id="admin-session")
    store = PostgresRecordStore(database)
    configuration = ConfigurationService(store, WindowsCredentialStore(platform.id), platform)
    run = RunFacade(
        store, configuration, EventReader(store, SecretStr("cursor-test-key-" + "k" * 32))
    )
    try:
        yield configuration, run, admin
    finally:
        async with database.sessions.begin() as session:
            for table in (OutboxRow, RequestRow, RecordVersionRow, RecordRow):
                await session.execute(delete(table).where(table.principal_id == platform.id))


async def seed(configuration: ConfigurationService, admin: Principal) -> Payload:
    provider = await configuration.register(
        admin,
        "provider",
        {
            "provider": {
                "id": "fixture-provider",
                "kind": "model",
                "endpoint": "https://provider.invalid/v1",
                "profile_ref": reference("provider_profile", "model.http"),
                "settings": {"model_name": "fixture-model", "timeout_ms": 30000},
            }
        },
        meta("provider"),
    )
    assert provider["state"] == "disconnected"  # No network/protocol probe is claimed.
    await configuration.register(
        admin,
        "model",
        {
            "entry": {
                "id": "fixture-model",
                "provider_ref": reference("provider", provider["id"]),
                "display_name": "Protocol fixture",
                "context_limit_tokens": 100000,
                "output_limit_tokens": 16000,
                "capabilities": ["text"],
            }
        },
        meta("model"),
    )
    approval = await configuration.register(
        admin,
        "policy",
        {
            "draft": {
                "name": "manual-policy",
                "payload": {
                    "id": "manual-policy",
                    "revision": 0,
                    "default_mode": "manual",
                    "allowed_modes": ["manual"],
                    "rules": [],
                },
            }
        },
        meta("approval"),
    )
    storage = await configuration.register(
        admin,
        "policy",
        {
            "draft": {
                "name": "dev-storage",
                "payload": {
                    "mode": "local_authoritative",
                    "local_cache_enabled": False,
                    "encrypted": False,
                    "revision": 0,
                },
            }
        },
        meta("storage"),
    )
    staged = await configuration.stage(
        admin,
        {
            "configuration": {
                "model_refs": [reference("model", "fixture-model")],
                "provider_refs": [reference("provider", provider["id"])],
                "environment_template_refs": [],
                "feature_flags": [
                    {
                        "id": flag,
                        "enabled": False,
                        "scope": {"resource_refs": []},
                        "reason": "Not implemented",
                    }
                    for flag in DEFAULT_DISABLED
                ],
                "approval_policy_ref": approval,
                "storage_policy_ref": storage,
            }
        },
        meta("stage"),
    )
    await configuration.validate(admin, staged["id"], meta("validate", 1))
    active = await configuration.activate(admin, staged["id"], meta("activate", 2))
    assert active["state"] == "active"
    return active


async def conversation(
    domain: tuple[ConfigurationService, RunFacade, Principal], actor: Principal
) -> Payload:
    configuration, run, admin = domain
    await seed(configuration, admin)
    return await run.create_conversation(
        actor,
        {
            "title": "中文任务",
            "model_choice": {"mode": "explicit", "model_id": "fixture-model"},
            "memory_policy": {
                "revision": 0,
                "read_enabled": False,
                "contribute_enabled": False,
                "scope": {"resource_refs": []},
            },
        },
        meta("create-conversation"),
    )


async def admitted(
    domain: tuple[ConfigurationService, RunFacade, Principal], actor: Principal
) -> Payload:
    conv = await conversation(domain, actor)
    return await domain[1].submit(
        actor,
        {
            "conversation_id": conv["id"],
            "text": "分析这个任务，保留  原文\n和换行。",
            "attachment_refs": [],
        },
        meta("submit"),
    )


async def test_configuration_fixed_revision_and_live_revocation(domain, principal):
    configuration, _, admin = domain
    active = await seed(configuration, admin)
    ref = reference("configuration", active["id"], active["revision"])
    assert await configuration.snapshot(ref) == active
    with pytest.raises(DomainError) as denied:
        await configuration.revoke_provider(principal, "fixture-provider", meta("forged-revoke", 1))
    assert denied.value.status_code == 403
    revoked = await configuration.revoke_provider(admin, "fixture-provider", meta("revoke", 1))
    assert revoked["state"] == "revoked"
    assert await configuration.snapshot(ref) == active
    with pytest.raises(DomainError) as blocked:
        await configuration.require_model("fixture-model", active)
    assert blocked.value.failure.code == "provider_revoked"
    assert (await configuration.models())["items"] == []


async def test_all_capability_boundaries_fail_closed(domain):
    configuration, _, admin = domain
    active = await seed(configuration, admin)
    ref = reference("configuration", active["id"], active["revision"])
    for boundary in ("discovery", "call", "resume", "child"):
        with pytest.raises(DomainError) as denied:
            await configuration.require_capability(
                "code_execution", ref, {}, implemented=True, boundary=boundary
            )
        assert denied.value.failure.code == "feature_disabled"
    invalid = {k: v for k, v in active.items() if k not in ("id", "state", "revision")}
    invalid["feature_flags"] = [
        {
            "id": "code_execution",
            "enabled": True,
            "scope": {"resource_refs": []},
            "reason": "forged",
        }
    ]
    staged = await configuration.stage(admin, {"configuration": invalid}, meta("stage-invalid"))
    with pytest.raises(DomainError):
        await configuration.validate(admin, staged["id"], meta("validate-invalid", 1))
    assert (
        await configuration.store.get(configuration.platform, "configurations", staged["id"])
    ).revision == 1


async def test_windows_secret_write_retry_and_no_database_plaintext(domain, principal):
    configuration, _, admin = domain
    secret = secrets.token_urlsafe(48)
    request = {"provider_id": "fixture-provider", "secret": secret}
    receipt = await configuration.put_secret(admin, request, meta("credential"))
    handle = receipt["credential_handle"]
    try:
        assert await configuration.put_secret(admin, request, meta("credential")) == receipt
        assert (
            await WindowsCredentialStore(configuration.platform.id).resolve(handle)
        ).get_secret_value() == secret
        with pytest.raises(DomainError):
            await configuration.put_secret(
                admin, {**request, "secret": "changed"}, meta("credential")
            )
        with pytest.raises(DomainError):
            await configuration.put_secret(principal, request, meta("user-secret"))
        async with configuration.store.database.sessions() as session:
            rows = (
                await session.scalars(
                    select(RecordRow).where(RecordRow.principal_id == configuration.platform.id)
                )
            ).all()
            requests = (
                await session.scalars(
                    select(RequestRow).where(RequestRow.principal_id == configuration.platform.id)
                )
            ).all()
            assert secret not in json.dumps(
                [r.payload for r in rows] + [r.result for r in requests]
            )
        assert set(receipt) == {"credential_handle", "version"}
    finally:
        await configuration.credentials.delete(handle)


async def test_concurrent_secret_retry_cannot_replace_the_first_secret(domain):
    configuration, _, admin = domain
    values = [secrets.token_urlsafe(24), secrets.token_urlsafe(24)]
    results = await asyncio.gather(
        *(
            configuration.put_secret(
                admin, {"provider_id": "fixture-provider", "secret": value}, meta("race-secret")
            )
            for value in values
        ),
        return_exceptions=True,
    )
    winner = next(index for index, result in enumerate(results) if isinstance(result, dict))
    receipt = results[winner]
    assert isinstance(receipt, dict)
    handle = receipt["credential_handle"]
    try:
        assert isinstance(results[1 - winner], DomainError)
        assert (await configuration.credentials.resolve(handle)).get_secret_value() == values[
            winner
        ]
    finally:
        await configuration.credentials.delete(handle)


async def test_submit_concurrent_retry_original_immutable_and_owner_partition(domain, principal):
    conv = await conversation(domain, principal)
    run = domain[1]
    request = {"conversation_id": conv["id"], "text": "  原文\n第二行  ", "attachment_refs": []}
    first, repeated = await asyncio.gather(
        run.submit(principal, request, meta("same")), run.submit(principal, request, meta("same"))
    )
    assert first == repeated
    bindings = (await run.store.get(principal, "run.bindings", first["id"])).payload
    original = (await run.store.get(principal, "inputs", bindings["input_ref"]["id"])).payload
    assert original["text"] == request["text"]
    assert first["status"] == "queued" and "outcome" not in first
    with pytest.raises(DomainError) as changed:
        await run.submit(principal, {**request, "text": "新原文"}, meta("same"))
    assert changed.value.failure.code == "idempotency_conflict"
    other = Principal(id="another-user", kind="user", auth_session_id="other-session")
    with pytest.raises(DomainError) as hidden:
        await run.get_run(other, first["id"])
    assert hidden.value.status_code == 404
    assert len((await run.events.read(principal, conv["id"]))["items"]) == 3
    policy = (
        await run.store.get(principal, "model.policies", bindings["model_policy_ref"]["id"])
    ).payload
    source = (await run.store.get(principal, "inputs", policy["source_input_ref"]["id"])).payload
    assert json.loads(source["text"])["model_id"] == policy["fixed_model_id"] == "fixture-model"


async def test_admission_rollback_leaves_no_original_or_events(domain, principal):
    conv = await conversation(domain, principal)
    run = domain[1]
    bad_budget = {
        "limits": {**DEFAULT_LIMITS, "money": "1000000"},
        "max_steps": 64,
        "max_depth": 2,
        "deadline": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
    }
    with pytest.raises(DomainError):
        await run.submit(
            principal,
            {
                "conversation_id": conv["id"],
                "text": "Must rollback",
                "attachment_refs": [],
                "budget": bad_budget,
            },
            meta("failed-admission"),
        )
    assert (await run.events.read(principal, conv["id"]))["items"] == []
    async with run.store.database.sessions() as session:
        rows = (
            await session.scalars(
                select(RecordRow).where(
                    RecordRow.principal_id == principal.id, RecordRow.namespace == "inputs"
                )
            )
        ).all()
        assert len(rows) == 1 and rows[0].payload["text"] != "Must rollback"


async def test_state_replay_cursor_scope_and_queued_cancel(domain, principal):
    record = await admitted(domain, principal)
    run = domain[1]
    with pytest.raises(DomainError):
        await run.advance(principal, record["id"], "running", meta("skip", 1))
    with pytest.raises(DomainError) as terminal:
        await run.advance(principal, record["id"], "completed", meta("fake-completion", 1))
    assert terminal.value.failure.code == "completion_controller_required"
    before = await run.events.read(principal, record["conversation_id"], limit=1)
    cancel = {
        "run_id": record["id"],
        "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop"},
    }
    ack = await run.control(principal, cancel, meta("cancel", 1))
    assert ack["status"] == "completed"
    assert await run.control(principal, cancel, meta("cancel", 1)) == ack
    assert (await run.get_run(principal, record["id"]))["status"] == "cancelled"
    resumed = await run.events.read(
        principal, record["conversation_id"], cursor=before["next_cursor"]
    )
    assert resumed["snapshot_revision"] == before["snapshot_revision"] == 3
    assert [e["seq"] for e in resumed["items"]] == [2, 3]
    with pytest.raises(DomainError):
        await run.events.read(
            principal, record["conversation_id"], cursor=before["next_cursor"] + "f"
        )
    with pytest.raises(DomainError):
        await run.events.read(
            principal, record["conversation_id"], cursor=before["next_cursor"], items=True
        )
    items = await run.events.read(principal, record["conversation_id"], items=True)
    assert [item["type"] for item in items["items"]] == ["user_message", "user_control"]
    assert len((await run.events.read(principal, record["conversation_id"]))["items"]) == 5


def context(
    principal: Principal, record: Payload, attempt: str = "attempt-1"
) -> TrustedExecutionContext:
    return TrustedExecutionContext(
        principal=principal,
        scope=Scope(principal_id=principal.id, conversation_id=record["conversation_id"]),
        run_id=record["id"],
        conversation_id=record["conversation_id"],
        operation_id="operation-1",
        trace_id="trace-1",
        attempt_id=attempt,
        deadline=record["budget"]["deadline"],
        capability_policy_ref=reference("policy", "manual-policy"),
    )


async def prepared_budget(domain, principal):
    record = await admitted(domain, principal)
    await domain[1].advance(principal, record["id"], "preparing", meta("prepare", 1))
    budgets = BudgetService(domain[1].store)
    ctx = context(principal, record)
    estimates = {
        **DEFAULT_LIMITS,
        "input_tokens": 500,
        "output_tokens": 100,
        "model_calls": 1,
        "tool_calls": 0,
        "child_agents": 0,
        "wall_time_ms": 1000,
        "money": "0.100000",
    }
    reservation = await budgets.reserve(
        principal,
        {
            "reservation_id": "reservation-1",
            "parent_run_id": record["id"],
            "estimates": estimates,
            "deadline": ctx.deadline,
            "expected_ledger_revision": 1,
        },
        meta("reserve"),
        ctx,
    )
    return record, budgets, ctx, reservation


async def test_failed_attempt_unknown_money_held_then_reconciled_once(domain, principal):
    record, budgets, ctx, reservation = await prepared_budget(domain, principal)
    ref = reference("reservation", reservation["id"])
    await budgets.dispatch(principal, ref, meta("dispatch"), ctx)
    assert (await budgets.dispatch(principal, ref, meta("dispatch"), ctx))["status"] == "unchanged"
    dispatched_ledger = (await budgets.store.get(principal, "budget.ledgers", record["id"])).payload
    assert dispatched_ledger["billing_pending"]
    usage = {
        "attempt_id": ctx.attempt_id,
        "resources": {
            "model_calls": 1,
            "tool_calls": 0,
            "child_agents": 0,
            "wall_time_ms": 500,
            "currency": "USD",
        },
        "billing_state": "pending",
    }
    request = {"reservation_ref": ref, "usage": usage, "expected_ledger_revision": 3}
    result = await budgets.settle(principal, request, meta("settle"), ctx, status="failed")
    assert result["billing_pending"] and result["remaining"]["money"] == "4.900000"
    assert await budgets.settle(principal, request, meta("settle"), ctx, status="failed") == result
    measured = (await budgets.store.get(principal, "usage", result["usage_refs"][0]["id"])).payload
    assert "money" not in measured["resources"] and "input_tokens" not in measured["resources"]
    with pytest.raises(DomainError) as release:
        await budgets.release(principal, result["reservation_ref"], meta("release-unknown"), ctx)
    assert release.value.failure.code == "unknown_usage_held"
    confirmed = {
        **usage,
        "billing_state": "confirmed",
        "resources": {
            **usage["resources"],
            "input_tokens": 450,
            "output_tokens": 80,
            "money": "0.000000001",
        },
        "provider_receipt_id": "fixture-receipt",
    }
    settled = await budgets.settle(
        principal,
        {
            "reservation_ref": result["reservation_ref"],
            "usage": confirmed,
            "expected_ledger_revision": 4,
        },
        meta("reconcile"),
        ctx,
        status="failed",
    )
    assert not settled["billing_pending"] and settled["remaining"]["money"] == "4.999999999"
    ledger = (await budgets.store.get(principal, "budget.ledgers", record["id"])).payload
    assert ledger["used"]["model_calls"] == 1 and ledger["used"]["input_tokens"] == 450
    assert ledger["held"]["input_tokens"] == 0
    trace = (await budgets.store.get(principal, "traces", ctx.attempt_id)).payload
    assert trace["status"] == "failed" and "text" not in trace


async def test_cancel_stops_dispatch_and_unused_reservation_can_release(domain, principal):
    record, budgets, ctx, reservation = await prepared_budget(domain, principal)
    await domain[1].control(
        principal,
        {
            "run_id": record["id"],
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop"},
        },
        meta("stop", 2),
    )
    with pytest.raises(DomainError):
        await budgets.dispatch(
            principal, reference("reservation", reservation["id"]), meta("late-dispatch"), ctx
        )
    released = await budgets.release(
        principal, reference("reservation", reservation["id"]), meta("release"), ctx
    )
    assert released["status"] == "released"
    assert (await domain[1].get_run(principal, record["id"]))["status"] == "preparing"


async def test_http_authentication_role_injection_and_wire_dto(domain, principal):
    configuration, run, admin = domain
    await seed(configuration, admin)
    settings = Settings(
        profile="development",
        development_principal_id=principal.id,
        development_admin_id=admin.id,
        platform_id=configuration.platform.id,
        development_user_token=SecretStr("u" * 40),
        development_admin_token=SecretStr("a" * 40),
        cursor_signing_key=SecretStr("k" * 40),
    )
    container = Container(
        settings=settings,
        bindings=RuntimeBindings(),
        records=run.store,
        configuration=configuration,
        run_service=run,
        budgets=BudgetService(run.store),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(container)), base_url="http://test"
    ) as client:
        assert (await client.get("/v1/models")).status_code == 401
        user = {"Authorization": "Bearer " + "u" * 40}
        assert (await client.get("/v1/admin/configuration", headers=user)).status_code == 403
        assert (
            await client.get("/v1/models", headers={**user, "Origin": "https://untrusted.invalid"})
        ).status_code == 403
        payload = {
            "title": "HTTP session",
            "model_choice": {"mode": "explicit", "model_id": "fixture-model"},
            "memory_policy": {
                "revision": 0,
                "read_enabled": False,
                "contribute_enabled": False,
                "scope": {"resource_refs": []},
            },
        }
        injected = {
            "meta": meta("http-create").wire(),
            "payload": {**payload, "principal": {"kind": "admin"}},
        }
        assert (
            await client.post("/v1/conversations", headers=user, json=injected)
        ).status_code == 422
        created = await client.post(
            "/v1/conversations",
            headers=user,
            json={"meta": meta("http-create").wire(), "payload": payload},
        )
        assert created.status_code == 200
        conv = created.json()["payload"]
        submitted = await client.post(
            f"/v1/conversations/{conv['id']}/turns",
            headers=user,
            json={
                "meta": meta("http-submit").wire(),
                "payload": {"text": "真实受理", "attachment_refs": []},
            },
        )
        assert submitted.status_code == 202 and submitted.json()["payload"]["status"] == "queued"
        assert (
            await client.get(f"/v1/conversations/{conv['id']}/events", headers=user)
        ).status_code == 200
        event = (await client.get(f"/v1/conversations/{conv['id']}/events", headers=user)).json()[
            "payload"
        ]["items"][0]
        actual = await client.get(f"/v1/events/{event['event_id']}/payload", headers=user)
        assert actual.json()["payload"]["parameters"]["text"] == "真实受理"
        assert (await client.get("/v1/models?limit=0", headers=user)).status_code == 422


def test_confirmed_usage_requires_known_money_and_tokens():
    value = {
        "attempt_id": "attempt",
        "resources": {
            "model_calls": 1,
            "tool_calls": 0,
            "child_agents": 0,
            "wall_time_ms": 1,
            "currency": "USD",
        },
        "billing_state": "pending",
    }
    validate_contract("Usage", value)
    with pytest.raises(ContractViolation):
        validate_contract("Usage", {**value, "billing_state": "confirmed"})


async def test_item_updates_keep_identity_and_page_watermark(domain, principal):
    record = await admitted(domain, principal)
    run = domain[1]
    item = await run.create_execution_item(
        principal, record["id"], "agent_message", meta("item-create")
    )
    first_page = await run.events.read(principal, record["conversation_id"], limit=1, items=True)
    started = await run.update_execution_item(
        principal, item["id"], "in_progress", "First version", meta("item-start", 1)
    )
    assert started["id"] == item["id"]
    assert (
        await run.update_execution_item(
            principal, item["id"], "in_progress", "First version", meta("item-start", 1)
        )
        == started
    )
    old_page = await run.events.read(
        principal, record["conversation_id"], items=True, cursor=first_page["next_cursor"]
    )
    assert old_page["items"][0]["status"] == "pending"
    current = await run.events.read(principal, record["conversation_id"], items=True)
    assert len(current["items"]) == 2 and current["items"][1]["text"] == "First version"
    done = await run.update_execution_item(
        principal, item["id"], "completed", "Final message", meta("item-end", 2)
    )
    with pytest.raises(DomainError):
        await run.update_execution_item(
            principal, item["id"], "in_progress", "Reopen", meta("item-reopen", done["revision"])
        )
    assert (await run.get_run(principal, record["id"]))["status"] == "queued"


async def test_runtime_create_uses_its_contract_and_preserves_ingress_original(domain, principal):
    conv = await conversation(domain, principal)
    run = domain[1]
    deadline = (datetime.now(UTC) + timedelta(minutes=5)).isoformat()
    ctx = TrustedExecutionContext(
        principal=principal,
        scope=Scope(principal_id=principal.id, conversation_id=conv["id"]),
        conversation_id=conv["id"],
        operation_id="ingress-operation",
        trace_id="ingress-trace",
        attempt_id="ingress-attempt",
        deadline=deadline,
        capability_policy_ref=reference("policy", "manual-policy"),
    )
    original = {
        "id": "input-from-ingress",
        "conversation_id": conv["id"],
        "turn_id": "turn-from-ingress",
        "text": "  Runtime 原文\n",
        "attachment_refs": [],
        "created_at": datetime.now(UTC).isoformat(),
    }
    request = {
        "conversation_id": conv["id"],
        "input": original,
        "budget": {"limits": DEFAULT_LIMITS, "max_steps": 64, "max_depth": 2, "deadline": deadline},
    }
    result = await run.create(request, meta("runtime-create"), ctx)
    assert result["kind"] == "ok"
    assert await run.create(request, meta("runtime-create"), ctx) == result
    assert (await run.store.get(principal, "inputs", original["id"])).payload == original
    invalid = await run.create(
        {**request, "input": {**original, "conversation_id": "wrong-conversation"}},
        meta("bad-runtime-create"),
        ctx,
    )
    assert invalid["kind"] == "denied"
    validate_contract("RuntimeRunruntimeCreateResult", invalid)


async def test_budget_conflicting_reservations_and_overdrawn_actual_usage(domain, principal):
    record, budgets, ctx, reservation = await prepared_budget(domain, principal)
    other_context = context(principal, record, "attempt-2")
    request = {
        "reservation_id": "reservation-2",
        "parent_run_id": record["id"],
        "estimates": reservation["estimates"],
        "deadline": ctx.deadline,
        "expected_ledger_revision": 2,
    }
    results = await asyncio.gather(
        budgets.reserve(principal, request, meta("reserve-2"), other_context),
        budgets.reserve(
            principal,
            {**request, "reservation_id": "reservation-3"},
            meta("reserve-3"),
            context(principal, record, "attempt-3"),
        ),
        return_exceptions=True,
    )
    assert sum(isinstance(result, dict) for result in results) == 1
    assert sum(isinstance(result, DomainError) for result in results) == 1
    ledger = (await budgets.store.get(principal, "budget.ledgers", record["id"])).payload
    assert ledger["held"]["model_calls"] == 2
    # The same actual attempt cannot be reserved twice with a fresh request ID.
    with pytest.raises(DomainError):
        await budgets.reserve(
            principal,
            {**request, "reservation_id": "duplicate-attempt", "expected_ledger_revision": 3},
            meta("duplicate-attempt"),
            ctx,
        )
    await budgets.dispatch(
        principal, reference("reservation", reservation["id"]), meta("dispatch"), ctx
    )
    usage = {
        "attempt_id": ctx.attempt_id,
        "resources": {**reservation["estimates"], "money": "6.000000"},
        "billing_state": "confirmed",
    }
    result = await budgets.settle(
        principal,
        {
            "reservation_ref": reference("reservation", reservation["id"]),
            "usage": usage,
            "expected_ledger_revision": 4,
        },
        meta("settle-overage"),
        ctx,
        status="failed",
    )
    assert Decimal(result["remaining"]["money"]) == 0
    ledger = (await budgets.store.get(principal, "budget.ledgers", record["id"])).payload
    assert ledger["used"]["money"] == "6.000000" and ledger["overdrawn"]
    with pytest.raises(DomainError) as exhausted:
        await budgets.reserve(
            principal,
            {**request, "reservation_id": "after-overage", "expected_ledger_revision": 5},
            meta("after-overage"),
            context(principal, record, "attempt-4"),
        )
    assert exhausted.value.failure.category == "budget"


async def test_protected_admin_publish_wire_protocol_and_openapi(domain, principal):
    configuration, run, admin = domain
    active = await seed(configuration, admin)
    settings = Settings(
        profile="development",
        development_principal_id=principal.id,
        development_admin_id=admin.id,
        platform_id=configuration.platform.id,
        development_user_token=SecretStr("u" * 40),
        development_admin_token=SecretStr("a" * 40),
        cursor_signing_key=SecretStr("k" * 40),
    )
    container = Container(
        settings=settings,
        bindings=RuntimeBindings(),
        records=run.store,
        configuration=configuration,
        run_service=run,
    )
    app = create_app(container)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = {"Authorization": "Bearer " + "a" * 40}
        draft = {k: v for k, v in active.items() if k not in ("id", "revision", "state")}
        staged = await client.post(
            "/v1/admin/configuration/drafts",
            headers=headers,
            json={"meta": meta("http-stage").wire(), "payload": {"configuration": draft}},
        )
        assert staged.status_code == 200
        config_id = staged.json()["payload"]["id"]
        path = f"/v1/admin/configuration/drafts/{config_id}"
        unvalidated = await client.post(
            path + "/activate",
            headers=headers,
            json={"meta": meta("invalid-activation", 1).wire(), "payload": {}},
        )
        assert unvalidated.status_code == 409
        validated = await client.post(
            path + "/validate",
            headers=headers,
            json={"meta": meta("http-validate", 1).wire(), "payload": {}},
        )
        assert validated.status_code == 200 and validated.json()["payload"]["valid"]
        activated = await client.post(
            path + "/activate",
            headers=headers,
            json={"meta": meta("http-activate", 2).wire(), "payload": {}},
        )
        assert activated.status_code == 200 and activated.json()["payload"]["state"] == "active"
        secret_value = secrets.token_urlsafe(36)
        receipt = await client.post(
            "/v1/admin/secrets",
            headers=headers,
            json={
                "meta": meta("http-secret").wire(),
                "payload": {"provider_id": "fixture-provider", "secret": secret_value},
            },
        )
        assert receipt.status_code == 200 and secret_value not in receipt.text
        await configuration.credentials.delete(receipt.json()["payload"]["credential_handle"])
        revoked = await client.request(
            "DELETE",
            "/v1/admin/providers/fixture-provider",
            headers=headers,
            json={"meta": meta("http-revoke", 1).wire(), "payload": {}},
        )
        assert revoked.status_code == 200 and revoked.json()["payload"]["state"] == "revoked"
        schema = (await client.get("/openapi.json")).json()
        assert "/v1/agents/invoke" not in schema["paths"]
        assert schema["paths"]["/v1/admin/secrets"]["post"]["security"]
        wire = schema["paths"]["/v1/conversations/{conversation_id}/turns"]["post"]["requestBody"][
            "content"
        ]["application/json"]["schema"]
        assert "conversation_id" not in wire["properties"]["payload"]["properties"]
