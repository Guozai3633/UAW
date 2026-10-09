"""The sole assembly root; no domain creates framework/ORM singletons."""

from collections.abc import Callable
from dataclasses import dataclass

from uaw.context.authority import RegisteredCompositionAuthority
from uaw.context.cache import PureComputationCache
from uaw.context.facade import ContextComponents
from uaw.context.intent import IntentContexts, UnderstandingRules
from uaw.context.model_input import GenericModelInputs
from uaw.context.ports import RegisteredRuleAssessor
from uaw.context.readers import RegisteredContextReader, RegisteredRuleProvider
from uaw.context.registered import RegisteredContextInputs
from uaw.context.repository import ContextRepository
from uaw.context.seed import StoredModelInputs
from uaw.infrastructure.blob.filesystem import FSBlobStore
from uaw.infrastructure.credentials import WindowsCredentialStore
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.session import Database
from uaw.infrastructure.db.transactions import TransactionalStore
from uaw.intent.facade import IntentFacade
from uaw.intent.frame import FrameRepository
from uaw.intent.original import OriginalReader
from uaw.model.adapters import ChatCompletionsAdapter
from uaw.model.context import FixedModelWindow
from uaw.model.facade import ModelFacade
from uaw.model.gateway import ModelGateway
from uaw.model.input_router import ContextModelInputs
from uaw.model.policy import PolicyResolver
from uaw.run.approval import ApprovalService
from uaw.run.budget import BudgetService
from uaw.run.context import RunContextSources
from uaw.run.context_sources import RegisteredRunContextSources, RegisteredToolSetValidator
from uaw.run.events import EventReader
from uaw.run.execution_sources import RunExecutionSources
from uaw.run.facade import RunFacade
from uaw.run.inputs import RunInputReader
from uaw.run.leases import ExecutionLeaseService
from uaw.run.permissions import ExecutionPolicyResolver
from uaw.run.runner_authority import RegisteredRunnerAuthority
from uaw.run.runner_commands import RunnerCommands
from uaw.run.runner_devices import RunnerDevices
from uaw.run.runner_mapping import RegisteredRunnerPrincipalMapping
from uaw.run.runner_receipts import RegisteredReceiptCommandReader
from uaw.run.tool_sources import PureTextResourceReader, RunToolAccessSources, RunToolRecoveryAccess
from uaw.shared.configuration import ConfigurationService
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable
from uaw.shared.ports import (
    AgentPort,
    ContextPort,
    IntentPort,
    ModelPort,
    RunnerActionGatePort,
    RunnerChannelSourcePort,
    RunnerCommandSigningPort,
    RunnerRootSourcePort,
    RunPort,
    ToolPort,
    WorkspacePort,
)
from uaw.shared.settings import ConfigurationError, Settings
from uaw.tool.approval import ToolApprovalAdapter
from uaw.tool.authority import ToolApprovalAuthority
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.facade import ToolFacade
from uaw.tool.invocation.dispatch import ToolInvocation
from uaw.tool.ledger import ToolLedger
from uaw.tool.providers.text import TextInspectExecutor, TextInspectVerifier, text_estimates
from uaw.tool.receipt_store import ToolReceiptStore
from uaw.tool.reconciliation import ToolReconciler
from uaw.tool.registry import ToolRegistry
from uaw.tool.results import ToolResults
from uaw.tool.retrieval import ToolRetriever


@dataclass(frozen=True)
class RuntimeBindings:
    intent: IntentPort | None = None
    agent: AgentPort | None = None
    context: ContextPort | None = None
    tool: ToolPort | None = None
    workspace: WorkspacePort | None = None
    model: ModelPort | None = None
    run: RunPort | None = None

    def availability(self) -> dict[str, bool]:
        return {
            name: getattr(self, name) is not None
            for name in ("intent", "agent", "context", "tool", "workspace", "model", "run")
        }

    def require(self, name: str) -> object:
        if name not in self.availability():
            raise KeyError(name)
        binding: object | None = getattr(self, name)
        if binding is None:
            raise CapabilityUnavailable(name)
        return binding


@dataclass
class Container:
    settings: Settings
    bindings: RuntimeBindings
    database: Database | None = None
    records: PostgresRecordStore | None = None
    blobs: FSBlobStore | None = None
    configuration: ConfigurationService | None = None
    run_service: RunFacade | None = None
    budgets: BudgetService | None = None
    execution_leases: ExecutionLeaseService | None = None
    approvals: ApprovalService | None = None
    execution_permissions: ExecutionPolicyResolver | None = None
    run_sources: RunExecutionSources | None = None
    tool_access: RunToolAccessSources | None = None
    model_service: ModelFacade | None = None
    intent_service: IntentFacade | None = None
    context_components: ContextComponents | None = None
    runner_devices: RunnerDevices | None = None
    runner_commands: RunnerCommands | None = None
    runner_authority: RegisteredRunnerAuthority | None = None
    runner_receipt_commands: RegisteredReceiptCommandReader | None = None
    runner_principals: RegisteredRunnerPrincipalMapping | None = None
    started: bool = False

    async def start(self) -> None:
        if self.database:
            try:
                await self.database.check()
            except Exception:
                await self.database.close()
                raise ConfigurationError(
                    "Database is unavailable or migrations are missing; run the deployment check"
                ) from None
        self.started = True

    async def close(self) -> None:
        self.started = False
        if self.model_service:
            await self.model_service.close()
        if self.database:
            await self.database.close()


