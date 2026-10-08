"""Route by real persisted namespace, never by inferred purpose or error fallback."""

from typing import Any

from sqlalchemy import select

from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.model.contracts import ModelPrompt
from uaw.model.ports import ModelInputPort
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing


class ContextModelInputs:
    def __init__(
        self,
        store: PostgresRecordStore,
        legacy: ModelInputPort,
        generic: ModelInputPort | None = None,
    ) -> None:
        self.store, self.legacy, self.generic = store, legacy, generic

    async def resolve(self, ref: dict[str, Any], ctx: TrustedExecutionContext) -> ModelPrompt:
        validate_contract("Ref", ref)
        if ref["kind"] != "context":
            raise reject("model_reference_invalid", "A fixed context Ref is required")
        async with self.store.database.sessions() as session:
            found = list(
                await session.scalars(
                    select(RecordRow.namespace).where(
                        RecordRow.principal_id == ctx.principal.id,
                        RecordRow.resource_id == ref["id"],
                        RecordRow.namespace.in_(("context.bindings", "context.generic.bindings")),
                        RecordRow.deleted.is_(False),
                    )
                )
            )
        if len(found) > 1:
            raise reject(
                "model_context_ambiguous", "Context exists in multiple owned namespaces", 409
            )
        if not found:
            raise StoreMissing()
        if found[0] == "context.generic.bindings":
            if self.generic is None:
                raise CapabilityUnavailable("context.generic_model_input_authority")
            return await self.generic.resolve(ref, ctx)
        return await self.legacy.resolve(ref, ctx)
