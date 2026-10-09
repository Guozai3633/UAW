"""Composition from actual persisted recipes and current Run-owned originals."""

from __future__ import annotations

import hashlib

from uaw.context.contracts import CompositionBinding, PreservationSpec
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
        recipe, original = await self.inputs.inspect(ctx)
        if recipe.request.preserve.requirement_ids or recipe.request.preserve.pending_action_refs:
            raise CapabilityUnavailable("context.registered_requirement_or_action_source")
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
