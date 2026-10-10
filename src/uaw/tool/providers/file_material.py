"""Bounded immutable file material, consumed only through its current owning Reader.

Internal Python adapter, not a new wire DTO or an authority/grant carried by a Ref.
A owns Context recipes, low-trust material placement and Artifact/Task decisions.
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Protocol, cast

from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.db.transactions import RecordTransaction, reference
from uaw.shared.contracts import JsonObject, Principal, Ref, TrustedExecutionContext
from uaw.tool.errors import fail, validate_dependency
from uaw.tool.ledger import action_key, immutable
from uaw.tool.providers.file_read import MAX_FILE_ENVELOPE_BYTES, MAX_RETURN_BYTES
from uaw.tool.providers.file_store import FileReceiptStore
from uaw.tool.schema import canonical


@dataclass(frozen=True)
class FileMaterialLimits:
    # Actual A/D whole receipt is currently <=16384 characters and <=64KiB UTF-8.
    # A smaller bound rejects; it never truncates, normalizes or reopens a file.
    max_characters: int = 16384
    max_utf8_bytes: int = MAX_RETURN_BYTES

    def __post_init__(self) -> None:
        if (
            type(self.max_characters) is not int
            or type(self.max_utf8_bytes) is not int
            or not 1 <= self.max_characters <= MAX_RETURN_BYTES
            or not 1 <= self.max_utf8_bytes <= MAX_RETURN_BYTES
        ):
            raise ValueError("Explicit positive file material bounds must not exceed 64KiB")


@dataclass(frozen=True)
class FileMaterial:
    """Immutable selected original material; cached value never grants current access.

    Stores strict canonical bytes, so caller mutation of a returned dict/model cannot
    alter the original observation. Contains only the verified selected FileContent,
    never the original full snapshot or a filesystem path outside its relative path.
    New consumption/reuse must call FileMaterialReaderPort.read(material_ref, ctx).
    """

    _content: bytes
    _usage: bytes
    _owner: bytes
    _references: tuple[tuple[str, bytes], ...]

    @property
    def content(self) -> JsonObject:
        return cast(JsonObject, json.loads(self._content))

    @property
    def usage(self) -> JsonObject:
        return cast(JsonObject, json.loads(self._usage))

    @property
    def owner(self) -> Principal:
        return Principal.model_validate_json(self._owner)

    @property
    def text(self) -> str:
        return cast(str, self.content["text"])

    @property
    def file_hash(self) -> str:
        return cast(str, self.content["content_hash"])

    def _ref(self, name: str) -> Ref:
        return Ref.model_validate_json(dict(self._references)[name])

    @property
    def material_ref(self) -> Ref:
        return self._ref("material")

    @property
    def observation_ref(self) -> Ref:
        return self._ref("observation")

    @property
    def fragment_ref(self) -> Ref:
        return self._ref("fragment")

    @property
    def command_ref(self) -> Ref:
        return self._ref("command")

    @property
    def runner_receipt_ref(self) -> Ref:
        return self._ref("runner_receipt")

    @property
    def raw_result_ref(self) -> Ref:
        return self._ref("raw_result")

    @property
    def provider_ref(self) -> Ref:
        return self._ref("provider")

    @property
    def call_ref(self) -> Ref:
        return self._ref("call")

    @classmethod
    def _from_verified(
        cls,
        content: JsonObject,
        usage: JsonObject,
        owner: Principal,
        references: dict[str, Ref],
    ) -> FileMaterial:
        # The owning adapter verifies source/permissions first; this constructor
        # only freezes existing named DTOs and is not a public model input API.
        from uaw.shared.schema import validate_contract

        validate_contract("FileContent", content)
        validate_contract("Usage", usage)
        validate_contract("Principal", owner.wire())
        for ref in references.values():
            validate_contract("Ref", ref.wire())
        return cls(
            canonical(content, max_bytes=MAX_FILE_ENVELOPE_BYTES),
            canonical(usage),
            canonical(owner.wire()),
            tuple((name, canonical(ref.wire())) for name, ref in sorted(references.items())),
        )


class FileMaterialReaderPort(Protocol):
    async def export(self, action_id: str, ctx: TrustedExecutionContext) -> FileMaterial:
        """Current owning file data authority + original signed source -> bounded material."""
        ...

    async def read(self, material_ref: Ref, ctx: TrustedExecutionContext) -> FileMaterial:
        """Recheck complete current data authority and original evidence; never new open/send."""
        ...


class FileMaterialAdapter:
    """Current owning Reader -> original selected FileContent -> immutable references.

    No new file execution or authority, no generic SQL/Blob bypass. Independent
    material rows hold only existing named contracts; all source/Blob IO is outside
    the Tool transaction. Every reuse checks the real original journal again.
    """

    def __init__(
        self, source: FileReceiptStore | None, *, limits: FileMaterialLimits | None = None
    ) -> None:
        self.source = source
        self.limits = limits if limits is not None else FileMaterialLimits()

    def ready(self) -> FileReceiptStore:
        source = self.source
        if source is None or source.access is None or source.verifier is None:
            raise fail(
                "dependency_unavailable",
                "Current owning file material Reader is not wired",
                phase="file_material",
                category="dependency",
                status=503,
            )
        source.ready()
        return source

    async def _current(self, action_id: str, ctx: TrustedExecutionContext) -> FileMaterial:
        source = self.ready()
        call, spec = await source.binding(ctx)
        if call["action_id"] != action_id:
            raise fail(
                "receipt_binding_conflict",
                "Material differs from original file action",
                phase="file_material",
                category="conflict",
                status=409,
            )
        original = await source.read_observation(action_id, ctx)
        receipt = await source.provider_receipt(ctx)
        if receipt is None:
            raise fail(
                "unknown_effect",
                "No original observed file response to export",
                phase="file_material",
                category="unknown_effect",
                status=409,
            )
        raw_ref = Ref.model_validate(receipt["raw_result_ref"])
        content = await source.read_raw(raw_ref, ctx)
        assert original.receipt.payload is not None
        if (
            content != original.receipt.payload["result"]
            or receipt["usage"] != original.receipt.usage
        ):
            raise fail(
                "receipt_binding_conflict",
                "Material body/Usage differs from original observation",
                phase="file_material",
                category="conflict",
                status=409,
            )
        text = cast(str, content["text"])
        if (
            len(text) > self.limits.max_characters
            or len(text.encode("utf-8")) > self.limits.max_utf8_bytes
        ):
            raise fail(
                "file_material_too_large",
                "Original file material exceeds explicit consumer bound",
                phase="file_material",
                category="arguments",
                status=413,
            )
        raw = source.data_bytes(content)
        if hashlib.sha256(raw).hexdigest() != raw_ref.content_hash:
            raise ValueError("File material differs from original immutable raw digest")
        observation = await source.ledger.get("tool.file.observation.refs", ctx.attempt_id, ctx)
        fragment = await source.ledger.get("tool.file.fragment.refs", ctx.attempt_id, ctx)
        if observation is None or fragment is None:
            raise fail(
                "dependency_unavailable",
                "Original file observation/fragment refs are unavailable",
                phase="file_material",
                category="dependency",
                status=503,
            )
        observation_ref = Ref.model_validate(observation)
        fragment_ref = Ref.model_validate(fragment)
        expected = source.observation_ref(original, ctx)
        if (
            observation_ref != expected
            or fragment_ref.location is None
            or fragment_ref.location.wire() != original.selection
            or fragment_ref.content_hash != hashlib.sha256(text.encode("utf-8")).hexdigest()
        ):
            raise fail(
                "receipt_binding_conflict",
                "Original file material provenance changed",
                phase="file_material",
                category="conflict",
                status=409,
            )
        refs = {
            "material": Ref(
                kind="content",
                id="file-material-"
                + parameter_hash({"run": ctx.run_id, "attempt": ctx.attempt_id}),
                version="1",
                content_hash=raw_ref.content_hash,
            ),
            "observation": observation_ref,
            "fragment": fragment_ref,
            "command": original.command_ref,
            "runner_receipt": original.receipt_ref,
            "raw_result": raw_ref,
            "provider": Ref.model_validate(spec["provider_ref"]),
            "call": Ref.model_validate(reference("tool_call", action_key(ctx, action_id))),
        }
        material = FileMaterial._from_verified(content, receipt["usage"], ctx.principal, refs)
        # No stale grant/value is returned across the remaining source/SQL awaits.
        again = await source.read_observation(action_id, ctx)
        if again != original:
            raise fail(
                "receipt_version_stale",
                "Original file source changed while exporting material",
                phase="file_material",
                category="conflict",
                status=412,
            )
        await source.binding(ctx)
        return material

    async def _fixed(self, material: FileMaterial, ctx: TrustedExecutionContext) -> None:
        source = self.ready()
        rows = (
            ("tool.file.material.refs", "Ref", material.material_ref.wire()),
            ("tool.file.material.observations", "Ref", material.observation_ref.wire()),
            ("tool.file.material.fragments", "Ref", material.fragment_ref.wire()),
            ("tool.file.material.commands", "Ref", material.command_ref.wire()),
            ("tool.file.material.receipts", "Ref", material.runner_receipt_ref.wire()),
            ("tool.file.material.providers", "Ref", material.provider_ref.wire()),
            ("tool.file.material.calls", "Ref", material.call_ref.wire()),
            ("tool.file.material.owners", "Principal", material.owner.wire()),
            ("tool.file.material.usages", "Usage", material.usage),
        )

        # Existing material still requires _current above; it cannot short-circuit
        # the current permission/source checks. Persistence is CAS, never authority.
        async def write(tx: RecordTransaction) -> JsonObject:
            for namespace, schema, value in rows:
                await immutable(tx, namespace, ctx.attempt_id, schema, value)
            return material.material_ref.wire()

        await source.ledger.transactions.inspect(ctx.principal, source.ledger.aggregate(ctx), write)

    async def export(self, action_id: str, ctx: TrustedExecutionContext) -> FileMaterial:
        material = await self._current(action_id, ctx)
        await self._fixed(material, ctx)
        # Recheck after persistence: a row/blob write is not permission to disclose.
        actual = await self._current(action_id, ctx)
        if actual != material:
            raise fail(
                "receipt_version_stale",
                "File material changed during immutable publication",
                phase="file_material",
                category="conflict",
                status=412,
            )
        return actual

    async def read(self, material_ref: Ref, ctx: TrustedExecutionContext) -> FileMaterial:
        source = self.ready()
        validate_dependency("Ref", material_ref.wire(), "file_material")
        call = await source.ledger.attempt(ctx)
        material = await self._current(str(call["action_id"]), ctx)
        fixed = await source.ledger.get("tool.file.material.refs", ctx.attempt_id, ctx)
        if fixed != material_ref.wire() or material_ref != material.material_ref:
            raise fail(
                "receipt_binding_conflict",
                "Material Ref is not this original exported attempt",
                phase="file_material",
                category="conflict",
                status=409,
            )
        await self._fixed(material, ctx)
        again = await self._current(str(call["action_id"]), ctx)
        if again != material:
            raise fail(
                "receipt_version_stale",
                "Original material changed while reading references",
                phase="file_material",
                category="conflict",
                status=412,
            )
        return again
