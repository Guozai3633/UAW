"""Temporary development SQLite admission CAS, not a deployed execution ledger/D01."""

from collections.abc import Callable
from pathlib import Path

from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.workspace.ports import Admission
from uaw_runner.state import LocalState


class PersistentAdmissions:
    def __init__(self, path: Path) -> None:
        self.state = LocalState(path)
        with self.state.transaction() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS admissions (
                principal_id TEXT NOT NULL, device_id TEXT NOT NULL, command_id TEXT NOT NULL,
                attempt_id TEXT NOT NULL, fingerprint TEXT NOT NULL, state TEXT NOT NULL,
                revision INTEGER NOT NULL,
                PRIMARY KEY(principal_id,device_id,command_id))""")

    def reserve(self, principal_id: str, device_id: str, admission: Admission) -> Admission:
        return self.reserve_checked(principal_id, device_id, admission, check=lambda: None)

    def reserve_checked(
        self,
        principal_id: str,
        device_id: str,
        admission: Admission,
        *,
        check: Callable[[], None],
    ) -> Admission:
        for value in (principal_id, device_id, admission.command_id, admission.attempt_id):
            validate_contract("ID", value)
        validate_contract("Hash", admission.fingerprint)
        if admission.state != "admitted":
            raise reject("schema_invalid", "New admission must be admitted")
        key = (principal_id, device_id, admission.command_id)
        with self.state.transaction() as db:
            check()  # Deadline/cancellation after acquiring a potentially contended SQL lock.
            row = db.execute(
                """SELECT * FROM admissions
                WHERE principal_id=? AND device_id=? AND command_id=?""",
                key,
            ).fetchone()
            if row is not None:
                if row["fingerprint"] != admission.fingerprint:
                    raise reject("revision_conflict", "Command identity changed", 409)
                result = Admission(
                    row["command_id"], row["attempt_id"], row["fingerprint"], row["state"]
                )
            else:
                db.execute(
                    "INSERT INTO admissions VALUES (?,?,?,?,?,?,0)",
                    (*key, admission.attempt_id, admission.fingerprint, admission.state),
                )
                result = admission
            check()  # A failure rolls back an insert instead of leaving a stale admission.
            return result

    def cancel(
        self,
        principal_id: str,
        device_id: str,
        command_id: str,
        *,
        expected_revision: int,
    ) -> None:
        # Trusted internal cancellation owner only; no public request endpoint.
        with self.state.transaction() as db:
            result = db.execute(
                """UPDATE admissions SET state='cancelled', revision=revision+1
                WHERE principal_id=? AND device_id=? AND command_id=? AND revision=?""",
                (principal_id, device_id, command_id, expected_revision),
            )
            if result.rowcount != 1:
                raise reject("revision_conflict", "Admission revision changed", 409)
