"""Controlled Win32 display calls; never a human confirmation."""

from ctypes import wintypes as W
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from uaw_runner.native_dialog import WindowsNativeDialog


@pytest.mark.parametrize("foreground", [True, False])
def test_only_own_window_is_shown_and_foreground_denial_flashes(foreground):
    dialog = object.__new__(WindowsNativeDialog)
    dialog.k = SimpleNamespace(GetCurrentThreadId=Mock(return_value=17))
    dialog.desktop = Mock(return_value="Default")
    dialog.u = SimpleNamespace(
        GetWindowThreadProcessId=Mock(return_value=17),
        SetWindowPos=Mock(return_value=True),
        SetForegroundWindow=Mock(return_value=foreground),
        FlashWindowEx=Mock(return_value=False),
    )
    assert dialog.request_attention(123)
    dialog.u.SetWindowPos.assert_called_once()
    args = dialog.u.SetWindowPos.call_args.args
    assert args[0] == 123 and args[1].value == W.HWND(-1).value
    assert args[2:6] == (0, 0, 0, 0) and args[6] == 0x53
    dialog.u.SetForegroundWindow.assert_called_once_with(123)
    assert dialog.u.FlashWindowEx.call_count == (0 if foreground else 1)


@pytest.mark.parametrize("thread,displayed", [(18, True), (17, False)])
def test_foreign_or_unshowable_window_never_gets_focus(thread, displayed):
    dialog = object.__new__(WindowsNativeDialog)
    dialog.k = SimpleNamespace(GetCurrentThreadId=Mock(return_value=17))
    dialog.desktop = Mock(return_value="Default")
    dialog.u = SimpleNamespace(
        GetWindowThreadProcessId=Mock(return_value=thread),
        SetWindowPos=Mock(return_value=displayed),
        SetForegroundWindow=Mock(),
        FlashWindowEx=Mock(),
    )
    assert not dialog.request_attention(123)
    assert dialog.u.SetWindowPos.call_count == (0 if thread != 17 else 1)
    dialog.u.SetForegroundWindow.assert_not_called()
    dialog.u.FlashWindowEx.assert_not_called()
