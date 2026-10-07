"""The sole assembly root; no domain creates framework/ORM singletons."""

from dataclasses import dataclass

from uaw.context.facade import ContextComponents
from uaw.context.intent import IntentContexts, UnderstandingRules
from uaw.context.seed import StoredModelInputs
from uaw.infrastructure.blob.filesystem import FSBlobStore
from uaw.infrastructure.credentials import WindowsCredentialStore
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.session import Database
from uaw.intent.facade import IntentFacade
from uaw.intent.frame import FrameRepository
from uaw.intent.original import OriginalReader
from uaw.model.adapters import ChatCompletionsAdapter
from uaw.model.context import FixedModelWindow
from uaw.model.facade import ModelFacade
from uaw.model.gateway import ModelGateway
from uaw.model.policy import PolicyResolver
from uaw.run.approval import ApprovalService
from uaw.run.budget import BudgetService
from uaw.run.context import RunContextSources
from uaw.run.events import EventReader
from uaw.run.facade import RunFacade
from uaw.run.inputs import RunInputReader
from uaw.run.permissions import ExecutionPolicyResolver
from uaw.shared.configuration import ConfigurationService
from uaw.shared.contracts import Principal
from uaw.shared.errors import CapabilityUnavailable
from uaw.shared.ports import (
    AgentPort,
    ContextPort,
    IntentPort,
    ModelPort,
    RunPort,
    ToolPort,
    WorkspacePort,
)
from uaw.shared.settings import ConfigurationError, Settings


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
    approvals: ApprovalService | None = None
    execution_permissions: ExecutionPolicyResolver | None = None
    model_service: ModelFacade | None = None
    intent_service: IntentFacade | None = None
    context_components: ContextComponents | None = None
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
    records: PostgresRecordStore, policies: PolicyResolver
) -> IntentContexts:
    """Real adapters shared by Intent and Model; general Context.build remains unbound."""
    sources = RunContextSources(records, policies.permissions)
    rules = UnderstandingRules(sources)
    components = ContextComponents(
        readers={"input": sources, "rule": rules},
        cancellation=sources,
        rules=rules,
        models=FixedModelWindow(policies),
    )
    return IntentContexts(records, RunInputReader(records), components)


def compose(settings: Settings) -> Container:
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
    policies = (
        PolicyResolver(records, configuration, permissions) if records and configuration else None
    )
    contexts = compose_understanding_context(records, policies) if records and policies else None
    model = (
        ModelFacade(
            ModelGateway(
                records,
                policies,
                StoredModelInputs(records, blobs, contexts),
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
        approvals=ApprovalService(records, configuration, permissions=permissions)
        if records and configuration
        else None,
        execution_permissions=permissions,
        model_service=model,
        intent_service=intent,
        context_components=contexts.components if contexts else None,
    )
