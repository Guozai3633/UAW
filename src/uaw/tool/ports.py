"""Internal MS-T1 ports. Implementations must come from trusted composition.

Snapshots resolve current and fixed policy/flags/role/environment and revocation;
never construct them from model input. A owns production adapters and storage wiring.
"""

from dataclasses import dataclass
from typing import Protocol

from uaw.shared.contracts import JsonObject, Ref, Scope, TrustedExecutionContext


@dataclass(frozen=True)
class ToolAccess:
    policy_ref: Ref
    scope: Scope
    role_categories: frozenset[str]
    allowed_capabilities: frozenset[str]
    denied_capabilities: frozenset[str]
    enabled_flags: frozenset[str]
    environment: str
    active_provider_refs: tuple[Ref, ...]
    cancelled: bool = False


class ToolAccessPort(Protocol):
    async def snapshot(self, ctx: TrustedExecutionContext) -> ToolAccess: ...


class PrecheckPort(Protocol):
    """Returns the existing ComponentToolInvocationPrecheckResult wire contract."""

    async def precheck(
        self, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> JsonObject: ...


class RecheckPort(Protocol):
    """Owns stored call/approval/resource binding; returns existing RecheckResult."""

    async def recheck(
        self, call: JsonObject, spec: JsonObject, precheck: JsonObject, ctx: TrustedExecutionContext
    ) -> JsonObject: ...
