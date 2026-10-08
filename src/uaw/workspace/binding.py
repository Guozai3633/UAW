"""Local root binding and read admission; never accepts a chat path as authority."""

import json
from datetime import datetime
from ntpath import isreserved
from pathlib import Path, PureWindowsPath

from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract
from uaw.workspace.contracts import RootSelection
from uaw.workspace.ports import RootGrant, RootRepository, RootSelectionPort


def aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise reject("schema_invalid", "A timezone-aware clock is required")
    return value


class RootBindings:
    def __init__(
        self, repository: RootRepository, selection_port: RootSelectionPort | None = None
    ) -> None:
        self.repository = repository
        self.selection_port = selection_port

    def bind(
        self,
        selection: RootSelection,
        *,
        principal_id: str,
        device_id: str,
        workspace_ref: Ref,
        capabilities: frozenset[str],
        now: datetime,
        owner: Principal | None = None,
    ) -> RootGrant:
        selection = RootSelection.model_validate(selection.wire())
        aware(now)
        if owner is not None:
            owner = Principal.model_validate_json(json.dumps(owner.wire()))
            if owner.kind != "user" or owner.id != principal_id:
                raise reject("permission_denied", "Root grant owner mismatch", 403, "permission")
        if self.selection_port is None:
            raise CapabilityUnavailable("runner.root_selection")
        if not capabilities or not capabilities <= {"read"}:
            raise CapabilityUnavailable("runner.write_exec_D03")
        if workspace_ref.kind != "workspace":
            raise reject("schema_invalid", "A fixed workspace reference is required")
        expiry = datetime.fromisoformat(selection.expires_at.replace("Z", "+00:00"))
        if expiry <= now:
            raise reject("stale_resource", "Root selection expired", 410)
        selected = self.selection_port.consume(
            selection,
            principal_id=principal_id,
            device_id=device_id,
            now=now,
        )
        if (
            selected.principal_id != principal_id
            or selected.device_id != device_id
            or selected.root_handle != selection.root_handle
            or aware(selected.expires_at) != expiry
            or not capabilities <= selected.capabilities
        ):
            raise reject(
                "permission_denied", "Native selection identity mismatch", 403, "permission"
            )
        try:
            if not selected.native_path.is_absolute():
                raise ValueError("Relative root")
            root = selected.native_path.resolve(strict=True)
            if not root.is_dir() or root == Path(root.anchor):
                raise ValueError("Invalid root")
            stat = root.stat()
        except OSError, ValueError, RuntimeError:
            raise reject(
                "permission_denied", "Selected root is unavailable", 403, "permission"
            ) from None
        grant = RootGrant(
            principal_id,
            device_id,
            selection.root_handle,
            workspace_ref,
            root,
            (stat.st_dev, stat.st_ino),
            capabilities,
            owner=owner,
            expires_at=expiry,
            selection_ticket_id=selected.selection_ticket_id,
            selection_key_id=selected.selection_key_id,
            selection_signature=selected.selection_signature,
            confirmation_expires_at=selected.confirmation_expires_at,
        )
        return self.repository.add(grant)

    def check_scope(
        self,
        *,
        root_handle: str,
        principal_id: str,
        device_id: str,
        workspace_ref: Ref,
        expected_revision: int,
        relative_path: str,
        now: datetime | None = None,
    ) -> Path:
        grant = self.repository.get(root_handle)
        if now is not None and grant.expires_at is not None:
            deadline = grant.expires_at
            if grant.confirmation_expires_at is not None:
                deadline = min(deadline, grant.confirmation_expires_at)
            if aware(deadline) <= aware(now):
                raise reject("deadline_exceeded", "Root grant expired", 410, "timeout")
        if grant.revoked:
            raise reject("permission_denied", "Root authorization revoked", 403, "permission")
        if (
            grant.principal_id != principal_id
            or grant.device_id != device_id
            or grant.workspace_ref.wire() != workspace_ref.wire()
        ):
            raise reject("binding_mismatch", "Binding identity/version mismatch", 403, "permission")
        if grant.revision != expected_revision:
            raise reject("revision_conflict", "Binding revision changed", 409)
        if "read" not in grant.capabilities:
            raise reject("permission_denied", "Root does not allow read", 403, "permission")
        validate_contract("RelativePath", relative_path)
        # Check both path dialects, including drive-relative, ADS and device names on Windows.
        windows = PureWindowsPath(relative_path)
        parts = relative_path.replace("\\", "/").split("/")
        if (
            windows.drive
            or windows.root
            or ":" in relative_path
            or "\x00" in relative_path
            or any(part == ".." or part.endswith((".", " ")) for part in parts if part != ".")
            or isreserved(relative_path)
        ):
            raise reject("permission_denied", "Unsafe relative path", 403, "permission")
        try:
            root = grant.native_path.resolve(strict=True)
            stat = root.stat()
            if root != grant.native_path or (stat.st_dev, stat.st_ino) != grant.file_identity:
                raise ValueError("Root replaced")
            target = root.joinpath(*parts).resolve(strict=True)
            if not target.is_relative_to(root):
                raise ValueError("Link escape")
        except OSError, ValueError, RuntimeError:
            raise reject(
                "permission_denied", "Path is outside or unavailable", 403, "permission"
            ) from None
        return target

    def revoke(self, root_handle: str, *, expected_revision: int) -> RootGrant:
        # Trusted local adapter only; no public HTTP route is registered by this package.
        return self.repository.revoke(root_handle, expected_revision=expected_revision)
