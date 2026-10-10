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


async def main() -> None:
    application = None
    work = None
    stopped = None
    try:
        identity = await asyncio.to_thread(WindowsApi().current)
        emit("identity", identity=identity.__dict__)
        if await asyncio.to_thread(sys.stdin.readline) != "start\n":
            return
        if len(sys.argv) != 2:
            raise CapabilityUnavailable("runner.helper.bootstrap_assembly")
        # This is trusted installation configuration, never a request/body-derived import.
        module = importlib.import_module(sys.argv[1])
        factory: HelperAssemblyPort = module.assembly
        application = await factory.create(identity)
        if not isinstance(application, HelperApplication):
            raise CapabilityUnavailable("runner.helper.bootstrap_assembly")
        work = asyncio.create_task(serve(application))
        stopped = asyncio.create_task(asyncio.to_thread(sys.stdin.readline))
        done, _ = await asyncio.wait((work, stopped), return_when=asyncio.FIRST_COMPLETED)
        if work in done:
            await work
    except DomainError as exc:
        emit("failure", code=exc.failure.code)
    except Exception:
        emit("failure", code="dependency_protocol_invalid")
    finally:
        if work is not None:
            work.cancel()
            try:
                await work
            except BaseException:
                pass
        if application is not None:
            await application.helper.close()
        if stopped is not None:
            stopped.cancel()
        emit("closed")


if __name__ == "__main__":
    from uaw_runner.helper_host import main as installed_main

    asyncio.run(installed_main())
