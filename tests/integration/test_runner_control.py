"""Real SQL and Ed25519. Channel/root/consent are controlled component sources.

No real pairing, native root selection, IPC, OS signing store or file execution.
"""

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import SecretStr

from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta, seed
from uaw.composition import compose
from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.db.transactions import reference
from uaw.run.budget import BudgetService
from uaw.run.facade import DEFAULT_LIMITS
from uaw.run.leases import ExecutionLeaseService
from uaw.run.permissions import ExecutionPolicyResolver
from uaw.run.runner_authority import RegisteredRunnerAuthority
from uaw.run.runner_commands import REQUESTS, RunnerCommands, copy, pin
from uaw.run.runner_devices import RunnerDevices
from uaw.shared.contracts import Principal, Ref, Scope, TrustedExecutionContext
from uaw.shared.errors import DomainError, reject
from uaw.shared.runner_signatures import VerificationKey, sign, verify
from uaw.shared.schema import ContractViolation, validate_contract
from uaw.shared.settings import Settings
from uaw.shared.stores import StoreMissing
from uaw.tool.invocation.schema import normalize
from uaw.tool.ledger import ToolLedger, action_key
from uaw.tool.registry import ToolRegistry


class Channel:
    def __init__(self, source):
        self.value = source

    async def read(self, channel_ref, *, device_id):
        if channel_ref.wire() != self.value["channel_ref"] or device_id != self.value["device_id"]:
            raise reject("controlled_channel_missing", "Independent source does not match", 403)
        return copy(self.value)


async def original_tool(case):
    """Actual original SQL rows; Tool provider/root/consent stay controlled here."""
    ctx = TrustedExecutionContext.model_validate_json(
        json.dumps({k: v for k, v in case.ctx.wire().items() if k != "budget_reservation_ref"})
    )
    spec = {
        "id": "file.read",
        "version": "1",
        "description": "Controlled read definition",
        "categories": ["file"],
        "required_capabilities": ["file.read"],
        "effect": "read",
        "feature_flag": "file_access",
        "provider_ref": reference("provider", "fixture-provider"),
        "retry_policy_ref": reference("policy", "no-automatic-retry"),
        "input_schema": {
            "type": "object",
            "properties": {
                "workspace_ref": {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string", "const": "workspace"},
                        "id": {"type": "string"},
                        "version": {"type": "string"},
                    },
                    "required": ["kind", "id", "version"],
                    "additionalProperties": False,
                },
                "path": {"type": "string"},
            },
            "required": ["workspace_ref", "path"],
            "additionalProperties": False,
        },
        "output_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    }
    registry = ToolRegistry()
    registry.register(spec, expected_revision=0)
    call = normalize(
        {
            "tool_ref": registry.reference(registry.snapshot()[1][0]),
            "arguments": case.request["parameters"]["parameters"],
            "action_id": "actual-tool-read",
        },
        registry,
    )
    ledger = ToolLedger(case.commands.store)
    await ledger.bind(call, spec, ctx)
    return ctx, call, spec, ledger


async def test_registered_tool_request_keeps_call_pin_and_original_budget_context(case):
    ctx, call, spec, ledger = await original_tool(case)
    ref = await case.commands.register_tool_request(
        call, spec, ctx, meta("tool-original-register"), authenticated_service=case.controller
    )
    key = action_key(ctx, call["action_id"])
    assert ref == pin("tool_call", key, call)
    reservation = await case.budgets.get_reservation(case.ctx.budget_reservation_ref.id, ctx)
    await ledger.save("tool.budget.reserved", ctx.attempt_id, "BudgetReservation", reservation, ctx)
    budget = await case.budgets.get_ledger(ctx)
    intent = {
        "validated_action_ref": reference("tool_call", key),
        "reservation_ref": reference("reservation", reservation["id"], reservation["revision"]),
        "provider_binding_ref": spec["provider_ref"],
    }
    assert await ledger.claim(intent, ctx, budget=budget, reservation=reservation)
    ack = await case.budgets.dispatch(
        ctx.principal, intent["reservation_ref"], meta("tool-dispatched"), ctx
    )
    await ledger.acknowledge(ack, ctx)
    registered = await case.commands.register(
        {**case.registered, "request_ref": ref},
        meta("tool-command-register"),
        authenticated_service=case.controller,
    )
    command = registered["command"]
    assert command["trusted_context"] == ctx.wire()
    assert (
        "budget_reservation_ref" not in command["trusted_context"]
        or command["trusted_context"]["budget_reservation_ref"] is None
    )
    assert command["request_ref"] == ref
    actual = await case.authority().current(command, authenticated_principal=case.actor)
    assert actual["context"] == ctx.wire() and actual["request_ref"] == ref


