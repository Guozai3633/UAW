"""Actual batch reads and SQL current revocation, including awaits at the last pass."""

from __future__ import annotations

import asyncio
from collections import Counter
from datetime import UTC, datetime, timedelta

import pytest

from tests.integration.context.test_assessment_chain_postgres import wire
from tests.integration.context.test_assessment_postgres import setup
from tests.integration.context.test_registered_postgres import case as case
from tests.integration.context.test_registered_postgres import domain as domain
from tests.integration.context.test_registered_postgres import registration as registration
from tests.integration.context.test_registered_postgres import understanding as understanding
from uaw.context.registered import TOOLS, recipe_id
from uaw.shared.errors import DomainError


@pytest.mark.parametrize("change", ["blob", "cancel", "tools"])
async def test_sql_last_pass_rechecks_actual_bytes_and_current_state(registration, change):
    s = registration
    mat, _, _, _, _, _ = await setup(s)
    inputs, _, _, _, _ = wire(s)
    actual_get = inputs.blobs.get
    calls = Counter()

    async def changing(principal, content_hash):
        calls[content_hash] += 1
        if content_hash == mat.content_hash and calls[content_hash] == 2:
            if change == "blob":
                path = inputs.blobs._path(principal, content_hash)
                assert path.is_relative_to(s.blob_directory.resolve())
                await asyncio.to_thread(path.write_bytes, b"changed actual fixture blob")
            else:
                namespace, identifier = (
                    ("budget.ledgers", s.ctx.run_id)
                    if change == "cancel"
                    else (TOOLS, recipe_id(s.ctx))
                )
                row = await s.records.get(principal, namespace, identifier)
                payload = dict(row.payload)
                if change == "cancel":
                    payload["cancel_requested"] = True
                await s.records.put(
                    principal,
                    namespace,
                    identifier,
                    row.schema_name,
                    payload,
                    expected_revision=row.revision,
                    request_id=f"last-pass-{change}",
                )
        return await actual_get(principal, content_hash)

    inputs.blobs.get = changing
    with pytest.raises(DomainError) as caught:
        await inputs.inspect(s.ctx)
    assert (
        caught.value.failure.code
        == {"blob": "source_changed", "cancel": "cancelled", "tools": "source_changed"}[change]
    )


@pytest.mark.parametrize("mode", ["deadline", "task-cancel"])
async def test_sql_batch_stalled_real_reader_is_bounded(registration, mode):
    s = registration
    mat, _, _, _, _, _ = await setup(s)
    inputs, _, _, _, _ = wire(s)
    actual_get = inputs.blobs.get
    started = asyncio.Event()

    async def stalled(principal, content_hash):
        if content_hash == mat.content_hash:
            started.set()
            await asyncio.Event().wait()
        return await actual_get(principal, content_hash)

    inputs.blobs.get = stalled
    ctx = (
        s.ctx.model_copy(
            update={"deadline": (datetime.now(UTC) + timedelta(seconds=3)).isoformat()}
        )
        if mode == "deadline"
        else s.ctx
    )
    task = asyncio.create_task(inputs.inspect(ctx))
    await asyncio.wait_for(started.wait(), 20)
    if mode == "task-cancel":
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    else:
        with pytest.raises(DomainError) as caught:
            await task
        assert caught.value.failure.code == "deadline_exceeded"
