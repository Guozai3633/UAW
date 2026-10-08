"""Trusted Context registration over named SQL records and owner-isolated blobs.

These methods are internal. authenticated_service comes from a trusted adapter,
not HTTP/model data. The complete controller Principal is fixed in composition.
No blob/record here grants Run/Tool permissions or chooses another user model.
"""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Awaitable, Callable, Coroutine
from dataclasses import dataclass
from functools import wraps
from typing import Any

from uaw.context.contracts import (
    BlockKind,
    ContextRequest,
    InstructionRule,
    ModelToolSet,
    PreservationSpec,
    Reading,
    RulesRequest,
    Trust,
    digest,
    from_wire,
    matches_pin,
)
from uaw.context.model_input import serialize
from uaw.context.ports import RegisteredRunSource, RegisteredToolValidator
from uaw.context.sources import Guard
from uaw.infrastructure.db.models import utcnow
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore
from uaw.shared.contracts import Principal, Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import BlobStorePort, Record, RecordStorePort, StoreConflict, StoreMissing

MATERIALS = "context.registered.materials"
RULES = "context.registered.rules"
RECIPES = "context.registered.recipes"
RECIPE_RULES = "context.registered.recipe_rules"
TOOLS = "context.registered.tools"
BINDINGS = "context.registered.bindings"
CATALOG = "context.registered.catalog"
SEALS = "context.registered.seals"
REVOKED = "context.registered.revoked"
MAX_TEXT_BYTES = 65536
MAX_ENTRIES = 64
MAX_REQUEST_BYTES = 262144


def identity(ctx: TrustedExecutionContext) -> dict[str, Any]:
    value = ctx.wire()
    for name in ("operation_id", "trace_id", "attempt_id", "deadline", "budget_reservation_ref"):
        value.pop(name, None)
    return value


def recipe_id(ctx: TrustedExecutionContext) -> str:
    return "recipe-" + digest({"run": ctx.run_id, "purpose": "agent_step"})


def material_id(ctx: TrustedExecutionContext) -> str:
    return "material-" + digest({"run": ctx.run_id, "operation": ctx.operation_id})


def numeric(ref: Ref) -> int:
    if (
        not ref.version.isascii()
        or not ref.version.isdigit()
        or not 1 <= int(ref.version) <= 2147483647
    ):
        raise reject("context_reference_invalid", "Expected a fixed positive revision")
    return int(ref.version)


def bounded[**P, T](
    method: Callable[P, Coroutine[Any, Any, T]],
) -> Callable[P, Coroutine[Any, Any, T]]:
    """One deadline for a public operation; underlying cancellation still propagates."""

    @wraps(method)
    async def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
        ctx = next(
            (
                value
                for value in (*args, *kwargs.values())
                if isinstance(value, TrustedExecutionContext)
            ),
            None,
        )
        if ctx is None:
            raise reject("context_registration_invalid", "Trusted execution context is required")
        try:
            async with asyncio.timeout(max(0, Guard.remaining(ctx))):
                return await method(*args, **kwargs)
        except TimeoutError:
            raise reject(
                "deadline_exceeded", "Context source deadline expired", 422, "timeout"
            ) from None

    return wrapped


@dataclass(frozen=True)
class RegisteredRecipe:
    ref: Ref
    request: ContextRequest
    rules: RulesRequest
    tools: ModelToolSet
    owner: TrustedExecutionContext


