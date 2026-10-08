"""Actual SQL/config sources; provider connection metadata is a controlled fixture.

No HTTP role installation, actual model call, Tool execution, native consent or
trusted IPC is claimed. The exact bounded text spec exercises resource authority.
"""

import asyncio
from contextlib import contextmanager

import pytest

from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.test_runner_control import case as case
from tests.integration.tool.conftest import tool_case as tool_case
from uaw.composition import Container, RuntimeBindings, assemble_runner_control, compose
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import reference
from uaw.run.execution_sources import RunExecutionSources
from uaw.run.permissions import ExecutionPolicyResolver
from uaw.run.runner_mapping import RegisteredRunnerPrincipalMapping
from uaw.run.tool_sources import (
    BINDINGS,
    PureTextResourceReader,
    RunToolAccessSources,
    RunToolRecoveryAccess,
    binding_key,
)
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, DomainError
from uaw.shared.settings import ConfigurationError, Settings
from uaw.shared.stores import StoreConflict
from uaw.tool.authority import ToolApprovalAuthority
from uaw.tool.discovery import require_entry
from uaw.tool.invocation.schema import normalize
from uaw.tool.registry import AdapterBinding


@contextmanager
def denied(code):
    with pytest.raises(DomainError) as caught:
        yield
    assert caught.value.failure.code == code


def profile(categories=None, version="1"):
    return {
        "id": "analysis",
        "version": version,
        "description": "Internal bounded text analysis role",
        "instructions_ref": reference("rule", "analysis-instructions"),
        "tool_categories": ["analysis"] if categories is None else categories,
        "skill_refs": [],
        "output_contract": {
            "goal": "Inspect submitted text",
            "version": "1",
            "requirements": [],
            "outputs": [],
        },
        # Deliberately not used to replace the user's fixed model.
        "auto_model_candidates": ["never-select-this-model"],
    }


@pytest.fixture
async def sources(tool_case):
    config, run, _admin = tool_case.domain
    current = RunExecutionSources(run.store, config, ExecutionPolicyResolver(run.store))
    access = RunToolAccessSources(run.store, config, current, environment="sql-component-test")
    role = await access.register_role(
        profile(), meta("install-role", 0), authenticated_service=config.platform
    )
    pin = await access.bind(
        tool_case.ctx, role, meta("bind-role", 0), authenticated_service=config.platform
    )
    spec = {
        **tool_case.spec,
        "id": "text.inspect",
        "description": "Bounded pure text inspection; no external access",
        "categories": ["analysis"],
        "effect": "read",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string", "maxLength": 1024}},
            "required": ["text"],
            "additionalProperties": False,
        },
    }
    tool_case.registry.register(
        spec,
        expected_revision=tool_case.registry.revision,
        binding=AdapterBinding(
            Ref.model_validate(spec["provider_ref"]),
            frozenset({"sql-component-test"}),
            implemented=True,
        ),
    )
    entry = tool_case.registry.snapshot()[1][-1]
    tool_ref = Ref.model_validate(tool_case.registry.reference(entry))
    call = normalize(
        {
            "tool_ref": tool_ref.wire(),
            "arguments": {"text": "保留  原文\r\n"},
            "action_id": "pure-text-action",
        },
        tool_case.registry,
    )
    return (
        access,
        role,
        pin,
        PureTextResourceReader(tool_case.registry, access, tool_ref),
        call,
        spec,
    )


async def test_real_role_binding_survives_new_instances_and_uses_fixed_user_model(
    sources, tool_case
):
    access, _role, _pin, reader, call, spec = sources
    snapshot = await access.snapshot(tool_case.ctx)
    assert snapshot.role_categories == frozenset({"analysis"})
    assert snapshot.allowed_capabilities == frozenset({"tool.invoke"})
    assert snapshot.enabled_flags == frozenset()
    assert snapshot.active_provider_refs == (Ref.model_validate(spec["provider_ref"]),)
    assert await reader.resolve(call, spec, tool_case.ctx) == ()
    config, run, _ = tool_case.domain
    store = PostgresRecordStore(run.store.database)
    restarted = RunToolAccessSources(
        store,
        config,
        RunExecutionSources(store, config, ExecutionPolicyResolver(store)),
        environment="sql-component-test",
    )
    assert await restarted.snapshot(tool_case.ctx) == snapshot


