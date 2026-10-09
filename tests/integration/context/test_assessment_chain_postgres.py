"""MS-C6 cost/chain/restart proofs on actual PG55433 and FS; controlled advice only."""

from __future__ import annotations

import asyncio
import json
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from tests.integration.context.registered_fixture import assemble
from tests.integration.context.test_assessment_postgres import ControlledAdvice, setup
from tests.integration.context.test_registered_chain_postgres import child, child_payload
from tests.integration.context.test_registered_postgres import case as case
from tests.integration.context.test_registered_postgres import domain as domain
from tests.integration.context.test_registered_postgres import registration as registration
from tests.integration.context.test_registered_postgres import understanding as understanding
from tests.integration.test_control_plane import meta
from uaw.context.cache import PureComputationCache
from uaw.context.contracts import Reading, digest, matches_pin
from uaw.context.model_input import GenericModelInputs, serialize
from uaw.context.readers import RegisteredContextReader
from uaw.context.registered import RegisteredContextInputs
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError, reject
from uaw.shared.stores import StoreConflict, StoreMissing


class LegacyExpansion(RegisteredContextInputs):
    """Published 17e4682 authority expansion as a comparison strategy, not fake SQL.

    Same current authority/RecordStore/real blobs; no cached data or permissions.
    Reproduces recipe/current/read/recipe/current public gates from stage 1/2.
    """

    async def inspect(self, ctx):
        saved = await self.recipe(ctx)
        original = await self.current(ctx)
        if any(
            not any(matches_pin(pin, actual) for actual in saved.request.source_refs)
            for pin in original
        ):
            raise reject("context_dependency_changed", "Run originals changed", 410)
        for pin in (*saved.request.source_refs, *saved.rules.user_instruction_refs):
            await self.read(pin, ctx)
        if await self.recipe(ctx) != saved or await self.current(ctx) != original:
            raise reject("context_dependency_changed", "Recipe/source boundary changed", 410)
        return saved, original

    async def _read(self, pin, ctx):
        if pin.kind == "configuration":
            # Stage read(configuration) nested the gated public recipe reader.
            saved = await self.recipe(ctx)
            text = serialize(saved.tools.wire())
            import hashlib

            actual = Ref(
                kind="configuration",
                id=saved.ref.id,
                version=saved.ref.version,
                content_hash=hashlib.sha256(text.encode()).hexdigest(),
            )
            if pin.location is not None or not matches_pin(pin, actual):
                raise reject("source_changed", "Tool set pin changed", 410)
            return Reading(actual, text, kind="material", trust="platform", required=True)
        return await super()._read(pin, ctx)


class CountingReader(RegisteredContextReader):
    def __init__(self, inputs):
        super().__init__(inputs)
        self.counts = Counter()

    async def check(self, pin, ctx):
        self.counts["check"] += 1
        return await super().check(pin, ctx)

    async def read(self, pin, policy, ctx):
        self.counts["read"] += 1
        return await super().read(pin, policy, ctx)


