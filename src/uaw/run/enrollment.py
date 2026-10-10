"""Account/OS/key proof registration. Pending enrollment grants no file authority."""

import asyncio
import base64
import hashlib
import json
import secrets
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, Protocol

from sqlalchemy import DateTime, select

from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore, parameter_hash
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore, timestamp
from uaw.shared.contracts import Principal, Ref, RequestMeta
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.runner_signatures import Domain, VerificationKey, verify
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreConflict, StoreMissing

Payload = dict[str, Any]
ENROLLMENTS = "runner.enrollments"
CANDIDATES = "runner.enrollment.candidates"
Authentication = Callable[[Principal], Awaitable[Payload]]


class EnrollmentCandidateSourcePort(Protocol):
    async def current(self, candidate_id: str, *, owner: Principal) -> Payload:
        """RunnerEnrollmentCandidate from actual protected launcher/OS observations.

        Never infer account ownership from PID, public key or HTTP candidate fields.
        Current processes and role keys must still be live and equal to this snapshot.
        """
        ...


class NativePairingEvidencePort(Protocol):
    async def current(self, proof_document: Payload, *, owner: Principal) -> Payload:
        """RunnerNativePairingEvidence from the native owning journal and current keys.

        Both original signatures and actual human confirmation must already exist.
        A timeout or missing evidence is unavailable, never an implicit approval.
        """
        ...


def fixed_ref(kind: str, key: str, value: Payload) -> Payload:
    return {"kind": kind, "id": key, "version": "1", "content_hash": parameter_hash(value)}


def frozen(value: Payload) -> Payload:
    result: Payload = json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
    return result