def compose_understanding_context(
    records: PostgresRecordStore,
    policies: PolicyResolver,
    *,
    cache: PureComputationCache | None = None,
) -> IntentContexts:
    """Real adapters shared by Intent and Model; general Context.build remains unbound."""
    sources = RunContextSources(records, policies.permissions)
    rules = UnderstandingRules(sources)
    components = ContextComponents(
        readers={"input": sources, "rule": rules},
        cancellation=sources,
        rules=rules,
        models=FixedModelWindow(policies),
        cache=cache,
    )
    return IntentContexts(records, RunInputReader(records), components)


def compose(settings: Settings, *, context_cache: PureComputationCache | None = None) -> Container:
    database = Database(settings.database_url.get_secret_value()) if settings.database_url else None
    records = PostgresRecordStore(database) if database else None
    configuration = (
        ConfigurationService(
            records,
            WindowsCredentialStore(settings.platform_id),
            Principal(id=settings.platform_id, kind="service", auth_session_id="control-plane"),
        )
        if records
        else None
    )
    run = (
        RunFacade(records, configuration, EventReader(records, settings.cursor_signing_key))
        if records and configuration
        else None
    )
    blobs = FSBlobStore(settings.blob_directory) if database else None
    budgets = BudgetService(records) if records else None
    permissions = ExecutionPolicyResolver(records) if records else None
    sources = (
        RunExecutionSources(records, configuration, permissions)
        if records and configuration and permissions
        else None
    )
    leases = ExecutionLeaseService(records) if records else None
    devices = RunnerDevices(records, configuration.platform) if records and configuration else None
    commands = (
        RunnerCommands(records, devices, configuration, permissions, budgets, leases)
        if records and devices and configuration and permissions and budgets and leases
        else None
    )
    policies = (
        PolicyResolver(records, configuration, permissions) if records and configuration else None
    )
    contexts = (
        compose_understanding_context(records, policies, cache=context_cache)
        if records and policies
        else None
    )
    model = (
        ModelFacade(
            ModelGateway(
                records,
                policies,
                ContextModelInputs(
                    records,
                    StoredModelInputs(records, blobs, contexts),
                    GenericModelInputs(contexts.components.composer, cache=context_cache),
                ),
                budgets,
                blobs,
                ChatCompletionsAdapter(),
            )
        )
        if records and policies and contexts and blobs and budgets
        else None
    )
    intent = (
        IntentFacade(
            OriginalReader(RunInputReader(records)),
            contexts,
            model,
            policies,
            FrameRepository(records),
        )
        if records and policies and contexts and model
        else None
    )
    return Container(
        settings=settings,
        bindings=RuntimeBindings(run=run, model=model, intent=intent),
        database=database,
        records=records,
        blobs=blobs,
        configuration=configuration,
        run_service=run,
        budgets=budgets,
        execution_leases=leases,
        approvals=ApprovalService(records, configuration, permissions=permissions)
        if records and configuration
        else None,
        execution_permissions=permissions,
        run_sources=sources,
        tool_access=RunToolAccessSources(
            records, configuration, sources, environment=settings.profile
        )
        if records and configuration and sources
        else None,
        model_service=model,
        intent_service=intent,
        context_components=contexts.components if contexts else None,
        runner_devices=devices,
        runner_commands=commands,
        runner_authority=RegisteredRunnerAuthority(commands) if commands else None,
        runner_receipt_commands=RegisteredReceiptCommandReader(commands) if commands else None,
        runner_principals=RegisteredRunnerPrincipalMapping(devices) if devices else None,
    )


@dataclass(frozen=True)
class RunnerControlBindings:
    devices: RunnerDevices
    principals: RegisteredRunnerPrincipalMapping
    commands: RunnerCommands
    authority: RegisteredRunnerAuthority
    receipt_commands: RegisteredReceiptCommandReader


@dataclass(frozen=True)
class RegisteredContextBindings:
    inputs: RegisteredContextInputs
    components: ContextComponents
    model_inputs: GenericModelInputs


