"""Real SQL/event/model-gateway integration with controlled semantic replies, not LLM QA."""

import asyncio
import json
from dataclasses import dataclass
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from tests.integration.model.test_gateway import Case, reply
from tests.integration.model.test_gateway import case as case
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from uaw.api.application import create_app
from uaw.composition import Container, RuntimeBindings
from uaw.context.intent import understanding_template
from uaw.intent.facade import IntentFacade
from uaw.intent.frame import FrameRepository
from uaw.intent.original import OriginalReader
from uaw.model.policy import PolicyResolver
from uaw.run.inputs import RunInputReader
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.shared.errors import DomainError
from uaw.shared.schema import validate_contract
from uaw.shared.settings import Settings
from uaw.shared.stores import StoreMissing

Payload = dict[str, Any]


def proposal(text: str, summary: str = "理解提示") -> Payload:
    quote = {"source_index": 0, "start": 0, "end": len(text), "text": text}
    return {
        "summary": summary,
        "requirements": [{"quote": quote}],
        "outputs": [],
        "assumptions": [],
        "unresolved": [],
    }


def response(value: Payload) -> httpx.Response:
    return httpx.Response(200, json=reply(json.dumps(value, ensure_ascii=False)))


@dataclass
class UnderstandingCase:
    intent: IntentFacade
    request: Payload
    ctx: TrustedExecutionContext
    original: Payload


@pytest.fixture
async def understanding(case: Case, domain, principal) -> UnderstandingCase:
    store = domain[1].store
    policy = await store.get(principal, "execution.policies", "model-test-policy")
    await store.put(
        principal,
        policy.namespace,
        policy.resource_id,
        "CapabilityPolicy",
        {
            **policy.payload,
            "revision": 2,
            "allowed_capabilities": ["model.generate", "intent.understand"],
        },
        expected_revision=1,
        request_id="understanding-policy",
    )
    ctx = case.ctx.model_copy(
        update={
            "capability_policy_ref": Ref.model_validate(
                {"kind": "policy", "id": policy.resource_id, "version": "2"}
            ),
            "scope": case.ctx.scope.model_copy(
                update={"capabilities": ("model.generate", "intent.understand")}
            ),
        }
    )
    reader = RunInputReader(store)
    inputs = await reader.read(ctx)
    assert case.inputs.understanding is not None
    intent = IntentFacade(
        OriginalReader(reader),
        case.inputs.understanding,
        case.model,
        PolicyResolver(store, domain[0]),
        FrameRepository(store),
    )
    request = {
        "original_input_ref": inputs.refs[0],
        "user_patch_refs": [],
        "material_refs": [],
        "expected_revision": 0,
    }
    case.responses[:] = [response(proposal(inputs.inputs[0]["text"]))]
    return UnderstandingCase(intent, request, ctx, inputs.inputs[0])


async def test_full_source_advisory_summary_and_real_atomic_publication(
    understanding, case, domain, principal
):
    result = await understanding.intent.understand(understanding.request, understanding.ctx)
    assert result["kind"] == "ok", result
    frame = result["payload"]
    assert frame["goal"] == understanding.original["text"]
    assert frame["summary"] == "理解提示" and frame["revision"] == 1
    quote = frame["constraints"][0]["source_refs"][0]
    assert quote["location"] == {"kind": "text_span", "start": 0, "end": len(frame["goal"])}
    assert (
        await domain[1].store.get(principal, "inputs", understanding.original["id"])
    ).payload == understanding.original
    assert await understanding.intent.frames.current(principal, case.run["task_id"]) == frame
    current_run = await domain[1].get_run(principal, case.run["id"])
    assert (
        current_run["frame_ref"] == result["output_refs"][0]
        and current_run["status"] == "preparing"
    )
    data = json.loads(case.requests[0].content)
    assert data["model"] == "fixture-model" and data["response_format"]["type"] == "json_schema"
    assert data["messages"][0] == {"role": "system", "content": understanding_template()}
    assert json.loads(data["messages"][1]["content"])["text"] == frame["goal"]
    events = (await domain[1].events.read(principal, case.run["conversation_id"], limit=100))[
        "items"
    ]
    assert len([event for event in events if event["type"] == "task.frame.committed"]) == 1
    assert "fixture-only-provider-secret" not in json.dumps(frame)
    validate_contract("RuntimeIntentruntimeUnderstandResult", result)


