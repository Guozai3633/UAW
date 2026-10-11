"""Controlled route sources: closing during the final device wait cannot escape."""

import asyncio
from types import SimpleNamespace

import pytest

from uaw.infrastructure.installed_files import InstalledFileRoute
from uaw.shared.contracts import Principal, Ref, Scope, TrustedExecutionContext
from uaw.shared.errors import DomainError


@pytest.mark.parametrize("change", ["stop", "done", "replace"])
async def test_final_device_wait_rechecks_original_lifecycle(monkeypatch, change):
    owner = Principal(id="route-user", kind="user", auth_session_id="web-session-route")
    workspace = Ref(kind="workspace", id="route-workspace", version="1")
    ctx = TrustedExecutionContext(
        principal=owner,
        scope=Scope(principal_id=owner.id, resource_refs=(workspace,), capabilities=("file.read",)),
        capability_policy_ref=Ref(kind="policy", id="controlled-policy", version="1"),
        operation_id="controlled-operation",
        attempt_id="controlled-attempt",
        trace_id="controlled-trace",
        deadline="2099-01-01T00:00:00Z",
    )
    device = {"revision": 1}
    grant = SimpleNamespace(device_id="controlled-device")
    entry = SimpleNamespace(stopping=False, done=asyncio.Event(), launch=None)
    lifecycle = SimpleNamespace(active=entry)
    reads = 0

    async def current(identifier, *, authenticated_principal):
        nonlocal reads
        assert identifier == grant.device_id and authenticated_principal == owner
        reads += 1
        if reads == 2:
            if change == "stop":
                entry.stopping = True
            elif change == "done":
                entry.done.set()
            else:
                lifecycle.active = SimpleNamespace(launch=entry.launch)
        return device

    launch = SimpleNamespace(
        connection=SimpleNamespace(devices=SimpleNamespace(current=current)), control_key=object()
    )
    entry.launch = launch

    async def owned_ready(actor, pin):
        assert actor == owner and pin == workspace
        return launch

    async def current_root(original):
        assert original is launch
        return grant

    lifecycle.owned_ready = owned_ready
    lifecycle.owned_source = owned_ready
    monkeypatch.setattr("uaw.infrastructure.installed_files.current_root", current_root)
    with pytest.raises(DomainError) as denied:
        await InstalledFileRoute(lifecycle).current(workspace, ctx)
    assert reads == 2 and denied.value.failure.category == "dependency"
