"""Call-local root/approval observations; never an authority or permission cache."""

import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from uaw.shared.contracts import JsonObject, Ref, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.ports import RunnerRootSourcePort
from uaw.workspace.contracts import RunnerRootSnapshot

RootCheck = Callable[[JsonObject | None], Awaitable[None]]


async def checked_file_root(
    roots: RunnerRootSourcePort,
    device_id: str,
    workspace: Ref,
    ctx: TrustedExecutionContext,
    check: RootCheck,
) -> JsonObject:
    """Bracket metadata approval inside the owning source's fresh root checks.

    Only absent checked_current uses the legacy two independent observations.
    A present but failing implementation must never fall back or retry.
    """
    missing = object()
    operation = getattr(roots, "checked_current", missing)
    if operation is missing:
        await check(None)
        return await roots.current(device_id, workspace, ctx)
    if not callable(operation):
        raise reject("installed_root_protocol_invalid", "Root check is not callable", 503)
    original_context, original_workspace = ctx.wire(), workspace.wire()
    observed: JsonObject | None = None
    completed = False

    def snapshot(value: JsonObject) -> JsonObject:
        root = RunnerRootSnapshot.model_validate_json(json.dumps(value, allow_nan=False)).wire()
        if (
            root["owner"] != original_context["principal"]
            or root["device_id"] != device_id
            or root["workspace_ref"] != original_workspace
            or workspace not in ctx.scope.resource_refs
            or "file.read" not in root["allowed_actions"]
            or not set(root["allowed_actions"]) <= {"file.read", "file.list"}
        ):
            raise reject("installed_file_root_denied", "Original read root required", 403)
        if min(
            datetime.fromisoformat(str(root["expires_at"]).replace("Z", "+00:00")),
            datetime.fromisoformat(ctx.deadline.replace("Z", "+00:00")),
        ) <= datetime.now(UTC):
            raise reject("deadline_exceeded", "Root approval observation expired", 410, "timeout")
        return root

    async def observe(value: JsonObject) -> None:
        nonlocal observed, completed
        if observed is not None:
            raise reject("installed_root_protocol_invalid", "Repeated approval observation", 503)
        observed = snapshot(value)
        await check(json.loads(json.dumps(observed, allow_nan=False)))
        completed = True

    result = snapshot(await operation(device_id, workspace, ctx, check=observe))
    if (
        not completed
        or result != observed
        or ctx.wire() != original_context
        or workspace.wire() != original_workspace
    ):
        raise reject("installed_root_source_changed", "Root/approval observation changed", 412)
    return result
