"""Read-only original file decision inside the closed Run/action source bracket.

Approval creation, decisions and expiry sealing retain ApprovalService. Each
current metadata set is a fresh SQL statement, not an authorization cache. No
tool/OS effect belongs in this service; the owning native root bracket and D
execution checkpoints remain independent requirements.
"""

import asyncio
import json
from datetime import UTC, datetime

from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.installed_file_approval import InstalledFileApprovalAuthority
from uaw.infrastructure.installed_tool_authority import InstalledFileResources
from uaw.run.approval import ApprovalService, instant
from uaw.run.execution_sources import RunSourceSnapshot
from uaw.run.permissions import ExecutionPolicyResolver, require_snapshot
from uaw.run.tool_sources import RunToolAccessSources
from uaw.shared.configuration import ConfigurationService
from uaw.shared.contracts import JsonObject, Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import Record


class InstalledFileDecision(ApprovalService):
    async def recheck(
        self, approval_ref: Ref, request: JsonObject, ctx: TrustedExecutionContext
    ) -> JsonObject:
        authority = self.authority
        if (
            type(authority) is not InstalledFileApprovalAuthority
            or not isinstance(authority, InstalledFileApprovalAuthority)
            or type(self.store) is not PostgresRecordStore
            or type(self.configuration) is not ConfigurationService
            or type(self.permissions) is not ExecutionPolicyResolver
            or type(authority.access) is not RunToolAccessSources
            or type(authority.resources) is not InstalledFileResources
            or not isinstance(authority.resources, InstalledFileResources)
            or authority.resources.observed is None
            or self.store is not self.configuration.store
            or self.store is not self.permissions.store
            or authority.ledger.store is not self.store
            or authority.configuration is not self.configuration
            or authority.policies is not self.permissions
            or authority.access.store is not self.store
            or authority.access.runs.permissions is not self.permissions
        ):
            raise CapabilityUnavailable("file.original_decision_sources")
        validate_contract("ApprovalCreateRequest", request)
        request = json.loads(json.dumps(request, allow_nan=False))
        caller = ctx.wire()
        store, configuration, permissions = self.store, self.configuration, self.permissions
        access, resources = authority.access, authority.resources
        ledger, registry = authority.ledger, authority.registry
        authentication = permissions.authentication_check
        controller = configuration.platform.wire()

        def unchanged() -> None:
            if (
                self.authority is not authority
                or self.store is not store
                or self.configuration is not configuration
                or self.permissions is not permissions
                or configuration.store is not store
                or permissions.store is not store
                or configuration.platform.wire() != controller
                or permissions.authentication_check is not authentication
                or authority.access is not access
                or authority.resources is not resources
                or authority.policies is not permissions
                or authority.ledger is not ledger
                or authority.ledger.store is not store
                or authority.registry is not registry
                or authority.configuration is not configuration
                or ctx.wire() != caller
                or instant(ctx.deadline) <= datetime.now(UTC)
            ):
                raise reject("approval_action_stale", "Original approval sources changed", 412)

        seconds = max(0, (instant(ctx.deadline) - datetime.now(UTC)).total_seconds())
        async with (
            asyncio.timeout(min(10, seconds)),
            store.current_reads(),
            store.current_witness(),
        ):
            # Keep the original durable expiry refresh; no new decision or grant.
            approval = await self.get(ctx.principal, approval_ref.id)
            binding_row = await store.get(ctx.principal, "approval.bindings", approval_ref.id)
            binding = binding_row.payload
            previous = TrustedExecutionContext.model_validate_json(json.dumps(binding["context"]))
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
                raise reject("approval_action_stale", "Original approval is not current", 412)
            addresses = (
                ("approvals", approval_ref.id),
                ("approval.bindings", approval_ref.id),
                ("approval.grants", approval_ref.id),
                ("runs", previous.run_id or ""),
                ("budget.ledgers", previous.run_id or ""),
                ("run.bindings", previous.run_id or ""),
                ("conversations", previous.conversation_id or ""),
            )
            before = await store.get_current_many(ctx.principal, addresses)
            policy_ref = binding["approval_policy_ref"]
            policy = await store.get(configuration.platform, "policies", policy_ref["id"])

            def validate(
                rows: tuple[Record, ...], rule: Record, sources: RunSourceSnapshot
            ) -> None:
                decision, original, grant, run, ledger, admission, conversation = rows
                if (
                    decision.payload != approval
                    or decision.revision != approval["revision"]
                    or original != binding_row
                    or admission.payload["configuration_ref"] != binding["configuration_ref"]
                ):
                    raise reject("approval_action_stale", "Stored approval binding changed", 412)
                validate_contract("ApprovalRequest", decision.payload)
                validate_contract("ApprovalBinding", original.payload)
                validate_contract("ApprovalGrant", grant.payload)
                if (
                    previous.principal != ctx.principal
                    or previous.scope.conversation_id != run.payload["conversation_id"]
                    or previous.conversation_id != run.payload["conversation_id"]
                    or previous.task_id != run.payload["task_id"]
                    or previous.scope.task_id != run.payload["task_id"]
                    or previous.scope.project_id is not None
                ):
                    raise reject("approval_scope_denied", "Approval is outside the owned Run", 403)
                if ledger.payload["cancel_requested"] or run.payload["status"] == "cancelled":
                    raise reject("approval_cancelled", "Original Run cancelled", 412)
                if datetime.now(UTC) >= min(
                    instant(previous.deadline),
                    instant(ledger.payload["deadline"]),
                    instant(binding["request"]["expires_at"]),
                ):
                    raise reject("approval_expired", "Original approval expired", 412)
                if run.payload["status"] not in (
                    "preparing",
                    "running",
                    "verifying",
                    "waiting_for_user",
                ):
                    raise reject("approval_stale", "Original Run inactive", 412)
                if (
                    not (
                        sources.fixed_configuration["approval_policy_ref"]
                        == sources.current_configuration["approval_policy_ref"]
                        == policy_ref
                    )
                    or str(rule.revision) != policy_ref["version"]
                ):
                    raise reject("approval_policy_stale", "Original approval policy differs", 412)
                validate_contract("ApprovalPolicy", rule.payload)
                if rule.payload["rules"]:
                    raise CapabilityUnavailable("approval.rule_evaluation")
                if conversation.payload["approval_mode"] != "manual" or (
                    "manual" not in rule.payload["allowed_modes"]
                ):
                    raise CapabilityUnavailable("non_manual_approval")
                require_snapshot(sources.permissions, previous)
                if any(
                    ref not in [r.wire() for r in previous.scope.resource_refs]
                    for ref in binding["request"]["resource_refs"]
                ):
                    raise reject(
                        "approval_permission_stale", "Original resource scope differs", 412
                    )

            async def metadata(actual: JsonObject, sources: RunSourceSnapshot) -> None:
                if actual != request:
                    raise reject("approval_action_stale", "Original action metadata differs", 412)
                validate(before, policy, sources)
                after = await store.get_current_many(ctx.principal, addresses)
                after_policy = await store.get(configuration.platform, "policies", policy_ref["id"])
                validate(after, after_policy, sources)
                if after != before or after_policy != policy:
                    raise reject(
                        "approval_action_stale", "Original decision changed while waiting", 412
                    )
                unchanged()

            await authority.checked_action(str(request["action_id"]), previous, check=metadata)
            unchanged()
        unchanged()  # Includes the outer witness/connection cleanup await.
        result: JsonObject = json.loads(json.dumps(before[2].payload, allow_nan=False))
        return result
