"""Isolated SQL fixtures. Connected provider metadata and Reader are controlled.

No actual LLM, product adapter, Runner, IPC or external consent is represented.
"""

from dataclasses import dataclass

import pytest

from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta, seed
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import reference
from uaw.run.approval import ApprovalService
from uaw.run.budget import BudgetService
from uaw.shared.contracts import Ref, Scope, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.tool.approval import ToolApprovalAdapter
from uaw.tool.authority import ToolApprovalAuthority
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.invocation.schema import normalize
from uaw.tool.ledger import ToolLedger
from uaw.tool.ports import ToolAccess
from uaw.tool.registry import AdapterBinding, ToolRegistry


class ControlledSQLReader:
    def __init__(self, store, source):
        self.store, self.source = store, source

    async def resolve(self, call, spec, ctx):
        row = await self.store.get(ctx.principal, "inputs", self.source["id"])
        if (
            str(row.revision) != self.source["version"]
            or row.payload["conversation_id"] != ctx.conversation_id
        ):
            raise reject("resource_stale", "Controlled input changed", 412)
        return (Ref.model_validate(self.source),)


class ControlledRoleEnvironment:
    # Role/environment is a test substitution; authority independently checks real
    # persisted Run, policy, fixed/current config, flags and provider.
    async def snapshot(self, ctx):
        return ToolAccess(
            ctx.capability_policy_ref,
            ctx.scope,
            frozenset({"fixture"}),
            frozenset(ctx.scope.capabilities),
            frozenset(),
            frozenset(),
            "sql-component-test",
            (Ref(kind="provider", id="fixture-provider", version="2"),),
        )


@dataclass
class ToolCase:
    ledger: ToolLedger
    registry: ToolRegistry
    authority: ToolApprovalAuthority
    approvals: ToolApprovalAdapter
    budget: ToolBudgetAdapter
    service: ApprovalService
    ctx: TrustedExecutionContext
    call: dict
    spec: dict
    domain: tuple
    reader: ControlledSQLReader


@pytest.fixture
async def tool_case(domain, principal):
    configuration, run, admin = domain
    active = await seed(configuration, admin)
    # Deliberate SQL fixture metadata, not an actual provider probe or product binding.
    row = await run.store.get(configuration.platform, "providers", "fixture-provider")
    await run.store.put(
        configuration.platform,
        "providers",
        "fixture-provider",
        "ProviderBinding",
        {**row.payload, "revision": 2, "state": "active"},
        expected_revision=1,
        request_id="fixture-connected-metadata",
    )
    model = (await run.store.get(configuration.platform, "models", "fixture-model")).payload
    await configuration.register(
        admin,
        "model",
        {
            "entry": {
                k: v
                for k, v in {
                    **model,
                    "provider_ref": reference("provider", "fixture-provider", 2),
                }.items()
                if k not in {"revision", "status"}
            }
        },
        meta("fixture-model-2", 1),
    )
    config = {k: v for k, v in active.items() if k not in {"id", "state", "revision"}}
    config["provider_refs"] = [reference("provider", "fixture-provider", 2)]
    config["model_refs"] = [reference("model", "fixture-model", 2)]
    staged = await configuration.stage(admin, {"configuration": config}, meta("fixture-stage-2"))
    await configuration.validate(admin, staged["id"], meta("fixture-validate-2", 1))
    await configuration.activate(admin, staged["id"], meta("fixture-activate-2", 2))
    conv = await run.create_conversation(
        principal,
        {
            "title": "SQL tool component fixture",
            "model_choice": {"mode": "explicit", "model_id": "fixture-model"},
            "memory_policy": {
                "revision": 0,
                "read_enabled": False,
                "contribute_enabled": False,
                "scope": {"resource_refs": []},
            },
        },
        meta("fixture-conversation"),
    )
    record = await run.submit(
        principal,
        {
            "conversation_id": conv["id"],
            "text": "保留  原文\r\n与 fixed model",
            "attachment_refs": [],
        },
        meta("fixture-submit"),
    )
    await run.advance(principal, record["id"], "preparing", meta("fixture-prepare", 1))
    binding = (await run.store.get(principal, "run.bindings", record["id"])).payload
    source = binding["input_ref"]
    policy = {
        "id": "tool-sql-policy",
        "revision": 1,
        "allowed_capabilities": ["tool.invoke"],
        "denied_capabilities": [],
        "resource_scope": {
            "conversation_id": conv["id"],
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
        request_id="fixture-policy",
    )
    ctx = TrustedExecutionContext(
        principal=principal,
        scope=Scope(
            principal_id=principal.id,
            conversation_id=conv["id"],
            task_id=record["task_id"],
            capabilities=("tool.invoke",),
            resource_refs=(Ref.model_validate(source),),
        ),
        conversation_id=conv["id"],
        task_id=record["task_id"],
        run_id=record["id"],
        operation_id="tool-operation",
        trace_id="tool-trace",
        attempt_id="tool-attempt",
        deadline=record["budget"]["deadline"],
        capability_policy_ref=Ref.model_validate(reference("policy", policy["id"])),
        model_policy_ref=Ref.model_validate(binding["model_policy_ref"]),
    )
    spec = {
        "id": "fixture.write",
        "version": "v1",
        "description": "Controlled SQL action; no executor",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
            "additionalProperties": False,
        },
        "output_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        "categories": ["fixture"],
        "required_capabilities": ["tool.invoke"],
        "effect": "external_write",
        "provider_ref": reference("provider", "fixture-provider", 2),
        "retry_policy_ref": reference("policy", "fixture-no-retry"),
    }
    registry = ToolRegistry()
    registry.register(
        spec,
        expected_revision=0,
        binding=AdapterBinding(
            Ref.model_validate(spec["provider_ref"]),
            frozenset({"sql-component-test"}),
            implemented=True,
        ),
    )
    call = normalize(
        {
            "tool_ref": registry.reference(registry.snapshot()[1][0]),
            "arguments": {"text": "  保留\r\n原文  "},
            "action_id": "fixture-action",
        },
        registry,
    )
    ledger = ToolLedger(PostgresRecordStore(run.store.database))
    await ledger.bind(call, spec, ctx)
    reader = ControlledSQLReader(run.store, source)
    authority = ToolApprovalAuthority(
        ledger, registry, configuration, ControlledRoleEnvironment(), reader
    )
    service = ApprovalService(run.store, configuration, authority)
    approvals = ToolApprovalAdapter(ledger, authority, service)
    return ToolCase(
        ledger,
        registry,
        authority,
        approvals,
        ToolBudgetAdapter(ledger, BudgetService(run.store), approvals),
        service,
        ctx,
        call,
        spec,
        domain,
        reader,
    )


async def approve(case):
    pending = await case.approvals.precheck(case.call, case.spec, case.ctx)
    assert pending["kind"] == "waiting"
    record = await case.service.get(case.ctx.principal, pending["wait_ref"]["id"])
    await case.service.decide(
        case.ctx.principal,
        {
            "approval_id": record["id"],
            "decision": {
                "decision": "approve_once",
                "expected_arguments_hash": record["arguments_hash"],
                "expected_resource_refs": record["resource_refs"],
                "reason": "Controlled test user decision",
            },
        },
        meta("fixture-approve", record["revision"]),
    )
    return record


def estimates():
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "model_calls": 0,
        "tool_calls": 1,
        "child_agents": 0,
        "wall_time_ms": 100,
        "money": "0.01",
        "currency": "USD",
    }