class RegisteredContextInputs:
    def __init__(
        self,
        *,
        controller: Principal,
        records: RecordStorePort,
        blobs: BlobStorePort,
        transactions: TransactionalStore,
        runs: RegisteredRunSource | None,
        tool_validator: RegisteredToolValidator | None = None,
    ) -> None:
        validate_contract("Principal", controller.wire())
        if controller.kind != "service":
            raise ValueError("Context controller must be a service Principal")
        self.controller, self.records, self.blobs = controller, records, blobs
        self.transactions, self.runs, self.tool_validator = transactions, runs, tool_validator
        self.guard = Guard(runs)

    async def _access(self, ctx: TrustedExecutionContext) -> tuple[Record, Record]:
        await self.guard.check(ctx)
        if self.runs is None:
            raise CapabilityUnavailable("context.registered_run_source")
        await self.runs.authorize(ctx)
        if not ctx.run_id or not ctx.scope.conversation_id or ctx.model_policy_ref is None:
            raise CapabilityUnavailable("context.registered_admitted_run")
        binding = await self.records.get(ctx.principal, "run.bindings", ctx.run_id)
        validate_contract("RunAdmissionBinding", binding.payload)
        if (
            binding.schema_name != "RunAdmissionBinding"
            or binding.payload["model_policy_ref"] != ctx.model_policy_ref.wire()
        ):
            raise reject("model_policy_conflict", "Fixed Run model binding changed", 409)
        state = await self.records.get(ctx.principal, "run.input_sets", ctx.run_id)
        validate_contract("RunInputState", state.payload)
        if (
            state.schema_name != "RunInputState"
            or state.payload["run_id"] != ctx.run_id
            or state.payload["conversation_id"] != ctx.scope.conversation_id
            or state.payload["original_input_ref"] != binding.payload["input_ref"]
        ):
            raise reject("source_changed", "Admitted source set changed", 410)
        return binding, state

    @bounded
    async def current(self, ctx: TrustedExecutionContext) -> tuple[Ref, ...]:
        before = await self._access(ctx)
        state = before[1]
        assert self.runs is not None
        if len(state.payload["patch_refs"]) >= MAX_ENTRIES:
            raise reject(
                "context_registration_too_large", "Run exceeds protected source bounds", 413
            )
        pins = []
        for data in (state.payload["original_input_ref"], *state.payload["patch_refs"]):
            requested = from_wire(Ref, data)
            reading = await self.runs.read(requested, "pinned", ctx)
            if (
                not matches_pin(requested, reading.ref)
                or reading.kind != "user_input"
                or reading.trust != "user"
                or not reading.required
                or reading.ref.content_hash
                != hashlib.sha256(reading.text.encode("utf-8")).hexdigest()
            ):
                raise reject("source_changed", "Run source lost its original identity", 410)
            pins.append(reading.ref)
        if await self._access(ctx) != before:
            raise reject("source_changed", "Run bindings changed during source read", 410)
        return tuple(pins)

    async def _service(self, actor: Principal, ctx: TrustedExecutionContext) -> tuple[Ref, ...]:
        validate_contract("Principal", actor.wire())
        if actor != self.controller:
            raise reject("permission_denied", "Registration controller differs", 403)
        return await self.current(ctx)

    @staticmethod
    def _meta(expected: int, meta: RequestMeta) -> None:
        validate_contract("RequestMeta", meta.wire())
        if (
            type(expected) is not int
            or not 0 <= expected < 2147483647
            or (meta.expected_revision is not None and meta.expected_revision != expected)
        ):
            raise reject("context_revision_invalid", "Registration revision boundary differs", 409)

    @staticmethod
    def _capacity(value: object) -> None:
        if len(serialize(value).encode("utf-8")) > MAX_REQUEST_BYTES:
            raise reject("context_registration_too_large", "Registration exceeds 256 KiB", 413)

    async def _owner(
        self, identifier: str, ctx: TrustedExecutionContext
    ) -> TrustedExecutionContext:
        row = await self.records.get(ctx.principal, BINDINGS, identifier)
        if row.schema_name != "TrustedExecutionContext":
            raise reject("source_changed", "Registration owner metadata changed", 410)
        owner = from_wire(TrustedExecutionContext, row.payload)
        if identity(owner) != identity(ctx):
            raise reject(
                "permission_denied", "Registration is outside its full owner/Run/scope", 403
            )
        return owner

    async def _seal(
        self,
        identifier: str,
        revision: int,
        entries: tuple[tuple[str, str, dict[str, Any]], ...],
        ctx: TrustedExecutionContext,
    ) -> None:
        row = await self.records.get(ctx.principal, SEALS, identifier)
        expected = Ref(
            kind="content",
            id=identifier,
            version=str(revision),
            content_hash=digest({"entries": entries, "owner": identity(ctx)}),
        )
        if (
            row.schema_name != "Ref"
            or row.revision != revision
            or from_wire(Ref, row.payload) != expected
        ):
            raise reject("source_changed", "Registered payload/metadata integrity changed", 410)

    async def _catalog(
        self, tx: RecordTransaction, identifier: str, pin: Ref, ctx: TrustedExecutionContext
    ) -> None:
        key = recipe_id(ctx)
        try:
            row = await tx.load(CATALOG, key)
        except StoreMissing:
            expected, pins = 0, []
        else:
            validate_contract("InternalContextSourcesRequest", row.payload)
            expected, pins = row.revision, row.payload["source_refs"]
        pins = [r for r in pins if r["id"] != identifier]
        if len(pins) >= MAX_ENTRIES:
            raise reject(
                "context_registration_too_large", "Run registration exceeds 64 entries", 413
            )
        await tx.write(
            CATALOG,
            key,
            "InternalContextSourcesRequest",
            {
                "source_refs": [*pins, pin.wire()],
                "purpose": "agent_step",
                "source_revision_policy": "pinned",
            },
            expected,
        )

    async def _write(
        self,
        ctx: TrustedExecutionContext,
        actor: Principal,
        expected: int,
        meta: RequestMeta,
        identifier: str,
        entries: tuple[tuple[str, str, dict[str, Any]], ...],
        pin: Ref,
        original: tuple[Ref, ...],
        parameters: dict[str, Any],
        *,
        catalog: bool,
        recheck: Callable[[], Awaitable[None]] | None = None,
    ) -> Ref:
        self._meta(expected, meta)
        self._capacity(parameters)

        async def verify() -> None:
            if await self._service(actor, ctx) != original:
                raise reject("source_changed", "Run input set changed during registration", 410)
            if recheck is not None:
                await recheck()

        async def write(tx: RecordTransaction) -> dict[str, Any]:
            if expected:
                await self._owner(identifier, ctx)
            else:
                await tx.write(BINDINGS, identifier, "TrustedExecutionContext", ctx.wire())
            for namespace, schema, value in entries:
                await tx.write(namespace, identifier, schema, value, expected)
            await tx.write(
                SEALS,
                identifier,
                "Ref",
                Ref(
                    kind="content",
                    id=identifier,
                    version=str(expected + 1),
                    content_hash=digest({"entries": entries, "owner": identity(ctx)}),
                ).wire(),
                expected,
            )
            if catalog:
                await self._catalog(tx, identifier, pin, ctx)
            await verify()
            return pin.wire()

        result = await self.transactions.execute(
            ctx.principal,
            "registered-context-" + digest({"run": ctx.run_id}),
            meta,
            {
                "action": "register",
                "identifier": identifier,
                "expected": expected,
                "controller": actor.wire(),
                "owner": identity(ctx),
                **parameters,
            },
            write,
            verify,
        )
        await verify()
        result_ref = from_wire(Ref, result)
        # Replay remains subject to current pin/access checks, never an old success grant.
        if entries[0][0] == RECIPES:
            if (await self.recipe(ctx)).ref != result_ref:
                raise reject("source_changed", "Recipe registration is stale", 410)
        else:
            await self.read(result_ref, ctx)
        return result_ref

    @bounded
    async def register_material(
        self,
        text: str,
        ctx: TrustedExecutionContext,
        *,
        authenticated_service: Principal,
        expected_revision: int,
        meta: RequestMeta,
    ) -> Ref:
        original = await self._service(authenticated_service, ctx)
        self._meta(expected_revision, meta)
        if type(text) is not str or not text or len(text.encode("utf-8")) > MAX_TEXT_BYTES:
            raise reject(
                "context_registration_too_large", "Material must be 1..65536 UTF-8 bytes", 413
            )
        identifier = material_id(ctx)
        content_hash = await self.blobs.put(ctx.principal, text.encode("utf-8"))
        if content_hash != hashlib.sha256(text.encode("utf-8")).hexdigest():
            raise reject("source_changed", "Blob store returned a different content hash", 410)
        pin = Ref(
            kind="content",
            id=identifier,
            version=str(expected_revision + 1),
            content_hash=content_hash,
        )
        block = {
            "id": identifier,
            "kind": "material",
            "source_refs": [pin.wire()],
            "content_ref": pin.wire(),
            "estimated_tokens": len(text.encode("utf-8")) + 64,
            "required": False,
            "trust": "external",
        }
        return await self._write(
            ctx,
            authenticated_service,
            expected_revision,
            meta,
            identifier,
            ((MATERIALS, "ContextBlock", block),),
            pin,
            original,
            {"block": block},
            catalog=True,
        )

    @bounded
    async def register_rule(
        self,
        rule: InstructionRule,
        ctx: TrustedExecutionContext,
        *,
        authenticated_service: Principal,
        expected_revision: int,
        meta: RequestMeta,
    ) -> Ref:
        original = await self._service(authenticated_service, ctx)
        self._meta(expected_revision, meta)
        rule = from_wire(InstructionRule, rule.wire())
        if not rule.text or len(rule.text.encode("utf-8")) > MAX_TEXT_BYTES:
            raise reject("context_registration_too_large", "Rule must be 1..65536 UTF-8 bytes", 413)
        if rule.id.startswith(("material-", "recipe-")):
            raise reject("context_reference_invalid", "Rule ID uses a reserved namespace")
        if (
            rule.scope.conversation_id != ctx.scope.conversation_id
            or any(
                getattr(rule.scope, name) is not None
                and getattr(rule.scope, name) != getattr(ctx.scope, name)
                for name in ("task_id", "project_id")
            )
            or rule.scope.resource_refs
        ):
            raise reject("permission_denied", "Rule must belong to this Run/conversation", 403)
        if rule.level not in (
            "platform",
            "capability_policy",
            "user_current",
            "user_preference",
            "role",
        ):
            raise CapabilityUnavailable("context.registered_rule_level")
        pin = Ref(
            kind="rule",
            id=rule.id,
            version=str(expected_revision + 1),
            content_hash=hashlib.sha256(rule.text.encode("utf-8")).hexdigest(),
        )
        if (
            not matches_pin(rule.source_ref, pin)
            or rule.source_ref.location is not None
            or rule.source_ref.access_scope is not None
        ):
            raise reject(
                "context_reference_invalid", "Rule source must name its next actual registration"
            )
        actual = rule.model_copy(update={"source_ref": pin})
        if await self.blobs.put(ctx.principal, rule.text.encode("utf-8")) != pin.content_hash:
            raise reject("source_changed", "Rule blob differs", 410)
        return await self._write(
            ctx,
            authenticated_service,
            expected_revision,
            meta,
            rule.id,
            ((RULES, "InstructionRule", actual.wire()),),
            pin,
            original,
            {"rule": actual.wire()},
            catalog=True,
        )

    async def check_tools(self, tools: ModelToolSet, ctx: TrustedExecutionContext) -> None:
        tools = from_wire(ModelToolSet, tools.wire())
        if tools.run_id != ctx.run_id:
            raise reject("permission_denied", "Tool set belongs to another Run", 403)
        if len(tools.tools) > MAX_ENTRIES or len({t["id"] for t in tools.tools}) != len(
            tools.tools
        ):
            raise reject(
                "tool_set_conflict", "Tool set exceeds bounds or repeats tool identity", 409
            )
        for tool in tools.tools:
            if not set(tool["required_capabilities"]).issubset(ctx.scope.capabilities):
                raise reject("permission_denied", "Tool exceeds current scope", 403)
        if tools.tools:
            if self.tool_validator is None:
                raise CapabilityUnavailable("context.current_tool_validation_source")
            before = tools.wire()
            offered = from_wire(ModelToolSet, before)
            await self.tool_validator.check(offered, ctx)
            if offered.wire() != before:
                raise reject("source_changed", "Tool validator changed the fixed definitions", 410)
        await self.guard.check(ctx)

    @bounded
    async def register_recipe(
        self,
        request: ContextRequest,
        rules: RulesRequest,
        tools: ModelToolSet,
        ctx: TrustedExecutionContext,
        *,
        authenticated_service: Principal,
        expected_revision: int,
        meta: RequestMeta,
    ) -> Ref:
        original = await self._service(authenticated_service, ctx)
        self._meta(expected_revision, meta)
        request = from_wire(ContextRequest, request.wire())
        rules = from_wire(RulesRequest, rules.wire())
        tools = from_wire(ModelToolSet, tools.wire())
        if request.purpose != "agent_step":
            raise CapabilityUnavailable("context.registered_purpose")
        if (
            request.model_policy_ref != ctx.model_policy_ref
            or request.expected_epoch != expected_revision
        ):
            raise reject(
                "context_epoch_conflict", "Recipe must use the fixed model/current CAS epoch", 409
            )
        if rules.scope_paths or rules.activated_skill_refs:
            raise CapabilityUnavailable("context.registered_path_or_skill_rules")
        if len(request.source_refs) > MAX_ENTRIES or len(rules.user_instruction_refs) > MAX_ENTRIES:
            raise reject("context_registration_too_large", "Recipe exceeds 64 sources/rules", 413)
        self._capacity({"request": request.wire(), "rules": rules.wire(), "tools": tools.wire()})
        await self.check_tools(tools, ctx)
        fixed_rules = []
        for rule_ref in rules.user_instruction_refs:
            if rule_ref.kind != "rule":
                raise reject(
                    "permission_denied", "Only actual registered rules can be selected", 403
                )
            fixed_rules.append((await self.read(rule_ref, ctx)).ref)
        sources: dict[str, Ref] = {digest(pin.wire()): pin for pin in original}
        for pin in (
            *request.source_refs,
            *request.preserve.required_refs,
            *request.preserve.pending_action_refs,
        ):
            read = await self.read(pin, ctx)
            if read.kind == "instruction" and not any(
                matches_pin(r, read.ref) for r in fixed_rules
            ):
                raise reject("permission_denied", "Unselected rule cannot enter recipe data", 403)
            sources[digest(read.ref.wire())] = read.ref
        if request.preserve.requirement_ids or request.preserve.pending_action_refs:
            raise CapabilityUnavailable("context.registered_requirement_or_action_source")
        if len(sources) > MAX_ENTRIES:
            raise reject(
                "context_registration_too_large", "Recipe exceeds protected source bounds", 413
            )
        preserve = PreservationSpec(
            required_refs=tuple(
                {digest(r.wire()): r for r in (*original, *request.preserve.required_refs)}.values()
            ),
            exact_strings=request.preserve.exact_strings,
            requirement_ids=(),
            pending_action_refs=(),
        )
        canonical = request.model_copy(
            update={
                "source_refs": tuple(sources.values()),
                "preserve": preserve,
                "expected_epoch": expected_revision + 1,
            }
        )
        fixed = rules.model_copy(update={"user_instruction_refs": tuple(fixed_rules)})
        identifier = recipe_id(ctx)
        pin = Ref(
            kind="content",
            id=identifier,
            version=str(expected_revision + 1),
            content_hash=digest(
                {
                    "request": canonical.wire(),
                    "rules": fixed.wire(),
                    "tools": tools.wire(),
                    "owner": identity(ctx),
                }
            ),
        )

        # Recheck all exact sources and current Tool validation inside and after commit.
        async def recheck() -> None:
            await self.check_tools(tools, ctx)
            for ref in (*canonical.source_refs, *fixed.user_instruction_refs):
                await self.read(ref, ctx)

        result = await self._write(
            ctx,
            authenticated_service,
            expected_revision,
            meta,
            identifier,
            (
                (RECIPES, "ContextRequest", canonical.wire()),
                (RECIPE_RULES, "InternalContextRulesRequest", fixed.wire()),
                (TOOLS, "ModelToolSet", tools.wire()),
            ),
            pin,
            original,
            {"request": canonical.wire(), "rules": fixed.wire(), "tools": tools.wire()},
            catalog=False,
            recheck=recheck,
        )
        return result

    @bounded
    async def recipe(self, ctx: TrustedExecutionContext) -> RegisteredRecipe:
        before = await self._access(ctx)
        identifier = recipe_id(ctx)
        owner = await self._owner(identifier, ctx)
        row = await self.records.get(ctx.principal, RECIPES, identifier)
        request = from_wire(ContextRequest, row.payload)
        rules = await self.records.get(ctx.principal, RECIPE_RULES, identifier)
        tools = await self.records.get(ctx.principal, TOOLS, identifier)
        if (
            row.schema_name != "ContextRequest"
            or rules.schema_name != "InternalContextRulesRequest"
            or tools.schema_name != "ModelToolSet"
            or rules.revision != row.revision
            or tools.revision != row.revision
            or request.expected_epoch != row.revision
            or request.purpose != "agent_step"
        ):
            raise reject("source_changed", "Recipe revision/schema changed", 410)
        await self._seal(
            identifier,
            row.revision,
            (
                (RECIPES, row.schema_name, row.payload),
                (RECIPE_RULES, rules.schema_name, rules.payload),
                (TOOLS, tools.schema_name, tools.payload),
            ),
            ctx,
        )
        selected = from_wire(RulesRequest, rules.payload)
        actual_tools = from_wire(ModelToolSet, tools.payload)
        pin = Ref(
            kind="content",
            id=identifier,
            version=str(row.revision),
            content_hash=digest(
                {
                    "request": request.wire(),
                    "rules": selected.wire(),
                    "tools": actual_tools.wire(),
                    "owner": identity(owner),
                }
            ),
        )
        await self.check_tools(actual_tools, ctx)
        if (
            await self.records.get(ctx.principal, RECIPES, identifier) != row
            or await self.records.get(ctx.principal, RECIPE_RULES, identifier) != rules
            or await self.records.get(ctx.principal, TOOLS, identifier) != tools
            or await self._owner(identifier, ctx) != owner
        ):
            raise reject("source_changed", "Recipe changed during read", 410)
        if await self._access(ctx) != before:
            raise reject("source_changed", "Run binding changed during recipe read", 410)
        return RegisteredRecipe(pin, request, selected, actual_tools, owner)

    @bounded
    async def read(self, pin: Ref, ctx: TrustedExecutionContext) -> Reading:
        before = await self._access(ctx)
        numeric(pin)
        if pin.access_scope is not None:
            raise reject("permission_denied", "Ref access_scope does not grant access", 403)
        if pin.kind == "input":
            assert self.runs is not None
            result = await self.runs.read(pin, "pinned", ctx)
        elif pin.kind in ("content", "rule") and not pin.id.startswith("recipe-"):
            namespace, schema = (
                (MATERIALS, "ContextBlock") if pin.kind == "content" else (RULES, "InstructionRule")
            )
            owner = await self._owner(pin.id, ctx)
            row = await self.records.get(ctx.principal, namespace, pin.id)
            validate_contract(schema, row.payload)
            if row.schema_name != schema or row.revision != numeric(pin):
                raise reject("source_changed", "Registered source revision changed", 410)
            await self._seal(
                pin.id, row.revision, ((namespace, row.schema_name, row.payload),), ctx
            )
            kind: BlockKind
            trust: Trust
            rule_value: InstructionRule | None = None
            if pin.kind == "content":
                value = row.payload
                actual = from_wire(Ref, value["content_ref"])
                if (
                    value["kind"] != "material"
                    or value["trust"] != "external"
                    or value["required"]
                    or value["source_refs"] != [actual.wire()]
                ):
                    raise reject("source_changed", "Material classification changed", 410)
                kind, trust, required = "material", "external", False
            else:
                rule_value = from_wire(InstructionRule, row.payload)
                actual = rule_value.source_ref
                kind, required = "instruction", True
                trust = (
                    "platform"
                    if rule_value.level in ("platform", "capability_policy", "role")
                    else "user"
                )
            if (
                actual.kind != pin.kind
                or actual.id != pin.id
                or actual.version != pin.version
                or actual.location is not None
                or actual.access_scope is not None
                or not actual.content_hash
            ):
                raise reject("source_changed", "Registered source metadata changed", 410)
            try:
                text = (await self.blobs.get(ctx.principal, actual.content_hash)).decode("utf-8")
            except ValueError, UnicodeError:
                raise reject("source_changed", "Registered blob is corrupt", 410) from None
            if (
                len(text.encode("utf-8")) > MAX_TEXT_BYTES
                or hashlib.sha256(text.encode("utf-8")).hexdigest() != actual.content_hash
                or (rule_value is not None and text != rule_value.text)
            ):
                raise reject("source_changed", "Registered text/hash changed", 410)
            if pin.location is not None:
                if pin.location.wire() == {"kind": "whole"}:
                    pass
                elif (
                    pin.location.kind == "text_span"
                    and set(pin.location.wire()) == {"kind", "start", "end"}
                    and pin.location.start is not None
                    and pin.location.end is not None
                    and 0 <= pin.location.start <= pin.location.end <= len(text)
                    and pin.kind == "content"
                ):
                    text = text[pin.location.start : pin.location.end]
                else:
                    raise CapabilityUnavailable("context.registered_location")
                actual = actual.model_copy(
                    update={
                        "location": pin.location,
                        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    }
                )
            if not matches_pin(pin, actual):
                raise reject("source_changed", "Registered source pin/hash changed", 410)
            if (
                await self.records.get(ctx.principal, namespace, pin.id) != row
                or await self._owner(pin.id, ctx) != owner
            ):
                raise reject("source_changed", "Source changed during blob read", 410)
            result = Reading(actual, text, kind=kind, trust=trust, required=required)
        elif pin.kind == "configuration" and pin.id == recipe_id(ctx):
            recipe = await self.recipe(ctx)
            text = serialize(recipe.tools.wire())
            actual = Ref(
                kind="configuration",
                id=recipe.ref.id,
                version=recipe.ref.version,
                content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            )
            if pin.location is not None or not matches_pin(pin, actual):
                raise reject("source_changed", "Tool set pin changed", 410)
            result = Reading(actual, text, kind="material", trust="platform", required=True)
        else:
            raise CapabilityUnavailable(f"context.registered_reader.{pin.kind}")
        if await self._access(ctx) != before:
            raise reject("source_changed", "Run binding changed during source read", 410)
        return result

    @bounded
    async def revoke(
        self,
        ref: Ref,
        ctx: TrustedExecutionContext,
        *,
        authenticated_service: Principal,
        expected_revision: int,
        meta: RequestMeta,
    ) -> None:
        self._meta(expected_revision, meta)
        if (
            numeric(ref) != expected_revision
            or ref.location is not None
            or ref.access_scope is not None
            or not ref.content_hash
            or ref.kind not in ("content", "rule")
        ):
            raise reject("context_reference_invalid", "Revocation requires the exact whole pin")
        namespace = (
            RECIPES
            if ref.kind == "content" and ref.id == recipe_id(ctx)
            else MATERIALS
            if ref.kind == "content"
            else RULES
        )

        async def verify() -> None:
            await self._service(authenticated_service, ctx)
            await self._owner(ref.id, ctx)

        async def remove(tx: RecordTransaction) -> dict[str, Any]:
            # A delete and its typed pin receipt share the registration CAS lock.
            # Replays still verify current identity/policy/cancellation above.
            actual = (
                (await self.recipe(ctx)).ref
                if namespace == RECIPES
                else (await self.read(ref, ctx)).ref
            )
            row = await tx.load(namespace, ref.id)
            if actual != ref or row.revision != expected_revision:
                raise StoreConflict()
            await verify()
            row.deleted, row.revision, row.updated_at = True, expected_revision + 1, utcnow()
            await tx.write(REVOKED, ref.id, "Ref", ref.wire())
            return {"ref": ref.wire()}

        result = await self.transactions.execute(
            ctx.principal,
            "registered-context-" + digest({"run": ctx.run_id}),
            meta,
            {
                "action": "revoke",
                "ref": ref.wire(),
                "expected": expected_revision,
                "controller": authenticated_service.wire(),
                "owner": identity(ctx),
            },
            remove,
            verify,
        )
        await verify()
        receipt = await self.records.get(ctx.principal, REVOKED, ref.id)
        if (
            receipt.schema_name != "Ref"
            or receipt.payload != result["ref"]
            or result["ref"] != ref.wire()
        ):
            raise reject("source_changed", "Revocation receipt differs", 410)
