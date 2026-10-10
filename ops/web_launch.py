"""Exchange CLI user authority for a short-lived browser launch URL; print no master key."""

import argparse
from pathlib import Path
from uuid import uuid4

import httpx

from uaw.shared.schema import validate_contract
from uaw.shared.settings import Settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    settings = Settings.from_file(args.config)
    if not settings.browser_origin or not settings.development_user_token:
        raise SystemExit("Browser origin and user authentication must be configured first.")
    host = f"[{settings.host}]" if ":" in settings.host else settings.host
    with httpx.Client(trust_env=False, timeout=10, follow_redirects=False) as client:
        response = client.post(
            f"http://{host}:{settings.port}/v1/web/launch",
            headers={
                "Authorization": "Bearer " + settings.development_user_token.get_secret_value()
            },
            json={
                "meta": {"request_id": "web-launch-" + uuid4().hex, "schema_version": "0.1"},
                "payload": {},
            },
        )
    value = response.json()
    validate_contract("HttpWebLaunchResult", value)
    if response.status_code != 200 or value["kind"] != "ok":
        raise SystemExit(
            "Web launch unavailable: " + value.get("failure", {}).get("code", "unknown")
        )
    print(value["payload"]["launch_url"])
    print("One-use URL expires in two minutes; open it locally and do not share it.")


if __name__ == "__main__":
    main()
