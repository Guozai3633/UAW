"""Actual SQL data/role/config authority; no native confirmation or file dispatch claimed."""

import pytest

from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.test_runtime_sources import profile
from tests.integration.tool.conftest import tool_case as tool_case
from uaw.infrastructure.db.transactions import reference
from uaw.infrastructure.installed_files import OriginalFileApprovalGate, RegisteredFileDataAccess
from uaw.infrastructure.installed_tool_authority import InstalledToolApprovalGate
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import DomainError
from uaw.tool.invocation.schema import normalize
from uaw.tool.ledger import ToolLedger
from uaw.tool.providers.file_read import file_read_spec
from uaw.tool.registry import AdapterBinding, ToolRegistry


@pytest.fixture
async def file_data_case(tool_case, tmp_path):
    from tests.integration.test_stage_wiring import container

    case = tool_case
    config, run, _ = case.domain
    c = container(run.store, config, tmp_path)
    workspace = Ref(kind="workspace", id="explicit-file-workspace", version="1")
    policy_row = await run.store.get(
        case.ctx.principal, "execution.policies", case.ctx.capability_policy_ref.id
    )
    policy = {
        **policy_row.payload,
        "revision": 2,
        "allowed_capabilities": ["tool.invoke", "workspace.process", "file.read"],
        "resource_scope": {
            **policy_row.payload["resource_scope"],
            "resource_refs": [workspace.wire()],
        },
    }
    await run.store.put(
        case.ctx.principal,
        "execution.policies",
        policy["id"],
        "CapabilityPolicy",
        policy,
        expected_revision=1,
        request_id="explicit-file-test-policy",
    )
    case.ctx = case.ctx.model_copy(
        update={
            "operation_id": "file-data-operation",
            "attempt_id": "file-data-attempt",
            "trace_id": "file-data-trace",
            "scope": case.ctx.scope.model_copy(
                update={
                    "resource_refs": (workspace,),
                    "capabilities": tuple(policy["allowed_capabilities"]),
                }
            ),
            "capability_policy_ref": Ref.model_validate(reference("policy", policy["id"], 2)),
        }
    )
    provider_ref = Ref.model_validate((await config.current())["provider_refs"][0])
    provider = Principal(id="bounded-file-provider", kind="service", auth_session_id="internal")
    registry = ToolRegistry()
    spec = file_read_spec(provider_ref)
    registry.register(spec, expected_revision=0)
    call = normalize(
        {
            "tool_ref": registry.reference(registry.snapshot()[1][0]),
            "arguments": {"workspace_ref": workspace.wire(), "path": "file.txt"},
            "action_id": "actual-file-action",
        },
        registry,
    )
    access = c.tool_access
    role = await access.register_role(
        profile(spec["categories"]), meta("file-role", 0), authenticated_service=config.platform
    )
    await access.bind(
        case.ctx, role, meta("file-role-bind", 0), authenticated_service=config.platform
    )
    ledger = ToolLedger(run.store)
    await ledger.bind(call, spec, case.ctx)
    return case, c, registry, provider_ref, provider, call, spec, ledger


async def test_current_data_authority_keeps_fixed_model_and_registered_action(file_data_case):
    case, c, registry, pin, provider, call, spec, _ = file_data_case
    source = RegisteredFileDataAccess(c, registry, pin, provider)
    assert await source.check(call, spec, case.ctx, provider=provider) is None
    other = case.ctx.model_copy(
        update={
            "principal": case.ctx.principal.model_copy(
                update={"auth_session_id": "another-session"}
            )
        }
    )
    with pytest.raises(DomainError):
        await source.check(call, spec, other, provider=provider)
    with pytest.raises(DomainError) as wrong:
        await source.check(
            call,
            spec,
            case.ctx,
            provider=provider.model_copy(update={"auth_session_id": "other-provider-session"}),
        )
    assert wrong.value.failure.code == "file_data_provider_denied"


async def test_data_read_after_cancel_does_not_restore_execution(file_data_case):
    case, c, registry, pin, provider, call, spec, _ = file_data_case
    source = RegisteredFileDataAccess(c, registry, pin, provider)
    config, run, _ = case.domain
    current = await run.get_run(case.ctx.principal, case.ctx.run_id)
    await run.control(
        case.ctx.principal,
        {
            "run_id": case.ctx.run_id,
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "stop original run"},
        },
        meta("cancel-data-source", current["revision"]),
    )
    assert await source.check(call, spec, case.ctx, provider=provider) is None
    with pytest.raises(DomainError):
        await c.tool_access.snapshot(case.ctx)
    await c.tool_access.revoke(
        case.ctx, meta("withdraw-data-binding", 1), authenticated_service=config.platform
    )
    with pytest.raises(DomainError) as revoked:
        await source.check(call, spec, case.ctx, provider=provider)
    assert revoked.value.failure.code == "tool_binding_revoked"


