"""Native consumed-selection/grant backend for the published opaque root source port.

No incoming command or path establishes ownership; current channel mapping is independent.
"""

import asyncio
import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from uaw.shared.contracts import JsonObject, Principal, Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.runner_signatures import signing_bytes
from uaw.shared.schema import validate_contract
from uaw.workspace.binding import RootBindings, aware
from uaw.workspace.contracts import RootSelection
from uaw.workspace.ports import (
    CurrentKeyDirectory,
    RootGrant,
    RootGrantLookup,
    RunnerPrincipalMappingPort,
)
from uaw_runner.keys import Ed25519SignatureAdapter
from uaw_runner.pairing import LocalRoots
from uaw_runner.protocol import timestamp
from uaw_runner.state import LocalState


def grant_data(grant: RootGrant) -> dict[str, Any]:
    values = asdict(grant)
    values.update(
        workspace_ref=grant.workspace_ref.wire(),
        owner=grant.owner.wire() if grant.owner else None,
        native_path=str(grant.native_path),
        file_identity=list(grant.file_identity),
        capabilities=sorted(grant.capabilities),
        expires_at=grant.expires_at.isoformat() if grant.expires_at else None,
        confirmation_expires_at=(
            grant.confirmation_expires_at.isoformat() if grant.confirmation_expires_at else None
        ),
    )
    return values


