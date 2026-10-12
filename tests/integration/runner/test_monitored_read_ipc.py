"""Actual Windows dual processes/OS keys/once journal with explicitly controlled authority.

Component current/watch ports below are fixtures, not A SQL or human confirmation.
"""

import asyncio
import json

from uaw_runner.read_watch import LocalReadInvalidation

from tests.integration.runner.test_windows_ipc import ipc_case as ipc_case
from tests.integration.runner.test_windows_read_ipc import child_result, endpoint_setup, read_setup
from uaw.workspace.contracts import (
    RunnerAuthoritySnapshot,
    RunnerChannelSnapshot,
    RunnerRootSnapshot,
)
from uaw.workspace.ports import RegisteredReadCurrent


class ControlledCurrent:
    def __init__(self, native, registry):
        self.native, self.registry = native, registry
        self.current_calls, self.watch_calls = 0, 0
        self.deadlines = []

    async def current(self, ref, *, authenticated_principal, channel_ref, deadline):
        self.current_calls += 1
        self.deadlines.append(deadline)
        native = self.native
        source = await native["reader"].resolve(
            ref, authenticated_principal=authenticated_principal
        )
        authority = await native["authority"].current(
            source.command, authenticated_principal=authenticated_principal
        )
        authority["allowed_actions"] = ["file.read", "file.list"]
        root = await native["source"].current(
            "d1", native["workspace"], source.command.trusted_context
        )
        channel = await self.registry.read(channel_ref, device_id="d1")
        return RegisteredReadCurrent(
            ref,
            source,
            RunnerAuthoritySnapshot.model_validate_json(json.dumps(authority)),
            RunnerChannelSnapshot.model_validate_json(json.dumps(channel)),
            RunnerRootSnapshot.model_validate_json(json.dumps(root)),
        )

    async def wait_changed(self, ref, **kwargs):
        self.watch_calls += 1
        await self.current(ref, **kwargs)
        await asyncio.Event().wait()  # explicit stable fixture only, never production watch


def attach(endpoint, native):
    source = ControlledCurrent(native, endpoint.registry)
    create = endpoint.runners.create

    async def make(*args, **kwargs):
        runner = await create(*args, **kwargs)
        runner.current_source = source
        return runner

    endpoint.runners.create = make
    endpoint.current_source = source
    endpoint.local_monitor = LocalReadInvalidation(native["source"])
    return source


async def test_actual_monitored_read_once_and_duplicate_cancelled_original_recovery(ipc_case):
    native = await read_setup(ipc_case)
    first, process, registry = await endpoint_setup(ipc_case, native)
    current = attach(first, native)
    ref = await first.serve_once()
    original = await child_result(process)
    assert original["receipt"]["kind"] == "ok"
    assert current.current_calls and current.watch_calls == 1
    assert len(set(current.deadlines)) == 1
    await registry.close()
    native["target"].unlink()
    native["authority"].value["cancelled"] = True
    second, child, registry = await endpoint_setup(ipc_case, native)
    current = attach(second, native)
    recovered = await second.serve_once()
    body = await child_result(child)
    assert body == original and recovered == ref
    assert current.current_calls == current.watch_calls == 0
    await registry.close()
    ipc_case["report"]["recovery"] = (
        "monitored_actual_signed_journal_duplicate_cancelled_no_new_current_or_file"
    )
