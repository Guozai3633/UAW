"""Internal original-command recheck/watch source. No execution or cached allowance."""

import asyncio
import json
import math
from typing import Protocol

from uaw.run.runner_authority import authority_snapshot
from uaw.run.runner_commands import RunnerCommands, pin
from uaw.run.runner_devices import instant
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import reject
from uaw.workspace.contracts import RunnerAuthoritySnapshot


class RegisteredRunnerRecheckPort(Protocol):
    async def recheck(
        self, command_ref: Ref, *, authenticated_principal: Principal, channel_ref: Ref
    ) -> RunnerAuthoritySnapshot: ...

    async def wait_changed(
        self,
        command_ref: Ref,
        *,
        authenticated_principal: Principal,
        channel_ref: Ref,
        deadline: float,
    ) -> None: ...


class RegisteredRunnerRechecks:
    """Fresh full owning sources, capped by the original command and 10s per call.

    Full source predicates remain, with fresh reads by default. Optional duplicate
    metadata inputs require a final fresh full-row SQL witness. This internal port is
    not yet consumed by the installed endpoint/watch or a product performance gate.
    Watch returns on changed snapshot, raises on revocation/deadline/dependency;
    neither result permits execution. No synthetic event or cached grant is used.
    """

    def __init__(self, commands: RunnerCommands) -> None:
        self.commands = commands

    @staticmethod
    def _fixed(ref: Ref, *, channel: bool = False) -> Ref:
        value = Ref.model_validate_json(json.dumps(ref.wire(), allow_nan=False))
        if (
            value.kind not in ({"content", "connection"} if channel else {"content"})
            or value.version != "1"
            or (value.kind == "content" and not value.content_hash)
            or value.location
            or value.access_scope
        ):
            raise reject("runner_recheck_ref_denied", "Original fixed content Ref required", 403)
        return value

    async def recheck(
        self, command_ref: Ref, *, authenticated_principal: Principal, channel_ref: Ref
    ) -> RunnerAuthoritySnapshot:
        ref, channel = self._fixed(command_ref), self._fixed(channel_ref, channel=True)
        actor = Principal.model_validate_json(
            json.dumps(authenticated_principal.wire(), allow_nan=False)
        )
        try:
            async with asyncio.timeout(10), self.commands.store.current_reads():
                record = await self.commands.record(ref.id)
                if record["state"] != "active" or ref.wire() != pin(
                    "content", ref.id, record["command"]
                ):
                    raise reject(
                        "runner_recheck_command_denied", "Original active command required", 412
                    )
                actual = await self.commands.collect(record, actor)
                if actual["device"]["source"]["channel_ref"] != channel.wire():
                    raise reject(
                        "runner_recheck_channel_denied", "Original current channel required", 403
                    )
                if await self.commands.record(ref.id) != record:
                    raise reject(
                        "runner_command_changed", "Original command changed while checking", 412
                    )
                if self.commands.devices.now() >= instant(record["command"]["expires_at"]):
                    raise reject("runner_deadline_denied", "Original command deadline passed", 409)
                return RunnerAuthoritySnapshot.model_validate_json(
                    json.dumps(authority_snapshot(record, actual), allow_nan=False)
                )
        except TimeoutError:
            raise reject(
                "runner_recheck_timeout", "Original owning recheck deadline passed", 410
            ) from None

    async def wait_changed(
        self,
        command_ref: Ref,
        *,
        authenticated_principal: Principal,
        channel_ref: Ref,
        deadline: float,
    ) -> None:
        now = asyncio.get_running_loop().time()
        if (
            type(deadline) not in (float, int)
            or not math.isfinite(deadline)
            or not now < deadline <= now + 10
        ):
            raise reject(
                "runner_watch_deadline_denied", "Original finite response deadline required", 403
            )
        try:
            async with asyncio.timeout_at(deadline):
                first = await self.recheck(
                    command_ref,
                    authenticated_principal=authenticated_principal,
                    channel_ref=channel_ref,
                )
                while True:
                    await asyncio.sleep(
                        min(0.05, max(0, deadline - asyncio.get_running_loop().time()))
                    )
                    current = await self.recheck(
                        command_ref,
                        authenticated_principal=authenticated_principal,
                        channel_ref=channel_ref,
                    )
                    if current != first:
                        return
        except TimeoutError:
            raise reject("runner_watch_timeout", "Original watch deadline passed", 410) from None
