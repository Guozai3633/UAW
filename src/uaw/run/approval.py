"""Durable manual decisions. A grant records consent; it never executes an action."""

import json
from datetime import UTC, datetime
from typing import Any

from uaw.infrastructure.db.records import PostgresRecordStore, parameter_hash
from uaw.infrastructure.db.transactions import (
    RecordTransaction,
    TransactionalStore,
    identifier,
    reference,
    timestamp,
)
from uaw.run.permissions import ExecutionPolicyResolver, require_snapshot
from uaw.shared.configuration import ConfigurationService
from uaw.shared.contracts import Principal, Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, DomainError, reject
from uaw.shared.ports import ApprovalAuthorityPort, ApprovalPort, ExecutionPolicyPort
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreConflict

Payload = dict[str, Any]


def instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ApprovalService(ApprovalPort):
    def __init__(
        self,
        store: PostgresRecordStore,
        configuration: ConfigurationService,
        authority: ApprovalAuthorityPort | None = None,
        permissions: ExecutionPolicyPort | None = None,
    ) -> None:
        self.store = store
        self.configuration = configuration
        self.authority = authority
        self.permissions = permissions or ExecutionPolicyResolver(store)
        self.transactions = TransactionalStore(store.database)

    async def _aggregate(self, actor: Principal, run_id: str) -> str:
        run = await self.store.get(actor, "runs", run_id)
        return f"conversation:{run.payload['conversation_id']}"

    async def _expiry(self, tx: RecordTransaction, binding: Payload) -> str | None:
        ctx = TrustedExecutionContext.model_validate_json(json.dumps(binding["context"]))
        run = (await tx.load("runs", ctx.run_id or "")).payload
        ledger = (await tx.load("budget.ledgers", ctx.run_id or "")).payload
        if ledger["cancel_requested"] or run["status"] == "cancelled":
            return "cancelled"
        deadline = min(
            instant(ctx.deadline),
            instant(ledger["deadline"]),
            instant(binding["request"]["expires_at"]),
        )
        if datetime.now(UTC) >= deadline:
            return "expired"
        if run["status"] not in ("preparing", "running", "verifying", "waiting_for_user"):
            return "stale"
        return None

    async def _authorize(self, tx: RecordTransaction, binding: Payload) -> None:
        ctx = TrustedExecutionContext.model_validate_json(json.dumps(binding["context"]))
        run = (await tx.load("runs", ctx.run_id or "")).payload
        if (
            ctx.principal.id != tx.owner
            or ctx.scope.conversation_id != run["conversation_id"]
            or ctx.conversation_id != run["conversation_id"]
            or ctx.task_id != run["task_id"]
            or ctx.scope.task_id != run["task_id"]
            or ctx.scope.project_id is not None
        ):
            raise reject("approval_scope_denied", "Approval is outside the Run scope", 403)
        invalid = await self._expiry(tx, binding)
        if invalid:
            raise reject("approval_" + invalid, "Approval is no longer actionable", 412)
        admission = (await tx.load("run.bindings", ctx.run_id or "")).payload
        if admission["configuration_ref"] != binding["configuration_ref"]:
            raise reject("approval_binding_stale", "Run configuration binding changed", 412)
        fixed = await self.configuration.snapshot(binding["configuration_ref"])
        current = await self.configuration.current()
        if not (
            fixed["approval_policy_ref"]
            == current["approval_policy_ref"]
            == binding["approval_policy_ref"]
        ):
            raise reject("approval_policy_stale", "Approval policy changed", 412)
        policy_ref = binding["approval_policy_ref"]
        policy = await self.store.get(self.configuration.platform, "policies", policy_ref["id"])
        if str(policy.revision) != policy_ref["version"]:
            raise reject("approval_policy_stale", "Approval policy was revised", 412)
        validate_contract("ApprovalPolicy", policy.payload)
        if policy.payload["rules"]:
            raise CapabilityUnavailable("approval.rule_evaluation")
        conversation = (await tx.load("conversations", run["conversation_id"])).payload
        if (
            conversation["approval_mode"] != "manual"
            or "manual" not in policy.payload["allowed_modes"]
        ):
            raise CapabilityUnavailable("non_manual_approval")
        try:
            snapshot = await self.permissions.resolve(ctx)
            require_snapshot(snapshot, ctx)
        except DomainError as exc:
            if exc.failure.code == "execution_policy_stale":
                raise reject(
                    "approval_permission_stale", "Execution permission changed", 412
                ) from None
            raise
        if any(
            ref not in [r.wire() for r in ctx.scope.resource_refs]
            for ref in binding["request"]["resource_refs"]
        ):
            raise reject(
                "approval_permission_stale", "Current permission does not allow the action", 412
            )
        if self.authority is None:
            raise CapabilityUnavailable("approval.action_authority")
        await self.authority.check(binding["request"], ctx)

    async def request(
        self, request: Payload, meta: RequestMeta, ctx: TrustedExecutionContext
    ) -> Payload:
        validate_contract("ApprovalCreateRequest", request)
        request = json.loads(json.dumps(request, allow_nan=False))
        if not ctx.run_id:
            raise CapabilityUnavailable("approval.run_binding")
        aggregate = await self._aggregate(ctx.principal, ctx.run_id)
        # Stable action identity persists independently of request_id and process lifetime.
        approval_id = "approval-" + parameter_hash(
            {"run": ctx.run_id, "action": request["action_id"]}
        )

        async def write(tx: RecordTransaction) -> Payload:
            admission = (await tx.load("run.bindings", ctx.run_id or "")).payload
            fixed = await self.configuration.snapshot(admission["configuration_ref"])
            binding = {
                "context": ctx.wire(),
                "request": request,
                "configuration_ref": admission["configuration_ref"],
                "approval_policy_ref": fixed["approval_policy_ref"],
            }
            validate_contract("ApprovalBinding", binding)
            await self._authorize(tx, binding)
            ledger = (await tx.load("budget.ledgers", ctx.run_id or "")).payload
            if instant(request["expires_at"]) > min(
                instant(ctx.deadline), instant(ledger["deadline"])
            ):
                raise reject("approval_deadline_invalid", "Approval exceeds the Run deadline")
            result = {
                **request,
                "id": approval_id,
                "revision": 1,
                "mode": "manual",
                "status": "pending",
            }
            await tx.write("approval.bindings", approval_id, "ApprovalBinding", binding)
            await tx.write("approvals", approval_id, "ApprovalRequest", result)
            await tx.emit(ctx.conversation_id or "", "approval.required", result)
            return result

        await self.transactions.execute(
            ctx.principal,
            aggregate,
            meta,
            {"action": "approval.request", "request": request, "context": ctx.wire()},
            write,
        )
        return await self.get(ctx.principal, approval_id)

    async def get(self, actor: Principal, approval_id: str) -> Payload:
        await self.store.get(actor, "approvals", approval_id)
        binding = (await self.store.get(actor, "approval.bindings", approval_id)).payload
        aggregate = await self._aggregate(actor, binding["context"]["run_id"])

        async def write(tx: RecordTransaction) -> Payload:
            current = await tx.load("approvals", approval_id)
            status = await self._expiry(tx, binding)
            if status and current.payload["status"] in ("pending", "approved"):
                result = {**current.payload, "revision": current.revision + 1, "status": status}
                await tx.write(
                    "approvals", approval_id, "ApprovalRequest", result, current.revision
                )
                return result
            return dict(current.payload)

        # Refresh is a read of authoritative state, not replay of an old GET response.
        return await self.transactions.inspect(actor, aggregate, write)

    async def decide(self, actor: Principal, request: Payload, meta: RequestMeta) -> Payload:
        validate_contract("ApprovalsDecideRequest", request)
        request = json.loads(json.dumps(request, allow_nan=False))
        if actor.kind != "user" or actor.delegated_by is not None:
            raise reject("approval_user_required", "Approval requires an authenticated user", 403)
        if meta.expected_revision is None:
            raise reject("approval_revision_required", "Expected approval revision is required")
        decision = request["decision"]
        if (
            decision["decision"] == "approve_scoped"
            or "scope_selector" in decision
            or "expires_at" in decision
        ):
            raise CapabilityUnavailable("approval.scoped_grants")
        approval_id = request["approval_id"]
        binding = (await self.store.get(actor, "approval.bindings", approval_id)).payload
        aggregate = await self._aggregate(actor, binding["context"]["run_id"])

        async def write(tx: RecordTransaction) -> Payload:
            row = await tx.load("approvals", approval_id)
            if row.revision != meta.expected_revision or row.payload["status"] != "pending":
                raise StoreConflict()
            if (
                decision["expected_arguments_hash"] != row.payload["arguments_hash"]
                or decision["expected_resource_refs"] != row.payload["resource_refs"]
            ):
                raise reject(
                    "approval_action_stale", "Approval parameters or resources changed", 412
                )
            if decision["decision"] == "approve_once":
                await self._authorize(tx, binding)
            status = {"approve_once": "approved", "decline": "declined", "cancel": "cancelled"}[
                decision["decision"]
            ]
            updated = {**row.payload, "revision": row.revision + 1, "status": status}
            await tx.write("approvals", approval_id, "ApprovalRequest", updated, row.revision)
            grant = {
                "id": identifier("grant"),
                "approval_ref": reference("approval", approval_id, updated["revision"]),
                "actor": actor.wire(),
                "decision": decision,
                "issued_at": timestamp(),
            }
            await tx.write("approval.grants", approval_id, "ApprovalGrant", grant)
            await tx.emit(
                binding["context"]["conversation_id"],
                "approval.decided",
                grant,
                base_revision=row.revision - 1,
                result_revision=updated["revision"],
            )
            return grant

        return await self.transactions.execute(
            actor,
            aggregate,
            meta,
            {
                "action": "approval.decide",
                "request": request,
                "expected": meta.expected_revision,
                "actor": actor.wire(),
            },
            write,
        )

    async def recheck(
        self, approval_ref: Ref, request: Payload, ctx: TrustedExecutionContext
    ) -> Payload:
        validate_contract("ApprovalCreateRequest", request)
        request = json.loads(json.dumps(request, allow_nan=False))
        approval = await self.get(ctx.principal, approval_ref.id)
        binding = (
            await self.store.get(ctx.principal, "approval.bindings", approval_ref.id)
        ).payload
        previous = TrustedExecutionContext.model_validate_json(json.dumps(binding["context"]))
        # Attempts may change; the action, operation, policy and scope may not.
        omitted = {"attempt_id", "trace_id", "deadline"}
        if (
            approval_ref.kind != "approval"
            or str(approval["revision"]) != approval_ref.version
            or approval["status"] != "approved"
            or request != binding["request"]
            or ctx.model_dump(exclude=omitted) != previous.model_dump(exclude=omitted)
            or instant(ctx.deadline) > instant(previous.deadline)
            or instant(ctx.deadline) <= datetime.now(UTC)
        ):
            raise reject(
                "approval_action_stale", "Grant does not authorize this current action", 412
            )
        aggregate = await self._aggregate(ctx.principal, ctx.run_id or "")

        async def read(tx: RecordTransaction) -> Payload:
            current = await tx.load("approvals", approval_ref.id)
            if current.revision != approval["revision"] or current.payload["status"] != "approved":
                raise reject("approval_action_stale", "Approval changed before recheck", 412)
            await self._authorize(tx, binding)
            return dict((await tx.load("approval.grants", approval_ref.id)).payload)

        return await self.transactions.inspect(ctx.principal, aggregate, read)
