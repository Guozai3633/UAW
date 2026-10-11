"""Disposable test tenant: first confirmation is controlled, root UI always rejects.

This tests pre-UI production composition only, never human consent or file access.
"""

import asyncio
import cProfile
import json
import os
import pstats
import time
from dataclasses import replace
from pathlib import Path

from uaw_runner.native_dialog import NativeDirectoryDecision, WindowsNativeDialog

from uaw.infrastructure.installed_helper import NAMESPACE_ENV, InstalledHelperAssembly
from uaw.shared.errors import reject


def controlled_dialog(self, prompt, stopped, deadline):
    if os.environ.get("UAW_TEST_INSTALLED_DIAGNOSTIC") != "1" or not os.environ.get(
        NAMESPACE_ENV, ""
    ).startswith("web-platform-"):
        raise reject("diagnostic_fixture_denied", "Disposable test tenant required", 403)
    if prompt.select_root:
        selected = os.environ.get("UAW_TEST_INSTALLED_SELECTED_ROOT")
        if selected:
            path = Path(selected)
            identity = path.stat()
            return NativeDirectoryDecision(path, (identity.st_dev, identity.st_ino))
        raise reject("diagnostic_reached_native", "Controlled root UI rejects", 409)
    return None


WindowsNativeDialog.show = controlled_dialog


class MeasuredDiagnosticAssembly:
    async def create(self, identity):
        application = await InstalledHelperAssembly().create(identity)
        destination = os.environ.get("UAW_TEST_INSTALLED_PROFILE")
        if destination is None:
            return application
        original = application.on_connected

        async def measured(helper):
            started = time.perf_counter()
            profile = cProfile.Profile()
            records = helper.container.records
            read = records.get
            reads = {}

            async def measured_read(*args, **kwargs):
                namespace = args[1]
                before = time.perf_counter()
                try:
                    return await read(*args, **kwargs)
                finally:
                    metric = reads.setdefault(namespace, {"calls": 0, "elapsed_seconds": 0.0})
                    metric["calls"] += 1
                    metric["elapsed_seconds"] += time.perf_counter() - before

            records.get = measured_read
            cpu_profile = os.environ.get("UAW_TEST_INSTALLED_CPU_PROFILE") == "1"
            if cpu_profile:
                profile.enable()
            try:
                await original(helper)
            finally:
                if cpu_profile:
                    profile.disable()
                records.get = read
                stats = pstats.Stats(profile) if cpu_profile else None
                # Only function names, counts and aggregate CPU times: no source values.
                rows = (
                    sorted(stats.stats.items(), key=lambda item: item[1][3], reverse=True)
                    if stats is not None
                    else []
                )
                output = {
                    "elapsed_seconds": time.perf_counter() - started,
                    "cpu_profile_enabled": cpu_profile,
                    "record_reads_by_namespace": reads,
                    "functions": [
                        {
                            "file": Path(key[0]).name,
                            "function": key[2],
                            "calls": value[1],
                            "cpu_seconds": value[2],
                            "cumulative_seconds": value[3],
                        }
                        for key, value in rows[:40]
                    ],
                }
                await asyncio.to_thread(
                    Path(destination).write_text, json.dumps(output), encoding="utf-8"
                )

        return replace(application, on_connected=measured)


assembly = MeasuredDiagnosticAssembly()
