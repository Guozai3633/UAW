"""Current independently registered challenge to local human read confirmation."""

import asyncio
import hashlib
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Event
from typing import Protocol

from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.runner_signatures import signing_bytes
from uaw.workspace.binding import aware
from uaw.workspace.ports import CurrentKeyDirectory, NativeConfirmation, RunnerPrincipalMappingPort
from uaw_runner.ipc.channel_source import ConnectionRegistry
from uaw_runner.ipc.windows_pipe import OsIdentity, WindowsApi
from uaw_runner.native_dialog import NativePrompt, WindowsNativeDialog
from uaw_runner.receipts import canonical, fixed_ref
from uaw_runner.state import LocalState, Ticket


@dataclass(frozen=True)
class NativeChallenge:
    ticket: Ticket
    owner: Principal
    actor: Principal
    channel_ref: Ref
    identity: OsIdentity
    expires_at: datetime

    def fingerprint(self) -> str:
        return canonical(
            {
                "ticket": self.ticket.document(),
                "revision": self.ticket.revision,
                "state": self.ticket.state,
                "owner": self.owner.wire(),
                "actor": self.actor.wire(),
                "channel": self.channel_ref.wire(),
                "identity": self.identity.__dict__,
                "expires_at": self.expires_at.isoformat(),
            }
        )


class NativeChallengeSourcePort(Protocol):
    async def current(self, ticket_id: str) -> NativeChallenge:
        """Read independently registered challenge/account/device and current live connection."""
        ...


class RegisteredNativeChallenges:
    def __init__(
        self,
        *,
        state: LocalState,
        registry: ConnectionRegistry,
        channel_ref: Ref,
        device_id: str,
        mapping: RunnerPrincipalMappingPort | None,
        clock: Callable[[], datetime],
    ) -> None:
        self.state, self.registry, self.channel_ref = state, registry, fixed_ref(channel_ref)
        self.device_id, self.mapping, self.clock = device_id, mapping, clock

    async def current(self, ticket_id: str) -> NativeChallenge:
        if self.mapping is None:
            raise CapabilityUnavailable("runner.native_registered_owner")
        ticket = await asyncio.to_thread(self.state.get, ticket_id, now=aware(self.clock()))
        session = await self.registry.session(self.channel_ref, device_id=self.device_id)
        actor = await self.registry.authenticated_principal(
            self.channel_ref, device_id=self.device_id
        )
        owner = await self.mapping.owner(authenticated_principal=actor, device_id=self.device_id)
        channel = await self.registry.read(self.channel_ref, device_id=self.device_id)
        if (
            owner.kind != "user"
            or owner.id != ticket.principal_id
            or ticket.device_id != self.device_id
            or owner.wire() != channel["owner"]
            or actor.wire() != channel["actor"]
        ):
            raise reject(
                "permission_denied", "Native account/device relationship differs", 403, "permission"
            )
        assert session.local is not None
        identity = await asyncio.to_thread(WindowsApi().current)
        if session.local.role != "device" or session.local.identity != identity:
            raise reject(
                "permission_denied", "Native endpoint OS instance differs", 403, "permission"
            )
        await session.check()
        return NativeChallenge(
            ticket,
            owner,
            actor,
            self.channel_ref,
            identity,
            min(ticket.expires_at, datetime.fromisoformat(str(channel["expires_at"]))),
        )