async def test_tool_runner_registration_rejects_unregistered_call_or_mutated_context(case):
    ctx, call, spec, _ = await original_tool(case)
    changed = copy(call)
    changed["arguments"]["path"] = "different.txt"
    with pytest.raises(DomainError):
        await case.commands.register_tool_request(
            changed, spec, ctx, meta("forged-tool"), authenticated_service=case.controller
        )
    with pytest.raises(DomainError):
        await case.commands.register_tool_request(
            call,
            spec,
            case.ctx,
            meta("changed-original-ctx"),
            authenticated_service=case.controller,
        )
    ref = await case.commands.register_tool_request(
        call, spec, ctx, meta("undispatched-tool"), authenticated_service=case.controller
    )
    with pytest.raises(DomainError) as missing:
        await case.commands.register(
            {**case.registered, "request_ref": ref},
            meta("not-tool-dispatched"),
            authenticated_service=case.controller,
        )
    assert missing.value.failure.code == "runner_original_budget_denied"


class Root:
    def __init__(self, value):
        self.value = value

    async def current(self, device_id, workspace_ref, ctx):
        return copy(self.value)


class Gate:
    def __init__(self):
        self.allowed = True
        self.hook = None

    async def check(self, request, ctx):
        if self.hook:
            hook, self.hook = self.hook, None
            await hook()
        if not self.allowed:
            raise reject("controlled_consent_revoked", "Current consent was withdrawn", 403)
        assert request["context"] == ctx.wire()


class Signer:
    def __init__(self):
        self.private = Ed25519PrivateKey.generate()
        self.revoked = False
        self.role = "control"
        self.hook = None

    async def sign(self, draft, *, device_id):
        return {
            **draft,
            "signature": sign(
                draft, self.private.private_bytes_raw(), device_id, "fixture-control", "command"
            ),
        }

    async def verify(self, command, *, device_id):
        if self.hook:
            hook, self.hook = self.hook, None
            await hook()
        key = VerificationKey(
            "fixture-control",
            device_id,
            self.private.public_key().public_bytes_raw(),
            self.role,
            self.revoked,
        )
        if not verify(command, command["signature"], key, "command"):
            raise reject("controlled_signature_denied", "Actual Ed25519/current key failed", 403)


@dataclass
class Case:
    domain: tuple
    ctx: TrustedExecutionContext
    budgets: BudgetService
    leases: ExecutionLeaseService
    devices: RunnerDevices
    commands: RunnerCommands
    channel: Channel
    root: Root
    gate: Gate
    signer: Signer
    request: dict
    device: dict
    lease: dict
    registered: dict

    @property
    def controller(self):
        return self.devices.controller

    @property
    def actor(self):
        return Principal.model_validate(self.channel.value["actor"])

    def authority(self):
        return RegisteredRunnerAuthority(self.commands)

    async def dispatch(self):
        await self.budgets.dispatch(
            self.ctx.principal, self.ctx.budget_reservation_ref.wire(), meta("dispatch"), self.ctx
        )

    async def register(self, identifier="command-one", request_id="command-register"):
        return await self.commands.register(
            {**self.registered, "command_id": identifier},
            meta(request_id),
            authenticated_service=self.controller,
        )


