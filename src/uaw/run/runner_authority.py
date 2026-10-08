"""Fresh asynchronous authority built from independent registered Runner sources."""

from uaw.run.runner_commands import Payload, RunnerCommands, copy
from uaw.run.runner_devices import instant
from uaw.shared.contracts import Principal
from uaw.shared.errors import reject
from uaw.shared.ports import AsyncRunnerAuthorityPort
from uaw.shared.schema import validate_contract


class RegisteredRunnerAuthority(AsyncRunnerAuthorityPort):
    def __init__(self, commands: RunnerCommands) -> None:
        self.commands = commands

    async def current(self, command: Payload, *, authenticated_principal: Principal) -> Payload:
        validate_contract("RunnerCommand", command)
        validate_contract("Principal", authenticated_principal.wire())
        claim = copy(command)
        record = await self.commands.record(claim["command_id"])
        if record["state"] != "active" or record["command"] != claim:
            raise reject(
                "runner_command_inactive", "Command is revoked or differs from registration", 409
            )
        actual = await self.commands.collect(record, authenticated_principal)
        again = await self.commands.record(claim["command_id"])
        if again != record:
            raise reject("runner_command_changed", "Command changed during current checks", 412)
        if self.commands.devices.now() >= instant(claim["expires_at"]):
            raise reject("runner_deadline_denied", "Command expired during final lookup", 409)
        root = actual["root"]
        if root != record["root"]:
            raise reject("runner_root_changed", "Registered root binding changed", 412)
        saved = actual["request"]
        result = {
            "context": saved["context"],
            "device_id": actual["device"]["device_id"],
            "root_handle": root["root_handle"],
            "workspace_ref": root["workspace_ref"],
            "binding_revision": root["binding_revision"],
            "fencing_token": actual["lease"]["fencing_token"],
            "lease_expires_at": actual["lease"]["expires_at"],
            "request_ref": record["command"]["request_ref"],
            "request_parameters": saved["parameters"],
            "policy_ref": saved["context"]["capability_policy_ref"],
            "required_scope_capability": saved["parameters"]["action"],
            "allowed_actions": root["allowed_actions"],
            "feature_enabled": True,
            "connected": actual["device"]["source"]["connected"],
            "cancelled": actual["budget"]["ledger"]["cancel_requested"],
        }
        validate_contract("RunnerAuthoritySnapshot", result)
        return result
