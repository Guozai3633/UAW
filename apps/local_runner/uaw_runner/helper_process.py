"""Launch only the installed helper host and a trusted deployment assembly module.

No per-command program, shell, identity, approved flag or directory argument exists.
"""

import asyncio
import json
import re
import subprocess
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.runner_bootstrap import FirstStartPolicy, FirstStartProgressPort
from uaw_runner.helper_stdio import PipeLineReader
from uaw_runner.ipc.windows_pipe import OsIdentity, WindowsApi


class HelperProcess:
    def __init__(self, process: subprocess.Popen[bytes], identity: OsIdentity) -> None:
        self.process, self.identity = process, identity
        self.closed = False
        self.started = False
        self.read_lock = asyncio.Lock()
        self.closing: asyncio.Task[None] | None = None
        self.reader = PipeLineReader(process.stdout) if process.stdout is not None else None

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

    async def event(
        self, *, deadline: float | None = None, _waiting: bool = False
    ) -> dict[str, Any]:
        if self.reader is None:
            raise CapabilityUnavailable("runner.helper.stdout")
        if deadline is None:
            deadline = asyncio.get_running_loop().time() + 15
        try:
            async with asyncio.timeout_at(deadline), self.read_lock:
                line = await self.reader.readline(4096)
                if not line or len(line) > 4096:
                    raise ValueError("Closed lifecycle stream")
                value = json.loads(
                    line.decode("utf-8"),
                    object_pairs_hook=strict_object,
                    parse_constant=invalid_constant,
                )
                if not isinstance(value, dict) or value.get("event") not in {
                    "identity",
                    "ready",
                    "connected",
                    "receipt",
                    "failure",
                    "closed",
                    *({"bootstrap_waiting"} if _waiting else set()),
                }:
                    raise ValueError("Invalid lifecycle event")
                return value
        except asyncio.CancelledError:
            await self.close()
            raise
        except ValueError, TimeoutError, OSError:
            await self.close()
            raise reject(
                "dependency_protocol_invalid", "Helper lifecycle response unavailable", 503
            ) from None

    async def start(
        self,
        *,
        first_start: FirstStartPolicy | None = None,
        on_progress: FirstStartProgressPort | None = None,
    ) -> dict[str, Any]:
        if self.closed or self.started or self.process.stdin is None:
            raise CapabilityUnavailable("runner.helper.closed")
        if first_start is not None and not isinstance(first_start, FirstStartPolicy):
            raise ValueError("Original FirstStartPolicy required")
        self.started = True
        loop = asyncio.get_running_loop()
        # Calculate once. Frames, observers and writes cannot extend this deadline.
        budget = 15.0 if first_start is None else first_start.remaining(datetime.now(UTC))
        deadline = loop.time() + budget
        waiting = False

        def check_expiry() -> None:
            if loop.time() >= deadline and budget > 0:
                raise TimeoutError("Original startup deadline exceeded")
            if first_start is not None and datetime.now(UTC) >= first_start.expires_at:
                raise reject("enrollment_expired", "Original challenge expired", 410)

        def begin() -> None:
            assert self.process.stdin is not None
            self.process.stdin.write(b"start\n")
            self.process.stdin.flush()

        sending: asyncio.Task[None] | None = None
        try:
            async with asyncio.timeout_at(deadline):
                check_expiry()
                sending = asyncio.create_task(asyncio.to_thread(begin))
                await asyncio.shield(sending)
                while True:
                    event = await self.event(deadline=deadline, _waiting=True)
                    check_expiry()
                    if event["event"] == "bootstrap_waiting":
                        if first_start is None or waiting:
                            raise ValueError("Unexpected or repeated first-start progress")
                        validate_waiting(event, first_start)
                        waiting = True
                        if on_progress is not None:
                            await on_progress.waiting(first_start)
                        check_expiry()
                        continue
                    if event["event"] == "failure":
                        if set(event) != {"event", "code"} or not isinstance(event["code"], str):
                            raise ValueError("Invalid failure event")
                        raise reject(event["code"], "Helper bootstrap failed", 503, "dependency")
                    if event["event"] != "ready":
                        raise ValueError("Helper did not become ready")
                    if (
                        set(event) != {"event", "name", "identity"}
                        or not isinstance(event["name"], str)
                        or not 0 < len(event["name"]) <= 160
                        or event["identity"] != self.identity.__dict__
                    ):
                        raise ValueError("Helper ready response invalid")
                    return event
        except BaseException as exc:
            # close stdin/process first, then drain a late start write if necessary.
            await self.close()
            if sending is not None:
                await asyncio.gather(sending, return_exceptions=True)
            if isinstance(exc, (ValueError, TimeoutError, OSError)):
                raise reject(
                    "dependency_protocol_invalid", "Helper bootstrap response unavailable", 503
                ) from None
            raise

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
            if (
                self.process.poll() is None
                and self.process.stdin is not None
                and not self.process.stdin.closed
            ):
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


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Repeated lifecycle field")
        result[key] = value
    return result


def invalid_constant(value: str) -> Any:
    raise ValueError("Non-finite lifecycle value")


def validate_waiting(event: dict[str, Any], policy: FirstStartPolicy) -> None:
    if (
        set(event) != {"event", "stage", "expires_at", "challenge_hash"}
        or event["stage"] != "enrollment"
        or event["challenge_hash"] != policy.challenge_hash
        or not isinstance(event["expires_at"], str)
    ):
        raise ValueError("First-start challenge progress differs")
    expiry = datetime.fromisoformat(event["expires_at"])
    offset = expiry.utcoffset()
    if (
        expiry.tzinfo is None
        or offset is None
        or offset.total_seconds() != 0
        or expiry != policy.expires_at
    ):
        raise ValueError("First-start challenge expiry differs")
