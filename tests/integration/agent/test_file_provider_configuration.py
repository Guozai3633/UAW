"""Real SQL configuration transactions; availability inputs here are controlled only."""

import copy

import pytest

from tests.integration.test_control_plane import conversation, meta
from tests.integration.test_control_plane import domain as domain
from uaw.infrastructure.db.transactions import reference
from uaw.shared.configuration import FILE_PROFILE, FILE_SETTINGS
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError, reject
from uaw.shared.file_provider import FileProviderConnectionAcceptance


class ControlledAvailability:
    def __init__(self):
        self.calls = []
        self.available = True

    async def require(self, scope):
        self.calls.append(copy.deepcopy(scope))
        if not self.available:
            raise reject("controlled_source_missing", "Test native source absent", 503)


async def registered(config, admin):
    return await config.register(
        admin,
        "provider",
        {
            "provider": {
                "id": "installed-file-v1",
                "kind": "local",
                "profile_ref": copy.deepcopy(FILE_PROFILE),
                "settings": copy.deepcopy(FILE_SETTINGS),
            }
        },
        meta("file-register", 0),
    )


def configuration(active, pin, scope, *, enabled):
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
    value["provider_refs"].append(pin)
    value["feature_flags"] = [
        {**f, "enabled": enabled, "scope": scope} if f["id"] == "local_files" else f
        for f in value["feature_flags"]
    ]
    return value


async def test_file_provider_registration_is_closed_disconnected_and_admin_only(domain, principal):
    config, _, admin = domain
    provider = await registered(config, admin)
    assert provider["state"] == "disconnected"
    with pytest.raises(DomainError):
        await registered(config, principal)
    with pytest.raises(DomainError) as missing:
        await FileProviderConnectionAcceptance(config).accept(
            admin,
            Ref.model_validate(reference("provider", provider["id"])),
            meta("accept-missing", 1),
        )
    assert missing.value.failure.code == "capability_unavailable"
    for alteration in ({"actions": ["file.read", "exec"]}, {"max_characters": 32768}):
        with pytest.raises(DomainError) as closed:
            await config.register(
                admin,
                "provider",
                {
                    "provider": {
                        "id": "other-file",
                        "kind": "local",
                        "profile_ref": FILE_PROFILE,
                        "settings": {**FILE_SETTINGS, **alteration},
                    }
                },
                meta("invalid-file", 0),
            )
        assert closed.value.failure.code == "file_provider_invalid"


async def test_activation_rechecks_availability_and_preserves_old_run_pin(domain, principal):
    config, run, admin = domain
    conv = await conversation(domain, principal)
    old = await run.submit(
        principal,
        {"conversation_id": conv["id"], "text": "old", "attachment_refs": []},
        meta("old-run"),
    )
    binding = (await run.store.get(principal, "run.bindings", old["id"])).payload
    active = await config.current()
    provider = await registered(config, admin)
    gate = ControlledAvailability()
    config.file_availability = gate
    connected = await FileProviderConnectionAcceptance(config).accept(
        admin, Ref.model_validate(reference("provider", provider["id"])), meta("file-accept", 1)
    )
    assert connected["state"] == "active" and connected["revision"] == 2
    assert gate.calls == [{}]
    assert await config.current() == active  # Acceptance never activates a flag/configuration.
    pin = reference("provider", connected["id"], 2)
    workspace = Ref(kind="workspace", id="controlled-native-workspace", version="1")
    scope = {"conversation_id": conv["id"], "resource_refs": [workspace.wire()]}
    staged = await config.stage(
        admin,
        {"configuration": configuration(active, pin, scope, enabled=True)},
        meta("file-stage"),
    )
    await config.validate(admin, staged["id"], meta("file-validate", 1))
    gate.available = False
    with pytest.raises(DomainError) as changed:
        await config.activate(admin, staged["id"], meta("file-activate-failed", 2))
    assert changed.value.failure.code == "controlled_source_missing"
    assert await config.current() == active
    gate.available = True
    now = await config.activate(admin, staged["id"], meta("file-activate", 2))
    assert (await run.store.get(principal, "run.bindings", old["id"])).payload == binding
    with pytest.raises(DomainError) as old_denied:
        await config.require_capability(
            "file_access", binding["configuration_ref"], scope, implemented=True, boundary="call"
        )
    assert old_denied.value.failure.code == "feature_disabled"
    await config.require_capability(
        "file_access",
        reference("configuration", now["id"], now["revision"]),
        scope,
        implemented=True,
        boundary="call",
    )
    with pytest.raises(DomainError):
        await config.require_capability(
            "file_access",
            reference("configuration", now["id"], now["revision"]),
            {**scope, "resource_refs": [workspace.model_copy(update={"version": "2"}).wire()]},
            implemented=True,
            boundary="call",
        )


@pytest.mark.parametrize(
    "scope,enabled",
    [
        ({"resource_refs": []}, True),
        ({"conversation_id": "other"}, True),
        ({"resource_refs": []}, False),
    ],
)
async def test_flag_requires_trusted_source_and_exact_workspace(domain, principal, scope, enabled):
    config, _, admin = domain
    await conversation(domain, principal)
    active = await config.current()
    provider = await registered(config, admin)
    staged = await config.stage(
        admin,
        {
            "configuration": configuration(
                active, reference("provider", provider["id"]), scope, enabled=enabled
            )
        },
        meta("invalid-stage"),
    )
    if enabled:
        with pytest.raises(DomainError):
            await config.validate(admin, staged["id"], meta("invalid-validate", 1))
    else:
        await config.validate(admin, staged["id"], meta("disabled-validate", 1))
    assert await config.current() == active
