"""Internal read-only connection adapter. A owns control side and production assembly.

Bodies carry only an independently registered fixed command Ref, never authority.
Explicit recovery cannot start an unknown attempt; transport never resends commands.
"""

import asyncio
from typing import Any, Protocol

from uaw.shared.contracts import Ref
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.workspace.contracts import RegisteredReceiptCommand
from uaw.workspace.ports import ReceiptCommandReaderPort
from uaw_runner.ipc.channel_source import ConnectionRegistry
from uaw_runner.ipc.sessions import AuthenticatedPipeSession
from uaw_runner.read_executor import ReadOnlyRunner
from uaw_runner.receipts import canonical, digest, fixed_ref


class ReadOnlyRunnerFactoryPort(Protocol):
    async def create(self, command_ref: Ref, *, channel_ref: Ref) -> ReadOnlyRunner:
        """Compose registered dependencies; never derive ownership from an IPC body."""
        ...


class ReadOnlyPipeEndpoint:
    def __init__(
        self,
        *,
        session: AuthenticatedPipeSession,
        registry: ConnectionRegistry,
        commands: ReceiptCommandReaderPort | None = None,
        runners: ReadOnlyRunnerFactoryPort | None = None,
    ) -> None:
        self.session, self.registry, self.commands, self.runners = (
            session,
            registry,
            commands,
            runners,
        )
        self.busy = False

    async def dispatch(self, frame: dict[str, Any]) -> Ref:
        if self.commands is None or self.runners is None:
            raise CapabilityUnavailable("runner.ipc.registered_read_assembly")
        if self.session.local is None or self.session.local.role != "device":
            raise CapabilityUnavailable("runner.ipc.device_endpoint")
        if frame["kind"] not in {"command", "recover"} or set(frame["body"]) != {"command_ref"}:
            raise reject("ipc_request_invalid", "Only a fixed registered read command is supported")
        try:
            ref = fixed_ref(Ref.model_validate_json(canonical(frame["body"]["command_ref"])))
        except ValueError, TypeError:
            raise reject("ipc_request_invalid", "Invalid fixed command Ref") from None
        channel_ref = self.session.channel_ref
        if channel_ref is None:
            raise CapabilityUnavailable("runner.ipc.handshake")
        device_id = self.session.local.device_id
        actor = await self.registry.authenticated_principal(channel_ref, device_id=device_id)
        source = await self.commands.resolve(ref, authenticated_principal=actor)
        await self.session.check()
        if not isinstance(source, RegisteredReceiptCommand):
            raise reject(
                "dependency_protocol_invalid", "Registered command source type invalid", 503
            )
        if source.device_id != device_id or ref.content_hash != digest(source.command.wire()):
            raise reject("binding_mismatch", "Registered device/command digest differs")
        runner = await self.runners.create(ref, channel_ref=channel_ref)
        await self.session.check()
        if (
            runner.command_ref.wire() != ref.wire()
            or runner.channel is not self.registry
            or runner.channel_ref is None
            or runner.channel_ref.wire() != channel_ref.wire()
            or runner.journal.reader is not self.commands
            or runner.protocol.device_id != device_id
        ):
            raise reject("binding_mismatch", "Read assembly differs from trusted connection")
        if runner.executions is None:
            raise CapabilityUnavailable("runner.file_read_journal")
        if frame["kind"] == "recover":
            attempt = await asyncio.to_thread(runner.executions.get, source, ref)
            await self.session.check()
            if attempt is None or attempt.receipt_data is None:
                raise CapabilityUnavailable("runner.ipc.original_signed_read_outcome")
        receipt = await runner.execute(source.command, authenticated_principal=actor)
        # ReadOnlyRunner independently checks mapping, root, lease/fence/flags/keys,
        # current authority and one-use CAS. Recovery uses current data permission.
        await self.session.check()
        source = await self.commands.resolve(ref, authenticated_principal=actor)
        attempt = await asyncio.to_thread(runner.executions.get, source, ref)
        if attempt is None or attempt.receipt_ref is None:
            raise CapabilityUnavailable("runner.ipc.published_read_outcome")
        actual = await runner.journal.read(attempt.receipt_ref, authenticated_principal=actor)
        if actual.wire() != receipt.wire():
            raise reject("revision_conflict", "Published read outcome differs", 409)
        await self.session.check()
        await self.session.send(
            "receipt",
            {
                "command_ref": ref.wire(),
                "receipt_ref": attempt.receipt_ref.wire(),
                "receipt": actual.wire(),
            },
        )
        return attempt.receipt_ref

    async def watch(self) -> None:
        while True:
            await asyncio.sleep(0.05)
            await self.session.check()

    async def serve_once(self) -> Ref:
        if self.busy:
            raise reject("ipc_busy", "Read endpoint already in use", 409)
        self.busy = True
        work = monitor = None
        try:
            frame = await self.session.receive()
            async with asyncio.timeout(self.session.pipe.timeout):
                work = asyncio.create_task(self.dispatch(frame))
                monitor = asyncio.create_task(self.watch())
                done, _ = await asyncio.wait((work, monitor), return_when=asyncio.FIRST_COMPLETED)
                if monitor in done:
                    await monitor  # raises actual disconnect/revocation/expiry
                return await work
        except TimeoutError:
            await self.session.close()
            raise reject("ipc_timeout", "Read response deadline expired", 408) from None
        except BaseException:
            await self.session.close()
            raise
        finally:
            for task in (work, monitor):
                if task is not None:
                    task.cancel()
            for task in (work, monitor):
                if task is not None:
                    try:
                        await task
                    except BaseException:
                        pass
            self.busy = False
