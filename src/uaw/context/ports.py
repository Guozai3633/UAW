"""Ports require current authorization and cooperative cancellation from adapters."""

from typing import Protocol

from uaw.context.contracts import ModelWindow, Reading, RulePlan, RulesRequest
from uaw.shared.contracts import Ref, TrustedExecutionContext


class Reader(Protocol):
    async def check(self, ref: Ref, ctx: TrustedExecutionContext) -> None:
        """Recheck current ACL, deletion/revocation and exact-version accessibility.

        Raise DomainError for denied/missing/disconnected/stale. A supplied Ref,
        its access_scope, or the reader registration never grants authorization.
        """
        ...

    async def read(self, ref: Ref, revision_policy: str, ctx: TrustedExecutionContext) -> Reading:
        """Read the actual pinned/latest version and location under current scope.

        Honor ctx.deadline and Run cancellation during I/O; propagate task cancel.
        The component checks before/after awaits; it cannot stop foreign blocking I/O.
        """
        ...


class RuleProvider(Protocol):
    async def discover(self, request: RulesRequest, ctx: TrustedExecutionContext) -> RulePlan:
        """Only registered origins; validate path ancestry, activation and overrides.

        Natural-language conflict assessment uses the inherited model if needed.
        Without that assessment return assessment_complete=False, never fake it.
        """
        ...


class ModelWindowProvider(Protocol):
    async def resolve(self, policy_ref: Ref, ctx: TrustedExecutionContext) -> ModelWindow:
        """Resolve the exact fixed user policy; no fallback model or guessed window."""
        ...


class Cancellation(Protocol):
    async def is_cancelled(self, ctx: TrustedExecutionContext) -> bool:
        """Read the Run-owned cancellation state, including preview operations."""
        ...


class TokenCounter(Protocol):
    name: str

    def count(self, reading: Reading) -> int:
        """Conservative serialized-block estimate for this fixed model."""
        ...
