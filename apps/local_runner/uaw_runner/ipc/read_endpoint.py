"""Internal read-only connection adapter. A owns control side and production assembly.

Bodies carry only an independently registered fixed command Ref, never authority.
Explicit recovery cannot start an unknown attempt; transport never resends commands.
"""

import asyncio
from typing import Any, Protocol

from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.workspace.contracts import RegisteredReceiptCommand
from uaw.workspace.ports import ReceiptCommandReaderPort, RunnerReadCurrentPort
from uaw_runner.ipc.channel_source import ConnectionRegistry
from uaw_runner.ipc.sessions import AuthenticatedPipeSession
from uaw_runner.read_current import reply_deadline
from uaw_runner.read_executor import ReadOnlyRunner
from uaw_runner.read_watch import LocalReadInvalidation, stop_on_change
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
        current_source: RunnerReadCurrentPort | None = None,
        local_monitor: LocalReadInvalidation | None = None,
    ) -> None:
        self.session, self.registry, self.commands, self.runners = (
            session,
            registry,
            commands,
            runners,
        )
        self.current_source = current_source
        self.local_monitor = local_monitor
        self.watch_frame: dict[str, Any] | None = None
        self.watch_deadline: float | None = None
        self.busy = False

    async def dispatch(self, frame: dict[str, Any], *, deadline: float | None = None) -> Ref:
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
            or runner.current_source is not self.current_source
        ):
            raise reject("binding_mismatch", "Read assembly differs from trusted connection")
        if runner.executions is None:
            raise CapabilityUnavailable("runner.file_read_journal")
        if frame["kind"] == "recover":
            attempt = await asyncio.to_thread(runner.executions.get, source, ref)
            await self.session.check()
            if attempt is None or attempt.receipt_data is None:
                raise CapabilityUnavailable("runner.ipc.original_signed_read_outcome")
        receipt = await runner.execute(
            source.command, authenticated_principal=actor, response_deadline=deadline
        )
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
        if deadline is not None:
            reply_deadline(deadline)
        await self.session.send(
            "receipt",
            {
                "command_ref": ref.wire(),
                "receipt_ref": attempt.receipt_ref.wire(),
                "receipt": actual.wire(),
            },
            deadline=deadline,
        )
        return attempt.receipt_ref

    async def full_watch(self) -> None:
        while True:
            await asyncio.sleep(0.05)
            await self.session.check()

    async def watch(self) -> None:
        frame, deadline = self.watch_frame, self.watch_deadline
        if (
            self.current_source is None
            or self.local_monitor is None
            or frame is None
            or frame.get("kind") != "command"
            or deadline is None
        ):
            # Legacy/default and journal data recovery keep the original full monitor.
            await self.full_watch()
            return
        if self.commands is None or self.runners is None or self.session.local is None:
            raise CapabilityUnavailable("runner.ipc.registered_read_assembly")
        if set(frame["body"]) != {"command_ref"} or self.session.local.role != "device":
            raise reject("ipc_request_invalid", "Original registered command required")
        ref = fixed_ref(Ref.model_validate_json(canonical(frame["body"]["command_ref"])))
        channel_ref = self.session.channel_ref
        if channel_ref is None:
            raise CapabilityUnavailable("runner.ipc.handshake")
        # Identity from the authenticated connection, never incoming body/command.
        channel = self.registry._snapshot(
            self.session, channel_ref, device_id=self.session.local.device_id
        )
        actor = Principal.model_validate_json(canonical(channel.actor.wire()))

        async def active_or_recovery() -> None:
            assert self.commands is not None and self.runners is not None
            assert self.local_monitor is not None
            source = await self.commands.resolve(ref, authenticated_principal=actor)
            runner = await self.runners.create(ref, channel_ref=channel_ref)
            if (
                not isinstance(source, RegisteredReceiptCommand)
                or runner.command_ref != ref
                or runner.channel_ref != channel_ref
                or runner.journal.reader is not self.commands
                or runner.current_source is not self.current_source
            ):
                raise reject("binding_mismatch", "Independent monitor assembly differs", 503)
            if runner.executions is None:
                raise CapabilityUnavailable("runner.file_read_journal")
            prior = await asyncio.to_thread(runner.executions.get, source, ref)
            if prior is not None and prior.receipt_data is not None:
                # Duplicate command may restore an original signed journal.
                # Data permission remains independent of active execution current.
                await self.full_watch()
                return
            assert self.current_source is not None
            await stop_on_change(
                self.current_source.wait_changed(
                    ref, authenticated_principal=actor, channel_ref=channel_ref, deadline=deadline
                ),
                self.local_monitor.watch(
                    runner,
                    source,
                    authenticated_principal=actor,
                    session=self.session,
                    registry=self.registry,
                    deadline=deadline,
                ),
            )

        await stop_on_change(
            active_or_recovery(),
            self.local_monitor.watch_connection(self.session, deadline=deadline),
        )

    async def serve_once(self, *, deadline: float | None = None) -> Ref:
        if self.busy:
            raise reject("ipc_busy", "Read endpoint already in use", 409)
        self.busy = True
        work = monitor = None
        try:
            until = min(self.session.pipe.deadline(deadline), self.session.monotonic_expiry)
            if self.current_source is not None:
                reply_deadline(until)
            frame = await self.session.receive(deadline=until)
            async with asyncio.timeout_at(until):
                work = asyncio.create_task(self.dispatch(frame, deadline=until))
                self.watch_frame, self.watch_deadline = frame, until
                monitor = asyncio.create_task(self.watch())
                done, _ = await asyncio.wait((work, monitor), return_when=asyncio.FIRST_COMPLETED)
                if monitor in done:
                    await monitor  # raises actual disconnect/revocation/expiry
                    raise reject("runner_current_changed", "Original monitor ended", 412)
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
            self.watch_frame, self.watch_deadline = None, None
            self.busy = False
