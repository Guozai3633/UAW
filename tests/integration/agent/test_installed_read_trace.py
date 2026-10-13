"""Run the unchanged original successful first-read/recovery assertions with timing."""

import json
import time
from contextlib import asynccontextmanager
from contextvars import ContextVar

from tests.integration.runner import test_installed_file_chain
from tests.integration.runner.test_installed_file_chain import (
    test_a8_file_facade_approval_budget_actual_helper_read as original_first_chain,
)
from tests.integration.test_browser_sessions import web as web
from uaw.infrastructure import enrollment_launch
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch


async def test_original_first_read_and_recovery_with_source_trace(web, tmp_path, monkeypatch):
    original_prepare = PreparedEnrollmentLaunch.prepare
    zero = time.monotonic()
    rows = []
    window = ContextVar("a_parent_reply_window", default=None)
    last_window = None

    def wrap(port, method, label):
        operation = getattr(port, method)

        async def measured(*args, **kwargs):
            nonlocal last_window
            token = None
            if label == "parent.exchange":
                token = window.set(kwargs["deadline"])
                last_window = kwargs["deadline"]
            until = window.get() or (last_window if label == "parent.close" else None)
            if until is None:
                return await operation(*args, **kwargs)
            now = time.monotonic()
            row = {
                "operation": label,
                "shared_start_seconds": now - zero,
                "remaining_seconds": until - now,
                "deadline_since_zero": until - zero,
                "status": "running",
            }
            rows.append(row)
            try:
                result = await operation(*args, **kwargs)
            except BaseException as exc:
                row["status"] = getattr(getattr(exc, "failure", None), "code", type(exc).__name__)
                raise
            else:
                row["status"] = "ok"
                return result
            finally:
                row["seconds"] = time.monotonic() - now
                if token is not None:
                    window.reset(token)

        monkeypatch.setattr(port, method, measured)

    original_case = test_installed_file_chain.installed_file_case

    @asynccontextmanager
    async def traced_case(*args, **kwargs):
        async with original_case(*args, **kwargs) as p:
            pipe = p.bindings.bridge.pipe
            for port, method, label in (
                (pipe, "_exchange", "parent.exchange"),
                (pipe.registry, "authenticated_principal", "parent.actor"),
                (pipe.commands, "resolve", "parent.command_source"),
                (pipe.session, "check", "parent.session_check"),
                (pipe.session, "send", "parent.send"),
                (pipe.session, "receive", "parent.receive"),
                (pipe.session, "close", "parent.close"),
            ):
                wrap(port, method, label)
            try:
                yield p
            finally:
                # Exchange and diagnostic cleanup already finished; no trace IO
                # runs inside the original ten-second response scope.
                (tmp_path / "parent-trace.json").write_text(
                    json.dumps({"rows": rows}), encoding="utf-8"
                )

    monkeypatch.setattr(test_installed_file_chain, "installed_file_case", traced_case)

    async def traced_prepare(*args, **kwargs):
        environment = dict(kwargs["environment"])
        environment["UAW_A_READ_TRACE"] = str((tmp_path / "source-trace.json").resolve())
        environment["UAW_A_READ_CLOCK_ZERO"] = str(zero)
        # D's existing fixture calls this wrapper after selecting its normal
        # measured helper. Only this private launch substitutes the A observer.
        monkeypatch.setattr(
            enrollment_launch, "MODULE", "tests.integration.agent.installed_read_trace"
        )
        return await original_prepare(*args, **{**kwargs, "environment": environment})

    monkeypatch.setattr(PreparedEnrollmentLaunch, "prepare", traced_prepare)
    await original_first_chain(web, tmp_path, monkeypatch)
