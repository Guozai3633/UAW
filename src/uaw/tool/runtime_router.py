"""Finite original-facade routing; composition supplies the effective Agent access.

Routing is not admission, result-data authority, or permission to replay a send.
Recovery selects only the recorded attempt and its owning result/receipt Readers.
"""

import json
from dataclasses import dataclass
from typing import Protocol, cast

from uaw.shared.contracts import JsonObject, Ref, TrustedExecutionContext
from uaw.shared.errors import DomainError, error_result
from uaw.shared.schema import ContractViolation, validate_contract
from uaw.tool.discovery import discover
from uaw.tool.errors import fail
from uaw.tool.facade import ToolFacade
from uaw.tool.invocation.schema import normalize
from uaw.tool.ledger import ToolLedger
from uaw.tool.ports import ToolAccessPort
from uaw.tool.registry import ToolRegistry
from uaw.tool.schema import canonical


class ToolResultReadPort(Protocol):
    async def read_result(self, action_id: str, ctx: TrustedExecutionContext) -> JsonObject: ...


@dataclass(frozen=True)
class ToolRuntimeRoute:
    tool_ref: Ref
    provider_ref: Ref
    facade: ToolFacade
    results: ToolResultReadPort


class RoutedToolRuntime:
    def __init__(
        self,
        registry: ToolRegistry,
        ledger: ToolLedger,
        routes: tuple[ToolRuntimeRoute, ...],
        *,
        access: ToolAccessPort,
    ) -> None:
        if type(routes) is not tuple or not 1 <= len(routes) <= 128:
            raise ValueError("Expected 1–128 explicit original Tool routes")
        if not callable(getattr(access, "snapshot", None)):
            raise ValueError("Effective Agent Tool access is required")
        self.registry, self.ledger, self.access = registry, ledger, access
        self._routes: dict[bytes, ToolRuntimeRoute] = {}
        versions = set()
        for route in routes:
            if (
                not isinstance(route, ToolRuntimeRoute)
                or not isinstance(route.tool_ref, Ref)
                or not isinstance(route.provider_ref, Ref)
                or not isinstance(route.facade, ToolFacade)
            ):
                raise ValueError("Expected a trusted ToolRuntimeRoute with typed fixed Refs/facade")
            tool, provider = route.tool_ref.wire(), route.provider_ref.wire()
            validate_contract("Ref", tool)
            validate_contract("Ref", provider)
            if (
                set(tool) != {"kind", "id", "version", "content_hash"}
                or route.tool_ref.kind != "configuration"
                or route.tool_ref.content_hash is None
                or set(provider) - {"kind", "id", "version", "content_hash"}
                or route.provider_ref.kind != "provider"
            ):
                raise ValueError("Routes require a complete tool hash and exact provider Ref")
            version = (route.tool_ref.id, route.tool_ref.version)
            if version in versions:
                raise ValueError("Duplicate Tool id/version, including conflicting hashes")
            versions.add(version)
            # Copy the wire pins; never rely on caller-owned model_copy/update values.
            fixed = ToolRuntimeRoute(
                Ref.model_validate_json(canonical(tool)),
                Ref.model_validate_json(canonical(provider)),
                route.facade,
                route.results,
            )
            try:
                self._current(fixed)
            except DomainError as exc:
                raise ValueError(
                    "Route is not an exact original registry/store/access binding"
                ) from exc
            self._routes[canonical(tool)] = fixed

    def _current(self, route: ToolRuntimeRoute) -> None:
        facade = route.facade
        invocation = facade.invocation
        if (
            facade.registry is not self.registry
            or invocation is None
            or invocation.registry is not self.registry
            or invocation.ledger.store is not self.ledger.store
            or invocation.access is not self.access
            or not callable(getattr(route.results, "read_result", None))
            or (
                facade.reconciler is not None
                and facade.reconciler.ledger.store is not self.ledger.store
            )
        ):
            raise fail(
                "runtime_binding_conflict",
                "Original registry/store/Agent access differs",
                phase="runtime_route",
                category="conflict",
                status=409,
            )
        entry = self.registry.get(route.tool_ref.wire())
        if (
            self.registry.reference(entry) != route.tool_ref.wire()
            or entry.spec()["provider_ref"] != route.provider_ref.wire()
            or entry.binding is None
            or entry.binding.provider_ref.wire() != route.provider_ref.wire()
        ):
            raise fail(
                "runtime_binding_conflict",
                "Current Tool/provider registration differs",
                phase="runtime_route",
                category="conflict",
                status=409,
            )

    def _select(self, tool_ref: JsonObject) -> ToolRuntimeRoute:
        route = self._routes.get(canonical(tool_ref))
        if route is None:
            raise fail(
                "dependency_unavailable",
                "No exact original Tool runtime route",
                phase="runtime_route",
                category="dependency",
                status=503,
            )
        self._current(route)
        return route

    async def discover(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject:
        result: JsonObject
        try:
            fixed = json.loads(canonical(request))
            validate_contract("ToolToolsDiscoverInput", fixed)
            current = await self.access.snapshot(ctx)
            eligible = set()
            for key, route in self._routes.items():
                try:
                    self._current(route)
                except DomainError:
                    continue
                eligible.add(key)
            payload = discover(
                self.registry,
                fixed["query"],
                fixed.get("categories", []),
                fixed["max_candidates"],
                current,
                ctx,
                tool_refs=frozenset(eligible),
            )
            result = {"kind": "ok", "payload": payload, "output_refs": []}
        except DomainError as exc:
            result = error_result(exc)
        except ContractViolation, ValueError, TypeError, RecursionError, OverflowError:
            result = error_result(
                fail("invalid_arguments", "Invalid discovery request", phase="discovery")
            )
        validate_contract("RuntimeToolruntimeDiscoverResult", result)
        return result

    async def invoke(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject:
        try:
            fixed = json.loads(canonical(request))
            call = normalize(fixed, self.registry)
            route = self._select(cast(JsonObject, call["tool_ref"]))
            # Delegate the frozen original request, with the original ctx and identifiers.
            result = await route.facade.invoke(fixed, ctx)
        except DomainError as exc:
            result = error_result(exc)
        except ContractViolation, ValueError, TypeError, RecursionError, OverflowError:
            result = error_result(fail("invalid_arguments", "Invalid Tool call", phase="normalize"))
        validate_contract("RuntimeToolruntimeInvokeResult", result)
        return result

    async def _original(self, action_id: str, ctx: TrustedExecutionContext) -> ToolRuntimeRoute:
        validate_contract("ID", action_id)
        attempt = await self.ledger.attempt(ctx)
        call, spec, _ = await self.ledger.action(action_id, ctx)
        if attempt != call or call["action_id"] != action_id:
            raise fail(
                "receipt_binding_conflict",
                "Requested action differs from the original attempt",
                phase="runtime_route",
                category="conflict",
                status=409,
            )
        route = self._select(cast(JsonObject, call["tool_ref"]))
        current = self.registry.get(route.tool_ref.wire()).spec()
        if spec != current or spec["provider_ref"] != route.provider_ref.wire():
            raise fail(
                "runtime_binding_conflict",
                "Recorded Tool/provider differs from current fixed route",
                phase="runtime_route",
                category="conflict",
                status=409,
            )
        return route

    async def reconcile(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject:
        try:
            fixed = json.loads(canonical(request))
            validate_contract("ReconcileRequest", fixed)
            if type(fixed["expected_revision"]) is not int:
                raise ValueError("Expected revision must be a strict integer")
            route = await self._original(fixed["action_id"], ctx)
            result = await route.facade.reconcile(fixed, ctx)
            await self._original(fixed["action_id"], ctx)
        except DomainError as exc:
            result = error_result(exc)
        except ContractViolation, ValueError, TypeError, RecursionError, OverflowError:
            result = error_result(
                fail("invalid_arguments", "Invalid reconciliation request", phase="reconcile")
            )
        validate_contract("RuntimeToolruntimeReconcileResult", result)
        return result

    async def read_outcome(self, action_id: str, ctx: TrustedExecutionContext) -> JsonObject:
        route = await self._original(action_id, ctx)
        result = await route.facade.read_outcome(action_id, ctx)
        await self._original(action_id, ctx)
        validate_contract("ToolReconciliationReceipt", result)
        return result

    async def read_result(self, action_id: str, ctx: TrustedExecutionContext) -> JsonObject:
        route = await self._original(action_id, ctx)
        result = await route.results.read_result(action_id, ctx)
        await self._original(action_id, ctx)
        validate_contract("RuntimeToolruntimeInvokeResult", result)
        return result
