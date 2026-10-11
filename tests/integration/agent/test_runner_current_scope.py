"""Actual SQL visibility across authority awaits, with controlled channel/consent."""

import asyncio

import pytest

from tests.integration.test_control_plane import meta
from tests.integration.test_runner_control import case as case
from uaw.infrastructure.db.transactions import reference
from uaw.shared.errors import DomainError


@pytest.mark.parametrize("change", ["none", "model", "command", "cancel"])
async def test_current_scope_reuses_connection_without_hiding_external_change(case, change):
    await case.dispatch()
    record = await case.register()
    store = case.commands.store
    sessions = []
    original = case.signer.verify
    changed = False

    async def external_change():
        # The child task must not inherit the parent's SQLAlchemy session.
        async with store.current_reads():
            assert store._current_reads.get()[1] is not sessions[0]
            if change == "model":
                row = await store.get(case.ctx.principal, "run.bindings", case.ctx.run_id)
                await store.put(
                    case.ctx.principal,
                    row.namespace,
                    row.resource_id,
                    row.schema_name,
                    {**row.payload, "model_policy_ref": reference("policy", "changed-model")},
                    expected_revision=row.revision,
                    request_id="scope-model-change",
                )
            elif change == "command":
                await case.commands.revoke(
                    "command-one", 1, meta("scope-revoke"), authenticated_service=case.controller
                )
            elif change == "cancel":
                await case.domain[1].control(
                    case.ctx.principal,
                    {
                        "run_id": case.ctx.run_id,
                        "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop"},
                    },
                    meta("scope-cancel", 2),
                )

    async def verify(command, *, device_id):
        nonlocal changed
        sessions.append(store._current_reads.get()[1])
        await original(command, device_id=device_id)
        if not changed:
            changed = True
            await asyncio.create_task(external_change())

    case.signer.verify = verify
    if change == "none":
        await case.authority().current(record["command"], authenticated_principal=case.actor)
        assert len(sessions) == 2
    else:
        with pytest.raises(DomainError):
            await case.authority().current(record["command"], authenticated_principal=case.actor)
    assert sessions and all(session is sessions[0] for session in sessions)
    assert store._current_reads.get() is None
