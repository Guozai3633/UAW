"""One deterministic installed-channel expiry from the original active enrollment."""

import json
from datetime import UTC, datetime, timedelta

from uaw_runner.ipc.channel_source import ConnectionRegistry
from uaw_runner.ipc.sessions import AuthenticatedPipeSession

from uaw.run.enrollment import Payload, RunnerEnrollments, fixed_ref
from uaw.shared.contracts import JsonObject, Ref
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.workspace.contracts import RunnerChannelSnapshot


class InstalledConnectionRegistry(ConnectionRegistry):
    def __init__(self, enrollment: Payload, *, lifetime_seconds: float) -> None:
        super().__init__(max_connections=1)
        validate_contract("RunnerEnrollmentRecord", enrollment)
        if lifetime_seconds not in (60.0, 120.0) or enrollment["state"] != "active":
            raise ValueError("Original active installed enrollment and closed lifetime required")
        if enrollment["pairing_ref"] != fixed_ref(
            "content",
            enrollment["id"],
            {k: v for k, v in enrollment.items() if k != "pairing_ref"},
        ):
            raise ValueError("Original active pairing digest required")
        self.pairing_ref = Ref.model_validate(enrollment["pairing_ref"])
        # Both processes observe identical persisted bytes. Starting before the
        # handshake makes this no later than either local session deadline.
        self.original_expiry = min(
            RunnerEnrollments.instant(enrollment["created_at"])
            + timedelta(seconds=lifetime_seconds),
            RunnerEnrollments.instant(enrollment["proof_document"]["expires_at"]),
        )

    def _snapshot(
        self,
        session: AuthenticatedPipeSession,
        channel_ref: Ref,
        *,
        device_id: str,
    ) -> RunnerChannelSnapshot:
        snapshot = super()._snapshot(session, channel_ref, device_id=device_id)
        if (
            snapshot.pairing_ref != self.pairing_ref
            or self.original_expiry <= datetime.now(UTC)
            or self.original_expiry > session.expires_at
        ):
            raise reject("installed_channel_expired", "Original channel deadline differs", 410)
        wire = snapshot.wire()
        wire["expires_at"] = self.original_expiry.isoformat()
        return RunnerChannelSnapshot.model_validate_json(json.dumps(wire))

    async def read(self, channel_ref: Ref, *, device_id: str) -> JsonObject:
        session = await self.session(channel_ref, device_id=device_id)
        # session() has just checked both current peers after its lock await.
        # Snapshot creation has no await/IO, so no authority-changing wait lies
        # between that check and this return. Expiry is checked by _snapshot.
        return self._snapshot(session, channel_ref, device_id=device_id).wire()
