"""Bounded process-local catalogue; not a durable effect/intent ledger."""

import json
from dataclasses import dataclass
from threading import RLock
from typing import Any

from uaw.shared.contracts import Ref
from uaw.shared.schema import ContractViolation, validate_contract
from uaw.tool.contracts import ToolSpec
from uaw.tool.errors import fail
from uaw.tool.schema import canonical, compile_schema, digest


@dataclass(frozen=True)
class AdapterBinding:
    """Internal composition metadata. Test bindings are never model-visible."""

    provider_ref: Ref
    environments: frozenset[str]
    implemented: bool = False
    test_only: bool = False


@dataclass(frozen=True)
class RegistryEntry:
    spec_bytes: bytes
    binding: AdapterBinding | None

    def spec(self) -> dict[str, Any]:
        return json.loads(self.spec_bytes)  # type: ignore[no-any-return]


class ToolRegistry:
    def __init__(self, *, capacity: int = 128) -> None:
        if type(capacity) is not int or not 1 <= capacity <= 256:
            raise ValueError("Catalogue capacity must be between 1 and 256")
        self.capacity = capacity
        self._revision = 0
        self._entries: dict[tuple[str, str], RegistryEntry] = {}
        self._lock = RLock()

    @property
    def revision(self) -> int:
        with self._lock:
            return self._revision

    def register(
        self, spec: dict[str, Any], *, expected_revision: int, binding: AdapterBinding | None = None
    ) -> int:
        """Internal/admin composition only; this method has no HTTP/model route."""
        try:
            spec_bytes = canonical(spec)
        except (ValueError, OverflowError, RecursionError) as exc:
            raise fail(
                "registration_invalid",
                "Tool registration exceeds JSON limits",
                phase="registration",
            ) from exc
        try:
            validate_contract("ToolSpec", spec)
        except ContractViolation as exc:
            raise fail(
                "registration_invalid", "ToolSpec violates the fixed contract", phase="registration"
            ) from exc
        # Retain the authoritative wire schema; the typed view is optional for consumers.
        compile_schema(spec["input_schema"], arguments=True)
        compile_schema(spec["output_schema"])
        if type(expected_revision) is not int or expected_revision < 0:
            raise fail(
                "registration_invalid",
                "Expected revision must be a nonnegative integer",
                phase="registration",
            )
        if binding is not None:
            if binding.provider_ref.wire() != spec["provider_ref"] or not binding.environments:
                raise fail(
                    "registration_invalid",
                    "Adapter does not match the fixed provider",
                    phase="registration",
                )
        key = (spec["id"], spec["version"])
        with self._lock:
            existing = self._entries.get(key)
            if existing:
                if existing.spec_bytes != spec_bytes or existing.binding != binding:
                    raise fail(
                        "revision_conflict",
                        "Tool versions and bindings are immutable",
                        phase="registration",
                        category="conflict",
                        status=409,
                    )
                return self._revision
            if self._revision != expected_revision:
                raise fail(
                    "revision_conflict",
                    "Catalogue revision changed",
                    phase="registration",
                    category="conflict",
                    status=409,
                )
            if len(self._entries) >= self.capacity:
                raise fail("registry_full", "Bounded catalogue is full", phase="registration")
            self._entries[key] = RegistryEntry(spec_bytes, binding)
            self._revision += 1
            return self._revision

    def unregister(self, tool_ref: dict[str, Any], *, expected_revision: int) -> int:
        """Trusted admin/composition CAS removal; cached vectors never keep it installed."""
        with self._lock:
            if type(expected_revision) is not int or expected_revision != self._revision:
                raise fail(
                    "revision_conflict",
                    "Catalogue revision changed",
                    phase="registration",
                    category="conflict",
                    status=409,
                )
            entry = self.get(tool_ref)
            spec = entry.spec()
            del self._entries[(spec["id"], spec["version"])]
            self._revision += 1
            return self._revision

    def snapshot(self) -> tuple[int, tuple[RegistryEntry, ...]]:
        with self._lock:
            return self._revision, tuple(self._entries.values())

    def get(self, tool_ref: dict[str, Any]) -> RegistryEntry:
        validate_contract("Ref", tool_ref)
        # ToolSpec is a registered configuration object; no undeclared RefKind is added.
        if tool_ref["kind"] != "configuration" or set(tool_ref) - {
            "kind",
            "id",
            "version",
            "content_hash",
        }:
            raise fail(
                "reference_error",
                "Expected a fixed tool configuration reference",
                phase="normalize",
            )
        with self._lock:
            entry = self._entries.get((tool_ref["id"], tool_ref["version"]))
        if entry is None:
            raise fail(
                "tool_missing",
                "Tool version is not registered",
                phase="normalize",
                category="dependency",
                status=404,
            )
        if tool_ref.get("content_hash", digest(entry.spec())) != digest(entry.spec()):
            raise fail(
                "stale_resource",
                "Tool content hash does not match its version",
                phase="normalize",
                category="conflict",
                status=412,
            )
        return entry

    @staticmethod
    def reference(entry: RegistryEntry) -> dict[str, Any]:
        spec = entry.spec()
        return {
            "kind": "configuration",
            "id": spec["id"],
            "version": spec["version"],
            "content_hash": digest(spec),
        }

    @staticmethod
    def typed(entry: RegistryEntry) -> ToolSpec:
        return ToolSpec.model_validate_json(entry.spec_bytes)
