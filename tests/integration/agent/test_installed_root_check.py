"""Joint callback protocol boundaries, not proof of native authority or latency."""

import asyncio
import copy
import json
from pathlib import Path

import pytest

from uaw.infrastructure.installed_root_check import checked_file_root
from uaw.infrastructure.installed_tool_authority import InstalledFileResources
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import DomainError
from uaw.tool.invocation.schema import normalize
from uaw.tool.providers.file_read import file_read_spec
from uaw.tool.registry import ToolRegistry


@pytest.fixture
def root_case():
    examples = json.loads(Path("contracts/examples.json").read_text(encoding="utf-8"))["examples"]
    workspace = Ref(kind="workspace", id="joint-root-workspace", version="1")
    context = examples["TrustedExecutionContext"]
    context["deadline"] = "2099-01-01T00:00:00Z"
    context["scope"]["resource_refs"] = [workspace.wire()]
    ctx = TrustedExecutionContext.model_validate_json(json.dumps(context))
    root = {
        **examples["RunnerRootSnapshot"],
        "workspace_ref": workspace.wire(),
        "allowed_actions": ["file.read"],
        "expires_at": context["deadline"],
    }
    return ctx, workspace, root


class Roots:
    def __init__(self, root):
        self.root, self.events = root, []

    async def current(self, device, workspace, ctx):
        self.events.append("legacy")
        return copy.deepcopy(self.root)

    async def checked_current(self, device, workspace, ctx, *, check):
        self.events.append("before")
        first = copy.deepcopy(self.root)
        await check(first)
        self.events.append("after")
        return copy.deepcopy(self.root)


async def test_call_local_reader_between_actual_root_observations(root_case):
    ctx, workspace, root = root_case
    roots = Roots(root)
    provider = Ref(kind="provider", id="joint-root-provider", version="1")
    spec = file_read_spec(provider)
    registry = ToolRegistry()
    registry.register(spec, expected_revision=0)
    call = normalize(
        {
            "tool_ref": registry.reference(registry.snapshot()[1][0]),
            "arguments": {"workspace_ref": workspace.wire(), "path": "file.txt"},
            "action_id": "joint-root-action",
        },
        registry,
    )

    async def check(observed):
        roots.events.append("approval")
        resources = InstalledFileResources(roots, root["device_id"], observed=observed)
        assert await resources.resolve(call, spec, ctx) == (workspace,)
        observed["binding_revision"] += 1  # detached callback input cannot rewrite root evidence

    result = await checked_file_root(roots, root["device_id"], workspace, ctx, check)
    assert result == root
    assert roots.events == ["before", "approval", "after"]


async def test_changed_root_after_approval_rejects_without_legacy_fallback(root_case):
    ctx, workspace, root = root_case
    roots = Roots(root)

    async def check(observed):
        roots.root = {**root, "binding_revision": root["binding_revision"] + 1}

    with pytest.raises(DomainError) as error:
        await checked_file_root(roots, root["device_id"], workspace, ctx, check)
    assert error.value.failure.code == "installed_root_source_changed"
    assert "legacy" not in roots.events


@pytest.mark.parametrize("mode", ["missing_callback", "twice", "expired", "wrong_owner", "error"])
async def test_present_invalid_source_never_falls_back(root_case, mode):
    ctx, workspace, root = root_case

    class Invalid(Roots):
        async def checked_current(self, device, workspace, ctx, *, check):
            if mode == "error":
                raise RuntimeError("source failed")
            if mode == "missing_callback":
                return self.root
            value = copy.deepcopy(self.root)
            if mode == "expired":
                value["expires_at"] = "2000-01-01T00:00:00Z"
            if mode == "wrong_owner":
                value["owner"]["auth_session_id"] = "different-original-session"
            await check(value)
            if mode == "twice":
                await check(value)
            return value

    roots = Invalid(root)

    async def check(observed):
        pass

    with pytest.raises((DomainError, RuntimeError)):
        await checked_file_root(roots, root["device_id"], workspace, ctx, check)
    assert roots.events == []


async def test_cancelled_approval_does_not_return_root_or_fall_back(root_case):
    ctx, workspace, root = root_case
    roots = Roots(root)

    async def check(observed):
        raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        await checked_file_root(roots, root["device_id"], workspace, ctx, check)
    assert roots.events == ["before"]


async def test_legacy_source_retains_independent_check_then_root(root_case):
    ctx, workspace, root = root_case
    events = []

    class Legacy:
        async def current(self, device, workspace, ctx):
            events.append("root")
            return root

    async def check(observed):
        assert observed is None
        events.append("approval")

    assert await checked_file_root(Legacy(), root["device_id"], workspace, ctx, check) == root
    assert events == ["approval", "root"]


async def test_present_noncallable_joint_source_is_rejected(root_case):
    ctx, workspace, root = root_case
    roots = Roots(root)
    roots.checked_current = None

    async def check(observed):
        raise AssertionError("Invalid source must not invoke approval")

    with pytest.raises(DomainError) as error:
        await checked_file_root(roots, root["device_id"], workspace, ctx, check)
    assert error.value.failure.code == "installed_root_protocol_invalid"
    assert roots.events == []
