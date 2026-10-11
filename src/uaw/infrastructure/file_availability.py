"""Installed native availability for explicit administrator configuration checks.

This check opens no user file, starts no process and grants no Run permission.
The original lifecycle remains the only source of owner/workspace/native proof.
"""

from typing import TYPE_CHECKING

from uaw.infrastructure.installed_receipt import current_root
from uaw.shared.contracts import JsonObject, Ref
from uaw.shared.errors import CapabilityUnavailable, reject

if TYPE_CHECKING:
    from uaw.infrastructure.installed_lifecycle import InstalledLifecycle


class InstalledFileAvailability:
    def __init__(self, lifecycle: InstalledLifecycle) -> None:
        self.lifecycle = lifecycle

    async def require(self, scope: JsonObject) -> None:
        entry = self.lifecycle.active
        if entry is None or entry.launch is None or entry.launch.root_workspace is None:
            raise CapabilityUnavailable("file.current_installed_availability")
        owner, workspace = entry.owner, entry.launch.root_workspace
        # {} is only the internal connection-acceptance probe. Flag activation
        # has its own exact conversation/workspace requirement in Configuration.
        if scope and (
            set(scope) != {"conversation_id", "resource_refs"}
            or scope["resource_refs"] != [workspace.wire()]
        ):
            raise reject(
                "file_availability_scope_denied", "Original native workspace required", 403
            )
        if scope:
            conversation = await self.lifecycle.records.get(
                owner, "conversations", str(scope["conversation_id"])
            )
            if conversation.payload["id"] != scope["conversation_id"]:
                raise reject("file_availability_owner_denied", "Owned conversation required", 403)
        launch = await self.lifecycle.owned_ready(owner, workspace)
        if launch is not entry.launch or launch.connection is None:
            raise CapabilityUnavailable("file.original_installed_availability")
        grant = await current_root(launch)
        device = await launch.connection.devices.current(
            grant.device_id, authenticated_principal=owner
        )
        if device["source"]["owner"] != owner.wire():
            raise reject("file_availability_owner_denied", "Current device owner differs", 403)
        if await current_root(launch) != grant:
            raise reject("file_availability_changed", "Original native root changed", 412)
        if (
            await launch.connection.devices.current(grant.device_id, authenticated_principal=owner)
            != device
        ):
            raise reject("file_availability_changed", "Current device changed", 412)
        if (
            self.lifecycle.active is not entry
            or entry.launch is not launch
            or entry.stopping
            or entry.done.is_set()
            or launch.root_workspace != Ref.model_validate(workspace.wire())
        ):
            raise CapabilityUnavailable("file.original_installed_availability")
