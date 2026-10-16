"""Real SQL atomic acceptance; these tests do not claim queued continuation."""

import asyncio
import json

import httpx
import pytest

from tests.integration.agent.test_conversation_postgres import (
    case as case,
)
from tests.integration.agent.test_conversation_postgres import (
    domain as domain,
)
from tests.integration.agent.test_conversation_postgres import (
    inventory,
    output,
)
from tests.integration.agent.test_conversation_postgres import (
    scenario as scenario,
)
from tests.integration.test_control_plane import meta
from uaw.api.application import create_app
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.conversation_control import PATCHES, ConversationControls
from uaw.run.jobs import JOBS
from uaw.shared.contracts import Principal
from uaw.shared.conversation import (
    ConversationRequestMeta,
    RunClarificationAnswerRequest,
    RunCorrectionRequest,
)
from uaw.shared.errors import DomainError

pytestmark = pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)


async def ask(p):
    p.case.responses[:] = [
        output(
            {
                "protocol": "conversation-v1",
                "action": "ask",
                "question": {
                    "text": "Please paste the material.",
                    "reason": "Its original text is required.",
                    "options": [],
                },
            }
        )
    ]
    assert await p.queue.tick()
    control = ConversationControls(p.runs.store)
    view = await control.view(p.actor, p.run["id"])
    assert view.question is not None
    return control, view


def answer(view, text="材料：原样  保留\n换行"):
    return RunClarificationAnswerRequest(
        run_id=view.run["id"],
        question_item_id=view.question.question.item_id,
        expected_question_revision=view.question.question.revision,
        expected_input_revision=view.input_revision,
        text=text,
        attachment_refs=(),
    )


def control_meta(view, request_id="answer-1"):
    return ConversationRequestMeta(
        request_id=request_id, schema_version="0.2", expected_revision=view.run["revision"]
    )


