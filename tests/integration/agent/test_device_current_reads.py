"""Real SQL device read/expiry semantics with a controlled channel source."""

import asyncio
import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import event

from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.test_runner_control import case as case
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.run.runner_devices import DEVICES, RunnerDevices
from uaw.shared.errors import DomainError
from uaw.shared.stores import StoreConflict


async def test_same_device_source_without_active_write_lock(case, monkeypatch, tmp_path):
    devices = case.devices
    source = devices.source
    counts = {"records": 0, "locks": 0, "source": 0}
    owner = asyncio.current_task()

    def sql(conn, cursor, statement, parameters, context, many):
        if asyncio.current_task() is owner and statement.lstrip().upper().startswith("SELECT"):
            counts["records"] += int("uaw_records" in statement)
            counts["locks"] += int("pg_advisory_xact_lock" in statement)

    async def measured(*args, **kwargs):
        counts["source"] += 1
        return await source(*args, **kwargs)

    monkeypatch.setattr(devices, "source", measured)
    engine = devices.store.database.engine.sync_engine
    event.listen(engine, "before_cursor_execute", sql)
    try:
        results, samples = [], {}
        for name in ("serialized", "fresh_read"):
            for field in counts:
                counts[field] = 0
            with monkeypatch.context() as scope:
                if name == "serialized":
                    scope.setattr(devices, "_current_binding", devices._load)
                results.append(
                    await devices.current(
                        case.device["device_id"], authenticated_principal=case.actor
                    )
                )
            samples[name] = dict(counts)
        assert results[0] == results[1] == case.device
        assert samples["serialized"]["locks"] == 2 and samples["fresh_read"]["locks"] == 0
        assert samples["serialized"]["records"] == samples["fresh_read"]["records"] == 2
        assert samples["serialized"]["source"] == samples["fresh_read"]["source"] == 1
        (tmp_path / "device-read-measurement.json").write_text(
            json.dumps(samples), encoding="utf-8"
        )
    finally:
        event.remove(engine, "before_cursor_execute", sql)


@pytest.mark.parametrize("change", ["revoke", "delete", "expiry", "mutate_result"])
async def test_actual_channel_await_keeps_second_read_and_expiry_sealing(case, monkeypatch, change):
    devices, source = case.devices, case.devices.source
    identifier = case.device["device_id"]
    original_clock = devices.clock

    async def changed(*args, **kwargs):
        result = await source(*args, **kwargs)
        if change == "revoke":
            await devices.revoke(
                identifier, 1, meta("read-await-revoke"), authenticated_service=case.controller
            )
        elif change == "delete":
            await devices.store.delete(
                case.controller,
                DEVICES,
                identifier,
                expected_revision=1,
                request_id="read-await-delete",
            )
        elif change == "expiry":
            later = datetime.now(UTC) + timedelta(hours=1)
            devices.clock = lambda: later
        else:
            result["owner"]["auth_session_id"] = "mutated-channel-result"
        return result

    monkeypatch.setattr(devices, "source", changed)
    with pytest.raises(DomainError):
        await devices.current(identifier, authenticated_principal=case.actor)
    if change == "expiry":
        sealed = await devices.store.get(case.controller, DEVICES, identifier)
        assert sealed.payload["state"] == "expired" and sealed.revision == 2
        devices.clock = original_clock
        with pytest.raises(DomainError):
            await devices.current(identifier, authenticated_principal=case.actor)


async def test_active_current_reads_remain_in_outer_witness(case):
    devices = case.devices
    with pytest.raises(StoreConflict):
        async with devices.store.current_witness():
            result = await devices.current(
                case.device["device_id"], authenticated_principal=case.actor
            )
            assert result == case.device
            await devices.revoke(
                case.device["device_id"],
                1,
                meta("witness-device-revoke"),
                authenticated_service=case.controller,
            )


async def test_active_observations_are_detached_and_not_reused(case):
    result = await case.devices.current(
        case.device["device_id"], authenticated_principal=case.actor
    )
    result["source"]["owner"]["auth_session_id"] = "detached-changed"
    assert (
        await case.devices.current(case.device["device_id"], authenticated_principal=case.actor)
        == case.device
    )


async def test_custom_store_retains_original_serialized_source(case, monkeypatch):
    class CustomRecords(PostgresRecordStore):
        pass

    devices = RunnerDevices(
        CustomRecords(case.devices.store.database), case.controller, case.channel
    )
    operation = devices._load
    calls = 0

    async def measured(*args, **kwargs):
        nonlocal calls
        calls += 1
        return await operation(*args, **kwargs)

    monkeypatch.setattr(devices, "_load", measured)
    assert (
        await devices.current(case.device["device_id"], authenticated_principal=case.actor)
        == case.device
    )
    assert calls == 2
