"""Hidden owned child: real native HWND observation and CANCEL only."""

import asyncio
import ctypes
import json
import sys
import time
from ctypes import wintypes as W
from pathlib import Path
from threading import Event

from uaw_runner.native_dialog import NativePrompt, WindowsNativeDialog

from uaw.shared.errors import DomainError


async def main(report_path):
    stopped = Event()
    report = {"human_approval": "pending", "automatic": "cancel_only"}
    dialog = WindowsNativeDialog()
    visible = dialog.u.IsWindowVisible
    visible.argtypes, visible.restype = [W.HWND], W.BOOL
    style = dialog.u.GetWindowLongPtrW
    style.argtypes, style.restype = [W.HWND, ctypes.c_int], ctypes.c_ssize_t
    alive = dialog.u.IsWindow
    alive.argtypes, alive.restype = [W.HWND], W.BOOL
    original = dialog.request_attention
    window = None

    def observe(hwnd):
        nonlocal window
        window = hwnd
        shown = original(hwnd)
        report.update(
            displayed=shown,
            visible=bool(visible(hwnd)),
            topmost=bool(style(hwnd, -20) & 8),
            own_thread=dialog.u.GetWindowThreadProcessId(hwnd, None)
            == dialog.k.GetCurrentThreadId(),
        )
        stopped.set()  # Never sends OK/select/path messages.
        return shown

    dialog.request_attention = observe
    try:
        await asyncio.wait_for(
            asyncio.to_thread(
                dialog.show,
                NativePrompt(
                    "controlled-no-read", "test-device", "short-lived", "no-approval", True
                ),
                stopped,
                time.monotonic() + 5,
            ),
            8,
        )
        report["failure_code"] = "unexpected_approval"
    except DomainError as exc:
        report["failure_code"] = exc.failure.code
    report["window_closed"] = window is not None and not bool(alive(window))
    report_path.write_text(json.dumps(report), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1])))
