"""Diagnostic CPU profile of current metadata only; no dispatch, file read or UI."""

import asyncio
import cProfile
import json
import pstats

from tests.integration.runner.installed_file_fixture import installed_file_case
from tests.integration.test_browser_sessions import web as web


async def test_current_installed_metadata_cpu_profile(web, tmp_path, monkeypatch):
    async with installed_file_case(web, tmp_path, monkeypatch) as p:
        profile = cProfile.Profile()
        profile.enable()
        try:
            route = await p.bindings.route.current(p.workspace, p.ctx)
            assert route.workspace_ref == p.workspace
        finally:
            profile.disable()
            stats = pstats.Stats(profile)
            rows = [
                {
                    "function": str(key),
                    "calls": value[1],
                    "cpu_seconds": value[2],
                    "cumulative_seconds": value[3],
                }
                for key, value in stats.stats.items()
            ]
            rows.sort(key=lambda row: row["cpu_seconds"], reverse=True)
            destination = tmp_path / "metadata-cpu.json"
            await asyncio.to_thread(
                destination.write_text, json.dumps(rows[:60], indent=2), encoding="utf-8"
            )
        assert p.metrics["sends"] == [] and (await p.child_metrics())["opens"] == 0