async def test_durable_replay_no_repeat_model_and_changed_request_conflict(understanding, case):
    first = await understanding.intent.understand(understanding.request, understanding.ctx)
    assert first["kind"] == "ok", first
    assert await understanding.intent.understand(understanding.request, understanding.ctx) == first
    changed = {**understanding.request, "expected_revision": 1}
    result = await understanding.intent.understand(changed, understanding.ctx)
    assert result["failure"]["code"] == "idempotency_conflict" and len(case.requests) == 1


async def test_bad_quote_cannot_invent_hard_requirement_and_is_billed(
    understanding, case, domain, principal
):
    value = proposal(understanding.original["text"])
    value["requirements"][0]["quote"]["text"] = "还要把全部资料发布到公网"
    case.responses[:] = [response(value)]
    result = await understanding.intent.understand(understanding.request, understanding.ctx)
    assert result["failure"]["code"] == "intent_quote_invalid"
    with pytest.raises(StoreMissing):
        await domain[1].store.get(principal, "intent.frames", case.run["task_id"])
    # Re-reading failed semantics uses the saved Model output, not another provider request.
    assert (await understanding.intent.understand(understanding.request, understanding.ctx))[
        "failure"
    ]["code"] == "intent_quote_invalid"
    ledger = (await domain[1].store.get(principal, "budget.ledgers", case.run["id"])).payload
    assert ledger["used"]["model_calls"] == 1 and len(case.requests) == 1


async def test_text_only_quote_is_grounded_with_raw_model_output_preserved(understanding, case):
    value = proposal(understanding.original["text"])
    quote = value["requirements"][0]["quote"]
    quote.pop("start")
    quote.pop("end")
    case.responses[:] = [response(value)]
    result = await understanding.intent.understand(understanding.request, understanding.ctx)
    assert result["kind"] == "ok", result
    source = result["payload"]["constraints"][0]["source_refs"][0]
    assert source["location"] == {"kind": "text_span", "start": 0, "end": len(quote["text"])}
    output = await understanding.intent.frames.store.get(
        understanding.ctx.principal, "model.outputs", understanding.ctx.attempt_id
    )
    assert output.payload["structured_data"] == value
    assert result["payload"]["goal"] == understanding.original["text"]


async def test_inferred_extra_work_cannot_replace_complete_user_goal(understanding, case):
    value = proposal(understanding.original["text"], "做完后发布到外网")
    value["requirements"], value["assumptions"] = [], ["可能需要发布，用户尚未确认"]
    value["unresolved"] = ["缺少资料，需要读取获准材料"]
    case.responses[:] = [response(value)]
    frame = (await understanding.intent.understand(understanding.request, understanding.ctx))[
        "payload"
    ]
    assert frame["goal"] == understanding.original["text"]
    assert not frame["output_specs"] and not frame["constraints"] and frame["unresolved"]


async def test_patch_invalidates_old_frame_revise_preserves_source_history(
    understanding, case, domain, principal
):
    first = await understanding.intent.understand(understanding.request, understanding.ctx)
    assert first["kind"] == "ok", first
    state = await domain[1].append_requirement(
        principal, case.run["id"], "不要发布，只交付Markdown", meta("user-patch", 1)
    )
    assert (
        await domain[1].append_requirement(
            principal, case.run["id"], "不要发布，只交付Markdown", meta("user-patch", 1)
        )
        == state
    )
    with pytest.raises(DomainError) as missing:
        await understanding.intent.frames.current(principal, case.run["task_id"])
    assert missing.value.failure.code == "task_frame_unavailable"
    item = (
        await domain[1].store.get(principal, "items", "understanding-" + case.run["task_id"])
    ).payload
    assert item["status"] == "waiting"
    assert (await understanding.intent.understand(understanding.request, understanding.ctx))[
        "kind"
    ] == "stale"
    value = proposal(understanding.original["text"])
    value["outputs"] = [
        {
            "kind": "markdown",
            "quote": {
                "source_index": 1,
                "start": 0,
                "end": len("不要发布，只交付Markdown"),
                "text": "不要发布，只交付Markdown",
            },
        }
    ]
    case.responses[:] = [response(value)]
    ctx = understanding.ctx.model_copy(
        update={"attempt_id": "patch-model", "operation_id": "patch-operation"}
    )
    request = {
        "current_frame_ref": first["output_refs"][0],
        "new_input_ref": state["patch_refs"][-1],
        "expected_revision": 1,
    }
    result = await understanding.intent.revise(request, ctx)
    assert result["kind"] == "ok", result
    assert result["payload"]["revision"] == result["payload"]["input_revision"] == 2
    assert "不要发布，只交付Markdown" in result["payload"]["goal"]
    assert (
        await domain[1].store.get(principal, "intent.frames", case.run["task_id"], revision=1)
    ).payload == first["payload"]
    assert await understanding.intent.revise(request, ctx) == result
    assert len(case.requests) == 2


