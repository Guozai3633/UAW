"""Ports require current authorization and cooperative cancellation from adapters."""

from typing import Protocol

from uaw.context.contracts import (
    CompositionBinding,
    ModelToolSet,
    ModelWindow,
    Reading,
    RecordReadKey,
    RuleCandidate,
    RulePlan,
    RulesRequest,
)
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.shared.stores import Record


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


class CompositionAuthority(Protocol):
    async def resolve(self, purpose: str, ctx: TrustedExecutionContext) -> CompositionBinding:
        """Provide actual purpose-specific rules, capability read pin and epoch.

        Preserve all admitted original input/critical requirements/pending actions.
        No default understanding instruction, invented capability ref or flags.
        """
        ...

    async def verify(self, binding: CompositionBinding, ctx: TrustedExecutionContext) -> None:
        """Recheck current owner revisions, ACL, revocation, flags and epoch.

        Called before/inside commit and on replay/read. External source changes
        are not made atomic by SQL; adapters must supply real revision checks.
        """
        ...


class RegisteredRunSource(Reader, Cancellation, Protocol):
    async def authorize(self, ctx: TrustedExecutionContext) -> None:
        """Actual admitted Run/current policy source, e.g. RunContextSources."""
        ...


class RegisteredToolValidator(Protocol):
    async def check(self, tools: ModelToolSet, ctx: TrustedExecutionContext) -> None:
        """Check every exact ToolSpec/version against current trusted discovery.

        Also check current role, permissions/flags and source revocation. The set
        itself and a controller registration never grant Tool execution authority.
        """
        ...


class RegisteredRuleAssessor(Protocol):
    async def assess(
        self, candidates: tuple[RuleCandidate, ...], ctx: TrustedExecutionContext
    ) -> RulePlan:
        """Semantic advice using A's actual fixed Model adapter; never authorization.

        Preserve every candidate's exact rule, Ref, level, scope, order and targets.
        Only topic/value/critical/supersedes/conflict_refs describe semantics. The
        Context boundary copies inputs, validates output and rechecks live sources.
        Controlled assessors demonstrate protocol behavior, not LLM quality.
        """
        ...


class ContextRecordBatchPort(Protocol):
    async def read(
        self, principal: Principal, keys: tuple[RecordReadKey, ...]
    ) -> tuple[Record, ...]:
        """At most 128 keys, ordered including duplicates, complete or raise.

        Every row belongs to this complete Principal. Missing/deleted/foreign rows
        fail the whole call; pinned revisions must match. No partial success. An
        adapter's database view is not atomic with external ACLs, tools or blobs;
        Context performs fresh authority and source checks around its own waits.
        """
        ...
