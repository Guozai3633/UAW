"""Live approval authority derived from fixed SQL actions and authoritative Readers."""

from typing import Any, Protocol

from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.shared.configuration import ConfigurationService
from uaw.shared.contracts import JsonObject, Ref, TrustedExecutionContext
from uaw.shared.ports import ApprovalAuthorityPort
from uaw.shared.schema import validate_contract
from uaw.tool.discovery import check_access, require_entry
from uaw.tool.errors import fail
from uaw.tool.invocation.schema import normalize
from uaw.tool.ledger import ToolLedger, action_key
from uaw.tool.ports import ToolAccessPort
from uaw.tool.registry import ToolRegistry

Payload = dict[str, Any]


class ActionResourceReaderPort(Protocol):
    """Owning domain resolves every actual resource and current access/version.

    Must derive resources from the fixed call/spec, not a caller supplied list.
    Path strings or well formed Refs alone never grant access.
    """

    async def resolve(
        self, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> tuple[Ref, ...]: ...


class ToolApprovalAuthority(ApprovalAuthorityPort):
    def __init__(
        self,
        ledger: ToolLedger,
        registry: ToolRegistry,
        configuration: ConfigurationService,
        access: ToolAccessPort | None = None,
        resources: ActionResourceReaderPort | None = None,
    ) -> None:
        self.ledger, self.registry, self.configuration = ledger, registry, configuration
        self.access, self.resources = access, resources

    async def current(self, action_id: str, ctx: TrustedExecutionContext) -> Payload:
        call, spec, pinned = await self.ledger.action(action_id, ctx)
        if self.access is None or self.resources is None:
            raise fail(
                "dependency_unavailable",
                "Live role/environment/resource Reader is not wired",
                phase="authority",
                category="dependency",
                status=503,
            )
        entry = self.registry.get(call["tool_ref"])
        if entry.spec() != spec or normalize(call_without_hash(call), self.registry) != call:
            raise fail(
                "action_conflict",
                "Fixed call/spec no longer matches registration",
                phase="authority",
                category="conflict",
                status=409,
            )
        await self._policy(spec, ctx)
        access = await self.access.snapshot(ctx)
        check_access(access, ctx)
        require_entry(entry, access)
        refs = await self.resources.resolve(call, spec, ctx)
        if len(refs) > 256 or any(
            ref.wire() not in [r.wire() for r in ctx.scope.resource_refs] for ref in refs
        ):
            raise fail(
                "permission_denied",
                "Resolved resources exceed the trusted Run scope",
                phase="authority",
                category="authorization",
                status=403,
            )
        # Re-read cancellation, flags and policies after Reader await as well.
        await self._policy(spec, ctx)
        refreshed = await self.access.snapshot(ctx)
        check_access(refreshed, ctx)
        require_entry(entry, refreshed)
        result = {
            "action_id": call["action_id"],
            "arguments_hash": call["arguments_hash"],
            "resource_refs": [r.wire() for r in refs],
            "effect": spec["effect"],
            "summary": spec["description"],
            "expires_at": pinned.deadline,
        }
        validate_contract("ApprovalCreateRequest", result)
        return result

    async def _policy(self, spec: Payload, ctx: TrustedExecutionContext) -> None:
        store: PostgresRecordStore = self.ledger.store
        run = (await store.get(ctx.principal, "runs", ctx.run_id or "")).payload
        budget = (await store.get(ctx.principal, "budget.ledgers", ctx.run_id or "")).payload
        if (
            run["conversation_id"] != ctx.conversation_id
            or run["task_id"] != ctx.task_id
            or ctx.scope.conversation_id != ctx.conversation_id
            or ctx.scope.task_id != ctx.task_id
        ):
            raise fail(
                "permission_denied",
                "Current Run is outside the fixed action scope",
                phase="authority",
                category="authorization",
                status=403,
            )
        if budget["cancel_requested"] or run["status"] == "cancelled":
            raise fail("cancelled", "Run was cancelled", phase="authority", category="cancelled")
        if run["status"] not in ("preparing", "running", "verifying", "waiting_for_user"):
            raise fail(
                "stale_resource",
                "Run is no longer active",
                phase="authority",
                category="conflict",
                status=412,
            )
        binding = (await store.get(ctx.principal, "run.bindings", ctx.run_id or "")).payload
        if (
            ctx.model_policy_ref is None
            or binding["model_policy_ref"] != ctx.model_policy_ref.wire()
        ):
            raise fail(
                "action_conflict",
                "Fixed user model binding changed",
                phase="authority",
                category="conflict",
                status=409,
            )
        from datetime import UTC, datetime

        if min(
            datetime.fromisoformat(s.replace("Z", "+00:00"))
            for s in (ctx.deadline, budget["deadline"])
        ) <= datetime.now(UTC):
            raise fail(
                "deadline_exceeded", "Run deadline expired", phase="authority", category="timeout"
            )
        # Parent policies have the same owner's execution namespace. No implicit fallback.
        policy_ref = ctx.capability_policy_ref
        seen: set[str] = set()
        while True:
            if policy_ref.kind != "policy" or policy_ref.id in seen or len(seen) >= 16:
                raise fail(
                    "permission_denied",
                    "Policy chain is unsupported or cyclic",
                    phase="authority",
                    category="authorization",
                    status=403,
                )
            seen.add(policy_ref.id)
            row = await store.get(ctx.principal, "execution.policies", policy_ref.id)
            policy = row.payload
            validate_contract("CapabilityPolicy", policy)
            if policy["feature_flag_refs"]:
                raise fail(
                    "dependency_unavailable",
                    "Policy flag reference Reader is not wired",
                    phase="authority",
                    category="dependency",
                    status=503,
                )
            selector = policy["resource_scope"]
            if (
                str(row.revision) != policy_ref.version
                or policy["revision"] != row.revision
                or not set(ctx.scope.capabilities) <= set(policy["allowed_capabilities"])
                or set(ctx.scope.capabilities) & set(policy["denied_capabilities"])
                or any(
                    selector.get(k) is not None and selector[k] != getattr(ctx.scope, k)
                    for k in ("conversation_id", "task_id", "project_id")
                )
                or any(r.wire() not in selector["resource_refs"] for r in ctx.scope.resource_refs)
                or not set(spec["required_capabilities"]) <= set(ctx.scope.capabilities)
            ):
                raise fail(
                    "permission_denied",
                    "Current policy chain denies the fixed action",
                    phase="authority",
                    category="authorization",
                    status=403,
                )
            if "parent_policy_ref" not in policy:
                break
            policy_ref = Ref.model_validate(policy["parent_policy_ref"])
        fixed = await self.configuration.snapshot(binding["configuration_ref"])
        current = await self.configuration.current()
        provider = spec["provider_ref"]
        if any(provider not in config["provider_refs"] for config in (fixed, current)):
            raise fail(
                "dependency_unavailable",
                "Fixed provider is not currently configured",
                phase="authority",
                category="dependency",
                status=503,
            )
        row = await store.get(self.configuration.platform, "providers", provider["id"])
        if str(row.revision) != provider["version"] or row.payload["state"] != "active":
            raise fail(
                "dependency_unavailable",
                "Provider is unavailable or revoked",
                phase="authority",
                category="dependency",
                status=503,
            )
        flags = {spec["feature_flag"]} if spec.get("feature_flag") else set()
        if spec["effect"] == "process":
            flags.add("code_execution")
        if spec["effect"] == "workspace_write":
            flags.add("local_files")
        for flag in flags:
            await self.configuration.require_capability(
                flag,
                binding["configuration_ref"],
                ctx.scope.wire(),
                implemented=True,
                boundary="call",
            )

    async def check(self, request: JsonObject, ctx: TrustedExecutionContext) -> None:
        validate_contract("ApprovalCreateRequest", request)
        expected = await self.current(str(request["action_id"]), ctx)
        fixed = await self.ledger.get(
            "tool.approval.requests", action_key(ctx, str(request["action_id"])), ctx
        )
        if expected != request or (fixed is not None and fixed != request):
            raise fail(
                "approval_action_stale",
                "Approval differs from the fixed actual action",
                phase="authority",
                category="conflict",
                status=412,
            )


def call_without_hash(call: Payload) -> Payload:
    return {k: v for k, v in call.items() if k != "arguments_hash"}
