"""A test-only timing observer around the original disposable D assembly.

No source values, paths, identities, keys or file contents are recorded. Wrappers
forward the original arguments, return values, errors and cancellation unchanged.
The original native fixture restrictions, deadlines and cleanup still apply.
"""

import asyncio
import json
import os
import time
from contextvars import ContextVar
from pathlib import Path

from uaw_runner.handle_read import WindowsReadHandle
from uaw_runner.read_executor import ReadOnlyRunner

from tests.integration.runner.installed_file_child import assembly as original_assembly


class TracedAssembly:
    async def create(self, identity):
        application = await original_assembly.create(identity)
        helper = application.helper
        started = time.perf_counter()
        zero = float(os.environ.get("UAW_A_READ_CLOCK_ZERO", time.monotonic()))
        rows = []
        checkpoint = ContextVar("a_read_checkpoint", default="startup")
        sequence = 0

        def begin(label, deadline=None):
            now = time.perf_counter()
            row = {
                "operation": label,
                "checkpoint": checkpoint.get(),
                "start_seconds": now - started,
                "shared_start_seconds": time.monotonic() - zero,
                "deadline_since_zero": deadline - zero if deadline is not None else None,
                "remaining_seconds": (
                    deadline - asyncio.get_running_loop().time() if deadline is not None else None
                ),
                "status": "running",
            }
            if len(rows) < 2048:
                rows.append(row)
            return row, now

        def finish(row, before, error=None):
            row["seconds"] = time.perf_counter() - before
            row["status"] = "ok" if error is None else type(error).__name__
            if error is not None and getattr(error, "failure", None) is not None:
                row["status"] = error.failure.code

        def measure(port, method, label):
            original = getattr(port, method)

            async def measured(*args, **kwargs):
                row, before = begin(label, kwargs.get("deadline"))
                try:
                    result = await original(*args, **kwargs)
                except BaseException as exc:
                    finish(row, before, exc)
                    raise
                finish(row, before)
                return result

            setattr(port, method, measured)

        original_current = ReadOnlyRunner.current

        async def current(runner, *args, **kwargs):
            nonlocal sequence
            sequence += 1
            token = checkpoint.set("effect-" + str(sequence))
            row, before = begin("runner.current", kwargs.get("response_deadline"))
            try:
                result = await original_current(runner, *args, **kwargs)
            except BaseException as exc:
                finish(row, before, exc)
                raise
            else:
                finish(row, before)
                return result
            finally:
                checkpoint.reset(token)

        ReadOnlyRunner.current = current
        original_watch = helper.current_source.wait_changed

        async def watch(*args, **kwargs):
            token = checkpoint.set("watch")
            try:
                return await original_watch(*args, **kwargs)
            finally:
                checkpoint.reset(token)

        helper.current_source.wait_changed = watch
        for port, method, label in (
            (helper.current_source, "current", "source.current"),
            (helper.current_source.commands, "collect_registered", "source.collect"),
            (helper.current_source.commands, "_collect", "source.full_pass"),
            (helper.current_source.commands, "_request", "source.request"),
            (helper.current_source.commands, "_run", "source.run"),
            (helper.current_source.commands.devices, "current", "source.device"),
            (helper.current_source.commands.gate, "check_root", "source.gate_root"),
            (helper.current_source.commands.budgets, "execution_state", "source.budget"),
            (helper.current_source.commands.leases, "current", "source.lease"),
            (helper.current_source.commands.signer, "verify", "source.signature"),
            (helper.current_source.commands.store, "_witness_rows", "source.witness"),
            (helper.bootstrap.registration, "current_pair", "native.paired"),
            (helper.roots, "current", "native.root"),
            (helper.journal, "publish", "receipt.publish"),
        ):
            measure(port, method, label)

        sign = helper.bootstrap.signer.sign_document

        async def signed(*args, **kwargs):
            label = "receipt.sign" if kwargs.get("domain") == "receipt" else "native.sign"
            row, before = begin(label)
            try:
                result = await sign(*args, **kwargs)
            except BaseException as exc:
                finish(row, before, exc)
                raise
            finish(row, before)
            return result

        helper.bootstrap.signer.sign_document = signed

        def observe_sync(method, label):
            original = getattr(WindowsReadHandle, method)

            def observed(handle, *args, **kwargs):
                row, before = begin(label)
                try:
                    result = original(handle, *args, **kwargs)
                except BaseException as exc:
                    finish(row, before, exc)
                    raise
                finish(row, before)
                return result

            setattr(WindowsReadHandle, method, observed)

        observe_sync("__init__", "file.open")
        observe_sync("read", "file.read")
        serve = helper.serve_once

        async def traced_serve():
            try:
                return await serve()
            finally:
                # Save after the exchange; no trace I/O is added to a checkpoint.
                destination = Path(os.environ["UAW_A_READ_TRACE"])
                temporary = destination.with_suffix(".pending")

                def save():
                    temporary.write_text(json.dumps({"rows": rows}), encoding="utf-8")
                    temporary.replace(destination)

                await asyncio.to_thread(save)

        helper.serve_once = traced_serve
        return application


assembly = TracedAssembly()
