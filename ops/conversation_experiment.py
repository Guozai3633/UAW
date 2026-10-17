"""Register fixed conditions before calls, or assemble explicit captured results."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from uaw.evaluation.io import digest, parse_json, read_bounded
from uaw.evaluation.reader import record
from uaw.run.evaluation_experiment import (
    ExperimentDraft,
    ExperimentInputError,
    ExperimentRegistration,
    assemble_experiment,
    register_experiment,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    register = commands.add_parser("register")
    register.add_argument("--draft", required=True, type=Path)
    assemble = commands.add_parser("assemble")
    assemble.add_argument("--registration", required=True, type=Path)
    assemble.add_argument("--capture", required=True, action="append", type=Path)
    for command in (register, assemble):
        command.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "register":
            draft = record(ExperimentDraft, parse_json(read_bounded(args.draft, limit=2**21)))
            registered = register_experiment(draft, args.output, now=datetime.now(UTC))
            print(
                json.dumps(
                    {
                        "registered": True,
                        "registered_at": registered.registered_at,
                        "registration_sha256": digest(registered.wire()),
                        "unreviewed_cases": sum(
                            c.review_status != "human_verified" for c in draft.suite.cases
                        ),
                        "new_model_calls": 0,
                        "release_gate_decided": False,
                    }
                )
            )
            return 0
        registration = record(
            ExperimentRegistration, parse_json(read_bounded(args.registration, limit=2**21))
        )
        report = assemble_experiment(
            registration, tuple(args.capture), args.output, now=datetime.now(UTC)
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": "experiment_operation_rejected",
                    "code": str(exc)
                    if isinstance(exc, ExperimentInputError)
                    else "input_or_io_invalid",
                    "error_type": type(exc).__name__,
                }
            )
        )
        return 2
    print(
        json.dumps(
            {
                "release_gate": report.release_gate.status,
                "comparison": report.comparison.status,
                "candidate_attempts": report.candidate.attempt_count,
                "baseline_attempts": report.baseline.attempt_count if report.baseline else 0,
                "new_model_calls": 0,
            }
        )
    )
    return {"passed": 0, "blocked": 1, "incomplete": 3}[report.release_gate.status]


if __name__ == "__main__":
    raise SystemExit(main())
