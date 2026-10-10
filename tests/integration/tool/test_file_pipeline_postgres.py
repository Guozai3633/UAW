"""Real SQL, actual temporary file handle, controlled registration/authority/pager."""

import asyncio
import hashlib
from copy import deepcopy
from dataclasses import replace

import pytest

from tests.integration.tool.file_pipeline_fixture import approve_file, recover_file
from tests.integration.tool.file_pipeline_fixture import file_pipeline as file_pipeline
from tests.integration.tool.test_durable import cancel
from tests.unit.tool.file_evidence_fixture import resign_evidence
from uaw.shared.errors import DomainError
from uaw.tool.invocation.schema import normalize


async def test_actual_file_read_preserves_original_and_pending_fee_restart(file_pipeline):
    p = await approve_file(file_pipeline)
    first = await p.facade.invoke(p.raw, p.case.ctx)
    assert first["kind"] == "ok", first
    data = first["payload"]["data"]
    snapshot = (p.root / "file.txt").read_bytes()
    assert data["text"] == snapshot.decode("utf-8")
    assert data["content_hash"] == hashlib.sha256(snapshot).hexdigest()
    recovered = recover_file(p)
    assert await recovered.facade.invoke(p.raw, p.case.ctx) == first
    assert (
        p.bridge.calls == p.bridge.opens == 1
        and recovered.bridge.calls == recovered.bridge.opens == 0
    )
    actual = await recovered.facade.read_outcome(p.case.call["action_id"], p.case.ctx)
    assert actual["outcome"] == "applied" and actual["usage"]["billing_state"] == "pending"
    assert "money" not in actual["usage"]["resources"]
    budget = await recovered.budget.get_ledger(p.case.ctx)
    assert budget["billing_pending"] and budget["held"]["tool_calls"] == 1
    assert budget["held"]["money"] == "0.05"


@pytest.mark.parametrize(
    "location",
    [{"kind": "text_span", "start": 2, "end": 10}, {"kind": "lines", "start": 2, "end": 2}],
)
async def test_actual_file_range_fragment_hash_distinct_from_whole(file_pipeline, location):
    p = file_pipeline
    p.raw["arguments"]["location"] = location
    p.case.call = normalize(p.raw, p.case.registry)
    await approve_file(p)
    result = await p.facade.invoke(p.raw, p.case.ctx)
    assert result["kind"] == "ok", result
    data = result["payload"]["data"]
    whole = (p.root / "file.txt").read_bytes()
    fragment = await p.case.ledger.get("tool.file.fragment.refs", p.case.ctx.attempt_id, p.case.ctx)
    assert fragment["content_hash"] == hashlib.sha256(data["text"].encode("utf-8")).hexdigest()
    assert data["content_hash"] == hashlib.sha256(whole).hexdigest() != fragment["content_hash"]
    assert fragment["location"] == location and data["location"] == location


def next_page(p, cursor):
    ctx = p.case.ctx.model_copy(update={"attempt_id": "page-2-attempt", "trace_id": "page-2-trace"})
    p.raw = {
        **p.raw,
        "action_id": "page-2-action",
        "arguments": {**p.raw["arguments"], "cursor": cursor},
    }
    p.case = replace(p.case, ctx=ctx, call=normalize(p.raw, p.case.registry))
    p.bridge.case = p.case
    p.bridge.data_authority.case = p.case
    p.configuration.ctx = ctx


@pytest.mark.parametrize("changed", [False, True])
async def test_registered_actual_pages_and_stale_snapshot_never_silently_reread(
    file_pipeline, changed
):
    p = await approve_file(file_pipeline)
    p.bridge.page_size = 16
    first = await p.facade.invoke(p.raw, p.case.ctx)
    assert first["kind"] == "ok", first
    data = first["payload"]["data"]
    assert data["location"] == {"kind": "text_span", "start": 0, "end": 16}
    next_page(p, data["next_cursor"])
    await approve_file(p)
    if changed:
        (p.root / "file.txt").write_bytes(b"changed original file contents")
    second = await p.facade.invoke(p.raw, p.case.ctx)
    if changed:
        assert second["failure"]["code"] == "cursor_stale"
        assert (await recover_file(p).facade.invoke(p.raw, p.case.ctx))["failure"][
            "code"
        ] == "unknown_effect"
    else:
        assert second["kind"] == "ok", second
        original = (p.root / "file.txt").read_bytes().decode("utf-8")
        assert data["text"] + second["payload"]["data"]["text"] == original
        assert data["content_hash"] == second["payload"]["data"]["content_hash"]
        assert (await recover_file(p).facade.invoke(p.raw, p.case.ctx)) == second
    assert p.bridge.calls == p.bridge.opens == 2


