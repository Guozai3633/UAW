"""Resolve owning Run services from persisted identities, not HTTP-selected providers."""

import json
from collections.abc import Awaitable, Callable

from uaw.infrastructure.db.records import PostgresRecordStore, parameter_hash
from uaw.run.completion import RunCompletionController
from uaw.shared.contracts import JsonObject, Principal, Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.ports import ApprovalPort
from uaw.shared.schema import validate_contract

ApprovalResolver = Callable[[TrustedExecutionContext], Awaitable[ApprovalPort]]
CompletionResolver = Callable[[TrustedExecutionContext], Awaitable[RunCompletionController]]


class RunApprovalRouter:
    def __init__(self, records: PostgresRecordStore, resolve: ApprovalResolver) -> None:
        self.records, self.resolve = records, resolve

    async def context(self, actor: Principal, approval_id: str) -> TrustedExecutionContext:
        validate_contract("ID", approval_id)
        row = await self.records.get(actor, "approval.bindings", approval_id)
        validate_contract("ApprovalBinding", row.payload)
        ctx = TrustedExecutionContext.model_validate_json(json.dumps(row.payload["context"]))
        if (
            row.schema_name != "ApprovalBinding"
            or row.revision != 1
            or ctx.principal != actor
            or approval_id
            != "approval-"
            + parameter_hash({"run": ctx.run_id, "action": row.payload["request"]["action_id"]})
        ):
            raise reject("approval_run_owner_denied", "Original Run/session binding required", 403)
        return ctx

    async def request(
        self, request: JsonObject, meta: RequestMeta, ctx: TrustedExecutionContext
    ) -> JsonObject:
        return await (await self.resolve(ctx)).request(request, meta, ctx)

    async def get(self, actor: Principal, approval_id: str) -> JsonObject:
        ctx = await self.context(actor, approval_id)
        return await (await self.resolve(ctx)).get(actor, approval_id)

    async def decide(self, actor: Principal, request: JsonObject, meta: RequestMeta) -> JsonObject:
        validate_contract("ApprovalsDecideRequest", request)
        request = json.loads(json.dumps(request, allow_nan=False))
        ctx = await self.context(actor, str(request["approval_id"]))
        return await (await self.resolve(ctx)).decide(actor, request, meta)

    async def recheck(
        self, approval_ref: Ref, request: JsonObject, ctx: TrustedExecutionContext
    ) -> JsonObject:
        original = await self.context(ctx.principal, approval_ref.id)
        return await (await self.resolve(original)).recheck(approval_ref, request, ctx)


class RunCompletionRouter:
    def __init__(self, resolve: CompletionResolver) -> None:
        self.resolve = resolve

    async def accept(
        self,
        actor: Principal,
        bundle_ref: Ref,
        artifact_ref: Ref,
        decision: str,
        ctx: TrustedExecutionContext,
        meta: RequestMeta,
    ) -> Ref:
        if actor != ctx.principal or actor.kind != "user":
            raise reject("completion_run_owner_denied", "Original authenticated user required", 403)
        return await (await self.resolve(ctx)).accept(
            actor, bundle_ref, artifact_ref, decision, ctx, meta
        )
