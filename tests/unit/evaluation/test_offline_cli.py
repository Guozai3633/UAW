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


def test_two_real_cli_processes_have_one_complete_immutable_publication(tmp_path):
    files = write_files(tmp_path, example_files(tmp_path))
    output = tmp_path / "concurrent.json"
    command = [sys.executable, str(SCRIPT)]
    for flag, path in zip(
        ("--suite", "--manifest", "--observations", "--reviews"), files, strict=True
    ):
        command.extend((flag, str(path)))
    command.extend(("--output", str(output)))
    first = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    second = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    first.communicate(timeout=30)
    second.communicate(timeout=30)
    assert sorted([first.returncode, second.returncode]) == [2, 3]
    assert json.loads(output.read_text(encoding="utf-8"))["release_gate"]["status"] == "incomplete"
    assert not list(tmp_path.glob(".evaluation-*"))


def test_bad_offline_input_does_not_publish_a_partial_report_or_disclose_its_body(tmp_path):
    files = write_files(tmp_path, example_files(tmp_path))
    files[0].write_text('{"secret":"do-not-print","secret":"forged"}', encoding="utf-8")
    output = tmp_path / "never-created.json"
    command = [sys.executable, str(SCRIPT)]
    for flag, path in zip(
        ("--suite", "--manifest", "--observations", "--reviews"), files, strict=True
    ):
        command.extend((flag, str(path)))
    command.extend(("--output", str(output)))
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert result.returncode == 2 and "duplicate_key" in result.stderr
    assert "do-not-print" not in result.stdout + result.stderr
    assert not output.exists()
