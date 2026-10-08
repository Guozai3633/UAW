"""MS-C4 pure computation checks; Readers/storage/authority remain controlled fixtures."""

from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta

import pytest

from tests.unit.context.test_components import candidate, context, reading
from tests.unit.context.test_model_input import ready, set_tools, tool
from tests.unit.context.test_snapshots import build
from uaw.context.cache import CacheKey, PureComputationCache, lookup, make_key, reading_key
from uaw.context.contracts import RulePlan
from uaw.context.model_input import GenericModelInputs
from uaw.context.selection import ConservativeTokenCounter
from uaw.shared.errors import DomainError, reject


class CountingInputs(GenericModelInputs):
    format_calls = 0

    def _format(self, *args):
        self.format_calls += 1
        return super()._format(*args)


class CountingCounter(ConservativeTokenCounter):
    calls = 0

    def count(self, value):
        self.calls += 1
        return super().count(value)


def cache(**limits):
    return PureComputationCache(**({"max_entries": 64, "max_bytes": 256000} | limits))


async def cached_ready(*, storage=None, count=True):
    c = await ready((tool(),))
    c.cache = storage if storage is not None else cache()
    c.counter = CountingCounter()
    c.component.selection.counter = c.counter
    c.component.selection.cache = c.cache if count else None
    c.resolver = CountingInputs(c.component.composer, cache=c.cache)
    return c


async def resolve(c, ctx=None, pin=None):
    return await c.resolver.resolve(pin if pin is not None else c.pin, ctx or c.ctx)


async def test_repeat_reduces_only_pure_calls_live_checks_remain_equal():
    c = await cached_ready()
    before = (c.reader.calls, c.authority.calls, c.models.calls, c.component.rules.provider.calls)
    first = await resolve(c)
    middle = (c.reader.calls, c.authority.calls, c.models.calls, c.component.rules.provider.calls)
    assert c.resolver.format_calls == 1 and c.counter.calls == 3
    # Trace/operation/attempt/deadline change does not change stable pure-input identity.
    ctx = c.ctx.model_copy(
        update={"operation_id": "generation", "attempt_id": "second", "trace_id": "next"}
    )
    second = await resolve(c, ctx)
    after = (c.reader.calls, c.authority.calls, c.models.calls, c.component.rules.provider.calls)
    assert first == second
    assert c.resolver.format_calls == 1 and c.counter.calls == 3
    assert tuple(b - a for a, b in zip(before, middle, strict=True)) == tuple(
        b - a for a, b in zip(middle, after, strict=True)
    )
    assert all(b > a for a, b in zip(middle, after, strict=True))


@pytest.mark.parametrize("limits", [{"max_entries": 0}, {"max_bytes": 0}, {}])
async def test_zero_and_absent_injection_disable_cache(limits):
    storage = PureComputationCache(**limits)
    c = await cached_ready(storage=storage)
    a, b = await resolve(c), await resolve(c)
    assert a == b and c.resolver.format_calls == 2 and c.counter.calls == 12
    assert storage.stats.entries == storage.stats.size_bytes == 0
    c.resolver = CountingInputs(c.component.composer)
    await resolve(c)
    await resolve(c)
    assert c.resolver.format_calls == 2


@pytest.mark.parametrize("change", ["required", "requirements"])
async def test_same_text_changed_preservation_metadata_recomputes(change):
    c = await cached_ready()
    first = await resolve(c)
    value = c.reader.records[c.original.ref.id]
    c.reader.records[value.ref.id] = replace(
        value,
        **({"required": True} if change == "required" else {"requirement_ids": ("new-id",)}),
    )
    second = await resolve(c)
    assert first == second and c.resolver.format_calls == 2 and c.counter.calls == 6


@pytest.mark.parametrize("change", ["text", "trust", "kind", "rule", "tools", "epoch"])
async def test_warm_cache_never_masks_stale_content_classification_rules_tools_epoch(change):
    c = await cached_ready()
    await resolve(c)
    if change == "text":
        c.reader.records[c.original.ref.id] = replace(c.original, text="changed same ID/version")
    elif change in ("trust", "kind"):
        c.reader.records[c.original.ref.id] = replace(
            c.original, **({"trust": "project"} if change == "trust" else {"kind": "material"})
        )
    elif change == "rule":
        c.component.rules.provider.plan = RulePlan(
            (candidate(c.rule, "project"),), assessment_complete=True
        )
    elif change == "tools":
        set_tools(c, [tool("other.read")])
    else:
        c.authority.binding = replace(c.authority.binding, epoch=1)
    with pytest.raises(DomainError):
        await resolve(c)
    assert c.resolver.format_calls == 1