async def test_same_run_answer_is_atomic_immutable_idempotent_and_only_accepted(scenario):
    p = scenario
    control, view = await ask(p)
    request, request_meta = answer(view), control_meta(view)
    original = await inventory(p, "inputs")
    clock = (await p.runs.store.get(p.actor, "run.execution_clocks", p.run["id"])).payload
    job = (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload
    receipt = await control.answer(p.actor, request, request_meta)
    assert receipt.run["id"] == p.run["id"] and receipt.patch.state == "accepted"
    assert receipt.patch.input_revision == 2 and receipt.run["status"] == "waiting_for_user"
    current = await control.view(p.actor, p.run["id"])
    assert current.question is None and current.continuation_request_ids == ("answer-1",)
    assert (
        await control.question(p.actor, p.run["id"], request.question_item_id)
    ).question.state == "answered"
    stored = (await p.runs.store.get(p.actor, "inputs", receipt.patch.input_ref.id)).payload
    assert stored["text"] == request.text
    assert len(await inventory(p, "inputs")) == len(original) + 1
    for previous in original:
        assert (await p.runs.store.get(p.actor, "inputs", previous["id"])).payload == previous
    assert (await control.answer(p.actor, request, request_meta)).wire() == receipt.wire()
    assert len(await inventory(p, PATCHES)) == 1
    assert (await p.runs.store.get(p.actor, "run.execution_clocks", p.run["id"])).payload == clock
    assert (await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload == job
    assert len(p.case.requests) == 1
    with pytest.raises(DomainError) as conflict:
        await control.answer(
            p.actor, request.model_copy(update={"text": "different"}), request_meta
        )
    assert conflict.value.status_code == 409


async def test_two_pages_answer_cas_has_one_winner_and_refresh_reads_original(scenario):
    p = scenario
    control, view = await ask(p)
    results = await asyncio.gather(
        *[
            control.answer(p.actor, answer(view), control_meta(view, key))
            for key in ("page-a", "page-b")
        ],
        return_exceptions=True,
    )
    success = [value for value in results if not isinstance(value, Exception)]
    assert len(success) == 1
    assert len(await inventory(p, PATCHES)) == 1
    restarted = ConversationControls(p.runs.store)
    assert (
        await restarted.lookup(p.actor, p.run["id"], success[0].patch.request_id)
    ).wire() == success[0].wire()


async def test_cancelled_run_replay_reads_receipt_but_new_answer_cannot_revive(scenario):
    p = scenario
    control, view = await ask(p)
    request, request_meta = answer(view), control_meta(view)
    receipt = await control.answer(p.actor, request, request_meta)
    current = await p.runs.get_run(p.actor, p.run["id"])
    await p.runs.control(
        p.actor,
        {
            "run_id": p.run["id"],
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "test cancel"},
        },
        meta("cancel", current["revision"]),
    )
    await p.driver.finalize((await p.runs.store.get(p.actor, JOBS, p.run["id"])).payload)
    replay = await control.answer(p.actor, request, request_meta)
    assert replay.run["status"] == "cancelled" and replay.patch.state == "cancelled"
    assert replay.patch.input_ref == receipt.patch.input_ref
    with pytest.raises(DomainError) as denied:
        await control.correct(
            p.actor,
            RunCorrectionRequest(
                run_id=p.run["id"], expected_input_revision=2, text="continue", attachment_refs=()
            ),
            ConversationRequestMeta(
                request_id="after-cancel",
                schema_version="0.2",
                expected_revision=replay.run["revision"],
            ),
        )
    assert denied.value.status_code == 409
    assert len(await inventory(p, PATCHES)) == 1


async def test_control_transaction_failure_rolls_back_input_question_patch_and_outbox(
    scenario, monkeypatch
):
    p = scenario
    control, view = await ask(p)
    before = {
        name: await inventory(p, name)
        for name in (
            "inputs",
            "items",
            "run.input_sets",
            "run.protocol_bindings",
            "run.clarification_questions",
            PATCHES,
            "events",
        )
    }
    from uaw.infrastructure.db.transactions import RecordTransaction

    original = RecordTransaction.write

    async def fail(self, namespace, *args, **kwargs):
        if namespace == "run.continuation.receipts":
            raise RuntimeError("injected commit preparation failure")
        return await original(self, namespace, *args, **kwargs)

    monkeypatch.setattr(RecordTransaction, "write", fail)
    with pytest.raises(RuntimeError):
        await control.answer(p.actor, answer(view), control_meta(view))
    for name, values in before.items():
        assert await inventory(p, name) == values


async def test_correction_invalidates_old_frame_and_is_not_a_new_task(scenario):
    p = scenario
    control = ConversationControls(p.runs.store)
    view = await control.view(p.actor, p.run["id"])
    request = RunCorrectionRequest(
        run_id=p.run["id"],
        expected_input_revision=1,
        text="Keep the original evidence; change only the audience.",
        attachment_refs=(),
    )
    runs_before = await inventory(p, "runs")
    receipt = await control.correct(p.actor, request, control_meta(view, "correct-1"))
    assert receipt.patch.kind == "correction" and receipt.patch.state == "accepted"
    assert receipt.run["id"] == p.run["id"] and receipt.run["task_id"] == p.run["task_id"]
    assert "frame_ref" not in receipt.run
    assert {v["id"] for v in await inventory(p, "runs")} == {v["id"] for v in runs_before}
    assert (await p.runs.store.get(p.actor, "run.protocol_bindings", p.run["id"])).payload[
        "input_revision"
    ] == 2
    assert not p.case.requests


async def test_old_protocol_and_foreign_actor_do_not_get_control_source(scenario):
    p = scenario
    control = ConversationControls(p.runs.store)
    with pytest.raises(DomainError):
        await control.view(
            Principal(id="foreign-user", kind="user", auth_session_id="foreign"), p.run["id"]
        )
    from sqlalchemy import delete

    from uaw.infrastructure.db.models import RecordRow

    async with p.runs.store.database.sessions.begin() as sql:
        await sql.execute(
            delete(RecordRow).where(
                RecordRow.principal_id == p.actor.id,
                RecordRow.namespace == "run.protocol_bindings",
                RecordRow.resource_id == p.run["id"],
            )
        )
    with pytest.raises(DomainError) as unavailable:
        await control.view(p.actor, p.run["id"])
    assert unavailable.value.status_code == 503


async def test_real_idle_inventory_allows_known_pending_money_and_rejects_live_reservations(
    scenario,
):
    p = scenario
    control, _ = await ask(p)

    async def check(tx):
        await RunIdleEffects().check(tx, p.actor, p.run["id"])
        return {}

    await control.transactions.inspect(p.actor, "conversation:" + p.run["conversation_id"], check)
    row = await p.runs.store.get(p.actor, "budget.ledgers", p.run["id"])
    ledger = {
        **row.payload,
        "revision": row.revision + 1,
        "held": {**row.payload["held"], "model_calls": 1},
    }
    await p.runs.store.put(
        p.actor,
        row.namespace,
        row.resource_id,
        row.schema_name,
        ledger,
        expected_revision=row.revision,
        request_id="inject-live-hold",
    )
    with pytest.raises(DomainError) as pending:
        await control.transactions.inspect(
            p.actor, "conversation:" + p.run["conversation_id"], check
        )
    assert pending.value.failure.code == "conversation_effect_pending"


async def test_cli_http_contract_auth_versions_and_original_request_lookup(scenario):
    p = scenario
    _, view = await ask(p)
    app = create_app(p.control)
    headers = {"Authorization": "Bearer " + "u" * 40}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8000"
    ) as client:
        url = f"/v1/runs/{p.run['id']}/conversation"
        assert (await client.get(url)).status_code == 401
        response = await client.get(url, headers={**headers, "X-UAW-Schema-Version": "0.2"})
        assert response.status_code == 200, response.json()
        assert (
            await client.get(url, headers={**headers, "X-UAW-Schema-Version": "0.1"})
        ).status_code == 422
        assert (await client.get(url + "?run_id=another", headers=headers)).status_code == 422
        assert (
            await client.get("/v1/runs/invalid%20id/conversation", headers=headers)
        ).status_code == 422
        target = f"/v1/runs/{p.run['id']}/clarifications/{view.question.question.item_id}/answers"
        payload = answer(view).wire()
        payload.pop("run_id")
        payload.pop("question_item_id")
        request = {"meta": control_meta(view).wire(), "payload": payload}
        wrong = json.loads(json.dumps(request))
        wrong["meta"]["schema_version"] = "0.1"
        assert (await client.post(target, headers=headers, json=wrong)).status_code == 422
        result = await client.post(target, headers=headers, json=request)
        assert result.status_code == 200, result.json()
        assert result.json()["payload"]["patch"]["state"] == "accepted"
        found = await client.get(f"/v1/runs/{p.run['id']}/continuations/answer-1", headers=headers)
        assert found.json() == result.json()
        duplicated = {**request, "payload": {**payload, "run_id": p.run["id"]}}
        assert (await client.post(target, headers=headers, json=duplicated)).status_code == 422
        document = (await client.get("/openapi.json")).json()
        assert document["paths"][
            target.replace(p.run["id"], "{run_id}").replace(
                view.question.question.item_id, "{question_item_id}"
            )
        ]["post"]["requestBody"]["content"]["application/json"]["schema"]["properties"]["meta"][
            "$ref"
        ].endswith("ConversationRequestMeta")


