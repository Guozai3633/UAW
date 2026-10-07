"""Runtime injection boundaries. Wire types are validated at their owning facade."""

from typing import Protocol

from uaw.shared.contracts import JsonObject, RequestMeta, TrustedExecutionContext


class IntentPort(Protocol):
    async def understand(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject: ...


class AgentPort(Protocol):
    async def start(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject: ...


class ContextPort(Protocol):
    async def build(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject: ...


class ToolPort(Protocol):
    async def invoke(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject: ...


class WorkspacePort(Protocol):
    async def allocate(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject: ...


class ModelPort(Protocol):
    async def generate(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject: ...


class RunPort(Protocol):
    async def create(
        self, request: JsonObject, meta: RequestMeta, ctx: TrustedExecutionContext
    ) -> JsonObject: ...
