"""Windows user-only folder selection and explicit read confirmation.

No path/approval input API. Cancel/timeout never means approval. Worker owns all UI.
"""

import ctypes
import os
import time
from ctypes import wintypes as W
from dataclasses import dataclass
from pathlib import Path
from threading import Event, Thread
from typing import Any

from uaw.shared.errors import CapabilityUnavailable, reject


@dataclass(frozen=True)
class NativeDirectoryDecision:
    path: Path
    identity: tuple[int, int]


@dataclass(frozen=True)
class NativePrompt:
    account: str
    device: str
    expires: str
    challenge: str
    select_root: bool

    def text(self) -> str:
        return (
            f"UAW 本机只读授权\n账号：{self.account}\n设备：{self.device}\n"
            f"范围：仅读取所选目录；不授权写入、安装或执行\n有效至：{self.expires}\n"
            f"挑战摘要：{self.challenge}\n请本人核对后选择；取消不会授权。"
        )


class WindowsNativeDialog:
    def __init__(self) -> None:
        if os.name != "nt":
            raise CapabilityUnavailable("runner.windows_native_dialog")
        self.u: Any = ctypes.WinDLL("user32", use_last_error=True)
        self.k: Any = ctypes.WinDLL("kernel32", use_last_error=True)
        self.s: Any = ctypes.WinDLL("shell32", use_last_error=True)
        self.o: Any = ctypes.WinDLL("ole32", use_last_error=True)
        self.browse_callback = ctypes.WINFUNCTYPE(ctypes.c_int, W.HWND, W.UINT, W.LPARAM, W.LPARAM)
        self.enum_callback = ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
        for dll, name, args, result in [
            (self.u, "OpenInputDesktop", [W.DWORD, W.BOOL, W.DWORD], W.HANDLE),
            (self.u, "CloseDesktop", [W.HANDLE], W.BOOL),
            (self.u, "GetThreadDesktop", [W.DWORD], W.HANDLE),
            (
                self.u,
                "GetUserObjectInformationW",
                [W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD, ctypes.c_void_p],
                W.BOOL,
            ),
            (self.u, "EnumThreadWindows", [W.DWORD, self.enum_callback, W.LPARAM], W.BOOL),
            (self.u, "PostMessageW", [W.HWND, W.UINT, W.WPARAM, W.LPARAM], W.BOOL),
            (self.u, "MessageBoxW", [W.HWND, W.LPCWSTR, W.LPCWSTR, W.UINT], ctypes.c_int),
            (self.k, "GetCurrentThreadId", [], W.DWORD),
            (self.s, "SHBrowseForFolderW", [ctypes.c_void_p], ctypes.c_void_p),
            (
                self.s,
                "SHGetPathFromIDListEx",
                [ctypes.c_void_p, W.LPWSTR, W.DWORD, W.DWORD],
                W.BOOL,
            ),
            (self.o, "CoInitializeEx", [ctypes.c_void_p, W.DWORD], ctypes.c_long),
            (self.o, "CoUninitialize", [], None),
            (self.o, "CoTaskMemFree", [ctypes.c_void_p], None),
        ]:
            fn = getattr(dll, name)
            fn.argtypes, fn.restype = args, result

    def desktop(self) -> str:
        desktop = self.u.OpenInputDesktop(0, False, 1)
        if not desktop:
            raise CapabilityUnavailable("runner.interactive_desktop")
        try:

            def name(handle: Any) -> str:
                value = ctypes.create_unicode_buffer(256)
                size = W.DWORD()
                if not self.u.GetUserObjectInformationW(
                    handle, 2, value, ctypes.sizeof(value), ctypes.byref(size)
                ):
                    raise CapabilityUnavailable("runner.interactive_desktop")
                return value.value

            actual = name(desktop)
            current = name(self.u.GetThreadDesktop(self.k.GetCurrentThreadId()))
            if actual.lower() != "default" or actual != current:
                raise CapabilityUnavailable("runner.interactive_desktop")
            return actual
        finally:
            self.u.CloseDesktop(desktop)

    def guard(self, stopped: Event, deadline: float) -> None:
        if stopped.is_set():
            raise reject("native_cancelled", "Native confirmation cancelled", 409, "cancelled")
        if time.monotonic() >= deadline:
            raise reject("native_timeout", "Native confirmation expired", 410, "timeout")
        self.desktop()

    def show(
        self, prompt: NativePrompt, stopped: Event, deadline: float
    ) -> NativeDirectoryDecision | None:
        self.guard(stopped, deadline)
        if self.o.CoInitializeEx(None, 2) < 0:
            raise CapabilityUnavailable("runner.native_dialog_com")
        done = Event()
        thread_id = self.k.GetCurrentThreadId()
        failed_desktop = Event()

        @self.enum_callback  # type: ignore[untyped-decorator]
        def close_window(hwnd: Any, _: int) -> bool:
            self.u.PostMessageW(hwnd, 0x10, 0, 0)  # WM_CLOSE, never an approval button
            return True

        def watch() -> None:
            while not done.wait(0.02):
                try:
                    self.desktop()
                except Exception:
                    failed_desktop.set()
                if stopped.is_set() or failed_desktop.is_set() or time.monotonic() >= deadline:
                    self.u.EnumThreadWindows(thread_id, close_window, 0)

        monitor = Thread(target=watch, name="UAW-native-cancel", daemon=True)
        monitor.start()
        try:
            selected = None
            selected_identity = None
            if prompt.select_root:

                class BrowseInfo(ctypes.Structure):
                    _fields_ = [
                        ("owner", W.HWND),
                        ("root", ctypes.c_void_p),
                        ("display", W.LPWSTR),
                        ("title", W.LPCWSTR),
                        ("flags", W.UINT),
                        ("callback", self.browse_callback),
                        ("data", W.LPARAM),
                        ("image", ctypes.c_int),
                    ]

                @self.browse_callback  # type: ignore[untyped-decorator]
                def callback(hwnd: Any, msg: int, data: int, _: int) -> int:
                    # The legacy tree has no edit box/new-folder/drag-drop UI.
                    # Selection alone is NOT approval; a separate default-Cancel dialog follows.
                    if stopped.is_set() or time.monotonic() >= deadline:
                        self.u.PostMessageW(hwnd, 0x10, 0, 0)
                    return 0

                display = ctypes.create_unicode_buffer(32768)
                info = BrowseInfo(
                    None,
                    None,
                    ctypes.cast(display, W.LPWSTR),
                    prompt.text(),
                    1 | 0x200 | 0x400,
                    callback,
                    0,
                    0,
                )
                pidl = self.s.SHBrowseForFolderW(ctypes.byref(info))
                try:
                    self.guard(stopped, deadline)
                    if not pidl:
                        raise reject(
                            "native_cancelled", "Folder selection cancelled", 409, "cancelled"
                        )
                    path = ctypes.create_unicode_buffer(32768)
                    if not self.s.SHGetPathFromIDListEx(pidl, path, len(path), 0):
                        raise reject("native_path_invalid", "Selected folder unavailable")
                    selected = Path(path.value)
                    if not selected.is_absolute() or str(selected).startswith("\\\\"):
                        raise reject(
                            "native_path_invalid", "Only a local absolute folder is supported"
                        )
                    before = selected.stat()
                    selected_identity = (before.st_dev, before.st_ino)
                finally:
                    if pidl:
                        self.o.CoTaskMemFree(pidl)
            self.guard(stopped, deadline)
            text = (
                prompt.text()
                + (f"\n本机目录：{selected}" if selected else "")
                + "\n\n确定：仅批准上述只读授权；取消：不批准。"
            )
            result = self.u.MessageBoxW(None, text, "UAW：请本人确认只读授权", 1 | 0x30 | 0x100)
            if failed_desktop.is_set():
                raise CapabilityUnavailable("runner.interactive_desktop")
            self.guard(stopped, deadline)
            if result != 1:
                raise reject("native_cancelled", "Read confirmation cancelled", 409, "cancelled")
            if selected is not None:
                after = selected.stat()
                if selected_identity != (after.st_dev, after.st_ino):
                    raise reject(
                        "permission_denied",
                        "Selected directory identity changed",
                        403,
                        "permission",
                    )
                assert selected_identity is not None
                return NativeDirectoryDecision(selected, selected_identity)
            return None
        finally:
            done.set()
            monitor.join(timeout=1)
            self.o.CoUninitialize()
