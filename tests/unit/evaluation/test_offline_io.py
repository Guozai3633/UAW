"""The pre-agreed offline JSON/CLI seam; no runtime, credentials, or model."""

import pytest

from uaw.evaluation.io import EvaluationInputError, parse_json


def test_offline_json_rejects_duplicate_keys_without_silently_choosing_a_value():
    with pytest.raises(EvaluationInputError, match="duplicate_key"):
        parse_json(b'{"case_id":"first","case_id":"replaced"}')
