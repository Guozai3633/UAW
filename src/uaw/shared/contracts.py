"""The small typed contract subset needed now; JSON Schema remains authoritative."""

from __future__ import annotations

from typing import Annotated, Any, ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from uaw.shared.schema import validate_contract

ID = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")]
Version = Annotated[str, Field(min_length=1, max_length=128)]
Revision = Annotated[int, Field(ge=0)]
Timestamp = str
JsonObject = dict[str, JsonValue]


class ContractModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True, hide_input_in_errors=True)
    schema_name: ClassVar[str | None] = None

    @model_validator(mode="after")
    def check_authoritative_contract(self) -> Self:
        validate_contract(
            self.schema_name or type(self).__name__,
            self.model_dump(mode="json", exclude_unset=True),
        )
        return self

    def wire(self) -> dict[str, Any]:
        # Omission and explicit null are distinct. Do not drop supplied null values.
        return self.model_dump(mode="json", exclude_unset=True)


class Location(ContractModel):
    kind: Literal["whole", "page", "lines", "paragraph", "json_pointer", "cell_range", "text_span"]
    start: int | None = None
    end: int | None = None
    anchor: str | None = None
    relative_path: str | None = None


class Ref(ContractModel):
    kind: str
    id: ID
    version: Version
    location: Location | None = None
    content_hash: str | None = None
    access_scope: Scope | None = None


class Principal(ContractModel):
    id: ID
    kind: Literal["user", "admin", "service", "runner"]
    auth_session_id: ID
    delegated_by: ID | None = None


class Scope(ContractModel):
    principal_id: ID
    conversation_id: ID | None = None
    task_id: ID | None = None
    project_id: ID | None = None
    resource_refs: tuple[Ref, ...] = ()
    capabilities: tuple[str, ...] = ()


class ScopeSelector(ContractModel):
    conversation_id: ID | None = None
    task_id: ID | None = None
    project_id: ID | None = None
    resource_refs: tuple[Ref, ...] = ()


class RequestMeta(ContractModel):
    request_id: ID
    schema_version: Literal["0.1"]
    expected_revision: Revision | None = None


class Failure(ContractModel):
    code: ID
    category: str
    message: str
    retryable: bool
    failed_phase: str
    recover_hint: str | None = None
    evidence_refs: tuple[Ref, ...] = ()
    side_effect_state: Literal["pending", "confirmed", "unknown", "none"] | None = None
    retry_after_ms: int | None = None


class TrustedExecutionContext(ContractModel):
    """Only internal adapters construct this; no HTTP/body field accepts it."""

    principal: Principal
    scope: Scope
    operation_id: ID
    trace_id: ID
    attempt_id: ID
    deadline: Timestamp
    capability_policy_ref: Ref
    conversation_id: ID | None = None
    task_id: ID | None = None
    run_id: ID | None = None
    agent_id: ID | None = None
    node_id: ID | None = None
    model_policy_ref: Ref | None = None
    budget_reservation_ref: Ref | None = None

    @model_validator(mode="after")
    def ensure_principal_scope(self) -> Self:
        if self.principal.id != self.scope.principal_id:
            raise ValueError("Execution scope does not belong to the authenticated principal")
        if self.conversation_id and self.scope.conversation_id != self.conversation_id:
            raise ValueError("Execution conversation does not match the authorized scope")
        return self


Ref.model_rebuild()
