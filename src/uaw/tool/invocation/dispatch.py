"""One read-only send owner, genuine approvals/budget, durable unknown on ambiguity."""

import json
from collections.abc import Callable
from typing import Any, cast

from uaw.shared.contracts import JsonObject, TrustedExecutionContext
from uaw.tool.approval import ToolApprovalAdapter
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.discovery import check_access, require_entry
from uaw.tool.errors import fail, validate_dependency
from uaw.tool.invocation.schema import normalize
from uaw.tool.ledger import ToolLedger, action_key
from uaw.tool.ports import ToolAccessPort, ToolExecutorPort, ToolInvocationResultsPort
from uaw.tool.registry import ToolRegistry
from uaw.tool.schema import canonical

Payload = dict[str, Any]


class ToolInvocation:
    def __init__(
        self,
        registry: ToolRegistry,
        ledger: ToolLedger,
        budgets: ToolBudgetAdapter,
        approvals: ToolApprovalAdapter | None,
        *,
        access: ToolAccessPort | None = None,
        executor: ToolExecutorPort | None = None,
        estimates: JsonObject | None = None,
        results: ToolInvocationResultsPort | None = None,
        prepare: Callable[[JsonObject, JsonObject], None] | None = None,
    ) -> None:
        self.registry, self.ledger, self.budgets, self.approvals = (
            registry,
            ledger,
            budgets,
            approvals,
        )
        self.access, self.executor, self.results = access, executor, results
        self.prepare = prepare
        self.estimates = json.loads(canonical(estimates)) if estimates is not None else None

    async def gate(self, call: Payload, spec: Payload, ctx: TrustedExecutionContext) -> None:
        if self.access is None:
            raise fail(
                "dependency_unavailable",
                "Current tool access is not wired",
                phase="policy_gate",
                category="dependency",
                status=503,
            )
        access = await self.access.snapshot(ctx)
        check_access(access, ctx)
        entry = self.registry.get(call["tool_ref"])
        require_entry(entry, access)
        if entry.spec() != spec or spec["effect"] != "read":
            raise fail(
                "executor_unavailable",
                "This orchestration supports registered read tools only",
                phase="dispatch",
                category="dependency",
                status=503,
            )

    async def resume(self, call: Payload, ctx: TrustedExecutionContext) -> JsonObject:
        if self.results is None:
            raise fail(
                "dependency_unavailable",
                "Durable result normalization/source is not wired",
                phase="result_source",
                category="dependency",
                status=503,
            )
        return await self.results.resume(call, ctx)

    async def invoke(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject:
        call = normalize(request, self.registry)
        spec = self.registry.get(call["tool_ref"]).spec()
        existing = await self.ledger.get("tool.effects", action_key(ctx, call["action_id"]), ctx)
        if existing and existing["attempt_ids"] and existing["attempt_ids"] != [ctx.attempt_id]:
            raise fail(
                "unknown_effect",
                "Action already belongs to its original send attempt",
                phase="dispatch",
                category="unknown_effect",
                status=409,
            )
        prior = await self.ledger.get("tool.attempt.contexts", ctx.attempt_id, ctx)
        if prior is not None:
            pinned = await self.ledger.attempt(ctx)
            if pinned != call:
                raise fail(
                    "action_conflict",
                    "Original attempt inputs changed",
                    phase="identity",
                    category="conflict",
                    status=409,
                )
            await self.ledger.action(call["action_id"], ctx)
            effect = await self.ledger.effect_from_attempt(ctx)
            if effect["attempt_ids"]:
                if effect["attempt_ids"] != [ctx.attempt_id]:
                    raise fail(
                        "unknown_effect",
                        "Another attempt owns the original send",
                        phase="dispatch",
                        category="unknown_effect",
                        status=409,
                    )
                return await self.resume(call, ctx)
        await self.gate(call, spec, ctx)
        if (
            self.executor is None
            or self.estimates is None
            or self.results is None
            or self.approvals is None
        ):
            raise fail(
                "dependency_unavailable",
                "Read executor/estimates/approvals/results are not wired",
                phase="dispatch",
                category="dependency",
                status=503,
            )
        if self.prepare is None:
            raise fail(
                "dependency_unavailable",
                "Actual executor admission validator is not wired",
                phase="dispatch",
                category="dependency",
                status=503,
            )
        self.results.ready()
        self.prepare(call, spec)
        validate_dependency("ResourceVector", self.estimates, "reserve")
        before = canonical({"call": call, "spec": spec, "ctx": ctx.wire()})

        def unchanged() -> None:
            if before != canonical({"call": call, "spec": spec, "ctx": ctx.wire()}):
                raise fail(
                    "action_conflict",
                    "Admission dependency changed fixed inputs",
                    phase="precheck",
                    category="conflict",
                    status=409,
                )

        decision = await self.approvals.precheck(call, spec, ctx)
        unchanged()
        validate_dependency("ComponentToolInvocationPrecheckResult", decision, "precheck")
        if decision["kind"] != "ok":
            return decision
        await self.gate(call, spec, ctx)
        checked = await self.approvals.recheck(call, spec, decision, ctx)
        unchanged()
        validate_dependency("ComponentToolInvocationRecheckResult", checked, "recheck")
        if checked["kind"] != "ok":
            return checked
        if not cast(Payload, checked["payload"])["allowed"]:
            raise fail(
                "permission_denied",
                "Actual approval/resource recheck denied",
                phase="recheck",
                category="authorization",
                status=403,
            )
        # Cleanup is limited to this admitted reserve/send operation. A malformed
        # or conflicting request must never release the original attempt's holds.
        try:
            # Bound estimates and the actual reservation plan survive response loss.
            await self.budgets.reserve(self.estimates, ctx)
            await self.gate(call, spec, ctx)
            await self.approvals.require_approved(ctx)
            owned = await self.budgets.mark_dispatch(ctx)
            if not owned:
                return await self.resume(call, ctx)
            # Accounting await is not a send grant. Recheck actual admission immediately
            # before invoking the trusted executor. Failure leaves the claimed unknown.
            await self.gate(call, spec, ctx)
            await self.approvals.require_approved(ctx)
            unchanged()
            fixed = before
            receipt = await self.executor.execute(call, spec, ctx)
            if fixed != canonical({"call": call, "spec": spec, "ctx": ctx.wire()}):
                raise fail(
                    "action_conflict",
                    "Executor mutated original inputs",
                    phase="dispatch",
                    category="conflict",
                    status=409,
                )
            receipt = json.loads(canonical(receipt))
            validate_dependency("ProviderReceipt", receipt, "dispatch")
            if (
                receipt["attempt_id"] != ctx.attempt_id
                or receipt["usage"]["attempt_id"] != ctx.attempt_id
            ):
                raise fail(
                    "receipt_binding_conflict",
                    "Provider receipt belongs to another attempt",
                    phase="dispatch",
                    category="conflict",
                    status=409,
                )
            await self.ledger.save(
                "tool.invocation.receipts", ctx.attempt_id, "ProviderReceipt", receipt, ctx
            )
            return await self.resume(call, ctx)
        except BaseException:
            # Only unsent reservations can be released. Claimed intent remains
            # unknown even if the following executor never replied.
            try:
                effect = await self.ledger.effect_from_attempt(ctx)
                if ctx.attempt_id not in effect["attempt_ids"]:
                    await self.budgets.recover_reserved(ctx)
                    await self.budgets.release(ctx)
            except Exception:
                # Leave durable accounting for recovery; preserve the original
                # error/cancellation, and never report an invented release.
                pass
            raise
