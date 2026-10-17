"""The pre-agreed offline JSON/CLI seam; no runtime, credentials, or model."""

import pytest

from uaw.evaluation.io import EvaluationInputError, parse_json


def test_offline_json_rejects_duplicate_keys_without_silently_choosing_a_value():
    with pytest.raises(EvaluationInputError, match="duplicate_key"):
        parse_json(b'{"case_id":"first","case_id":"replaced"}')


@pytest.mark.parametrize(
    "raw",
    [b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}', b'{"x":1e999}', b"\xff", b'"\\ud800"'],
)
def test_nonfinite_invalid_utf8_and_lone_surrogate_are_not_offline_data(raw):
    with pytest.raises(EvaluationInputError):
        parse_json(raw)


@pytest.mark.parametrize(
    "raw", [b"[" * 50 + b"0" + b"]" * 50, b"x" * (2**21 + 1)], ids=["over-depth", "over-2mib"]
)
def test_depth_and_size_are_bounded_before_domain_processing(raw):
    with pytest.raises(EvaluationInputError):
        parse_json(raw)
