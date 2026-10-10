"""Startup metadata cannot extend an original expiry or silently accept bad timing."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from uaw.shared.runner_bootstrap import FirstStartPolicy
from uaw.shared.schema import ContractViolation

NOW = datetime(2026, 10, 10, tzinfo=UTC)


@pytest.mark.parametrize(
    "changes",
    [
        {"wait_seconds": True},
        {"wait_seconds": 91},
        {"wait_seconds": float("nan")},
        {"expires_at": NOW.replace(tzinfo=None)},
        {"challenge_hash": "not-a-hash"},
    ],
)
def test_first_start_invalid_timing_or_challenge_rejected(changes):
    with pytest.raises((ValueError, ContractViolation)):
        FirstStartPolicy(
            **{
                "expires_at": NOW + timedelta(minutes=5),
                "challenge_hash": "a" * 64,
                **changes,
            }
        )


def test_first_start_wait_clips_to_original_expiry_and_is_never_extended():
    policy = FirstStartPolicy(expires_at=NOW + timedelta(seconds=60), challenge_hash="a" * 64)
    assert policy.remaining(NOW) == 60
    assert policy.remaining(NOW + timedelta(seconds=59)) == 1
    assert policy.remaining(NOW + timedelta(seconds=60)) == 0
    assert policy.remaining(NOW + timedelta(minutes=5)) == 0
    with pytest.raises(ValueError):
        policy.remaining(NOW.replace(tzinfo=None))


def test_first_start_policy_is_frozen_and_long_challenge_still_has_90_second_cap():
    policy = FirstStartPolicy(expires_at=NOW + timedelta(minutes=5), challenge_hash="a" * 64)
    assert policy.remaining(NOW) == 90
    with pytest.raises(FrozenInstanceError):
        policy.wait_seconds = 120
