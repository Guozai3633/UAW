"""Current Run, policy and authenticated fixed-model sources for internal adapters."""

from dataclasses import dataclass
from typing import Any

from uaw.context.seed import revision
from uaw.infrastructure.db.records import PostgresRecordStore, parameter_hash
from uaw.run.permissions import ExecutionPolicyResolver, require_snapshot
from uaw.shared.configuration import ConfigurationService
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import parse_json, validate_contract

Payload = dict[str, Any]


@dataclass(frozen=True)
class RunDataSnapshot:
    admission: Payload
    fixed_configuration: Payload
    current_configuration: Payload


@dataclass(frozen=True)
class RunSourceSnapshot(RunDataSnapshot):
    permissions: Payload


class RunExecutionSources:
    """Consumes trusted contexts; never creates authentication from model claims.

    The deployment/transport authenticates the principal before constructing ctx.
    Role bindings separately pin the complete principal including its session.
    Model provider protocol/credentials are still checked by Model Runtime when
    generating; a Tool call does not need permission to call the model endpoint.
    """

    def __init__(
        self,
        store: PostgresRecordStore,
        configuration: ConfigurationService,
        permissions: ExecutionPolicyResolver,
    ) -> None:
        self.store, self.configuration, self.permissions = store, configuration, permissions

    async def current(self, ctx: TrustedExecutionContext) -> RunSourceSnapshot:
        access = require_snapshot(await self.permissions.resolve(ctx), ctx)
        data = await self.data(ctx)
        again = require_snapshot(await self.permissions.resolve(ctx), ctx)
        if again != access:
            raise reject("run_source_changed", "Execution permission changed", 412)
        return RunSourceSnapshot(
            data.admission, data.fixed_configuration, data.current_configuration, access
        )

    async def data(self, ctx: TrustedExecutionContext) -> RunDataSnapshot:
        """Owned fixed-model data after cancellation/expiry; no execution grant.

        Callers must separately check current complete session/data ownership,
        e.g. the independently registered Tool binding, and actual resource Reader.
        """
        validate_contract("TrustedExecutionContext", ctx.wire())
        if ctx.principal.kind != "user" or not ctx.principal.auth_session_id:
            raise reject("run_principal_denied", "Authenticated user session required", 403)
        run = (await self.store.get(ctx.principal, "runs", ctx.run_id or "")).payload
        if (
            ctx.scope.principal_id != ctx.principal.id
            or ctx.conversation_id != run["conversation_id"]
            or ctx.scope.conversation_id != run["conversation_id"]
            or ctx.task_id != run["task_id"]
            or ctx.scope.task_id != run["task_id"]
            or ctx.scope.project_id is not None
        ):
            raise reject("run_source_scope_denied", "Context differs from the owned Run", 403)
        admission_row = await self.store.get(ctx.principal, "run.bindings", run["id"])
        admission = admission_row.payload
        validate_contract("RunAdmissionBinding", admission)
        pin = admission["model_policy_ref"]
        if ctx.model_policy_ref is None or ctx.model_policy_ref.wire() != pin:
            raise reject("run_model_binding_stale", "Fixed Run model policy differs", 412)
        if pin["kind"] != "policy" or set(pin) - {"kind", "id", "version", "content_hash"}:
            raise reject("run_model_source_invalid", "Invalid model policy reference", 403)
        row = await self.store.get(ctx.principal, "model.policies", pin["id"])
        policy = row.payload
        validate_contract("ResolvedModelPolicy", policy)
        if (
            row.schema_name != "ResolvedModelPolicy"
            or row.revision != revision(pin, "policy")
            or policy["revision"] != row.revision
            or policy["id"] != pin["id"]
            or (pin.get("content_hash") and pin["content_hash"] != parameter_hash(policy))
            or policy["mode"] != "explicit"
        ):
            raise reject("run_model_source_invalid", "Current fixed-model source differs", 412)
        source = policy["source_input_ref"]
        original = (
            await self.store.get(
                ctx.principal, "inputs", source["id"], revision=revision(source, "input")
            )
        ).payload
        if original["conversation_id"] != run["conversation_id"] or parse_json(
            original["text"]
        ) != {"mode": "explicit", "model_id": policy["fixed_model_id"]}:
            raise reject("run_model_source_invalid", "Authenticated model selection differs", 403)
        fixed = await self.configuration.snapshot(admission["configuration_ref"])
        # No replacement from current catalogue or role model candidates.
        await self.configuration.require_model(policy["fixed_model_id"], fixed)
        current = await self.configuration.current()
        # Re-read after awaits: these snapshots are observations, never a send lease.
        if (await self.store.get(ctx.principal, "run.bindings", run["id"])) != admission_row or (
            await self.store.get(ctx.principal, "model.policies", pin["id"])
        ) != row:
            raise reject("run_source_changed", "Run or fixed-model source changed", 412)
        return RunDataSnapshot(admission, fixed, current)
