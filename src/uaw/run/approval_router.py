"""HTTP approval routing from the original durable tool action, never a default service."""

import json
from dataclasses import dataclass
from typing import Any

from uaw.infrastructure.db.records import parameter_hash
from uaw.run.approval import ApprovalService
from uaw.shared.contracts import JsonObject, Principal, Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.tool.authority import ToolApprovalAuthority
from uaw.tool.invocation.schema import normalize
from uaw.tool.ledger import ToolLedger
from uaw.tool.registry import ToolRegistry


@dataclass(frozen=True)
class ToolApprovalRoute:
    tool_ref: Ref
    provider_ref: Ref
    service: ApprovalService


class RoutedApprovals:
    def __init__(
        self, registry: ToolRegistry, ledger: ToolLedger, routes: tuple[ToolApprovalRoute, ...]
    ) -> None:
        if type(routes) is not tuple or not 1 <= len(routes) <= 128:
            raise ValueError("One to 128 original approval routes required")
        fixed = []
        keys = set()
        for route in routes:
            tool = Ref.model_validate_json(json.dumps(route.tool_ref.wire(), allow_nan=False))
            provider = Ref.model_validate_json(
                json.dumps(route.provider_ref.wire(), allow_nan=False)
            )
            entry = registry.get(tool.wire())
            authority = route.service.authority
            if (
                registry.reference(entry) != tool.wire()
                or entry.spec()["provider_ref"] != provider.wire()
                or route.service.store is not ledger.store
                or not isinstance(authority, ToolApprovalAuthority)
                or authority.registry is not registry
                or authority.ledger.store is not ledger.store
                or authority.configuration is not route.service.configuration
            ):
                raise ValueError("Exact ToolSpec/provider and original SQL authority required")
            key = (tool.id, tool.version)
            if key in keys:
                raise ValueError("Duplicate approval tool route")
            keys.add(key)
            fixed.append(ToolApprovalRoute(tool, provider, route.service))
        if len({id(r.service.configuration) for r in fixed}) != 1:
            raise ValueError("Shared original configuration owner required")
        self.registry, self.ledger, self.routes = registry, ledger, tuple(fixed)

    async def _action(
        self, request: dict[str, Any], ctx: TrustedExecutionContext
    ) -> ApprovalService:
        call, spec, original = await self.ledger.action(str(request["action_id"]), ctx)
        if (
            request["arguments_hash"] != call["arguments_hash"]
            or request["effect"] != spec["effect"]
            or any(
                r not in [p.wire() for p in original.scope.resource_refs]
                for r in request["resource_refs"]
            )
        ):
            raise reject("approval_route_action_denied", "Original approval action differs", 403)
        current = self.registry.get(call["tool_ref"])
        if (
            current.spec() != spec
            or normalize({k: v for k, v in call.items() if k != "arguments_hash"}, self.registry)
            != call
        ):
            raise reject("approval_route_registration_changed", "Original ToolSpec differs", 412)
        for route in self.routes:
            if (
                route.tool_ref.wire() == call["tool_ref"]
                and route.provider_ref.wire() == spec["provider_ref"]
            ):
                return route.service
        raise CapabilityUnavailable("approval.original_tool_service")

    async def _binding(
        self, actor: Principal, approval_id: str
    ) -> tuple[ApprovalService, JsonObject, TrustedExecutionContext]:
        validate_contract("ID", approval_id)
        row = await self.ledger.store.get(actor, "approval.bindings", approval_id)
        validate_contract("ApprovalBinding", row.payload)
        if row.schema_name != "ApprovalBinding" or row.revision != 1:
            raise reject(
                "approval_route_binding_changed", "Original approval binding required", 412
            )
        binding = json.loads(json.dumps(row.payload, allow_nan=False))
        ctx = TrustedExecutionContext.model_validate_json(json.dumps(binding["context"]))
        if actor != ctx.principal or approval_id != "approval-" + parameter_hash(
            {"run": ctx.run_id, "action": binding["request"]["action_id"]}
        ):
            raise reject("approval_route_owner_denied", "Original browser/Run owner required", 403)
        service = await self._action(binding["request"], ctx)
        if await self.ledger.store.get(actor, "approval.bindings", approval_id) != row:
            raise reject(
                "approval_route_binding_changed", "Approval binding changed while waiting", 412
            )
        # _action checks current registration after the final awaited binding read.
        service = await self._action(binding["request"], ctx)
        return service, binding["request"], ctx

    async def request(
        self, request: JsonObject, meta: RequestMeta, ctx: TrustedExecutionContext
    ) -> JsonObject:
        validate_contract("ApprovalCreateRequest", request)
        request = json.loads(json.dumps(request, allow_nan=False))
        ctx = TrustedExecutionContext.model_validate_json(json.dumps(ctx.wire(), allow_nan=False))
        service = await self._action(request, ctx)
        return await service.request(request, meta, ctx)

    async def get(self, actor: Principal, approval_id: str) -> JsonObject:
        service, _, _ = await self._binding(actor, approval_id)
        return await service.get(actor, approval_id)

    async def decide(self, actor: Principal, request: JsonObject, meta: RequestMeta) -> JsonObject:
        validate_contract("ApprovalsDecideRequest", request)
        request = json.loads(json.dumps(request, allow_nan=False))
        service, _, _ = await self._binding(actor, str(request["approval_id"]))
        return await service.decide(actor, request, meta)

    async def recheck(
        self, approval_ref: Ref, request: JsonObject, ctx: TrustedExecutionContext
    ) -> JsonObject:
        request = json.loads(json.dumps(request, allow_nan=False))
        service, original, _ = await self._binding(ctx.principal, approval_ref.id)
        if request != original:
            raise reject("approval_route_action_denied", "Original request required", 403)
        if await self._action(request, ctx) is not service:
            raise reject("approval_route_action_denied", "Original service required", 403)
        return await service.recheck(approval_ref, request, ctx)
