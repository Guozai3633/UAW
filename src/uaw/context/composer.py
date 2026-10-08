"""Generic immutable snapshots; all authority comes from explicitly injected ports."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from uaw.context.cache import binding_key
from uaw.context.contracts import (
    CompositionBinding,
    ContextRequest,
    PreparedSnapshot,
    PreservationSpec,
    SelectionRequest,
    digest,
    from_wire,
    matches_pin,
    ref_key,
)
from uaw.context.ports import CompositionAuthority
from uaw.context.repository import ContextRepository, snapshot_hash
from uaw.context.rules import RuleResolver
from uaw.context.selection import Selector
from uaw.context.sources import SourceResolver
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import parse_json, validate_contract


def unique(refs: tuple[Ref, ...]) -> tuple[Ref, ...]:
    return tuple({ref_key(ref): ref for ref in refs}.values())


def preserve_both(one: PreservationSpec, two: PreservationSpec) -> PreservationSpec:
    return PreservationSpec(
        required_refs=unique((*one.required_refs, *two.required_refs)),
        pending_action_refs=unique((*one.pending_action_refs, *two.pending_action_refs)),
        exact_strings=tuple(dict.fromkeys((*one.exact_strings, *two.exact_strings))),
        requirement_ids=tuple(dict.fromkeys((*one.requirement_ids, *two.requirement_ids))),
    )


class Composer:
    def __init__(
        self,
        sources: SourceResolver,
        rules: RuleResolver,
        selector: Selector,
        repository: ContextRepository,
        authority: CompositionAuthority,
    ) -> None:
        self.sources, self.rules, self.selector = sources, rules, selector
        self.repository, self.authority = repository, authority

    async def binding(
        self, request: ContextRequest, ctx: TrustedExecutionContext
    ) -> CompositionBinding:
        await self.sources.guard.check(ctx)
        if ctx.model_policy_ref is None or request.model_policy_ref != ctx.model_policy_ref:
            raise reject("model_policy_conflict", "Build must keep the fixed user policy", 409)
        binding = await self.authority.resolve(request.purpose, ctx)
        if binding.request is not None and binding.request != request:
            raise reject(
                "context_recipe_conflict", "Build differs from current registered recipe", 409
            )
        validate_contract("Revision", binding.epoch)
        if binding.epoch != request.expected_epoch:
            raise reject("context_epoch_conflict", "Context epoch changed", 409)
        await self.authority.verify(binding, ctx)
        await self.sources.guard.check(ctx)
        return binding

    async def build(self, request: ContextRequest, ctx: TrustedExecutionContext) -> dict[str, Any]:
        binding = await self.binding(request, ctx)

        prepared: PreparedSnapshot | None = None

        async def verify() -> None:
            if await self.binding(request, ctx) != binding:
                raise reject("context_dependency_changed", "Composition binding changed", 410)
            if prepared is not None:
                actual = unique(
                    tuple(
                        from_wire(Ref, pin)
                        for pin in (
                            *prepared.snapshot["manifest"]["input_refs"],
                            *prepared.snapshot["manifest"]["dependency_refs"],
                        )
                    )
                )
                for pin in actual:
                    if pin not in (ctx.model_policy_ref, ctx.capability_policy_ref):
                        await self.sources.read(pin, "pinned", ctx)

        async def prepare(identifier: str) -> PreparedSnapshot:
            nonlocal prepared
            prepared = await self.prepare(identifier, request, binding, ctx)
            return prepared

        snapshot = await self.repository.commit(request.wire(), ctx, prepare, verify)
        await self.recheck(snapshot, ctx)
        return snapshot

    async def prepare(
        self,
        identifier: str,
        request: ContextRequest,
        binding: CompositionBinding,
        ctx: TrustedExecutionContext,
    ) -> PreparedSnapshot:
        # Never borrow the understanding rule for a different purpose by default.
        assembly = await self.rules.assemble(binding.rules, ctx)
        cap = await self.sources.read(binding.capability_ref, "pinned", ctx)
        if cap.trust != "platform" or cap.kind != "material":
            raise reject(
                "permission_denied", "Capability data must come from platform authority", 403
            )
        capabilities = parse_json(cap.text)
        validate_contract("ModelToolSet", capabilities)
        if capabilities["run_id"] != ctx.run_id:
            raise reject("permission_denied", "Capability snapshot belongs to another Run", 403)
        models = self.selector.models
        if models is None or ctx.model_policy_ref is None:
            raise CapabilityUnavailable("context.fixed_model_window")
        window = await models.resolve(ctx.model_policy_ref, ctx)
        trusted_preserve = preserve_both(binding.preserve, request.preserve)
        rule_refs = tuple(rule.source_ref for rule in assembly.instructions.rules)
        pins = unique(
            (
                *rule_refs,
                cap.ref,
                *request.source_refs,
                *trusted_preserve.required_refs,
                *trusted_preserve.pending_action_refs,
            )
        )
        protected = preserve_both(
            trusted_preserve,
            PreservationSpec(
                required_refs=(*rule_refs, cap.ref),
                exact_strings=(),
                requirement_ids=(),
                pending_action_refs=(),
            ),
        )
        allocation = await self.selector.allocate(
            SelectionRequest(
                candidate_refs=pins,
                purpose=request.purpose,
                model_context_limit=window.context_limit,
                output_reserve=request.output_reserve,
                tool_reserve=request.tool_reserve,
            ),
            ctx,
            protected,
            cache_boundary={
                "snapshot_id": identifier,
                "request": request.wire(),
                "binding": binding_key(binding),
            },
        )
        for reading in allocation.selected:
            if reading.kind in ("instruction", "skill") and not any(
                matches_pin(ref, reading.ref) for ref in rule_refs
            ):
                raise reject(
                    "permission_denied", "Instruction was not in the resolved rule set", 403
                )
        # Prefix is stable; material remains explicitly tagged data.
        order = {"instruction": 0, "skill": 1, "user_input": 2, "history": 3}
        selected = tuple(sorted(allocation.selected, key=lambda r: order.get(r.kind, 4)))
        blocks = [
            {
                "id": "block-" + ref_key(reading.ref),
                "kind": reading.kind,
                "source_refs": [reading.ref.wire()],
                "content_ref": reading.ref.wire(),
                "estimated_tokens": self.selector.counter.count(reading),
                "required": any(matches_pin(pin, reading.ref) for pin in allocation.preserved),
                "trust": reading.trust,
            }
            for reading in selected
        ]
        instructions = assembly.instructions.wire()
        instruction_ref = {
            "kind": "rule",
            "id": identifier,
            "version": "1",
            "content_hash": digest(instructions),
        }
        snapshot: dict[str, Any] = {
            "id": identifier,
            "epoch": binding.epoch,
            "purpose": request.purpose,
            "blocks": blocks,
            "instruction_set_ref": instruction_ref,
            "capability_snapshot_ref": cap.ref.wire(),
            "input_tokens": allocation.input_tokens,
            "output_reserve": request.output_reserve,
            "tool_reserve": request.tool_reserve,
            "omitted_refs": [r.ref.wire() for r in allocation.omitted],
            "compressed_refs": [],
        }
        extra_dependencies = tuple(
            [(await self.sources.read(pin, "pinned", ctx)).ref for pin in binding.dependency_refs]
        )
        dependencies = unique(
            (
                *assembly.dependencies,
                cap.ref,
                *extra_dependencies,
                ctx.capability_policy_ref,
                request.model_policy_ref,
            )
        )
        snapshot["manifest"] = {
            "version": "ms-c2",
            "input_refs": [r.ref.wire() for r in selected],
            "dependency_refs": [pin.wire() for pin in dependencies],
            "content_hash": "0" * 64,
        }
        # Count the complete envelope, including manifest and escaped source text.
        # +64 bounds the numeric-count field growing after serialization.
        envelope = {
            "snapshot": snapshot,
            "instructions": instructions,
            "capabilities": capabilities,
            "text_blocks": [{"ref": r.ref.wire(), "text": r.text} for r in selected],
        }
        serialized = len(json.dumps(envelope, ensure_ascii=False).encode("utf-8")) + 64
        snapshot["input_tokens"] = max(allocation.input_tokens, serialized)
        if (
            snapshot["input_tokens"]
            + request.output_reserve
            + request.tool_reserve
            + window.serialization_reserve
            > window.context_limit
        ):
            raise reject("context_insufficient", "Serialized context does not fit", 422, "budget")
        snapshot["manifest"]["content_hash"] = snapshot_hash(snapshot)
        validate_contract("ContextSnapshot", snapshot)
        references = tuple(
            {
                "ref": r.ref.wire(),
                "title": f"{r.ref.kind}:{r.ref.id}",
                "content_ref": r.ref.wire(),
                "retrieved_at": datetime.now(UTC).isoformat(),
                "provenance_refs": [r.ref.wire()],
                "access_scope": ctx.scope.wire(),
            }
            for r in selected
        )
        for ref in (*assembly.dependencies, *binding.dependency_refs):
            await self.sources.recheck(ref, ctx)
        for r in allocation.selected:
            await self.sources.recheck(r.ref, ctx)
        await self.authority.verify(binding, ctx)
        return PreparedSnapshot(snapshot, instructions, references, request.wire())

    async def recheck(self, snapshot: dict[str, Any], ctx: TrustedExecutionContext) -> None:
        await self.sources.guard.check(ctx)
        instructions = await self.repository.instructions(snapshot, ctx)
        binding = await self.authority.resolve(snapshot["purpose"], ctx)
        if binding.epoch != snapshot["epoch"] or not matches_pin(
            binding.capability_ref, from_wire(Ref, snapshot["capability_snapshot_ref"])
        ):
            raise reject("context_dependency_changed", "Snapshot epoch/capabilities are stale", 410)
        await self.authority.verify(binding, ctx)
        current = await self.rules.assemble(binding.rules, ctx)
        if current.instructions.wire() != instructions:
            raise reject("context_dependency_changed", "Snapshot rules changed", 410)
        models = self.selector.models
        if models is None or ctx.model_policy_ref is None:
            raise CapabilityUnavailable("context.fixed_model_window")
        deps = tuple(from_wire(Ref, r) for r in snapshot["manifest"]["dependency_refs"])
        if not any(ref == ctx.model_policy_ref for ref in deps) or not any(
            ref == ctx.capability_policy_ref for ref in deps
        ):
            raise reject(
                "context_dependency_changed", "Snapshot model/permission policy changed", 410
            )
        window = await models.resolve(ctx.model_policy_ref, ctx)
        if (
            window.policy_ref != ctx.model_policy_ref
            or snapshot["input_tokens"]
            + snapshot["output_reserve"]
            + snapshot["tool_reserve"]
            + window.serialization_reserve
            > window.context_limit
        ):
            raise reject(
                "context_insufficient", "Stored context exceeds the current window", 422, "budget"
            )
        for ref in deps:
            if ref not in (ctx.model_policy_ref, ctx.capability_policy_ref):
                await self.sources.read(ref, "pinned", ctx)
        saved_request = from_wire(
            ContextRequest, await self.repository.request(snapshot["id"], ctx)
        )
        if saved_request.model_policy_ref != ctx.model_policy_ref:
            raise reject("context_dependency_changed", "Saved user model policy changed", 410)
        required = preserve_both(saved_request.preserve, binding.preserve)
        allocation = await self.selector.allocate(
            SelectionRequest(
                candidate_refs=tuple(from_wire(Ref, b["content_ref"]) for b in snapshot["blocks"]),
                purpose=snapshot["purpose"],
                model_context_limit=window.context_limit,
                output_reserve=snapshot["output_reserve"],
                tool_reserve=snapshot["tool_reserve"],
            ),
            ctx,
            required,
            cache_boundary={
                "snapshot": snapshot,
                "request": saved_request.wire(),
                "binding": binding_key(binding),
                "instructions": instructions,
            },
        )
        if allocation.omitted:
            raise reject(
                "context_insufficient", "Saved input cannot be fully reloaded", 422, "budget"
            )
        readings = {ref_key(r.ref): r for r in allocation.selected}
        for block in snapshot["blocks"]:
            reading = readings.get(ref_key(from_wire(Ref, block["content_ref"])))
            if reading is None or reading.kind != block["kind"] or reading.trust != block["trust"]:
                raise reject("snapshot_changed", "Input origin classification changed", 410)
            if (
                reading.required or reading.kind in ("instruction", "skill", "user_input")
            ) and not block["required"]:
                raise reject("snapshot_changed", "Required input protection changed", 410)
        await self.sources.guard.check(ctx)
