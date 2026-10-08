"""Windows read handles held without write/delete sharing until terminal commit.

No path-only fallback. Reparse points (including in-root links) are rejected.
"""

import ctypes
import hashlib
import os
import unicodedata
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from uaw.shared.contracts import JsonObject
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.workspace.ports import RootGrant

MAX_FILE_BYTES = 1024 * 1024
MAX_RETURN_BYTES = 64 * 1024
MAX_RETURN_CHARACTERS = 16384  # Published FileContent.text -> Text; A owns widening.


class FileId(ctypes.Structure):
    _fields_ = [("volume", ctypes.c_ulonglong), ("id", ctypes.c_ubyte * 16)]


class BasicInfo(ctypes.Structure):
    _fields_ = [
        ("created", ctypes.c_longlong),
        ("accessed", ctypes.c_longlong),
        ("written", ctypes.c_longlong),
        ("changed", ctypes.c_longlong),
        ("attributes", wintypes.DWORD),
    ]


class StandardInfo(ctypes.Structure):
    _fields_ = [
        ("allocated", ctypes.c_longlong),
        ("size", ctypes.c_longlong),
        ("links", wintypes.DWORD),
        ("deleted", wintypes.BOOLEAN),
        ("directory", wintypes.BOOLEAN),
    ]


@dataclass(frozen=True)
class HandleIdentity:
    path: str
    identity: tuple[int, int]
    size: int
    written: int
    changed: int
    attributes: int
    directory: bool
    links: int


def normal(path: str | Path) -> str:
    value = str(path)
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    return os.path.normcase(os.path.normpath(value))