async def test_cookie_control_requires_exact_origin_csrf_and_logout_revokes_access(scenario):
    from pydantic import SecretStr

    from tests.integration.test_browser_sessions import ORIGIN, login
    from uaw.api.browser import BrowserSessions

    p = scenario
    _, view = await ask(p)
    p.control.settings = p.control.settings.model_copy(
        update={
            "browser_origin": ORIGIN,
            "browser_session_signing_key": SecretStr("b" * 40),
            "platform_id": p.control.configuration.platform.id,
        }
    )
    p.control.browser_sessions = BrowserSessions(p.runs.store, p.control.settings)
    app = create_app(p.control)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8000"
    ) as client:
        public = await login(client)
        target = f"/v1/runs/{p.run['id']}/clarifications/{view.question.question.item_id}/answers"
        payload = answer(view).wire()
        payload.pop("run_id")
        payload.pop("question_item_id")
        body = {"meta": control_meta(view).wire(), "payload": payload}
        assert (await client.post(target, headers={"Origin": ORIGIN}, json=body)).status_code == 403
        assert (
            await client.post(
                target,
                headers={"Origin": "http://other.invalid", "X-UAW-CSRF": public["csrf_token"]},
                json=body,
            )
        ).status_code == 403
        accepted = await client.post(
            target, headers={"Origin": ORIGIN, "X-UAW-CSRF": public["csrf_token"]}, json=body
        )
        assert accepted.status_code == 200, accepted.json()
        from uaw.api.browser import COOKIE

        old_cookie = client.cookies.get(COOKIE)
        logout = await client.request(
            "DELETE",
            "/v1/web/session",
            headers={"Origin": ORIGIN, "X-UAW-CSRF": public["csrf_token"]},
            json={
                "meta": {"request_id": "logout-controls", "schema_version": "0.1"},
                "payload": {},
            },
        )
        assert logout.status_code == 200
        from uaw.api.browser import COOKIE

        client.cookies.set(COOKIE, old_cookie)
        assert (
            await client.get(f"/v1/runs/{p.run['id']}/conversation", headers={"Origin": ORIGIN})
        ).status_code == 401


async def test_idle_cannot_treat_a_claimed_original_model_as_free_wait(scenario):
    p = scenario
    control, _ = await ask(p)
    invocation = next(
        value for value in await inventory(p, "model.invocations") if value["run_id"] == p.run["id"]
    )
    row = await p.runs.store.get(p.actor, "model.invocations", invocation["id"])
    value = {**row.payload, "state": "claimed"}
    value.pop("result", None)
    await p.runs.store.put(
        p.actor,
        row.namespace,
        row.resource_id,
        row.schema_name,
        value,
        expected_revision=row.revision,
        request_id="unknown-model-effect",
    )

    async def check(tx):
        await RunIdleEffects().check(tx, p.actor, p.run["id"])
        return {}

    with pytest.raises(DomainError) as pending:
        await control.transactions.inspect(
            p.actor, "conversation:" + p.run["conversation_id"], check
        )
    assert pending.value.failure.code == "conversation_effect_pending"
    assert len(p.case.requests) == 1


async def test_oversized_or_unavailable_attachments_do_not_append_partial_input(scenario):
    p = scenario
    control, view = await ask(p)
    inputs = await inventory(p, "inputs")
    from uaw.shared.contracts import Ref

    with pytest.raises(DomainError) as missing:
        await control.answer(
            p.actor,
            answer(view).model_copy(
                update={"attachment_refs": (Ref(kind="input", id="not-authorized", version="1"),)}
            ),
            control_meta(view),
        )
    assert missing.value.status_code == 503
    with pytest.raises(DomainError) as too_large:
        await control.answer(p.actor, answer(view, "😀" * 16384), control_meta(view))
    assert too_large.value.status_code == 413
    assert await inventory(p, "inputs") == inputs
    assert not await inventory(p, PATCHES)
