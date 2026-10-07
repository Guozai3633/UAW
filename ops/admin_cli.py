"""Loopback admin client. Secret input uses getpass; tokens are never command arguments."""

import argparse
import getpass
import json
from pathlib import Path
from uuid import uuid4

import httpx

from uaw.shared.schema import parse_json
from uaw.shared.settings import Settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("ops/database-development.toml"))
    parser.add_argument("--method", choices=("GET", "POST", "DELETE"), default="POST")
    parser.add_argument("--path", required=True)
    parser.add_argument("--payload-file", type=Path)
    parser.add_argument("--provider-id")
    parser.add_argument("--request-id", default=f"admin-{uuid4().hex}")
    parser.add_argument("--expected-revision", type=int)
    args = parser.parse_args()
    settings = Settings.from_file(args.config)
    if not settings.development_admin_token:
        parser.error("Development administrator authentication is not configured")
    if not args.path.startswith("/v1/admin/") or "?" in args.path or "#" in args.path:
        parser.error("Only a development admin API path is permitted")
    payload = {}
    if args.path == "/v1/admin/secrets":
        if args.payload_file or not args.provider_id or args.method != "POST":
            parser.error("Secret writes require --provider-id and interactive input")
        payload = {"provider_id": args.provider_id, "secret": getpass.getpass("Provider credential: ")}
    elif args.payload_file:
        payload = parse_json(args.payload_file.read_bytes())
    meta = {"request_id": args.request_id, "schema_version": "0.1"}
    if args.expected_revision is not None:
        meta["expected_revision"] = args.expected_revision
    host = f"[{settings.host}]" if ":" in settings.host else settings.host
    with httpx.Client(timeout=30, trust_env=False, follow_redirects=False) as client:
        response = client.request(args.method, f"http://{host}:{settings.port}{args.path}",
            headers={"Authorization": f"Bearer {settings.development_admin_token.get_secret_value()}"},
            json={"meta": meta, "payload": payload} if args.method != "GET" else None)
    print(json.dumps({"request_id": args.request_id, "result": response.json()}, ensure_ascii=False, indent=2))
    if response.is_error:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
