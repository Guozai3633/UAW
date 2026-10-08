"""SQL-backed MS-C3 fixture sources; not production Tool discovery or an authority service."""

from __future__ import annotations

import asyncio
import json

from uaw.context.contracts import (
    CompositionBinding,
    InstructionRule,
    Reading,
    RuleCandidate,
    RulePlan,
    RulesRequest,
    from_wire,
)
from uaw.context.facade import ContextComponents
from uaw.context.model_input import GenericModelInputs, serialize
from uaw.context.repository import ContextRepository
from uaw.infrastructure.credentials import WindowsCredentialStore
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.session import Database
from uaw.infrastructure.db.transactions import TransactionalStore
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.model.context import FixedModelWindow
from uaw.model.policy import PolicyResolver
from uaw.run.context import RunContextSources
from uaw.shared.configuration import ConfigurationService
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.shared.errors import DomainError, reject

RULES = "context.test.c3.rules"
TOOLS = "context.test.c3.tools"
MATERIALS = "context.test.c3.materials"
EPOCHS = "context.test.c3.requests"


class SQLSources:
    """Reads actual SQL fixture rows and real Run permission/cancellation state."""

    def __init__(self, records, authority):
        self.records, self.authority = records, authority

    async def current(self, kind, ctx):
        namespace = {"rule": RULES, "configuration": TOOLS, "content": MATERIALS}[kind]
        identifier = f"{kind}-{ctx.run_id}"
        record = await self.records.get(ctx.principal, namespace, identifier)
        if kind == "configuration":
            text, block_kind, trust = serialize(record.payload), "material", "platform"
        elif kind == "rule":
            text, block_kind, trust = record.payload["text"], "instruction", "platform"
        else:
            text, block_kind, trust = record.payload["text"], "material", "external"
        import hashlib

        pin = Ref(
            kind=kind,
            id=identifier,
            version=str(record.revision),
            content_hash=hashlib.sha256(text.encode()).hexdigest(),
        )
        return Reading(pin, text, kind=block_kind, trust=trust, required=kind != "content")

    async def check(self, pin, ctx):
        await self.authority.authorize(ctx)
        current = await self.current(pin.kind, ctx)
        if current.ref != pin:
            raise reject("source_changed", "SQL fixture source version changed", 410)

    async def read(self, pin, revision_policy, ctx):
        await self.check(pin, ctx)
        return await self.current(pin.kind, ctx)


class SQLRules:
    def __init__(self, sources):
        self.sources = sources

    async def discover(self, request, ctx):
        if request != RulesRequest(
            scope_paths=(), user_instruction_refs=(), activated_skill_refs=()
        ):
            raise reject("fixture_rules_unavailable", "Only this registered fixture rule exists")
        reading = await self.sources.current("rule", ctx)
        await self.sources.check(reading.ref, ctx)
        record = await self.sources.records.get(ctx.principal, RULES, reading.ref.id)
        rule = from_wire(InstructionRule, {**record.payload, "source_ref": reading.ref.wire()})
        return RulePlan((RuleCandidate(rule),), assessment_complete=True)


class SQLComposition:
    """Persisted fixture epoch/protection; live permission checks use the real port."""

    def __init__(self, records, sources):
        self.records, self.sources = records, sources

    async def resolve(self, purpose, ctx):
        await self.sources.authority.authorize(ctx)
        request = (await self.records.get(ctx.principal, EPOCHS, ctx.run_id)).payload
        if purpose != request["purpose"]:
            raise reject(
                "fixture_purpose_unavailable", "No registered fixture rules for this purpose"
            )
        capability = await self.sources.current("configuration", ctx)
        from uaw.context.contracts import PreservationSpec

        return CompositionBinding(
            epoch=request["expected_epoch"],
            rules=RulesRequest(scope_paths=(), user_instruction_refs=(), activated_skill_refs=()),
            capability_ref=capability.ref,
            preserve=from_wire(PreservationSpec, request["preserve"]),
        )

    async def verify(self, binding, ctx):
        if binding != await self.resolve("agent_step", ctx):
            raise reject("context_dependency_changed", "SQL fixture binding changed", 410)


def components(records, configuration):
    authority = RunContextSources(records)
    sources = SQLSources(records, authority)
    return ContextComponents(
        readers={"input": authority, "rule": sources, "configuration": sources, "content": sources},
        cancellation=authority,
        rules=SQLRules(sources),
        models=FixedModelWindow(PolicyResolver(records, configuration)),
        repository=ContextRepository(records, TransactionalStore(records.database)),
        authority=SQLComposition(records, sources),
    )


async def restart(payload):
    """Fresh interpreter/DB connection; no copied secret store or model HTTP calls."""
    database = Database(payload["database_url"])
    try:
        records = PostgresRecordStore(database)
        platform = from_wire(Principal, payload["platform"])
        configuration = ConfigurationService(records, WindowsCredentialStore(platform.id), platform)
        ctx = from_wire(TrustedExecutionContext, payload["context"])
        prompt = await GenericModelInputs(components(records, configuration).composer).resolve(
            payload["ref"], ctx
        )
        from uaw.context.contracts import digest

        return {
            "messages_hash": digest(prompt.messages),
            "tools_hash": digest(prompt.tools),
            "estimated_tokens": prompt.estimated_tokens,
        }
    finally:
        await database.close()


if __name__ == "__main__":
    # The controlled test URL arrives on stdin, never in command args/logs/artifacts.
    import sys

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
