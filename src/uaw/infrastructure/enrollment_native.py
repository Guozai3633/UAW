"""Separate first native enrollment decision; no pending peer or root grant fabricated."""

import asyncio
import base64
import hashlib
import time
from datetime import UTC, datetime
from threading import Event

from uaw_runner.ipc.windows_pipe import WindowsApi
from uaw_runner.keys import ProtectedSigner
from uaw_runner.native_dialog import NativePrompt, WindowsNativeDialog

from uaw.infrastructure.db.records import parameter_hash
from uaw.run.enrollment import Payload, RunnerEnrollments, fixed_ref
from uaw.shared.contracts import Principal
from uaw.shared.errors import reject
from uaw.shared.runner_signatures import verify
from uaw.shared.stores import StoreMissing
from uaw.workspace.ports import CurrentKeyDirectory

JOURNAL = "runner.enrollment.native.decisions"


class EnrollmentPrompt(NativePrompt):
    def text(self) -> str:
        return (
            f"UAW 本机账号与设备确认\n账号：{self.account}\n设备：{self.device}\n"
            f"范围：仅绑定上述账号与设备身份；不授予目录、写入、安装或执行权限\n"
            f"有效至：{self.expires}\n挑战摘要：{self.challenge}\n"
            "目录读取需要后续单独选择和确认；取消不会绑定。"
        )


class WindowsEnrollmentConfirmation:
    """Trusted device-side assembly supplies handles and the original control proof.

    This producer is intentionally separate from the get/current outcome Reader.
    Only confirm opens UI. No API accepts an approved flag, path or private key.
    It must run in the original independently observed device process.
    """

    def __init__(
        self,
        service: RunnerEnrollments,
        directory: CurrentKeyDirectory,
        signer: ProtectedSigner,
        *,
        device_credential_handle: str,
        timeout_seconds: float = 60,
    ) -> None:
        if not 0 < timeout_seconds <= 120 or signer.directory is not directory:
            raise ValueError("Original current directory and bounded timeout required")
        self.service, self.directory, self.signer = service, directory, signer
        self.handle, self.timeout = device_credential_handle, timeout_seconds
        self.busy = False

    async def checked(self, owner: Principal, key: str, control_proof: str) -> Payload:
        document = await self.service.challenge(owner, key)
        actual = await asyncio.to_thread(WindowsApi().current)
        expected = document["device"]["identity"]
        if expected != {
            "pid": actual.pid,
            "created": str(actual.created),
            "user_sid": actual.user_sid,
            "logon_sid": actual.logon_sid,
        }:
            raise reject(
                "enrollment_native_instance_denied", "Original device OS instance differs", 403
            )
        keys = {}
        for role in ("control", "device"):
            peer = document[role]
            current = await asyncio.to_thread(
                self.directory.lookup, peer["key_id"], device_id=document["device_id"]
            )
            if (
                current.revoked
                or current.role != role
                or current.device_id != document["device_id"]
                or current.key_id != peer["key_id"]
                or current.public_bytes != base64.b64decode(peer["public_key"], validate=True)
                or hashlib.sha256(current.public_bytes).hexdigest()
                != peer["key_ref"]["content_hash"]
            ):
                raise reject(
                    "enrollment_native_key_denied", "Original current role key differs", 403
                )
            keys[role] = current
        if not verify(document, control_proof, keys["control"], "command"):
            raise reject(
                "enrollment_control_proof_denied", "Original control proof is invalid", 403
            )
        await self.signer.check_private(
            device_id=document["device_id"],
            key_id=document["device"]["key_id"],
            credential_handle=self.handle,
        )
        if await self.service.challenge(owner, key) != document:
            raise reject("enrollment_native_challenge_changed", "Original challenge changed", 412)
        return document

    async def confirm(self, owner: Principal, enrollment_id: str, *, control_proof: str) -> Payload:
        if self.busy:
            raise reject("enrollment_native_busy", "One native enrollment decision at a time", 409)
        self.busy = True
        stopped, stop_watch = Event(), asyncio.Event()
        work = monitor = None
        try:
            async with asyncio.timeout(self.timeout):
                document = await self.checked(owner, enrollment_id, control_proof)
                document_hash = parameter_hash(document)
                seconds = min(
                    self.timeout,
                    (
                        datetime.fromisoformat(document["expires_at"].replace("Z", "+00:00"))
                        - datetime.now(UTC)
                    ).total_seconds(),
                )
                # Existing actual Windows dialog defaults to cancel. This stage binds
                # accounts/keys only; a later separate directory decision grants roots.
                try:
                    await self.service.records.get(self.service.controller, JOURNAL, enrollment_id)
                except StoreMissing:
                    pass
                else:
                    raise reject(
                        "enrollment_native_already_decided",
                        "Read the original decision; do not reopen UI",
                        409,
                    )
                prompt = EnrollmentPrompt(
                    owner.id, document["device_id"], document["expires_at"], document_hash, False
                )
                work = asyncio.create_task(
                    asyncio.to_thread(
                        WindowsNativeDialog().show, prompt, stopped, time.monotonic() + seconds
                    )
                )

                async def watch() -> None:
                    while not stop_watch.is_set():
                        await asyncio.sleep(0.1)
                        if (
                            not stop_watch.is_set()
                            and await self.checked(owner, enrollment_id, control_proof) != document
                        ):
                            raise reject(
                                "enrollment_native_challenge_changed",
                                "Current relationship changed",
                                412,
                            )

                monitor = asyncio.create_task(watch())
                done, _ = await asyncio.wait((work, monitor), return_when=asyncio.FIRST_COMPLETED)
                if monitor in done:
                    await monitor
                await asyncio.shield(
                    work
                )  # refusal/timeout propagate; None means explicit native Yes
                stop_watch.set()
                await monitor
                if await self.checked(owner, enrollment_id, control_proof) != document:
                    raise reject(
                        "enrollment_native_challenge_changed", "Original challenge changed", 412
                    )
                device_proof = await self.signer.sign_document(
                    document,
                    device_id=document["device_id"],
                    key_id=document["device"]["key_id"],
                    credential_handle=self.handle,
                    domain="pairing-proof",
                )
                evidence = {
                    "enrollment_id": enrollment_id,
                    "owner": owner.wire(),
                    "device_id": document["device_id"],
                    "device_identity": document["device"]["identity"],
                    "proof_document_hash": document_hash,
                    "expires_at": document["expires_at"],
                    "device_proof": device_proof,
                    "control_proof": control_proof,
                }
                evidence["confirmation_ref"] = fixed_ref(
                    "check", "native-enrollment-" + enrollment_id, dict(evidence)
                )
                # Current account/key checks precede publishing. The record is an
                # outcome, never registration authority or permission to access files.
                if await self.checked(owner, enrollment_id, control_proof) != document:
                    raise reject(
                        "enrollment_native_challenge_changed", "Current relationship changed", 412
                    )
                await self.service.records.put(
                    self.service.controller,
                    JOURNAL,
                    enrollment_id,
                    "RunnerNativePairingEvidence",
                    evidence,
                    expected_revision=0,
                    request_id="native-decision",
                )
                return evidence
        except TimeoutError:
            raise reject(
                "enrollment_native_timeout",
                "Original native enrollment confirmation expired",
                410,
                "timeout",
            ) from None
        finally:
            stopped.set()
            stop_watch.set()
            if monitor is not None:
                monitor.cancel()
                await asyncio.gather(monitor, return_exceptions=True)
            if work is not None:
                await asyncio.gather(work, return_exceptions=True)
            self.busy = False


