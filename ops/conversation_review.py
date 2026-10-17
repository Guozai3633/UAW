"""Prepare an offline review page or import explicit human/control submissions."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from uaw.evaluation.io import digest, parse_json, read_bounded
from uaw.evaluation.reader import record
from uaw.run.evaluation_review import (
    ReviewInputError,
    ReviewPacket,
    ReviewSubmission,
    import_review,
    prepare_review,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    consume = commands.add_parser("import")
    for command in (prepare, consume):
        command.add_argument("--source", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
    consume.add_argument("--packet", type=Path, required=True)
    consume.add_argument("--submission", type=Path, required=True)
    consume.add_argument(
        "--basis", choices=("human_evidence_review", "controlled_test"), required=True
    )
    consume.add_argument(
        "--ack-human-input",
        action="store_true",
        help="Operator confirms the supplied file contains actual independent human judgments.",
    )
    args = parser.parse_args()
    result: dict[str, object]
    try:
        if args.command == "prepare":
            packet = prepare_review(args.source, args.output, now=datetime.now(UTC))
            result = {"prepared": True, "targets": len(packet.targets), "human_reviews_created": 0}
        else:
            if args.basis == "human_evidence_review" and not args.ack_human_input:
                raise ReviewInputError("explicit_operator_acknowledgement_required")
            packet = record(ReviewPacket, parse_json(read_bounded(args.packet, limit=2**21)))
            submission = record(
                ReviewSubmission, parse_json(read_bounded(args.submission, limit=2**21))
            )
            count = import_review(
                args.source,
                packet,
                submission,
                args.output,
                now=datetime.now(UTC),
                basis=args.basis,
            )
            result = {
                "imported": True,
                "reviews": count,
                "basis": args.basis,
                "human_identity_authenticated": False,
                "packet_sha256": digest(packet.wire()),
            }
    except Exception as exc:
        # Do not echo model answers, operator notes, local paths or JSON input values.
        print(
            json.dumps(
                {
                    "error": "review_operation_rejected",
                    "code": str(exc)
                    if isinstance(exc, ReviewInputError)
                    else "input_or_io_invalid",
                    "error_type": type(exc).__name__,
                }
            )
        )
        return 2
    print(json.dumps({**result, "new_model_calls": 0, "runtime_writes": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
