"""Public ModelInputPort adapter for generic fixed Context snapshots.

ModelPrompt.tools retains the approved ToolSpec objects expected by the published
Model consumer. Only the provider adapter converts them to native function calls.
This module does not send requests, grant tool access, or use an Intent template.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from uaw.context.cache import (
    PureComputationCache,
    binding_key,
    cache_enabled,
    lookup,
    make_key,
    reading_key,
    remember,
    window_key,
)
from uaw.context.composer import Composer
from uaw.context.contracts import InstructionSet, Reading, from_wire, matches_pin, ref_key
from uaw.model.contracts import ModelPrompt
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import ContractViolation, parse_json, validate_contract


def serialize(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


class GenericModelInputs:
    """Inject the same Composer/Reader/authority as generic Context construction.

    Every resolution reloads persisted records and live sources. Optional caching
    only reuses formatting/serialization/estimation after current validation.
    Missing Composer/authority/capability Reader fails explicitly. operation_id
    may differ from the build operation; the snapshot remains bound to Run/scope.
    """

    def __init__(
        self, composer: Composer | None, *, cache: PureComputationCache | None = None
    ) -> None:
        self.composer = composer
        self.cache = cache

    async def resolve(self, ref: dict[str, Any], ctx: TrustedExecutionContext) -> ModelPrompt:
        if self.composer is None:
            raise CapabilityUnavailable("context.generic_model_input_authority")
        try:
            async with asyncio.timeout(max(0, self.composer.sources.guard.remaining(ctx))):
                await self.composer.sources.guard.check(ctx)
                pin = from_wire(Ref, ref)
                prompt = await self._resolve(pin, ctx, self.composer)
                await self.composer.sources.guard.check(ctx)
                return prompt
        except ContractViolation, ValueError, TypeError:
            # Contract errors never disclose original material or model configuration.
            raise reject("context_model_input_invalid", "Invalid fixed Context input") from None
        except TimeoutError:
            raise reject(
                "deadline_exceeded", "Context input deadline expired", 422, "timeout"
            ) from None
        except asyncio.CancelledError:
            raise reject(
                "cancelled", "Context input resolution cancelled", 422, "cancelled"
            ) from None

    async def _resolve(
        self, pin: Ref, ctx: TrustedExecutionContext, composer: Composer
    ) -> ModelPrompt:
        sources = composer.sources
        snapshot = await composer.repository.load_snapshot(pin, ctx)
        await composer.recheck(snapshot, ctx)
        binding = await composer.authority.resolve(snapshot["purpose"], ctx)
        await composer.authority.verify(binding, ctx)
        saved = await composer.repository.request(snapshot["id"], ctx)
        if (
            any(
                saved[name] != snapshot[name]
                for name in ("purpose", "output_reserve", "tool_reserve")
            )
            or saved["expected_epoch"] != snapshot["epoch"]
        ):
            raise reject("snapshot_changed", "Snapshot request boundary changed", 410)
        if snapshot["compressed_refs"]:
            raise CapabilityUnavailable("context.verified_compressed_input")

        instructions = from_wire(
            InstructionSet, await composer.repository.instructions(snapshot, ctx)
        )
        if instructions.conflict_refs:
            raise reject("rule_conflict", "Unresolved instructions cannot be sent", 409, "conflict")
        readings: dict[str, Reading] = {}
        for block in snapshot["blocks"]:
            content_ref = from_wire(Ref, block["content_ref"])
            reading = await sources.read(content_ref, "pinned", ctx)
            key = ref_key(reading.ref)
            if (
                key in readings
                or block["source_refs"] != [reading.ref.wire()]
                or reading.kind != block["kind"]
                or reading.trust != block["trust"]
                or reading.ref.wire() != block["content_ref"]
            ):
                raise reject(
                    "snapshot_changed", "Fixed block identity or classification changed", 410
                )
            readings[key] = reading
        if snapshot["manifest"]["input_refs"] != [
            block["content_ref"] for block in snapshot["blocks"]
        ]:
            raise reject("snapshot_changed", "Manifest does not match the actual input blocks", 410)

        capability_ref = from_wire(Ref, snapshot["capability_snapshot_ref"])
        capability = await sources.read(capability_ref, "pinned", ctx)
        if capability.kind != "material" or capability.trust != "platform":
            raise reject("permission_denied", "Capability source is not platform data", 403)
        if ref_key(capability.ref) not in readings:
            raise reject("snapshot_changed", "Capability source is absent from fixed blocks", 410)
        tool_set = parse_json(capability.text)
        validate_contract("ModelToolSet", tool_set)
        if tool_set["run_id"] != ctx.run_id:
            raise reject("permission_denied", "Tool set belongs to a different Run", 403)
        tools = tuple(tool_set["tools"])
        names: set[str] = set()
        for tool in tools:
            if tool["id"] in names:
                raise reject("tool_set_conflict", "Tool names are not unique in this snapshot", 409)
            names.add(tool["id"])
            if not set(tool["required_capabilities"]).issubset(ctx.scope.capabilities):
                raise reject("permission_denied", "Tool exceeds current trusted capabilities", 403)
        # Current flags, provider/role/resource eligibility remain authority-owned.
        # A missing live Reader/authority never becomes an empty tool set.

        rule_sources: set[str] = set()
        for rule in instructions.rules:
            rule_reading = readings.get(ref_key(rule.source_ref))
            if (
                rule_reading is None
                or rule_reading.text != rule.text
                or rule_reading.kind not in ("instruction", "skill", "user_input")
            ):
                raise reject("snapshot_changed", "An effective rule has no exact read block", 410)
            rule_sources.add(ref_key(rule_reading.ref))
            if rule.level in ("platform", "capability_policy") and rule_reading.trust != "platform":
                raise reject(
                    "permission_denied", "Non-platform rule cannot be a system message", 403
                )
        for reading in readings.values():
            if ref_key(reading.ref) in rule_sources or reading.ref == capability.ref:
                continue
            if reading.kind in ("instruction", "skill"):
                raise reject("permission_denied", "Unresolved rule cannot enter the prompt", 403)
            if reading.kind == "user_input" and reading.trust != "user":
                raise reject("permission_denied", "Original input must retain user identity", 403)

        dependencies = tuple(
            from_wire(Ref, value) for value in snapshot["manifest"]["dependency_refs"]
        )
        for required in (*binding.dependency_refs, capability.ref):
            if not any(matches_pin(required, actual) for actual in dependencies):
                raise reject(
                    "context_dependency_changed", "Current dependency is not in manifest", 410
                )
        models = composer.selector.models
        if models is None or ctx.model_policy_ref is None:
            raise CapabilityUnavailable("context.fixed_model_window")
        window = await models.resolve(ctx.model_policy_ref, ctx)
        await sources.guard.check(ctx)
        if (
            window.policy_ref != ctx.model_policy_ref
            or type(window.context_limit) is not int
            or window.context_limit < 1
            or type(window.max_output_tokens) is not int
            or window.max_output_tokens < 1
            or type(window.serialization_reserve) is not int
            or window.serialization_reserve < 0
        ):
            raise reject("model_policy_conflict", "Fixed model window is invalid or changed", 409)
        computation_key = None
        if cache_enabled(self.cache):
            computation_key = make_key(
                self.cache,
                ctx,
                algorithm="generic-model-input-format:utf8-envelope-64:v1",
                inputs={
                    "formatter": type(self).__module__ + "." + type(self).__qualname__,
                    "snapshot_ref": pin.wire(),
                    "snapshot": snapshot,
                    "request": saved,
                    "binding": binding_key(binding),
                    "instructions": instructions.wire(),
                    "readings": [reading_key(r) for r in readings.values()],
                    "capability": reading_key(capability),
                    "tools": tools,
                    "window": window_key(window),
                },
                readings=(*readings.values(), capability),
                pins=(pin,),
            )
        cached = lookup(self.cache, computation_key)
        pure = None
        if cached is not None:
            try:
                candidate = json.loads(cached)
                if (
                    isinstance(candidate, dict)
                    and set(candidate) == {"messages", "estimated_tokens"}
                    and isinstance(candidate["messages"], list)
                    and all(
                        isinstance(m, dict)
                        and set(m) == {"role", "content"}
                        and m["role"] in ("user", "system")
                        and isinstance(m["content"], str)
                        for m in candidate["messages"]
                    )
                    and type(candidate["estimated_tokens"]) is int
                    and candidate["estimated_tokens"] >= snapshot["input_tokens"]
                ):
                    pure = candidate
            except ValueError, TypeError:
                pass
        if pure is None:
            messages, estimate = self._format(instructions, readings, capability, tools, snapshot)
            pure = {"messages": messages, "estimated_tokens": estimate}
            if computation_key is not None:
                remember(self.cache, computation_key, serialize(pure).encode("utf-8"))
        messages, estimate = pure["messages"], pure["estimated_tokens"]
        if (
            not 1 <= snapshot["output_reserve"] <= window.max_output_tokens
            or estimate
            + snapshot["output_reserve"]
            + snapshot["tool_reserve"]
            + window.serialization_reserve
            > window.context_limit
        ):
            raise reject(
                "context_insufficient", "Complete messages and tools do not fit", 422, "budget"
            )

        # Recheck after every awaited source/model lookup and serialization. Reader
        # cooperation cannot make external ACL changes atomic with later dispatch.
        await composer.recheck(snapshot, ctx)
        current = await composer.authority.resolve(snapshot["purpose"], ctx)
        await composer.authority.verify(current, ctx)
        if current != binding:
            raise reject("context_dependency_changed", "Composition changed during input read", 410)
        if await models.resolve(ctx.model_policy_ref, ctx) != window:
            raise reject("model_policy_conflict", "Model window changed during input read", 409)
        await sources.guard.check(ctx)
        return ModelPrompt(tuple(messages), tools, estimate)

    @staticmethod
    def _format(
        instructions: InstructionSet,
        readings: dict[str, Reading],
        capability: Reading,
        tools: tuple[dict[str, Any], ...],
        snapshot: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], int]:
        """Pure formatting of already validated data; never Reader/authority lookup."""
        messages: list[dict[str, Any]] = []
        rule_sources: set[str] = set()
        for rule in instructions.rules:
            reading = readings[ref_key(rule.source_ref)]
            rule_sources.add(ref_key(reading.ref))
            if rule.level in ("platform", "capability_policy"):
                messages.append({"role": "system", "content": reading.text})
            elif rule.level == "user_current":
                messages.append({"role": "user", "content": reading.text})
            else:
                messages.append(
                    {
                        "role": "user",
                        "content": serialize(
                            {
                                "context_kind": "registered_instruction",
                                "level": rule.level,
                                "source_ref": reading.ref.wire(),
                                "scope": rule.scope.wire(),
                                "text": reading.text,
                            }
                        ),
                    }
                )
        for reading in readings.values():
            if ref_key(reading.ref) in rule_sources or reading.ref == capability.ref:
                continue
            if reading.kind == "user_input":
                messages.append({"role": "user", "content": reading.text})
            else:
                # History/material/tool data retain source identity, never provider roles.
                messages.append(
                    {
                        "role": "user",
                        "content": serialize(
                            {
                                "context_kind": "data",
                                "kind": reading.kind,
                                "trust": reading.trust,
                                "source_refs": [reading.ref.wire()],
                                "text": reading.text,
                            }
                        ),
                    }
                )
        estimate = max(
            snapshot["input_tokens"],
            len(serialize({"messages": messages, "tools": tools}).encode("utf-8"))
            + 64 * (len(messages) + len(tools) + 1),
        )
        return messages, estimate
