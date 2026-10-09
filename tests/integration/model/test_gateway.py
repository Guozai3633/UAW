"""Real persistence + explicitly controlled protocol replies, not actual LLM evidence."""

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx
import pytest

from tests.integration.test_control_plane import admitted, context, meta, seed
from tests.integration.test_control_plane import domain as domain
from uaw.composition import compose_understanding_context
from uaw.context.seed import StoredModelInputs
from uaw.infrastructure.blob.filesystem import FSBlobStore
from uaw.infrastructure.db.transactions import reference
from uaw.model.adapters import ChatCompletionsAdapter
from uaw.model.facade import ModelFacade
from uaw.model.gateway import ModelGateway
from uaw.model.policy import PolicyResolver
from uaw.run.budget import BudgetService
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.schema import validate_contract

Payload = dict[str, Any]


def reply(text: str = "Protocol fixture", *, model: str = "fixture-model") -> Payload:
    return {
        "id": "receipt-fixture",
        "model": model,
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": text},
            }
        ],
        "usage": {
            "prompt_tokens": 20,
            "completion_tokens": 8,
            "total_tokens": 28,
            "prompt_tokens_details": {"cached_tokens": 5},
        },
    }


@dataclass
class Case:
    model: ModelFacade
    request: Payload
    ctx: TrustedExecutionContext
    run: Payload
    requests: list[httpx.Request]
    responses: list[httpx.Response | Exception]
    inputs: StoredModelInputs


