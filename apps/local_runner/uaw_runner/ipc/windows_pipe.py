"""Owned Windows overlapped pipe handles, explicit logon ACL and OS peer identity.

Every blocking operation runs in a worker with bounded waits; no impersonated business IO.
"""

import asyncio
import ctypes
import os
import re
import struct
import time
from ctypes import wintypes as W
from dataclasses import dataclass
from threading import Event, RLock
from typing import Any

from uaw.shared.errors import CapabilityUnavailable, reject

MAX_FRAME = 256 * 1024
DEFAULT_TIMEOUT = 10.0


class SecurityAttributes(ctypes.Structure):
    _fields_ = [("length", W.DWORD), ("descriptor", ctypes.c_void_p), ("inherit", W.BOOL)]


class Overlapped(ctypes.Structure):
    _fields_ = [
        ("internal", ctypes.c_size_t),
        ("high", ctypes.c_size_t),
        ("offset", W.DWORD),
        ("offset_high", W.DWORD),
        ("event", W.HANDLE),
    ]


class SidAttributes(ctypes.Structure):
    _fields_ = [("sid", ctypes.c_void_p), ("attributes", W.DWORD)]


@dataclass(frozen=True)
class OsIdentity:
    pid: int
    created: int
    user_sid: str
    logon_sid: str