class RegisteredNativeEnrollmentEvidence:
    """Reader never opens UI or reissues a decision during active get/recovery."""

    def __init__(self, service: RunnerEnrollments) -> None:
        self.service = service

    async def current(self, proof_document: Payload, *, owner: Principal) -> Payload:
        key = proof_document["enrollment_id"]
        if await self.service.challenge(owner, key) != proof_document:
            raise reject(
                "enrollment_native_challenge_changed", "Current original document differs", 412
            )
        try:
            row = await self.service.records.get(self.service.controller, JOURNAL, key)
        except StoreMissing:
            raise reject(
                "enrollment_native_confirmation_pending",
                "Original native decision unavailable",
                503,
                "dependency",
            ) from None
        if (
            row.schema_name != "RunnerNativePairingEvidence"
            or row.revision != 1
            or row.payload["owner"] != owner.wire()
            or row.payload["proof_document_hash"] != parameter_hash(proof_document)
            or row.payload["confirmation_ref"]
            != fixed_ref(
                "check",
                "native-enrollment-" + key,
                {k: v for k, v in row.payload.items() if k != "confirmation_ref"},
            )
        ):
            raise reject("enrollment_native_decision_changed", "Original decision differs", 412)
        if await self.service.challenge(owner, key) != proof_document:
            raise reject("enrollment_native_challenge_changed", "Original source changed", 412)
        return row.payload
