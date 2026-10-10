"""Ordered bounded consumption of existing materials, never execution or authority."""

from dataclasses import dataclass

from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.tool.errors import fail
from uaw.tool.providers.file_material import FileMaterial, FileMaterialReaderPort


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

    async def read(self, refs: tuple[Ref, ...], ctx: TrustedExecutionContext) -> FileMaterialSet:
        # M1 pins the consumer signature. M2 supplies current owning reads; no fake source.
        raise fail(
            "dependency_unavailable",
            "Multi-material owning reads are not yet implemented",
            phase="file_material_set",
            category="dependency",
            status=503,
        )
