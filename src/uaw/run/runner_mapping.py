"""Keyword-compatible native owner mapping backed by current registered devices."""

from uaw.run.runner_devices import RunnerDevices
from uaw.shared.contracts import Principal
from uaw.shared.errors import CapabilityUnavailable


class RegisteredRunnerPrincipalMapping:
    def __init__(self, devices: RunnerDevices | None) -> None:
        self.devices = devices

    async def owner(self, *, authenticated_principal: Principal, device_id: str) -> Principal:
        if self.devices is None:
            raise CapabilityUnavailable("runner.registered_principal_mapping")
        # RunnerDevices checks complete actor/session, actual channel, revocation
        # and expiry. No identity is read from a command or root claim.
        return await self.devices.owner(authenticated_principal, device_id)
