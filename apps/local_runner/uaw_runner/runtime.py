"""Owned read-only helper composition. No HTTP enrollment, flags or file actions.

Lifecycle methods are internal trusted local calls. IPC remains command/recover only.
"""

import asyncio
import math
import secrets
from dataclasses import dataclass

from uaw.shared.contracts import Ref
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.workspace.ports import ReceiptCommandReaderPort, RunnerReadCurrentPort
from uaw_runner.bootstrap import BootstrapConsumer, BootstrapNativeChallenges
from uaw_runner.ipc.channel_source import ConnectionRegistry
from uaw_runner.ipc.read_endpoint import ReadOnlyPipeEndpoint
from uaw_runner.ipc.sessions import AuthenticatedPipeSession, IpcSigner, IpcSigningBinding
from uaw_runner.ipc.windows_pipe import OsIdentity, WindowsApi, WindowsPipeListener
from uaw_runner.keys import Ed25519SignatureAdapter
from uaw_runner.native_authorization import NativeReadAuthorization
from uaw_runner.native_confirmation import WindowsNativeConfirmation
from uaw_runner.pairing import PairingVerifier
from uaw_runner.protocol import RunnerProtocol
from uaw_runner.read_executor import ReadOnlyRunner
from uaw_runner.read_state import ReadExecutionJournal
from uaw_runner.read_watch import LocalReadInvalidation
from uaw_runner.receipts import ReceiptJournal
from uaw_runner.root_source import NativeRootSource


@dataclass(frozen=True)
class HelperAddress:
    name: str
    identity: OsIdentity


class HelperReadAssembly:
    def __init__(self, helper: ReadOnlyHelper) -> None:
        self.helper = helper

    async def create(self, command_ref: Ref, *, channel_ref: Ref) -> ReadOnlyRunner:
        helper = self.helper
        # Composition copies fixed connection metadata only. It grants no permission:
        # endpoint checks after this await, and execute independently reads current
        # Reader/owner/channel/root/authority before admission or opening a handle.
        if helper.session is None:
            raise CapabilityUnavailable("runner.ipc.handshake")
        helper.registry._snapshot(helper.session, channel_ref, device_id=helper.protocol.device_id)
        return ReadOnlyRunner(
            protocol=helper.protocol,
            command_ref=command_ref,
            journal=helper.journal,
            executions=helper.executions,
            currency=helper.currency,
            roots=helper.roots,
            channel=helper.registry,
            channel_ref=channel_ref,
            signer=helper.bootstrap.signer,
            device_key=helper.bootstrap.device_key,
            current_source=helper.current_source,
        )


