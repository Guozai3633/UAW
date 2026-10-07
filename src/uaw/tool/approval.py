"""Real ApprovalPort adapter; persisted approval records are the only wait refs."""

from typing import Any, cast

from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.db.transactions import reference
from uaw.shared.contracts import JsonObject, Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import DomainError, error_result
from uaw.shared.ports import ApprovalPort
from uaw.shared.schema import validate_contract
from uaw.tool.authority import ToolApprovalAuthority
from uaw.tool.errors import fail, validate_dependency
from uaw.tool.ledger import ToolLedger, action_key

Payload = dict[str, Any]


class ToolApprovalAdapter:
    def __init__(
        self, ledger: ToolLedger, authority: ToolApprovalAuthority, approvals: ApprovalPort
    ) -> None:
        self.ledger, self.authority, self.approvals = ledger, authority, approvals

    async def _approval(self, action_id: str, ctx: TrustedExecutionContext) -> Payload:
        key = action_key(ctx, action_id)
        request = await self.authority.current(action_id, ctx)
        request = await self.ledger.save(
            "tool.approval.requests", key, "ApprovalCreateRequest", request, ctx
        )
        _, _, pinned = await self.ledger.action(action_id, ctx)
        # ApprovalService hashes its original complete context. Always replay that context.
        meta = RequestMeta(
            request_id="tool-approval-" + parameter_hash({"key": key}), schema_version="0.1"
        )
        created = await self.approvals.request(request, meta, pinned)
        validate_dependency("ApprovalRequest", created, "approval")
        current: dict[str, Any] = await self.approvals.get(ctx.principal, str(created["id"]))
        validate_dependency("ApprovalRequest", current, "approval")
        if any(current.get(k) != v for k, v in request.items()):
            raise fail(
                "approval_action_stale",
                "Approval record differs from the fixed request",
                phase="approval",
                category="conflict",
                status=412,
            )
        if current["status"] == "pending":
            return {
                "kind": "waiting",
                "output_refs": [],
                "wait_ref": reference("approval", current["id"], current["revision"]),
            }
        if current["status"] != "approved":
            category = "cancelled" if current["status"] == "cancelled" else "authorization"
            raise fail(
                "approval_" + current["status"],
                "Approval does not permit this action",
                phase="approval",
                category=category,
                status=403,
            )
        ref = Ref.model_validate(reference("approval", current["id"], current["revision"]))
        grant = await self.approvals.recheck(ref, request, ctx)
        validate_dependency("ApprovalGrant", grant, "approval")
        await self.authority.check(request, ctx)
        return {
            "kind": "ok",
            "output_refs": [],
            "payload": {
                "allowed": True,
                "approval_required": False,
                "policy_ref": ctx.capability_policy_ref.wire(),
                "resource_refs": request["resource_refs"],
                "violations": [],
            },
        }

    async def precheck(
        self, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> JsonObject:
        try:
            await self.ledger.bind(call, spec, ctx)
            result = await self._approval(str(call["action_id"]), ctx)
        except DomainError as exc:
            result = error_result(exc)
        validate_contract("ComponentToolInvocationPrecheckResult", result)
        return result

    async def recheck(
        self, call: JsonObject, spec: JsonObject, precheck: JsonObject, ctx: TrustedExecutionContext
    ) -> JsonObject:
        try:
            validate_dependency("ComponentToolInvocationPrecheckResult", precheck, "recheck")
            payload = cast(dict[str, Any], precheck.get("payload", {}))
            if (
                precheck["kind"] != "ok"
                or not payload.get("allowed")
                or payload.get("approval_required") is not False
                or payload.get("policy_ref") != ctx.capability_policy_ref.wire()
            ):
                raise fail(
                    "approval_action_stale",
                    "Recheck requires a matching successful precheck",
                    phase="recheck",
                    category="conflict",
                    status=412,
                )
            key = await self.ledger.bind(call, spec, ctx)
            result = await self._approval(str(call["action_id"]), ctx)
            if result["kind"] == "ok":
                request = await self.authority.current(str(call["action_id"]), ctx)
                result = {
                    "kind": "ok",
                    "output_refs": [],
                    "payload": {
                        "allowed": True,
                        "validated_call_ref": reference("tool_call", key),
                        "resource_refs": request["resource_refs"],
                        "reason": "Live SQL grant rechecked",
                    },
                }
        except DomainError as exc:
            result = error_result(exc)
        validate_contract("ComponentToolInvocationRecheckResult", result)
        return result

    async def require_approved(self, ctx: TrustedExecutionContext) -> None:
        call = await self.ledger.attempt(ctx)
        result = await self._approval(call["action_id"], ctx)
        if result["kind"] != "ok":
            raise fail(
                "approval_pending",
                "Current approval is required before budget/dispatch",
                phase="approval",
                category="authorization",
                status=403,
            )
