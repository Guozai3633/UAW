"""Composition from actual persisted recipes and current Run-owned originals."""

from __future__ import annotations

import hashlib

from uaw.context.contracts import CompositionBinding, PreservationSpec, matches_pin
from uaw.context.model_input import serialize
from uaw.context.registered import RegisteredContextInputs
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject


class RegisteredCompositionAuthority:
    def __init__(self, inputs: RegisteredContextInputs) -> None:
        self.inputs = inputs

    async def resolve(self, purpose: str, ctx: TrustedExecutionContext) -> CompositionBinding:
        if purpose != "agent_step":
            raise CapabilityUnavailable("context.registered_purpose")
        recipe = await self.inputs.recipe(ctx)
        original = await self.inputs.current(ctx)
        if any(
            not any(matches_pin(pin, saved) for saved in recipe.request.source_refs)
            for pin in original
        ):
            raise reject(
                "context_dependency_changed",
                "Admitted originals/patches need a revised recipe",
                410,
            )
        for pin in (*recipe.request.source_refs, *recipe.rules.user_instruction_refs):
            await self.inputs.read(pin, ctx)
        if recipe.request.preserve.requirement_ids or recipe.request.preserve.pending_action_refs:
            raise CapabilityUnavailable("context.registered_requirement_or_action_source")
        if await self.inputs.recipe(ctx) != recipe or await self.inputs.current(ctx) != original:
            raise reject(
                "context_dependency_changed", "Recipe/source set changed during resolve", 410
            )
        tools_text = serialize(recipe.tools.wire())
        capability = Ref(
            kind="configuration",
            id=recipe.ref.id,
            version=recipe.ref.version,
            content_hash=hashlib.sha256(tools_text.encode("utf-8")).hexdigest(),
        )
        preserve = PreservationSpec(
            required_refs=tuple(dict.fromkeys((*original, *recipe.request.preserve.required_refs))),
            exact_strings=recipe.request.preserve.exact_strings,
            requirement_ids=(),
            pending_action_refs=(),
        )
        return CompositionBinding(
            recipe.request.expected_epoch,
            recipe.rules,
            capability,
            preserve,
            request=recipe.request,
        )

    async def verify(self, binding: CompositionBinding, ctx: TrustedExecutionContext) -> None:
        if binding != await self.resolve("agent_step", ctx):
            raise reject("context_dependency_changed", "Current registered binding changed", 410)
