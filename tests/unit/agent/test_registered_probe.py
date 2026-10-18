"""Only protocol/isolation guards, with no model or human actions."""

import pytest

from ops.registered_report_probe import ProbeStop, scenario_inputs
from tests.unit.evaluation.factories import example_files
from uaw.evaluation.contracts import Case
from uaw.evaluation.io import digest
from uaw.evaluation.reader import record
from uaw.run.evaluation_capture import environment_hash


def test_report_scenario_preserves_exact_original_and_one_correction(tmp_path):
    case = example_files(tmp_path)["suite"]["cases"][0]
    case["prompt"] = "原文  与换行\n保留。\n\n用户追加要求\n只增加这个要求。"
    original, correction = scenario_inputs(record(Case, case))
    assert original == "原文  与换行\n保留。" and correction == "只增加这个要求。"


@pytest.mark.parametrize(
    "prompt", ["single input", "\n\n用户追加要求\n", "a\n\n用户追加要求\nb\n\n用户追加要求\nc"]
)
def test_scenario_does_not_guess_missing_or_multiple_corrections(tmp_path, prompt):
    case = example_files(tmp_path)["suite"]["cases"][0]
    case["prompt"] = prompt
    with pytest.raises(ProbeStop, match="exactly_one_explicit_correction_required"):
        scenario_inputs(record(Case, case))


def test_environment_hash_keeps_old_pins_and_binds_execution_scope():
    original = {
        "dependency_inventory_sha256": "1" * 64,
        "dependency_lock_sha256": "2" * 64,
        "settings_sha256": "3" * 64,
    }
    assert environment_hash(original) == digest(original)
    isolated = {**original, "evaluation_execution_scope": {"mode": "isolated"}}
    assert environment_hash(isolated) != environment_hash(original)
    assert environment_hash(isolated) != environment_hash(
        {**original, "evaluation_execution_scope": {"mode": "shared"}}
    )
    # Namespace locators do not silently redefine the declared comparison policy.
    assert environment_hash({**isolated, "database_name": "new-per-variant"}) == environment_hash(
        isolated
    )
