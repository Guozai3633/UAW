"""MS-T1 facade: discovery and admission only. No dispatch or fake success path."""

from typing import Any, cast

from uaw.shared.contracts import JsonObject, TrustedExecutionContext
from uaw.shared.errors import DomainError, error_result
from uaw.shared.schema import ContractViolation, validate_contract
from uaw.tool.discovery import check_access, discover, require_entry
from uaw.tool.errors import fail
from uaw.tool.identity import ActionIdentities
from uaw.tool.invocation.schema import normalize
from uaw.tool.ports import PrecheckPort, RecheckPort, ToolAccess, ToolAccessPort
from uaw.tool.registry import ToolRegistry
from uaw.tool.schema import canonical


class ToolFacade:
    def __init__(
        self,
        registry: ToolRegistry,
        access: ToolAccessPort | None = None,
        *,
        precheck: PrecheckPort | None = None,
        recheck: RecheckPort | None = None,
        identities: ActionIdentities | None = None,
    ) -> None:
        self.registry, self.access = registry, access
        self.precheck, self.recheck = precheck, recheck
        self.identities = identities or ActionIdentities()

    async def _access(self, ctx: TrustedExecutionContext) -> ToolAccess:
        if self.access is None:
            raise fail(
                "dependency_unavailable",
                "Trusted tool access port is not wired",
                phase="policy_gate",
                category="dependency",
                status=503,
            )
        result = await self.access.snapshot(ctx)
        check_access(result, ctx)
        return result

    async def discover(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject:
        result: dict[str, Any]
        try:
            canonical(request)
            validate_contract("ToolToolsDiscoverInput", request)
            access = await self._access(ctx)
            payload = discover(
                self.registry,
                cast(str, request["query"]),
                cast(list[str], request.get("categories", [])),
                cast(int, request["max_candidates"]),
                access,
                ctx,
            )
            result = {"kind": "ok", "payload": payload, "output_refs": []}
        except ContractViolation, ValueError, RecursionError, OverflowError:
            result = error_result(
                fail("invalid_arguments", "Invalid tool discovery request", phase="discovery")
            )
        except DomainError as exc:
            result = error_result(exc)
        validate_contract("RuntimeToolruntimeDiscoverResult", result)
        return result

    async def invoke(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject:
        try:
            result = await self._invoke(request, ctx)
        except ContractViolation, ValueError, RecursionError, OverflowError:
            result = error_result(
                fail("invalid_arguments", "Invalid call or dependency response", phase="normalize")
            )
        except DomainError as exc:
            result = error_result(exc)
        validate_contract("RuntimeToolruntimeInvokeResult", result)
        return result

    async def _invoke(self, request: dict[str, Any], ctx: TrustedExecutionContext) -> JsonObject:
        call = normalize(request, self.registry)
        access = await self._access(ctx)
        entry = self.registry.get(call["tool_ref"])
        require_entry(entry, access)
        self.identities.bind(call, ctx)
        if self.precheck is None:
            raise fail(
                "dependency_unavailable",
                "Budget/approval precheck port is not wired",
                phase="precheck",
                category="dependency",
                status=503,
            )
        spec = entry.spec()
        before = canonical({"call": call, "spec": spec, "ctx": ctx.wire()})
        decision = await self.precheck.precheck(call, spec, ctx)
        try:
            validate_contract("ComponentToolInvocationPrecheckResult", decision)
        except ContractViolation as exc:
            raise fail(
                "dependency_protocol_invalid",
                "Precheck returned an invalid result",
                phase="precheck",
                category="dependency",
                status=503,
            ) from exc
        if before != canonical({"call": call, "spec": spec, "ctx": ctx.wire()}):
            raise fail(
                "action_conflict",
                "Dependency changed immutable call inputs",
                phase="precheck",
                category="conflict",
                status=409,
            )
        # Refresh after every asynchronous dependency; cached permission is insufficient.
        require_entry(entry, await self._access(ctx))
        if decision["kind"] != "ok":
            return decision
        payload = cast(dict[str, Any], decision["payload"])
        if payload["policy_ref"] != ctx.capability_policy_ref.wire():
            raise fail(
                "stale_resource",
                "Precheck used another policy version",
                phase="precheck",
                category="conflict",
                status=412,
            )
        if not payload["allowed"]:
            raise fail(
                "permission_denied",
                "Precheck refused the call",
                phase="precheck",
                category="authorization",
                status=403,
            )
        if payload["approval_required"]:
            # Real pending approvals must instead return kind=waiting with a real wait_ref.
            raise fail(
                "dependency_unavailable",
                "A real approval wait is required",
                phase="approval",
                category="dependency",
                status=503,
            )
        if self.recheck is None:
            raise fail(
                "dependency_unavailable",
                "Approval/resource recheck port is not wired",
                phase="recheck",
                category="dependency",
                status=503,
            )
        checked = await self.recheck.recheck(call, spec, decision, ctx)
        try:
            validate_contract("ComponentToolInvocationRecheckResult", checked)
        except ContractViolation as exc:
            raise fail(
                "dependency_protocol_invalid",
                "Recheck returned an invalid result",
                phase="recheck",
                category="dependency",
                status=503,
            ) from exc
        if before != canonical({"call": call, "spec": spec, "ctx": ctx.wire()}):
            raise fail(
                "action_conflict",
                "Dependency changed immutable call inputs",
                phase="recheck",
                category="conflict",
                status=409,
            )
        require_entry(entry, await self._access(ctx))
        if checked["kind"] != "ok":
            return checked
        if not cast(dict[str, Any], checked["payload"])["allowed"]:
            raise fail(
                "permission_denied",
                "Recheck refused the call",
                phase="recheck",
                category="authorization",
                status=403,
            )
        # MS-T2 requires durable intent/effect, budget settlement and real execution ports.
        raise fail(
            "dependency_unavailable",
            "Durable dispatch/effect/settlement is not wired",
            phase="dispatch",
            category="dependency",
            status=503,
        )
