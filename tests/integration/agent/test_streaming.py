"""Real SQL stream lifecycle with controlled provider bytes, no actual LLM/human labels."""

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from tests.integration.agent.test_conversation_postgres import case as case
from tests.integration.agent.test_conversation_postgres import domain as domain
from tests.integration.agent.test_conversation_postgres import inventory
from tests.integration.agent.test_conversation_postgres import scenario as scenario
from tests.integration.test_control_plane import meta
from tests.unit.model.test_streaming import frame
from uaw.run.events import EventReader
from uaw.run.streaming import NAMESPACE, ConversationStreams
from uaw.shared.errors import DomainError

pytestmark = pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)


class PausedReply(httpx.AsyncByteStream):
    def __init__(self, *, disconnected=False):
        self.paused, self.release = asyncio.Event(), asyncio.Event()
        self.disconnected = disconnected

    async def __aiter__(self):
        yield frame({"role": "assistant", "reasoning_content": "hidden internal fixture"})
        yield frame({"content": '{"protocol":"conversation-v1","action":"reply","text":"First '})
        self.paused.set()
        await self.release.wait()
        if self.disconnected:
            raise httpx.ReadError("Controlled provider interruption")
        yield frame({"content": 'second. "}'})
        yield frame({}, reason="stop", usage={"prompt_tokens": 100, "completion_tokens": 20})
        yield b"data: [DONE]\n\n"


async def start(p, *, disconnected=False):
    gateway = p.driver.agent.runtime.loop.models.model.gateway
    gateway.streams = ConversationStreams(p.runs.store)
    source = PausedReply(disconnected=disconnected)
    p.case.responses[:] = [
        httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=source)
    ]
    task = asyncio.create_task(p.queue.tick())
    try:
        await asyncio.wait_for(source.paused.wait(), timeout=20)
    except BaseException:
        source.release.set()
        if task.done():
            task.result()
            job = await p.runs.store.get(p.actor, "run.background.jobs", p.run["id"])
            pytest.fail(str(job.payload.get("failure", job.payload)))
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        raise
    return source, task


async def test_real_sql_partial_visible_before_final_same_item_replays_and_does_not_repeat_model(
    scenario,
):
    p = scenario
    source, task = await start(p)
    try:
        items = [v for v in await inventory(p, "items") if v["type"] == "agent_message"]
        assert (
            len(items) == 1 and items[0]["status"] == "in_progress" and items[0]["text"] == "First "
        )
        assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "running"
        reader = EventReader(p.runs.store, p.control.settings.cursor_signing_key)
        snapshot = await reader.read(p.actor, p.run["conversation_id"], items=True)
        assert next(v for v in snapshot["items"] if v["id"] == items[0]["id"])["text"] == "First "
        before = snapshot["snapshot_revision"]
    finally:
        source.release.set()
    assert await task
    final = [v for v in await inventory(p, "items") if v["type"] == "agent_message"]
    assert len(final) == 1 and final[0]["id"] == items[0]["id"]
    assert final[0]["status"] == "completed" and final[0]["text"] == "First second. "
    assert (
        final[0]["created_at"] == items[0]["created_at"]
        and final[0]["revision"] > items[0]["revision"]
    )
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "completed"
    stream = (await inventory(p, NAMESPACE))[0]
    assert stream["state"] == "published" and stream["input_revision"] == 1
    assert stream["first_provider_at"] <= stream["first_text_at"] <= stream["received_at"]
    events = await reader.read(p.actor, p.run["conversation_id"], after_seq=before)
    assert events["items"] and min(e["seq"] for e in events["items"]) > before
    assert len(p.case.requests) == 1 and json.loads(p.case.requests[0].content)["stream"]
    assert not await p.queue.tick() and len(p.case.requests) == 1
    assert not await inventory(p, "workspace.artifacts")


async def test_provider_disconnect_preserves_partial_and_unknown_without_success_or_resend(
    scenario,
):
    p = scenario
    source, task = await start(p, disconnected=True)
    source.release.set()
    assert await task
    stream = (await inventory(p, NAMESPACE))[0]
    assert stream["state"] == "interrupted" and stream["text"] == "First "
    assert stream["failure_code"] == "provider_transport_unknown"
    item = next(v for v in await inventory(p, "items") if v["id"] == stream["item_id"])
    assert item["status"] == "failed" and item["text"] == "First "
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] != "completed"
    attempt = (await inventory(p, "model.attempts"))[0]
    assert attempt["usage"]["billing_state"] == "pending" and attempt["response_ref"]
    assert not await p.queue.tick() and len(p.case.requests) == 1