class Meter:
    def __init__(self, records):
        self.counts = Counter()
        self.phases = []
        actual = records.get

        async def get(principal, namespace, identifier, **kwargs):
            self.counts[namespace] += 1
            return await actual(principal, namespace, identifier, **kwargs)

        records.get = get

    async def run(self, strategy, boundary, operation, reader=None, assessor=None):
        before = self.counts.copy()
        reads = reader.counts.copy() if reader else Counter()
        calls = assessor.calls if assessor else 0
        started = time.perf_counter()
        try:
            result = await operation
            status = "ok"
        except (DomainError, StoreMissing) as exc:
            result = exc
            status = exc.failure.code
        elapsed = time.perf_counter() - started
        delta = self.counts - before
        self.phases.append(
            dict(
                strategy=strategy,
                boundary=boundary,
                seconds=round(elapsed, 6),
                record_get=sum(delta.values()),
                namespaces=dict(delta),
                reader=dict(reader.counts - reads) if reader else {},
                assessor=assessor.calls - calls if assessor else 0,
                result=status,
            )
        )
        await asyncio.to_thread(
            Path("tests/.artifacts/B/MS-C6/read-cost-progress.json").write_text,
            json.dumps(self.phases, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return result


def wire(s, *, inputs_type=RegisteredContextInputs, cache=None):
    assessor = ControlledAdvice()
    inputs, components, model = assemble(
        s.records,
        s.configuration,
        s.blob_directory,
        s.controller,
        current_runs=True,
        assessor=assessor,
        inputs_type=inputs_type,
        cache=cache,
    )
    reader = CountingReader(inputs)
    components.sources.readers = dict.fromkeys(
        ("input", "content", "rule", "configuration"), reader
    )
    # Count body expansion separately from the public Reader port calls.
    for method, label in (
        ("_read", "registered_body"),
        ("_access", "current_gate"),
        ("_recipe", "recipe_body"),
        ("_current", "originals_body"),
    ):
        actual = getattr(inputs, method)

        async def counted(*args, _actual=actual, _label=label):
            reader.counts[_label] += 1
            return await _actual(*args)

        setattr(inputs, method, counted)
    return inputs, components, model, reader, assessor


async def test_sql_actual_current_chain_cost_and_cache_comparison(registration):
    s = registration
    s.ctx = s.ctx.model_copy(
        update={"deadline": (datetime.now(UTC) + timedelta(minutes=55)).isoformat()}
    )
    meter = Meter(s.records)
    # Registration itself runs against A's published actual Run/Model policy adapter.
    s.inputs, s.components, s.model, reader, assessor = wire(s)
    mat, pins, saved, _, _, _ = await meter.run("batch", "registration", setup(s), reader, assessor)
    prompts = []
    snapshots = []
    assemblies = []
    for strategy, kind in (
        ("stage-expansion", LegacyExpansion),
        ("batch", RegisteredContextInputs),
    ):
        inputs, components, model, reader, assessor = wire(s, inputs_type=kind)
        ctx = s.ctx.model_copy(update={"operation_id": f"cost-{strategy}"})
        binding = await meter.run(
            strategy,
            "authority.resolve",
            components.composer.authority.resolve("agent_step", ctx),
            reader,
            assessor,
        )
        assert not isinstance(binding, Exception)
        assert not isinstance(
            await meter.run(strategy, "read", inputs.read(mat, ctx), reader, assessor), Exception
        )
        assert not isinstance(
            await meter.run(strategy, "recipe", inputs.recipe(ctx), reader, assessor), Exception
        )
        await meter.run(
            strategy,
            "authority.verify",
            components.composer.authority.verify(binding, ctx),
            reader,
            assessor,
        )
        assembly = await meter.run(
            strategy, "rules", components.rules.assemble(saved.rules, ctx), reader, assessor
        )
        assert not isinstance(assembly, Exception)
        built = await meter.run(
            strategy, "build", components.build(saved.request.wire(), ctx), reader, assessor
        )
        assert built["kind"] == "ok", built
        prompt = await meter.run(
            strategy, "ModelInput", model.resolve(built["output_refs"][0], ctx), reader, assessor
        )
        assert not isinstance(prompt, Exception)
        prompts.append(prompt)
        snapshots.append(built)
        assemblies.append(assembly)
        opened = await meter.run(
            strategy,
            "reference",
            components.references.read({"reference": mat.wire()}, ctx),
            reader,
            assessor,
        )
        assert opened["text"].startswith("部门,预算,已用")
    assert prompts[0] == prompts[1]
    assert assemblies[0] == assemblies[1]
    assert s.original["text"] in [message["content"] for message in prompts[1].messages]
    assert not prompts[1].tools and not s.case.requests
    phase = {(p["strategy"], p["boundary"]): p for p in meter.phases}
    for boundary in ("authority.resolve", "authority.verify", "rules", "build", "ModelInput"):
        assert (
            phase[("batch", boundary)]["record_get"]
            < phase[("stage-expansion", boundary)]["record_get"]
        )
    cache = PureComputationCache(max_entries=128, max_bytes=2097152)
    inputs, components, _, reader, assessor = wire(s, cache=cache)
    cached = GenericModelInputs(components.composer, cache=cache)
    pin = snapshots[1]["output_refs"][0]
    for name in ("cache-cold", "cache-warm"):
        assert (
            await meter.run("batch", name, cached.resolve(pin, s.ctx), reader, assessor)
            == prompts[1]
        )
    assert cache.stats.hits > 0
    disabled = GenericModelInputs(
        components.composer, cache=PureComputationCache(max_entries=0, max_bytes=0)
    )
    assert (
        await meter.run("batch", "cache-disabled", disabled.resolve(pin, s.ctx), reader, assessor)
        == prompts[1]
    )
    await inputs.revoke(
        mat,
        s.ctx,
        authenticated_service=s.controller,
        expected_revision=1,
        meta=meta("cost-revoke", 1),
    )
    for strategy, kind in (
        ("stage-expansion", LegacyExpansion),
        ("batch", RegisteredContextInputs),
    ):
        _, components, model, reader, assessor = wire(s, inputs_type=kind, cache=cache)
        rejected = await meter.run(
            strategy, "revoked-ModelInput", model.resolve(pin, s.ctx), reader, assessor
        )
        assert isinstance(rejected, Exception)
        assert meter.phases[-1]["result"] == "resource_missing"
    report = dict(
        evidence="actual PostgreSQL55433/FS; controlled advice; no LLM/production latency claim",
        baseline="f5b08fa6dcc653c0cd3939a32f36deeb0e51dff8",
        comparison=(
            "stage 17e4682 public expansion vs batch; same actual A authority/sources; "
            "distinct build operation IDs"
        ),
        prompt_hash=digest(prompts[1].messages),
        estimated_tokens=prompts[1].estimated_tokens,
        phases=meter.phases,
    )
    await asyncio.to_thread(
        Path("tests/.artifacts/B/MS-C6/read-cost.json").write_text,
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


async def test_sql_multirule_new_process_and_concurrent_snapshot(registration):
    s = registration
    mat, pins, saved, _, _, _ = await setup(s)
    s.inputs, s.components, s.model, _, _ = wire(s)
    s.ctx = s.ctx.model_copy(
        update={
            "operation_id": "multi-concurrent",
            "deadline": (datetime.now(UTC) + timedelta(minutes=10)).isoformat(),
        }
    )
    results = await asyncio.gather(
        *[s.components.build(saved.request.wire(), s.ctx) for _ in range(2)]
    )
    assert all(r["kind"] == "ok" for r in results), results
    assert results[0]["output_refs"] == results[1]["output_refs"]
    prompt = await s.model.resolve(results[0]["output_refs"][0], s.ctx)
    payload = child_payload(s)
    payload.update(current_runs=True, controlled_assessor=True)
    code, restored = await child(payload)
    assert code == 0 and restored["messages_hash"] == digest(prompt.messages), restored
    assert restored["snapshot_ref"] == results[0]["output_refs"][0]
    assert restored["estimated_tokens"] == prompt.estimated_tokens
    assert not s.case.requests


@pytest.mark.parametrize("change", ["cancel", "model", "scope"])
async def test_sql_actual_current_model_wait_revocation(registration, change):
    s = registration
    _, _, saved, _, assessor, _ = await setup(s, wait=True)
    # Keep the controlled waiter but use actual A Run/model current authority.
    inputs, components, _, _, _ = wire(s)
    from uaw.context.readers import RegisteredRuleProvider

    provider = RegisteredRuleProvider(inputs, assessor=assessor)
    task = asyncio.create_task(provider.discover(saved.rules, s.ctx))
    await asyncio.wait_for(assessor.started.wait(), 45)
    try:
        if change == "cancel":
            row = await s.records.get(s.ctx.principal, "budget.ledgers", s.ctx.run_id)
            data = dict(row.payload)
            data["cancel_requested"] = True
            await s.records.put(
                s.ctx.principal,
                row.namespace,
                row.resource_id,
                row.schema_name,
                data,
                expected_revision=row.revision,
                request_id="wait-cancel",
            )
        elif change == "model":
            row = await s.records.get(s.ctx.principal, "model.policies", s.ctx.model_policy_ref.id)
            await s.records.put(
                s.ctx.principal,
                row.namespace,
                row.resource_id,
                row.schema_name,
                row.payload,
                expected_revision=row.revision,
                request_id="wait-model-revise",
            )
        else:
            # Real capability policy change, scope/Run remain fixed in ctx.
            row = await s.records.get(
                s.ctx.principal, "execution.policies", s.ctx.capability_policy_ref.id
            )
            data = dict(row.payload)
            data["revision"] = row.revision + 1
            data["resource_scope"] = {"conversation_id": "foreign"}
            await s.records.put(
                s.ctx.principal,
                row.namespace,
                row.resource_id,
                row.schema_name,
                data,
                expected_revision=row.revision,
                request_id="wait-scope-revise",
            )
    finally:
        assessor.release.set()
    with pytest.raises(DomainError):
        await task


async def test_sql_batch_detects_actual_corruption_between_passes(registration):
    s = registration
    mat, _, _, _, _, _ = await setup(s)
    actual_get = s.inputs.blobs.get
    calls = Counter()

    async def corrupted(principal, content_hash):
        calls[content_hash] += 1
        data = await actual_get(principal, content_hash)
        if content_hash == mat.content_hash and calls[content_hash] == 2:
            # Timing controlled, bytes are changed to invalid actual content in the read.
            return data + b"changed"
        return data

    s.inputs.blobs.get = corrupted
    with pytest.raises(DomainError) as caught:
        await s.inputs.inspect(s.ctx)
    assert caught.value.failure.code == "source_changed"


async def test_sql_concurrent_revision_invalidates_assessed_sources(registration):
    s = registration
    _, pins, saved, _, assessor, provider = await setup(s, wait=True)
    task = asyncio.create_task(provider.discover(saved.rules, s.ctx))
    await asyncio.wait_for(assessor.started.wait(), 30)
    from tests.integration.context.test_registered_postgres import register_rule, rule

    values = await asyncio.gather(
        *[
            register_rule(
                s,
                rule(s, id="format-0", text=f"revision-{i}", revision=1, level="user_current"),
                expected=1,
                name=f"concurrent-rule-{i}",
            )
            for i in range(2)
        ],
        return_exceptions=True,
    )
    assessor.release.set()
    assert len([v for v in values if isinstance(v, Ref)]) == 1
    assert len([v for v in values if isinstance(v, StoreConflict)]) == 1
    with pytest.raises(DomainError):
        await task
