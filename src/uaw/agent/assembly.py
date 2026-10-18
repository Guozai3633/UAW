"""Explicit internal assembly; no default API bindings or flags are changed."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from uaw.agent.adapters import AgentObservations, RegisteredAgentContexts, RegisteredAgentModels
from uaw.agent.conversation_context import ConversationContexts
from uaw.agent.engines.langgraph import LangGraphAgentEngine
from uaw.agent.facade import AgentRuntime
from uaw.agent.factory import AgentFactory
from uaw.agent.loop import AgentLoop
from uaw.agent.ports import AgentCompletionPort
from uaw.agent.repository import AgentRepository
from uaw.agent.sources import RegisteredAgentSources
from uaw.agent.tool_access import AgentToolAccess
from uaw.model.facade import ModelFacade
from uaw.model.gateway import ModelGateway
from uaw.model.input_router import ContextModelInputs
from uaw.run.file_context import FileContextMaterials
from uaw.shared.contracts import Ref
from uaw.shared.settings import ConfigurationError
from uaw.tool.facade import ToolFacade
from uaw.tool.invocation.dispatch import ToolInvocation
from uaw.tool.ledger import ToolLedger
from uaw.tool.registry import ToolRegistry
from uaw.tool.retrieval import ToolRetriever
from uaw.tool.runtime_router import RoutedToolRuntime, ToolRuntimeRoute

if TYPE_CHECKING:
    from uaw.composition import (
        Container,
        OfficeToolBindings,
        RegisteredContextBindings,
        TextToolBindings,
    )


@dataclass(frozen=True)
class AgentAssembly:
    runtime: AgentRuntime
    sources: RegisteredAgentSources
    repository: AgentRepository

    def engine(self, *, checkpointer: Any) -> LangGraphAgentEngine:
        return LangGraphAgentEngine(self.runtime, checkpointer=checkpointer)


def bind_agent_tool_facade(
    original: ToolFacade,
    registry: ToolRegistry,
    access: AgentToolAccess,
    *,
    retriever: ToolRetriever | None = None,
) -> ToolFacade:
    """Clone dispatch with the actual Agent access; preserve original owning gates/readers."""
    existing = original.invocation
    if existing is None or original.registry is not registry or existing.registry is not registry:
        raise ConfigurationError("Original registered ToolInvocation required")
    invocation = ToolInvocation(
        registry,
        existing.ledger,
        existing.budgets,
        existing.approvals,
        access=access,
        executor=existing.executor,
        estimates=existing.estimates,
        results=existing.results,
        prepare=existing.prepare,
    )
    return ToolFacade(
        registry,
        invocation=invocation,
        lookup=original.lookup,
        reconciler=original.reconciler,
        retriever=retriever,
    )


def assemble_agent_runtime(
    container: Container,
    contexts: RegisteredContextBindings,
    tools: TextToolBindings | OfficeToolBindings,
    *,
    registry: ToolRegistry,
    completion: AgentCompletionPort | None = None,
    retriever: ToolRetriever | None = None,
    max_output_tokens: int = 512,
    instruction_refs: tuple[Ref, ...] = (),
    tool_routes: Callable[[AgentToolAccess], tuple[ToolRuntimeRoute, ...]] | None = None,
    file_materials: FileContextMaterials | None = None,
) -> AgentAssembly:
    if type(max_output_tokens) is not int or not 1 <= max_output_tokens <= 16384:
        raise ConfigurationError("Root output reserve must be between 1 and 16384 tokens")
    if (
        container.records is None
        or container.run_sources is None
        or container.tool_access is None
        or container.budgets is None
        or container.model_service is None
    ):
        raise ConfigurationError("Actual records/Run/role/budget/Model sources required for Agent")
    sources = RegisteredAgentSources(
        container.run_sources, container.tool_access, container.budgets
    )
    repository = AgentRepository(container.records, sources)
    original = container.model_service.gateway
    from uaw.run.streaming import ConversationStreams

    # A second routing facade shares the owned provider client; Container remains
    # its lifecycle owner. Existing understanding/default bindings are untouched.
    model = ModelFacade(
        ModelGateway(
            original.store,
            original.policies,
            ContextModelInputs(container.records, original.inputs, contexts.model_inputs),
            original.budgets,
            original.blobs,
            original.adapter,
            streams=ConversationStreams(container.records)
            if container.settings.agent_streaming_enabled
            else None,
        )
    )
    observations = AgentObservations(
        container.records, sources, results=tools.results, file_materials=file_materials
    )
    context_adapter = RegisteredAgentContexts(
        contexts.inputs,
        contexts.components,
        sources,
        observations,
        registry=registry,
        access=container.tool_access,
        retriever=retriever,
        output_reserve=max_output_tokens,
        instruction_refs=instruction_refs,
    )
    conversation_contexts = ConversationContexts(context_adapter)
    assert isinstance(model.gateway.inputs, ContextModelInputs)
    model.gateway.inputs.conversation = conversation_contexts
    models = RegisteredAgentModels(
        model, original.policies, sources, max_output_tokens=max_output_tokens
    )
    access = AgentToolAccess(container.tool_access, repository, sources)
    facade = bind_agent_tool_facade(tools.facade, registry, access, retriever=retriever)
    runtime_tools: ToolFacade | RoutedToolRuntime = facade
    if tool_routes is not None:
        # The factory is trusted composition code. It receives this exact Agent
        # access and returns independent original provider facades, not grants.
        runtime_tools = RoutedToolRuntime(
            registry,
            ToolLedger(container.records),
            tool_routes(access),
            access=access,
        )
        observations.results = runtime_tools
    loop = AgentLoop(
        repository,
        conversation_contexts,
        models,
        observations,
        tools=runtime_tools,
        completion=completion,
        tool_access=access,
    )
    return AgentAssembly(AgentRuntime(AgentFactory(repository), loop), sources, repository)
