"""Real offline subprocess and immutable output publication, not mocks."""

import json
import subprocess
import sys
from pathlib import Path

from tests.unit.evaluation.factories import example_files, write_files

SCRIPT = Path(__file__).resolve().parents[3] / "ops" / "evaluate_conversation.py"


def test_cli_reports_incomplete_and_will_never_overwrite_a_previous_report(tmp_path):
    files = write_files(tmp_path, example_files(tmp_path))
    report = tmp_path / "report.json"
    command = [sys.executable, str(SCRIPT)]
    for flag, path in zip(
        ("--suite", "--manifest", "--observations", "--reviews"), files, strict=True
    ):
        command.extend((flag, str(path)))
    command.extend(("--output", str(report)))
    first = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert first.returncode == 3, first.stdout + first.stderr
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["release_gate"]["status"] == "incomplete"
    original = report.read_bytes()
    second = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert second.returncode == 2
    assert report.read_bytes() == original
