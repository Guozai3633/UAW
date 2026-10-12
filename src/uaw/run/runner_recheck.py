"""Internal original-command recheck/watch source. No execution or cached allowance."""

import asyncio
import json
import math
from datetime import datetime
from typing import Protocol

from uaw.run.runner_authority import authority_snapshot
from uaw.run.runner_commands import RunnerCommands, pin
from uaw.run.runner_devices import instant
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import reject
from uaw.workspace.contracts import (
    RegisteredReceiptCommand,
    RunnerAuthoritySnapshot,
    RunnerChannelSnapshot,
    RunnerCommand,
    RunnerRootSnapshot,
)
from uaw.workspace.ports import RegisteredReadCurrent


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
    metadata inputs require a final fresh full-row SQL witness. Watch checks one
    full source, then fresh SQL input changes; it is not native/key/pipe monitoring
    or an execution permission. No synthetic event or cached grant is used.
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
        return (
            await self.current(
                command_ref,
                authenticated_principal=authenticated_principal,
                channel_ref=channel_ref,
                deadline=asyncio.get_running_loop().time() + 10,
            )
        ).authority

    @staticmethod
    def _deadline(deadline: float) -> None:
        now = asyncio.get_running_loop().time()
        if (
            type(deadline) not in (float, int)
            or not math.isfinite(deadline)
            or not now < deadline <= now + 10
        ):
            raise reject(
                "runner_watch_deadline_denied", "Original finite response deadline required", 403
            )

    async def current(
        self,
        command_ref: Ref,
        *,
        authenticated_principal: Principal,
        channel_ref: Ref,
        deadline: float,
    ) -> RegisteredReadCurrent:
        self._deadline(deadline)
        ref, channel = self._fixed(command_ref), self._fixed(channel_ref, channel=True)
        actor = Principal.model_validate_json(
            json.dumps(authenticated_principal.wire(), allow_nan=False)
        )
        try:
            async with (
                asyncio.timeout_at(deadline),
                self.commands.store.current_reads(),
                self.commands.store.current_witness(),
            ):
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
                signed = RunnerCommand.model_validate_json(
                    json.dumps(record["command"], allow_nan=False)
                )
                owner = signed.trusted_context.principal
                connection = RunnerChannelSnapshot.model_validate_json(
                    json.dumps(actual["device"]["source"], allow_nan=False)
                )
                root = RunnerRootSnapshot.model_validate_json(
                    json.dumps(actual["root"], allow_nan=False)
                )
                authority = RunnerAuthoritySnapshot.model_validate_json(
                    json.dumps(authority_snapshot(record, actual), allow_nan=False)
                )
                if (
                    connection.actor != actor
                    or connection.owner != owner
                    or root.owner != owner
                    or root.device_id != connection.device_id
                    or root.workspace_ref != authority.workspace_ref
                    or root.root_handle != authority.root_handle
                    or root.binding_revision != authority.binding_revision
                    or root.allowed_actions != authority.allowed_actions
                    or authority.device_id != connection.device_id
                    or authority.context != signed.trusted_context
                    or record["device_ref"]["id"] != connection.device_id
                    or actual["root"] != record["root"]
                    or signed.parameters["action"] != "file.read"
                ):
                    raise reject(
                        "runner_read_current_binding_denied", "Original read sources differ", 412
                    )
                if await self.commands.record(ref.id) != record:
                    raise reject(
                        "runner_command_changed", "Original command changed while checking", 412
                    )
                if self.commands.devices.now() >= instant(record["command"]["expires_at"]):
                    raise reject("runner_deadline_denied", "Original command deadline passed", 409)
                result = RegisteredReadCurrent(
                    ref,
                    RegisteredReceiptCommand(signed, connection.device_id, owner),
                    authority,
                    connection,
                    root,
                )
            # SQL inputs have a final single-statement comparison point. Closing
            # the owning connection may await: this is not an atomic grant
            # spanning SQL, OS or native stores. Check deadlines after cleanup;
            # D keeps native/key/handle guards and rereads after critical work.
            if (
                asyncio.get_running_loop().time() >= deadline
                or self.commands.devices.now() >= instant(result.source.command.expires_at)
            ):
                raise reject("runner_deadline_denied", "Original read deadline passed", 409)
            return result
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
        self._deadline(deadline)
        ref, channel = self._fixed(command_ref), self._fixed(channel_ref, channel=True)
        actor = Principal.model_validate_json(
            json.dumps(authenticated_principal.wire(), allow_nan=False)
        )
        expiry: datetime | None = None
        budget: asyncio.Timeout | None = None

        async def initial() -> None:
            nonlocal expiry
            state = await self.current(
                ref,
                authenticated_principal=actor,
                channel_ref=channel,
                deadline=deadline,
            )
            expiry = instant(state.source.command.expires_at)
            assert budget is not None
            budget.reschedule(
                min(
                    deadline,
                    asyncio.get_running_loop().time()
                    + max(0, (expiry - self.commands.devices.now()).total_seconds()),
                )
            )

        def check() -> None:
            if expiry is None or self.commands.devices.now() >= expiry:
                raise reject("runner_deadline_denied", "Original command deadline passed", 409)

        try:
            async with asyncio.timeout_at(deadline) as budget:
                await self.commands.store.wait_for_read_change(
                    initial, deadline=deadline, check=check
                )
                # A change is never permission to continue. Resolve any actual
                # owning denial for diagnostics; valid changes also end watch.
                await self.current(
                    ref,
                    authenticated_principal=actor,
                    channel_ref=channel,
                    deadline=deadline,
                )
        except TimeoutError:
            raise reject("runner_watch_timeout", "Original watch deadline passed", 410) from None
