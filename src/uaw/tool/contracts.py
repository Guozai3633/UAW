"""Typed views of existing contracts, with no new wire fields."""

from typing import Literal

from uaw.shared.contracts import ID, ContractModel, JsonObject, Ref, Version


class ToolSpec(ContractModel):
    id: ID
    version: Version
    description: str
    input_schema: JsonObject
    output_schema: JsonObject
    categories: tuple[ID, ...]
    required_capabilities: tuple[ID, ...]
    effect: Literal[
        "read", "internal_write", "workspace_write", "external_write", "process", "credential"
    ]
    provider_ref: Ref
    retry_policy_ref: Ref
    equivalence_contract_ref: Ref | None = None
    feature_flag: ID | None = None


class ToolCall(ContractModel):
    tool_ref: Ref
    arguments: JsonObject
    action_id: ID


class ValidatedCall(ToolCall):
    arguments_hash: str
