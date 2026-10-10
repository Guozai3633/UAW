"""Bounded immutable file material, consumed only through its current owning Reader.

Internal Python adapter, not a new wire DTO or an authority/grant carried by a Ref.
A owns Context recipes, low-trust material placement and Artifact/Task decisions.
"""

import json
from dataclasses import dataclass
from typing import Protocol, cast

from uaw.shared.contracts import JsonObject, Principal, Ref, TrustedExecutionContext
from uaw.tool.providers.file_read import MAX_FILE_ENVELOPE_BYTES, MAX_RETURN_BYTES
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