class ReadOnlyHelper:
    def __init__(
        self,
        *,
        bootstrap: BootstrapConsumer,
        protocol: RunnerProtocol,
        commands: ReceiptCommandReaderPort | None,
        journal: ReceiptJournal,
        executions: ReadExecutionJournal | None,
        roots: NativeRootSource,
        registry: ConnectionRegistry,
        currency: str,
        session_lifetime_seconds: float = 60,
        native_timeout_seconds: float = 60,
        current_source: RunnerReadCurrentPort | None = None,
    ) -> None:
        if (
            any(
                type(value) not in (int, float) or not 0 < value <= 120 or not math.isfinite(value)
                for value in (session_lifetime_seconds, native_timeout_seconds)
            )
            or native_timeout_seconds > session_lifetime_seconds
        ):
            raise ValueError(
                "Finite native/session seconds must satisfy 0 < native <= session <= 120"
            )
        if (
            journal.protocol is not protocol
            or journal.reader is not commands
            or roots.bindings is not protocol.bindings
            or roots.directory is not bootstrap.directory
            or protocol.principal_mapping is not bootstrap.mapping
            or roots.mapping is not bootstrap.mapping
            or protocol.device_id != bootstrap.device_key.device_id
            or not isinstance(protocol.signatures, Ed25519SignatureAdapter)
            or protocol.signatures.directory is not bootstrap.directory
        ):
            raise ValueError("Helper keys/owner/root/protocol/journal sources must be identical")
        self.bootstrap, self.protocol, self.commands, self.journal = (
            bootstrap,
            protocol,
            commands,
            journal,
        )
        self.executions, self.roots, self.registry, self.currency = (
            executions,
            roots,
            registry,
            currency,
        )
        self.current_source = current_source
        self.session_lifetime_seconds = session_lifetime_seconds
        self.native_timeout_seconds = native_timeout_seconds
        self.listener: WindowsPipeListener | None = None
        self.session: AuthenticatedPipeSession | None = None
        self.endpoint: ReadOnlyPipeEndpoint | None = None
        self.closed = False
        self.operation: asyncio.Task[object] | None = None
        self.lock = asyncio.Lock()

    def available(self) -> None:
        self.bootstrap.available()
        for name, value in (
            ("commands", self.commands),
            ("executions", self.executions),
            ("authority", self.protocol.async_authority),
            ("native_roots", self.roots.native_roots),
            ("selections", self.roots.selections),
            ("grants", self.roots.grants),
        ):
            if value is None:
                raise CapabilityUnavailable("runner.helper." + name)
        if self.closed:
            raise CapabilityUnavailable("runner.helper.closed")

    async def start(self) -> HelperAddress:
        async with self.lock:
            self.available()
            if self.listener is not None:
                raise reject("ipc_busy", "Helper already listening", 409)
            identity = await asyncio.to_thread(WindowsApi().current)
            await self.bootstrap.local(identity)
            # Only create an OS listener after independent account/key/private proof.
            opening = asyncio.create_task(
                asyncio.to_thread(
                    WindowsPipeListener,
                    name="uaw-helper-" + secrets.token_hex(16),
                    logon_sid=identity.logon_sid,
                )
            )
            try:
                listener = await asyncio.shield(opening)
            except asyncio.CancelledError:
                # Drain OS handle creation; cancellation must not leak a late listener.
                listener = await opening
                await listener.close()
                raise
            self.listener = listener
            try:
                await self.bootstrap.local(identity)
                self.available()
                return HelperAddress(listener.name, identity)
            except BaseException:
                self.listener = None
                await listener.close()
                raise

    async def accept(self) -> Ref:
        self.available()
        if self.listener is None or self.operation is not None or self.session is not None:
            raise reject("ipc_busy", "Helper accept state invalid", 409)
        self.operation = asyncio.current_task()
        session = None
        try:
            pipe = await self.listener.accept()
            bootstrap = self.bootstrap
            binding = bootstrap.device_key
            session = AuthenticatedPipeSession(
                pipe=pipe,
                registration=bootstrap.registration,
                lifetime_seconds=self.session_lifetime_seconds,
                directory=bootstrap.directory,
                signer=IpcSigner(
                    binding=IpcSigningBinding(
                        binding.device_id, binding.key_id, "device", binding.credential_handle
                    ),
                    directory=bootstrap.directory,
                    credentials=bootstrap.signer.credentials,
                ),
            )
            await session.handshake()
            await bootstrap.connected(session)
            channel_ref = await self.registry.add(session)
            self.session = session
            self.endpoint = ReadOnlyPipeEndpoint(
                session=session,
                registry=self.registry,
                commands=self.commands,
                runners=HelperReadAssembly(self),
                current_source=self.current_source,
                local_monitor=LocalReadInvalidation(self.roots) if self.current_source else None,
            )
            return channel_ref
        except BaseException:
            if session is not None:
                await session.close()
            if self.listener is not None:
                await self.listener.close()
                self.listener = None
            raise
        finally:
            self.operation = None

    async def authorization(self) -> NativeReadAuthorization:
        self.available()
        if self.session is None or self.session.channel_ref is None:
            raise CapabilityUnavailable("runner.helper.connected_native")
        roots = self.roots
        assert roots.selections is not None and roots.native_roots is not None
        challenges = BootstrapNativeChallenges(
            bootstrap=self.bootstrap,
            state=roots.selections,
            registry=self.registry,
            channel_ref=self.session.channel_ref,
            device_id=self.protocol.device_id,
            mapping=self.bootstrap.mapping,
            clock=self.protocol.clock,
        )
        native = WindowsNativeConfirmation(
            source=challenges,
            directory=self.bootstrap.directory,
            clock=self.protocol.clock,
            local_roots=roots.native_roots,
            timeout_seconds=self.native_timeout_seconds,
        )
        verifier = PairingVerifier(
            roots.selections, native=native, roots=roots.native_roots, clock=self.protocol.clock
        )
        return await asyncio.to_thread(
            NativeReadAuthorization,
            native=native,
            challenges=challenges,
            verifier=verifier,
            signer=self.bootstrap.signer,
            device_key=self.bootstrap.device_key,
            roots=roots,
        )

    async def serve_once(self) -> Ref:
        self.available()
        if self.endpoint is None or self.session is None:
            raise CapabilityUnavailable("runner.helper.connected_read")
        if self.operation is not None:
            raise reject("ipc_busy", "Helper operation already active", 409)
        self.operation = asyncio.current_task()
        try:
            # Do not consume the frame/response budget while a user is deciding
            # an original approval. This wait grants nothing, performs no read,
            # and never renews the authenticated session or native root deadline.
            first_byte = await self.session.pipe.wait_readable(
                deadline=self.session.monotonic_expiry
            )
            until = min(first_byte + self.session.pipe.timeout, self.session.monotonic_expiry)
            async with asyncio.timeout_at(until):
                await self.bootstrap.connected(self.session)
                return await self.endpoint.serve_once(deadline=until)
        except TimeoutError:
            raise reject("ipc_timeout", "Read frame deadline expired", 408, "timeout") from None
        finally:
            self.operation = None

    async def disconnect(self) -> None:
        async with self.lock:
            if self.session is not None:
                await self.session.close()
            if self.listener is not None:
                await self.listener.close()
            task = self.operation
            if task is not None and task is not asyncio.current_task():
                task.cancel()
                try:
                    await task
                except BaseException:
                    pass
            self.session, self.listener, self.endpoint = None, None, None
            # Current registry retains no old channel permission after disconnect.
            await self.registry.close()

    async def close(self) -> None:
        self.closed = True
        await self.disconnect()
