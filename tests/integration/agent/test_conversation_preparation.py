"""A-side same-Run input preparation; deliberately does not wake or send a call."""

import json

import pytest

from tests.integration.agent.test_conversation_controls import (
    answer,
    ask,
    control_meta,
)
from tests.integration.agent.test_conversation_controls import (
    case as case,
)
from tests.integration.agent.test_conversation_controls import (
    domain as domain,
)
from tests.integration.agent.test_conversation_controls import (
    scenario as scenario,
)
from tests.integration.agent.test_conversation_postgres import inventory
from tests.integration.test_control_plane import meta
from uaw.run.conversation_entry import source_frame
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import DomainError

pytestmark = pytest.mark.parametrize(
    "case", [{"active_provider_for_tools": True, "json_object_mode": True}], indirect=True
)


async def prepared(p):
    control, view = await ask(p)
    old = await p.runs.store.get(p.actor, "intent.frames", p.run["task_id"])
    receipt = await control.answer(
        p.actor,
        answer(view, "The second option, with the original terminology."),
        control_meta(view),
    )
    current = await p.runs.get_run(p.actor, p.run["id"])
    await p.runs.advance(
        p.actor, p.run["id"], "preparing", meta("prepare-new-input", current["revision"])
    )
    ctx = p.driver.step_context(
        TrustedExecutionContext.model_validate_json(json.dumps(p.job["context"])), 2
    )
    frame_ref = await source_frame(p.runs.store, ctx)
    return control, view, receipt, old, ctx, frame_ref


async def test_new_input_frame_is_versioned_idempotent_and_old_source_is_preserved(scenario):
    p = scenario
    control, view, receipt, old, ctx, frame_ref = await prepared(p)
    assert frame_ref["id"] == old.resource_id and int(frame_ref["version"]) == old.revision + 1
    assert (
        await p.runs.store.get(p.actor, "intent.frames", old.resource_id, revision=old.revision)
    ) == old
    current = await p.runs.store.get(p.actor, "intent.frames", old.resource_id)
    assert current.payload["original_input_ref"] == old.payload["original_input_ref"]
    assert current.payload["patch_refs"][-1] == receipt.patch.input_ref.wire()
    assert current.payload["input_revision"] == 2 and "second option" in current.payload["goal"]
    assert await source_frame(p.runs.store, ctx) == frame_ref
    assert (
        await p.runs.store.get(p.actor, "intent.frames", old.resource_id)
    ).revision == current.revision
    assert (await control.lookup(p.actor, p.run["id"], "answer-1")).patch.state == "accepted"
    assert len(p.case.requests) == 1


async def test_next_context_contains_exact_question_and_answer_links_without_second_understanding(
    scenario,
):
    p = scenario
    control, view, receipt, old, ctx, frame_ref = await prepared(p)
    loop = p.driver.agent.runtime.loop
    context = await loop.contexts.prepare("continuation-preparation-2", (), ctx)
    prompt = await loop.contexts.resolve(context.snapshot_ref.wire(), ctx)
    data = json.loads(prompt.messages[1]["content"])
    assert len(data["clarifications"]) == 1
    clarification = data["clarifications"][0]
    assert clarification["question"] == view.question.question.prompt.wire()
    assert clarification["answer_input_ref"] == receipt.patch.input_ref.wire()
    assert clarification["question_item_ref"]["id"] == view.question.question.item_id
    assert data["inputs"][0]["id"] == old.payload["original_input_ref"]["id"]
    assert data["inputs"][-1]["text"] == "The second option, with the original terminology."
    assert (await control.lookup(p.actor, p.run["id"], "answer-1")).patch.state == "accepted"
    assert len(p.case.requests) == 1
    assert not [
        value for value in await inventory(p, "model.invocations") if value["id"] == ctx.attempt_id
    ]


async def test_changed_question_after_snapshot_is_rejected_before_model_input(scenario):
    p = scenario
    _, view, _, _, ctx, _ = await prepared(p)
    loop = p.driver.agent.runtime.loop
    context = await loop.contexts.prepare("continuation-stale-question", (), ctx)
    row = await p.runs.store.get(
        p.actor, "run.clarification_questions", view.question.question.item_id
    )
    changed = {
        **row.payload,
        "revision": row.revision + 1,
        "prompt": {**row.payload["prompt"], "text": "Altered question"},
    }
    await p.runs.store.put(
        p.actor,
        row.namespace,
        row.resource_id,
        row.schema_name,
        changed,
        expected_revision=row.revision,
        request_id="alter-question",
    )
    with pytest.raises(DomainError) as stale:
        await loop.contexts.resolve(context.snapshot_ref.wire(), ctx)
    assert stale.value.status_code == 412
    assert len(p.case.requests) == 1
