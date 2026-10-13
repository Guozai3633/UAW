"""Actual SQL metadata brackets: equivalent observations and late source denial."""

import asyncio
import json

import pytest
from sqlalchemy import event

from tests.integration.agent.test_installed_file_authority import (
    file_data_case as file_data_case,
)
from tests.integration.agent.test_installed_file_authority import (
    original_file_gate as original_file_gate,
)
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.tool.conftest import tool_case as tool_case
from uaw.shared.errors import DomainError
from uaw.shared.stores import StoreConflict


async def test_same_access_and_model_with_one_owning_permission_bracket(
    original_file_gate, tmp_path
):
    _, service, _, ctx, c = original_file_gate
    access = service.authority.access
    permissions = access.runs.permissions
    resolve = permissions.resolve
    owner = asyncio.current_task()
    counts = {"sql": 0, "permission": 0, "callback": 0}

    async def counted(*args, **kwargs):
        counts["permission"] += 1
        return await resolve(*args, **kwargs)

    def sql(conn, cursor, statement, parameters, context, many):
        if asyncio.current_task() is owner and statement.lstrip().upper().startswith("SELECT"):
            counts["sql"] += 1

    async def check(observed, sources):
        counts["callback"] += 1
        assert sources.admission["model_policy_ref"] == ctx.model_policy_ref.wire()
        assert observed.policy_ref == ctx.capability_policy_ref

    engine = access.store.database.engine.sync_engine
    event.listen(engine, "before_cursor_execute", sql)
    permissions.resolve = counted
    try:
        legacy = await access._snapshot(ctx, check=check)
        baseline = dict(counts)
        for name in counts:
            counts[name] = 0
        actual = await access.checked_snapshot(ctx, check=check)
        assert actual == legacy
        assert counts["permission"] == 2 and baseline["permission"] == 4
        assert counts["callback"] == baseline["callback"] == 1
        assert 0 < counts["sql"] < baseline["sql"]
        (tmp_path / "checked-run-measurement.json").write_text(
            json.dumps({"legacy": baseline, "outer": counts}), encoding="utf-8"
        )
    finally:
        permissions.resolve = resolve
        event.remove(engine, "before_cursor_execute", sql)


@pytest.mark.parametrize("source", ["role", "provider", "admission", "authentication"])
async def test_late_change_after_tool_close_still_rejected(original_file_gate, source):
    _, service, _, ctx, c = original_file_gate
    access = service.authority.access
    permissions = access.runs.permissions
    resolve = permissions.resolve
    authentication = permissions.authentication_check
    calls = 0

    async def changed(*args, **kwargs):
        nonlocal calls
        result = await resolve(*args, **kwargs)
        calls += 1
        if calls == 2:
            if source == "authentication":
                permissions.authentication_check = None
                if authentication is None:

                    async def unavailable(principal):
                        raise RuntimeError("Source replaced during metadata check")

                    permissions.authentication_check = unavailable
            elif source == "role":
                await access.revoke(
                    ctx,
                    meta("checked-late-role", 1),
                    authenticated_service=c.configuration.platform,
                )
            else:
                owner = c.configuration.platform if source == "provider" else ctx.principal
                namespace = "providers" if source == "provider" else "run.bindings"
                identifier = (
                    (await access.runs.data(ctx)).fixed_configuration["provider_refs"][0]["id"]
                    if source == "provider"
                    else ctx.run_id
                )
                row = await c.records.get(owner, namespace, identifier)
                await c.records.delete(
                    owner,
                    namespace,
                    identifier,
                    expected_revision=row.revision,
                    request_id="checked-late-" + source,
                )
        return result

    async def no_effect(observed, sources):
        return None

    permissions.resolve = changed
    try:
        with pytest.raises((DomainError, StoreConflict)):
            await access.checked_snapshot(ctx, check=no_effect)
        assert calls == 2
    finally:
        permissions.resolve = resolve
        permissions.authentication_check = authentication


async def test_checked_run_callback_cannot_replace_sources(original_file_gate):
    _, service, _, ctx, c = original_file_gate
    runs = service.authority.access.runs
    permissions = runs.permissions

    async def replace_source(snapshot):
        runs.permissions = object()

    try:
        with pytest.raises(DomainError):
            await runs.checked_current(ctx, check=replace_source)
    finally:
        runs.permissions = permissions


@pytest.mark.parametrize("source", ["run_port", "tool_settings"])
async def test_memory_source_change_during_final_witness_is_denied(
    original_file_gate, monkeypatch, source
):
    _, service, _, ctx, c = original_file_gate
    access = service.authority.access
    runs, store = access.runs, access.store
    permissions, flags = runs.permissions, access.implemented_flags
    witness = store._witness_rows

    async def changed(*args, **kwargs):
        result = await witness(*args, **kwargs)
        if source == "run_port":
            runs.permissions = object()
        else:
            access.implemented_flags = frozenset()
            if not flags:
                access.implemented_flags = frozenset({"changed-unavailable-flag"})
        return result

    async def no_effect(observed, sources):
        return None

    monkeypatch.setattr(store, "_witness_rows", changed)
    try:
        with pytest.raises(DomainError):
            await access.checked_snapshot(ctx, check=no_effect)
    finally:
        runs.permissions, access.implemented_flags = permissions, flags
