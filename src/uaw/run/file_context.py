"""Current owning file material in Context, without copying it into a trusted blob."""

import json
from datetime import datetime

from uaw.context.contracts import Reading
from uaw.context.registered import RegisteredContextInputs, identity
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.stores import Record, StoreConflict, StoreMissing
from uaw.tool.providers.file_material import FileMaterial, FileMaterialReaderPort

ORIGIN = "run.context.file.origins"
PINS = "run.context.file.pins"
MATERIAL = "run.context.file.materials"
OBSERVATION = "run.context.file.observations"


class FileContextMaterials:
    def __init__(
        self,
        records: PostgresRecordStore,
        controller: Principal,
        source: FileMaterialReaderPort | None,
    ) -> None:
        self.records, self.controller, self.source = records, controller, source
        self.transactions = TransactionalStore(records.database)

    def ready(self) -> FileMaterialReaderPort:
        if self.source is None:
            raise CapabilityUnavailable("context.current_file_material_source")
        return self.source

    @staticmethod
    def reading(material: FileMaterial) -> Reading:
        return Reading(material.fragment_ref, material.text, kind="material", trust="external")

    async def register(
        self, action_id: str, ctx: TrustedExecutionContext, *, authenticated_service: Principal
    ) -> Ref:
        if authenticated_service != self.controller or self.controller.kind != "service":
            raise reject("file_context_controller_denied", "Current controller required", 403)
        source = self.ready()
        material = await source.export(action_id, ctx)
        if material.owner != ctx.principal or not ctx.run_id:
            raise reject("file_context_owner_denied", "Original material owner differs", 403)
        fragment = material.fragment_ref
        if fragment.kind != "content" or not fragment.id.startswith("file-fragment-"):
            raise reject("file_context_fragment_denied", "Original fragment pin required", 412)
        entries = (
            (ORIGIN, "TrustedExecutionContext", ctx.wire()),
            (PINS, "Ref", fragment.wire()),
            (MATERIAL, "Ref", material.material_ref.wire()),
            (OBSERVATION, "Ref", material.observation_ref.wire()),
        )

        async def write(tx: RecordTransaction) -> dict[str, object]:
            for namespace, schema, value in entries:
                try:
                    row = await tx.load(namespace, fragment.id)
                except StoreMissing:
                    await tx.write(namespace, fragment.id, schema, value)
                else:
                    if row.schema_name != schema or row.revision != 1 or row.payload != value:
                        raise StoreConflict("file_context_origin_conflict")
            return {}

        await self.transactions.inspect(ctx.principal, "file-context-" + ctx.run_id, write)
        # Permission/source IO is outside the SQL lock and remains mandatory on replay.
        if await source.read(material.material_ref, ctx) != material:
            raise reject("file_context_material_changed", "Original material changed", 412)
        return fragment

    async def read(self, pin: Ref, ctx: TrustedExecutionContext) -> Reading:
        source = self.ready()
        namespaces = (ORIGIN, PINS, MATERIAL, OBSERVATION)
        rows = tuple([await self.records.get(ctx.principal, n, pin.id) for n in namespaces])
        expected = ("TrustedExecutionContext", "Ref", "Ref", "Ref")
        if any(
            r.schema_name != name or r.revision != 1 for r, name in zip(rows, expected, strict=True)
        ):
            raise reject("file_context_origin_changed", "Original source binding changed", 412)
        original = TrustedExecutionContext.model_validate_json(json.dumps(rows[0].payload))
        if identity(original) != identity(ctx) or datetime.fromisoformat(
            ctx.deadline.replace("Z", "+00:00")
        ) > datetime.fromisoformat(original.deadline.replace("Z", "+00:00")):
            raise reject("file_context_scope_denied", "Original file scope/session differs", 403)
        if pin.wire() != rows[1].payload:
            raise reject("file_context_pin_changed", "Exact original fragment required", 412)
        material = await source.read(Ref.model_validate(rows[2].payload), original)
        if (
            material.owner != ctx.principal
            or material.fragment_ref != pin
            or material.observation_ref.wire() != rows[3].payload
        ):
            raise reject("file_context_source_changed", "Original file provenance differs", 412)
        if tuple([await self.records.get(ctx.principal, n, pin.id) for n in namespaces]) != rows:
            raise reject("file_context_origin_changed", "Binding changed during source await", 412)
        return self.reading(material)


class FileAwareContextInputs(RegisteredContextInputs):
    """Use ordinary Context gates/recipes, route only registered file fragments externally."""

    file_materials: FileContextMaterials | None = None

    @staticmethod
    def file_pin(pin: Ref) -> bool:
        return pin.kind == "content" and pin.id.startswith("file-fragment-")

    async def _read(
        self,
        pin: Ref,
        ctx: TrustedExecutionContext,
        source_rows: tuple[Record, Record, Record] | None = None,
    ) -> Reading:
        if self.file_pin(pin):
            if self.file_materials is None:
                raise CapabilityUnavailable("context.current_file_material_source")
            return await self.file_materials.read(pin, ctx)
        return await super()._read(pin, ctx, source_rows)

    async def _read_many(
        self, pins: tuple[Ref, ...], ctx: TrustedExecutionContext
    ) -> tuple[Reading, ...]:
        if not any(self.file_pin(p) for p in pins):
            return await super()._read_many(pins, ctx)
        if type(pins) is not tuple or len(pins) > 128:
            raise reject("file_context_batch_too_large", "At most128 sources required", 413)
        regular = tuple(p for p in pins if not self.file_pin(p))
        readings = iter(await super()._read_many(regular, ctx))
        result = []
        for pin in pins:
            result.append(await self._read(pin, ctx) if self.file_pin(pin) else next(readings))
        return tuple(result)