async def test_original_journal_reply_loss_file_changed_cancel_recovers_old_bytes(file_pipeline):
    p = await approve_file(file_pipeline)
    before = (p.root / "file.txt").read_bytes()

    async def lost():
        raise TimeoutError(
            "Controlled transport reply lost AFTER independent actual journal commit"
        )

    p.bridge.after_journal = lost
    first = await p.facade.invoke(p.raw, p.case.ctx)
    assert first["failure"]["code"] == "invocation_interrupted"
    assert (
        await p.case.ledger.get("tool.provider.receipts", p.case.ctx.attempt_id, p.case.ctx) is None
    )
    (p.root / "file.txt").write_bytes(b"new file is not original result")
    await cancel(p.case)
    p.role.allowed = False
    p.configuration.allowed = False
    fresh = recover_file(p)
    result = await fresh.facade.invoke(p.raw, p.case.ctx)
    assert result["kind"] == "ok", result
    assert result["payload"]["data"]["text"] == before.decode("utf-8")
    assert p.bridge.calls == p.bridge.opens == 1 and fresh.bridge.calls == fresh.bridge.opens == 0
    assert (await fresh.budget.get_ledger(p.case.ctx))["billing_pending"]


@pytest.mark.parametrize(
    "missing", ["bridge", "signatures", "executor", "access", "verifier", "resources"]
)
async def test_missing_file_actual_port_refused_before_hold(file_pipeline, missing):
    p = file_pipeline
    if missing == "executor":
        p.invocation.executor = None
    elif missing == "resources":
        p.case.authority.resources = None
    else:
        setattr(p.source, missing, None)
    result = await p.facade.invoke(p.raw, p.case.ctx)
    assert result["failure"]["code"] == "dependency_unavailable", result
    assert p.bridge.calls == p.bridge.opens == 0
    assert (
        await p.case.ledger.get("tool.budget.reserved", p.case.ctx.attempt_id, p.case.ctx) is None
    )


@pytest.mark.parametrize(
    "part", ["signature", "old_digest", "wrong_path", "wrong_attempt", "snapshot"]
)
async def test_runner_ok_signed_or_tampered_evidence_does_not_publish(file_pipeline, part):
    p = await approve_file(file_pipeline)

    def changed(e):
        if part == "signature":
            return replace(
                e, receipt=e.receipt.model_copy(update={"signature": "invalid-signature"})
            )
        if part == "wrong_attempt":
            return replace(
                e, receipt=e.receipt.model_copy(update={"attempt_id": "foreign-attempt"})
            )
        if part == "snapshot":
            return replace(e, snapshot=b"not the bytes that were read")
        data = deepcopy(e.receipt.payload["result"])
        data["content_hash" if part == "old_digest" else "path"] = (
            "0" * 64 if part == "old_digest" else "another.txt"
        )
        return resign_evidence(e, data, p.signatures)

    p.bridge.transform = changed
    result = await p.facade.invoke(p.raw, p.case.ctx)
    assert result["kind"] != "ok", result
    assert p.bridge.calls == 1
    assert await p.case.ledger.get("tool.results", p.case.ctx.attempt_id, p.case.ctx) is None
    again = await recover_file(p).facade.invoke(p.raw, p.case.ctx)
    assert again["kind"] != "ok" and p.bridge.calls == 1
    assert (await p.case.budget.get_ledger(p.case.ctx))["held"]["tool_calls"] == 1