@pytest.mark.parametrize("finish_race", [False, True])
async def test_cancel_during_stream_does_not_publish_success_and_preserves_billing(
    scenario, finish_race
):
    p = scenario
    source, task = await start(p)
    try:
        current = await p.runs.get_run(p.actor, p.run["id"])
        await p.runs.control(
            p.actor,
            {
                "run_id": current["id"],
                "control": {
                    "mode": "cancel",
                    "preserve_refs": [],
                    "reason": "Controlled stream cancel",
                },
            },
            meta("stream-cancel", current["revision"]),
        )
        if not finish_race:
            assert await asyncio.wait_for(asyncio.shield(task), timeout=20)
    finally:
        source.release.set()
    assert await task
    run = await p.runs.get_run(p.actor, p.run["id"])
    attempts = await inventory(p, "model.attempts")
    ledger = (await inventory(p, "budget.ledgers"))[0]
    assert ledger["cancel_requested"]
    if "input_tokens" in attempts[0]["usage"]["resources"]:
        assert run["status"] == "cancelled"
    else:
        # Missing provider usage remains reserved; never forge zero fees to force a terminal Run.
        assert run["status"] != "completed" and ledger["held"]["input_tokens"] > 0
        assert (await inventory(p, "run.background.jobs"))[0]["state"] == "blocked"
    stream = (await inventory(p, NAMESPACE))[0]
    assert stream["state"] == "interrupted" and stream["text"] == "First "
    assert not any(
        v["status"] == "completed" and v["id"] == stream["item_id"]
        for v in await inventory(p, "items")
    )
    assert attempts[0]["usage"]["billing_state"] == "pending"
    assert attempts[0]["response_ref"]  # The actual partial SSE survives cancellation.
    assert len(p.case.requests) == 1


async def test_incremental_event_cursor_binds_offset_and_owner(scenario):
    p = scenario
    reader = EventReader(p.runs.store, p.control.settings.cursor_signing_key)
    first = await reader.read(p.actor, p.run["conversation_id"], limit=1, after_seq=1)
    assert first["next_cursor"] and first["items"][0]["seq"] == 2
    second = await reader.read(
        p.actor, p.run["conversation_id"], limit=1, after_seq=1, cursor=first["next_cursor"]
    )
    assert second["items"][0]["seq"] == 3
    with pytest.raises(DomainError):
        await reader.read(
            p.actor, p.run["conversation_id"], after_seq=2, cursor=first["next_cursor"]
        )
    with pytest.raises(DomainError):
        await reader.read(p.actor, p.run["conversation_id"], after_seq=2**30)
    with pytest.raises(DomainError):
        await reader.read(p.actor, p.run["conversation_id"], items=True, after_seq=1)


async def test_late_original_publication_failure_closes_display_without_marking_success(
    scenario, monkeypatch
):
    from uaw.shared.errors import reject

    async def deny_original(*args):
        raise reject("original_publication_denied", "Controlled original final guard", 403)

    p = scenario
    monkeypatch.setattr("uaw.run.streaming.finish_item", deny_original)
    source, task = await start(p)
    source.release.set()
    assert await task
    stream = (await inventory(p, NAMESPACE))[0]
    assert (
        stream["state"] == "interrupted" and stream["failure_code"] == "original_publication_denied"
    )
    item = next(v for v in await inventory(p, "items") if v["id"] == stream["item_id"])
    assert item["status"] == "failed" and item["text"] == "First second. "
    assert (await p.runs.get_run(p.actor, p.run["id"]))["status"] == "failed"
    assert len(p.case.requests) == 1
    assert not await p.queue.tick() and len(p.case.requests) == 1


async def test_event_read_measurement_and_missing_owned_history_is_rejected(scenario):
    from sqlalchemy import event, update
    from uaw.infrastructure.db.models import RecordRow

    p = scenario
    reader = EventReader(p.runs.store, p.control.settings.cursor_signing_key)
    statements = []

    def capture(*args):
        statements.append(args[2])

    engine = p.runs.store.database.engine.sync_engine
    event.listen(engine, "before_cursor_execute", capture)
    try:
        page = await reader.read(p.actor, p.run["conversation_id"])
    finally:
        event.remove(engine, "before_cursor_execute", capture)
    path = Path(
        __import__("os").environ.get(
            "UAW_A18_EVENT_MEASUREMENT", "tests/.artifacts/A18/event-read.json"
        )
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "events": len(page["items"]),
                "sql_statements": len(statements),
                "statements": statements,
            }
        ),
        encoding="utf8",
    )
    assert len(page["items"]) >= 3
    async with p.runs.store.database.sessions.begin() as session:
        await session.execute(
            update(RecordRow)
            .where(
                RecordRow.principal_id == p.actor.id,
                RecordRow.namespace == "events",
                RecordRow.resource_id == page["items"][0]["event_id"],
            )
            .values(deleted=True)
        )
    with pytest.raises(DomainError) as failure:
        await reader.read(p.actor, p.run["conversation_id"])
    assert failure.value.failure.code == "snapshot_required"
