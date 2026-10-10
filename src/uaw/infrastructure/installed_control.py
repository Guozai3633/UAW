"""Owned control connection to one actually started installed helper.

No directory, command or approval comes from the lifecycle response. Enrollment,
OS instances, role keys and the signed handshake independently supply identity.
"""

import asyncio
from typing import Any

from uaw_runner.helper_process import HelperProcess
from uaw_runner.ipc.channel_source import ConnectionRegistry
from uaw_runner.ipc.sessions import AuthenticatedPipeSession, IpcSigner, IpcSigningBinding
from uaw_runner.ipc.windows_pipe import WindowsApi, connect_pipe
from uaw_runner.state import LocalState

from uaw.composition import Container
from uaw.infrastructure.credentials import WindowsCredentialStore
from uaw.infrastructure.enrollment_peers import EnrolledPeerRegistry
from uaw.run.runner_devices import DEVICES, RunnerDevices
from uaw.shared.contracts import Principal, Ref, RequestMeta
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.stores import StoreMissing


class InstalledControlConnection:
    def __init__(
        self,
        *,
        container: Container,
        owner: Principal,
        enrollment_id: str,
        directory: LocalState,
        credentials: WindowsCredentialStore,
        control_key: IpcSigningBinding,
    ) -> None:
        service, records, config = (
            container.runner_enrollments,
            container.records,
            container.configuration,
        )
        if not service or not records or not config or control_key.role != "control":
            raise CapabilityUnavailable("runner.installed.control_sources")
        self.container, self.owner, self.control_key = container, owner, control_key
        self.peers = EnrolledPeerRegistry(
            service, owner=owner, enrollment_id=enrollment_id, directory=directory
        )
        self.registry = ConnectionRegistry(max_connections=1)
        self.devices = RunnerDevices(records, config.platform, self.registry)
        self.directory, self.credentials = directory, credentials
        self.session: AuthenticatedPipeSession | None = None
        self.channel_ref: Ref | None = None
        self.used = False
        self.closing: asyncio.Task[None] | None = None

    async def connect(self, helper: HelperProcess, ready: dict[str, Any]) -> Ref:
        if self.used or self.closing is not None or helper.closed or not helper.started:
            raise CapabilityUnavailable("runner.installed.connection_consumed")
        self.used = True
        if (
            set(ready) != {"event", "name", "identity"}
            or ready["event"] != "ready"
            or ready["identity"] != helper.identity.__dict__
            or not isinstance(ready["name"], str)
        ):
            raise reject("runner_installed_ready_changed", "Original helper ready required", 412)
        # Freeze before awaited OS/registration IO. This value is only an address.
        name = ready["name"]
        try:
            async with asyncio.timeout(30):
                identity = await asyncio.to_thread(WindowsApi().current)
                peer = await self.peers.current(identity, role="control")
                device = await self.peers.current(helper.identity, role="device")
                if (
                    peer.device_id != self.control_key.device_id
                    or peer.key_id != self.control_key.key_id
                    or device.owner != self.owner
                ):
                    raise reject("runner_installed_control_changed", "Current role differs", 412)
                pipe = await connect_pipe(name=name, logon_sid=identity.logon_sid)
                self.session = AuthenticatedPipeSession(
                    pipe=pipe,
                    registration=self.peers,
                    directory=self.directory,
                    signer=IpcSigner(
                        binding=self.control_key,
                        directory=self.directory,
                        credentials=self.credentials,
                    ),
                )
                await self.session.handshake()
                if self.session.peer is None or self.session.peer.identity != helper.identity:
                    raise reject("runner_installed_peer_changed", "Original device differs", 412)
                ref = await self.registry.add(self.session)
                self.channel_ref = ref
                event = await helper.event()
                if event != {"event": "connected", "channel_ref": ref.wire()}:
                    raise reject("runner_installed_connection_changed", "Channel differs", 412)
                # Bind using the current cryptographically authenticated channel source.
                await self.devices.bind(
                    {
                        "device_id": peer.device_id,
                        "channel_ref": ref.wire(),
                        "expected_revision": 0,
                    },
                    RequestMeta(request_id="installed-bind-" + ref.id, schema_version="0.1"),
                    authenticated_service=self.devices.controller,
                )
                await self.session.check()
                return ref
        except BaseException:
            await self.close()
            raise

    async def close(self) -> None:
        if self.closing is None:
            self.closing = asyncio.create_task(self._close())
        try:
            await asyncio.shield(self.closing)
        except asyncio.CancelledError:
            await self.closing
            raise

    async def _close(self) -> None:
        try:
            # Include a commit completed just before cancellation of bind's final read.
            if self.channel_ref is not None:
                try:
                    row = await self.devices.store.get(
                        self.devices.controller, DEVICES, self.control_key.device_id
                    )
                except StoreMissing:
                    row = None
                if row is not None:
                    source = row.payload["source"]
                    if (
                        row.payload["state"] == "active"
                        and source["channel_ref"] == self.channel_ref.wire()
                        and source["owner"] == self.owner.wire()
                    ):
                        await self.devices.revoke(
                            self.control_key.device_id,
                            row.revision,
                            RequestMeta(
                                request_id="installed-close-" + self.channel_ref.id,
                                schema_version="0.1",
                            ),
                            authenticated_service=self.devices.controller,
                        )
        finally:
            try:
                await self.registry.close()
            finally:
                if self.session is not None:
                    await self.session.close()