async def test_provider_revocation_during_source_wait_blocks_data(file_data_case, monkeypatch):
    case, c, registry, pin, provider, call, spec, _ = file_data_case
    source = RegisteredFileDataAccess(c, registry, pin, provider)
    old = c.tool_access.runs.data
    config = c.configuration
    calls = 0

    async def withdrawn(ctx):
        nonlocal calls
        result = await old(ctx)
        calls += 1
        if calls == 1:
            row = await c.records.get(config.platform, "providers", pin.id)
            await c.records.put(
                config.platform,
                "providers",
                pin.id,
                "ProviderBinding",
                {**row.payload, "revision": row.revision + 1, "state": "revoked"},
                expected_revision=row.revision,
                request_id="revoke-during-data-source",
            )
        return result

    monkeypatch.setattr(c.tool_access.runs, "data", withdrawn)
    with pytest.raises(DomainError) as rejected:
        await source.check(call, spec, case.ctx, provider=provider)
    assert rejected.value.failure.code == "file_data_provider_denied"


async def test_missing_approval_adapter_cannot_admit_original_file(file_data_case):
    case, _, _, _, _, call, _, ledger = file_data_case
    gate = OriginalFileApprovalGate(ledger)
    with pytest.raises(DomainError) as unavailable:
        await gate.check(
            {
                "context": case.ctx.wire(),
                "parameters": {"action": "file.read", "parameters": call["arguments"]},
            },
            case.ctx,
        )
    assert unavailable.value.failure.category == "dependency"


@pytest.fixture
async def original_file_gate(file_data_case):
    """Real SQL authority/approval. Only root Reader and initial flags are controlled.

    The enabled configuration is a new fixture version before a NEW Run, never
    a rewritten Run pin or production administrator publication.
    """
    from uaw.run.approval import ApprovalService
    from uaw.tool.approval import ToolApprovalAdapter
    from uaw.tool.authority import ToolApprovalAuthority

    case, c, _, pin, _, old_call, spec, ledger = file_data_case
    config, run, _ = case.domain
    active = await config.current()
    revision = active["revision"] + 1
    await run.store.put(
        config.platform,
        "configurations",
        active["id"],
        "ConfigurationVersion",
        {
            **active,
            "revision": revision,
            "feature_flags": [
                {**f, "enabled": f["id"] == "local_files"} for f in active["feature_flags"]
            ],
        },
        expected_revision=active["revision"],
        request_id="controlled-file-gate-config",
    )
    pointer = await run.store.get(config.platform, "configuration.pointer", "current")
    await run.store.put(
        config.platform,
        "configuration.pointer",
        "current",
        "Ref",
        reference("configuration", active["id"], revision),
        expected_revision=pointer.revision,
        request_id="controlled-file-gate-pointer",
    )
    record = await run.submit(
        case.ctx.principal,
        {
            "conversation_id": case.ctx.conversation_id,
            "text": "explicit file gate",
            "attachment_refs": [],
        },
        meta("new-file-gate-run"),
    )
    await run.advance(case.ctx.principal, record["id"], "preparing", meta("prepare-file-gate", 1))
    binding = (await run.store.get(case.ctx.principal, "run.bindings", record["id"])).payload
    previous = (
        await run.store.get(
            case.ctx.principal, "execution.policies", case.ctx.capability_policy_ref.id
        )
    ).payload
    policy = {
        **previous,
        "id": "original-file-gate-policy",
        "revision": 1,
        "resource_scope": {**previous["resource_scope"], "task_id": record["task_id"]},
    }
    await run.store.put(
        case.ctx.principal,
        "execution.policies",
        policy["id"],
        "CapabilityPolicy",
        policy,
        expected_revision=0,
        request_id="original-file-gate-policy",
    )
    ctx = case.ctx.model_copy(
        update={
            "run_id": record["id"],
            "task_id": record["task_id"],
            "deadline": record["budget"]["deadline"],
            "operation_id": "original-file-gate-operation",
            "attempt_id": "original-file-gate-attempt",
            "scope": case.ctx.scope.model_copy(update={"task_id": record["task_id"]}),
            "capability_policy_ref": Ref.model_validate(reference("policy", policy["id"])),
            "model_policy_ref": Ref.model_validate(binding["model_policy_ref"]),
        }
    )
    c.tool_access.implemented_flags = frozenset({"file_access"})
    role = Ref.model_validate((await c.tool_access._binding(case.ctx))["role_ref"])
    await c.tool_access.bind(
        ctx, role, meta("gate-role-bind", 0), authenticated_service=config.platform
    )
    registry = ToolRegistry()
    registry.register(
        spec,
        expected_revision=0,
        binding=AdapterBinding(pin, frozenset({c.tool_access.environment}), implemented=True),
    )
    call = normalize({k: v for k, v in old_call.items() if k != "arguments_hash"}, registry)
    await ledger.bind(call, spec, ctx)

    class ControlledRootReader:
        async def resolve(self, fixed_call, fixed_spec, context):
            assert (fixed_call, fixed_spec, context) == (call, spec, ctx)
            return ctx.scope.resource_refs

    authority = ToolApprovalAuthority(
        ledger,
        registry,
        config,
        c.tool_access,
        ControlledRootReader(),
        policies=c.execution_permissions,
    )
    approvals = ApprovalService(run.store, config, authority, permissions=c.execution_permissions)
    adapter = ToolApprovalAdapter(ledger, authority, approvals)
    gate = OriginalFileApprovalGate(ledger)
    gate.approvals = adapter
    request = {
        "context": ctx.wire(),
        "parameters": {"action": "file.read", "parameters": call["arguments"]},
    }
    return gate, approvals, request, ctx, c


