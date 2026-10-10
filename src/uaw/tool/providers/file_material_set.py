"""Ordered bounded consumption of existing materials, never execution or authority."""

from dataclasses import dataclass

from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.tool.errors import fail
from uaw.tool.providers.file_material import FileMaterial, FileMaterialReaderPort
from uaw.tool.schema import canonical


@dataclass(frozen=True)
class FileMaterialSetLimits:
    max_characters: int = 16384
    max_utf8_bytes: int = 65536

    def __post_init__(self) -> None:
        if (
            type(self.max_characters) is not int
            or type(self.max_utf8_bytes) is not int
            or not 1 <= self.max_characters <= 16384
            or not 1 <= self.max_utf8_bytes <= 65536
        ):
            raise ValueError("Positive set bounds may only reduce the default totals")


@dataclass(frozen=True)
class FileMaterialSet:
    """Original ordered immutable materials; reuse still requires current owning reads."""

    materials: tuple[FileMaterial, ...]

    def __post_init__(self) -> None:
        if (
            type(self.materials) is not tuple
            or not 1 <= len(self.materials) <= 8
            or any(type(m) is not FileMaterial for m in self.materials)
        ):
            raise ValueError("One to eight immutable original FileMaterial values required")

    @property
    def refs(self) -> tuple[Ref, ...]:
        return tuple(m.material_ref for m in self.materials)

    @property
    def characters(self) -> int:
        return sum(len(m.text) for m in self.materials)

    @property
    def utf8_bytes(self) -> int:
        return sum(len(m.text.encode("utf-8")) for m in self.materials)


class FileMaterialSetAdapter:
    def __init__(
        self, reader: FileMaterialReaderPort | None, *, limits: FileMaterialSetLimits | None = None
    ) -> None:
        self.reader = reader
        self.limits = limits if limits is not None else FileMaterialSetLimits()

    @staticmethod
    def _inputs(refs: tuple[Ref, ...]) -> tuple[Ref, ...]:
        if type(refs) is not tuple or not 1 <= len(refs) <= 8:
            raise fail(
                "file_material_set_invalid",
                "One to eight complete material Refs in a tuple required",
                phase="file_material_set",
            )
        fixed = []
        pins = set()
        for ref in refs:
            if type(ref) is not Ref:
                raise fail(
                    "file_material_set_invalid",
                    "Complete typed material Ref required",
                    phase="file_material_set",
                )
            try:
                # Freeze the full wire before any await, including nested scope/location.
                raw = canonical(ref.wire())
                pin = Ref.model_validate_json(raw)
                if pin.kind != "content" or pin.content_hash is None:
                    raise ValueError("Immutable content hash required")
            except ValueError as exc:
                raise fail(
                    "file_material_set_invalid",
                    "Complete immutable content Ref required",
                    phase="file_material_set",
                ) from exc
            if raw in pins:
                raise fail(
                    "file_material_set_duplicate",
                    "Duplicate material Ref is not a new source",
                    phase="file_material_set",
                    category="conflict",
                    status=409,
                )
            pins.add(raw)
            fixed.append(pin)
        return tuple(fixed)

    async def _read(
        self,
        reader: FileMaterialReaderPort,
        ref: Ref,
        ctx: TrustedExecutionContext,
    ) -> FileMaterial:
        # Give the owning Reader a fresh exact pin, never a shared mutable reference.
        material = await reader.read(Ref.model_validate_json(canonical(ref.wire())), ctx)
        if type(material) is not FileMaterial:
            raise fail(
                "dependency_protocol_invalid",
                "Owning Reader did not return original FileMaterial",
                phase="file_material_set",
                category="dependency",
                status=503,
            )
        if material.material_ref.wire() != ref.wire() or material.owner != ctx.principal:
            raise fail(
                "receipt_binding_conflict",
                "Material is outside its exact original Ref/owner",
                phase="file_material_set",
                category="conflict",
                status=409,
            )
        return material

    def _bounded(self, materials: tuple[FileMaterial, ...]) -> FileMaterialSet:
        result = FileMaterialSet(materials)
        if (
            result.characters > self.limits.max_characters
            or result.utf8_bytes > self.limits.max_utf8_bytes
        ):
            raise fail(
                "file_material_set_too_large",
                "Original materials exceed explicit total bounds",
                phase="file_material_set",
                status=413,
            )
        return result

    async def read(self, refs: tuple[Ref, ...], ctx: TrustedExecutionContext) -> FileMaterialSet:
        fixed = self._inputs(refs)
        reader = self.reader
        if reader is None:
            raise fail(
                "dependency_unavailable",
                "Current owning material Reader is not wired",
                phase="file_material_set",
                category="dependency",
                status=503,
            )
        materials = []
        for ref in fixed:
            materials.append(await self._read(reader, ref, ctx))
            # Early total refusal prevents unbounded accumulated bodies. No partial return.
            self._bounded(tuple(materials))
        original = self._bounded(tuple(materials))
        for ref, material in zip(fixed, original.materials, strict=True):
            again = await self._read(reader, ref, ctx)
            if again != material:
                raise fail(
                    "receipt_version_stale",
                    "Original material changed during set consumption",
                    phase="file_material_set",
                    category="conflict",
                    status=412,
                )
        # No SQL lock/cache/executor or task survives this call. The final sequential
        # source rechecks are not a global atomic authority snapshot across modules.
        return original