async def test_actual_approval_authority_consumes_registered_role_and_pure_resources(
    sources, tool_case
):
    access, _, _, reader, call, spec = sources
    ctx = tool_case.ctx.model_copy(update={"attempt_id": "pure-text-attempt"})
    await tool_case.ledger.bind(call, spec, ctx)
    authority = ToolApprovalAuthority(
        tool_case.ledger,
        tool_case.registry,
        tool_case.domain[0],
        access,
        reader,
        policies=ExecutionPolicyResolver(tool_case.ledger.store),
    )
    request = await authority.current(call["action_id"], ctx)
    assert request["resource_refs"] == []
    assert request["effect"] == "read"
    await authority.check(request, ctx)


@pytest.mark.parametrize("actor_change", [{"kind": "admin"}, {"auth_session_id": "other-session"}])
async def test_same_id_different_kind_or_session_cannot_consume_binding(
    sources, tool_case, actor_change
):
    access = sources[0]
    ctx = tool_case.ctx.model_copy(
        update={"principal": tool_case.ctx.principal.model_copy(update=actor_change)}
    )
    with denied("tool_binding_denied"):
        await access.snapshot(ctx)


@pytest.mark.parametrize("change", ["model", "policy", "scope", "agent"])
async def test_claimed_policy_scope_model_or_agent_cannot_replace_binding(
    sources, tool_case, change
):
    access = sources[0]
    ctx = tool_case.ctx
    updates = {
        "model": {"model_policy_ref": Ref.model_validate(reference("policy", "replacement"))},
        "policy": {"capability_policy_ref": Ref.model_validate(reference("policy", "replacement"))},
        "scope": {"scope": ctx.scope.model_copy(update={"capabilities": ("tool.invoke", "exec")})},
        "agent": {"agent_id": "unbound-child"},
    }
    with pytest.raises(DomainError):
        await access.snapshot(ctx.model_copy(update=updates[change]))


async def test_controller_session_required_for_registration_and_revocation(sources, tool_case):
    access, role, _, *_ = sources
    controller = tool_case.domain[0].platform.model_copy(update={"auth_session_id": "fake"})
    with denied("tool_service_denied"):
        await access.register_role(
            profile(version="2"), meta("bad-install", 1), authenticated_service=controller
        )
    with denied("tool_service_denied"):
        await access.bind(
            tool_case.ctx, role, meta("bad-bind", 1), authenticated_service=controller
        )
    with denied("tool_service_denied"):
        await access.revoke(tool_case.ctx, meta("bad-revoke", 1), authenticated_service=controller)
    assert (await access.snapshot(tool_case.ctx)).role_categories == frozenset({"analysis"})


async def test_role_revision_invalidates_existing_access(sources, tool_case):
    access = sources[0]
    await access.register_role(
        profile(categories=[], version="2"),
        meta("revise-role", 1),
        authenticated_service=tool_case.domain[0].platform,
    )
    with denied("tool_role_stale"):
        await access.snapshot(tool_case.ctx)


async def test_missing_role_binding_never_grants_default_categories(sources, tool_case):
    ctx = tool_case.ctx.model_copy(update={"agent_id": "new-child"})
    with pytest.raises(CapabilityUnavailable, match="tool.registered_role_binding"):
        await sources[0].snapshot(ctx)


async def test_role_binding_revocation_and_lost_registration_reply(sources, tool_case):
    access, role, *_ = sources
    controller = tool_case.domain[0].platform
    await access.revoke(tool_case.ctx, meta("revoke", 1), authenticated_service=controller)
    with denied("tool_binding_revoked"):
        await access.snapshot(tool_case.ctx)
    with denied("tool_binding_revoked"):
        await access.bind(
            tool_case.ctx, role, meta("bind-role", 0), authenticated_service=controller
        )


async def test_run_cancellation_blocks_access_but_cleanup_remains_available(sources, tool_case):
    access = sources[0]
    _, run, _ = tool_case.domain
    await run.control(
        tool_case.ctx.principal,
        {
            "run_id": tool_case.ctx.run_id,
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "user cancel"},
        },
        meta("cancel", 2),
    )
    with denied("execution_cancelled"):
        await access.snapshot(tool_case.ctx)
    revoked = await access.revoke(
        tool_case.ctx, meta("cleanup", 1), authenticated_service=tool_case.domain[0].platform
    )
    assert revoked.version == "2"


async def test_current_provider_revocation_cannot_be_hidden_by_fixed_configuration(
    sources, tool_case
):
    config, _, admin = tool_case.domain
    await config.revoke_provider(admin, "fixture-provider", meta("revoke-provider", 2))
    with denied("provider_revoked"):
        await sources[0].snapshot(tool_case.ctx)


