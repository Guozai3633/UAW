"""Process-local component stores. No durable pairing/execution or D01 decision."""

from dataclasses import replace
from threading import RLock

from uaw.shared.errors import reject
from uaw.workspace.ports import Admission, RootGrant


class MemoryRootRepository:
    def __init__(self) -> None:
        self._roots: dict[str, RootGrant] = {}
        self._lock = RLock()

    def add(self, grant: RootGrant) -> RootGrant:
        with self._lock:
            if grant.root_handle in self._roots:
                raise reject("revision_conflict", "Root handle already exists", 409)
            self._roots[grant.root_handle] = grant
            return grant

    def get(self, root_handle: str) -> RootGrant:
        with self._lock:
            if root_handle not in self._roots:
                raise reject("permission_denied", "Root is not authorized", 403, "permission")
            return self._roots[root_handle]

    def revoke(self, root_handle: str, *, expected_revision: int) -> RootGrant:
        with self._lock:
            grant = self.get(root_handle)
            if grant.revision != expected_revision:
                raise reject("revision_conflict", "Binding revision changed", 409)
            if not grant.revoked:
                grant = replace(grant, revoked=True, revision=grant.revision + 1)
                self._roots[root_handle] = grant
            return grant


class MemoryAdmissionRepository:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str, str], Admission] = {}
        self._lock = RLock()

    def reserve(self, principal_id: str, device_id: str, admission: Admission) -> Admission:
        key = (principal_id, device_id, admission.command_id)
        with self._lock:
            previous = self._records.get(key)
            if previous is not None:
                if previous.fingerprint != admission.fingerprint:
                    raise reject("revision_conflict", "Command identity changed", 409)
                return previous
            self._records[key] = admission
            return admission

    def cancel(self, principal_id: str, device_id: str, command_id: str) -> Admission:
        # Internal store transition only; trusted Run adapter owns cancellation authority.
        key = (principal_id, device_id, command_id)
        with self._lock:
            if key not in self._records:
                raise reject("stale_resource", "Command is absent", 404)
            record = replace(self._records[key], state="cancelled")
            self._records[key] = record
            return record
