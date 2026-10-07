"""Control-plane loop factory. Runner subprocesses use a separate process/loop."""

import asyncio
import selectors
import sys


def control_plane_loop() -> asyncio.AbstractEventLoop:
    if sys.platform == "win32":
        # Psycopg does not support ProactorEventLoop. Avoid deprecated global policies.
        return asyncio.SelectorEventLoop(selectors.SelectSelector())
    return asyncio.new_event_loop()
