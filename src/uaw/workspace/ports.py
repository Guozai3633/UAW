"""Internal trusted adapter ports, never accepted from HTTP/model parameters."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from uaw.shared.contracts import JsonObject, Principal, Ref, TrustedExecutionContext
from uaw.shared.runner_signatures import VerificationKey
from uaw.workspace.contracts import RegisteredReceiptCommand, RootSelection, RunnerCommand


@dataclass(frozen=True)
class SelectedRoot:
    # Supplied ONLY by a trusted native selection adapter after atomic token consumption.
    principal_id: str
    device_id: str
    root_handle: str
    native_path: Path
    capabilities: frozenset[str]
    expires_at: datetime
    selection_ticket_id: str | None = None
    selection_key_id: str | None = None
    selection_signature: str | None = None
    confirmation_expires_at: datetime | None = None


@dataclass(frozen=True)
class RootGrant:
    principal_id: str
    device_id: str
    root_handle: str
    workspace_ref: Ref
    native_path: Path
    file_identity: tuple[int, int]
    capabilities: frozenset[str]
    revision: int = 0
    revoked: bool = False
    owner: Principal | None = None
    expires_at: datetime | None = None
    selection_ticket_id: str | None = None
    selection_key_id: str | None = None
    selection_signature: str | None = None
    confirmation_expires_at: datetime | None = None


@dataclass(frozen=True)
class CommandAuthority:
    # All values resolved freshly from trusted services, not copied from the command.
    context: TrustedExecutionContext
    device_id: str
    root_handle: str
    workspace_ref: Ref
    binding_revision: int
    fencing_token: int
    lease_expires_at: datetime
    request_ref: Ref
    request_parameters: JsonObject
    policy_ref: Ref
    required_scope_capability: str
    allowed_actions: frozenset[str]
    feature_enabled: bool
    connected: bool
    cancelled: bool


@dataclass(frozen=True)
class Admission:
    command_id: str
    attempt_id: str
    fingerprint: str
    state: str = "admitted"


class SignaturePort(Protocol):
    def verify_command(self, command: RunnerCommand, *, device_id: str) -> bool:
        """Verify every wire field except signature, including all nested parameters."""
        ...

    def verify_receipt(self, receipt: JsonObject, *, device_id: str) -> bool: ...


class RootSelectionPort(Protocol):
    def consume(
        self,
        selection: RootSelection,
        *,
        principal_id: str,
        device_id: str,
        now: datetime,
    ) -> SelectedRoot:
        """Verify native origin, signature, identity, expiry and atomic single use."""
        ...


class AuthorityPort(Protocol):
    def current(self, command: RunnerCommand) -> CommandAuthority:
        """Resolve request/version, policy intersection, flag, device and live Run lease."""
        ...


class RootRepository(Protocol):
    def add(self, grant: RootGrant) -> RootGrant: ...
    def get(self, root_handle: str) -> RootGrant: ...
    def revoke(self, root_handle: str, *, expected_revision: int) -> RootGrant: ...


class AdmissionRepository(Protocol):
    def reserve(self, principal_id: str, device_id: str, admission: Admission) -> Admission:
        """Atomically return original state; same ID with different fingerprint conflicts."""
        ...


class CurrentKeyDirectory(Protocol):
    def lookup(self, key_id: str, *, device_id: str) -> VerificationKey:
        """Fresh trusted lookup including role and revocation, never payload public keys."""
        ...


@dataclass(frozen=True)
class NativeConfirmation:
    # Authenticated IPC/OS user interaction result, NOT a model-supplied approval boolean.
    ticket_id: str
    principal_id: str
    device_id: str
    document_hash: str
    expires_at: datetime
    native_path: Path | None = None


class NativeConfirmationPort(Protocol):
    async def confirm(
        self,
        *,
        ticket_id: str,
        principal_id: str,
        device_id: str,
        document_hash: str,
    ) -> NativeConfirmation:
        """Authenticate local user/channel, show exact request, confirm and bind its hash."""
        ...


class RunnerPrincipalMappingPort(Protocol):
    async def owner(
        self,
        *,
        authenticated_principal: Principal,
        device_id: str,
    ) -> Principal:
        """Read current registered device ownership and validate the authenticated channel.

        Missing relationships are unavailable. Never derive the user from command claims.
        """
        ...


@runtime_checkable
class CheckedAdmissionRepository(Protocol):
    def reserve_checked(
        self,
        principal_id: str,
        device_id: str,
        admission: Admission,
        *,
        check: Callable[[], None],
    ) -> Admission:
        """Run deadline/cancellation checks inside the same CAS/lock, including replay."""
        ...


class ReceiptCommandReaderPort(Protocol):
    async def resolve(
        self, command_ref: Ref, *, authenticated_principal: Principal
    ) -> RegisteredReceiptCommand:
        """Read immutable command/device/owner and check current recovery access.

        Verify the fixed version/hash and actual channel/device ownership independently.
        Run cancellation/expiry is distinct from data/key revocation. Never synthesize
        the registration from receipt or incoming command claims.
        """
        ...


class RootGrantLookup(RootRepository, Protocol):
    def find(self, *, principal_id: str, device_id: str, workspace_ref: Ref) -> RootGrant:
        """Find one independently persisted grant, rejecting missing/ambiguous bindings."""
        ...