async def test_binding_cas_has_one_winner_for_a_new_agent(sources, tool_case):
    access, role, *_ = sources
    ctx = tool_case.ctx.model_copy(update={"agent_id": "new-child"})
    controller = tool_case.domain[0].platform
    results = await asyncio.gather(
        *[
            access.bind(ctx, role, meta(f"competing-{n}", 0), authenticated_service=controller)
            for n in range(2)
        ],
        return_exceptions=True,
    )
    assert sum(isinstance(r, Ref) for r in results) == 1
    assert sum(isinstance(r, StoreConflict) for r in results) == 1
    assert (await access.snapshot(ctx)).role_categories == frozenset({"analysis"})


async def test_binding_owner_cannot_be_transferred_on_same_run(sources, tool_case):
    access, role, *_ = sources
    # The storage owner ID is unchanged; complete session must still match.
    ctx = tool_case.ctx.model_copy(
        update={
            "principal": tool_case.ctx.principal.model_copy(update={"auth_session_id": "another"})
        }
    )
    with denied("tool_owner_transfer_denied"):
        await access.bind(
            ctx, role, meta("transfer", 1), authenticated_service=tool_case.domain[0].platform
        )


async def test_current_model_policy_change_invalidates_input_and_tool_authority(sources, tool_case):
    _, run, _ = tool_case.domain
    pin = tool_case.ctx.model_policy_ref
    row = await run.store.get(tool_case.ctx.principal, "model.policies", pin.id)
    await run.store.put(
        tool_case.ctx.principal,
        "model.policies",
        pin.id,
        "ResolvedModelPolicy",
        {**row.payload, "revision": 2},
        expected_revision=1,
        request_id="controlled-model-revision",
    )
    with denied("run_model_source_invalid"):
        await sources[0].snapshot(tool_case.ctx)


@pytest.mark.parametrize("mutation", ["effect", "unbounded", "path"])
async def test_pure_resource_reader_cannot_authorize_arbitrary_actions(
    sources, tool_case, mutation
):
    access, _, _, _reader, call, spec = sources
    spec = {**spec, "version": "v2"}
    if mutation == "effect":
        spec["effect"] = "external_write"
    elif mutation == "unbounded":
        spec["input_schema"] = {**spec["input_schema"], "properties": {"text": {"type": "string"}}}
    else:
        spec["input_schema"] = {
            "type": "object",
            "properties": {"path": {"type": "string", "maxLength": 256}},
            "required": ["path"],
            "additionalProperties": False,
        }
    registry = tool_case.registry
    registry.register(
        spec,
        expected_revision=registry.revision,
        binding=AdapterBinding(
            Ref.model_validate(spec["provider_ref"]),
            frozenset({"sql-component-test"}),
            implemented=True,
        ),
    )
    pin = Ref.model_validate(registry.reference(registry.snapshot()[1][-1]))
    request = normalize(
        {
            "tool_ref": pin.wire(),
            "arguments": {"path": "secret"} if mutation == "path" else {"text": "hi"},
            "action_id": "other",
        },
        registry,
    )
    reader = PureTextResourceReader(registry, access, pin)
    with pytest.raises(CapabilityUnavailable):
        await reader.resolve(request, spec, tool_case.ctx)


async def test_unsupported_categories_remain_denied_after_trusted_binding(sources, tool_case):
    snapshot = await sources[0].snapshot(tool_case.ctx)
    with denied("permission_denied"):
        require_entry(tool_case.registry.get(tool_case.call["tool_ref"]), snapshot)


async def test_real_binding_record_contains_full_principal_and_cas_revision(sources, tool_case):
    row = await sources[0].store.get(sources[0].controller, BINDINGS, binding_key(tool_case.ctx))
    assert row.schema_name == "RunToolAccessBinding"
    assert row.payload["principal"] == tool_case.ctx.principal.wire()
    assert row.payload["revision"] == row.revision == 1


