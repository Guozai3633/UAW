"""Actual native windows auto-CANCEL only. Human affirmative acceptance stays pending."""

import asyncio
import json
import time
from datetime import UTC, datetime, timedelta
from threading import Event

import pytest
from uaw_runner.native_dialog import NativePrompt, WindowsNativeDialog

from uaw.shared.errors import DomainError


@pytest.mark.parametrize("select_root", [False, True])
async def test_actual_native_dialog_deadline_closes_without_approval(tmp_path, select_root):
    dialog = WindowsNativeDialog()
    desktop = await asyncio.to_thread(dialog.desktop)
    prompt = NativePrompt(
        "controlled-test-account",
        "random-test-device",
        (datetime.now(UTC) + timedelta(seconds=1)).isoformat(),
        "test challenge: no approval",
        select_root,
    )
    started = time.monotonic()
    with pytest.raises(DomainError) as exc:
        await asyncio.to_thread(dialog.show, prompt, Event(), started + 0.8)
    assert exc.value.failure.code == "native_timeout"
    report = dict(
        backend="Windows-native",
        desktop=desktop,
        operation="folder" if select_root else "confirmation",
        automatic="timeout_cancel_only",
        human_approval="pending",
        elapsed=time.monotonic() - started,
    )
    (tmp_path.parents[1] / ("native-ui-" + tmp_path.name + ".json")).write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )


async def test_actual_native_cancel_event_closes_window(tmp_path):
    dialog, stopped = WindowsNativeDialog(), Event()
    prompt = NativePrompt(
        "controlled-account", "test-device", "short-lived", "fixture challenge", True
    )
    work = asyncio.create_task(
        asyncio.to_thread(dialog.show, prompt, stopped, time.monotonic() + 3)
    )
    await asyncio.sleep(0.3)
    stopped.set()
    with pytest.raises(DomainError) as exc:
        await asyncio.wait_for(work, 2)
    assert exc.value.failure.code == "native_cancelled"