async def test_new_input_during_model_work_blocks_old_commit(
    understanding, case, domain, principal
):
    original_generate = case.model.generate

    async def change_then_return(request, ctx):
        result = await original_generate(request, ctx)
        await domain[1].append_requirement(
            principal, case.run["id"], "用户在生成期间修改了要求", meta("during-generation", 1)
        )
        return result

    understanding.intent.models.generate = change_then_return
    result = await understanding.intent.understand(understanding.request, understanding.ctx)
    assert result["kind"] == "stale" and result["failure"]["code"] == "intent_input_stale"
    with pytest.raises(StoreMissing):
        await domain[1].store.get(principal, "intent.frames", case.run["task_id"])


async def test_unchanged_understanding_does_not_bump_frame_or_events(
    understanding, case, domain, principal
):
    first = await understanding.intent.understand(understanding.request, understanding.ctx)
    assert first["kind"] == "ok", first
    before = (await domain[1].events.read(principal, case.run["conversation_id"], limit=100))[
        "snapshot_revision"
    ]
    case.responses[:] = [response(proposal(understanding.original["text"]))]
    ctx = understanding.ctx.model_copy(update={"attempt_id": "check-again"})
    result = await understanding.intent.understand(
        {**understanding.request, "expected_revision": 1}, ctx
    )
    assert result == first
    assert (await domain[1].events.read(principal, case.run["conversation_id"], limit=100))[
        "snapshot_revision"
    ] == before
    assert (
        len(case.requests) == 2
    )  # Both model attempts are accounted; only frame revision is reused.


async def test_permission_scope_material_and_stale_cas_fail_before_send(
    understanding, case, domain, principal
):
    ctx = understanding.ctx.model_copy(
        update={
            "scope": understanding.ctx.scope.model_copy(
                update={"capabilities": ("model.generate",)}
            )
        }
    )
    assert (await understanding.intent.understand(understanding.request, ctx))["kind"] == "denied"
    material = {"kind": "blob", "id": "missing-material", "version": "1"}
    assert (
        await understanding.intent.understand(
            {**understanding.request, "material_refs": [material]}, understanding.ctx
        )
    )["failure"]["code"] == "capability_unavailable"
    assert (
        await understanding.intent.understand(
            {**understanding.request, "expected_revision": 9}, understanding.ctx
        )
    )["kind"] == "conflict"
    other = Principal(id="unrelated-user", kind="user", auth_session_id="unrelated-session")
    other_ctx = understanding.ctx.model_copy(
        update={
            "principal": other,
            "scope": understanding.ctx.scope.model_copy(update={"principal_id": other.id}),
        }
    )
    assert (await understanding.intent.understand(understanding.request, other_ctx))[
        "kind"
    ] == "missing"
    with pytest.raises(DomainError):
        await domain[1].append_requirement(
            principal.model_copy(update={"kind": "service"}),
            case.run["id"],
            "agent fabricated user update",
            meta("bad-patch", 1),
        )
    assert not case.requests


