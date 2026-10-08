"""Protect required input before choosing optional sources; never rewrite text."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from uaw.context.cache import (
    PureComputationCache,
    cache_enabled,
    lookup,
    make_key,
    reading_key,
    remember,
    window_key,
)
from uaw.context.contracts import (
    Allocation,
    PreservationSpec,
    Reading,
    SelectionRequest,
    SourcesRequest,
    from_wire,
    ref_key,
)
from uaw.context.ports import ModelWindowProvider, TokenCounter
from uaw.context.sources import SourceResolver, component_result
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract


class ConservativeTokenCounter:
    """Serialized block UTF-8 byte count + 64. Estimate only, not a provider tokenizer.

    The Model adapter supplies an additional envelope reserve. The final Model
    gateway must recount its actual serialized request before sending it.
    """

    name = "utf8_bytes_plus_64_estimate"
    cache_version = "1"

    def count(self, reading: Reading) -> int:
        block = {
            "source_ref": reading.ref.wire(),
            "kind": reading.kind,
            "trust": reading.trust,
            "text": reading.text,
        }
        return len(json.dumps(block, ensure_ascii=False).encode("utf-8")) + 64


class Selector:
    def __init__(
        self,
        sources: SourceResolver,
        models: ModelWindowProvider | None,
        counter: TokenCounter | None = None,
        *,
        cache: PureComputationCache | None = None,
    ) -> None:
        self.sources = sources
        self.models = models
        self.counter = counter or ConservativeTokenCounter()
        self.cache = cache
        self._counter_identity = uuid4().hex
        self._keyed_counter = self.counter

    async def allocate(
        self,
        request: SelectionRequest,
        ctx: TrustedExecutionContext,
        preserve: PreservationSpec | None = None,
        *,
        cache_boundary: dict[str, Any] | None = None,
    ) -> Allocation:
        await self.sources.guard.check(ctx)
        if self.models is None or ctx.model_policy_ref is None:
            raise CapabilityUnavailable("context.fixed_model_window")
        window = await self.models.resolve(ctx.model_policy_ref, ctx)
        await self.sources.guard.check(ctx)
        if window.policy_ref != ctx.model_policy_ref:
            raise reject("model_policy_conflict", "Model adapter changed the fixed policy", 409)
        if (
            window.context_limit < 1
            or window.max_output_tokens < 1
            or window.serialization_reserve < 0
        ):
            raise CapabilityUnavailable("context.validated_model_window")
        if request.model_context_limit != window.context_limit:
            raise reject("model_window_conflict", "Requested window differs from fixed model", 409)
        if request.output_reserve < 1 or request.output_reserve > window.max_output_tokens:
            raise reject(
                "context_insufficient", "Valid output space must be reserved", 422, "budget"
            )
        budget = (
            window.context_limit
            - request.output_reserve
            - request.tool_reserve
            - window.serialization_reserve
        )
        if budget < 0:
            raise reject("context_insufficient", "Reserves exceed model window", 422, "budget")
        readings = await self.sources.resolve(
            SourcesRequest(
                source_refs=request.candidate_refs,
                purpose=request.purpose,
                source_revision_policy="pinned",
            ),
            ctx,
        )
        mandatory = {
            ref_key(r.ref)
            for r in readings
            if r.required or r.kind in ("user_input", "instruction", "skill")
        }
        if preserve is not None:
            required = {
                ref_key(ref) for ref in (*preserve.required_refs, *preserve.pending_action_refs)
            }
            # Ref comparison is against the input pin, whose omitted hash may be enriched.
            matched: set[str] = set()
            by_pin = {(r.ref.kind, r.ref.id, r.ref.version, r.ref.location): r for r in readings}
            for ref in (*preserve.required_refs, *preserve.pending_action_refs):
                reading = by_pin.get((ref.kind, ref.id, ref.version, ref.location))
                if reading is not None and (
                    ref.content_hash is None or ref.content_hash == reading.ref.content_hash
                ):
                    mandatory.add(ref_key(reading.ref))
                    matched.add(ref_key(ref))
            if required - matched:
                raise reject(
                    "dependency_missing", "A protected source was not read", 404, "dependency"
                )
            for exact in preserve.exact_strings:
                matches = [r for r in readings if exact in r.text]
                if not matches:
                    raise reject(
                        "dependency_missing", "Protected exact text is absent", 404, "dependency"
                    )
                mandatory.add(ref_key(matches[0].ref))
            for requirement in preserve.requirement_ids:
                matches = [r for r in readings if requirement in r.requirement_ids]
                if not matches:
                    raise CapabilityUnavailable("context.verified_requirement_binding")
                mandatory.update(ref_key(r.ref) for r in matches)
        # All current Reader/model/preservation checks above precede pure estimates.
        if cache_enabled(self.cache):
            boundary = {
                "selection": request.wire(),
                "preserve": preserve.wire() if preserve is not None else None,
                "window": window_key(window),
                "composition": cache_boundary,
                "readings": [reading_key(r) for r in readings],
            }
            costs = {ref_key(r.ref): self._count(r, ctx, boundary) for r in readings}
        else:
            costs = {ref_key(r.ref): self.counter.count(r) for r in readings}
        if any(type(cost) is not int or cost < 0 for cost in costs.values()):
            raise reject("schema_invalid", "Token counter returned invalid counts")
        protected = [r for r in readings if ref_key(r.ref) in mandatory]
        used = sum(costs[ref_key(r.ref)] for r in protected)
        if used > budget:
            raise reject("context_insufficient", "Protected input does not fit", 422, "budget")
        selected_keys = set(mandatory)
        # Caller supplies purpose-relevant candidates. Do not invent semantic scores.
        trust_order = {"platform": 0, "user": 1, "project": 2, "external": 3}
        optional = sorted(
            (r for r in readings if ref_key(r.ref) not in mandatory),
            key=lambda r: trust_order[r.trust],
        )
        for reading in optional:
            cost = costs[ref_key(reading.ref)]
            if used + cost <= budget:
                selected_keys.add(ref_key(reading.ref))
                used += cost
        for reading in readings:
            await self.sources.recheck(reading.ref, ctx)
        result = Allocation(
            selected=tuple(r for r in readings if ref_key(r.ref) in selected_keys),
            omitted=tuple(r for r in readings if ref_key(r.ref) not in selected_keys),
            input_budget=budget,
            input_tokens=used,
            estimation=self.counter.name,
            preserved=tuple(r.ref for r in protected),
        )
        validate_contract("SelectionResult", result.wire())
        return result

    def _count(
        self, reading: Reading, ctx: TrustedExecutionContext, boundary: dict[str, Any]
    ) -> int:
        # Custom counters opt in with a stable cache_version covering all parameters.
        # Retain per-instance identity; replacement cannot reuse another counter's count.
        if self._keyed_counter is not self.counter:
            self._counter_identity = uuid4().hex
            self._keyed_counter = self.counter
        try:
            version = getattr(self.counter, "cache_version", None)
        except Exception:
            version = None
        key = None
        if isinstance(version, str) and version:
            key = make_key(
                self.cache,
                ctx,
                algorithm="selection-token-estimate:v1",
                inputs={
                    "counter": {
                        "type": (
                            type(self.counter).__module__ + "." + type(self.counter).__qualname__
                        ),
                        "name": self.counter.name,
                        "identity": self._counter_identity,
                        "version": version,
                    },
                    "reading": reading_key(reading),
                    "boundary": boundary,
                },
                readings=(reading,),
            )
        cached = lookup(self.cache, key)
        if cached is not None:
            try:
                value = json.loads(cached)
                if type(value) is int and value >= 0:
                    return value
            except ValueError, TypeError:
                pass
        value = self.counter.count(reading)
        if type(value) is int and value >= 0:
            remember(self.cache, key, str(value).encode("ascii"))
        return value

    async def handle(self, request: dict[str, Any], ctx: TrustedExecutionContext) -> dict[str, Any]:
        async def operation() -> dict[str, Any]:
            validate_contract("InternalContextSelectionRequest", request)
            allocation = await self.allocate(
                from_wire(SelectionRequest, request["parameters"]), ctx
            )
            return {
                "kind": "ok",
                "payload": {"action": request["action"], "result": allocation.wire()},
                "output_refs": [],
            }

        return await component_result(
            "ComponentContextSelectionResult", ctx, self.sources.guard, operation
        )