class WindowsApi:
    def __init__(self) -> None:
        if os.name != "nt":
            raise CapabilityUnavailable("runner.windows_named_pipe")
        self.k: Any = ctypes.WinDLL("kernel32", use_last_error=True)
        self.a: Any = ctypes.WinDLL("advapi32", use_last_error=True)
        signatures = {
            "CreateNamedPipeW": (
                [W.LPCWSTR, W.DWORD, W.DWORD, W.DWORD, W.DWORD, W.DWORD, W.DWORD, ctypes.c_void_p],
                W.HANDLE,
            ),
            "CreateFileW": (
                [W.LPCWSTR, W.DWORD, W.DWORD, ctypes.c_void_p, W.DWORD, W.DWORD, W.HANDLE],
                W.HANDLE,
            ),
            "CreateEventW": ([ctypes.c_void_p, W.BOOL, W.BOOL, W.LPCWSTR], W.HANDLE),
            "CloseHandle": ([W.HANDLE], W.BOOL),
            "OpenProcess": ([W.DWORD, W.BOOL, W.DWORD], W.HANDLE),
            "GetProcessTimes": (
                [W.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p],
                W.BOOL,
            ),
            "WaitForSingleObject": ([W.HANDLE, W.DWORD], W.DWORD),
            "ConnectNamedPipe": ([W.HANDLE, ctypes.c_void_p], W.BOOL),
            "ReadFile": (
                [W.HANDLE, ctypes.c_void_p, W.DWORD, ctypes.c_void_p, ctypes.c_void_p],
                W.BOOL,
            ),
            "WriteFile": (
                [W.HANDLE, ctypes.c_void_p, W.DWORD, ctypes.c_void_p, ctypes.c_void_p],
                W.BOOL,
            ),
            "GetOverlappedResult": ([W.HANDLE, ctypes.c_void_p, ctypes.c_void_p, W.BOOL], W.BOOL),
            "CancelIoEx": ([W.HANDLE, ctypes.c_void_p], W.BOOL),
            "GetNamedPipeClientProcessId": ([W.HANDLE, ctypes.c_void_p], W.BOOL),
            "GetNamedPipeServerProcessId": ([W.HANDLE, ctypes.c_void_p], W.BOOL),
            "PeekNamedPipe": (
                [
                    W.HANDLE,
                    ctypes.c_void_p,
                    W.DWORD,
                    ctypes.c_void_p,
                    ctypes.c_void_p,
                    ctypes.c_void_p,
                ],
                W.BOOL,
            ),
            "GetCurrentThread": ([], W.HANDLE),
            "LocalFree": ([ctypes.c_void_p], ctypes.c_void_p),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.k, name)
            fn.argtypes = args
            fn.restype = result
        for name, args in {
            "OpenProcessToken": [W.HANDLE, W.DWORD, ctypes.c_void_p],
            "OpenThreadToken": [W.HANDLE, W.DWORD, W.BOOL, ctypes.c_void_p],
            "GetTokenInformation": [
                W.HANDLE,
                ctypes.c_int,
                ctypes.c_void_p,
                W.DWORD,
                ctypes.c_void_p,
            ],
            "ConvertSidToStringSidW": [ctypes.c_void_p, ctypes.c_void_p],
            "ConvertStringSecurityDescriptorToSecurityDescriptorW": [
                W.LPCWSTR,
                W.DWORD,
                ctypes.c_void_p,
                ctypes.c_void_p,
            ],
            "ImpersonateNamedPipeClient": [W.HANDLE],
            "RevertToSelf": [],
        }.items():
            fn = getattr(self.a, name)
            fn.argtypes = args
            fn.restype = W.BOOL

    def fail(self) -> None:
        raise OSError("Windows IPC identity/operation unavailable")

    def token_data(self, token: Any, kind: int) -> Any:
        size = W.DWORD()
        self.a.GetTokenInformation(token, kind, None, 0, ctypes.byref(size))
        if not 0 < size.value < 65536:
            self.fail()
        buf = ctypes.create_string_buffer(size.value)
        if not self.a.GetTokenInformation(token, kind, buf, size, ctypes.byref(size)):
            self.fail()
        return buf

    def sid_text(self, sid: Any) -> str:
        result = W.LPWSTR()
        if not self.a.ConvertSidToStringSidW(sid, ctypes.byref(result)):
            self.fail()
        try:
            return str(result.value)
        finally:
            self.k.LocalFree(result)

    def token_identity(self, token: Any) -> tuple[str, str]:
        user = self.token_data(token, 1)
        user_sid = self.sid_text(ctypes.cast(user, ctypes.POINTER(SidAttributes)).contents.sid)
        groups = self.token_data(token, 2)
        count = ctypes.cast(groups, ctypes.POINTER(W.DWORD)).contents.value
        offset = (
            (ctypes.sizeof(W.DWORD) + ctypes.alignment(SidAttributes) - 1)
            // ctypes.alignment(SidAttributes)
            * ctypes.alignment(SidAttributes)
        )
        items = ctypes.cast(ctypes.addressof(groups) + offset, ctypes.POINTER(SidAttributes))
        logons = [
            self.sid_text(items[i].sid)
            for i in range(count)
            if items[i].attributes & 0xC0000000 == 0xC0000000
        ]
        if len(logons) != 1:
            self.fail()
        return user_sid, logons[0]

    def process(self, pid: int) -> tuple[Any, OsIdentity]:
        handle = self.k.OpenProcess(0x1000 | 0x100000, False, pid)
        if not handle:
            self.fail()
        token = W.HANDLE()
        try:
            if not self.a.OpenProcessToken(handle, 8, ctypes.byref(token)):
                self.fail()
            user, logon = self.token_identity(token)
            times = [ctypes.c_ulonglong() for _ in range(4)]
            if not self.k.GetProcessTimes(handle, *(ctypes.byref(v) for v in times)):
                self.fail()
            if self.k.WaitForSingleObject(handle, 0) != 258:
                self.fail()
            return handle, OsIdentity(pid, times[0].value, user, logon)
        except BaseException:
            self.k.CloseHandle(handle)
            raise
        finally:
            if token.value:
                self.k.CloseHandle(token)

    def current(self) -> OsIdentity:
        handle, identity = self.process(os.getpid())
        self.k.CloseHandle(handle)
        return identity


