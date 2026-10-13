"""Closed file.read approval checks within the owning Run/role source bracket."""

import json
from collections.abc import Awaitable, Callable
from copy import deepcopy

from uaw.run.execution_sources import RunExecutionSources, RunSourceSnapshot
from uaw.run.permissions import ExecutionPolicyResolver, require_snapshot
from uaw.run.tool_sources import RunToolAccessSources
from uaw.shared.contracts import JsonObject, Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.tool.authority import ToolApprovalAuthority, call_without_hash
from uaw.tool.discovery import check_access, require_entry
from uaw.tool.invocation.schema import normalize
from uaw.tool.ports import ToolAccess
from uaw.tool.providers.file_read import file_read_spec


class InstalledFileApprovalAuthority(ToolApprovalAuthority):
    """Same stored approval request; only exact actual A sources can use this graph.

    The generic authority remains unchanged for all other tools/custom adapters.
    This current never decides, registers or executes an action.
    """

    async def current(self, action_id: str, ctx: TrustedExecutionContext) -> JsonObject:
        return await self.checked_action(action_id, ctx)

    async def checked_action(
        self,
        action_id: str,
        ctx: TrustedExecutionContext,
        *,
        check: Callable[[JsonObject, RunSourceSnapshot], Awaitable[object]] | None = None,
    ) -> JsonObject:
        """Check original action metadata inside the existing fresh Run bracket."""
        access, resources = self.access, self.resources
        components = (
            self.ledger,
            self.registry,
            self.configuration,
            self.policies,
            access,
            resources,
        )
        if (
            type(access) is not RunToolAccessSources
            or type(access.runs) is not RunExecutionSources
            or type(access.runs.permissions) is not ExecutionPolicyResolver
            or self.policies is not access.runs.permissions
            or self.ledger.store is not access.store
            or self.ledger.store is not access.runs.store
            or self.configuration is not access.configuration
            or self.configuration is not access.runs.configuration
            or resources is None
            or ctx.model_policy_ref is None
            or ctx.conversation_id is None
            or ctx.task_id is None
        ):
            raise CapabilityUnavailable("file.original_joint_sources")
        call, spec, pinned = await self.ledger.action(action_id, ctx)
        provider = Ref.model_validate_json(json.dumps(spec["provider_ref"], allow_nan=False))
        entry = self.registry.get(call["tool_ref"])
        if (
            pinned != ctx
            or spec != file_read_spec(provider)
            or entry.spec() != spec
            or normalize(call_without_hash(call), self.registry) != call
        ):
            raise reject(
                "file_original_approval_denied", "Exact original file action required", 403
            )
        refs: tuple[Ref, ...] | None = None
        result: JsonObject | None = None

        def request(resolved: tuple[Ref, ...]) -> JsonObject:
            value: JsonObject = {
                "action_id": call["action_id"],
                "arguments_hash": call["arguments_hash"],
                "resource_refs": [ref.wire() for ref in resolved],
                "effect": spec["effect"],
                "summary": spec["description"],
                "expires_at": pinned.deadline,
            }
            validate_contract("ApprovalCreateRequest", value)
            return value

        async def metadata(tool_access: ToolAccess, sources: RunSourceSnapshot) -> None:
            nonlocal refs, result
            assert ctx.model_policy_ref is not None
            permission = require_snapshot(sources.permissions, ctx)
            if (
                permission["feature_flag_refs"]
                or not set(spec["required_capabilities"]) <= set(permission["allowed_capabilities"])
                or sources.admission["model_policy_ref"] != ctx.model_policy_ref.wire()
                or any(
                    provider.wire() not in config["provider_refs"]
                    for config in (sources.fixed_configuration, sources.current_configuration)
                )
            ):
                raise reject(
                    "file_original_approval_denied", "Original policy/model/provider required", 403
                )
            check_access(tool_access, ctx)
            require_entry(entry, tool_access)
            refs = await resources.resolve(call, spec, ctx)
            if len(refs) > 256 or any(ref not in ctx.scope.resource_refs for ref in refs):
                raise reject("file_original_approval_denied", "Resource scope differs", 403)
            result = request(refs)
            if check is not None and await check(deepcopy(result), deepcopy(sources)) is not None:
                raise reject("file_check_protocol_invalid", "Metadata check must return None", 503)

        await access.checked_snapshot(ctx, check=metadata)
        current_components = (
            self.ledger,
            self.registry,
            self.configuration,
            self.policies,
            self.access,
            self.resources,
        )
        if (
            refs is None
            or result is None
            or entry.spec() != spec
            or any(a is not b for a, b in zip(components, current_components, strict=True))
        ):
            raise reject("file_original_approval_denied", "Original registry/Reader changed", 412)
        return result
