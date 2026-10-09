"""Complete bounded inventory of recorded Tool actions, never global OS activity claims."""

from sqlalchemy import select

from uaw.agent.contracts import Payload
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore, parameter_hash
from uaw.model.evaluation_inputs import EvaluationSource
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing

MAX_TOOL_ACTIONS = 16


async def tool_activity(
    records: PostgresRecordStore, ctx: TrustedExecutionContext
) -> tuple[Payload, tuple[EvaluationSource, ...], dict[str, Ref], tuple[str, ...]]:
    async with records.database.sessions() as session:
        contexts = tuple(
            await session.scalars(
                select(RecordRow)
                .where(
                    RecordRow.principal_id == ctx.principal.id,
                    RecordRow.namespace == "tool.contexts",
                    RecordRow.deleted.is_(False),
                    RecordRow.payload["run_id"].as_string() == ctx.run_id,
                )
                .order_by(RecordRow.resource_id)
                .limit(MAX_TOOL_ACTIONS + 1)
            )
        )
    if len(contexts) > MAX_TOOL_ACTIONS:
        raise reject("completion_activity_too_large", "Tool action inventory exceeds 16", 413)
    actions, pins, offered = [], [], {}
    for index, context in enumerate(contexts):
        key = context.resource_id
        rows = [
            await records.get(ctx.principal, namespace, key)
            for namespace in (
                "tool.contexts",
                "tool.calls",
                "tool.specs",
                "tool.effects",
            )
        ]
        try:
            intent = await records.get(ctx.principal, "tool.dispatch.intents", key)
        except StoreMissing:
            intent = None
        if intent is not None:
            rows.append(intent)
        for row in rows:
            validate_contract(row.schema_name, row.payload)
            pins.append(
                EvaluationSource(
                    row.namespace,
                    Ref(
                        kind="content",
                        id=key,
                        version=str(row.revision),
                        content_hash=parameter_hash(row.payload),
                    ),
                    row.schema_name,
                )
            )
        if rows[0].payload["run_id"] != ctx.run_id:
            raise reject("completion_activity_changed", "Tool activity belongs to another Run", 412)
        alias = f"activity-{index}"
        offered[alias] = pins[-len(rows)].ref
        actions.append(
            {
                "id": alias,
                "tool_spec": rows[2].payload,
                "call": rows[1].payload,
                "dispatch_recorded": intent is not None,
                "effect_state": rows[3].payload["state"],
            }
        )
    return (
        {
            "scope": "All recorded Tool actions in this UAW Run; model provider HTTP is separate. "
            "Does not attest global OS or provider-internal activity.",
            "complete_within_scope": True,
            "actions": actions,
        },
        tuple(pins),
        offered,
        tuple(c.resource_id for c in contexts),
    )
