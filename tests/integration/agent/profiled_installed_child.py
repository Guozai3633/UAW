"""A disposable source-cost profiler; original D fixture and execution unchanged."""

import asyncio
import cProfile
import json
import os
import pstats
from dataclasses import replace
from pathlib import Path

from tests.integration.runner.installed_file_child import assembly as original


class ProfiledAssembly:
    async def create(self, identity):
        application = await original.create(identity)
        serve = application.helper.serve_once

        async def profiled():
            profile = cProfile.Profile()
            profile.enable()
            try:
                return await serve()
            finally:
                profile.disable()
                stats = pstats.Stats(profile)
                selected = []
                for (filename, line, name), (
                    primitive,
                    calls,
                    total,
                    cumulative,
                    _,
                ) in stats.stats.items():
                    normalized = filename.replace("\\", "/")
                    if any(
                        part in normalized
                        for part in ("/uaw/", "/uaw_runner/", "/jsonschema/", "/referencing/")
                    ):
                        selected.append(
                            {
                                "module": normalized.rsplit("/", 1)[-1],
                                "line": line,
                                "function": name,
                                "calls": calls,
                                "primitive_calls": primitive,
                                "self_seconds": total,
                                "cumulative_seconds": cumulative,
                            }
                        )
                selected.sort(key=lambda v: v["self_seconds"], reverse=True)
                target = Path(os.environ["UAW_D_METRICS"]).with_name("a17-source-profile.json")
                await asyncio.to_thread(
                    target.write_text,
                    json.dumps(
                        {
                            "scope": (
                                "whole child serve loop incl concurrent monitors; "
                                "profiler overhead; not per-task cost"
                            ),
                            "selected_self_seconds": sum(v["self_seconds"] for v in selected),
                            "top": selected[:40],
                        }
                    ),
                    encoding="utf-8",
                )

        application.helper.serve_once = profiled
        return replace(application)


assembly = ProfiledAssembly()
