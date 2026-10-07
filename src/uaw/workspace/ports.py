"""Internal trusted adapter ports, never accepted from HTTP/model parameters."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from uaw.shared.contracts import JsonObject, Ref, TrustedExecutionContext
from uaw.shared.runner_signatures import VerificationKey
from uaw.workspace.contracts import RootSelection, RunnerCommand


@dataclass(frozen=True)
class SelectedRoot:
    # Supplied ONLY by a trusted native selection adapter after atomic token consumption.
    principal_id: str
    device_id: str
    root_handle: str
    native_path: Path
    capabilities: frozenset[str]
    expires_at: datetime


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
