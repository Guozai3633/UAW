"""Per-Run file/office assembly from the admitted original installed source."""

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from uaw.agent.assembly import AgentAssembly, assemble_agent_runtime, bind_agent_tool_facade
from uaw.agent.completion.assembly import CompletionAssembly, assemble_completion_runtime
from uaw.agent.tool_access import AgentToolAccess
from uaw.infrastructure.db.context_batch import PostgresContextRecordBatch
from uaw.infrastructure.installed_files import InstalledFileBindings, assemble_installed_file
from uaw.run.approval_router import RoutedApprovals, ToolApprovalRoute
from uaw.run.file_context import FileContextMaterials
from uaw.run.tool_sources import RunToolAccessSources
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.tool.ledger import ToolLedger
from uaw.tool.providers.arithmetic import arithmetic_spec
from uaw.tool.providers.file_read import file_read_spec
from uaw.tool.providers.json_data import json_data_spec
from uaw.tool.providers.text import text_spec
from uaw.tool.registry import AdapterBinding, ToolRegistry
from uaw.tool.results import ToolResults
from uaw.tool.runtime_router import ToolRuntimeRoute

if TYPE_CHECKING:
    from uaw.composition import Container, RegisteredContextBindings


@dataclass(frozen=True)
class FileRunRuntime:
    agent: AgentAssembly
    contexts: RegisteredContextBindings
    completion: CompletionAssembly
    approvals: RoutedApprovals
    file: InstalledFileBindings


async def assemble_file_run(container: Container, ctx: TrustedExecutionContext) -> FileRunRuntime:
    from uaw.composition import assemble_office_tools, assemble_registered_context

    c = container
    if (
        not c.file_run_sources
        or not c.configuration
        or not c.records
        or not c.tool_access
        or not c.run_sources
    ):
        raise CapabilityUnavailable("file.admitted_runtime_sources")
    source_row = await c.records.get(ctx.principal, "run.file.sources", ctx.run_id or "")
    workspace = Ref.model_validate(source_row.payload["workspace_ref"])
    source = await c.file_run_sources.current(ctx, workspace)
    configuration = await c.configuration.snapshot(source["configuration_ref"])
    offices = [r for r in configuration["provider_refs"] if r["id"] == "builtin-office-v1"]
    if len(offices) != 1:
        raise CapabilityUnavailable("file.original_office_provider")
    office_pin = Ref.model_validate(offices[0])
    office_row = await c.records.get(c.configuration.platform, "providers", office_pin.id)
    if office_row.payload["state"] != "active" or str(office_row.revision) != office_pin.version:
        raise reject("file_office_provider_changed", "Original office provider differs", 412)
    file_pin = Ref.model_validate(source["provider_ref"])
    # Actual implementation support is scoped to this assembly. It is not an
    # enabled flag or a mutation of another Run's original access instance.
    access = RunToolAccessSources(
        c.records,
        c.configuration,
        c.run_sources,
        environment=c.tool_access.environment,
        implemented_flags=frozenset({"file_access"}),
    )
    scoped = replace(c, tool_access=access)
    registry = ToolRegistry()
    for spec in (
        text_spec(office_pin),
        arithmetic_spec(office_pin),
        json_data_spec(office_pin),
        file_read_spec(file_pin),
    ):
        pin = Ref.model_validate(spec["provider_ref"])
        registry.register(
            spec,
            expected_revision=registry.revision,
            binding=AdapterBinding(pin, frozenset({access.environment}), implemented=True),
        )
    office_refs = tuple(
        Ref.model_validate(registry.reference(e))
        for e in registry.snapshot()[1]
        if e.spec()["id"] != "file.read"
    )
    file_ref = Ref.model_validate(
        registry.reference(
            registry.get({"kind": "configuration", "id": "file.read", "version": "1"})
        )
    )
    office = assemble_office_tools(
        scoped,
        registry=registry,
        tool_refs=office_refs,
        provider=Principal(
            id="development-local-office", kind="service", auth_session_id="internal-local-adapter"
        ),
    )
    file = await assemble_installed_file(
        scoped,
        owner=ctx.principal,
        workspace=workspace,
        registry=registry,
        tool_ref=file_ref,
        provider=Principal(
            id="installed-readonly-file", kind="service", auth_session_id="internal-file-adapter"
        ),
        money_ceiling="0.05",
    )
    assert file.tool.facade.invocation and file.tool.facade.invocation.results
    file_results = file.tool.facade.invocation.results
    if not isinstance(file_results, ToolResults):
        raise CapabilityUnavailable("file.original_owning_results")
    materials = FileContextMaterials(c.records, c.configuration.platform, file.tool.materials)
    contexts = assemble_registered_context(
        scoped,
        registry=registry,
        record_batch=PostgresContextRecordBatch(c.records),
        batch_required=True,
        file_materials=materials,
    )

    def routes(agent_access: AgentToolAccess) -> tuple[ToolRuntimeRoute, ...]:
        office_facade = bind_agent_tool_facade(office.facade, registry, agent_access)
        file_facade = bind_agent_tool_facade(file.tool.facade, registry, agent_access)
        assert file.tool.facade.invocation and file.tool.facade.invocation.results
        return (
            *tuple(
                ToolRuntimeRoute(pin, office_pin, office_facade, office.results)
                for pin in office_refs
            ),
            ToolRuntimeRoute(file_ref, file_pin, file_facade, file_results),
        )

    agent = assemble_agent_runtime(
        scoped,
        contexts,
        office,
        registry=registry,
        max_output_tokens=c.settings.agent_max_output_tokens,
        tool_routes=routes,
        file_materials=materials,
    )
    completion = assemble_completion_runtime(
        scoped,
        agent,
        contexts=contexts,
        acceptance_required=c.settings.agent_acceptance_required,
    )
    approvals = RoutedApprovals(
        registry,
        ToolLedger(c.records),
        (
            *tuple(ToolApprovalRoute(pin, office_pin, office.approvals) for pin in office_refs),
            ToolApprovalRoute(file_ref, file_pin, file.tool.approvals),
        ),
    )
    if await c.file_run_sources.current(ctx, workspace) != source:
        raise reject(
            "file_runtime_source_changed", "Original admitted source changed during assembly", 412
        )
    return FileRunRuntime(agent, contexts, completion, approvals, file)