@pytest.fixture
async def case(domain, principal):
    configuration, run, admin = domain
    active = await seed(configuration, admin)
    # Controlled SQL flag fixture only: admin publication still prohibits enabling
    # product local_files. Insert a NEW version before the Run fixes its snapshot.
    flags = [dict(f, enabled=f["id"] == "local_files") for f in active["feature_flags"]]
    await run.store.put(
        configuration.platform,
        "configurations",
        active["id"],
        "ConfigurationVersion",
        {**active, "revision": 4, "feature_flags": flags},
        expected_revision=3,
        request_id="controlled-flag-version",
    )
    await run.store.put(
        configuration.platform,
        "configuration.pointer",
        "current",
        "Ref",
        reference("configuration", active["id"], 4),
        expected_revision=1,
        request_id="controlled-pointer",
    )
    conv = await run.create_conversation(
        principal,
        {
            "title": "Runner control SQL component",
            "model_choice": {"mode": "explicit", "model_id": "fixture-model"},
            "memory_policy": {
                "revision": 0,
                "read_enabled": False,
                "contribute_enabled": False,
                "scope": {"resource_refs": []},
            },
        },
        meta("conversation"),
    )
    admitted = await run.submit(
        principal,
        {"conversation_id": conv["id"], "text": "读取 workspace 中的文件", "attachment_refs": []},
        meta("submit"),
    )
    await run.advance(principal, admitted["id"], "preparing", meta("prepare", 1))
    binding = (await run.store.get(principal, "run.bindings", admitted["id"])).payload
    workspace = reference("workspace", "controlled-workspace")
    policy = {
        "id": "runner-read-policy",
        "revision": 1,
        "allowed_capabilities": ["file.read", "file.list"],
        "denied_capabilities": [],
        "resource_scope": {
            "conversation_id": conv["id"],
            "task_id": admitted["task_id"],
            "resource_refs": [workspace],
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
    deadline = (datetime.now(UTC) + timedelta(minutes=3)).isoformat()
    ctx = TrustedExecutionContext(
        principal=principal,
        scope=Scope(
            principal_id=principal.id,
            conversation_id=conv["id"],
            task_id=admitted["task_id"],
            capabilities=("file.read", "file.list"),
            resource_refs=(Ref.model_validate(workspace),),
        ),
        conversation_id=conv["id"],
        task_id=admitted["task_id"],
        run_id=admitted["id"],
        operation_id="read-operation",
        trace_id="read-trace",
        attempt_id="read-attempt",
        deadline=deadline,
        capability_policy_ref=Ref.model_validate(reference("policy", policy["id"])),
        model_policy_ref=Ref.model_validate(binding["model_policy_ref"]),
    )
    budgets = BudgetService(run.store)
    estimates = {
        **DEFAULT_LIMITS,
        "input_tokens": 0,
        "output_tokens": 0,
        "model_calls": 0,
        "tool_calls": 1,
        "child_agents": 0,
        "wall_time_ms": 1000,
        "money": "0.100000",
    }
    reservation = await budgets.reserve(
        principal,
        {
            "reservation_id": "read-reservation",
            "parent_run_id": admitted["id"],
            "estimates": estimates,
            "deadline": deadline,
            "expected_ledger_revision": 1,
        },
        meta("reserve"),
        ctx,
    )
    ctx = ctx.model_copy(
        update={
            "budget_reservation_ref": Ref.model_validate(
                reference("reservation", reservation["id"])
            )
        }
    )
    controller = configuration.platform
    actor = Principal(id="runner-fixture", kind="runner", auth_session_id="channel-session")
    channel = Channel(
        {
            "device_id": "device-fixture",
            "owner": principal.wire(),
            "actor": actor.wire(),
            "pairing_ref": reference("check", "controlled-pair"),
            "channel_ref": reference("connection", "controlled-channel"),
            "key_ref": reference("content", "controlled-device-key"),
            "connected": True,
            "expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
        }
    )
    devices = RunnerDevices(run.store, controller, channel)
    device = await devices.bind(
        {
            "device_id": channel.value["device_id"],
            "channel_ref": channel.value["channel_ref"],
            "expected_revision": 0,
        },
        meta("bind"),
        authenticated_service=controller,
    )
    root = Root(
        {
            "owner": principal.wire(),
            "device_id": device["device_id"],
            "workspace_ref": workspace,
            "root_handle": "opaque-controlled-root",
            "binding_revision": 1,
            "allowed_actions": ["file.read", "file.list"],
            "expires_at": channel.value["expires_at"],
        }
    )
    gate, signer = Gate(), Signer()
    leases = ExecutionLeaseService(run.store)
    lease = await leases.acquire(
        {"lease_ttl_ms": 300000, "expected_revision": 0}, meta("lease"), ctx, holder=controller
    )
    commands = RunnerCommands(
        run.store,
        devices,
        configuration,
        ExecutionPolicyResolver(run.store),
        budgets,
        leases,
        roots=root,
        gate=gate,
        signer=signer,
    )
    request = {
        "id": "read-request",
        "parameters": {
            "action": "file.read",
            "parameters": {"workspace_ref": workspace, "path": "README.md"},
        },
    }
    request_ref = await commands.register_request(
        request, meta("register-request"), ctx, authenticated_service=controller
    )
    registered = {
        "command_id": "command-one",
        "request_ref": request_ref,
        "device_ref": {
            **reference("device", device["device_id"], device["revision"]),
            "content_hash": parameter_hash(device),
        },
        "lease_ref": reference("lease", lease["id"], lease["revision"]),
        "fencing_token": lease["fencing_token"],
        "expires_at": (datetime.fromisoformat(deadline) - timedelta(seconds=1)).isoformat(),
    }
    return Case(
        domain,
        ctx,
        budgets,
        leases,
        devices,
        commands,
        channel,
        root,
        gate,
        signer,
        request,
        device,
        lease,
        registered,
    )


async def test_real_budget_intent_and_signed_registration_survive_restart(case):
    state = await case.budgets.execution_state(case.ctx.budget_reservation_ref.id, case.ctx)
    assert state["reservation"]["status"] == "reserved"
    assert not state["attempt"]["dispatched"]
    with pytest.raises(DomainError, match="Actual attempt"):
        await case.register()
    await case.dispatch()
    record = await case.register()
    assert record == await case.register()  # Response loss recovers identical signed bytes.
    state = await case.budgets.execution_state(case.ctx.budget_reservation_ref.id, case.ctx)
    assert state["attempt"]["dispatched"] and state["ledger"]["billing_pending"]
    new = RunnerCommands(
        case.commands.store,
        case.devices,
        case.commands.configuration,
        case.commands.permissions,
        case.budgets,
        case.leases,
        roots=case.root,
        gate=case.gate,
        signer=case.signer,
    )
    snapshot = await RegisteredRunnerAuthority(new).current(
        record["command"], authenticated_principal=case.actor
    )
    validate_contract("RunnerAuthoritySnapshot", snapshot)
    assert snapshot["context"] == case.ctx.wire()
    assert snapshot["root_handle"] == "opaque-controlled-root"
    assert snapshot["request_parameters"] == case.request["parameters"]
    assert snapshot["feature_enabled"] and not snapshot["cancelled"]
    assert (
        await new.read(
            Ref.model_validate(pin("content", "command-one", record["command"])),
            authenticated_principal=case.ctx.principal,
        )
    ) == record


@pytest.mark.parametrize("change", ["user", "session", "service-id"])
async def test_internal_controller_is_not_a_body_claim(case, change):
    actor = case.controller.model_copy(
        update={
            "kind": "user" if change == "user" else "service",
            "auth_session_id": "forged" if change == "session" else case.controller.auth_session_id,
            "id": "other" if change == "service-id" else case.controller.id,
        }
    )
    with pytest.raises(DomainError) as denied:
        await case.commands.register_request(
            case.request, meta("forged"), case.ctx, authenticated_service=actor
        )
    assert denied.value.failure.code == "runner_service_denied"


@pytest.mark.parametrize("change", ["owner", "actor", "session", "disconnected", "source"])
async def test_device_current_identity_and_channel_are_independent(case, change):
    actor = case.actor
    if change in ("owner", "actor", "session"):
        actor = actor.model_copy(
            update={
                "id": "other" if change != "session" else actor.id,
                "kind": "user" if change == "owner" else "runner",
                "auth_session_id": "other",
            }
        )
    elif change == "disconnected":
        case.channel.value["connected"] = False
    else:
        case.channel.value["key_ref"] = reference("content", "different-key")
    with pytest.raises(DomainError):
        await case.devices.current(case.device["device_id"], authenticated_principal=actor)


async def test_device_revoke_old_replay_and_terminal_expiry_do_not_revive(case):
    await case.devices.revoke(
        case.device["device_id"], 1, meta("device-revoke"), authenticated_service=case.controller
    )
    with pytest.raises(DomainError):
        await case.devices.bind(
            {
                "device_id": case.device["device_id"],
                "channel_ref": case.channel.value["channel_ref"],
                "expected_revision": 0,
            },
            meta("bind"),
            authenticated_service=case.controller,
        )
    with pytest.raises(DomainError) as stale:
        await case.devices.bind(
            {
                "device_id": case.device["device_id"],
                "channel_ref": case.channel.value["channel_ref"],
                "expected_revision": 2,
            },
            meta("old-pair"),
            authenticated_service=case.controller,
        )
    assert stale.value.failure.code == "runner_pairing_stale"
    case.channel.value["pairing_ref"] = reference("check", "fresh-pair")
    case.channel.value["channel_ref"] = reference("connection", "fresh-channel")
    rebound = await case.devices.bind(
        {
            "device_id": case.device["device_id"],
            "channel_ref": case.channel.value["channel_ref"],
            "expected_revision": 2,
        },
        meta("new-pair"),
        authenticated_service=case.controller,
    )
    assert rebound["revision"] == 3
    before = datetime.now(UTC)
    case.devices.clock = lambda: before + timedelta(hours=1)
    with pytest.raises(DomainError):
        await case.devices.current(case.device["device_id"], authenticated_principal=case.actor)
    case.devices.clock = lambda: before
    current = await case.devices._load(case.device["device_id"])
    assert current["state"] == "expired" and current["revision"] == 4
    with pytest.raises(DomainError):
        await case.devices.current(case.device["device_id"], authenticated_principal=case.actor)


async def test_device_cas_concurrent_update_and_owner_transfer(case):
    request = {
        "device_id": case.device["device_id"],
        "channel_ref": case.channel.value["channel_ref"],
        "expected_revision": 1,
    }
    results = await asyncio.gather(
        *[
            case.devices.bind(request, meta(f"cas-{i}"), authenticated_service=case.controller)
            for i in range(2)
        ],
        return_exceptions=True,
    )
    assert sum(isinstance(r, dict) for r in results) == 1
    assert sum(isinstance(r, DomainError) for r in results) == 1
    case.channel.value["owner"]["id"] = "foreign"
    with pytest.raises(DomainError) as denied:
        await case.devices.bind(
            {**request, "expected_revision": 2},
            meta("owner-change"),
            authenticated_service=case.controller,
        )
    assert denied.value.failure.code == "runner_owner_transfer_denied"


async def test_request_body_is_immutable_and_model_context_is_not_accepted(case):
    changed = copy(case.request)
    changed["parameters"]["parameters"]["path"] = "other.md"
    with pytest.raises(DomainError):
        await case.commands.register_request(
            changed, meta("register-request"), case.ctx, authenticated_service=case.controller
        )
    with pytest.raises(ContractViolation):
        await case.commands.register_request(
            {**case.request, "context": case.ctx.wire()},
            meta("body-context"),
            case.ctx,
            authenticated_service=case.controller,
        )
    assert (await case.commands.store.get(case.controller, REQUESTS, "read-request")).revision == 1


async def test_same_attempt_cannot_get_second_command_and_wrong_budget_attempt_is_denied(case):
    await case.dispatch()
    await case.register()
    with pytest.raises(DomainError):
        await case.register("command-two", "second-register")
    with pytest.raises(StoreMissing):
        await case.commands.record("command-two")
    with pytest.raises(DomainError) as denied:
        await case.budgets.execution_state(
            case.ctx.budget_reservation_ref.id,
            case.ctx.model_copy(update={"attempt_id": "foreign-attempt"}),
        )
    assert denied.value.failure.code == "attempt_scope_denied"


async def test_concurrent_command_ids_use_one_original_attempt(case):
    await case.dispatch()
    results = await asyncio.gather(
        case.register("command-a", "register-a"),
        case.register("command-b", "register-b"),
        return_exceptions=True,
    )
    assert sum(isinstance(r, dict) for r in results) == 1
    assert sum(isinstance(r, DomainError) for r in results) == 1


@pytest.mark.parametrize(
    "change",
    ["request-hash", "device-version", "lease-holder", "root-write", "workspace", "channel-body"],
)
async def test_registration_requires_pinned_sources_and_read_only_root(case, change):
    await case.dispatch()
    if change == "request-hash":
        case.registered["request_ref"].pop("content_hash")
    elif change == "device-version":
        case.registered["device_ref"]["version"] = "2"
    elif change == "lease-holder":
        case.commands.devices.controller = case.controller.model_copy(
            update={"auth_session_id": "other-service-session"}
        )
    elif change == "root-write":
        case.root.value["allowed_actions"].append("file.write")
    elif change == "workspace":
        case.root.value["workspace_ref"] = reference("workspace", "outside")
    else:
        case.channel.value["expires_at"] = (datetime.now(UTC) + timedelta(minutes=6)).isoformat()
    with pytest.raises(DomainError):
        await case.register()
    with pytest.raises(StoreMissing):
        await case.commands.record("command-one")


async def test_file_list_uses_unique_actual_scope_workspace(case):
    listed = {
        "id": "list-request",
        "parameters": {
            "action": "file.list",
            "parameters": {"workspace_id": case.root.value["workspace_ref"]["id"], "path": "src"},
        },
    }
    case.registered["request_ref"] = await case.commands.register_request(
        listed, meta("register-list"), case.ctx, authenticated_service=case.controller
    )
    await case.dispatch()
    command = (await case.register())["command"]
    result = await case.authority().current(command, authenticated_principal=case.actor)
    assert result["required_scope_capability"] == "file.list"
    assert result["workspace_ref"] == case.root.value["workspace_ref"]


async def test_signer_cannot_change_business_body_and_expiry_after_signing_is_checked(case):
    await case.dispatch()
    original = case.signer.sign

    async def changed(draft, *, device_id):
        signed = await original(draft, device_id=device_id)
        signed["parameters"]["parameters"]["path"] = "changed.md"
        return signed

    case.signer.sign = changed
    with pytest.raises(DomainError) as denied:
        await case.register()
    assert denied.value.failure.code == "runner_signer_binding_denied"

    async def expired(draft, *, device_id):
        signed = await original(draft, device_id=device_id)
        now = datetime.fromisoformat(case.registered["expires_at"]) + timedelta(seconds=1)
        case.devices.clock = lambda: now
        return signed

    case.signer.sign = expired
    with pytest.raises((DomainError, TimeoutError)):
        await case.register()
    with pytest.raises(StoreMissing):
        await case.commands.record("command-one")


@pytest.mark.parametrize("change", ["command_id", "context", "parameter", "fence", "signature"])
async def test_received_command_cannot_replace_registered_authority(case, change):
    await case.dispatch()
    command = copy((await case.register())["command"])
    if change == "command_id":
        command["command_id"] = "not-registered"
    elif change == "context":
        command["trusted_context"]["principal"]["auth_session_id"] = "forged-session"
    elif change == "parameter":
        command["parameters"]["parameters"]["path"] = "foreign.md"
    elif change == "fence":
        command["fencing_token"] += 1
    else:
        command["signature"] += "A"
    with pytest.raises(DomainError):
        await case.authority().current(command, authenticated_principal=case.actor)


@pytest.mark.parametrize(
    "change",
    ["policy", "model", "root", "consent", "key", "key-role", "lease", "cancel", "flag", "command"],
)
async def test_current_revocation_and_versions_stop_new_admission(case, change):
    await case.dispatch()
    record = await case.register()
    store = case.commands.store
    if change == "policy":
        policy = await store.get(case.ctx.principal, "execution.policies", "runner-read-policy")
        await store.put(
            case.ctx.principal,
            policy.namespace,
            policy.resource_id,
            policy.schema_name,
            {**policy.payload, "revision": 2, "denied_capabilities": ["file.read"]},
            expected_revision=1,
            request_id="withdraw-policy",
        )
    elif change == "model":
        # Actual owner record gets another fixed policy; current cmd ctx retains its original pin.
        binding = await store.get(case.ctx.principal, "run.bindings", case.ctx.run_id)
        await store.put(
            case.ctx.principal,
            binding.namespace,
            binding.resource_id,
            binding.schema_name,
            {**binding.payload, "model_policy_ref": reference("policy", "different-model")},
            expected_revision=binding.revision,
            request_id="changed-model-binding",
        )
    elif change == "root":
        case.root.value["binding_revision"] += 1
    elif change == "consent":
        case.gate.allowed = False
    elif change in ("key", "key-role"):
        case.signer.revoked = change == "key"
        case.signer.role = "device" if change == "key-role" else "control"
    elif change == "lease":
        await case.leases.release(
            {
                "lease_ref": case.registered["lease_ref"],
                "fencing_token": case.lease["fencing_token"],
            },
            meta("release-lease"),
            case.ctx,
            holder=case.controller,
        )
    elif change == "cancel":
        await case.domain[1].control(
            case.ctx.principal,
            {
                "run_id": case.ctx.run_id,
                "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop"},
            },
            meta("cancel", 2),
        )
    elif change == "flag":
        configuration, _, admin = case.domain
        current = await configuration.current()
        draft = {k: v for k, v in current.items() if k not in {"id", "revision", "state"}}
        draft["feature_flags"] = [dict(f, enabled=False) for f in draft["feature_flags"]]
        staged = await configuration.stage(admin, {"configuration": draft}, meta("flags-off"))
        await configuration.validate(admin, staged["id"], meta("flags-off-validate", 1))
        await configuration.activate(admin, staged["id"], meta("flags-off-activate", 2))
    else:
        await case.commands.revoke(
            "command-one", 1, meta("revoke-command"), authenticated_service=case.controller
        )
    with pytest.raises(DomainError):
        await case.authority().current(record["command"], authenticated_principal=case.actor)


@pytest.mark.parametrize("missing", ["channels", "roots", "gate", "signer"])
async def test_missing_independent_sources_never_grant(case, missing):
    await case.dispatch()
    if missing == "channels":
        case.devices.channels = None
    else:
        setattr(case.commands, missing, None)
    with pytest.raises(DomainError) as unavailable:
        await case.register()
    assert unavailable.value.failure.code == "capability_unavailable"
    with pytest.raises(StoreMissing):
        await case.commands.record("command-one")


async def test_recovery_after_cancellation_and_command_revocation_keeps_signature(case):
    await case.dispatch()
    record = await case.register()
    command_ref = Ref.model_validate(pin("content", "command-one", record["command"]))
    await case.commands.revoke(
        "command-one", 1, meta("revoke-command"), authenticated_service=case.controller
    )
    await case.domain[1].control(
        case.ctx.principal,
        {
            "run_id": case.ctx.run_id,
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop"},
        },
        meta("cancel", 2),
    )
    read = await case.commands.read(command_ref, authenticated_principal=case.actor)
    assert read["command"] == record["command"] and read["state"] == "revoked"
    assert (await case.budgets.execution_state(case.ctx.budget_reservation_ref.id, case.ctx))[
        "ledger"
    ]["cancel_requested"]
    case.signer.revoked = True
    with pytest.raises(DomainError):
        await case.commands.read(command_ref, authenticated_principal=case.actor)


@pytest.mark.parametrize("when", ["gate", "signature", "deadline"])
async def test_changes_during_await_are_observed(case, when):
    await case.dispatch()
    record = await case.register()

    async def revoke():
        await case.devices.revoke(
            case.device["device_id"],
            1,
            meta("mid-await-revoke"),
            authenticated_service=case.controller,
        )

    if when == "gate":
        case.gate.hook = revoke
    elif when == "signature":
        case.signer.hook = revoke
    else:

        async def expire():
            now = datetime.fromisoformat(case.registered["expires_at"]) + timedelta(seconds=1)
            case.devices.clock = lambda: now

        case.signer.hook = expire
    with pytest.raises(DomainError):
        await case.authority().current(record["command"], authenticated_principal=case.actor)


async def test_scoped_flag_does_not_enable_other_resources_and_admin_stays_disabled(case):
    configuration = case.commands.configuration
    current = await configuration.current()
    flags = [
        dict(f, scope={"resource_refs": [case.root.value["workspace_ref"]]})
        if f["id"] == "local_files"
        else f
        for f in current["feature_flags"]
    ]
    await configuration.store.put(
        case.controller,
        "configurations",
        current["id"],
        "ConfigurationVersion",
        {**current, "revision": 5, "feature_flags": flags},
        expected_revision=4,
        request_id="controlled-scoped-flags",
    )
    await configuration.store.put(
        case.controller,
        "configuration.pointer",
        "current",
        "Ref",
        reference("configuration", current["id"], 5),
        expected_revision=2,
        request_id="controlled-scoped-pointer",
    )
    fixed = reference("configuration", current["id"], 4)
    await configuration.require_capability(
        "local_files", fixed, case.ctx.scope.wire(), implemented=True, boundary="call"
    )
    for resources in ([], [reference("workspace", "outside")]):
        with pytest.raises(DomainError) as denied:
            await configuration.require_capability(
                "local_files",
                fixed,
                {**case.ctx.scope.wire(), "resource_refs": resources},
                implemented=True,
                boundary="call",
            )
        assert denied.value.failure.code == "feature_disabled"
    staged = await configuration.stage(
        case.domain[2],
        {
            "configuration": {
                k: v for k, v in current.items() if k not in {"id", "revision", "state"}
            }
        },
        meta("admin-true"),
    )
    with pytest.raises(DomainError):
        await configuration.validate(case.domain[2], staged["id"], meta("admin-true-validate", 1))


async def test_composition_registers_services_without_execution_sources(case):
    container = compose(
        Settings(
            profile="development",
            development_principal_id="fixture-user",
            database_url=SecretStr(os.environ["UAW_TEST_DATABASE_URL"]),
        )
    )
    try:
        assert container.runner_devices and container.runner_commands and container.runner_authority
        assert container.runner_devices.channels is None
        assert container.runner_commands.roots is None and container.runner_commands.signer is None
        assert container.bindings.workspace is None and container.bindings.tool is None
    finally:
        await container.close()
