"""Runner wire DTOs: the published schema, with no private wire extensions."""

from dataclasses import dataclass
from typing import Literal

from pydantic import Field

from uaw.shared.contracts import (
    ID,
    ContractModel,
    Failure,
    JsonObject,
    Principal,
    Ref,
    Revision,
    Timestamp,
    TrustedExecutionContext,
)


class RunnerCommand(ContractModel):
    command_id: ID
    operation_id: ID
    request_ref: Ref
    trusted_context: TrustedExecutionContext
    fencing_token: Revision
    expires_at: Timestamp
    signature: str = Field(min_length=1)
    parameters: JsonObject


class RunnerReceipt(ContractModel):
    command_id: ID
    attempt_id: ID
    kind: Literal["ok", "waiting", "failed", "cancelled"]
    usage: JsonObject
    signature: str = Field(min_length=1)
    payload: JsonObject | None = None
    wait_ref: Ref | None = None
    failure: Failure | None = None


class RootSelection(ContractModel):
    selection_token: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    expires_at: Timestamp
    root_handle: ID


class RunnerAuthoritySnapshot(ContractModel):
    """Typed consumer of A's published complete schema; no default authority fields."""

    context: TrustedExecutionContext
    device_id: ID
    root_handle: ID
    workspace_ref: Ref
    binding_revision: Revision
    fencing_token: Revision
    lease_expires_at: Timestamp
    request_ref: Ref
    request_parameters: JsonObject
    policy_ref: Ref
    required_scope_capability: str = Field(min_length=1)
    allowed_actions: tuple[ID, ...]
    feature_enabled: bool
    connected: bool
    cancelled: bool


@dataclass(frozen=True)
class RegisteredReceiptCommand:
    """Internal Reader result from an independent registered source, never a wire DTO."""

    command: RunnerCommand
    device_id: str
    owner: Principal


class RunnerChannelSnapshot(ContractModel):
    device_id: ID
    owner: Principal
    actor: Principal
    pairing_ref: Ref
    channel_ref: Ref
    key_ref: Ref
    connected: bool
    expires_at: Timestamp


class RunnerRootSnapshot(ContractModel):
    owner: Principal
    device_id: ID
    workspace_ref: Ref
    root_handle: ID
    binding_revision: Revision
    allowed_actions: tuple[ID, ...]
    expires_at: Timestamp