class WindowsReadHandle:
    """All operations are synchronous; callers MUST run them in a worker thread."""

    def __init__(self, grant: RootGrant, relative_path: str) -> None:
        if os.name != "nt":
            raise CapabilityUnavailable("runner.windows_handle_read")
        self.api: Any = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        self.api.CreateFileW.restype = wintypes.HANDLE
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]
        self.api.GetFileInformationByHandleEx.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        self.api.GetFinalPathNameByHandleW.argtypes = [
            wintypes.HANDLE,
            wintypes.LPWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        self.api.GetFileType.argtypes = [wintypes.HANDLE]
        self.api.ReadFile.argtypes = [
            wintypes.HANDLE,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.c_void_p,
        ]
        self.handles: list[Any] = []
        self.paths: list[Path] = []
        self.initial: list[HandleIdentity] = []
        self.grant = grant
        try:
            parts = relative_path.replace("\\", "/").split("/")
            parts = [part for part in parts if part not in ("", ".")]
            if not parts:
                raise reject("file_not_regular", "A regular file is required")
            path = grant.native_path
            paths = [path]
            for part in parts:
                path = path / part
                paths.append(path)
            for index, path in enumerate(paths):
                directory = index != len(paths) - 1
                # READ_ATTRIBUTES for directories, GENERIC_READ for file. SHARE_READ only:
                # no existing/new writer or renamer is compatible while handles are held.
                access = 0x80 if directory else 0x80000000
                handle = self.api.CreateFileW(
                    str(path), access, 1, None, 3, 0x02000000 | 0x00200000, None
                )
                if handle == ctypes.c_void_p(-1).value:
                    raise reject(
                        "file_unavailable", "Read handle unavailable or sharing conflict", 409
                    )
                self.handles.append(handle)
                self.paths.append(path)
                info = self.info(handle)
                if (
                    normal(info.path) != normal(path)
                    or info.attributes & 0x400
                    or info.directory != directory
                    or self.api.GetFileType(handle) != 1
                    or (not directory and info.links != 1)
                ):
                    raise reject(
                        "file_identity_invalid",
                        "Link, special file or path identity rejected",
                        403,
                        "permission",
                    )
                self.initial.append(info)
            if self.initial[0].identity != grant.file_identity:
                raise reject(
                    "file_identity_invalid",
                    "Opened root differs from granted identity",
                    403,
                    "permission",
                )
            if self.initial[-1].size > MAX_FILE_BYTES:
                raise reject("file_too_large", "File exceeds 1 MiB read limit")
            self.check()
        except BaseException:
            self.close()
            raise

    def info(self, handle: Any) -> HandleIdentity:
        identity, basic, standard = FileId(), BasicInfo(), StandardInfo()
        for kind, value in [(18, identity), (0, basic), (1, standard)]:
            if not self.api.GetFileInformationByHandleEx(
                handle, kind, ctypes.byref(value), ctypes.sizeof(value)
            ):
                raise CapabilityUnavailable("runner.windows_handle_identity")
        buffer = ctypes.create_unicode_buffer(32768)
        length = self.api.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
        if not 0 < length < len(buffer):
            raise CapabilityUnavailable("runner.windows_final_path")
        return HandleIdentity(
            buffer.value,
            (identity.volume, int.from_bytes(identity.id, "little")),
            standard.size,
            basic.written,
            basic.changed,
            basic.attributes,
            bool(standard.directory),
            standard.links,
        )

    def check(self) -> None:
        if not self.handles:
            raise reject("file_identity_invalid", "Read handle is closed", 409)
        for index, (handle, path, initial) in enumerate(
            zip(self.handles, self.paths, self.initial, strict=True)
        ):
            info = self.info(handle)
            try:
                stat = path.stat(follow_symlinks=False)
                path_identity = (stat.st_dev, stat.st_ino)
            except OSError:
                raise reject("file_identity_invalid", "Opened path was replaced", 409) from None
            # Directory timestamps may change for unrelated children. Directory identity,
            # final path and attributes must remain fixed; file timestamps/size too.
            if (
                info.identity != initial.identity
                or path_identity != initial.identity
                or normal(info.path) != normal(path)
                or info.attributes != initial.attributes
                or info.directory != initial.directory
                or (index == len(self.handles) - 1 and info != initial)
            ):
                raise reject("file_identity_invalid", "Opened file/root changed", 409)

    def read(self, parameters: JsonObject) -> JsonObject:
        self.check()
        data = bytearray()
        while True:
            buffer = ctypes.create_string_buffer(MAX_RETURN_BYTES)
            actual = wintypes.DWORD()
            if not self.api.ReadFile(
                self.handles[-1], buffer, len(buffer), ctypes.byref(actual), None
            ):
                raise reject("file_read_failed", "OS read failed", 409)
            data.extend(buffer.raw[: actual.value])
            if len(data) > MAX_FILE_BYTES:
                raise reject("file_too_large", "File exceeds 1 MiB read limit")
            if actual.value == 0:
                break
        self.check()
        if len(data) != self.initial[-1].size:
            raise reject("file_identity_invalid", "File changed during read", 409)
        try:
            text = data.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            raise reject("file_not_text", "Only UTF-8 text is supported") from None
        if any(unicodedata.category(char) == "Cc" and char not in "\t\n\r" for char in text):
            raise reject("file_not_text", "Binary/control content is unsupported")
        location = parameters.get("location", {"kind": "whole"})
        assert isinstance(location, dict)
        if location == {"kind": "whole"}:
            selected = text
        elif (
            set(location) == {"kind", "start", "end"}
            and location["kind"] == "text_span"
            and isinstance(location["start"], int)
            and isinstance(location["end"], int)
            and 0 <= location["start"] <= location["end"] <= len(text)
        ):
            selected = text[location["start"] : location["end"]]
        else:
            raise reject("unsupported_location", "Only whole or bounded text_span is supported")
        # Never silently truncate whole or change the signed range; caller can use a span.
        if (
            len(selected) > MAX_RETURN_CHARACTERS
            or len(selected.encode("utf-8")) > MAX_RETURN_BYTES
        ):
            raise reject(
                "read_range_too_large",
                "Selected text exceeds 64 KiB or 16384-character contract limit",
            )
        result = {
            "workspace_ref": parameters["workspace_ref"],
            "path": parameters["path"],
            "encoding": "utf-8",
            "text": selected,
            "content_hash": hashlib.sha256(data).hexdigest(),
            "location": location,
        }
        validate_contract("FileContent", result)
        return result

    def close(self) -> None:
        for handle in reversed(self.handles):
            self.api.CloseHandle(handle)
        self.handles.clear()
