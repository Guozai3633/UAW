"""Launch only the installed helper host and a trusted deployment assembly module.

No per-command program, shell, identity, approved flag or directory argument exists.
"""

import asyncio
import json
import re
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from uaw.shared.errors import CapabilityUnavailable, reject
from uaw_runner.ipc.windows_pipe import OsIdentity, WindowsApi


class HelperProcess:
    def __init__(self, process: subprocess.Popen[bytes], identity: OsIdentity) -> None:
        self.process, self.identity = process, identity
        self.closed = False
        self.started = False
        self.read_lock = asyncio.Lock()
        self.closing: asyncio.Task[None] | None = None

    @classmethod
    async def prepare(
        cls, *, python: Path, assembly_module: str, environment: Mapping[str, str] | None = None
    ) -> HelperProcess:
        if not hasattr(subprocess, "CREATE_NO_WINDOW"):
            raise CapabilityUnavailable("runner.helper.windows")
        if not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", assembly_module):
            raise ValueError("Trusted deployment module required")
        spawning = asyncio.create_task(
            asyncio.to_thread(
                subprocess.Popen,
                [str(python), "-m", "uaw_runner.helper_host", assembly_module],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
                env=dict(environment) if environment is not None else None,
            )
        )
        try:
            process = await asyncio.shield(spawning)
        except asyncio.CancelledError:
            process = await spawning
            await cls(process, OsIdentity(0, 0, "", "")).close()
            raise
        holder = cls(process, OsIdentity(0, 0, "", ""))
        try:
            value = await holder.event()
            if set(value) != {"event", "identity"} or value["event"] != "identity":
                raise reject("dependency_protocol_invalid", "Helper identity response invalid", 503)
            identity = OsIdentity(**value["identity"])
            if identity.pid != process.pid:
                raise reject("permission_denied", "Helper PID differs", 403, "permission")

            def actual_identity() -> OsIdentity:
                api = WindowsApi()
                handle, actual = api.process(process.pid)
                try:
                    return actual
                finally:
                    api.k.CloseHandle(handle)

            if await asyncio.to_thread(actual_identity) != identity:
                raise reject("permission_denied", "Helper OS instance differs", 403, "permission")
            holder.identity = identity
            return holder
        except BaseException:
            await holder.close()
            raise

    async def event(self) -> dict[str, Any]:
        if self.process.stdout is None:
            raise CapabilityUnavailable("runner.helper.stdout")
        async with self.read_lock:
            try:
                async with asyncio.timeout(15):
                    line = await asyncio.to_thread(self.process.stdout.readline, 4097)
                if not line or len(line) > 4096:
                    raise ValueError("Closed or oversized event")
                value = json.loads(line)
                if not isinstance(value, dict) or value.get("event") not in {
                    "identity",
                    "ready",
                    "connected",
                    "receipt",
                    "failure",
                    "closed",
                }:
                    raise ValueError("Invalid lifecycle event")
                return value
            except asyncio.CancelledError:
                await self.close()
                raise
            except ValueError, TimeoutError:
                await self.close()
                raise reject(
                    "dependency_protocol_invalid", "Helper lifecycle response unavailable", 503
                ) from None

    async def start(self) -> dict[str, Any]:
        if self.closed or self.started or self.process.stdin is None:
            raise CapabilityUnavailable("runner.helper.closed")
        self.started = True

        def begin() -> None:
            assert self.process.stdin is not None
            self.process.stdin.write(b"start\n")
            self.process.stdin.flush()

        await asyncio.to_thread(begin)
        event = await self.event()
        if event["event"] != "ready":
            raise CapabilityUnavailable("runner.helper.bootstrap")
        return event

    async def close(self) -> None:
        if self.closing is not None:
            try:
                await asyncio.shield(self.closing)
            except asyncio.CancelledError:
                await self.closing
                raise
            return
        self.closed = True

        def finish() -> None:
            if self.process.poll() is None and self.process.stdin is not None:
                try:
                    self.process.stdin.write(b"stop\n")
                    self.process.stdin.flush()
                except BrokenPipeError, ConnectionError, OSError:
                    pass
                self.process.stdin.close()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
            for stream in (self.process.stdin, self.process.stdout):
                if stream is not None:
                    stream.close()

        closing = asyncio.create_task(asyncio.to_thread(finish))
        self.closing = closing
        try:
            await asyncio.shield(closing)
        except asyncio.CancelledError:
            await closing
            raise