class PipeConnection:
    def __init__(
        self,
        api: WindowsApi,
        handle: Any,
        *,
        server: bool,
        logon_sid: str,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if not 0 < timeout <= DEFAULT_TIMEOUT:
            raise ValueError("IPC timeout must be in (0,10]")
        self.api, self.handle, self.server, self.logon_sid = api, handle, server, logon_sid
        self.timeout = timeout
        self.closed = Event()
        self.lock = RLock()
        self.busy = asyncio.Lock()
        self.peer_handle: Any = None
        self.peer_identity: OsIdentity | None = None

    def deadline(self, deadline: float | None) -> float:
        return (
            min(time.monotonic() + self.timeout, deadline)
            if deadline is not None
            else time.monotonic() + self.timeout
        )

    def guard(self, deadline: float) -> None:
        if self.closed.is_set():
            raise reject("ipc_closed", "IPC connection is closed", 409, "dependency")
        if time.monotonic() >= deadline:
            raise reject("ipc_timeout", "IPC deadline exceeded", 410, "timeout")
        if self.peer_handle and self.api.k.WaitForSingleObject(self.peer_handle, 0) != 258:
            raise reject("ipc_peer_exited", "IPC peer exited", 410, "dependency")

    def overlapped(self, kind: str, buffer: Any, size: int, deadline: float) -> int:
        self.guard(deadline)
        event = self.api.k.CreateEventW(None, True, False, None)
        if not event:
            self.api.fail()
        op = Overlapped(event=event)
        done = W.DWORD()
        pending = False
        try:
            if kind == "connect":
                ok = self.api.k.ConnectNamedPipe(self.handle, ctypes.byref(op))
            else:
                ok = getattr(self.api.k, "ReadFile" if kind == "read" else "WriteFile")(
                    self.handle, buffer, size, ctypes.byref(done), ctypes.byref(op)
                )
            error = ctypes.get_last_error()
            if not ok and kind == "connect" and error == 535:
                return 0
            if not ok and error != 997:
                raise reject("ipc_broken", "IPC disconnected or OS IO failed", 409, "dependency")
            pending = not bool(ok)
            if pending:
                while self.api.k.WaitForSingleObject(event, 20) == 258:
                    self.guard(deadline)
            if not self.api.k.GetOverlappedResult(
                self.handle, ctypes.byref(op), ctypes.byref(done), False
            ):
                raise reject("ipc_broken", "IPC operation failed", 409, "dependency")
            pending = False
            self.guard(deadline)
            return int(done.value)
        finally:
            if pending:
                self.api.k.CancelIoEx(self.handle, ctypes.byref(op))
                # Cancellation completion before freeing OVERLAPPED/buffer memory.
                self.api.k.GetOverlappedResult(
                    self.handle, ctypes.byref(op), ctypes.byref(done), True
                )
            self.api.k.CloseHandle(event)

    def receive_sync(self, deadline: float) -> bytes:
        with self.lock:

            def exact(size: int) -> bytes:
                result = bytearray()
                while len(result) < size:
                    buffer = ctypes.create_string_buffer(size - len(result))
                    count = self.overlapped("read", buffer, len(buffer), deadline)
                    if not count:
                        raise reject("ipc_broken", "Truncated IPC frame", 409, "dependency")
                    result.extend(buffer.raw[:count])
                return bytes(result)

            length = struct.unpack("!I", exact(4))[0]
            if not 0 < length <= MAX_FRAME:
                raise reject("ipc_frame_invalid", "IPC frame length rejected")
            return exact(length)

    def send_sync(self, data: bytes, deadline: float) -> None:
        if not 0 < len(data) <= MAX_FRAME:
            raise reject("ipc_frame_invalid", "IPC frame length rejected")
        with self.lock:
            raw = struct.pack("!I", len(data)) + data
            offset = 0
            while offset < len(raw):
                buffer = ctypes.create_string_buffer(raw[offset:])
                count = self.overlapped("write", buffer, len(raw) - offset, deadline)
                if not count:
                    raise reject("ipc_broken", "IPC write interrupted", 409, "dependency")
                offset += count

    def identify_sync(self) -> OsIdentity:
        with self.lock:
            self.guard(time.monotonic() + self.timeout)
            pid = W.DWORD()
            fn = (
                self.api.k.GetNamedPipeClientProcessId
                if self.server
                else self.api.k.GetNamedPipeServerProcessId
            )
            if not fn(self.handle, ctypes.byref(pid)):
                self.api.fail()
            process, identity = self.api.process(pid.value)
            try:
                if identity.logon_sid != self.logon_sid:
                    raise reject(
                        "ipc_identity_denied", "Peer logon identity rejected", 403, "permission"
                    )
                if self.server:
                    # Last client message has been read; identify token on THIS worker thread.
                    if not self.api.a.ImpersonateNamedPipeClient(self.handle):
                        self.api.fail()
                    token = W.HANDLE()
                    try:
                        if not self.api.a.OpenThreadToken(
                            self.api.k.GetCurrentThread(), 8, True, ctypes.byref(token)
                        ):
                            self.api.fail()
                        if self.api.token_identity(token) != (
                            identity.user_sid,
                            identity.logon_sid,
                        ):
                            raise OSError("Pipe token and process identity differ")
                    finally:
                        if token.value:
                            self.api.k.CloseHandle(token)
                        if not self.api.a.RevertToSelf():
                            os._exit(70)  # Cannot return a worker with leaked identity.
                if self.peer_identity is not None and identity != self.peer_identity:
                    raise reject(
                        "ipc_identity_denied", "Peer process instance changed", 403, "permission"
                    )
                if self.peer_handle:
                    self.api.k.CloseHandle(process)
                else:
                    self.peer_handle, self.peer_identity = process, identity
                return identity
            except BaseException:
                self.api.k.CloseHandle(process)
                raise

    async def operation(self, fn: Any, *args: Any) -> Any:
        if self.busy.locked():
            raise reject("ipc_busy", "Only one in-flight pipe operation is allowed", 409)
        async with self.busy:
            task = asyncio.create_task(asyncio.to_thread(fn, *args))
            try:
                return await asyncio.shield(task)
            except BaseException as exc:
                self.closed.set()
                self.api.k.CancelIoEx(self.handle, None)
                while not task.done():
                    try:
                        await asyncio.shield(task)
                    except asyncio.CancelledError:
                        continue
                    except Exception:
                        break
                await self.close()
                if isinstance(exc, OSError):
                    raise CapabilityUnavailable("runner.ipc.os_identity") from None
                raise

    async def receive(self, *, deadline: float | None = None) -> bytes:
        return bytes(await self.operation(self.receive_sync, self.deadline(deadline)))

    async def send(self, data: bytes, *, deadline: float | None = None) -> None:
        await self.operation(self.send_sync, bytes(data), self.deadline(deadline))

    async def identify(self) -> OsIdentity:
        result = await self.operation(self.identify_sync)
        assert isinstance(result, OsIdentity)
        return result

    def live_sync(self) -> bool:
        with self.lock:
            if self.closed.is_set() or self.peer_handle is None:
                return False
            if self.api.k.WaitForSingleObject(self.peer_handle, 0) != 258:
                return False
            if not self.api.k.PeekNamedPipe(self.handle, None, 0, None, None, None):
                return False
            assert self.peer_identity is not None
            try:
                handle, actual = self.api.process(self.peer_identity.pid)
                self.api.k.CloseHandle(handle)
                return actual == self.peer_identity
            except OSError:
                return False

    def close_sync(self) -> None:
        self.closed.set()
        self.api.k.CancelIoEx(self.handle, None)
        with self.lock:
            if self.handle:
                self.api.k.CloseHandle(self.handle)
                self.handle = None
            if self.peer_handle:
                self.api.k.CloseHandle(self.peer_handle)
                self.peer_handle = None

    async def close(self) -> None:
        self.closed.set()
        if self.handle:
            self.api.k.CancelIoEx(self.handle, None)
        await asyncio.to_thread(self.close_sync)


class WindowsPipeListener:
    def __init__(self, *, name: str, logon_sid: str, timeout: float = DEFAULT_TIMEOUT) -> None:
        if not 0 < timeout <= DEFAULT_TIMEOUT:
            raise ValueError("IPC timeout must be in (0,10]")
        if not re.fullmatch(r"uaw-[A-Za-z0-9_-]{8,96}", name):
            raise ValueError("Invalid local pipe name")
        self.api = WindowsApi()
        if self.api.current().logon_sid != logon_sid:
            raise ValueError("Listener must own the explicit logon SID")
        descriptor = ctypes.c_void_p()
        # Exact rights avoid FILE_GENERIC_WRITE's FILE_CREATE_PIPE_INSTANCE alias.
        sddl = f"D:P(A;;0x0012019B;;;{logon_sid})"
        if not self.api.a.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, 1, ctypes.byref(descriptor), None
        ):
            self.api.fail()
        security = SecurityAttributes(ctypes.sizeof(SecurityAttributes), descriptor, False)
        try:
            handle = self.api.k.CreateNamedPipeW(
                chr(92) * 2 + "." + chr(92) + "pipe" + chr(92) + name,
                3 | 0x40000000 | 0x80000,
                8,
                1,
                MAX_FRAME,
                MAX_FRAME,
                10000,
                ctypes.byref(security),
            )
            if handle == ctypes.c_void_p(-1).value:
                self.api.fail()
        finally:
            self.api.k.LocalFree(descriptor)
        self.name, self.sddl = name, sddl
        self.connection = PipeConnection(
            self.api, handle, server=True, logon_sid=logon_sid, timeout=timeout
        )
        self.accepted = False

    async def accept(self, *, deadline: float | None = None) -> PipeConnection:
        if self.accepted:
            raise reject("ipc_closed", "Listener accepts exactly one connection", 409)
        self.accepted = True
        await self.connection.operation(
            self.connection.overlapped, "connect", None, 0, self.connection.deadline(deadline)
        )
        return self.connection

    async def close(self) -> None:
        await self.connection.close()