class RunnerEnrollments:
    def __init__(
        self,
        records: PostgresRecordStore,
        controller: Principal,
        *,
        authenticate: Authentication | None,
        candidates: EnrollmentCandidateSourcePort | None = None,
        native: NativePairingEvidencePort | None = None,
        clock: Callable[[], datetime] | None = None,
        capacity: int = 32,
    ) -> None:
        if controller.kind != "service":
            raise ValueError("Independent authenticated control service required")
        if not 1 <= capacity <= 64:
            raise ValueError("Enrollment capacity must be 1..64")
        self.capacity = capacity
        self.records, self.controller = records, controller
        self.authentication, self.candidates, self.native = authenticate, candidates, native
        self.clock = clock or (lambda: datetime.now(UTC))
        self.transactions = TransactionalStore(records.database)
        # Serializes trusted local launch provisioning; never held by SQL transactions.
        self.local_launch_lock = asyncio.Lock()

    def now(self) -> datetime:
        value = self.clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Enrollment clock must be timezone aware")
        return value

    async def actor(self, owner: Principal) -> Payload:
        if owner.kind != "user" or not owner.auth_session_id.startswith("web-session-"):
            raise reject("enrollment_web_user_required", "Current Web user required", 403)
        if self.authentication is None:
            raise CapabilityUnavailable("enrollment.current_web_authentication")
        current = await self.authentication(owner)
        if (
            current["principal"] != owner.wire()
            or self.instant(current["expires_at"]) <= self.now()
        ):
            raise reject("enrollment_user_changed", "Current Web identity differs", 403)
        return current

    @staticmethod
    def instant(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise reject("enrollment_source_invalid", "Aware source deadline required", 503)
        return parsed

    @staticmethod
    def peer(peer: Payload, role: str) -> None:
        validate_contract("RunnerEnrollmentPeer", peer)
        if peer["role"] != role or peer["actor"]["kind"] != "runner":
            raise reject("enrollment_role_denied", "Exact control/device actor role required", 403)
        pin = Ref.model_validate(peer["key_ref"])
        if (
            pin.kind != "content"
            or pin.id != peer["key_id"]
            or not pin.content_hash
            or pin.location
            or pin.access_scope
        ):
            raise reject("enrollment_key_pin_denied", "Fixed current role key required", 403)
        raw = base64.b64decode(peer["public_key"], validate=True)
        if len(raw) != 32 or base64.b64encode(raw).decode() != peer["public_key"]:
            raise reject("enrollment_key_invalid", "Canonical Ed25519 public key required", 403)
        if pin.content_hash != hashlib.sha256(raw).hexdigest():
            raise reject(
                "enrollment_key_pin_denied", "Actual current public key digest differs", 403
            )

    async def candidate(self, key: str, owner: Principal) -> Payload:
        validate_contract("ID", key)
        if self.candidates is None:
            raise CapabilityUnavailable("enrollment.protected_candidate_source")
        async with asyncio.timeout(10):
            value = frozen(await self.candidates.current(key, owner=owner))
        validate_contract("RunnerEnrollmentCandidate", value)
        if value["id"] != key or value["owner"] != owner.wire():
            raise reject(
                "enrollment_candidate_owner_denied", "Independent candidate owner differs", 403
            )
        self.peer(value["control"], "control")
        self.peer(value["device"], "device")
        if (
            value["control"]["identity"] == value["device"]["identity"]
            or value["control"]["identity"]["pid"] == value["device"]["identity"]["pid"]
            or any(
                value["control"]["identity"][k] != value["device"]["identity"][k]
                for k in ("user_sid", "logon_sid")
            )
            or value["control"]["public_key"] == value["device"]["public_key"]
            or value["control"]["key_id"] == value["device"]["key_id"]
            or self.instant(value["expires_at"]) <= self.now()
        ):
            raise reject(
                "enrollment_candidate_denied", "Independent process/key/expiry differs", 403
            )
        return value

    async def begin(self, owner: Principal, candidate_id: str, meta: RequestMeta) -> Payload:
        current = await self.actor(owner)
        candidate = await self.candidate(candidate_id, owner)
        key = "enrollment-" + parameter_hash({"owner": owner.wire(), "request_id": meta.request_id})
        candidate_ref = fixed_ref("content", candidate_id, candidate)
        deadline = min(
            self.now() + timedelta(minutes=5),
            self.instant(current["expires_at"]),
            self.instant(candidate["expires_at"]),
        )
        document = {
            "protocol": "uaw-enrollment-v1",
            "enrollment_id": key,
            "candidate_ref": candidate_ref,
            "owner": owner.wire(),
            "device_id": candidate["device_id"],
            "control": candidate["control"],
            "device": candidate["device"],
            "nonce": secrets.token_urlsafe(32),
            "expires_at": deadline.isoformat(),
        }
        if await self.candidate(candidate_id, owner) != candidate:
            raise reject("enrollment_candidate_changed", "Candidate changed while registering", 412)

        async def write(tx: RecordTransaction) -> Payload:
            # Fresh authentication after waiting; never store a bearer/cookie/code/private key.
            await self.actor(owner)
            if self.now() >= deadline:
                raise reject(
                    "enrollment_candidate_changed", "Candidate changed while registering", 412
                )
            active = list(
                await tx.session.scalars(
                    select(RecordRow.resource_id)
                    .where(
                        RecordRow.principal_id == self.controller.id,
                        RecordRow.namespace == ENROLLMENTS,
                        RecordRow.deleted.is_(False),
                        RecordRow.payload["proof_document"]["owner"]["id"].astext == owner.id,
                        RecordRow.payload["state"].astext.in_(("pending", "active")),
                        RecordRow.payload["proof_document"]["expires_at"].astext.cast(
                            DateTime(timezone=True)
                        )
                        > self.now(),
                    )
                    .limit(self.capacity)
                )
            )
            if len(active) >= self.capacity:
                raise reject("enrollment_capacity_full", "Current enrollment capacity reached", 409)
            resource_id = "candidate-" + parameter_hash(
                {"owner": owner.wire(), "candidate": candidate_id}
            )
            try:
                previous = await tx.load(CANDIDATES, resource_id)
            except StoreMissing:
                await tx.write(CANDIDATES, resource_id, "RunnerEnrollmentCandidate", candidate)
            else:
                if previous.payload != candidate:
                    raise StoreConflict("enrollment_candidate_changed")
            value = {
                "id": key,
                "revision": 1,
                "state": "pending",
                "proof_document": document,
                "created_at": timestamp(),
            }
            await tx.write(ENROLLMENTS, key, "RunnerEnrollmentRecord", value)
            return value

        # Idempotency uses caller request and fixed candidate. Fresh random nonce is
        # discarded on replay; the original persisted nonce/deadline is returned.
        value = await self.transactions.execute(
            self.controller,
            "enrollment:" + owner.id,
            meta,
            {"action": "begin", "owner": owner.wire(), "candidate": candidate},
            write,
        )
        await self.actor(owner)
        await self.original(value, owner)
        return value

    async def original(self, value: Payload, owner: Principal) -> Payload:
        validate_contract("RunnerEnrollmentRecord", value)
        document = value["proof_document"]
        if document["owner"] != owner.wire():
            raise reject("enrollment_owner_denied", "Original Web session required", 403)
        if (
            value["state"] not in ("pending", "active")
            or self.instant(document["expires_at"]) <= self.now()
        ):
            raise reject("enrollment_inactive", "Enrollment revoked or expired", 409)
        source = await self.candidate(document["candidate_ref"]["id"], owner)
        if fixed_ref("content", source["id"], source) != document["candidate_ref"] or any(
            source[k] != document[k] for k in ("control", "device", "device_id")
        ):
            raise reject("enrollment_source_changed", "Original process/key source changed", 412)
        return source

    async def get(self, owner: Principal, key: str) -> Payload:
        await self.actor(owner)
        row = await self.records.get(self.controller, ENROLLMENTS, key)
        value = row.payload
        if (
            row.schema_name != "RunnerEnrollmentRecord"
            or value["id"] != key
            or value["revision"] != row.revision
        ):
            raise reject(
                "enrollment_record_changed", "Enrollment record identity/version differs", 412
            )
        await self.original(value, owner)
        if value["state"] == "active":
            if value["pairing_ref"] != fixed_ref(
                "content", key, {k: v for k, v in value.items() if k != "pairing_ref"}
            ):
                raise reject(
                    "enrollment_pairing_pin_changed", "Original pairing digest differs", 412
                )
            evidence = await self.proof(value["proof_document"], owner)
            if any(
                evidence[k] != value[k]
                for k in ("confirmation_ref", "device_proof", "control_proof")
            ):
                raise reject(
                    "enrollment_native_source_changed", "Original native proof changed", 412
                )
        await self.actor(owner)
        return value

    async def challenge(self, owner: Principal, key: str) -> Payload:
        """Internal native-source read, not pairing authority or public file access.

        This path checks original account/candidate/deadline but never calls the
        native outcome Reader, avoiding get -> outcome -> get recursion.
        """
        await self.actor(owner)
        row = await self.records.get(self.controller, ENROLLMENTS, key)
        if (
            row.schema_name != "RunnerEnrollmentRecord"
            or row.payload["id"] != key
            or row.payload["revision"] != row.revision
        ):
            raise reject("enrollment_record_changed", "Original challenge identity differs", 412)
        await self.original(row.payload, owner)
        await self.actor(owner)
        return frozen(row.payload["proof_document"])

    async def proof(self, document: Payload, owner: Principal) -> Payload:
        if self.native is None:
            raise CapabilityUnavailable("enrollment.native_human_evidence")
        async with asyncio.timeout(10):
            evidence = frozen(await self.native.current(frozen(document), owner=owner))
        validate_contract("RunnerNativePairingEvidence", evidence)
        if (
            evidence["owner"] != owner.wire()
            or evidence["enrollment_id"] != document["enrollment_id"]
            or evidence["device_id"] != document["device_id"]
            or evidence["device_identity"] != document["device"]["identity"]
            or evidence["proof_document_hash"] != parameter_hash(document)
            or not self.now()
            < self.instant(evidence["expires_at"])
            <= self.instant(document["expires_at"])
        ):
            raise reject(
                "enrollment_native_binding_denied", "Original native confirmation differs", 403
            )
        pin = Ref.model_validate(evidence["confirmation_ref"])
        if (
            pin.kind != "check"
            or pin.version != "1"
            or not pin.content_hash
            or pin.location
            or pin.access_scope
        ):
            raise reject(
                "enrollment_native_pin_denied", "Fixed native decision evidence required", 403
            )
        roles: tuple[tuple[Literal["control", "device"], Domain], ...] = (
            ("control", "command"),
            ("device", "pairing-proof"),
        )
        for role, domain in roles:
            peer = document[role]
            key = VerificationKey(
                peer["key_id"],
                document["device_id"],
                base64.b64decode(peer["public_key"], validate=True),
                role,
            )
            if not verify(document, evidence[role + "_proof"], key, domain):
                raise reject("enrollment_key_proof_denied", "Original role-key proof differs", 403)
        return evidence

    async def complete(self, owner: Principal, key: str, meta: RequestMeta) -> Payload:
        before = await self.get(owner, key)
        evidence = await self.proof(before["proof_document"], owner)
        await self.actor(owner)
        await self.original(before, owner)
        if await self.proof(before["proof_document"], owner) != evidence:
            raise reject("enrollment_native_source_changed", "Native evidence changed", 412)

        async def write(tx: RecordTransaction) -> Payload:
            row = await tx.load(ENROLLMENTS, key)
            if (
                row.payload != before
                or before["state"] != "pending"
                or meta.expected_revision != row.revision
            ):
                raise StoreConflict("enrollment_revision_changed")
            await self.actor(owner)
            # No launcher/native IPC under the SQL lock. The CAS fixes original
            # proof bytes; every subsequent read rechecks those live sources.
            if self.now() >= min(
                self.instant(before["proof_document"]["expires_at"]),
                self.instant(evidence["expires_at"]),
            ):
                raise reject(
                    "enrollment_confirmation_expired", "Native evidence expired before commit", 409
                )
            value = {
                **before,
                "revision": row.revision + 1,
                "state": "active",
                "confirmation_ref": evidence["confirmation_ref"],
                "device_proof": evidence["device_proof"],
                "control_proof": evidence["control_proof"],
            }
            value["pairing_ref"] = fixed_ref(
                "content", key, {k: v for k, v in value.items() if k != "pairing_ref"}
            )
            await tx.write(ENROLLMENTS, key, "RunnerEnrollmentRecord", value, row.revision)
            return value

        result = await self.transactions.execute(
            self.controller,
            "enrollment:" + owner.id,
            meta,
            {
                "action": "complete",
                "owner": owner.wire(),
                "id": key,
                "expected": meta.expected_revision,
            },
            write,
        )
        if await self.get(owner, key) != result:
            raise reject("enrollment_commit_changed", "Current pairing differs after commit", 412)
        return result

    async def revoke(self, owner: Principal, key: str, meta: RequestMeta) -> Payload:
        await self.actor(owner)

        async def write(tx: RecordTransaction) -> Payload:
            row = await tx.load(ENROLLMENTS, key)
            if row.payload["proof_document"]["owner"] != owner.wire():
                raise reject("enrollment_owner_denied", "Original Web session required", 403)
            if meta.expected_revision != row.revision:
                raise StoreConflict()
            value = {**row.payload, "revision": row.revision + 1, "state": "revoked"}
            await tx.write(ENROLLMENTS, key, "RunnerEnrollmentRecord", value, row.revision)
            return value

        return await self.transactions.execute(
            self.controller,
            "enrollment:" + owner.id,
            meta,
            {
                "action": "revoke",
                "id": key,
                "owner": owner.wire(),
                "expected": meta.expected_revision,
            },
            write,
        )