def assemble_registered_context(
    container: Container,
    *,
    registry: ToolRegistry | None = None,
    cache: PureComputationCache | None = None,
    rule_assessor: RegisteredRuleAssessor | None = None,
) -> RegisteredContextBindings:
    records, config, blobs, sources = (
        container.records,
        container.configuration,
        container.blobs,
        container.run_sources,
    )
    if not records or not config or not blobs or not sources:
        raise ConfigurationError("Registered Context requires the configured control-plane sources")
    runs = RegisteredRunContextSources(sources)
    transactions = TransactionalStore(records.database)
    inputs = RegisteredContextInputs(
        controller=config.platform,
        records=records,
        blobs=blobs,
        transactions=transactions,
        runs=runs,
        tool_validator=RegisteredToolSetValidator(registry, container.tool_access),
    )
    reader = RegisteredContextReader(inputs)
    components = ContextComponents(
        readers={"input": reader, "content": reader, "rule": reader, "configuration": reader},
        cancellation=runs,
        rules=RegisteredRuleProvider(inputs, assessor=rule_assessor),
        models=FixedModelWindow(PolicyResolver(records, config, sources.permissions)),
        repository=ContextRepository(records, transactions),
        authority=RegisteredCompositionAuthority(inputs),
        cache=cache,
    )
    return RegisteredContextBindings(
        inputs, components, GenericModelInputs(components.composer, cache=cache)
    )


@dataclass(frozen=True)
class TextToolBindings:
    facade: ToolFacade
    invocation: ToolInvocation
    ledger: ToolLedger
    approvals: ApprovalService
    responses: ToolReceiptStore
    executor: TextInspectExecutor
    results: ToolResults


def assemble_text_tool(
    container: Container,
    *,
    registry: ToolRegistry,
    tool_ref: Ref,
    provider: Principal,
    currency: str = "USD",
    retriever: ToolRetriever | None = None,
) -> TextToolBindings:
    """Consume C's actual verifier, receipt source and original-attempt recovery.

    The caller registers the exact implemented adapter and role through trusted
    services. This assembly does not install a product catalogue or activate API.
    """
    records, config, blobs, access, budgets, policies = (
        container.records,
        container.configuration,
        container.blobs,
        container.tool_access,
        container.budgets,
        container.execution_permissions,
    )
    if not records or not config or not blobs or not access or not budgets or not policies:
        raise ConfigurationError("Text Tool requires the configured control-plane sources")
    spec = registry.get(tool_ref.wire()).spec()
    provider_ref = Ref.model_validate(spec["provider_ref"])
    ledger = ToolLedger(records)
    resources = PureTextResourceReader(registry, access, tool_ref)
    authority = ToolApprovalAuthority(
        ledger, registry, config, access, resources, policies=policies
    )
    service = ApprovalService(records, config, authority, permissions=policies)
    gates = ToolApprovalAdapter(ledger, authority, service)
    budget = ToolBudgetAdapter(ledger, budgets, gates, state=budgets)
    source = ToolReceiptStore(
        ledger,
        blobs,
        provider_ref=provider_ref,
        provider=provider,
        access=RunToolRecoveryAccess(
            resources, ledger, provider_ref=provider_ref, provider=provider
        ),
        verifier=TextInspectVerifier(provider_ref),
    )
    executor = TextInspectExecutor(source, provider=provider, currency=currency)
    reconciler = ToolReconciler(ledger, budget, receipts=source, evidence=source)
    results = ToolResults(source, reconciler)
    invocation = ToolInvocation(
        registry,
        ledger,
        budget,
        gates,
        access=access,
        executor=executor,
        estimates=text_estimates(currency),
        prepare=executor.check,
        results=results,
    )
    return TextToolBindings(
        ToolFacade(
            registry,
            access,
            invocation=invocation,
            lookup=source,
            reconciler=reconciler,
            retriever=retriever,
        ),
        invocation,
        ledger,
        service,
        source,
        executor,
        results,
    )


def assemble_runner_control(
    container: Container,
    *,
    channels: RunnerChannelSourcePort,
    root_factory: Callable[[RegisteredRunnerPrincipalMapping], RunnerRootSourcePort],
    gate: RunnerActionGatePort,
    signer: RunnerCommandSigningPort,
) -> RunnerControlBindings:
    """Explicit trusted adapters; construct roots with the actual device owner mapping.

    Returns internal bindings without publishing product routes or changing flags.
    Native confirmation and transport proof remain responsibilities of adapters.
    The default container never invents any of these missing dependencies.
    """
    records, config = container.records, container.configuration
    policies, budgets, leases = (
        container.execution_permissions,
        container.budgets,
        container.execution_leases,
    )
    if not records or not config or not policies or not budgets or not leases:
        raise ConfigurationError("Runner assembly requires the configured control-plane sources")
    devices = RunnerDevices(records, config.platform, channels)
    principals = RegisteredRunnerPrincipalMapping(devices)
    roots = root_factory(principals)
    commands = RunnerCommands(
        records,
        devices,
        config,
        policies,
        budgets,
        leases,
        roots=roots,
        gate=gate,
        signer=signer,
    )
    return RunnerControlBindings(
        devices,
        principals,
        commands,
        RegisteredRunnerAuthority(commands),
        RegisteredReceiptCommandReader(commands),
    )