async def test_recovery_after_cancel_never_grants_new_execution(sources, tool_case):
    access, _, _, reader, call, spec = sources
    ctx = tool_case.ctx.model_copy(update={"attempt_id": "recovery-text-attempt"})
    await tool_case.ledger.bind(call, spec, ctx)
    provider = Principal(id="internal-text", kind="service", auth_session_id="text-service-session")
    recovery = RunToolRecoveryAccess(
        reader,
        tool_case.ledger,
        provider_ref=Ref.model_validate(spec["provider_ref"]),
        provider=provider,
    )
    await recovery.check(call, spec, ctx, provider=provider)
    _, run, _ = tool_case.domain
    await run.control(
        ctx.principal,
        {
            "run_id": ctx.run_id,
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "cancel new actions"},
        },
        meta("cancel-recovery", 2),
    )
    await recovery.check(call, spec, ctx, provider=provider)
    with denied("execution_cancelled"):
        await access.snapshot(ctx)
    await access.revoke(
        ctx, meta("revoke-data", 1), authenticated_service=tool_case.domain[0].platform
    )
    with denied("tool_binding_revoked"):
        await recovery.check(call, spec, ctx, provider=provider)


async def test_recovery_checks_registered_action_and_current_provider_identity(sources, tool_case):
    _access, _, _, reader, call, spec = sources
    ctx = tool_case.ctx.model_copy(update={"attempt_id": "recovery-text-attempt"})
    await tool_case.ledger.bind(call, spec, ctx)
    provider = Principal(
        id="internal-text", kind="service", auth_session_id="actual-service-session"
    )
    recovery = RunToolRecoveryAccess(
        reader,
        tool_case.ledger,
        provider_ref=Ref.model_validate(spec["provider_ref"]),
        provider=provider,
    )
    with denied("tool_recovery_provider_denied"):
        await recovery.check(
            call, spec, ctx, provider=provider.model_copy(update={"auth_session_id": "forged"})
        )
    forged = normalize(
        {
            "tool_ref": call["tool_ref"],
            "arguments": {"text": "changed"},
            "action_id": call["action_id"],
        },
        tool_case.registry,
    )
    with denied("tool_recovery_action_denied"):
        await recovery.check(forged, spec, ctx, provider=provider)
    config, _, admin = tool_case.domain
    await config.revoke_provider(admin, "fixture-provider", meta("revoke-recovery-provider", 2))
    with denied("provider_revoked"):
        await recovery.check(call, spec, ctx, provider=provider)


def test_default_assembly_does_not_publish_unbound_tool_or_workspace():
    container = compose(
        Settings(profile="development", development_principal_id="development-user")
    )
    assert container.run_sources is None and container.tool_access is None
    assert not container.bindings.availability()["tool"]
    assert not container.bindings.availability()["workspace"]
    with pytest.raises(ConfigurationError):
        assemble_runner_control(
            container, channels=None, root_factory=lambda _: None, gate=None, signer=None
        )


async def test_missing_registered_mapping_is_unavailable():
    with pytest.raises(CapabilityUnavailable):
        await RegisteredRunnerPrincipalMapping(None).owner(
            authenticated_principal=Principal(
                id="runner", kind="runner", auth_session_id="session"
            ),
            device_id="device",
        )


async def test_runner_assembly_supplies_actual_mapping_to_root_factory(case):
    runner_case = case
    config, run, _ = runner_case.domain
    container = Container(
        settings=Settings(profile="development", development_principal_id="assembly-user"),
        bindings=RuntimeBindings(),
        records=run.store,
        configuration=config,
        execution_permissions=ExecutionPolicyResolver(run.store),
        budgets=runner_case.budgets,
        execution_leases=runner_case.leases,
    )
    seen = []

    def roots(mapping):
        seen.append(mapping)
        return runner_case.root

    assembly = assemble_runner_control(
        container,
        channels=runner_case.channel,
        root_factory=roots,
        gate=runner_case.gate,
        signer=runner_case.signer,
    )
    assert seen == [assembly.principals]
    owner = await assembly.principals.owner(
        authenticated_principal=runner_case.actor, device_id=runner_case.device["device_id"]
    )
    assert owner == runner_case.ctx.principal
    assert assembly.commands.budgets is runner_case.budgets
    assert assembly.commands.leases is runner_case.leases
    actor = runner_case.actor.model_copy(update={"auth_session_id": "forged-channel"})
    with denied("runner_actor_denied"):
        await assembly.principals.owner(
            authenticated_principal=actor, device_id=runner_case.device["device_id"]
        )
    await runner_case.devices.revoke(
        runner_case.device["device_id"],
        1,
        meta("revoke-device"),
        authenticated_service=config.platform,
    )
    with denied("runner_device_inactive"):
        await assembly.principals.owner(
            authenticated_principal=runner_case.actor, device_id=runner_case.device["device_id"]
        )
