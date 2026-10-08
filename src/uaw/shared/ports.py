"""Runtime injection boundaries. Wire types are validated at their owning facade."""

from typing import Protocol

from uaw.shared.contracts import JsonObject, Principal, Ref, RequestMeta, TrustedExecutionContext


class IntentPort(Protocol):
    async def understand(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject: ...


class AgentPort(Protocol):
    async def start(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject: ...


class ContextPort(Protocol):
    async def build(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject: ...


class ToolPort(Protocol):
    async def invoke(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject: ...


class WorkspacePort(Protocol):
    async def allocate(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject: ...


class ModelPort(Protocol):
    async def generate(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject: ...


class RunPort(Protocol):
    async def create(
        self, request: JsonObject, meta: RequestMeta, ctx: TrustedExecutionContext
    ) -> JsonObject: ...


class ExecutionPolicyPort(Protocol):
    """Fresh Run-bound permission intersection. Does not issue grants or enable flags.

    Return ExecutionPolicySnapshot only from current owned policy records;
    callers still check role, configuration, resources, lease/fence and executor.
    """

    async def resolve(self, ctx: TrustedExecutionContext) -> JsonObject: ...


class ApprovalAuthorityPort(Protocol):
    """Tool-owned live action/resource check. Missing implementations never grant access.

    Compare the immutable validated call and trusted ToolSpec (including effect),
    current role/flags/provider, and every resource version. Raise on any mismatch.
    ApprovalService supplies only its persisted request and trusted Run context.
    """

    async def check(self, request: JsonObject, ctx: TrustedExecutionContext) -> None: ...


class ApprovalPort(Protocol):
    async def request(
        self, request: JsonObject, meta: RequestMeta, ctx: TrustedExecutionContext
    ) -> JsonObject: ...

    async def get(self, actor: Principal, approval_id: str) -> JsonObject: ...

    async def decide(
        self, actor: Principal, request: JsonObject, meta: RequestMeta
    ) -> JsonObject: ...

    async def recheck(
        self, approval_ref: Ref, request: JsonObject, ctx: TrustedExecutionContext
    ) -> JsonObject: ...


class BudgetPort(Protocol):
    async def reserve(
        self, actor: Principal, request: JsonObject, meta: RequestMeta, ctx: TrustedExecutionContext
    ) -> JsonObject: ...

    async def dispatch(
        self,
        actor: Principal,
        reservation_ref: JsonObject,
        meta: RequestMeta,
        ctx: TrustedExecutionContext,
    ) -> JsonObject: ...

    async def release(
        self,
        actor: Principal,
        reservation_ref: JsonObject,
        meta: RequestMeta,
        ctx: TrustedExecutionContext,
    ) -> JsonObject: ...

    async def settle(
        self,
        actor: Principal,
        request: JsonObject,
        meta: RequestMeta,
        ctx: TrustedExecutionContext,
        *,
        status: str,
    ) -> JsonObject: ...


class BudgetStatePort(Protocol):
    """Current owned state for recovery, never an admission or dispatch authorization.

    Return RootBudgetLedger / BudgetReservation. Reservation reads require the
    exact Run, operation, trace and attempt owner. Cancellation/expiry does not
    prevent recovery reads. Callers still use CAS and the mutating BudgetPort.
    """

    async def get_ledger(self, ctx: TrustedExecutionContext) -> JsonObject: ...

    async def get_reservation(
        self, reservation_id: str, ctx: TrustedExecutionContext
    ) -> JsonObject: ...


class ToolReceiptReaderPort(Protocol):
    """Read a trusted provider receipt, never model assertions or timeout inference.

    Validate source ownership, signature/provenance and pinned Ref before returning
    ToolReconciliationReceipt. No reader means reconciliation is unavailable.
    """

    async def read(self, receipt_ref: Ref, ctx: TrustedExecutionContext) -> JsonObject: ...


class AsyncRunnerAuthorityPort(Protocol):
    """Fresh authority from authenticated transport and owned records.

    authenticated_principal is supplied by a trusted channel adapter, never a body
    field. Return RunnerAuthoritySnapshot. Command context is a claim to compare,
    not the source of Run, policy, device, workspace, lease or request authority.
    """

    async def current(
        self, command: JsonObject, *, authenticated_principal: Principal
    ) -> JsonObject: ...


class RunnerChannelSourcePort(Protocol):
    """Independently authenticate channel/owner/device/key and current data access.

    Return RunnerChannelSnapshot. A Ref or actor body never proves a pairing.
    """

    async def read(self, channel_ref: Ref, *, device_id: str) -> JsonObject: ...


class RunnerRootSourcePort(Protocol):
    """Actual native grant owner checks current root/version, not a chat path."""

    async def current(
        self, device_id: str, workspace_ref: Ref, ctx: TrustedExecutionContext
    ) -> JsonObject: ...


class RunnerActionGatePort(Protocol):
    """Check actual role, all resources and required consent for the fixed request."""

    async def check(self, request: JsonObject, ctx: TrustedExecutionContext) -> None: ...


class RunnerCommandSigningPort(Protocol):
    """Use an actual current control key; no private material in parameters/results.

    sign returns RunnerCommand and covers the exact RunnerCommandDraft fields.
    verify must recheck current trusted control key role/revocation plus signature.
    """

    async def sign(self, draft: JsonObject, *, device_id: str) -> JsonObject: ...

    async def verify(self, command: JsonObject, *, device_id: str) -> None: ...


class BudgetExecutionStatePort(Protocol):
    """Current actual dispatch intent/deadline; recovery read is not admission."""

    async def execution_state(
        self, reservation_id: str, ctx: TrustedExecutionContext
    ) -> JsonObject: ...


class ExecutionLeasePort(Protocol):
    """Run-owned root coordination, not a permission or command authorization.

    holder is an authenticated internal service identity from composition/transport,
    never HTTP/model body. Reads check exact revision/fence/holder and current Run.
    Nested node leases are unavailable. Return ExecutionLease; release returns
    ExecutionLeaseStateRecord. A consumer must recheck before sending or executing.
    """

    async def acquire(
        self,
        request: JsonObject,
        meta: RequestMeta,
        ctx: TrustedExecutionContext,
        *,
        holder: Principal,
    ) -> JsonObject: ...

    async def renew(
        self,
        request: JsonObject,
        meta: RequestMeta,
        ctx: TrustedExecutionContext,
        *,
        holder: Principal,
    ) -> JsonObject: ...

    async def release(
        self,
        request: JsonObject,
        meta: RequestMeta,
        ctx: TrustedExecutionContext,
        *,
        holder: Principal,
    ) -> JsonObject: ...

    async def current(
        self,
        lease_ref: Ref,
        fencing_token: int,
        ctx: TrustedExecutionContext,
        *,
        holder: Principal,
    ) -> JsonObject: ...

    async def state(self, ctx: TrustedExecutionContext, *, holder: Principal) -> JsonObject:
        """Owned ExecutionLeaseStateRecord for takeover/cleanup, not execution permission."""
        ...