@pytest.mark.parametrize("change", ["text", "rule", "tools", "epoch", "reserves"])
async def test_new_valid_snapshot_never_reuses_old_pure_payload(change):
    c = await cached_ready()
    first = await resolve(c)
    old_pin = c.pin.copy()
    c.ctx = c.ctx.model_copy(update={"operation_id": "new-context"})
    if change == "text":
        value = reading(
            "New exact user text\r\n", id=c.original.ref.id, kind="user_input", trust="user"
        )
        value = replace(value, ref=value.ref.model_copy(update={"version": "v2"}))
        c.original = value
        c.reader.records[value.ref.id] = value
        c.request["source_refs"] = [value.ref.wire()]
        c.request["preserve"]["exact_strings"] = []
        c.authority.binding = replace(
            c.authority.binding,
            preserve=c.authority.binding.preserve.model_copy(
                update={"required_refs": (value.ref,)}
            ),
        )
    elif change == "rule":
        value = reading(
            "New registered rule", id=c.rule.ref.id, kind="instruction", trust="platform"
        )
        value = replace(value, ref=value.ref.model_copy(update={"version": "v2"}))
        c.rule = value
        c.reader.records[value.ref.id] = value
        c.component.rules.provider.plan = RulePlan(
            (candidate(value, "platform"),), assessment_complete=True
        )
    elif change == "tools":
        set_tools(c, [tool("new.read", description="New ToolSpec schema")])
        value = replace(c.cap, ref=c.cap.ref.model_copy(update={"version": "v2"}))
        c.reader.records[value.ref.id] = value
        c.authority.binding = replace(c.authority.binding, capability_ref=value.ref)
    elif change == "epoch":
        c.authority.binding = replace(c.authority.binding, epoch=1)
        c.request["expected_epoch"] = 1
    else:
        c.request["output_reserve"] += 1
        c.request["tool_reserve"] += 1
    result = await build(c)
    assert result["kind"] == "ok", result
    c.pin = result["output_refs"][0]
    second = await resolve(c)
    assert c.resolver.format_calls == 2
    assert c.pin != old_pin  # Actual new snapshot has a distinct build identity.
    if change in ("text", "rule"):
        assert second.messages != first.messages
    elif change == "tools":
        assert second.tools != first.tools


async def test_window_change_recomputes_and_reduced_window_rejects():
    c = await cached_ready()
    a = await resolve(c)
    c.models.limit += 1
    b = await resolve(c)
    assert a == b and c.resolver.format_calls == 2 and c.counter.calls == 6
    c.models.limit = 100
    with pytest.raises(DomainError) as caught:
        await resolve(c)
    assert caught.value.failure.category == "budget" and c.resolver.format_calls == 2


@pytest.mark.parametrize("change", ["reader", "authority", "cancel", "deadline", "missing_reader"])
async def test_warm_cache_still_rejects_revoke_cancel_expiry_missing_reader(change):
    c = await cached_ready()
    await resolve(c)
    if change == "reader":
        c.reader.revoked = True
    elif change == "authority":
        c.authority.revoked = True
    elif change == "cancel":
        c.control.cancelled = True
    elif change == "deadline":
        c.ctx = c.ctx.model_copy(
            update={"deadline": (datetime.now(UTC) - timedelta(seconds=1)).isoformat()}
        )
    else:
        del c.component.sources.readers["input"]
    with pytest.raises(DomainError):
        await resolve(c)
    assert c.resolver.format_calls == 1


