"""Actual SQL admission rollback/fixed sources; native inputs are controlled metadata."""

import copy
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from tests.integration.agent.test_file_provider_configuration import (
    ControlledAvailability,
    configuration,
    registered,
)
from tests.integration.test_control_plane import conversation, meta
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_stage_wiring import container
from uaw.infrastructure.db.transactions import reference
from uaw.run.file_admission import NAMESPACE, InstalledFileRunSources
from uaw.shared.contracts import Ref, Scope, TrustedExecutionContext
from uaw.shared.errors import DomainError
from uaw.shared.file_provider import FileProviderConnectionAcceptance


@pytest.fixture
async def file_run_case(domain, principal, tmp_path, monkeypatch):
    config, run, admin = domain
    conv = await conversation(domain, principal)
    active = await config.current()
    provider = await registered(config, admin)
    config.file_availability = ControlledAvailability()
    connected = await FileProviderConnectionAcceptance(config).accept(
        admin, Ref.model_validate(reference("provider", provider["id"])), meta("native-accept", 1)
    )
    workspace = Ref(kind="workspace", id="actual-run-controlled-workspace", version="1")
    scope = {"conversation_id": conv["id"], "resource_refs": [workspace.wire()]}
    staged = await config.stage(
        admin,
        {
            "configuration": configuration(
                active,
                reference("provider", connected["id"], connected["revision"]),
                scope,
                enabled=True,
            )
        },
        meta("admission-file-stage"),
    )
    await config.validate(admin, staged["id"], meta("admission-file-validate", 1))
    await config.activate(admin, staged["id"], meta("admission-file-activate", 2))
    c = container(run.store, config, tmp_path)
    sources = InstalledFileRunSources(c)
    run.file_admission = c.file_run_sources = sources
    native = {
        "launch_id": "controlled-original-launch",
        "workspace_ref": workspace.wire(),
        "device_ref": {
            "kind": "device",
            "id": "controlled-native-device",
            "version": "1",
            "content_hash": "d" * 64,
        },
        "root_identity_hash": "e" * 64,
        "expires_at": (datetime.now(UTC) + timedelta(seconds=120)).isoformat(),
    }
    calls = []

    async def original(owner, pin):
        assert owner == principal and pin == workspace
        calls.append((owner, pin))
        return copy.deepcopy(native)

    monkeypatch.setattr(sources, "_native", original)
    return SimpleNamespace(
        c=c,
        config=config,
        run=run,
        admin=admin,
        conversation=conv,
        workspace=workspace,
        native=native,
        sources=sources,
        calls=calls,
    )


async def submit(p, actor, name):
    return await p.run.submit(
        actor,
        {"conversation_id": p.conversation["id"], "text": "original task", "attachment_refs": []},
        meta(name),
    )


async def context(p, actor, run):
    binding = (await p.run.store.get(actor, "run.bindings", run["id"])).payload
    return TrustedExecutionContext(
        principal=actor,
        scope=Scope(
            principal_id=actor.id,
            conversation_id=run["conversation_id"],
            task_id=run["task_id"],
            resource_refs=(p.workspace,),
            capabilities=("file.read", "workspace.process"),
        ),
        run_id=run["id"],
        conversation_id=run["conversation_id"],
        task_id=run["task_id"],
        model_policy_ref=Ref.model_validate(binding["model_policy_ref"]),
        capability_policy_ref=Ref(kind="policy", id="controlled-admission-policy", version="1"),
        operation_id="file-admission-operation",
        attempt_id="file-admission-attempt",
        trace_id="file-admission-trace",
        deadline=run["budget"]["deadline"],
    )


async def test_file_admission_pin_is_immutable_and_original_request_replay_reads_no_native(
    file_run_case, principal
):
    p = file_run_case
    run = await submit(p, principal, "source-original-submit")
    pin = await p.run.store.get(principal, NAMESPACE, run["id"])
    assert pin.schema_name == "FileRunSourceBinding" and pin.revision == 1
    assert (
        pin.payload["fixed_model_id"] == "fixture-model"
        and pin.payload["owner"] == principal.wire()
    )
    assert "native_path" not in pin.payload and "text" not in pin.payload
    before = len(p.calls)
    assert await submit(p, principal, "source-original-submit") == run
    assert len(p.calls) == before
    ctx = await context(p, principal, run)
    assert await p.sources.current(ctx, p.workspace) == pin.payload
    p.native["launch_id"] = "replacement-launch"
    with pytest.raises(DomainError) as replacement:
        await p.sources.current(ctx, p.workspace)
    assert replacement.value.failure.code == "file_run_source_changed"


async def test_missing_file_admission_never_leaves_successful_run(file_run_case, principal):
    p = file_run_case
    p.run.file_admission = None
    before = await p.run.store.get(principal, "conversations", p.conversation["id"])
    with pytest.raises(DomainError) as missing:
        await submit(p, principal, "source-missing-submit")
    assert missing.value.failure.code == "capability_unavailable"
    assert await p.run.store.get(principal, "conversations", p.conversation["id"]) == before
    # A retry of the same request after restoring the actual source is admitted;
    # the failed transaction has not left a deduplication success receipt.
    p.run.file_admission = p.sources
    run = await submit(p, principal, "source-missing-submit")
    assert (await p.run.store.get(principal, NAMESPACE, run["id"])).revision == 1


@pytest.mark.parametrize(
    "change", ["session", "workspace", "model", "root", "device", "closed_flag"]
)
async def test_file_current_source_rejects_changed_scope_or_authority(
    file_run_case, principal, change
):
    p = file_run_case
    run = await submit(p, principal, "source-change-submit")
    ctx = await context(p, principal, run)
    workspace = p.workspace
    if change == "session":
        ctx = ctx.model_copy(
            update={"principal": principal.model_copy(update={"auth_session_id": "other-session"})}
        )
    elif change == "workspace":
        workspace = workspace.model_copy(update={"version": "2"})
    elif change == "model":
        ctx = ctx.model_copy(
            update={"model_policy_ref": ctx.model_policy_ref.model_copy(update={"version": "2"})}
        )
    elif change == "root":
        p.native["root_identity_hash"] = "f" * 64
    elif change == "device":
        p.native["device_ref"]["version"] = "2"
    else:
        active = await p.config.current()
        value = {
            k: copy.deepcopy(active[k])
            for k in (
                "provider_refs",
                "model_refs",
                "environment_template_refs",
                "feature_flags",
                "approval_policy_ref",
                "storage_policy_ref",
            )
        }
        for flag in value["feature_flags"]:
            flag["enabled"] = False
        staged = await p.config.stage(
            p.admin, {"configuration": value}, meta("source-disabled-stage")
        )
        await p.config.validate(p.admin, staged["id"], meta("source-disabled-validate", 1))
        await p.config.activate(p.admin, staged["id"], meta("source-disabled-activate", 2))
    with pytest.raises(DomainError):
        await p.sources.current(ctx, workspace)
