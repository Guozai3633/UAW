import argparse
import asyncio
import sys
from pathlib import Path

import uvicorn

from uaw.api.application import create_app
from uaw.composition import compose
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.shared.settings import ConfigurationError, Settings


def main() -> None:
    parser = argparse.ArgumentParser(prog="uaw")
    parser.add_argument("command", choices=["serve", "check-config"])
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    try:
        settings = Settings.from_file(args.config)
    except ConfigurationError as exc:
        print(f"uaw configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    if args.command == "check-config":
        print("Configuration valid; runtime capabilities are verified separately.")
        return
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(compose(settings)),
            host=settings.host,
            port=settings.port,
            proxy_headers=False,
        )
    )
    asyncio.run(server.serve(), loop_factory=control_plane_loop)


if __name__ == "__main__":
    main()
