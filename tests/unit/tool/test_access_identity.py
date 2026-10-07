from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from uaw.shared.errors import DomainError
from uaw.tool.discovery import check_access
from uaw.tool.facade import ToolFacade
from uaw.tool.identity import ActionIdentities, require_safe_recovery
from uaw.tool.invocation.schema import normalize
from uaw.tool.registry import ToolRegistry


async def test_discovery_returns_only_candidates_and_invocation_remains_unavailable(
    registry, access, ctx, call
):
    facade = ToolFacade(registry, access)
    found = await facade.discover({"query": "content.read", "max_candidates": 1}, ctx)
    assert found["kind"] == "ok"
    assert found["payload"]["tools"][0]["tool_ref"] == call["tool_ref"]
    assert found["payload"]["tools"][0]["score"] == 1
    denied = await facade.invoke(call, ctx)
    assert denied["failure"]["code"] == "dependency_unavailable"
    assert denied["failure"]["failed_phase"] == "precheck"


@pytest.mark.parametrize(
    "changes",
    [
        {"role_categories": frozenset()},
        {"allowed_capabilities": frozenset()},
        {"denied_capabilities": frozenset({"content.read"})},
        {"environment": "unapproved"},
        {"active_provider_refs": ()},
    ],
)
async def test_filtering_precedes_search_and_forged_direct_call_cannot_bypass(
    registry, access, ctx, call, changes
):
    access.changes = changes
    facade = ToolFacade(registry, access)
    hidden = await facade.discover({"query": "content.read", "max_candidates": 1}, ctx)
    assert hidden["failure"]["code"] == "capability_gap"
    assert "fixture-provider" not in str(hidden)
    assert (await facade.invoke(call, ctx))["kind"] in {"denied", "failed"}


async def test_feature_flag_and_test_only_or_unimplemented_adapter_are_not_published(
    spec, binding, access, ctx
):
    for bound in (None, replace(binding, implemented=False), replace(binding, test_only=True)):
        registry = ToolRegistry()
        registry.register(spec, expected_revision=0, binding=bound)
        result = await ToolFacade(registry, access).discover(
            {"query": "content.read", "max_candidates": 1}, ctx
        )
        assert result["kind"] == "failed"
    spec["feature_flag"] = "local_files"
    registry = ToolRegistry()
    registry.register(spec, expected_revision=0, binding=binding)
    facade = ToolFacade(registry, access)
    call = {
        "tool_ref": registry.reference(registry.snapshot()[1][0]),
        "arguments": {"text": "original", "count": 1},
        "action_id": "a",
    }
    assert (await facade.invoke(call, ctx))["failure"]["code"] == "feature_disabled"
    access.changes = {"enabled_flags": frozenset({"local_files"})}
    assert (await facade.discover({"query": "content.read", "max_candidates": 1}, ctx))[
        "kind"
    ] == "ok"


async def test_current_revocation_cancellation_deadline_and_missing_access(
    registry, access, ctx, call
):
    facade = ToolFacade(registry, access)
    await facade.discover({"query": "content.read", "max_candidates": 1}, ctx)
    access.changes = {"denied_capabilities": frozenset({"content.read"})}
    assert (await facade.invoke(call, ctx))["kind"] == "denied"
    access.changes = {"cancelled": True}
    assert (await facade.invoke(call, ctx))["kind"] == "cancelled"
    access.changes = {}
    expired = ctx.model_copy(
        update={"deadline": (datetime.now(UTC) - timedelta(seconds=1)).isoformat()}
    )
    assert (await facade.invoke(call, expired))["failure"]["code"] == "deadline_exceeded"
    assert (await ToolFacade(registry).invoke(call, ctx))["failure"][
        "code"
    ] == "dependency_unavailable"


def test_foreign_or_broader_snapshot_is_rejected(access, ctx):
    for scope in (
        ctx.scope.model_copy(update={"principal_id": "other"}),
        ctx.scope.model_copy(update={"capabilities": ("content.read", "process.exec")}),
    ):
        with pytest.raises(DomainError):
            check_access(replace(access.value, scope=scope), ctx)
    with pytest.raises(DomainError):
        check_access(
            replace(
                access.value,
                policy_ref=ctx.capability_policy_ref.model_copy(update={"version": "2"}),
            ),
            ctx,
        )


def test_action_not_attempt_identity_and_fixed_version_boundaries(registry, call, ctx):
    guard = ActionIdentities(capacity=1)
    fixed = normalize(call, registry)
    assert guard.bind(fixed, ctx) is False
    assert guard.bind(fixed, ctx.model_copy(update={"attempt_id": "attempt-2"})) is True
    with pytest.raises(DomainError) as exc:
        guard.bind({**fixed, "arguments_hash": "0" * 64}, ctx)
    assert exc.value.failure.code == "action_conflict"
    with pytest.raises(DomainError):
        guard.bind(
            fixed,
            ctx.model_copy(
                update={
                    "model_policy_ref": ctx.model_policy_ref.model_copy(update={"version": "2"})
                }
            ),
        )
    with pytest.raises(DomainError) as exc:
        guard.bind({**fixed, "action_id": "new-action"}, ctx)
    assert exc.value.failure.code == "identity_capacity"
    with pytest.raises(DomainError):
        guard.bind(fixed, ctx.model_copy(update={"run_id": None}))


@pytest.mark.parametrize(
    "effect", ["internal_write", "workspace_write", "external_write", "process", "credential"]
)
def test_unknown_or_pending_write_effect_is_not_retryable(effect):
    for state in ("unknown", "pending", "confirmed"):
        with pytest.raises(DomainError) as exc:
            require_safe_recovery(effect, state)
        assert exc.value.failure.retryable is False
    with pytest.raises(ValueError):
        require_safe_recovery(effect, "none")
    require_safe_recovery("read", "unknown")


async def test_effect_is_trusted_spec_and_cannot_omit_mandatory_product_flags(
    spec, binding, access, ctx
):
    for effect in ("process", "workspace_write"):
        spec["effect"] = effect
        registry = ToolRegistry()
        registry.register(spec, expected_revision=0, binding=binding)
        call = {
            "tool_ref": registry.reference(registry.snapshot()[1][0]),
            "arguments": {"text": "original", "count": 1},
            "action_id": effect,
        }
        result = await ToolFacade(registry, access).invoke(call, ctx)
        assert result["failure"]["code"] == "feature_disabled"


def test_cas_is_atomic_across_concurrent_registrations(spec):
    from concurrent.futures import ThreadPoolExecutor

    registry = ToolRegistry()

    def attempt(version):
        try:
            registry.register({**spec, "version": version}, expected_revision=0)
            return "registered"
        except DomainError as exc:
            return exc.failure.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, ("v1", "v2")))
    assert sorted(outcomes) == ["registered", "revision_conflict"]
    assert registry.revision == 1
