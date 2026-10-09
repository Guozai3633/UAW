"""Explicit completion wiring; no default public API/feature-flag changes."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from uaw.agent.completion.delivery import CompletionCoordinator
from uaw.agent.completion.evidence import EvidenceRead
from uaw.agent.completion.semantic import SemanticVerifier
from uaw.context.readers import RegisteredRuleProvider
from uaw.model.evaluation_inputs import FixedModelEvaluator, FixedModelRuleAssessor
from uaw.run.completion import RunCompletionController
from uaw.shared.settings import ConfigurationError
from uaw.workspace.artifact_repository import ArtifactRepository
from uaw.workspace.artifacts import TextArtifacts

if TYPE_CHECKING:
    from uaw.agent.assembly import AgentAssembly
    from uaw.composition import Container, RegisteredContextBindings


@dataclass(frozen=True)
class CompletionAssembly:
    evaluator: FixedModelEvaluator
    rule_assessor: FixedModelRuleAssessor
    coordinator: CompletionCoordinator
    controller: RunCompletionController


def assemble_completion_runtime(
    container: Container,
    agent: AgentAssembly,
    *,
    read_evidence: EvidenceRead | None = None,
    acceptance_required: bool = False,
    max_output_tokens: int = 2048,
    contexts: RegisteredContextBindings | None = None,
) -> CompletionAssembly:
    if container.model_service is None or container.records is None or container.blobs is None:
        raise ConfigurationError("Actual Model/record/blob sources required for completion")
    evaluator = FixedModelEvaluator(
        container.model_service.gateway, agent.sources, max_output_tokens=max_output_tokens
    )
    artifacts = TextArtifacts(ArtifactRepository(container.records, container.blobs), agent.sources)
    coordinator = CompletionCoordinator(
        agent.repository,
        artifacts,
        SemanticVerifier(evaluator),
        read_evidence=read_evidence,
        observations=agent.runtime.loop.observations,
        acceptance_required=acceptance_required,
    )
    agent.runtime.loop.completion = coordinator
    assessor = FixedModelRuleAssessor(evaluator)
    if contexts is not None:
        provider = contexts.components.rules.provider
        if (
            not isinstance(provider, RegisteredRuleProvider)
            or provider.inputs is not contexts.inputs
        ):
            raise ConfigurationError("Actual registered rule provider required")
        provider.assessor = assessor
    return CompletionAssembly(
        evaluator,
        assessor,
        coordinator,
        RunCompletionController(coordinator),
    )