@pytest.mark.parametrize("change", ["reader", "authority", "cancel", "epoch", "window"])
async def test_final_recheck_runs_even_after_pure_cache_hit(change):
    class FlipOnHit(PureComputationCache):
        action = None

        def get(self, key):
            value = super().get(key)
            if value is not None and self.action is not None:
                self.action()
            return value

    storage = FlipOnHit(max_entries=16, max_bytes=256000)
    c = await cached_ready(storage=storage, count=False)
    await resolve(c)

    def flip():
        if change == "reader":
            c.reader.revoked = True
        elif change == "authority":
            c.authority.revoked = True
        elif change == "cancel":
            c.control.cancelled = True
        elif change == "epoch":
            c.authority.binding = replace(c.authority.binding, epoch=1)
        else:
            c.models.limit = 100

    storage.action = flip
    with pytest.raises(DomainError):
        await resolve(c)
    assert storage.stats.hits == 1 and c.resolver.format_calls == 1


async def test_returned_mutation_is_isolated_from_future_hits_and_sources():
    c = await cached_ready()
    first = await resolve(c)
    first.messages[0]["content"] = "modified system text"
    first.tools[0]["input_schema"]["properties"]["key"]["type"] = "integer"
    second = await resolve(c)
    assert second.messages[0]["content"] == c.rule.text
    assert second.tools[0] == tool()
    assert c.resolver.format_calls == 1
    with pytest.raises(FrozenInstanceError):
        c.cache.stats.entries = 100


@pytest.mark.parametrize(
    "change", ["run_id", "principal", "scope", "auth_session", "permission", "model"]
)
async def test_security_boundary_never_cross_hits(change):
    c = await cached_ready(count=False)
    await resolve(c)
    ctx = c.ctx
    if change == "run_id":
        ctx = ctx.model_copy(update={"run_id": "different-run"})
    elif change == "principal":
        ctx = ctx.model_copy(
            update={
                "principal": ctx.principal.model_copy(update={"id": "different"}),
                "scope": ctx.scope.model_copy(update={"principal_id": "different"}),
            }
        )
    elif change == "scope":
        ctx = ctx.model_copy(
            update={"scope": ctx.scope.model_copy(update={"project_id": "different"})}
        )
    elif change == "auth_session":
        ctx = ctx.model_copy(
            update={"principal": ctx.principal.model_copy(update={"auth_session_id": "next"})}
        )
    else:
        name = "capability_policy_ref" if change == "permission" else "model_policy_ref"
        ctx = ctx.model_copy(update={name: getattr(ctx, name).model_copy(update={"version": "v2"})})
    if change == "auth_session":
        # Fixture authorizes either session. Its new full principal still cannot hit.
        await resolve(c, ctx)
        assert c.resolver.format_calls == 2
    else:
        with pytest.raises(DomainError):
            await resolve(c, ctx)
        assert c.resolver.format_calls == 1
    assert c.cache.stats.hits == 0


async def test_digestless_snapshot_bypasses_and_invalid_reading_hash_rejects():
    c = await cached_ready(count=False)
    await resolve(c)
    pin = {name: value for name, value in c.pin.items() if name != "content_hash"}
    await resolve(c, pin=pin)
    await resolve(c, pin=pin)
    assert c.resolver.format_calls == 3 and c.cache.stats.hits == 0
    c.reader.records[c.original.ref.id] = replace(
        c.original, ref=c.original.ref.model_copy(update={"content_hash": None})
    )
    with pytest.raises(DomainError):
        await resolve(c)


@pytest.mark.parametrize("broken", ["get", "put", "corrupt"])
async def test_cache_faults_recompute_without_swallowing_real_failures(broken):
    class BrokenCache(PureComputationCache):
        def get(self, key):
            if broken == "get":
                raise OSError("controlled cache fault")
            if broken == "corrupt":
                return b"{broken"
            return super().get(key)

        def put(self, key, value):
            if broken == "put":
                raise OSError("controlled cache fault")
            return super().put(key, value)

    c = await cached_ready(storage=BrokenCache(max_entries=32, max_bytes=256000))
    a, b = await resolve(c), await resolve(c)
    assert a == b and c.resolver.format_calls == 2
    c.reader.revoked = True
    with pytest.raises(DomainError):
        await resolve(c)


