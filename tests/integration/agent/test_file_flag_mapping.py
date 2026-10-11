"""Both published names obey the same fixed/current administrator switch.

Initial enabled state is the existing controlled SQL fixture. Actual production
configuration publication still rejects enabling capabilities before acceptance.
"""

import pytest

from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.test_runner_control import case as case
from uaw.shared.errors import DomainError


async def test_file_tool_name_uses_original_local_file_switch(case):
    config, run, _ = case.domain
    fixed = (await run.store.get(case.ctx.principal, "run.bindings", case.ctx.run_id)).payload
    for capability in ("file_access", "local_files"):
        assert (
            await config.require_capability(
                capability,
                fixed["configuration_ref"],
                case.ctx.scope.wire(),
                implemented=True,
                boundary="call",
            )
            is None
        )
    with pytest.raises(DomainError):
        await config.require_capability(
            "file_access",
            fixed["configuration_ref"],
            case.ctx.scope.wire(),
            implemented=False,
            boundary="call",
        )


async def test_current_admin_disable_denies_both_names_without_changing_fixed_version(case):
    config, run, admin = case.domain
    fixed = (await run.store.get(case.ctx.principal, "run.bindings", case.ctx.run_id)).payload
    current = await config.current()
    value = {k: v for k, v in current.items() if k not in {"id", "revision", "state"}}
    value["feature_flags"] = [{**f, "enabled": False} for f in current["feature_flags"]]
    staged = await config.stage(admin, {"configuration": value}, meta("disable-file-stage"))
    await config.validate(admin, staged["id"], meta("disable-file-validate", 1))
    await config.activate(admin, staged["id"], meta("disable-file-activate", 2))
    for capability in ("file_access", "local_files"):
        with pytest.raises(DomainError) as denied:
            await config.require_capability(
                capability,
                fixed["configuration_ref"],
                case.ctx.scope.wire(),
                implemented=True,
                boundary="call",
            )
        assert denied.value.failure.code == "feature_disabled"