@pytest.mark.parametrize("revoke", ["root", "key", "data"])
async def test_current_recovery_revocation_blocks_saved_actual_data(file_pipeline, revoke):
    p = await approve_file(file_pipeline)
    assert (await p.facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    before = await p.case.budget.get_ledger(p.case.ctx)
    if revoke == "root":
        p.bridge.allowed = False
    elif revoke == "key":
        p.signatures.revoked = True
    else:
        p.bridge.data_authority.allowed = False
    restored = recover_file(p)
    assert (await restored.facade.invoke(p.raw, p.case.ctx))["kind"] != "ok"
    with pytest.raises(DomainError):
        await restored.facade.read_outcome(p.case.call["action_id"], p.case.ctx)
    assert await restored.budget.get_ledger(p.case.ctx) == before
    assert p.bridge.calls == p.bridge.opens == 1


@pytest.mark.parametrize("change", ["principal", "project", "provider", "attempt"])
async def test_cross_subject_project_attempt_provider_recovery_refused(file_pipeline, change):
    p = await approve_file(file_pipeline)
    assert (await p.facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    fresh = recover_file(p)
    ctx = p.case.ctx
    if change == "principal":
        ctx = ctx.model_copy(
            update={"principal": ctx.principal.model_copy(update={"auth_session_id": "other-auth"})}
        )
    elif change == "project":
        ctx = ctx.model_copy(
            update={"scope": ctx.scope.model_copy(update={"project_id": "foreign-project"})}
        )
    elif change == "attempt":
        ctx = ctx.model_copy(update={"attempt_id": "foreign-attempt"})
    else:
        fresh.source.provider_ref = fresh.source.provider_ref.model_copy(update={"version": "999"})
    assert (await fresh.facade.invoke(p.raw, ctx))["kind"] != "ok"
    assert p.bridge.calls == p.bridge.opens == 1 and fresh.bridge.calls == 0


async def test_concurrent_file_dispatch_and_concurrent_recovery_keep_original_attempt(
    file_pipeline,
):
    p = await approve_file(file_pipeline)
    rows = await asyncio.gather(*(p.facade.invoke(p.raw, p.case.ctx) for _ in range(2)))
    assert p.bridge.calls == p.bridge.opens == 1 and any(r["kind"] == "ok" for r in rows), rows
    fresh = recover_file(p)
    results = await asyncio.gather(*(fresh.facade.invoke(p.raw, p.case.ctx) for _ in range(2)))
    assert all(r["kind"] == "ok" for r in results), results
    assert results[0] == results[1] and fresh.bridge.calls == 0
    assert (await fresh.case.ledger.effect_from_attempt(p.case.ctx))["attempt_ids"] == [
        p.case.ctx.attempt_id
    ]


async def test_no_original_journal_retains_unknown_hold_and_refuses_new_attempt(file_pipeline):
    p = await approve_file(file_pipeline)

    async def unknown(*args):
        p.bridge.calls += 1
        raise TimeoutError("Controlled send ambiguity, no actual original receipt observed")

    p.executor.execute = unknown
    assert (await p.facade.invoke(p.raw, p.case.ctx))["failure"]["code"] == "invocation_interrupted"
    fresh = recover_file(p)
    assert (await fresh.facade.invoke(p.raw, p.case.ctx))["failure"]["code"] == "unknown_effect"
    other = p.case.ctx.model_copy(
        update={"attempt_id": "replacement-attempt", "trace_id": "replacement-trace"}
    )
    assert (await p.facade.invoke(p.raw, other))["failure"]["code"] == "unknown_effect"
    assert await p.case.ledger.get("tool.attempt.contexts", other.attempt_id, p.case.ctx) is None
    assert (await fresh.budget.get_ledger(p.case.ctx))["held"]["tool_calls"] == 1
    assert p.bridge.calls == 1 and p.bridge.opens == fresh.bridge.calls == 0


async def test_actual_fee_reply_loss_replays_original_plan_independent_of_file_effect(
    file_pipeline,
):
    p = await approve_file(file_pipeline)
    settle = p.case.budget.budgets.settle

    async def lost(*args, **kwargs):
        await settle(*args, **kwargs)
        raise TimeoutError("Controlled usage settlement reply lost AFTER actual SQL commit")

    p.case.budget.budgets.settle = lost
    failed = await p.facade.invoke(p.raw, p.case.ctx)
    assert failed["failure"]["code"] == "reconciliation_interrupted", failed
    actual = await p.facade.read_outcome(p.case.call["action_id"], p.case.ctx)
    assert actual["outcome"] == "applied" and actual["usage"]["billing_state"] == "pending"
    before = await p.case.budget.get_ledger(p.case.ctx)
    fresh = recover_file(p)
    assert (await fresh.facade.invoke(p.raw, p.case.ctx))["kind"] == "ok"
    assert await fresh.budget.get_ledger(p.case.ctx) == before
    assert before["billing_pending"] and before["held"]["tool_calls"] == 1
    assert p.bridge.calls == p.bridge.opens == 1


@pytest.mark.parametrize("boundary", ["cancel", "flag", "root"])
async def test_current_admission_revocation_before_send_never_reads(file_pipeline, boundary):
    p = await approve_file(file_pipeline)
    if boundary == "cancel":
        await cancel(p.case)
    elif boundary == "flag":
        p.configuration.allowed = False
    else:
        p.bridge.allowed = False
    denied = await p.facade.invoke(p.raw, p.case.ctx)
    assert denied["kind"] != "ok" and p.bridge.calls == p.bridge.opens == 0
    assert (
        await p.case.ledger.get("tool.budget.reserved", p.case.ctx.attempt_id, p.case.ctx) is None
    )
