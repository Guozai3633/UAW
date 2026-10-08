"""Persistent root execution leases. Fences coordinate workers; they grant no access."""

import hashlib
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore, reference
from uaw.shared.contracts import Principal, Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.ports import ExecutionLeasePort
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreConflict, StoreMissing

Payload = dict[str, Any]
NAMESPACE = "execution.leases"


def instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ExecutionLeaseService(ExecutionLeasePort):
    def __init__(
        self, store: PostgresRecordStore, *, clock: Callable[[], datetime] | None = None
    ) -> None:
        self.store = store
        self.transactions = TransactionalStore(store.database)
        self.clock = clock or (lambda: datetime.now(UTC))

    def _now(self) -> datetime:
        now = self.clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("Lease clock must be timezone aware")
        return now

    @staticmethod
    def identifier(ctx: TrustedExecutionContext) -> str:
        return "lease-" + hashlib.sha256((ctx.run_id or "").encode()).hexdigest()

    async def _aggregate(self, ctx: TrustedExecutionContext, holder: Principal) -> str:
        validate_contract("TrustedExecutionContext", ctx.wire())
        validate_contract("Principal", holder.wire())
        if holder.kind != "service":
            raise reject(
                "lease_holder_denied", "An authenticated execution service is required", 403
            )
        if not ctx.run_id:
            raise CapabilityUnavailable("execution.admitted_run")
        if ctx.node_id is not None:
            raise CapabilityUnavailable("execution.node_lease")
        run = await self.store.get(ctx.principal, "runs", ctx.run_id)
        return f"conversation:{run.payload['conversation_id']}"

    async def _run(
        self, tx: RecordTransaction, ctx: TrustedExecutionContext
    ) -> tuple[datetime, str | None]:
        run = (await tx.load("runs", ctx.run_id or "")).payload
        ledger = (await tx.load("budget.ledgers", ctx.run_id or "")).payload
        if (
            ctx.scope.conversation_id != run["conversation_id"]
            or (ctx.conversation_id is not None and ctx.conversation_id != run["conversation_id"])
            or any(
                value is not None and value != run["task_id"]
                for value in (ctx.task_id, ctx.scope.task_id)
            )
            or ctx.scope.project_id is not None
        ):
            raise reject("lease_scope_denied", "Lease is outside the owned Run", 403)
        root_deadline = min(instant(run["budget"]["deadline"]), instant(ledger["deadline"]))
        deadline = min(instant(ctx.deadline), root_deadline)
        reason = None
        if ledger["cancel_requested"] or run["status"] == "cancelled":
            reason = "lease_revoked"
        elif run["status"] not in (
            "preparing",
            "running",
            "verifying",
            "waiting_for_user",
            "waiting_for_merge",
        ):
            reason = "lease_run_unavailable"
        elif root_deadline <= self._now():
            reason = "lease_expired"
        return deadline, reason

    def _pin(
        self,
        ctx: TrustedExecutionContext,
        pin: Payload,
        fence: int,
        state: Payload,
        holder: Principal,
    ) -> None:
        validate_contract("ExecutionLeaseStateRecord", state)
        lease = state["lease"]
        if (
            pin != reference("lease", self.identifier(ctx), lease["revision"])
            or fence != lease["fencing_token"]
            or lease["run_id"] != ctx.run_id
            or lease["id"] != self.identifier(ctx)
            or lease.get("node_id") is not None
        ):
            raise StoreConflict()
        if lease["holder"] != holder.wire():
            raise reject("lease_holder_denied", "Current service does not own this lease", 403)

    async def current(
        self, lease_ref: Ref, fencing_token: int, ctx: TrustedExecutionContext, *, holder: Principal
    ) -> Payload:
        validate_contract("Revision", fencing_token)
        aggregate = await self._aggregate(ctx, holder)

        async def read(tx: RecordTransaction) -> Payload:
            _, reason = await self._run(tx, ctx)
            row = await tx.load(NAMESPACE, self.identifier(ctx))
            state = row.payload
            self._pin(ctx, lease_ref.wire(), fencing_token, state, holder)
            lease = state["lease"]
            if row.revision != lease["revision"]:
                raise StoreConflict()
            if state["state"] != "active":
                return {"unavailable": "lease_" + state["state"]}
            if reason is None and instant(lease["expires_at"]) <= self._now():
                reason = "lease_expired"
            if reason is not None:
                # Return the failure marker, then raise outside the transaction so
                # an observed expiry/revocation is durable even if the clock rolls back.
                terminal = "expired" if reason == "lease_expired" else "revoked"
                await tx.write(
                    NAMESPACE,
                    row.resource_id,
                    "ExecutionLeaseStateRecord",
                    {
                        "lease": {**lease, "revision": row.revision + 1},
                        "state": terminal,
                    },
                    row.revision,
                )
                return {"unavailable": reason}
            if instant(ctx.deadline) <= self._now():
                # An expired caller cannot use the lease, but cannot revoke a
                # different still-live root execution by supplying a shorter deadline.
                return {"unavailable": "lease_context_expired"}
            return dict(lease)

        result = await self.transactions.inspect(ctx.principal, aggregate, read)
        if "unavailable" in result:
            raise reject(
                result["unavailable"], "Execution lease is no longer active", 409, "cancelled"
            )
        return result

    async def _change(
        self,
        action: str,
        request: Payload,
        meta: RequestMeta,
        ctx: TrustedExecutionContext,
        holder: Principal,
    ) -> Payload:
        validate_contract("ExecutionLease" + action.capitalize() + "Request", request)
        aggregate = await self._aggregate(ctx, holder)
        lease_id = self.identifier(ctx)

        async def write(tx: RecordTransaction) -> Payload:
            deadline, reason = await self._run(tx, ctx)
            try:
                row = await tx.load(NAMESPACE, lease_id)
            except StoreMissing:
                row = None
            now = self._now()  # Taken after waiting for the same lock used by Run.control.
            if row:
                validate_contract("ExecutionLeaseStateRecord", row.payload)
                if row.payload["lease"]["revision"] != row.revision:
                    raise StoreConflict()
            if action != "release" and reason is None and deadline <= now:
                reason = "lease_context_expired"
            if action != "release" and reason is not None:
                raise reject(reason, "Run cannot accept an execution lease", 409, "cancelled")
            if action == "acquire":
                revision = row.revision if row else 0
                if request["expected_revision"] != revision:
                    raise StoreConflict()
                if (
                    row
                    and row.payload["state"] == "active"
                    and instant(row.payload["lease"]["expires_at"]) > now
                ):
                    raise reject("lease_busy", "Run already has an active execution holder", 409)
                fence = row.payload["lease"]["fencing_token"] + 1 if row else 1
                lease = {
                    "id": lease_id,
                    "run_id": ctx.run_id,
                    "holder": holder.wire(),
                    "revision": revision + 1,
                    "fencing_token": fence,
                    "expires_at": min(
                        now + timedelta(milliseconds=request["lease_ttl_ms"]), deadline
                    ).isoformat(),
                }
                state = {"lease": lease, "state": "active"}
            else:
                if row is None:
                    raise StoreMissing()
                self._pin(ctx, request["lease_ref"], request["fencing_token"], row.payload, holder)
                revision = row.revision
                if row.payload["lease"]["revision"] != revision:
                    raise StoreConflict()
                if action == "renew" and (
                    row.payload["state"] != "active"
                    or instant(row.payload["lease"]["expires_at"]) <= now
                ):
                    raise reject("lease_expired", "Inactive lease cannot be renewed", 409)
                lease = {
                    **row.payload["lease"],
                    "revision": revision + 1,
                    "expires_at": now.isoformat()
                    if action == "release"
                    else min(
                        now + timedelta(milliseconds=request["lease_ttl_ms"]), deadline
                    ).isoformat(),
                }
                state = {"lease": lease, "state": "released" if action == "release" else "active"}
            await tx.write(NAMESPACE, lease_id, "ExecutionLeaseStateRecord", state, revision)
            return state

        state = await self.transactions.execute(
            ctx.principal,
            aggregate,
            meta,
            {
                "action": "lease." + action,
                "request": request,
                "context": ctx.wire(),
                "holder": holder.wire(),
            },
            write,
        )
        if action == "release":
            return state  # An idempotent historical release receipt never grants execution.
        lease = state["lease"]
        return await self.current(
            Ref.model_validate(reference("lease", lease_id, lease["revision"])),
            lease["fencing_token"],
            ctx,
            holder=holder,
        )

    async def acquire(
        self,
        request: Payload,
        meta: RequestMeta,
        ctx: TrustedExecutionContext,
        *,
        holder: Principal,
    ) -> Payload:
        return await self._change("acquire", request, meta, ctx, holder)

    async def state(self, ctx: TrustedExecutionContext, *, holder: Principal) -> Payload:
        aggregate = await self._aggregate(ctx, holder)

        async def read(tx: RecordTransaction) -> Payload:
            _, reason = await self._run(tx, ctx)
            row = await tx.load(NAMESPACE, self.identifier(ctx))
            state = row.payload
            validate_contract("ExecutionLeaseStateRecord", state)
            lease = state["lease"]
            if (
                lease["revision"] != row.revision
                or lease["id"] != row.resource_id
                or lease["run_id"] != ctx.run_id
                or lease.get("node_id") is not None
            ):
                raise StoreConflict()
            if state["state"] == "active":
                if reason is None and instant(lease["expires_at"]) <= self._now():
                    reason = "lease_expired"
                if reason is not None:
                    state = {
                        "lease": {**lease, "revision": row.revision + 1},
                        "state": "expired" if reason == "lease_expired" else "revoked",
                    }
                    await tx.write(
                        NAMESPACE, row.resource_id, "ExecutionLeaseStateRecord", state, row.revision
                    )
            return dict(state)

        return await self.transactions.inspect(ctx.principal, aggregate, read)

    async def renew(
        self,
        request: Payload,
        meta: RequestMeta,
        ctx: TrustedExecutionContext,
        *,
        holder: Principal,
    ) -> Payload:
        validate_contract("ExecutionLeaseRenewRequest", request)
        # Seal observed expiry/revocation before entering a mutation transaction
        # whose rejection would otherwise roll back that terminal observation.
        try:
            await self.current(
                Ref.model_validate(request["lease_ref"]),
                request["fencing_token"],
                ctx,
                holder=holder,
            )
        except StoreConflict:
            # A lost response may leave the original pin behind. The immutable
            # request ledger, mutation CAS and final current() still must agree.
            pass
        return await self._change("renew", request, meta, ctx, holder)

    async def release(
        self,
        request: Payload,
        meta: RequestMeta,
        ctx: TrustedExecutionContext,
        *,
        holder: Principal,
    ) -> Payload:
        return await self._change("release", request, meta, ctx, holder)
