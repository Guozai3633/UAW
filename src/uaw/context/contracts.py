"""Wire DTOs follow the baseline schema; dataclasses below are injection-only records."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Literal

from uaw.shared.contracts import ID, ContractModel, Ref, ScopeSelector, Version

Trust = Literal["platform", "user", "project", "external"]
BlockKind = Literal[
    "instruction", "user_input", "history", "material", "memory", "board", "tool_result", "skill"
]
Level = Literal[
    "platform", "capability_policy", "user_current", "project", "user_preference", "role", "skill"
]


@dataclass(frozen=True)
class RecordReadKey:
    """Internal named-record lookup; no Ref or authorization grant."""

    namespace: str
    resource_id: str
    revision: int | None = None


class SourcesRequest(ContractModel):
    schema_name = "InternalContextSourcesRequest"
    source_refs: tuple[Ref, ...]
    purpose: str
    source_revision_policy: Literal["pinned", "latest_required"]


class RulesRequest(ContractModel):
    schema_name = "InternalContextRulesRequest"
    scope_paths: tuple[Ref, ...]
    user_instruction_refs: tuple[Ref, ...]
    activated_skill_refs: tuple[Ref, ...]


class InstructionRule(ContractModel):
    id: ID
    source_ref: Ref
    level: Level
    scope: ScopeSelector
    text: str


class InstructionSet(ContractModel):
    rules: tuple[InstructionRule, ...]
    conflict_refs: tuple[Ref, ...]
    version: Version


class SelectionRequest(ContractModel):
    candidate_refs: tuple[Ref, ...]
    purpose: str
    model_context_limit: int
    output_reserve: int
    tool_reserve: int


class PreservationSpec(ContractModel):
    required_refs: tuple[Ref, ...]
    exact_strings: tuple[str, ...]
    requirement_ids: tuple[str, ...]
    pending_action_refs: tuple[Ref, ...]


@dataclass(frozen=True)
class Reading:
    """Exact UTF-8 text of ref.location, never a synthetic summary of that location.

    The authorized adapter owns kind/trust/required/requirement_ids classification.
    user_input, instructions and pending state must be marked protected. No caller
    or text parser may derive platform trust from the contents.
    """

    ref: Ref
    text: str
    kind: BlockKind = "material"
    trust: Trust = "external"
    required: bool = False
    requirement_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class RuleCandidate:
    """Registered rule metadata from the trusted provider, not wire/LLM parameters.

    topic/value identify a verified conflict dimension. Unknown natural-language
    conflicts remain the provider's responsibility. order is root-to-target then
    explicit correction order. target_refs bind discovered directory rules.
    """

    rule: InstructionRule
    target_refs: tuple[Ref, ...] = ()
    order: int = 0
    topic: str | None = None
    value: str | None = None
    critical: bool = True
    supersedes: tuple[str, ...] = ()


@dataclass(frozen=True)
class RulePlan:
    candidates: tuple[RuleCandidate, ...]
    conflict_refs: tuple[Ref, ...] = ()
    assessment_complete: bool = False


@dataclass(frozen=True)
class RuleAssembly:
    """Internal audit trail for A's Composer; no invented stored output Ref."""

    instructions: InstructionSet
    dependencies: tuple[Ref, ...]
    overrides: tuple[tuple[Ref, Ref], ...]  # suppressed, effective

    def manifest(self) -> dict[str, object]:
        return {
            "version": "0.1",
            "input_refs": [ref.wire() for ref in self.dependencies],
            "dependency_refs": [],
            "content_hash": self.instructions.version,
        }


@dataclass(frozen=True)
class ModelWindow:
    """Resolved from the user's fixed policy by an authorized Model adapter."""

    policy_ref: Ref
    context_limit: int
    max_output_tokens: int
    serialization_reserve: int


@dataclass(frozen=True)
class Allocation:
    """Diagnostic metadata is internal; SelectionResult wire shape stays unchanged."""

    selected: tuple[Reading, ...]
    omitted: tuple[Reading, ...]
    input_budget: int
    input_tokens: int
    estimation: str
    preserved: tuple[Ref, ...]

    def wire(self) -> dict[str, object]:
        return {
            "selected_refs": [r.ref.wire() for r in self.selected],
            "omitted_refs": [r.ref.wire() for r in self.omitted],
            "allocated_tokens": self.input_tokens,
            "preserved_refs": [r.wire() for r in self.preserved],
        }


def digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def ref_key(ref: Ref) -> str:
    return digest(ref.wire())


def from_wire[T: ContractModel](model: type[T], value: dict[str, Any]) -> T:
    # Strict DTOs accept JSON arrays, without relaxing Python-side type checks.
    return model.model_validate_json(json.dumps(value, ensure_ascii=False))


def matches_pin(requested: Ref, actual: Ref) -> bool:
    return (
        requested.kind == actual.kind
        and requested.id == actual.id
        and requested.version == actual.version
        and requested.location == actual.location
        and (requested.content_hash is None or requested.content_hash == actual.content_hash)
    )


class ContextRequest(ContractModel):
    purpose: str
    source_refs: tuple[Ref, ...]
    model_policy_ref: Ref
    output_reserve: int
    tool_reserve: int
    preserve: PreservationSpec
    expected_epoch: int


@dataclass(frozen=True)
class CompositionBinding:
    """Trusted, purpose-specific facts. Missing adapters must return unavailable.

    The owner advances epoch when requirements, rules, flags or capability inputs
    change, and verifies current source/policy revisions before commit/replay.
    The body is injection-only; it is never accepted from HTTP or LLM arguments.
    """

    epoch: int
    rules: RulesRequest
    capability_ref: Ref
    preserve: PreservationSpec
    dependency_refs: tuple[Ref, ...] = ()
    request: ContextRequest | None = None  # Optional exact registered recipe boundary.


@dataclass(frozen=True)
class PreparedSnapshot:
    snapshot: dict[str, Any]
    instructions: dict[str, Any]
    references: tuple[dict[str, Any], ...]
    request: dict[str, Any]


class ModelToolSet(ContractModel):
    run_id: ID
    tools: tuple[dict[str, Any], ...]