async def test_counter_version_identity_and_unversioned_opt_out():
    c = await cached_ready()
    await resolve(c)
    assert c.counter.calls == 3
    c.counter.cache_version = "2"
    await resolve(c)
    assert c.counter.calls == 6
    new_counter = CountingCounter()
    c.component.selection.counter = new_counter
    await resolve(c)
    assert new_counter.calls == 3
    new_counter.cache_version = None
    await resolve(c)
    assert new_counter.calls == 9  # Both current and final rechecks recompute.


async def test_pure_counter_failure_propagates_and_cannot_use_previous_counter():
    c = await cached_ready()
    await resolve(c)

    class UnavailableCounter:
        name, cache_version = "controlled", "1"

        def count(self, value):
            raise reject("counter_unavailable", "Controlled estimator unavailable")

    c.component.selection.counter = UnavailableCounter()
    with pytest.raises(DomainError) as caught:
        await resolve(c)
    assert caught.value.failure.code == "counter_unavailable"


def key(number):
    return CacheKey("a" * 64, hashlib.sha256(str(number).encode()).hexdigest())


def test_lru_entry_byte_limits_replacement_clear_and_immutable_bytes():
    storage = cache(max_entries=2, max_bytes=260)
    storage.put(key(1), b"a")
    storage.put(key(2), b"b")
    assert storage.stats.size_bytes == 258 and storage.stats.entries == 2
    assert storage.get(key(1)) == b"a"
    storage.put(key(3), b"c")
    assert storage.get(key(2)) is None and storage.get(key(1)) == b"a"
    assert storage.stats.evictions == 1
    storage.put(key(1), b"xyz")
    assert storage.stats.size_bytes == 260 and storage.stats.entries == 2
    storage.put(key(4), b"x" * 133)  # 128 digest bytes + payload exceeds total budget.
    assert storage.stats.entries == 2
    with pytest.raises(TypeError):
        storage.put(key(4), bytearray(b"x"))
    storage.clear()
    assert storage.stats.entries == storage.stats.size_bytes == 0


async def test_component_eviction_recomputes_same_result_without_authority_change():
    c = await cached_ready(storage=cache(max_entries=1), count=False)
    a = await resolve(c)
    c.models.limit += 1
    await resolve(c)
    c.models.limit -= 1
    b = await resolve(c)
    assert a == b and c.resolver.format_calls == 3 and c.cache.stats.evictions == 2
    assert c.cache.stats.entries == 1


@pytest.mark.parametrize("number", [-1, True, 1.5])
def test_invalid_limits(number):
    with pytest.raises(ValueError):
        PureComputationCache(max_entries=number, max_bytes=256)
    with pytest.raises(ValueError):
        PureComputationCache(max_entries=1, max_bytes=number)


@pytest.mark.parametrize(
    "change",
    [
        "text",
        "kind",
        "trust",
        "required",
        "requirements",
        "ref",
        "scope",
        "run",
        "principal",
        "session",
        "model",
        "permission",
        "algorithm",
        "window",
        "rules",
        "tools",
    ],
)
def test_full_key_metadata_security_and_algorithm_isolation(change):
    storage = cache()
    ctx = context().model_copy(update={"run_id": "run"})
    value = reading("same")
    inputs = {"reading": reading_key(value), "window": 4000, "rules": ["r1"], "tools": [tool()]}
    algorithm = "fixture:v1"
    original = make_key(storage, ctx, algorithm=algorithm, inputs=inputs, readings=(value,))
    if change in ("text", "kind", "trust", "required", "requirements", "ref"):
        updates = {
            "text": {"text": "different"},
            "kind": {"kind": "history"},
            "trust": {"trust": "project"},
            "required": {"required": True},
            "requirements": {"requirement_ids": ("important",)},
            "ref": {"ref": value.ref.model_copy(update={"access_scope": ctx.scope})},
        }
        value = replace(value, **updates[change])
        inputs["reading"] = reading_key(value)
    elif change == "scope":
        ctx = ctx.model_copy(
            update={"scope": ctx.scope.model_copy(update={"capabilities": ("extra",)})}
        )
    elif change == "run":
        ctx = ctx.model_copy(update={"run_id": "other"})
    elif change == "principal":
        ctx = ctx.model_copy(
            update={"principal": ctx.principal.model_copy(update={"kind": "admin"})}
        )
    elif change == "session":
        ctx = ctx.model_copy(
            update={"principal": ctx.principal.model_copy(update={"auth_session_id": "new"})}
        )
    elif change in ("model", "permission"):
        name = "model_policy_ref" if change == "model" else "capability_policy_ref"
        ctx = ctx.model_copy(update={name: getattr(ctx, name).model_copy(update={"version": "v2"})})
    elif change == "algorithm":
        algorithm = "fixture:v2"
    else:
        inputs[change] = {"window": 4001, "rules": ["r2"], "tools": [tool("other")]}[change]
    updated = make_key(storage, ctx, algorithm=algorithm, inputs=inputs, readings=(value,))
    assert original is not None and updated is not None and original != updated
    storage.put(original, b"pure")
    assert lookup(storage, updated) is None