@pytest.mark.parametrize("decision", ["approve_once", "decline"])
async def test_original_file_gate_consumes_exact_sql_user_decision(original_file_gate, decision):
    gate, service, request, ctx, c = original_file_gate
    with pytest.raises(DomainError) as pending:
        await gate.check(request, ctx)
    assert pending.value.failure.code == "approval_pending"
    call, spec, _ = await gate.ledger.action("actual-file-action", ctx)
    # Replay the adapter's original request ID, never create a second approval.
    waiting = await gate.approvals.precheck(call, spec, ctx)
    assert waiting["kind"] == "waiting"
    record = await service.get(ctx.principal, waiting["wait_ref"]["id"])
    await service.decide(
        ctx.principal,
        {
            "approval_id": record["id"],
            "decision": {
                "decision": decision,
                "expected_arguments_hash": record["arguments_hash"],
                "expected_resource_refs": record["resource_refs"],
                "reason": "Controlled test user decision",
            },
        },
        meta("decide-original-file", record["revision"]),
    )
    if decision == "decline":
        with pytest.raises(DomainError) as declined:
            await gate.check(request, ctx)
        assert declined.value.failure.code == "approval_declined"
    else:
        assert await gate.check(request, ctx) is None
        with pytest.raises(DomainError) as changed:
            await gate.check(
                {
                    **request,
                    "parameters": {
                        "action": "file.read",
                        "parameters": {
                            **request["parameters"]["parameters"],
                            "path": "different.txt",
                        },
                    },
                },
                ctx,
            )
        assert changed.value.failure.code == "file_original_approval_denied"
        # Revoke the actual role after approval; the persisted grant cannot bypass it.
        await c.tool_access.revoke(
            ctx,
            meta("revoke-approved-file-role", 1),
            authenticated_service=c.configuration.platform,
        )
        with pytest.raises(DomainError):
            await gate.check(request, ctx)


async def test_joint_root_gate_preserves_original_sql_decision_and_shared_authority(
    original_file_gate,
):
    gate, service, request, ctx, c = original_file_gate
    call, spec, _ = await gate.ledger.action("actual-file-action", ctx)
    waiting = await gate.approvals.precheck(call, spec, ctx)
    record = await service.get(ctx.principal, waiting["wait_ref"]["id"])
    await service.decide(
        ctx.principal,
        {
            "approval_id": record["id"],
            "decision": {
                "decision": "approve_once",
                "expected_arguments_hash": record["arguments_hash"],
                "expected_resource_refs": record["resource_refs"],
                "reason": "Controlled SQL joint root test",
            },
        },
        meta("joint-root-original-approval", record["revision"]),
    )
    original_authority, original_resources = service.authority, service.authority.resources
    workspace = ctx.scope.resource_refs[0]
    root = {
        "owner": ctx.principal.wire(),
        "device_id": "joint-root-device",
        "workspace_ref": workspace.wire(),
        "root_handle": "joint-root-handle",
        "binding_revision": 1,
        "allowed_actions": ["file.read"],
        "expires_at": ctx.deadline,
    }

    class BracketedRoots:
        def __init__(self):
            self.calls = 0

        async def current(self, device, workspace, ctx):
            raise AssertionError("Joint callback must not recursively read roots")

        async def checked_current(self, device, workspace, ctx, *, check):
            self.calls += 1
            await check(root)
            return root

    roots = BracketedRoots()
    assert (
        await gate.check_root(
            request, ctx, roots=roots, device_id=root["device_id"], workspace=workspace
        )
        == root
    )
    assert roots.calls == 1
    child = InstalledToolApprovalGate(c, roots, root["device_id"])
    assert (
        await child.check_root(
            request, ctx, roots=roots, device_id=root["device_id"], workspace=workspace
        )
        == root
    )
    assert roots.calls == 2
    assert service.authority is original_authority
    assert service.authority.resources is original_resources
    await c.tool_access.revoke(
        ctx, meta("revoke-joint-root-role", 1), authenticated_service=c.configuration.platform
    )
    with pytest.raises(DomainError):
        await gate.check_root(
            request, ctx, roots=roots, device_id=root["device_id"], workspace=workspace
        )
    with pytest.raises(DomainError):
        await child.check_root(
            request, ctx, roots=roots, device_id=root["device_id"], workspace=workspace
        )
