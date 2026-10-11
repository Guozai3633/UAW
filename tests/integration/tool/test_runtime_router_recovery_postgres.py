"""Additional original-ledger boundaries and actual independent-process recovery."""

import asyncio
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from tests.integration.tool.runtime_router_fixture import file_pipeline as file_pipeline
from tests.integration.tool.runtime_router_fixture import mixed_runtime as mixed_runtime
from tests.integration.tool.runtime_router_fixture import office_pipeline as office_pipeline
from tests.integration.tool.runtime_router_fixture import recover_mixed
from tests.integration.tool.test_durable import cancel
from tests.integration.tool.test_runtime_router_postgres import approve
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.tool.ledger import action_key
from uaw.tool.runtime_router import RoutedToolRuntime


async def test_actual_fresh_process_mixed_sql_journal_no_executor_or_reopen(mixed_runtime):
    m = mixed_runtime
    before_text = (m.file.root / "file.txt").read_bytes().decode("utf-8")
    execute = m.office.executor.execute

    async def office_lost(*args):
        await execute(*args)
        raise TimeoutError("Controlled office response loss")

    async def file_lost():
        raise TimeoutError("Controlled signed file journal response loss")

    m.office.executor.execute = office_lost
    m.file.bridge.after_journal = file_lost
    for p in (m.office, m.file):
        await approve(m.runtime, p)
        assert (await m.runtime.invoke(p.raw, p.case.ctx))["failure"][
            "code"
        ] == "invocation_interrupted"
    (m.file.root / "file.txt").unlink()
    await cancel(m.file.case)
    sources = [
        {
            "context": p.case.ctx.wire(),
            "request": p.raw,
            "provider": p.provider.wire(),
            "blob_directory": str(p.blob.directory),
        }
        for p in (m.office, m.file)
    ]
    sources[1]["public_keys"] = {
        "control": list(m.file.signatures.control.public_key().public_bytes_raw()),
        "device": list(m.file.signatures.device.public_key().public_bytes_raw()),
    }
    child = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-m", "tests.integration.tool.runtime_router_recovery_child"],
        input=json.dumps({"sources": sources}),
        text=True,
        capture_output=True,
        timeout=180,
        cwd=Path(__file__).parents[3],
    )
    assert child.returncode == 0, child.stdout + child.stderr
    result = json.loads(child.stdout)
    assert result["sends"] == result["opens"] == result["executors"] == 0
    assert [row["tool_ref"] for row in result["results"]] == [
        p.raw["tool_ref"] for p in (m.office, m.file)
    ]
    assert all(row["outcome"] == "applied" for row in result["results"])
    assert result["results"][1]["data"]["text"] == before_text
    assert m.office.executor.calls == m.file.bridge.calls == m.file.bridge.opens == 1


