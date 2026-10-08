"""Controlled SQL/fee protocol fixtures with actual text calculation and private blob."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from tests.unit.tool.test_reconciliation import reconciliation_case as reconciliation_case
from uaw.infrastructure.blob.filesystem import FSBlobStore
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import DomainError, reject
from uaw.shared.schema import validate_contract
from uaw.tool.ledger import action_key
from uaw.tool.providers.text import (
    TextInspectExecutor,
    TextInspectVerifier,
    inspect_text,
    text_spec,
)
from uaw.tool.receipt_store import ToolReceiptStore
from uaw.tool.reconciliation import ToolReconciler
from uaw.tool.registry import ToolRegistry
from uaw.tool.results import ToolResults
from uaw.tool.schema import digest


class CurrentRecoveryFixture:
    def __init__(self, case, provider):
        self.ctx, self.provider, self.allowed = case.ctx, provider, True
        self.transactions = case.ledger.transactions

    async def check(self, call, spec, ctx, *, provider):
        assert not self.transactions.lock.locked(), "Source await under Tool transaction lock"
        if not self.allowed or ctx != self.ctx or provider != self.provider:
            raise reject(
                "result_source_revoked",
                "Controlled current recovery access denied",
                403,
                "authorization",
            )


@pytest.fixture
async def unit_text_pipeline(reconciliation_case, tmp_path):
    c = reconciliation_case
    key = action_key(c.ctx, "action-c")
    provider_ref = Ref.model_validate(c.receipt["provider_ref"])
    spec = text_spec(provider_ref)
    registry = ToolRegistry()
    registry.register(spec, expected_revision=0)
    args = {"text": "  原文\r\nKeep\u0301 exact  "}
    call = {
        "tool_ref": registry.reference(registry.snapshot()[1][0]),
        "action_id": "action-c",
        "arguments": args,
        "arguments_hash": digest(args),
    }
    c.store.put("tool.calls", key, "ValidatedCall", call)
    c.store.put("tool.attempt.calls", c.ctx.attempt_id, "ValidatedCall", call)
    c.store.put("tool.specs", key, "ToolSpec", spec)
    provider = Principal(
        id="unit-text-service", kind="service", auth_session_id="unit-provider-session"
    )
    access = CurrentRecoveryFixture(c, provider)
    source = ToolReceiptStore(
        c.ledger,
        FSBlobStore(tmp_path / "unit-blobs"),
        provider_ref=provider_ref,
        provider=provider,
        access=access,
        verifier=TextInspectVerifier(provider_ref),
    )
    reconciler = ToolReconciler(c.ledger, c.budget, receipts=source, evidence=source)
    results = ToolResults(source, reconciler)
    executor = TextInspectExecutor(source, provider=provider)
    return SimpleNamespace(
        case=c,
        ctx=c.ctx,
        call=call,
        spec=spec,
        provider=provider,
        source=source,
        access=access,
        results=results,
        reconciler=reconciler,
        executor=executor,
    )


async def execute(p):
    return await p.executor.execute(p.call, p.spec, p.ctx)


async def test_actual_provider_raw_evidence_receipt_and_tool_result_bindings(unit_text_pipeline):
    p = unit_text_pipeline
    receipt = await execute(p)
    validate_contract("ProviderReceipt", receipt)
    assert await p.source.find("action-c", p.ctx) is None
    result = await p.results.resume(p.call, p.ctx)
    validate_contract("RuntimeToolruntimeInvokeResult", result)
    assert result["payload"]["data"] == inspect_text(p.call["arguments"]["text"])
    ref = await p.source.find("action-c", p.ctx)
    actual = await p.source.read(ref, p.ctx)
    assert actual == await p.reconciler.read_outcome("action-c", p.ctx)
    assert actual["outcome"] == "applied" and actual["usage"]["resources"]["money"] == "0.00"
    assert p.case.fee.commits == 1
    assert await p.results.resume(p.call, p.ctx) == result and p.case.fee.commits == 1


@pytest.mark.parametrize("field", ["attempt_id", "raw_result_ref", "usage", "approved"])
async def test_provider_publish_requires_exact_real_saved_receipt(unit_text_pipeline, field):
    p = unit_text_pipeline
    actual = await execute(p)
    bad = deepcopy(actual)
    if field == "usage":
        bad["usage"]["attempt_id"] = "foreign-attempt"
    elif field == "raw_result_ref":
        bad["raw_result_ref"]["id"] = "invented-raw"
    else:
        bad[field] = "invented"
    with pytest.raises(DomainError):
        await p.source.publish(bad, p.ctx, authenticated_provider=p.provider)
    assert await p.source.find("action-c", p.ctx) is None and p.case.fee.commits == 0


@pytest.mark.parametrize("field", ["id", "auth_session_id", "kind"])
async def test_provider_identity_is_full_independently_bound_principal(unit_text_pipeline, field):
    p = unit_text_pipeline
    actual = await execute(p)
    foreign = p.provider.model_copy(update={field: "user" if field == "kind" else "foreign"})
    with pytest.raises(DomainError) as error:
        await p.source.publish(actual, p.ctx, authenticated_provider=foreign)
    assert error.value.failure.code == "provider_scope_denied"


@pytest.mark.parametrize("missing", ["authority", "verifier"])
async def test_results_missing_authority_or_verifier_not_success(unit_text_pipeline, missing):
    p = unit_text_pipeline
    await execute(p)
    if missing == "authority":
        p.source.access = None
    else:
        p.source.verifier = None
    with pytest.raises(DomainError) as error:
        p.results.ready()
    assert error.value.failure.code == "dependency_unavailable"
    with pytest.raises(DomainError):
        await p.results.resume(p.call, p.ctx)
    assert p.case.fee.commits == 0


async def test_unknown_no_saved_raw_does_not_guess_from_transport_or_budget(unit_text_pipeline):
    p = unit_text_pipeline
    with pytest.raises(DomainError) as error:
        await p.results.resume(p.call, p.ctx)
    assert error.value.failure.code == "unknown_effect" and p.case.fee.commits == 0
    assert (await p.case.ledger.effect_from_attempt(p.ctx))["state"] == "unknown"


@pytest.mark.parametrize(
    "bad", [{"unknown": 1}, {"characters": 1, "utf8_bytes": 1, "lines": 1, "sha256": "0" * 64}]
)
async def test_output_schema_and_actual_semantics_independent_of_transport(unit_text_pipeline, bad):
    p = unit_text_pipeline
    receipt = await execute(p)
    # Fresh controlled persisted raw observations are still not successful outputs.
    for ns in ("tool.response.refs", "tool.response.providers", "tool.provider.receipts"):
        p.case.store.rows.pop((ns, p.ctx.attempt_id))
    bad_receipt = await p.source.save_response(
        bad, receipt["usage"], p.ctx, authenticated_provider=p.provider
    )
    assert bad_receipt["effect_state"] == "confirmed"
    with pytest.raises(DomainError) as error:
        await p.results.resume(p.call, p.ctx)
    assert error.value.failure.code == "tool_output_invalid" and p.case.fee.commits == 0


async def test_outcome_and_actual_effect_survive_fee_response_loss(unit_text_pipeline):
    p = unit_text_pipeline
    await execute(p)
    p.case.fee.lose_reply = True
    interrupted = await p.results.resume(p.call, p.ctx)
    assert interrupted["failure"]["code"] == "reconciliation_interrupted"
    actual = await p.reconciler.read_outcome("action-c", p.ctx)
    assert actual["outcome"] == "applied" and p.case.fee.commits == 1
    assert (await p.results.resume(p.call, p.ctx))["kind"] == "ok" and p.case.fee.commits == 1


async def test_current_source_revocation_denies_all_cached_result_access(unit_text_pipeline):
    p = unit_text_pipeline
    await execute(p)
    result = await p.results.resume(p.call, p.ctx)
    assert result["kind"] == "ok"
    before = deepcopy(p.case.store.rows)
    p.access.allowed = False
    for read in (
        p.results.read_result("action-c", p.ctx),
        p.reconciler.read_outcome("action-c", p.ctx),
        p.source.find("action-c", p.ctx),
    ):
        with pytest.raises(DomainError) as error:
            await read
        assert error.value.status_code == 403
    assert p.case.store.rows == before and p.case.fee.commits == 1


async def test_current_source_revocation_during_output_verify_no_publish_or_fees(
    unit_text_pipeline,
):
    p = unit_text_pipeline
    await execute(p)
    original = p.source.verifier.verify

    async def revoke(*args):
        await original(*args)
        p.access.allowed = False

    p.source.verifier.verify = revoke
    with pytest.raises(DomainError):
        await p.results.resume(p.call, p.ctx)
    assert await p.case.ledger.get("tool.source.receipts", p.ctx.attempt_id, p.ctx) is None
    assert p.case.fee.commits == 0


async def test_accepted_results_return_copy_and_exact_pinned_refs(unit_text_pipeline):
    p = unit_text_pipeline
    await execute(p)
    result = await p.results.resume(p.call, p.ctx)
    result["payload"]["data"]["sha256"] = "0" * 64
    actual = await p.results.read_result("action-c", p.ctx)
    assert (
        actual["payload"]["data"]["sha256"] == inspect_text(p.call["arguments"]["text"])["sha256"]
    )
    ref = await p.source.find("action-c", p.ctx)
    with pytest.raises(DomainError):
        await p.source.read(ref.model_copy(update={"content_hash": "0" * 64}), p.ctx)
    assert p.case.fee.commits == 1


@pytest.mark.parametrize("field", ["data", "usage_ref", "output_refs"])
async def test_stored_toolresult_changes_cannot_fake_current_success(unit_text_pipeline, field):
    p = unit_text_pipeline
    await execute(p)
    result = await p.results.resume(p.call, p.ctx)
    changed = deepcopy(result["payload"])
    if field == "data":
        changed["data"]["characters"] += 1
    elif field == "usage_ref":
        changed[field]["id"] = "invented-usage"
    else:
        changed[field] = []
    p.case.store.put("tool.results", p.ctx.attempt_id, "ToolResult", changed)
    with pytest.raises(DomainError):
        await p.results.read_result("action-c", p.ctx)
    assert p.case.fee.commits == 1


async def test_source_declines_wrong_action_scope_and_raw_evidence(unit_text_pipeline):
    p = unit_text_pipeline
    await execute(p)
    assert (await p.results.resume(p.call, p.ctx))["kind"] == "ok"
    for read in (
        p.source.find("different-action", p.ctx),
        p.source.check(Ref(kind="content", id="invented", version="1"), p.ctx),
        p.results.read_result("different-action", p.ctx),
    ):
        with pytest.raises(DomainError):
            await read
