"""Controlled component fixtures; no model or Runner execution is represented."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from uaw.shared.contracts import Principal, Ref, Scope, TrustedExecutionContext
from uaw.tool.ports import ToolAccess
from uaw.tool.registry import AdapterBinding, ToolRegistry


@pytest.fixture
def ctx():
    return TrustedExecutionContext(
        principal=Principal(id="user-c", kind="user", auth_session_id="session-c"),
        scope=Scope(
            principal_id="user-c",
            conversation_id="conversation-c",
            task_id="task-c",
            capabilities=("content.read",),
        ),
        conversation_id="conversation-c",
        task_id="task-c",
        run_id="run-c",
        agent_id="agent-c",
        operation_id="operation-c",
        trace_id="trace-c",
        attempt_id="attempt-1",
        deadline=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        capability_policy_ref=Ref(kind="policy", id="policy-c", version="1"),
        model_policy_ref=Ref(kind="policy", id="fixed-user-model", version="1"),
    )


@pytest.fixture
def spec():
    return {
        "id": "content.read",
        "version": "v1",
        "description": "Read exact supplied content",
        "categories": ["content"],
        "required_capabilities": ["content.read"],
        "effect": "read",
        "provider_ref": {"kind": "provider", "id": "fixture-provider", "version": "1"},
        "retry_policy_ref": {"kind": "policy", "id": "no-automatic-retry", "version": "1"},
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "count": {"type": "integer", "minimum": 1},
                "optional": {"type": "null"},
            },
            "required": ["text", "count"],
            "additionalProperties": False,
        },
        "output_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    }


@pytest.fixture
def binding(spec):
    # These tests exercise declared binding metadata, never a live adapter or product catalogue.
    return AdapterBinding(
        Ref.model_validate(spec["provider_ref"]), frozenset({"component-test"}), implemented=True
    )


@pytest.fixture
def registry(spec, binding):
    registry = ToolRegistry()
    registry.register(spec, expected_revision=0, binding=binding)
    return registry


@pytest.fixture
def call(registry):
    return {
        "tool_ref": registry.reference(registry.snapshot()[1][0]),
        "arguments": {"text": "  原文\r\nKeep\u0301 exact  ", "count": 2},
        "action_id": "action-c",
    }


class FixtureAccess:
    def __init__(self, ctx, *, changes=None):
        self.value = ToolAccess(
            ctx.capability_policy_ref,
            ctx.scope,
            frozenset({"content"}),
            frozenset({"content.read"}),
            frozenset(),
            frozenset(),
            "component-test",
            (Ref(kind="provider", id="fixture-provider", version="1"),),
        )
        self.changes = changes or {}
        self.calls = 0

    async def snapshot(self, ctx):
        self.calls += 1
        return replace(self.value, **self.changes)


@pytest.fixture
def access(ctx):
    return FixtureAccess(ctx)
