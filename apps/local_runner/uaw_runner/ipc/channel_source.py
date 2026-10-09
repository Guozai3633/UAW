"""Bounded process-local live connection registry, never a durable permission cache."""

import asyncio

from uaw.shared.contracts import JsonObject, Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.workspace.contracts import RunnerChannelSnapshot
from uaw_runner.ipc.sessions import AuthenticatedPipeSession
from uaw_runner.receipts import canonical, fixed_ref


class ConnectionRegistry:
    def __init__(self, *, max_connections: int = 16) -> None:
        if not 1 <= max_connections <= 32:
            raise ValueError("Connection bound must be 1..32")
        self.max_connections = max_connections
        self.connections: dict[str, AuthenticatedPipeSession] = {}
        self.lock = asyncio.Lock()

    async def add(self, session: AuthenticatedPipeSession) -> Ref:
        await session.check()
        if session.channel_ref is None:
            raise CapabilityUnavailable("runner.ipc.handshake")
        ref = fixed_ref(session.channel_ref)
        async with self.lock:
            # Remove dead entries only; never revive an old Ref or persist permission.
            for key, old in tuple(self.connections.items()):
                if old.pipe.closed.is_set():
                    del self.connections[key]
            if ref.id in self.connections:
                raise reject("revision_conflict", "Connection already registered", 409)
            if len(self.connections) >= self.max_connections:
                raise reject("ipc_busy", "Connection registry bound reached", 409)
            self.connections[ref.id] = session
        return ref

    async def session(self, channel_ref: Ref, *, device_id: str) -> AuthenticatedPipeSession:
        ref = fixed_ref(channel_ref)
        async with self.lock:
            session = self.connections.get(ref.id)
        if (
            session is None
            or session.channel_ref is None
            or session.channel_ref.wire() != ref.wire()
        ):
            raise CapabilityUnavailable("runner.ipc.registered_live_connection")
        await session.check()
        if session.local is None or session.peer is None or session.local.device_id != device_id:
            raise reject(
                "permission_denied", "Current connection device differs", 403, "permission"
            )
        return session

    async def read(self, channel_ref: Ref, *, device_id: str) -> JsonObject:
        session = await self.session(channel_ref, device_id=device_id)
        assert session.local is not None and session.peer is not None
        control = session.local if session.local.role == "control" else session.peer
        device = session.local if session.local.role == "device" else session.peer
        snapshot = RunnerChannelSnapshot.model_validate_json(
            canonical(
                {
                    "device_id": device.device_id,
                    "owner": device.owner.wire(),
                    "actor": control.actor.wire(),
                    "pairing_ref": device.pairing_ref.wire(),
                    "channel_ref": channel_ref.wire(),
                    "key_ref": device.key_ref.wire(),
                    "connected": True,
                    "expires_at": session.expires_at.isoformat(),
                }
            )
        )
        await session.check()
        return snapshot.wire()

    async def authenticated_principal(self, channel_ref: Ref, *, device_id: str) -> Principal:
        session = await self.session(channel_ref, device_id=device_id)
        assert session.local is not None and session.peer is not None
        control = session.local if session.local.role == "control" else session.peer
        return Principal.model_validate_json(canonical(control.actor.wire()))

    async def close(self) -> None:
        async with self.lock:
            sessions = tuple(self.connections.values())
            self.connections.clear()
        for session in sessions:
            await session.close()
