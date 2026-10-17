"""Read explicitly supplied offline files; never call a model or mutate a Runtime."""

import argparse
import json
import sys
from pathlib import Path

from uaw.evaluation.io import EvaluationInputError, publish_report
from uaw.evaluation.runner import evaluate_files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("suite", "manifest", "observations", "reviews", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise FileExistsError
        report = evaluate_files(args.suite, args.manifest, args.observations, args.reviews)
        publish_report(args.output, report.wire())
    except FileExistsError:
        print(json.dumps({"error": "output_exists"}), file=sys.stderr)
        return 2
    except EvaluationInputError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    except OSError:
        print(json.dumps({"error": "input_or_output_unavailable"}), file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "release_gate": report.release_gate.status,
                "candidate_attempts": report.candidate.attempt_count,
            },
            sort_keys=True,
        )
    )
    return {"passed": 0, "blocked": 1, "incomplete": 3}[report.release_gate.status]


if __name__ == "__main__":
    raise SystemExit(main())
