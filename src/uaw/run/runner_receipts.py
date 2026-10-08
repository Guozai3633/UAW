"""Journal Reader for registered SQL commands. It grants no new execution access."""

import asyncio
import json

from uaw.run.runner_commands import RunnerCommands
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, reject
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
            device_id = record["device_ref"]["id"]
            owner = await self.commands.devices.owner(authenticated_principal, device_id)
            current = await self.commands.read(
                command_ref, authenticated_principal=authenticated_principal
            )
            again = await self.commands.devices.owner(authenticated_principal, device_id)
        if current["command"] != record["command"] or again != owner:
            raise reject("runner_receipt_source_changed", "Registered recovery source changed", 412)
        command = RunnerCommand.model_validate_json(json.dumps(current["command"]))
        if command.trusted_context.principal != owner:
            raise reject("runner_owner_denied", "Actual device owner differs from command", 403)
        return RegisteredReceiptCommand(command, device_id, owner)