class PersistentRootGrants:
    """Explicit local development native directory, no D01 choice or public wire records."""

    def __init__(self, path: Path) -> None:
        self.state = LocalState(path)
        with self.state.transaction() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS root_grants (
                root_handle TEXT PRIMARY KEY, principal_id TEXT NOT NULL, device_id TEXT NOT NULL,
                workspace_pin TEXT NOT NULL, grant_data TEXT NOT NULL)""")

    @staticmethod
    def _decode(data: str) -> RootGrant:
        try:
            values = json.loads(data)
            values["workspace_ref"] = Ref.model_validate_json(json.dumps(values["workspace_ref"]))
            values["owner"] = (
                Principal.model_validate_json(json.dumps(values["owner"]))
                if values.get("owner")
                else None
            )
            values["native_path"] = Path(values["native_path"])
            identity = values["file_identity"]
            if len(identity) != 2 or any(type(v) is not int or v < 0 for v in identity):
                raise ValueError("Invalid directory identity")
            values["file_identity"] = tuple(identity)
            values["capabilities"] = frozenset(values["capabilities"])
            for field in ("expires_at", "confirmation_expires_at"):
                values[field] = timestamp(values[field]) if values.get(field) else None
            validate_contract("Revision", values["revision"])
            if type(values["revoked"]) is not bool:
                raise ValueError("Invalid revocation")
            return RootGrant(**values)
        except ValueError, TypeError, KeyError:
            raise reject("schema_invalid", "Persisted root grant is invalid") from None

    def add(self, grant: RootGrant) -> RootGrant:
        # Every production-capable grant must retain consumed-source metadata.
        if (
            grant.owner is None
            or grant.expires_at is None
            or grant.confirmation_expires_at is None
            or not grant.selection_ticket_id
            or not grant.selection_key_id
            or not grant.selection_signature
            or grant.owner.kind != "user"
            or grant.owner.id != grant.principal_id
            or not grant.capabilities
            or not grant.capabilities <= {"read"}
            or grant.revoked
            or grant.revision != 0
            or not grant.native_path.is_absolute()
        ):
            raise reject(
                "permission_denied", "Proven bounded root grant required", 403, "permission"
            )
        validate_contract("Principal", grant.owner.wire())
        validate_contract("Ref", grant.workspace_ref.wire())
        for value in (
            grant.root_handle,
            grant.device_id,
            grant.principal_id,
            grant.selection_ticket_id,
            grant.selection_key_id,
        ):
            validate_contract("ID", value)
        with self.state.transaction() as db:
            db.execute(
                "INSERT INTO root_grants VALUES (?,?,?,?,?)",
                (
                    grant.root_handle,
                    grant.principal_id,
                    grant.device_id,
                    json.dumps(grant.workspace_ref.wire(), sort_keys=True),
                    json.dumps(grant_data(grant), ensure_ascii=False, sort_keys=True),
                ),
            )
        return grant

    def get(self, root_handle: str) -> RootGrant:
        with self.state.transaction() as db:
            row = db.execute(
                "SELECT grant_data FROM root_grants WHERE root_handle=?", (root_handle,)
            ).fetchone()
            if row is None:
                raise reject("permission_denied", "Root grant unavailable", 403, "permission")
            return self._decode(row["grant_data"])

    def find(self, *, principal_id: str, device_id: str, workspace_ref: Ref) -> RootGrant:
        with self.state.transaction() as db:
            rows = db.execute(
                """SELECT grant_data FROM root_grants
                WHERE principal_id=? AND device_id=? AND workspace_pin=?""",
                (principal_id, device_id, json.dumps(workspace_ref.wire(), sort_keys=True)),
            ).fetchall()
            if len(rows) != 1:
                raise reject(
                    "permission_denied", "One actual root binding required", 403, "permission"
                )
            return self._decode(rows[0]["grant_data"])

    def revoke(self, root_handle: str, *, expected_revision: int) -> RootGrant:
        with self.state.transaction() as db:
            row = db.execute(
                "SELECT grant_data FROM root_grants WHERE root_handle=?", (root_handle,)
            ).fetchone()
            if row is None:
                raise reject("permission_denied", "Root grant unavailable", 403, "permission")
            grant = self._decode(row["grant_data"])
            if grant.revision != expected_revision:
                raise reject("revision_conflict", "Root grant revision changed", 409)
            if not grant.revoked:
                grant = replace(grant, revoked=True, revision=grant.revision + 1)
                db.execute(
                    "UPDATE root_grants SET grant_data=? WHERE root_handle=?",
                    (
                        json.dumps(grant_data(grant), ensure_ascii=False, sort_keys=True),
                        root_handle,
                    ),
                )
            return grant


class NativeRootSource:
    def __init__(
        self,
        bindings: RootBindings,
        *,
        grants: RootGrantLookup | None,
        selections: LocalState | None,
        native_roots: LocalRoots | None,
        mapping: RunnerPrincipalMappingPort | None,
        directory: CurrentKeyDirectory | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if grants is not None and bindings.repository is not grants:
            raise ValueError("Root bindings and lookup require the same actual repository")
        if selections is not None and isinstance(grants, PersistentRootGrants):
            if selections.path == grants.state.path:
                raise ValueError("Control selections and native grants need separate files")
        self.bindings, self.grants, self.selections = bindings, grants, selections
        self.native_roots, self.mapping, self.directory = native_roots, mapping, directory
        self.clock = clock or (lambda: datetime.now(UTC))

    async def _owner(self, actor: Principal, device_id: str) -> Principal:
        if self.mapping is None:
            raise CapabilityUnavailable("runner.current_principal_mapping")
        owner = await self.mapping.owner(authenticated_principal=actor, device_id=device_id)
        if not isinstance(owner, Principal):
            raise reject("dependency_protocol_invalid", "Current root owner source is invalid", 503)
        owner = Principal.model_validate_json(json.dumps(owner.wire()))
        if (
            owner.kind != "user"
            or actor.kind not in ("user", "runner")
            or (actor.kind == "user" and actor.wire() != owner.wire())
        ):
            raise reject(
                "permission_denied", "Actual root owner/channel differs", 403, "permission"
            )
        return owner

    def _read(self, device_id: str, workspace_ref: Ref, owner: Principal) -> JsonObject:
        if (
            self.grants is None
            or self.selections is None
            or self.native_roots is None
            or self.directory is None
        ):
            raise CapabilityUnavailable("runner.consumed_native_root_source")
        grant = self.grants.find(
            principal_id=owner.id, device_id=device_id, workspace_ref=workspace_ref
        )
        if (
            grant.owner is None
            or grant.owner.wire() != owner.wire()
            or grant.expires_at is None
            or grant.confirmation_expires_at is None
            or not grant.selection_ticket_id
            or not grant.selection_key_id
            or not grant.selection_signature
        ):
            raise reject(
                "permission_denied",
                "Root grant lacks actual proof/owner/deadline",
                403,
                "permission",
            )
        now = aware(self.clock())
        if grant.revoked:
            raise reject("permission_denied", "Native root grant revoked", 403, "permission")
        if min(grant.expires_at, grant.confirmation_expires_at) <= now:
            # Durable revocation tombstone prevents expiry observations being reversed by a
            # subsequent wall-clock rollback. No infinite old-grant fallback is allowed.
            self.bindings.repository.revoke(grant.root_handle, expected_revision=grant.revision)
            raise reject("deadline_exceeded", "Native root grant expired", 410, "timeout")
        ticket, confirmation_hash, confirmation_deadline = self.selections.consumed_root(
            grant.selection_ticket_id, now=now
        )
        key = self.directory.lookup(ticket.key_id, device_id=device_id)
        if (
            key.revoked
            or key.role != "device"
            or key.device_id != device_id
            or key.key_id != ticket.key_id
            or key.public_bytes != ticket.public_bytes
        ):
            raise reject(
                "permission_denied", "Current native selection key differs", 403, "permission"
            )
        expected_hash = hashlib.sha256(
            signing_bytes(ticket.document(), ticket.device_id, ticket.key_id, "pairing-proof")
        ).hexdigest()
        if (
            ticket.principal_id != owner.id
            or ticket.device_id != device_id
            or ticket.root_handle != grant.root_handle
            or ticket.key_id != grant.selection_key_id
            or ticket.expires_at != grant.expires_at
            or confirmation_deadline != grant.confirmation_expires_at
            or confirmation_hash != expected_hash
            or not Ed25519SignatureAdapter(self.directory).verify_document(
                {**ticket.document(), "signature": grant.selection_signature},
                device_id=device_id,
                domain="root-selection",
            )
        ):
            raise reject(
                "permission_denied", "Actual consumed root proof differs", 403, "permission"
            )
        path = self.native_roots.current(ticket)
        if path != grant.native_path:
            raise reject(
                "permission_denied", "Actual native root binding differs", 403, "permission"
            )
        self.bindings.check_scope(
            root_handle=grant.root_handle,
            principal_id=owner.id,
            device_id=device_id,
            workspace_ref=workspace_ref,
            expected_revision=grant.revision,
            relative_path=".",
            now=aware(self.clock()),
        )
        # Final local re-read catches revoke/replacement while inspecting the native directory.
        if self.bindings.repository.get(grant.root_handle) != grant:
            raise reject("revision_conflict", "Native root grant changed", 409)
        current_ticket, current_hash, current_deadline = self.selections.consumed_root(
            grant.selection_ticket_id, now=aware(self.clock())
        )
        if (
            self.directory.lookup(ticket.key_id, device_id=device_id) != key
            or current_ticket != ticket
            or current_hash != confirmation_hash
            or current_deadline != confirmation_deadline
            or self.native_roots.current(ticket) != path
            or not Ed25519SignatureAdapter(self.directory).verify_document(
                {**ticket.document(), "signature": grant.selection_signature},
                device_id=device_id,
                domain="root-selection",
            )
        ):
            raise reject("permission_denied", "Native selection/key changed", 403, "permission")
        result: JsonObject = {
            "owner": owner.wire(),
            "device_id": device_id,
            "workspace_ref": workspace_ref.wire(),
            "root_handle": grant.root_handle,
            "binding_revision": grant.revision,
            "allowed_actions": ["file.read", "file.list"],
            "expires_at": min(grant.expires_at, confirmation_deadline).isoformat(),
        }
        validate_contract("RunnerRootSnapshot", result)
        return result

    async def current(
        self, device_id: str, workspace_ref: Ref, ctx: TrustedExecutionContext
    ) -> JsonObject:
        validate_contract("ID", device_id)
        workspace = Ref.model_validate_json(json.dumps(workspace_ref.wire()))
        context = TrustedExecutionContext.model_validate_json(json.dumps(ctx.wire()))
        if workspace.kind != "workspace" or workspace.wire() not in [
            r.wire() for r in context.scope.resource_refs
        ]:
            raise reject(
                "permission_denied", "Workspace is outside trusted scope", 403, "permission"
            )

        def deadline() -> None:
            if timestamp(context.deadline) <= aware(self.clock()):
                raise reject("deadline_exceeded", "Root source request expired", 410, "timeout")

        deadline()
        owner = await self._owner(context.principal, device_id)
        deadline()
        first = await asyncio.to_thread(self._read, device_id, workspace, owner)
        deadline()
        second_owner = await self._owner(context.principal, device_id)
        deadline()
        if second_owner.wire() != owner.wire():
            raise reject("permission_denied", "Root owner changed", 403, "permission")
        second = await asyncio.to_thread(self._read, device_id, workspace, second_owner)
        deadline()
        if second != first or timestamp(str(second["expires_at"])) <= aware(self.clock()):
            raise reject("revision_conflict", "Current root source changed", 409)
        return second

    async def bind(
        self,
        selection: RootSelection,
        workspace_ref: Ref,
        *,
        device_id: str,
        authenticated_principal: Principal,
    ) -> None:
        # Trusted native adapter only. No path/owner/approval is accepted from a command.
        if (
            self.grants is None
            or self.selections is None
            or self.native_roots is None
            or self.directory is None
        ):
            raise CapabilityUnavailable("runner.consumed_native_root_source")
        owner = await self._owner(authenticated_principal, device_id)
        await asyncio.to_thread(
            self.bindings.bind,
            selection,
            principal_id=owner.id,
            device_id=device_id,
            workspace_ref=workspace_ref,
            capabilities=frozenset({"read"}),
            now=aware(self.clock()),
            owner=owner,
        )
        second_owner = await self._owner(authenticated_principal, device_id)
        if owner.wire() != second_owner.wire():
            raise reject(
                "permission_denied", "Root owner changed during binding", 403, "permission"
            )
        await asyncio.to_thread(self._read, device_id, workspace_ref, owner)
