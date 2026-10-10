"""Hidden process host. A installs the trusted factory; default bootstrap is absent.

Only actual native authorization UI may be visible. stdout has bounded public lifecycle
metadata; no codes/proofs, private keys, paths, file bodies or principals are printed.
"""

import asyncio
import importlib
import json
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from uaw.shared.errors import CapabilityUnavailable, DomainError, reject
from uaw.shared.runner_bootstrap import FirstStartPolicy, FirstStartProgressPort
from uaw_runner.helper_stdio import PipeLineReader
from uaw_runner.ipc.windows_pipe import OsIdentity, WindowsApi
from uaw_runner.runtime import ReadOnlyHelper


@dataclass(frozen=True)
class HelperApplication:
    helper: ReadOnlyHelper
    # Trusted local control adapter, not a wire callback or boolean approval.
    on_connected: Callable[[ReadOnlyHelper], Awaitable[None]] | None = None


class HelperAssemblyPort(Protocol):
    async def create(self, identity: OsIdentity) -> HelperApplication: ...


def emit(event: str, **values: object) -> None:
    print(json.dumps({"event": event, **values}, separators=(",", ":")), flush=True)


class HelperBootstrapProgress(FirstStartProgressPort):
    """One original checked challenge progress, never approval or a grant."""

    def __init__(self) -> None:
        self.sent = False

    async def waiting(self, policy: FirstStartPolicy) -> None:
        if self.sent or not isinstance(policy, FirstStartPolicy):
            raise reject("dependency_protocol_invalid", "Repeated first-start progress", 503)
        if datetime.now(UTC) >= policy.expires_at:
            raise reject("enrollment_expired", "Original challenge expired", 410)
        self.sent = True
        writing = asyncio.create_task(
            asyncio.to_thread(
                emit,
                "bootstrap_waiting",
                stage="enrollment",
                expires_at=policy.expires_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
                challenge_hash=policy.challenge_hash,
            )
        )
        try:
            await asyncio.shield(writing)
        except asyncio.CancelledError:
            await writing
            raise


async def serve(application: HelperApplication) -> None:
    helper = application.helper
    try:
        while True:
            address = await helper.start()
            emit("ready", name=address.name, identity=address.identity.__dict__)
            try:
                channel = await helper.accept()
                emit("connected", channel_ref=channel.wire())
                if application.on_connected is not None:
                    await application.on_connected(helper)
                receipt = await helper.serve_once()
                emit("receipt", receipt_ref=receipt.wire())
            except DomainError as exc:
                emit("failure", code=exc.failure.code)
            finally:
                await helper.disconnect()
    finally:
        await helper.close()


async def initialize(
    factory: HelperAssemblyPort, identity: OsIdentity, stopping: asyncio.Event
) -> None:
    application = None
    try:
        application = await factory.create(identity)
        if not isinstance(application, HelperApplication):
            raise CapabilityUnavailable("runner.helper.bootstrap_assembly")
        # A factory may finish in a cancellation cleanup/late worker. Never start
        # its listener after stop; own and close the returned helper instead.
        if not stopping.is_set():
            await serve(application)
    finally:
        if isinstance(application, HelperApplication):
            await application.helper.close()


async def main() -> None:
    work: asyncio.Task[None] | None = None
    stopped: asyncio.Task[bytes] | None = None
    stopping = asyncio.Event()
    try:
        identity = await asyncio.to_thread(WindowsApi().current)
        emit("identity", identity=identity.__dict__)
        reader = PipeLineReader(sys.stdin.buffer)
        if await reader.readline(32) != b"start\n":
            return
        # Subscribe BEFORE invoking the installed factory, including native UI wait.
        stopped = asyncio.create_task(reader.readline(32))
        if len(sys.argv) != 2:
            raise CapabilityUnavailable("runner.helper.bootstrap_assembly")
        module = importlib.import_module(sys.argv[1])
        factory: HelperAssemblyPort = module.assembly
        work = asyncio.create_task(initialize(factory, identity, stopping))
        done, _ = await asyncio.wait((work, stopped), return_when=asyncio.FIRST_COMPLETED)
        if stopped in done:
            await stopped  # EOF and stop both cancel; malformed/truncated input fails closed.
            stopping.set()
        elif work in done:
            await work
    except DomainError as exc:
        emit("failure", code=exc.failure.code)
    except Exception:
        emit("failure", code="dependency_protocol_invalid")
    finally:
        stopping.set()
        if work is not None:
            work.cancel()
            await asyncio.gather(work, return_exceptions=True)
        if stopped is not None:
            stopped.cancel()
            await asyncio.gather(stopped, return_exceptions=True)
        emit("closed")


if __name__ == "__main__":
    from uaw.infrastructure.event_loop import control_plane_loop
    from uaw_runner.helper_host import main as installed_main

    asyncio.run(installed_main(), loop_factory=control_plane_loop)