class WindowsNativeConfirmation:
    def __init__(
        self,
        *,
        source: NativeChallengeSourcePort | None,
        directory: CurrentKeyDirectory,
        clock: Callable[[], datetime],
        timeout_seconds: float = 60,
    ) -> None:
        if not 0 < timeout_seconds <= 120:
            raise ValueError("Native confirmation timeout must be in (0,120]")
        self.source, self.directory, self.clock, self.timeout = (
            source,
            directory,
            clock,
            timeout_seconds,
        )
        self.busy = False

    async def checked(
        self, ticket_id: str, principal_id: str, device_id: str, document_hash: str
    ) -> NativeChallenge:
        if self.source is None:
            raise CapabilityUnavailable("runner.native_registered_challenge")
        current = await self.source.current(ticket_id)
        if not isinstance(current, NativeChallenge):
            raise reject("dependency_protocol_invalid", "Native source type invalid", 503)
        ticket = current.ticket
        actual_hash = hashlib.sha256(
            signing_bytes(ticket.document(), ticket.device_id, ticket.key_id, "pairing-proof")
        ).hexdigest()
        key = await asyncio.to_thread(self.directory.lookup, ticket.key_id, device_id=device_id)
        if (
            ticket.ticket_id != ticket_id
            or ticket.principal_id != principal_id
            or ticket.device_id != device_id
            or ticket.state != "pending"
            or current.owner.kind != "user"
            or current.owner.id != principal_id
            or actual_hash != document_hash
            or aware(current.expires_at) <= aware(self.clock())
            or current.expires_at > ticket.expires_at
            or key.revoked
            or key.role != "device"
            or key.key_id != ticket.key_id
            or key.device_id != ticket.device_id
            or key.public_bytes != ticket.public_bytes
        ):
            raise reject(
                "permission_denied", "Native challenge/key/expiry differs", 403, "permission"
            )
        if await asyncio.to_thread(WindowsApi().current) != current.identity:
            raise reject("permission_denied", "Native local OS identity differs", 403, "permission")
        return current

    async def confirm(
        self, *, ticket_id: str, principal_id: str, device_id: str, document_hash: str
    ) -> NativeConfirmation:
        if self.busy:
            raise reject("native_busy", "One native decision at a time", 409)
        self.busy = True
        stopped = Event()
        worker = monitor = None
        try:
            async with asyncio.timeout(self.timeout):
                current = await self.checked(ticket_id, principal_id, device_id, document_hash)
                expiry = min(
                    current.expires_at, aware(self.clock()) + timedelta(seconds=self.timeout)
                )
                deadline = time.monotonic() + (expiry - aware(self.clock())).total_seconds()
                prompt = NativePrompt(
                    current.owner.id,
                    device_id,
                    expiry.isoformat(),
                    document_hash,
                    current.ticket.kind == "root",
                )
                dialog = WindowsNativeDialog()
                worker = asyncio.create_task(
                    asyncio.to_thread(dialog.show, prompt, stopped, deadline)
                )

                async def watch() -> None:
                    while True:
                        await asyncio.sleep(0.1)
                        checked = await self.checked(
                            ticket_id, principal_id, device_id, document_hash
                        )
                        if checked.fingerprint() != current.fingerprint():
                            raise reject(
                                "permission_denied",
                                "Native relationship changed",
                                403,
                                "permission",
                            )

                monitor = asyncio.create_task(watch())
                done, _ = await asyncio.wait((worker, monitor), return_when=asyncio.FIRST_COMPLETED)
                if monitor in done:
                    await monitor
                path = await asyncio.shield(worker)
                final = await self.checked(ticket_id, principal_id, device_id, document_hash)
                if final.fingerprint() != current.fingerprint() or aware(self.clock()) >= expiry:
                    raise reject(
                        "permission_denied",
                        "Native authorization changed/expired",
                        403,
                        "permission",
                    )
                return NativeConfirmation(
                    ticket_id, principal_id, device_id, document_hash, expiry, path
                )
        except TimeoutError:
            raise reject(
                "native_timeout", "Native confirmation deadline exceeded", 410, "timeout"
            ) from None
        finally:
            stopped.set()
            if monitor is not None:
                monitor.cancel()
                try:
                    await monitor
                except BaseException:
                    pass
            if worker is not None:
                while not worker.done():
                    try:
                        await asyncio.shield(worker)
                    except asyncio.CancelledError:
                        continue
                    except Exception:
                        break
                if worker.done() and not worker.cancelled():
                    worker.exception()  # retrieve failure after cancellation
            self.busy = False
