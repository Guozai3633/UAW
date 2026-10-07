"""Authorization precedes small-catalogue retrieval; the model chooses candidates."""

from datetime import UTC, datetime
from typing import Any

from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import DomainError
from uaw.tool.errors import fail
from uaw.tool.ports import ToolAccess
from uaw.tool.registry import RegistryEntry, ToolRegistry


def check_access(access: ToolAccess, ctx: TrustedExecutionContext) -> None:
    if access.cancelled:
        raise fail("cancelled", "Run is cancelled", phase="policy_gate", category="cancelled")
    if datetime.fromisoformat(ctx.deadline.replace("Z", "+00:00")) <= datetime.now(UTC):
        raise fail(
            "deadline_exceeded", "Run deadline has expired", phase="policy_gate", category="timeout"
        )
    if access.policy_ref != ctx.capability_policy_ref:
        raise fail(
            "stale_resource",
            "Effective policy differs from the trusted version",
            phase="policy_gate",
            category="conflict",
            status=412,
        )
    for field in ("principal_id", "conversation_id", "task_id", "project_id"):
        if getattr(access.scope, field) != getattr(ctx.scope, field):
            raise fail(
                "permission_denied",
                "Access snapshot does not belong to this scope",
                phase="policy_gate",
                category="authorization",
                status=403,
            )
    if not set(access.scope.capabilities) <= set(ctx.scope.capabilities) or not set(
        r.model_dump_json() for r in access.scope.resource_refs
    ) <= set(r.model_dump_json() for r in ctx.scope.resource_refs):
        raise fail(
            "permission_denied",
            "Access snapshot broadens the trusted scope",
            phase="policy_gate",
            category="authorization",
            status=403,
        )


def require_entry(entry: RegistryEntry, access: ToolAccess) -> None:
    spec = entry.spec()
    effective = (
        set(access.scope.capabilities) & access.allowed_capabilities - access.denied_capabilities
    )
    if (
        not spec["categories"]
        or not set(spec["categories"]) <= access.role_categories
        or not set(spec["required_capabilities"]) <= effective
    ):
        raise fail(
            "permission_denied",
            "Tool is outside the effective role/capabilities",
            phase="policy_gate",
            category="authorization",
            status=403,
        )
    required_flags = {spec["feature_flag"]} if spec.get("feature_flag") else set()
    # Existing product flags apply even if a spec omits its optional feature_flag.
    if spec["effect"] == "process":
        required_flags.add("code_execution")
    if spec["effect"] == "workspace_write":
        required_flags.add("local_files")
    if not required_flags <= access.enabled_flags:
        raise fail(
            "feature_disabled",
            "Tool feature flag is disabled",
            phase="policy_gate",
            category="policy",
            status=403,
        )
    binding = entry.binding
    if (
        binding is None
        or not binding.implemented
        or binding.test_only
        or access.environment not in binding.environments
        or spec["provider_ref"] not in [ref.wire() for ref in access.active_provider_refs]
    ):
        raise fail(
            "dependency_unavailable",
            "No implemented adapter in this environment",
            phase="policy_gate",
            category="dependency",
            status=503,
        )


def discover(
    registry: ToolRegistry,
    query: str,
    categories: list[str],
    max_candidates: int,
    access: ToolAccess,
    ctx: TrustedExecutionContext,
) -> dict[str, Any]:
    check_access(access, ctx)
    revision, entries = registry.snapshot()
    candidates = []
    for entry in entries:
        try:
            require_entry(entry, access)
        except DomainError:
            continue
        spec = entry.spec()
        if categories and not set(spec["categories"]) & set(categories):
            continue
        text = (spec["id"] + " " + spec["description"]).casefold()
        tokens = query.casefold().split()
        exact = query.casefold() == spec["id"].casefold()
        score = 1.0 if exact else sum(token in text for token in tokens) / max(len(tokens), 1)
        if tokens and score == 0:
            continue
        candidates.append(
            {
                "tool_ref": registry.reference(entry),
                "description": spec["description"],
                "input_schema": spec["input_schema"],
                "effect": spec["effect"],
                "score": score,
            }
        )
    candidates.sort(key=lambda c: (-c["score"], c["tool_ref"]["id"], c["tool_ref"]["version"]))
    if not candidates:
        raise fail(
            "capability_gap",
            "No available tools match the bounded search",
            phase="discovery",
            category="dependency",
            status=503,
        )
    return {"tools": candidates[:max_candidates], "agents": [], "registry_revision": revision}
