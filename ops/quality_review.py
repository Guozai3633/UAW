"""Register a verified capture for the configured user, or export a submitted review."""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from uaw.composition import compose
from uaw.evaluation.io import parse_json, publish_report, read_bounded
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.session import Database
from uaw.run.quality import QualityReviews, parsed, write_files
from uaw.shared.contracts import Principal, RequestMeta
from uaw.shared.quality import QualityFiles, QualityOrigin
from uaw.shared.settings import Settings


async def execute(args: argparse.Namespace) -> dict[str, object]:
    settings = Settings.from_file(args.settings)
    if settings.development_admin_token is None:
        raise ValueError("configured_admin_required")
    container = compose(settings)
    source_database: Database | None = None
    try:
        if container.records is None:
            raise ValueError("configured_persistence_required")
        await container.records.database.check()
        service = QualityReviews(container.records)
        operator = Principal(
            id=settings.development_admin_id,
            kind="admin",
            auth_session_id="operator-"
            + hashlib.sha256(
                settings.development_admin_token.get_secret_value().encode()
            ).hexdigest()[:24],
        )
        owner = Principal(
            id=settings.development_principal_id,
            kind="user",
            auth_session_id=operator.auth_session_id,
        )
        if args.command == "register":
            origin = parsed(QualityOrigin, parse_json(read_bounded(args.origin, limit=16384)))
            source_records = None
            if args.source_settings is not None:
                source_settings = Settings.from_file(args.source_settings)
                if source_settings.database_url is None:
                    raise ValueError("configured_source_database_required")
                source_database = Database(source_settings.database_url.get_secret_value())
                await source_database.check()
                source_records = PostgresRecordStore(source_database)
            result = await service.register(
                operator,
                owner,
                args.source,
                origin,
                args.title,
                RequestMeta(request_id=args.request_id, schema_version="0.1", expected_revision=0),
                source_records=source_records,
            )
            return {
                "review_id": result["id"],
                "revision": result["revision"],
                "status": result["status"],
                "new_model_calls": 0,
                "human_reviews_created": 0,
            }
        exported = await service.export(owner, args.review_id)
        args.output.mkdir(parents=False, exist_ok=False)
        write_files(args.output, parsed(QualityFiles, exported["files"]))
        publish_report(
            args.output / "web-review-audit.json",
            {k: v for k, v in exported.items() if k != "files"},
        )
        return {"review_id": args.review_id, "exported": True, "new_model_calls": 0}
    finally:
        if source_database is not None:
            await source_database.close()
        await container.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--settings", required=True, type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    register = commands.add_parser("register")
    register.add_argument("--source", required=True, type=Path)
    register.add_argument("--origin", required=True, type=Path)
    register.add_argument("--title", required=True)
    register.add_argument("--request-id", required=True)
    register.add_argument(
        "--source-settings",
        type=Path,
        help="Optional trusted source DB config; no public upload or arbitrary source URL.",
    )
    export = commands.add_parser("export")
    export.add_argument("--review-id", required=True)
    export.add_argument("--output", required=True, type=Path)
    try:
        result = asyncio.run(execute(parser.parse_args()))
    except Exception as exc:
        # Never echo settings, answers, operator notes, secret handles or private paths.
        print(json.dumps({"error": "quality_operation_rejected", "error_type": type(exc).__name__}))
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
