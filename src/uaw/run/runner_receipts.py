"""Journal Reader for registered SQL commands. It grants no new execution access."""

import asyncio
import json

from uaw.run.runner_commands import RunnerCommands
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable
from uaw.workspace.contracts import RegisteredReceiptCommand, RunnerCommand
from uaw.workspace.ports import ReceiptCommandReaderPort


class RegisteredReceiptCommandReader(ReceiptCommandReaderPort):
    def __init__(self, commands: RunnerCommands | None) -> None:
        self.commands = commands

    async def resolve(
        self, command_ref: Ref, *, authenticated_principal: Principal
    ) -> RegisteredReceiptCommand:
        if self.commands is None:
            raise CapabilityUnavailable("runner.registered_command_source")
        # Recovery uses an independent bounded call, never the old command deadline.
        async with asyncio.timeout(30):
            record = await self.commands.read(
                command_ref, authenticated_principal=authenticated_principal
            )
            # The owning read already brackets original command/request/signature
            # with fresh device/channel/owner checks. Re-entering it and then
            # resolving owner twice expands the same graph without intervening IO.
            command = RunnerCommand.model_validate_json(json.dumps(record["command"]))
        return RegisteredReceiptCommand(
            command, record["device_ref"]["id"], command.trusted_context.principal
        )
