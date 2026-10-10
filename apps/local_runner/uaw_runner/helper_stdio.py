"""Cancellation-safe reads of owned Windows subprocess pipes.

Peek before reading only available bytes; no blocked readline executor thread survives
stop/EOF or cancellation. The subprocess owns the handles, this reader owns no handle.
"""

import asyncio
import ctypes
import msvcrt
from ctypes import wintypes as W
from typing import IO

from uaw_runner.ipc.windows_pipe import WindowsApi


class PipeLineReader:
    def __init__(self, stream: IO[bytes]) -> None:
        self.handle = msvcrt.get_osfhandle(stream.fileno())
        self.api = WindowsApi()
        self.buffer = bytearray()

    def poll(self, limit: int) -> bytes | None:
        available = W.DWORD()
        if not self.api.k.PeekNamedPipe(self.handle, None, 0, None, ctypes.byref(available), None):
            if ctypes.get_last_error() in (109, 232):
                return b""
            self.api.fail()
        if not available.value:
            return None
        size = min(available.value, limit)
        data = ctypes.create_string_buffer(size)
        read = W.DWORD()
        if not self.api.k.ReadFile(self.handle, data, size, ctypes.byref(read), None):
            self.api.fail()
        return data.raw[: read.value]

    async def readline(self, limit: int) -> bytes:
        while True:
            end = self.buffer.find(b"\n")
            if end >= 0:
                end += 1
                line = bytes(self.buffer[:end])
                del self.buffer[:end]
                if len(line) > limit:
                    raise ValueError("Oversized lifecycle line")
                return line
            if len(self.buffer) >= limit:
                raise ValueError("Oversized or unterminated lifecycle line")
            reading = asyncio.create_task(asyncio.to_thread(self.poll, limit - len(self.buffer)))
            try:
                chunk = await asyncio.shield(reading)
            except asyncio.CancelledError:
                await reading  # Drain only the nonblocking kernel read before closing handles.
                raise
            if chunk is None:
                await asyncio.sleep(0.02)
            elif chunk:
                self.buffer.extend(chunk)
            else:
                if self.buffer:
                    raise ValueError("Truncated lifecycle line")
                return b""
