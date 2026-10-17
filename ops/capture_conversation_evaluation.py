"""Capture one explicit terminal Run for offline quality review. Never execute it."""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from uaw.evaluation.contracts import Case, Policy
from uaw.evaluation.io import canonical, digest, parse_json, read_bounded
from uaw.infrastructure.db.session import Database
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.run.evaluation_capture import (
    instant,
    prepare_bundle,
    read_run,
    verify_runtime,
    write_bundle,
)
from uaw.shared.contracts import Principal
from uaw.shared.settings import Settings

REPOSITORY = Path(__file__).resolve().parents[1]


async def capture(args: argparse.Namespace) -> dict[str, object]:
    if args.output.exists():
        raise FileExistsError()
    settings = Settings.from_file(args.config)
    if settings.database_url is None:
        raise ValueError("database_unavailable")
    environment = parse_json(read_bounded(args.environment, limit=2**21))
    runtime = args.environment.parent / "runtime"
    attestation = verify_runtime(args.repository, runtime, environment["backend_source"])
    case = Case.model_validate_json(canonical(parse_json(read_bounded(args.case, limit=2**21))))
    policy = Policy.model_validate_json(
        canonical(parse_json(read_bounded(args.policy, limit=2**21)))
    )
    database = Database(settings.database_url.get_secret_value())
    actor = Principal(
        id=settings.development_principal_id,
        kind="user",
        auth_session_id="offline-evidence-capture",
    )
    try:
        await database.check()
        rows = await read_run(database, actor, args.run_id)
    finally:
        await database.close()
    run = next(r.payload for r in rows if r.namespace == "runs")
    if instant(run["created_at"]) < instant(environment["backend_switched_at"]):
        raise ValueError("run_predates_recorded_runtime_switch")
    prompt = runtime / "src/uaw/resources/prompts/conversation-v1.txt"
    bundle = prepare_bundle(
        rows,
        case,
        policy,
        candidate_id=args.candidate_id,
        source_commit=environment["backend_source"],
        environment_hash=digest(
            {
                k: environment[k]
                for k in (
                    "dependency_inventory_sha256",
                    "dependency_lock_sha256",
                    "settings_sha256",
                )
            }
        ),
        prompt_hash=hashlib.sha256(prompt.read_bytes()).hexdigest(),
        selected_attempt=args.answer_attempt_id,
    )
    bundle["audit"].update(
        runtime=attestation,
        policy_preregistered_by_exporter=False,
        scope_is_complete_product_experiment=False,
        schema_version="uaw.capture.v1",
        runtime_source_basis="operator_recorded_switch_and_exact_archive_bytes",
        immutable_Run_code_attestation_available=False,
        exporter_sources_sha256={
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in (
                ("cli", Path(__file__)),
                (
                    "adapter",
                    REPOSITORY / "src/uaw/run/evaluation_capture.py",
                ),
            )
        },
    )
    write_bundle(args.output, bundle)
    return {
        "captured": True,
        "attempts": len(bundle["observations"]),
        "human_reviews": 0,
        "new_model_calls": 0,
        "runtime_writes": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("config", "environment", "case", "policy", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    for name in ("run-id", "candidate-id"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--answer-attempt-id")
    parser.add_argument("--repository", type=Path, default=REPOSITORY)
    args = parser.parse_args()
    try:
        result = asyncio.run(capture(args), loop_factory=control_plane_loop)
    except Exception as exc:
        # Pydantic/SQL/provider values can contain private text; never echo them.
        print(json.dumps({"error": "capture_rejected", "error_type": type(exc).__name__}))
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