def test_missing_hash_incomplete_key_and_default_disabled():
    value = reading("same")
    storage = cache()
    ctx = context()
    assert (
        make_key(storage, ctx, algorithm="v1", inputs={"bad": object()}, readings=(value,)) is None
    )
    without_hash = replace(value, ref=value.ref.model_copy(update={"content_hash": None}))
    assert make_key(storage, ctx, algorithm="v1", inputs={}, readings=(without_hash,)) is None
    assert (
        make_key(PureComputationCache(), ctx, algorithm="v1", inputs={}, readings=(value,)) is None
    )


def test_cache_does_not_retain_raw_keys_or_source_objects():
    storage = cache()
    value = reading("sensitive原文")
    pin = make_key(storage, context(), algorithm="v1", inputs=reading_key(value), readings=(value,))
    assert pin is not None and "sensitive" not in repr(pin)
    storage.put(pin, json.dumps({"estimated_tokens": 5}).encode())
    assert storage.get(pin) == b'{"estimated_tokens": 5}'


async def test_same_reader_input_counts_are_isolated_across_valid_runs_and_subjects():
    from tests.unit.context.test_components import Control, FixtureModels, FixtureReader
    from uaw.context.contracts import SelectionRequest
    from uaw.context.selection import Selector
    from uaw.context.sources import Guard, SourceResolver

    value = reading("authorized fixture input")

    class RegisteredReader(FixtureReader):
        async def check(self, pin, ctx):
            # Explicit controlled ACL for both fixtures; no production admission claim.
            assert ctx.principal.id in ("user", "other")
            assert ctx.run_id in ("run-one", "run-two")

    counter = CountingCounter()
    storage = cache()
    selector = Selector(
        SourceResolver({"input": RegisteredReader(value)}, Guard(Control())),
        FixtureModels(),
        counter,
        cache=storage,
    )
    request = SelectionRequest(
        candidate_refs=(value.ref,),
        purpose="agent_step",
        model_context_limit=4096,
        output_reserve=256,
        tool_reserve=64,
    )
    ctx = context().model_copy(update={"run_id": "run-one"})
    first = await selector.allocate(request, ctx)
    assert await selector.allocate(request, ctx) == first and counter.calls == 1
    assert await selector.allocate(request, ctx.model_copy(update={"run_id": "run-two"})) == first
    assert counter.calls == 2
    other = ctx.model_copy(
        update={
            "principal": ctx.principal.model_copy(update={"id": "other"}),
            "scope": ctx.scope.model_copy(update={"principal_id": "other"}),
        }
    )
    assert await selector.allocate(request, other) == first and counter.calls == 3
    assert storage.stats.entries == 3


async def test_cache_enabled_failure_bypasses_only_cache():
    class FaultyCache(PureComputationCache):
        @property
        def enabled(self):
            raise OSError("controlled cache fault")

    c = await cached_ready(storage=FaultyCache())
    assert await resolve(c) == await resolve(c)
    assert c.resolver.format_calls == 2 and c.counter.calls == 12
    c.control.cancelled = True
    with pytest.raises(DomainError):
        await resolve(c)


def test_parallel_cache_accounting_stays_bounded():
    from concurrent.futures import ThreadPoolExecutor

    storage = cache(max_entries=4, max_bytes=520)

    def compute(number):
        storage.put(key(number), b"x")
        storage.get(key(number))

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(compute, range(100)))
    assert storage.stats.entries <= 4 and storage.stats.size_bytes <= 520
