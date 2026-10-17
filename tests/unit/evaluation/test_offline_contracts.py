"""Strict evaluation contracts are separate from public UAW DTOs."""

import pytest
from pydantic import ValidationError

from uaw.evaluation.contracts import Usage


def test_unknown_cost_can_never_become_confirmed_or_coerced_to_zero():
    with pytest.raises(ValidationError):
        Usage.model_validate_json(
            '{"input_tokens":0,"output_tokens":0,"model_calls":1,"tool_calls":0,"money":null,"currency":"USD","billing_state":"confirmed"}'
        )
