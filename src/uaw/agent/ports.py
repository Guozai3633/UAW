"""Internal injection points. No adapter may manufacture current authorization."""

from dataclasses import dataclass
from typing import Protocol

from uaw.agent.contracts import Payload
from uaw.shared.contracts import Ref, TrustedExecutionContext


@dataclass(frozen=True)
class AgentView:
    run: Payload
    frame: Payload
    role_ref: Ref
    role: Payload
    remaining_budget: Payload


@dataclass(frozen=True)
class PreparedAgentContext:
    snapshot_ref: Ref
    epoch: int


class AgentSourcePort(Protocol):
    async def current(self, ctx: TrustedExecutionContext) -> AgentView: ...

    async def cancelled(self, ctx: TrustedExecutionContext) -> bool: ...


class AgentContextPort(Protocol):
    async def prepare(
        self, operation_id: str, observations: tuple[Ref, ...], ctx: TrustedExecutionContext
    ) -> PreparedAgentContext: ...


class AgentModelPort(Protocol):
    async def request(self, snapshot: Ref, ctx: TrustedExecutionContext) -> Payload: ...

    async def generate(self, request: Payload, ctx: TrustedExecutionContext) -> Payload: ...

    async def read(self, result: Payload, ctx: TrustedExecutionContext) -> Payload: ...


class AgentObservationPort(Protocol):
    async def save_tool(
        self, result: Payload, call: Payload, ctx: TrustedExecutionContext
    ) -> Ref: ...

    async def read(self, ref: Ref, ctx: TrustedExecutionContext) -> Payload: ...


class AgentCompletionPort(Protocol):
    async def propose(
        self, instance_ref: Ref, model_result: Payload, ctx: TrustedExecutionContext
    ) -> Ref:
        """Return an actual owned DeliveryProposal with current artifacts/report.

        It is not Run completion. Missing actual semantic/evidence sources deny.
        """
        ...


class AgentEnginePort(Protocol):
    async def run(
        self, instance_ref: Ref, ctx: TrustedExecutionContext, *, max_cycles: int
    ) -> Payload: ...
