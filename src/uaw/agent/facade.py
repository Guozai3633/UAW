"""Unified Agent entry. Unsupported definitions/delegation stay unavailable."""

from collections.abc import Awaitable, Callable

from uaw.agent.contracts import Payload
from uaw.agent.factory import AgentFactory
from uaw.agent.loop import AgentLoop
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, DomainError, error_result, reject
from uaw.shared.schema import ContractViolation, validate_contract


class AgentRuntime:
    def __init__(self, factory: AgentFactory, loop: AgentLoop) -> None:
        self.factory, self.loop = factory, loop

    async def _call(self, result_type: str, action: Callable[[], Awaitable[Payload]]) -> Payload:
        try:
            result = await action()
        except ContractViolation, ValueError, TypeError:
            result = error_result(reject("agent_request_invalid", "Invalid Agent request"))
        except DomainError as exc:
            result = error_result(exc)
        validate_contract(result_type, result)
        return result

    async def start(self, request: Payload, ctx: TrustedExecutionContext) -> Payload:
        return await self._call(
            "RuntimeAgentruntimeStartResult", lambda: self.factory.create(request, ctx)
        )

    async def step(self, request: Payload, ctx: TrustedExecutionContext) -> Payload:
        async def execute() -> Payload:
            try:
                return await self.loop.step(request, ctx)
            except DomainError as exc:
                if exc.failure.category == "cancelled":
                    await self.loop.repository.sync_cancellation(request["instance_ref"]["id"], ctx)
                raise

        return await self._call("RuntimeAgentruntimeStepResult", execute)

    async def define_agent(self, request: Payload, ctx: TrustedExecutionContext) -> Payload:
        return error_result(CapabilityUnavailable("agent.definitions"))

    async def delegate(self, request: Payload, ctx: TrustedExecutionContext) -> Payload:
        return error_result(CapabilityUnavailable("agent.delegation"))

    async def verify(self, request: Payload, ctx: TrustedExecutionContext) -> Payload:
        return error_result(CapabilityUnavailable("agent.completion_controller"))
