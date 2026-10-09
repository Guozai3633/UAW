"""Local administrator credential enrollment with terminal-only hidden input."""

import argparse
import asyncio
import getpass
import json
import sys
import warnings
from pathlib import Path
from uuid import uuid4

from uaw.composition import compose
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.shared.contracts import Principal, RequestMeta
from uaw.shared.settings import ConfigurationError, Settings


async def enroll(args: argparse.Namespace) -> None:
    settings = Settings.from_file(args.config)
    if not settings.development_admin_token:
        raise ConfigurationError("Protected local administrator identity is required")
    if not sys.stdin.isatty():
        raise ConfigurationError("Use an interactive terminal; credential input must be hidden")
    control = compose(settings)
    try:
        await control.start()
        if control.configuration is None:
            raise ConfigurationError("Actual development database is required")
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            credential = getpass.getpass("Provider API key (hidden): ")
        if not credential.strip():
            raise ConfigurationError("Credential is empty")
        result = await control.configuration.put_secret(
            Principal(
                id=settings.development_principal_id + "-admin",
                kind="admin",
                auth_session_id="local-credential-enrollment",
            ),
            {"provider_id": args.provider_id, "secret": credential},
            RequestMeta(request_id=args.request_id, schema_version="0.1"),
        )
        print(json.dumps({"provider_id": args.provider_id, "receipt": result}, ensure_ascii=False))
    finally:
        await control.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("ops/database-development.toml"))
    parser.add_argument("--provider-id", default="deepseek-live")
    parser.add_argument("--request-id", default="credential-enrollment-" + uuid4().hex)
    args = parser.parse_args()
    try:
        asyncio.run(enroll(args), loop_factory=control_plane_loop)
    except Exception as exc:
        # Never print credential-bearing exception text or request data.
        print(
            f"Credential enrollment unavailable ({type(exc).__name__}); check local setup.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
