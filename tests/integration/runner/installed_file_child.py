"""D disposable installed assembly; controlled native input, actual A factory/OS/IPC.

Never a production module. No window is shown or clicked. Metadata metrics contain
no root path, proof, credential, body, principal identifier or key material.
"""

import asyncio
import json
import os
import time
from dataclasses import replace
from pathlib import Path

from uaw_runner.handle_read import WindowsReadHandle
from uaw_runner.ipc.read_endpoint import ReadOnlyPipeEndpoint
from uaw_runner.ipc.sessions import AuthenticatedPipeSession
from uaw_runner.native_dialog import NativeDirectoryDecision, WindowsNativeDialog
from uaw_runner.read_executor import ReadOnlyRunner

from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.installed_helper import NAMESPACE_ENV, InstalledHelperAssembly
from uaw.shared.errors import reject


def controlled_native(self, prompt, stopped, deadline):
    base = Path(os.environ["UAW_D_FIXTURE_BASE"]).resolve()
    root = Path(os.environ["UAW_D_FIXTURE_ROOT"]).resolve()
    if (
        os.environ.get("UAW_D_INSTALLED_FIXTURE") != "1"
        or not os.environ.get(NAMESPACE_ENV, "").startswith("web-platform-test-")
        or not root.is_relative_to(base)
        or root == base
        or stopped.is_set()
        or time.monotonic() >= deadline
    ):
        raise reject("d_fixture_denied", "Disposable D fixture required", 403)
    if prompt.select_root:
        identity = root.stat()
        return NativeDirectoryDecision(root, (identity.st_dev, identity.st_ino))
    return None


WindowsNativeDialog.show = controlled_native


class MeasuredInstalledAssembly:
    async def create(self, identity):
        destination = Path(os.environ["UAW_D_METRICS"])
        values = {"queries": {}, "phases": {}, "opens": 0, "frames": []}
        original_get = PostgresRecordStore.get

        def save():
            # Metadata is observational only. Publish whole JSON atomically so
            # parent diagnostics cannot see a truncated concurrent write.
            temporary = destination.with_name(destination.name + ".pending")
            temporary.write_text(json.dumps(values), encoding="utf-8")
            temporary.replace(destination)

        async def measured_get(records, *args, **kwargs):
            started = time.perf_counter()
            try:
                return await original_get(records, *args, **kwargs)
            finally:
                row = values["queries"].setdefault(args[1], {"calls": 0, "seconds": 0.0})
                row["calls"] += 1
                row["seconds"] += time.perf_counter() - started

        PostgresRecordStore.get = measured_get
        started = time.perf_counter()
        try:
            application = await InstalledHelperAssembly().create(identity)
        finally:
            values["phases"]["factory_create"] = time.perf_counter() - started
            await asyncio.to_thread(save)
        original_open = WindowsReadHandle.__init__

        def counted_open(self, *args, **kwargs):
            values["opens"] += 1
            save()
            return original_open(self, *args, **kwargs)

        WindowsReadHandle.__init__ = counted_open

        def measure(port, method, label):
            original = getattr(port, method)

            async def measured(*args, **kwargs):
                started = time.perf_counter()
                row = values["phases"].setdefault(label, {"calls": 0, "seconds": 0.0, "errors": {}})
                row["calls"] += 1
                try:
                    return await original(*args, **kwargs)
                except BaseException as exc:
                    failure = getattr(exc, "failure", None)
                    code = failure.code if failure is not None else type(exc).__name__
                    row["errors"][code] = row["errors"].get(code, 0) + 1
                    raise
                finally:
                    row["seconds"] += time.perf_counter() - started

            setattr(port, method, measured)

        measure(application.helper.protocol.async_authority, "current", "authority")
        measure(application.helper.bootstrap.signer, "sign_document", "signatures")
        measure(application.helper.journal, "publish", "receipt_publish")
        measure(application.helper.commands, "resolve", "registered_reader")
        measure(application.helper.protocol.principal_mapping, "owner", "owner_mapping")
        measure(application.helper.roots, "current", "root_source")
        measure(AuthenticatedPipeSession, "check", "session_current")
        measure(ReadOnlyPipeEndpoint, "dispatch", "endpoint_dispatch")
        measure(ReadOnlyPipeEndpoint, "watch", "endpoint_watch")
        measure(ReadOnlyRunner, "current", "runner_current")
        measure(ReadOnlyRunner, "execute", "runner_execute")
        original_connected = application.on_connected
        original_serve = application.helper.serve_once

        async def connected(helper):
            started = time.perf_counter()
            try:
                if original_connected is not None:
                    await original_connected(helper)
            finally:
                values["phases"]["callback"] = time.perf_counter() - started
                await asyncio.to_thread(save)

        async def serve():
            started = time.perf_counter()
            session = application.helper.session
            receive = session.receive

            async def counted_receive():
                frame = await receive()
                values["frames"].append(frame["kind"])
                return frame

            session.receive = counted_receive
            try:
                return await original_serve()
            finally:
                session.receive = receive
                values["phases"].setdefault("read_exchanges", []).append(
                    time.perf_counter() - started
                )
                await asyncio.to_thread(save)

        application.helper.serve_once = serve
        return replace(application, on_connected=connected)


assembly = MeasuredInstalledAssembly()
