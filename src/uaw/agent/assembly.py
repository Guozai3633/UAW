"""Explicit internal assembly; no default API bindings or flags are changed."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from uaw.agent.adapters import AgentObservations, RegisteredAgentContexts, RegisteredAgentModels
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
from uaw.shared.settings import ConfigurationError
from uaw.tool.facade import ToolFacade
from uaw.tool.invocation.dispatch import ToolInvocation
from uaw.tool.registry import ToolRegistry
from uaw.tool.retrieval import ToolRetriever

if TYPE_CHECKING:
    from uaw.composition import Container, RegisteredContextBindings, TextToolBindings


@dataclass(frozen=True)
class AgentAssembly:
    runtime: AgentRuntime
    sources: RegisteredAgentSources
    repository: AgentRepository

    def engine(self, *, checkpointer: Any) -> LangGraphAgentEngine:
        return LangGraphAgentEngine(self.runtime, checkpointer=checkpointer)


def assemble_agent_runtime(
    container: Container,
    contexts: RegisteredContextBindings,
    tools: TextToolBindings,
    *,
    registry: ToolRegistry,
    completion: AgentCompletionPort | None = None,
    retriever: ToolRetriever | None = None,
) -> AgentAssembly:
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
        )
    )
    observations = AgentObservations(container.records, sources, results=tools.results)
    context_adapter = RegisteredAgentContexts(
        contexts.inputs,
        contexts.components,
        sources,
        observations,
        registry=registry,
        access=container.tool_access,
        retriever=retriever,
    )
    models = RegisteredAgentModels(model, original.policies, sources)
    access = AgentToolAccess(container.tool_access, repository, sources)
    existing = tools.invocation
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
    facade = ToolFacade(
        registry,
        invocation=invocation,
        lookup=tools.facade.lookup,
        reconciler=tools.facade.reconciler,
        retriever=retriever,
    )
    loop = AgentLoop(
        repository,
        context_adapter,
        models,
        observations,
        tools=facade,
        completion=completion,
        tool_access=access,
    )
    return AgentAssembly(AgentRuntime(AgentFactory(repository), loop), sources, repository)