@pytest.fixture
async def case(domain, principal, tmp_path, request: pytest.FixtureRequest) -> AsyncIterator[Case]:
    configuration, run, admin = domain
    await seed(configuration, admin)
    secret = await configuration.put_secret(
        admin,
        {
            "provider_id": "fixture-provider",
            "secret": "fixture-only-provider-secret-123456789",
        },
        meta("model-fixture-secret"),
    )
    try:
        protocol_options = {}
        if getattr(request, "param", {}).get("json_object_mode", False):
            protocol_options = {
                "structured_output_mode": "json_object",
                "include_n": False,
                "reasoning_levels": ["none"],
                "default_reasoning_level": "none",
            }
        provider = await configuration.register(
            admin,
            "provider",
            {
                "provider": {
                    "id": "fixture-provider",
                    "kind": "model",
                    "endpoint": "http://127.0.0.1:1234/v1",
                    "credential_handle": secret["credential_handle"],
                    "profile_ref": reference("provider_profile", "model.chat_completions"),
                    "settings": {
                        "model_name": "fixture-model",
                        "timeout_ms": 1000,
                        "output_token_parameter": "max_completion_tokens",
                        "reservation_money": "0.250000000",
                        "allow_temperature": False,
                        **protocol_options,
                    },
                }
            },
            meta("model-fixture-provider", 1),
        )
        provider_revision = 2
        if getattr(request, "param", {}).get("active_provider_for_tools", False):
            # Controlled connectivity metadata for Agent/Tool composition tests,
            # not a real provider probe. Keep config/binding revisions consistent.
            binding = await run.store.get(configuration.platform, "providers", provider["id"])
            configured = await run.store.get(
                configuration.platform, "provider.configs", provider["id"]
            )
            await run.store.put(
                configuration.platform,
                configured.namespace,
                provider["id"],
                "ProviderDraft",
                configured.payload,
                expected_revision=2,
                request_id="agent-fixture-connected-config",
            )
            await run.store.put(
                configuration.platform,
                binding.namespace,
                provider["id"],
                "ProviderBinding",
                {**binding.payload, "state": "active", "revision": 3},
                expected_revision=2,
                request_id="agent-fixture-connected-binding",
            )
            provider_revision = 3
        await configuration.register(
            admin,
            "model",
            {
                "entry": {
                    "id": "fixture-model",
                    "provider_ref": reference("provider", provider["id"], provider_revision),
                    "display_name": "Protocol fixture",
                    "context_limit_tokens": getattr(request, "param", {}).get(
                        "context_limit_tokens", 100000
                    ),
                    "output_limit_tokens": getattr(request, "param", {}).get(
                        "output_limit_tokens", 16000
                    ),
                    "capabilities": ["text", "json_schema", "tool_calls"],
                }
            },
            meta("model-fixture-catalogue", 1),
        )
        active = await configuration.current()
        draft = {
            key: active[key]
            for key in (
                "environment_template_refs",
                "feature_flags",
                "approval_policy_ref",
                "storage_policy_ref",
            )
        }
        draft.update(
            model_refs=[reference("model", "fixture-model", 2)],
            provider_refs=[reference("provider", "fixture-provider", provider_revision)],
        )
        staged = await configuration.stage(
            admin, {"configuration": draft}, meta("model-fixture-stage")
        )
        await configuration.validate(admin, staged["id"], meta("model-fixture-validate", 1))
        await configuration.activate(admin, staged["id"], meta("model-fixture-activate", 2))
        record = await admitted(domain, principal)
        await run.advance(principal, record["id"], "preparing", meta("model-prepare", 1))
        ctx = context(principal, record)
        from uaw.shared.contracts import Ref

        await run.store.put(
            principal,
            "execution.policies",
            "model-test-policy",
            "CapabilityPolicy",
            {
                "id": "model-test-policy",
                "revision": 1,
                "allowed_capabilities": ["model.generate"],
                "denied_capabilities": [],
                "resource_scope": {"conversation_id": record["conversation_id"]},
                "network_allowlist": ["127.0.0.1"],
                "feature_flag_refs": [],
            },
            expected_revision=0,
            request_id="test-policy",
        )
        ctx = ctx.model_copy(
            update={
                "scope": ctx.scope.model_copy(update={"capabilities": ("model.generate",)}),
                "capability_policy_ref": Ref.model_validate(
                    reference("policy", "model-test-policy")
                ),
            }
        )
        binding = (await run.store.get(principal, "run.bindings", record["id"])).payload
        policies = PolicyResolver(run.store, configuration)
        inputs = StoredModelInputs(
            run.store, FSBlobStore(tmp_path), compose_understanding_context(run.store, policies)
        )
        input_ref = await inputs.seed(ctx, 128)
        requests: list[httpx.Request] = []
        responses: list[httpx.Response | Exception] = [httpx.Response(200, json=reply())]

        async def respond(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            response = responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response

        adapter = ChatCompletionsAdapter(
            httpx.AsyncClient(
                transport=httpx.MockTransport(respond),
                trust_env=False,
                follow_redirects=False,
            )
        )
        gateway = ModelGateway(
            run.store,
            PolicyResolver(run.store, configuration),
            inputs,
            BudgetService(run.store),
            inputs.blobs,
            adapter,
        )
        model = ModelFacade(gateway)
        request = {
            "context_snapshot_ref": input_ref,
            "model_config": {
                "model_id": "fixture-model",
                "catalog_revision": 2,
                "provider_ref": reference("provider", "fixture-provider", provider_revision),
                "policy_ref": binding["model_policy_ref"],
                "max_output_tokens": 128,
            },
            "output_protocol": "text",
            "attempt_id": ctx.attempt_id,
        }
        yield Case(model, request, ctx, record, requests, responses, inputs)
        await model.close()
    finally:
        await configuration.credentials.delete(secret["credential_handle"])


async def test_output_refs_dedupe_actual_usage_and_secret_separation(case, domain, principal):
    text = "完整输出" * 5000
    case.responses[:] = [httpx.Response(200, json=reply(text))]
    first, second = await asyncio.gather(
        case.model.generate(case.request, case.ctx), case.model.generate(case.request, case.ctx)
    )
    result = first if first["kind"] == "ok" else second
    assert result["kind"] == "ok" and len(case.requests) == 1
    assert await case.model.generate(case.request, case.ctx) == result
    output = result["payload"]
    assert not output["text_complete"] and len(output["text"]) == 16384
    assert (await case.inputs.blobs.get(principal, output["content_ref"]["id"])).decode() == text
    assert output["actual_config"]["provider_model_name"] == "fixture-model"
    assert output["actual_config"]["response_model_name"] == "fixture-model"
    assert output["usage"]["cached_input_tokens"] == 5
    assert "money" not in output["usage"]["resources"]
    ledger = (await domain[1].store.get(principal, "budget.ledgers", case.run["id"])).payload
    assert ledger["used"]["input_tokens"] == 20 and ledger["used"]["model_calls"] == 1
    assert ledger["held"]["money"] == "0.250000000" and ledger["billing_pending"]
    assert (
        case.requests[0].headers["authorization"] == "Bearer fixture-only-provider-secret-123456789"
    )
    assert "fixture-only-provider-secret" not in json.dumps(result)
    validate_contract("RuntimeModelruntimeGenerateResult", result)
    assert (await domain[1].get_run(principal, case.run["id"]))["status"] == "preparing"


async def test_fixed_model_inheritance_and_changes_cannot_send(case):
    powerless = case.ctx.model_copy(
        update={"scope": case.ctx.scope.model_copy(update={"capabilities": ()})}
    )
    assert (await case.model.generate(case.request, powerless))["kind"] == "denied"
    inherited = case.ctx.model_copy(update={"agent_id": "future-child"})
    resolved = await case.model.gateway.policies.resolve(case.request["model_config"], inherited)
    assert resolved.config["model_id"] == "fixture-model"
    altered = json.loads(json.dumps(case.request))
    altered["model_config"]["model_id"] = "silently-cheaper"
    denied = await case.model.generate(altered, case.ctx)
    assert denied["kind"] == "denied" and not case.requests
    altered["model_config"] = {**case.request["model_config"], "temperature": 0.4}
    assert (await case.model.generate(altered, case.ctx))["failure"][
        "code"
    ] == "model_parameter_unsupported"
    valid = await case.model.generate(case.request, case.ctx)
    assert valid["kind"] == "ok"
    altered["model_config"] = {**case.request["model_config"], "max_output_tokens": 64}
    assert (await case.model.generate(altered, case.ctx))["kind"] == "conflict"
    assert len(case.requests) == 1


async def test_safe_retry_separate_attempts_and_same_model(case, domain, principal):
    case.responses[:] = [httpx.Response(429), httpx.Response(200, json=reply())]
    result = await case.model.generate(case.request, case.ctx)
    assert result["kind"] == "ok" and len(case.requests) == 2
    assert result["payload"]["attempt_id"] != case.ctx.attempt_id
    assert [json.loads(r.content)["model"] for r in case.requests] == ["fixture-model"] * 2
    ledger = (await domain[1].store.get(principal, "budget.ledgers", case.run["id"])).payload
    assert ledger["used"]["model_calls"] == 2 and ledger["held"]["money"] == "0.500000000"
    failed = await domain[1].store.get(principal, "model.attempts", case.ctx.attempt_id)
    assert (
        failed.payload["state"] == "failed"
        and failed.payload["usage"]["billing_state"] == "pending"
    )
    assert "input_tokens" not in failed.payload["usage"]["resources"]


@pytest.mark.parametrize("response", [httpx.ReadTimeout("fixture timeout"), httpx.Response(503)])
async def test_ambiguous_failure_not_retried_and_survives_replay(case, domain, principal, response):
    case.responses[:] = [response]
    result = await case.model.generate(case.request, case.ctx)
    assert result["kind"] == "failed" and len(case.requests) == 1
    assert await case.model.generate(case.request, case.ctx) == result
    ledger = (await domain[1].store.get(principal, "budget.ledgers", case.run["id"])).payload
    assert ledger["billing_pending"] and ledger["held"]["output_tokens"] == 128


async def test_invalid_structured_output_retains_observed_tokens(case, domain, principal):
    case.request.update(
        output_protocol="json_schema",
        output_schema={
            "type": "object",
            "properties": {"answer": {"type": "integer"}},
            "required": ["answer"],
            "additionalProperties": False,
        },
    )
    case.responses[:] = [httpx.Response(200, json=reply('{"answer":"wrong"}'))]
    result = await case.model.generate(case.request, case.ctx)
    assert result["failure"]["code"] == "provider_structured_output_invalid"
    assert len(case.requests) == 1
    ledger = (await domain[1].store.get(principal, "budget.ledgers", case.run["id"])).payload
    assert ledger["used"]["input_tokens"] == 20 and ledger["used"]["output_tokens"] == 8
    attempt = await domain[1].store.get(principal, "model.attempts", case.ctx.attempt_id)
    assert attempt.payload["response_ref"]["kind"] == "blob"


async def test_native_structured_output_and_unavailable_tools(case):
    no_tools = {**case.request, "output_protocol": "tool_calls"}
    assert (await case.model.generate(no_tools, case.ctx))["failure"][
        "code"
    ] == "model_tools_unavailable"
    assert not case.requests
    case.request.update(
        output_protocol="json_schema",
        output_schema={
            "type": "object",
            "properties": {"answer": {"type": "integer"}},
            "required": ["answer"],
            "additionalProperties": False,
        },
    )
    case.responses[:] = [httpx.Response(200, json=reply('{"answer":42}'))]
    result = await case.model.generate(case.request, case.ctx)
    assert result["payload"]["structured_data"] == {"answer": 42}
    assert json.loads(case.requests[0].content)["response_format"]["type"] == "json_schema"


async def test_scope_revocation_and_remote_schema_deny_before_sending(case, domain):
    wrong = case.ctx.model_copy(update={"run_id": "foreign-run"})
    assert (await case.model.generate(case.request, wrong))["kind"] == "missing"
    schema = {
        **case.request,
        "output_protocol": "json_schema",
        "output_schema": {"$ref": "https://never-fetch.invalid/schema"},
    }
    assert (await case.model.generate(schema, case.ctx))["failure"][
        "code"
    ] == "model_schema_refs_unsupported"
    await domain[0].revoke_provider(domain[2], "fixture-provider", meta("model-revoke", 2))
    assert (await case.model.generate(case.request, case.ctx))["kind"] == "denied"
    assert not case.requests


async def test_cancel_closes_provider_work_and_keeps_unknown_billing(case, domain, principal):
    started = asyncio.Event()
    stopped = asyncio.Event()

    async def wait(request: httpx.Request) -> httpx.Response:
        case.requests.append(request)
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            stopped.set()
        raise AssertionError("Cancelled fixture returned unexpectedly")

    await case.model.gateway.adapter.close()
    case.model.gateway.adapter = ChatCompletionsAdapter(
        httpx.AsyncClient(transport=httpx.MockTransport(wait))
    )
    operation = asyncio.create_task(case.model.generate(case.request, case.ctx))
    await asyncio.wait_for(started.wait(), 5)
    await domain[1].control(
        principal,
        {
            "run_id": case.run["id"],
            "control": {
                "mode": "cancel",
                "preserve_refs": [],
                "reason": "Stop actual pending work",
            },
        },
        meta("cancel-model", 2),
    )
    result = await asyncio.wait_for(operation, 5)
    assert result["kind"] == "cancelled" and stopped.is_set() and len(case.requests) == 1
    ledger = (await domain[1].store.get(principal, "budget.ledgers", case.run["id"])).payload
    assert ledger["billing_pending"] and ledger["cancel_requested"]


async def test_claimed_invocation_after_restart_is_not_resent(case, domain, principal):
    from uaw.infrastructure.db.records import parameter_hash

    digest = parameter_hash({"request": case.request, "context": case.ctx.wire()})
    # Commit an actual claim without calling a provider, modelling process loss at this boundary.
    from uaw.infrastructure.db.transactions import RecordTransaction, timestamp
    from uaw.model.gateway import request_meta

    async def claim(tx: RecordTransaction) -> Payload:
        await tx.write(
            "model.invocations",
            case.ctx.attempt_id,
            "ModelInvocation",
            {
                "id": case.ctx.attempt_id,
                "run_id": case.run["id"],
                "request_hash": digest,
                "request": case.request,
                "operation_id": case.ctx.operation_id,
                "trace_id": case.ctx.trace_id,
                "state": "claimed",
                "created_at": timestamp(),
            },
        )
        return {"new": True}

    await case.model.gateway.transactions.execute(
        principal,
        f"conversation:{case.run['conversation_id']}",
        request_meta("model-claim", case.ctx.attempt_id),
        {"action": "model.claim", "hash": digest},
        claim,
    )
    result = await case.model.generate(case.request, case.ctx)
    assert result["failure"]["code"] == "model_invocation_pending" and not case.requests


async def test_changed_execution_permission_cannot_reuse_old_snapshot(case, domain, principal):
    store = domain[1].store
    record = await store.get(principal, "execution.policies", "model-test-policy")
    await store.put(
        principal,
        "execution.policies",
        record.resource_id,
        "CapabilityPolicy",
        {**record.payload, "revision": 2, "denied_capabilities": ["model.generate"]},
        expected_revision=1,
        request_id="revoke-model-permission",
    )
    stale = await case.model.generate(case.request, case.ctx)
    assert stale["kind"] == "stale" and not case.requests
    from uaw.shared.contracts import Ref

    current = case.ctx.model_copy(
        update={
            "capability_policy_ref": Ref.model_validate(reference("policy", record.resource_id, 2))
        }
    )
    assert (await case.model.generate(case.request, current))["kind"] == "denied"