async def connect_pipe(  # noqa: ASYNC109 - worker IO uses absolute bounded deadlines
    *,
    name: str,
    logon_sid: str,
    timeout: float = DEFAULT_TIMEOUT,  # noqa: ASYNC109 - absolute OS deadline
    deadline: float | None = None,
) -> PipeConnection:
    if not re.fullmatch(r"uaw-[A-Za-z0-9_-]{8,96}", name):
        raise ValueError("Invalid local pipe name")
    if not 0 < timeout <= DEFAULT_TIMEOUT:
        raise ValueError("IPC timeout must be in (0,10]")
    api = WindowsApi()
    until = (
        min(time.monotonic() + timeout, deadline)
        if deadline is not None
        else time.monotonic() + timeout
    )
    while True:
        opening = asyncio.create_task(
            asyncio.to_thread(
                api.k.CreateFileW,
                chr(92) * 2 + "." + chr(92) + "pipe" + chr(92) + name,
                0x0012019B,
                0,
                None,
                3,
                0x40000000 | 0x00110000,
                None,
            )
        )
        try:
            handle = await asyncio.shield(opening)
        except BaseException:
            while not opening.done():
                try:
                    await asyncio.shield(opening)
                except asyncio.CancelledError:
                    continue
            handle = opening.result()
            if handle != ctypes.c_void_p(-1).value:
                api.k.CloseHandle(handle)
            raise
        if handle != ctypes.c_void_p(-1).value:
            if time.monotonic() >= until:
                api.k.CloseHandle(handle)
                raise reject("ipc_timeout", "Pipe connect deadline exceeded", 410, "timeout")
            return PipeConnection(api, handle, server=False, logon_sid=logon_sid, timeout=timeout)
        if time.monotonic() >= until:
            raise reject("ipc_timeout", "Pipe connect deadline exceeded", 410, "timeout")
        await asyncio.sleep(0.02)
