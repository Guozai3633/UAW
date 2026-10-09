"""Real MS-C5 SQL/FS blob assembly. No fixture CompositionAuthority or RuleProvider."""

from __future__ import annotations

from pathlib import Path

from uaw.context.authority import RegisteredCompositionAuthority
from uaw.context.cache import PureComputationCache
from uaw.context.facade import ContextComponents
from uaw.context.model_input import GenericModelInputs
from uaw.context.readers import RegisteredContextReader, RegisteredRuleProvider
from uaw.context.registered import RegisteredContextInputs
from uaw.context.repository import ContextRepository
from uaw.infrastructure.blob.filesystem import FSBlobStore
from uaw.infrastructure.db.transactions import TransactionalStore
from uaw.model.context import FixedModelWindow
from uaw.model.policy import PolicyResolver
from uaw.run.context import RunContextSources
from uaw.shared.contracts import Principal


def assemble(
    records,
    configuration,
    directory: Path,
    controller: Principal,
    *,
    cache=None,
    tool_validator=None,
    assessor=None,
    current_runs=False,
    inputs_type=RegisteredContextInputs,
    record_batch=None,
    batch_required=False,
):
    runs = RunContextSources(records)
    if current_runs:
        from uaw.run.context_sources import RegisteredRunContextSources
        from uaw.run.execution_sources import RunExecutionSources
        from uaw.run.permissions import ExecutionPolicyResolver

        runs = RegisteredRunContextSources(
            RunExecutionSources(records, configuration, ExecutionPolicyResolver(records))
        )
    inputs = inputs_type(
        controller=controller,
        records=records,
        blobs=FSBlobStore(directory),
        transactions=TransactionalStore(records.database),
        runs=runs,
        tool_validator=tool_validator,
        record_batch=record_batch,
        batch_required=batch_required,
    )
    reader = RegisteredContextReader(inputs)
    components = ContextComponents(
        readers={"input": reader, "content": reader, "rule": reader, "configuration": reader},
        cancellation=runs,
        rules=RegisteredRuleProvider(inputs, assessor=assessor),
        models=FixedModelWindow(PolicyResolver(records, configuration)),
        repository=ContextRepository(records, TransactionalStore(records.database)),
        authority=RegisteredCompositionAuthority(inputs),
        cache=cache,
    )
    return inputs, components, GenericModelInputs(components.composer, cache=cache)


class ControlledGetBatch:
    """Test consumer using real sequential SQL get; NOT A's SQL batch adapter."""

    def __init__(self, records):
        self.records, self.calls = records, []

    async def read(self, principal, keys):
        self.calls.append((principal, keys))
        return tuple(
            [
                await self.records.get(
                    principal, key.namespace, key.resource_id, revision=key.revision
                )
                for key in keys
            ]
        )


def restart_assessor(payload):
    if not payload.get("controlled_assessor"):
        return None
    # Only this explicit test flag constructs controlled semantic advice.
    from tests.integration.context.test_assessment_postgres import ControlledAdvice

    return ControlledAdvice()


async def restart(payload):
    from uaw.context.contracts import digest, from_wire
    from uaw.infrastructure.credentials import WindowsCredentialStore
    from uaw.infrastructure.db.records import PostgresRecordStore
    from uaw.infrastructure.db.session import Database
    from uaw.shared.configuration import ConfigurationService
    from uaw.shared.contracts import TrustedExecutionContext

    database = Database(payload["database_url"])
    try:
        records = PostgresRecordStore(database)
        platform = from_wire(Principal, payload["platform"])
        configuration = ConfigurationService(records, WindowsCredentialStore(platform.id), platform)
        ctx = from_wire(TrustedExecutionContext, payload["context"])
        inputs, components, model = assemble(
            records,
            configuration,
            Path(payload["blob_directory"]),
            from_wire(Principal, payload["controller"]),
            cache=PureComputationCache(max_entries=128, max_bytes=2097152),
            current_runs=payload.get("current_runs", False),
            assessor=restart_assessor(payload),
            record_batch=ControlledGetBatch(records)
            if payload.get("controlled_record_batch")
            else None,
            batch_required=payload.get("controlled_record_batch", False),
        )
        if payload.get("register_material"):
            from uaw.shared.contracts import RequestMeta

            ref = await inputs.register_material(
                payload["register_material"],
                ctx,
                authenticated_service=inputs.controller,
                expected_revision=payload["expected_revision"],
                meta=RequestMeta(request_id=payload["request_id"], schema_version="0.1"),
            )
            return {"ref": ref.wire()}
        recipe = await inputs.recipe(ctx)
        result = await components.build(recipe.request.wire(), ctx)
        if result["kind"] != "ok":
            return {"failure": result["failure"]["code"]}
        prompt = await model.resolve(result["output_refs"][0], ctx)
        return {
            "messages_hash": digest(prompt.messages),
            "tools_hash": digest(prompt.tools),
            "estimated_tokens": prompt.estimated_tokens,
            "snapshot_ref": result["output_refs"][0],
        }
    finally:
        await database.close()


if __name__ == "__main__":
    import asyncio
    import json
    import sys

    from uaw.infrastructure.event_loop import control_plane_loop
    from uaw.shared.errors import DomainError

    try:
        with asyncio.Runner(loop_factory=control_plane_loop) as runner:
            result = runner.run(restart(json.loads(sys.stdin.buffer.read())))
    except DomainError as exc:
        print(json.dumps({"failure": exc.failure.code}))
        raise SystemExit(1) from None
    except Exception as exc:
        print(json.dumps({"failure": type(exc).__name__}))
        raise SystemExit(1) from None
    print(json.dumps(result))