async def test_recorded_provider_change_rejected_before_any_owning_reader(mixed_runtime):
    m = mixed_runtime
    p = m.office
    await approve(m.runtime, p)
    assert (await m.runtime.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    row = await m.ledger.store.get(
        p.case.ctx.principal, "tool.specs", action_key(p.case.ctx, p.raw["action_id"])
    )
    changed = {
        **row.payload,
        "provider_ref": {**row.payload["provider_ref"], "version": "wrong-original-provider"},
    }
    await m.ledger.store.put(
        p.case.ctx.principal,
        "tool.specs",
        row.resource_id,
        "ToolSpec",
        changed,
        expected_revision=row.revision,
        request_id="controlled-router-spec-tamper",
    )
    owner = m.owners[p.kind]

    async def no_scan(*args):
        pytest.fail("A wrong original provider must never reach any owning Reader")

    owner.facade.read_outcome = no_scan
    owner.results.read_result = no_scan
    owner.facade.reconcile = no_scan
    assert (
        await m.runtime.reconcile(
            {"action_id": p.raw["action_id"], "expected_revision": 0}, p.case.ctx
        )
    )["failure"]["code"] == "runtime_binding_conflict"
    with pytest.raises(DomainError):
        await m.runtime.read_result(p.raw["action_id"], p.case.ctx)
    with pytest.raises(DomainError):
        await m.runtime.read_outcome(p.raw["action_id"], p.case.ctx)


async def test_missing_route_and_wrong_attempt_or_subject_never_probe_other_facade(mixed_runtime):
    m = mixed_runtime
    p = m.office
    await approve(m.runtime, p)
    assert (await m.runtime.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    only_file = RoutedToolRuntime(m.registry, m.ledger, (m.routes[1],), access=m.access)
    assert (
        await only_file.reconcile(
            {"action_id": p.raw["action_id"], "expected_revision": 0}, p.case.ctx
        )
    )["failure"]["code"] == "dependency_unavailable"
    with pytest.raises(DomainError):
        await only_file.read_result(p.raw["action_id"], p.case.ctx)
    for changed in (
        p.case.ctx.model_copy(update={"attempt_id": "wrong-attempt"}),
        p.case.ctx.model_copy(
            update={"principal": p.case.ctx.principal.model_copy(update={"id": "other-subject"})}
        ),
        m.file.case.ctx,
    ):
        assert (
            await m.runtime.reconcile(
                {"action_id": p.raw["action_id"], "expected_revision": 0}, changed
            )
        )["kind"] != "ok"
        with pytest.raises(DomainError):
            await m.runtime.read_outcome(p.raw["action_id"], changed)
    assert m.office.executor.calls == 1 and m.file.bridge.calls == 0


async def test_registration_hash_or_provider_replacement_rejects_original_recovery(mixed_runtime):
    m = mixed_runtime
    p = m.file
    await approve(m.runtime, p)
    assert (await m.runtime.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    entry = m.registry.get(p.raw["tool_ref"])
    m.registry.unregister(p.raw["tool_ref"], expected_revision=m.registry.revision)
    spec = {
        **entry.spec(),
        "description": "Changed specification",
        "provider_ref": {**entry.spec()["provider_ref"], "version": "different"},
    }
    m.registry.register(
        spec,
        expected_revision=m.registry.revision,
        binding=replace(entry.binding, provider_ref=Ref.model_validate(spec["provider_ref"])),
    )
    with pytest.raises(DomainError):
        await m.runtime.read_result(p.raw["action_id"], p.case.ctx)
    assert (
        await m.runtime.reconcile(
            {"action_id": p.raw["action_id"], "expected_revision": 0}, p.case.ctx
        )
    )["kind"] == "stale"
    assert p.bridge.calls == p.bridge.opens == 1


async def test_missing_lookup_and_data_reader_are_unavailable_not_false_success(mixed_runtime):
    m = mixed_runtime
    p = m.office
    await approve(m.runtime, p)
    assert (await m.runtime.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    m.owners[p.kind].facade.lookup = None
    result = await m.runtime.reconcile(
        {"action_id": p.raw["action_id"], "expected_revision": 0}, p.case.ctx
    )
    assert result["failure"]["code"] == "dependency_unavailable"
    p.source.access = None
    with pytest.raises(DomainError):
        await m.runtime.read_result(p.raw["action_id"], p.case.ctx)
    assert p.executor.calls == 1


async def test_unknown_original_intent_preserves_hold_and_no_new_attempt(mixed_runtime):
    m = mixed_runtime
    p = m.file
    await approve(m.runtime, p)
    mark = p.case.budget.mark_dispatch

    async def cancelled(context):
        owner = await mark(context)
        await cancel(p.case)
        return owner

    p.case.budget.mark_dispatch = cancelled
    assert (await m.runtime.invoke(p.raw, p.case.ctx))["kind"] != "ok"
    fresh = recover_mixed(m)
    assert (await fresh.runtime.invoke(p.raw, p.case.ctx))["failure"]["code"] == "unknown_effect"
    foreign = p.case.ctx.model_copy(
        update={"attempt_id": "forbidden-new-attempt", "trace_id": "forbidden"}
    )
    assert (await m.runtime.invoke(p.raw, foreign))["failure"]["code"] == "unknown_effect"
    assert await m.ledger.get("tool.attempt.contexts", foreign.attempt_id, p.case.ctx) is None
    assert (await fresh.budget.get_ledger(p.case.ctx))["held"]["tool_calls"] == 1
    assert p.bridge.calls == p.bridge.opens == fresh.bridge.calls == fresh.bridge.opens == 0