async def test_cancel_after_model_result_prevents_frame_publication(
    understanding, case, domain, principal
):
    original_generate = case.model.generate

    async def cancel_then_return(request, ctx):
        result = await original_generate(request, ctx)
        run = await domain[1].get_run(principal, case.run["id"])
        await domain[1].control(
            principal,
            {
                "run_id": run["id"],
                "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop understanding"},
            },
            meta("stop-understanding", run["revision"]),
        )
        return result

    understanding.intent.models.generate = cancel_then_return
    result = await understanding.intent.understand(understanding.request, understanding.ctx)
    assert result["kind"] == "cancelled"
    with pytest.raises(StoreMissing):
        await domain[1].store.get(principal, "intent.frames", case.run["task_id"])


async def test_http_frame_reads_current_owned_output_and_auth(
    understanding, case, domain, principal
):
    first = await understanding.intent.understand(understanding.request, understanding.ctx)
    assert first["kind"] == "ok", first
    settings = Settings(
        profile="development",
        development_principal_id=principal.id,
        development_user_token=SecretStr("frame-test-token-" + "t" * 32),
        cursor_signing_key=SecretStr("k" * 40),
    )
    container = Container(
        settings=settings,
        bindings=RuntimeBindings(),
        records=domain[1].store,
        configuration=domain[0],
        run_service=domain[1],
        intent_service=understanding.intent,
    )
    app = create_app(container)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        url = f"/v1/tasks/{case.run['task_id']}/frame"
        assert (await client.get(url)).status_code == 401
        actual = await client.get(
            url,
            headers={
                "Authorization": "Bearer " + settings.development_user_token.get_secret_value()
            },
        )
        assert actual.status_code == 200 and actual.json()["payload"] == first["payload"]
        assert (await client.get("/openapi.json")).json()["paths"]["/v1/tasks/{task_id}/frame"][
            "get"
        ]["operationId"] == "tasks.frame"
    with pytest.raises(StoreMissing):
        await understanding.intent.frames.current(
            Principal(id="other-owner", kind="user", auth_session_id="s"), case.run["task_id"]
        )


async def test_parallel_same_request_only_one_model_call_and_commit(understanding, case):
    results = await asyncio.gather(
        understanding.intent.understand(understanding.request, understanding.ctx),
        understanding.intent.understand(understanding.request, understanding.ctx),
    )
    success = [result for result in results if result["kind"] == "ok"]
    assert success and len(case.requests) == 1
    assert (
        await understanding.intent.understand(understanding.request, understanding.ctx)
        == success[0]
    )


async def test_legacy_run_requires_new_turn_without_silent_backfill(
    understanding, case, domain, principal
):
    store = domain[1].store
    await store.delete(
        principal,
        "run.input_sets",
        case.run["id"],
        expected_revision=1,
        request_id="legacy-run-fixture",
    )
    result = await understanding.intent.understand(understanding.request, understanding.ctx)
    assert result["failure"]["code"] == "intent_input_set_unavailable"
    assert (await domain[1].get_run(principal, case.run["id"]))["id"] == case.run["id"]
    with pytest.raises(DomainError) as rejected:
        await domain[1].append_requirement(
            principal, case.run["id"], "new requirement", meta("legacy-patch", 1)
        )
    assert rejected.value.failure.code == "intent_input_set_unavailable"
    assert not case.requests


async def test_expired_run_rejects_understanding_and_requirement_updates(
    understanding, case, domain, principal
):
    store = domain[1].store
    run = await store.get(principal, "runs", case.run["id"])
    await store.put(
        principal,
        "runs",
        run.resource_id,
        "RunRecord",
        {
            **run.payload,
            "revision": run.revision + 1,
            "budget": {**run.payload["budget"], "deadline": "2000-01-01T00:00:00Z"},
        },
        expected_revision=run.revision,
        request_id="expired-run-fixture",
    )
    result = await understanding.intent.understand(understanding.request, understanding.ctx)
    assert result["failure"]["code"] == "intent_deadline_expired"
    with pytest.raises(DomainError) as rejected:
        await domain[1].append_requirement(
            principal, case.run["id"], "new requirement", meta("expired-patch", 1)
        )
    assert rejected.value.failure.code == "intent_deadline_expired"
    assert not case.requests
