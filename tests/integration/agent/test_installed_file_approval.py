"""Actual SQL closed-file authority: equivalent request and await-time revocations."""

import asyncio

import pytest

from tests.integration.agent.test_installed_file_authority import (
    file_data_case as file_data_case,
)
from tests.integration.agent.test_installed_file_authority import (
    original_file_gate as original_file_gate,
)
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.tool.conftest import tool_case as tool_case
from uaw.infrastructure.installed_file_approval import InstalledFileApprovalAuthority
from uaw.shared.errors import DomainError


def joint(original):
    return InstalledFileApprovalAuthority(
        original.ledger,
        original.registry,
        original.configuration,
        original.access,
        original.resources,
        policies=original.policies,
    )


async def test_joint_file_authority_returns_identical_original_request(original_file_gate):
    gate, service, _, ctx, _ = original_file_gate
    original = service.authority
    actual = joint(original)
    assert await actual.current("actual-file-action", ctx) == await original.current(
        "actual-file-action", ctx
    )
    assert original.resources is actual.resources  # No shared mutation or new grant.


@pytest.mark.parametrize("source", ["role", "provider", "model", "budget", "configuration"])
async def test_source_changed_during_reader_await_rejects_joint_approval(
    original_file_gate, source
):
    gate, service, _, ctx, c = original_file_gate
    original = service.authority
    actual = joint(original)
    reader = original.resources
    calls = 0

    class ChangedReader:
        async def resolve(self, call, spec, context):
            nonlocal calls
            calls += 1
            refs = await reader.resolve(call, spec, context)
            if source == "role":
                await c.tool_access.revoke(
                    ctx,
                    meta("joint-await-revoke", 1),
                    authenticated_service=c.configuration.platform,
                )
            elif source in ("provider", "model"):
                owner = c.configuration.platform if source == "provider" else ctx.principal
                namespace = "providers" if source == "provider" else "model.policies"
                identifier = (
                    spec["provider_ref"]["id"] if source == "provider" else ctx.model_policy_ref.id
                )
                row = await c.records.get(owner, namespace, identifier)
                await c.records.delete(
                    owner,
                    namespace,
                    identifier,
                    expected_revision=row.revision,
                    request_id="joint-await-delete-" + source,
                )
            elif source == "budget":
                row = await c.records.get(ctx.principal, "budget.ledgers", ctx.run_id)
                await c.records.put(
                    ctx.principal,
                    "budget.ledgers",
                    ctx.run_id,
                    row.schema_name,
                    {**row.payload, "revision": row.revision + 1, "cancel_requested": True},
                    expected_revision=row.revision,
                    request_id="joint-await-cancel",
                )
            else:
                row = await c.records.get(
                    c.configuration.platform, "configuration.pointer", "current"
                )
                await c.records.delete(
                    c.configuration.platform,
                    "configuration.pointer",
                    "current",
                    expected_revision=row.revision,
                    request_id="joint-await-remove-config",
                )
            return refs

    actual.resources = ChangedReader()
    with pytest.raises(DomainError):
        await actual.current("actual-file-action", ctx)
    assert calls == 1
    assert original.resources is reader


@pytest.mark.parametrize("response", ["invalid", "cancel", "timeout", "mutated_inputs"])
async def test_checked_role_source_callback_boundaries(original_file_gate, response):
    _, service, _, ctx, _ = original_file_gate
    access = service.authority.access
    expected = await access.snapshot(ctx)

    async def check(tool_access, sources):
        if response == "invalid":
            return "allowed"  # Runtime protocol rejects non-None, never a grant.
        if response == "cancel":
            raise asyncio.CancelledError()
        if response == "timeout":
            await asyncio.sleep(10)
        else:
            sources.current_configuration.clear()  # Detached, no shared source mutation.

    if response == "mutated_inputs":
        assert await access.checked_snapshot(ctx, check=check) == expected
        assert await access.snapshot(ctx) == expected
    elif response == "timeout":
        with pytest.raises(TimeoutError):
            async with asyncio.timeout(0.05):
                await access.checked_snapshot(ctx, check=check)
    else:
        with pytest.raises((DomainError, asyncio.CancelledError)):
            await access.checked_snapshot(ctx, check=check)


async def test_joint_authority_never_borrows_different_permission_source(original_file_gate):
    _, service, _, ctx, _ = original_file_gate
    actual = joint(service.authority)
    actual.policies = None
    with pytest.raises(DomainError) as error:
        await actual.current("actual-file-action", ctx)
    assert error.value.failure.category == "dependency"


@pytest.mark.parametrize("field", ["conversation_id", "task_id", "model_policy_ref"])
async def test_joint_authority_requires_complete_original_context(original_file_gate, field):
    _, service, _, ctx, _ = original_file_gate
    with pytest.raises(DomainError):
        await joint(service.authority).current(
            "actual-file-action", ctx.model_copy(update={field: None})
        )
