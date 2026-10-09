"""Real Windows handle tests, exclusively pytest temporary roots."""

import hashlib
import os

import pytest
from uaw_runner.handle_read import MAX_FILE_BYTES, MAX_RETURN_BYTES, WindowsReadHandle

from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.workspace.ports import RootGrant


@pytest.fixture
def handle_case(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    stat = root.stat()
    workspace = Ref(kind="workspace", id="workspace1", version="1")
    grant = RootGrant(
        "u1", "d1", "root1", workspace, root, (stat.st_dev, stat.st_ino), frozenset(["read"])
    )
    return root, grant, {"workspace_ref": workspace.wire(), "path": "file.txt"}


@pytest.mark.parametrize("text", ["", "hello", "中文\n😀é\r\n", "\t\n\r"])
def test_actual_utf8_whole_and_hash(handle_case, text):
    root, grant, parameters = handle_case
    data = text.encode("utf-8")
    (root / "file.txt").write_bytes(data)
    handle = WindowsReadHandle(grant, "file.txt")
    try:
        result = handle.read(parameters)
        assert result["text"] == text
        assert result["content_hash"] == hashlib.sha256(data).hexdigest()
        assert result["location"] == {"kind": "whole"}
        assert str(root) not in str(result)
    finally:
        handle.close()


@pytest.mark.parametrize("start,end", [(0, 0), (0, 2), (1, 4), (4, 4)])
def test_unicode_character_span_exclusive_end(handle_case, start, end):
    root, grant, parameters = handle_case
    text = "中😀é"
    (root / "file.txt").write_text(text, encoding="utf-8")
    parameters["location"] = {"kind": "text_span", "start": start, "end": end}
    handle = WindowsReadHandle(grant, "file.txt")
    try:
        result = handle.read(parameters)
        assert result["text"] == text[start:end]
        assert result["content_hash"] == hashlib.sha256(text.encode()).hexdigest()
        assert result["location"] == parameters["location"]
    finally:
        handle.close()


@pytest.mark.parametrize("size", [MAX_RETURN_BYTES, MAX_FILE_BYTES])
def test_exact_total_and_return_limits_with_whole_file_digest(handle_case, size):
    root, grant, parameters = handle_case
    data = "😀".encode() * (size // 4)
    (root / "file.txt").write_bytes(data)
    parameters["location"] = {"kind": "text_span", "start": 0, "end": MAX_RETURN_BYTES // 4}
    handle = WindowsReadHandle(grant, "file.txt")
    try:
        result = handle.read(parameters)
        assert len(result["text"].encode()) == MAX_RETURN_BYTES
        assert result["content_hash"] == hashlib.sha256(data).hexdigest()
    finally:
        handle.close()


def test_over_total_limit_rejected(handle_case):
    root, grant, _ = handle_case
    (root / "file.txt").write_bytes(b"a" * (MAX_FILE_BYTES + 1))
    with pytest.raises(DomainError, match="1 MiB"):
        WindowsReadHandle(grant, "file.txt")


@pytest.mark.parametrize("data", [b"\xff", b"abc\x00def", b"\x01", b"\x7f"])
def test_binary_invalid_utf8_controls_rejected(handle_case, data):
    root, grant, parameters = handle_case
    (root / "file.txt").write_bytes(data)
    handle = WindowsReadHandle(grant, "file.txt")
    try:
        with pytest.raises(DomainError):
            handle.read(parameters)
    finally:
        handle.close()


@pytest.mark.parametrize(
    "location",
    [
        None,
        {"kind": "text_span", "start": 0, "end": 65537},
        {"kind": "text_span", "start": 0, "end": 999999},
        {"kind": "lines", "start": 1, "end": 2},
    ],
)
def test_return_limit_and_ranges_reject_without_truncation(handle_case, location):
    root, grant, parameters = handle_case
    (root / "file.txt").write_bytes(b"a" * (MAX_RETURN_BYTES + 1))
    if location is not None:
        parameters["location"] = location
    handle = WindowsReadHandle(grant, "file.txt")
    try:
        with pytest.raises(DomainError):
            handle.read(parameters)
    finally:
        handle.close()


def test_utf8_limit_is_bytes_not_characters(handle_case):
    root, grant, parameters = handle_case
    (root / "file.txt").write_text("😀" * 16385, encoding="utf-8")
    parameters["location"] = {"kind": "text_span", "start": 0, "end": 16385}
    handle = WindowsReadHandle(grant, "file.txt")
    try:
        with pytest.raises(DomainError, match="64 KiB"):
            handle.read(parameters)
    finally:
        handle.close()


def test_actual_handles_prevent_edit_file_rename_and_root_replacement(handle_case):
    root, grant, parameters = handle_case
    target = root / "file.txt"
    target.write_text("original", encoding="utf-8")
    handle = WindowsReadHandle(grant, "file.txt")
    try:
        for operation in [
            lambda: target.write_text("changed", encoding="utf-8"),
            lambda: target.rename(root / "replaced.txt"),
            lambda: root.rename(root.parent / "replaced-root"),
        ]:
            with pytest.raises(OSError):
                operation()
        assert handle.read(parameters)["text"] == "original"
    finally:
        handle.close()
    target.write_text("changed after close", encoding="utf-8")


def test_existing_writer_sharing_conflict_rejected(handle_case):
    root, grant, _ = handle_case
    target = root / "file.txt"
    with target.open("wb") as writer:
        writer.write(b"original")
        writer.flush()
        with pytest.raises(DomainError, match="sharing"):
            WindowsReadHandle(grant, "file.txt")


def test_hard_link_even_inside_root_rejected(handle_case):
    root, grant, _ = handle_case
    (root / "source.txt").write_text("original", encoding="utf-8")
    os.link(root / "source.txt", root / "file.txt")
    with pytest.raises(DomainError, match="Link"):
        WindowsReadHandle(grant, "file.txt")


def test_directory_and_root_identity_replaced_before_open_rejected(handle_case):
    root, grant, _ = handle_case
    (root / "file.txt").mkdir()
    with pytest.raises(DomainError):
        WindowsReadHandle(grant, "file.txt")
    root.rename(root.parent / "old-root")
    root.mkdir()
    (root / "file.txt").write_text("replacement", encoding="utf-8")
    with pytest.raises(DomainError, match="root"):
        WindowsReadHandle(grant, "file.txt")
