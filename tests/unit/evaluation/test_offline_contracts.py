"""Strict evaluation contracts are separate from public UAW DTOs."""

import pytest
from pydantic import ValidationError

from uaw.evaluation.contracts import Usage


def test_unknown_cost_can_never_become_confirmed_or_coerced_to_zero():
    with pytest.raises(ValidationError):
        Usage.model_validate_json(
            '{"input_tokens":0,"output_tokens":0,"model_calls":1,"tool_calls":0,"money":null,"currency":"USD","billing_state":"confirmed"}'
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"input_tokens": True},
        {"model_calls": 1.0},
        {"money": 0.01},
        {"money": "-0.01"},
        {"money": "NaN"},
        {"input_tokens": -1},
        {"currency": "usd"},
        {"approved": True},
    ],
)
def test_actual_usage_rejects_coercion_nonfinite_negative_and_extra_fields(changes):
    from uaw.evaluation.io import canonical

    usage = {
        "input_tokens": 0,
        "output_tokens": None,
        "model_calls": 1,
        "tool_calls": 0,
        "money": "0.01",
        "currency": "USD",
        "billing_state": "pending",
    }
    usage.update(changes)
    with pytest.raises(ValidationError):
        Usage.model_validate_json(canonical(usage))
