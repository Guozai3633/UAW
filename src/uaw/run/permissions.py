"""Current owned policy chains; no permission cache, registration or inferred grants."""

from datetime import UTC, datetime
from typing import Any

from uaw.infrastructure.db.records import PostgresRecordStore, parameter_hash
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.ports import ExecutionPolicyPort
from uaw.shared.schema import validate_contract

Payload = dict[str, Any]
MAX_POLICY_DEPTH = 8


def ref_identity(ref: Payload) -> str:
    return parameter_hash(ref)


def scope_within(child: Payload, parent: Payload) -> bool:
    return all(
        parent.get(key) is None or child.get(key) == parent[key]
        for key in ("conversation_id", "task_id", "project_id")
    ) and {ref_identity(r) for r in child.get("resource_refs", [])}.issubset(
        ref_identity(r) for r in parent.get("resource_refs", [])
    )


def require_snapshot(snapshot: Payload, ctx: TrustedExecutionContext) -> Payload:
    """Check injected output schema and its binding to the trusted request scope."""
    validate_contract("ExecutionPolicySnapshot", snapshot)
    if (
        snapshot["run_id"] != ctx.run_id
        or snapshot["scope"] != ctx.scope.wire()
        or set(snapshot["allowed_capabilities"]) != set(ctx.scope.capabilities)
        or set(snapshot["allowed_capabilities"]).intersection(snapshot["denied_capabilities"])
    ):
        raise reject(
            "execution_snapshot_scope_denied",
            "Permission snapshot does not match its trusted caller",
            403,
            "authorization",
        )
    return snapshot


class ExecutionPolicyResolver(ExecutionPolicyPort):
    def __init__(self, store: PostgresRecordStore) -> None:
        self.store = store

    async def _run(self, ctx: TrustedExecutionContext) -> None:
        if not ctx.run_id:
            raise CapabilityUnavailable("execution.admitted_run")
        run = (await self.store.get(ctx.principal, "runs", ctx.run_id)).payload
        if (
            ctx.principal.id != ctx.scope.principal_id
            or ctx.scope.conversation_id != run["conversation_id"]
            or (ctx.conversation_id is not None and ctx.conversation_id != run["conversation_id"])
            or any(
                value is not None and value != run["task_id"]
                for value in (ctx.task_id, ctx.scope.task_id)
            )
            or ctx.scope.project_id is not None
        ):
            raise reject(
                "execution_scope_denied",
                "Execution scope is outside the owned Run",
                403,
                "authorization",
            )
        ledger = (await self.store.get(ctx.principal, "budget.ledgers", ctx.run_id)).payload
        if ledger["cancel_requested"] or run["status"] == "cancelled":
            raise reject("execution_cancelled", "Run has been cancelled", 409, "cancelled")
        if run["status"] not in ("preparing", "running", "verifying", "waiting_for_user"):
            raise reject("execution_run_unavailable", "Run is not active", 409)
        if any(
            datetime.fromisoformat(deadline.replace("Z", "+00:00")) <= datetime.now(UTC)
            for deadline in (ctx.deadline, run["budget"]["deadline"], ledger["deadline"])
        ):
            raise reject(
                "execution_deadline_expired", "Execution deadline has passed", 409, "timeout"
            )

    async def resolve(self, ctx: TrustedExecutionContext) -> Payload:
        validate_contract("TrustedExecutionContext", ctx.wire())
        await self._run(ctx)
        pin = ctx.capability_policy_ref.wire()
        policies: list[Payload] = []
        pins: list[Payload] = []
        seen: set[str] = set()
        for _ in range(MAX_POLICY_DEPTH):
            validate_contract("Ref", pin)
            if pin["kind"] != "policy" or set(pin) - {"kind", "id", "version", "content_hash"}:
                raise reject(
                    "execution_policy_invalid",
                    "Policy Ref cannot carry scope or location",
                    403,
                    "authorization",
                )
            if pin["id"] in seen:
                raise reject(
                    "execution_policy_cycle",
                    "Policy ancestry contains a cycle",
                    403,
                    "authorization",
                )
            seen.add(pin["id"])
            row = await self.store.get(ctx.principal, "execution.policies", pin["id"])
            policy = row.payload
            validate_contract("CapabilityPolicy", policy)
            digest = parameter_hash(policy)
            if (
                row.schema_name != "CapabilityPolicy"
                or str(row.revision) != pin["version"]
                or policy["id"] != pin["id"]
                or policy["revision"] != row.revision
                or (pin.get("content_hash") is not None and pin["content_hash"] != digest)
            ):
                raise reject("execution_policy_stale", "Execution policy revision changed", 412)
            if policy["feature_flag_refs"]:
                raise CapabilityUnavailable("execution.policy_feature_flags")
            if policies:
                child = policies[-1]
                if (
                    not set(child["allowed_capabilities"]).issubset(policy["allowed_capabilities"])
                    or not set(child["network_allowlist"]).issubset(policy["network_allowlist"])
                    or not scope_within(child["resource_scope"], policy["resource_scope"])
                ):
                    raise reject(
                        "execution_policy_escalation",
                        "Child policy expands parent authority",
                        403,
                        "authorization",
                    )
            policies.append(policy)
            pins.append(
                {
                    "kind": "policy",
                    "id": row.resource_id,
                    "version": str(row.revision),
                    "content_hash": digest,
                }
            )
            parent = policy.get("parent_policy_ref")
            if parent is None:
                break
            pin = parent
        else:
            raise reject(
                "execution_policy_depth",
                "Policy ancestry exceeds its bounded depth",
                403,
                "authorization",
            )
        allowed = set(policies[0]["allowed_capabilities"])
        denied: set[str] = set()
        networks = set(policies[0]["network_allowlist"])
        for policy in policies:
            allowed.intersection_update(policy["allowed_capabilities"])
            denied.update(policy["denied_capabilities"])
            networks.intersection_update(policy["network_allowlist"])
        requested = set(ctx.scope.capabilities)
        if (
            not requested
            or not requested.issubset(allowed)
            or requested.intersection(denied)
            or policies[0]["resource_scope"].get("conversation_id") != ctx.scope.conversation_id
            or not scope_within(ctx.scope.wire(), policies[0]["resource_scope"])
        ):
            raise reject(
                "execution_policy_denied",
                "Policy chain does not authorize this scope",
                403,
                "authorization",
            )
        # Detect concurrent changes encountered while traversing. This is not a dispatch lease.
        for actual in pins:
            current = await self.store.get(ctx.principal, "execution.policies", actual["id"])
            if (
                str(current.revision) != actual["version"]
                or parameter_hash(current.payload) != actual["content_hash"]
            ):
                raise reject(
                    "execution_policy_stale", "Policy changed during permission resolution", 412
                )
        await self._run(ctx)
        result = {
            "run_id": ctx.run_id,
            "scope": ctx.scope.wire(),
            "policy_refs": pins,
            "allowed_capabilities": sorted(requested),
            "denied_capabilities": sorted(denied),
            "network_allowlist": sorted(networks),
            "feature_flag_refs": [],
        }
        return require_snapshot(result, ctx)
