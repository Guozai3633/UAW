"""Actual administrator local-provider/role/approval/budget/results wiring; no LLM."""

import pytest

from tests.integration.test_control_plane import admitted, context, meta, seed
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_runtime_sources import profile
from tests.integration.test_stage_wiring import container
from uaw.composition import assemble_office_tools
from uaw.shared.builtin_tools import publish_builtin_office
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import DomainError
from uaw.tool.providers.arithmetic import arithmetic_spec
from uaw.tool.providers.json_data import json_data_spec
from uaw.tool.providers.text import text_spec
from uaw.tool.registry import AdapterBinding, ToolRegistry


async def test_actual_office_provider_three_tools_cancel_recovery_and_revocation(
    domain, principal, tmp_path
):
    config, runs, admin = domain
    original = await seed(config, admin)
    provider = await publish_builtin_office(config, admin, "actual-builtin")
    active = await config.current()
    assert active["feature_flags"] == original["feature_flags"]
    assert active["model_refs"] == original["model_refs"]
    binding = await runs.store.get(config.platform, "providers", provider.id)
    assert binding.payload["kind"] == "local" and binding.payload["state"] == "active"
    record = await admitted(domain, principal)
    await runs.advance(principal, record["id"], "preparing", meta("office-prepare", 1))
    admission = (await runs.store.get(principal, "run.bindings", record["id"])).payload
    ctx = context(principal, record).model_copy(
        update={
            "task_id": record["task_id"],
            "scope": context(principal, record).scope.model_copy(
                update={"task_id": record["task_id"], "capabilities": ("tool.invoke",)}
            ),
            "model_policy_ref": Ref.model_validate(admission["model_policy_ref"]),
            "capability_policy_ref": Ref(kind="policy", id="office-policy", version="1"),
        }
    )
    await runs.store.put(
        principal,
        "execution.policies",
        "office-policy",
        "CapabilityPolicy",
        {
            "id": "office-policy",
            "revision": 1,
            "allowed_capabilities": ["tool.invoke"],
            "denied_capabilities": [],
            "resource_scope": {"conversation_id": ctx.conversation_id},
            "network_allowlist": [],
            "feature_flag_refs": [],
        },
        expected_revision=0,
        request_id="policy",
    )
    control = container(runs.store, config, tmp_path)
    role = await control.tool_access.register_role(
        profile(["text", "arithmetic", "data"]),
        meta("office-role", 0),
        authenticated_service=config.platform,
    )
    await control.tool_access.bind(
        ctx, role, meta("office-bind", 0), authenticated_service=config.platform
    )
    registry = ToolRegistry()
    for factory in (text_spec, arithmetic_spec, json_data_spec):
        registry.register(
            factory(provider),
            expected_revision=registry.revision,
            binding=AdapterBinding(provider, frozenset({"development"}), implemented=True),
        )
    pins = tuple(Ref.model_validate(registry.reference(e)) for e in registry.snapshot()[1])
    service = Principal(
        id="actual-office-adapter", kind="service", auth_session_id="internal-office"
    )
    tools = assemble_office_tools(control, registry=registry, tool_refs=pins, provider=service)
    cases = {
        "text.inspect": {"text": "实际文本"},
        "arithmetic.calculate": {"operation": "percent", "operands": ["1200", "7.5"]},
        "data.inspect_json": {"text": '{"x":1}', "required_keys": ["x", "year"]},
    }
    results = []
    for number, pin in enumerate(pins):
        call_ctx = ctx.model_copy(
            update={
                "operation_id": f"office-op-{number}",
                "attempt_id": f"office-attempt-{number}",
                "trace_id": f"office-trace-{number}",
            }
        )
        call = {
            "tool_ref": pin.wire(),
            "arguments": cases[pin.id],
            "action_id": f"office-action-{number}",
        }
        waiting = await tools.facade.invoke(call, call_ctx)
        assert waiting["kind"] == "waiting", waiting
        approval = await tools.approvals.get(principal, waiting["wait_ref"]["id"])
        await tools.approvals.decide(
            principal,
            {
                "approval_id": approval["id"],
                "decision": {
                    "decision": "approve_once",
                    "expected_arguments_hash": approval["arguments_hash"],
                    "expected_resource_refs": approval["resource_refs"],
                    "reason": "Actual exact local approval",
                },
            },
            meta(f"approve-{number}", approval["revision"]),
        )
        actual = await tools.facade.invoke(call, call_ctx)
        assert actual["kind"] == "ok", actual
        usage_ref = Ref.model_validate(actual["payload"]["usage_ref"])
        usage = await runs.store.get(principal, "usage", usage_ref.id)
        assert str(usage.revision) == usage_ref.version
        assert usage.payload["billing_state"] == "confirmed"
        assert usage.payload["attempt_id"] == call_ctx.attempt_id
        data = actual["payload"]["data"]
        if pin.id == "arithmetic.calculate":
            assert data["value"] == "90.0"
        elif pin.id == "data.inspect_json":
            assert data["missing_keys"] == ["year"]
        results.append(
            (call, call_ctx, await tools.facade.read_outcome(call["action_id"], call_ctx))
        )
    current = await runs.get_run(principal, ctx.run_id)
    await runs.control(
        principal,
        {
            "run_id": ctx.run_id,
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop new execution"},
        },
        meta("cancel", current["revision"]),
    )
    restarted = assemble_office_tools(control, registry=registry, tool_refs=pins, provider=service)
    for call, call_ctx, result in results:
        assert await restarted.facade.read_outcome(call["action_id"], call_ctx) == result
    await config.revoke_provider(admin, provider.id, meta("revoke-local", int(provider.version)))
    with pytest.raises(DomainError):
        await restarted.facade.read_outcome(results[0][0]["action_id"], results[0][1])
