"""Internal startup timing/progress contract, never an authorization or wire grant."""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from uaw.shared.schema import validate_contract


@dataclass(frozen=True)
class FirstStartPolicy:
    expires_at: datetime
    challenge_hash: str
    wait_seconds: float = 90.0

    def __post_init__(self) -> None:
        if self.expires_at.tzinfo is None or self.expires_at.utcoffset() is None:
            raise ValueError("Original timezone-aware challenge expiry required")
        validate_contract("Hash", self.challenge_hash)
        if (
            type(self.wait_seconds) not in (int, float)
            or not math.isfinite(self.wait_seconds)
            or not 0 < self.wait_seconds <= 90
        ):
            raise ValueError("First start wait must be finite and in (0,90]")

    def remaining(self, now: datetime) -> float:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("Timezone-aware current clock required")
        return max(0.0, min(self.wait_seconds, (self.expires_at - now).total_seconds()))


class FirstStartProgressPort(Protocol):
    async def waiting(self, policy: FirstStartPolicy) -> None:
        """Original checked challenge is awaiting native decision; no permission granted.

        Child implementation emits bounded lifecycle metadata. Parent observer, if
        supplied, consumes only the strictly validated same challenge/expiry event.
        Neither role may reset the original monotonic start deadline.
        """
        ...
