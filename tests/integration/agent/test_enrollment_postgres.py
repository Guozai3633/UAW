"""Real Web identity/SQL/Ed25519; launcher/native evidence are controlled sources."""

import asyncio
import base64
import copy
import hashlib
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tests.integration.test_browser_sessions import ORIGIN, envelope, login
from tests.integration.test_browser_sessions import web as web
from tests.integration.test_control_plane import meta
from uaw.run.enrollment import ENROLLMENTS, RunnerEnrollments, fixed_ref
from uaw.shared.contracts import Principal
from uaw.shared.errors import DomainError, reject
from uaw.shared.runner_signatures import sign


@pytest.fixture
async def enrollment_case(web):
    c, client = web
    session = await login(client)
    owner = Principal.model_validate(session["principal"])
    keys = {role: Ed25519PrivateKey.generate() for role in ("control", "device")}

    def peer(role, pid):
        raw = keys[role].public_key().public_bytes_raw()
        return {
            "identity": {
                "pid": pid,
                "created": "133987654321098765",
                "user_sid": "S-1-5-21-1",
                "logon_sid": "S-1-5-5-1-1",
            },
            "actor": {
                "id": role + "-actor",
                "kind": "runner",
                "auth_session_id": role + "-session",
            },
            "role": role,
            "key_id": role + "-key",
            "key_ref": {
                "kind": "content",
                "id": role + "-key",
                "version": "1",
                "content_hash": hashlib.sha256(raw).hexdigest(),
            },
            "public_key": base64.b64encode(raw).decode(),
        }

    candidate = {
        "id": "candidate-one",
        "owner": owner.wire(),
        "device_id": "device-one",
        "control": peer("control", 1001),
        "device": peer("device", 1002),
        "expires_at": (datetime.now(UTC) + timedelta(minutes=4)).isoformat(),
    }

    class Candidates:
        allowed = True

        async def current(self, key, *, owner):
            if not self.allowed:
                raise reject("candidate_revoked", "Controlled candidate revoked", 403)
            assert key == candidate["id"]
            return copy.deepcopy(candidate)

    class Native:
        allowed = True
        mutate = None

        async def current(self, doc, *, owner):
            if not self.allowed:
                raise reject("native_revoked", "Controlled native evidence revoked", 403)
            from uaw.infrastructure.db.records import parameter_hash

            document_hash = parameter_hash(doc)
            value = {
                "enrollment_id": doc["enrollment_id"],
                "owner": owner.wire(),
                "device_id": doc["device_id"],
                "device_identity": doc["device"]["identity"],
                "proof_document_hash": document_hash,
                "confirmation_ref": {
                    "kind": "check",
                    "id": "native-one",
                    "version": "1",
                    "content_hash": document_hash,
                },
                "expires_at": doc["expires_at"],
                "device_proof": sign(
                    doc,
                    keys["device"].private_bytes_raw(),
                    doc["device_id"],
                    "device-key",
                    "pairing-proof",
                ),
                "control_proof": sign(
                    doc,
                    keys["control"].private_bytes_raw(),
                    doc["device_id"],
                    "control-key",
                    "command",
                ),
            }
            if self.mutate:
                self.mutate(value)
            return value

    candidates, native = Candidates(), Native()
    service = RunnerEnrollments(
        c.records,
        c.configuration.platform,
        authenticate=c.browser_sessions.principal,
        candidates=candidates,
        native=native,
    )
    return SimpleNamespace(
        control=c,
        client=client,
        owner=owner,
        candidate=candidate,
        candidates=candidates,
        native=native,
        service=service,
        keys=keys,
        session=session,
    )


async def test_enrollment_pending_has_no_pairing_and_replay_keeps_original_nonce(enrollment_case):
    p = enrollment_case
    original = await p.service.begin(p.owner, p.candidate["id"], meta("begin"))
    assert original["state"] == "pending" and "pairing_ref" not in original
    repeat = await p.service.begin(p.owner, p.candidate["id"], meta("begin"))
    assert repeat == original
    restarted = RunnerEnrollments(
        p.control.records,
        p.control.configuration.platform,
        authenticate=p.control.browser_sessions.principal,
        candidates=p.candidates,
        native=p.native,
    )
    assert await restarted.get(p.owner, original["id"]) == original
    p.native.allowed = False
    document = await restarted.challenge(p.owner, original["id"])
    assert document == original["proof_document"]
    document["nonce"] = "x" * 32
    assert await restarted.challenge(p.owner, original["id"]) == original["proof_document"]
    p.candidates.allowed = False
    with pytest.raises(DomainError, match="Controlled candidate revoked"):
        await restarted.challenge(p.owner, original["id"])


async def test_enrollment_both_proofs_native_binding_and_same_request_replay(enrollment_case):
    p = enrollment_case
    started = await p.service.begin(p.owner, p.candidate["id"], meta("begin"))
    active = await p.service.complete(p.owner, started["id"], meta("complete", 1))
    assert active["state"] == "active" and active["revision"] == 2
    assert active["pairing_ref"] == fixed_ref(
        "content", active["id"], {k: v for k, v in active.items() if k != "pairing_ref"}
    )
    assert await p.service.complete(p.owner, started["id"], meta("complete", 1)) == active
    assert await p.service.get(p.owner, started["id"]) == active
    with pytest.raises(DomainError):
        await p.service.complete(p.owner, started["id"], meta("new-complete", 2))


@pytest.mark.parametrize(
    "field", ["owner", "device_identity", "proof_document_hash", "control_proof", "device_proof"]
)
async def test_enrollment_native_mismatch_never_activates(enrollment_case, field):
    p = enrollment_case
    started = await p.service.begin(p.owner, p.candidate["id"], meta("begin"))

    def mutate(value):
        if field == "owner":
            value[field] = {**value[field], "auth_session_id": "another-session"}
        elif field == "device_identity":
            value[field] = {**value[field], "created": "133987654321098766"}
        elif field == "proof_document_hash":
            value[field] = "0" * 64
        else:
            value[field] = "invalid-signature"

    p.native.mutate = mutate
    with pytest.raises(DomainError):
        await p.service.complete(p.owner, started["id"], meta("forged", 1))
    row = await p.control.records.get(p.control.configuration.platform, ENROLLMENTS, started["id"])
    assert row.payload["state"] == "pending"


async def test_enrollment_current_logout_and_new_session_cannot_inherit_pairing(enrollment_case):
    p = enrollment_case
    started = await p.service.begin(p.owner, p.candidate["id"], meta("begin"))
    await p.control.browser_sessions.logout(p.owner, meta("logout"))
    with pytest.raises(DomainError) as revoked:
        await p.service.complete(p.owner, started["id"], meta("complete", 1))
    assert revoked.value.status_code == 401


async def test_enrollment_current_native_and_key_revocation_close_active_read(enrollment_case):
    p = enrollment_case
    started = await p.service.begin(p.owner, p.candidate["id"], meta("begin"))
    await p.service.complete(p.owner, started["id"], meta("complete", 1))
    p.native.allowed = False
    with pytest.raises(DomainError):
        await p.service.get(p.owner, started["id"])
    p.native.allowed = True
    p.candidate["device"]["key_ref"]["version"] = "2"
    with pytest.raises(DomainError):
        await p.service.get(p.owner, started["id"])


async def test_enrollment_cancel_or_complete_cas_never_reopens_revoked(enrollment_case):
    p = enrollment_case
    started = await p.service.begin(p.owner, p.candidate["id"], meta("begin"))
    results = await asyncio.gather(
        p.service.complete(p.owner, started["id"], meta("complete", 1)),
        p.service.revoke(p.owner, started["id"], meta("revoke", 1)),
        return_exceptions=True,
    )
    assert sum(isinstance(r, dict) for r in results) == 1
    row = await p.control.records.get(p.control.configuration.platform, ENROLLMENTS, started["id"])
    if row.payload["state"] == "active":
        await p.service.revoke(p.owner, started["id"], meta("revoke-after", 2))
    with pytest.raises(DomainError):
        await p.service.get(p.owner, started["id"])


async def test_enrollment_missing_sources_expiry_and_cli_identity_deny(enrollment_case):
    p = enrollment_case
    p.service.candidates = None
    with pytest.raises(DomainError) as missing:
        await p.service.begin(p.owner, p.candidate["id"], meta("begin"))
    assert missing.value.status_code == 503
    p.service.candidates = p.candidates
    with pytest.raises(DomainError):
        await p.service.begin(
            p.owner.model_copy(update={"auth_session_id": "session-cli"}),
            p.candidate["id"],
            meta("cli"),
        )
    started = await p.service.begin(p.owner, p.candidate["id"], meta("begin"))
    p.service.clock = lambda: datetime.now(UTC) + timedelta(hours=2)
    with pytest.raises(DomainError):
        await p.service.get(p.owner, started["id"])


async def test_enrolled_peer_registry_uses_actual_windows_instances_and_current_roles(
    enrollment_case,
):
    import subprocess
    import sys

    from uaw_runner.ipc.windows_pipe import WindowsApi

    from uaw.infrastructure.enrollment_peers import EnrolledPeerRegistry
    from uaw.shared.runner_signatures import VerificationKey

    p = enrollment_case
    process = await asyncio.to_thread(
        subprocess.Popen,
        [sys._base_executable, "-c", "import time; time.sleep(60)"],
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    api = WindowsApi()
    try:
        control = api.current()
        handle, device = api.process(process.pid)
        api.k.CloseHandle(handle)
        for role, observed in (("control", control), ("device", device)):
            p.candidate[role]["identity"] = {
                "pid": observed.pid,
                "created": str(observed.created),
                "user_sid": observed.user_sid,
                "logon_sid": observed.logon_sid,
            }

        class Directory:
            revoked = False

            def lookup(self, key_id, *, device_id):
                role = "control" if key_id == "control-key" else "device"
                return VerificationKey(
                    key_id,
                    device_id,
                    p.keys[role].public_key().public_bytes_raw(),
                    role,
                    self.revoked,
                )

        directory = Directory()
        started = await p.service.begin(p.owner, p.candidate["id"], meta("actual-os-begin"))
        peers = EnrolledPeerRegistry(
            p.service, owner=p.owner, enrollment_id=started["id"], directory=directory
        )
        with pytest.raises(DomainError) as pending:
            await peers.current(device, role="device")
        assert pending.value.failure.code == "enrolled_pairing_pending"
        await p.service.complete(p.owner, started["id"], meta("actual-os-complete", 1))
        actual = await peers.current(device, role="device")
        assert (
            actual.identity == device
            and actual.owner == p.owner
            and actual.pairing_ref.kind == "content"
        )
        assert (
            await peers.owner(authenticated_principal=actual.actor, device_id=actual.device_id)
            == p.owner
        )
        assert (await peers.current(control, role="control")).role == "control"
        directory.revoked = True
        with pytest.raises(DomainError):
            await peers.current(device, role="device")
        directory.revoked = False
        process.terminate()
        await asyncio.to_thread(process.wait, timeout=5)
        with pytest.raises(DomainError):
            await peers.current(device, role="device")
    finally:
        if process.poll() is None:
            process.terminate()
            await asyncio.to_thread(process.wait, timeout=5)


async def test_enrollment_http_current_cookie_and_exact_revision(enrollment_case):
    p = enrollment_case
    p.control.runner_enrollments = p.service
    headers = {"Origin": ORIGIN, "X-UAW-CSRF": p.session["csrf_token"]}
    begin = await p.client.post(
        "/v1/runner/enrollments",
        headers=headers,
        json=envelope("http-begin", candidate_id=p.candidate["id"]),
    )
    assert begin.status_code == 200, begin.json()
    pending = begin.json()["payload"]
    url = f"/v1/runner/enrollments/{pending['id']}"
    read = await p.client.get(url, headers=headers)
    assert read.status_code == 200 and read.json()["payload"] == pending
    invalid = await p.client.post(
        url + "/confirmation", headers=headers, json=envelope("no-revision")
    )
    assert invalid.status_code == 400
    accepted = await p.client.post(
        url + "/confirmation",
        headers=headers,
        json={"meta": meta("http-complete", 1).wire(), "payload": {}},
    )
    assert accepted.status_code == 200, accepted.json()
    assert accepted.json()["payload"]["state"] == "active"
    rejected = await p.client.post(
        url + "/revocation",
        headers=headers,
        json={"meta": meta("http-revoke", 2).wire(), "payload": {}},
    )
    assert rejected.status_code == 200 and rejected.json()["payload"]["state"] == "revoked"


async def test_enrollment_http_rejects_self_authorization_and_missing_sources(enrollment_case):
    p = enrollment_case
    p.control.runner_enrollments = p.service
    headers = {"Origin": ORIGIN, "X-UAW-CSRF": p.session["csrf_token"]}
    forged = await p.client.post(
        "/v1/runner/enrollments",
        headers=headers,
        json=envelope("forged", candidate_id=p.candidate["id"], approved=True),
    )
    assert forged.status_code == 422 and forged.json()["failure"]["code"] == "request_invalid"
    p.service.candidates = None
    missing = await p.client.post(
        "/v1/runner/enrollments",
        headers=headers,
        json=envelope("missing", candidate_id=p.candidate["id"]),
    )
    assert missing.status_code == 503
    without_csrf = await p.client.post(
        "/v1/runner/enrollments",
        headers={"Origin": ORIGIN},
        json=envelope("without-csrf", candidate_id=p.candidate["id"]),
    )
    assert without_csrf.status_code == 403


async def test_enrollment_capacity_rolls_back_new_record_and_replay_remains_original(
    enrollment_case,
):
    p = enrollment_case
    p.service.capacity = 1
    first = await p.service.begin(p.owner, p.candidate["id"], meta("first"))
    assert await p.service.begin(p.owner, p.candidate["id"], meta("first")) == first
    with pytest.raises(DomainError) as full:
        await p.service.begin(p.owner, p.candidate["id"], meta("second"))
    assert full.value.failure.code == "enrollment_capacity_full"
    await p.service.revoke(p.owner, first["id"], meta("revoke", 1))
    next_ = await p.service.begin(p.owner, p.candidate["id"], meta("second"))
    assert next_["state"] == "pending" and next_["id"] != first["id"]


async def test_native_enrollment_reader_uses_fixed_journal_without_ui_recursion(enrollment_case):
    from uaw.infrastructure.enrollment_native import JOURNAL, RegisteredNativeEnrollmentEvidence

    p = enrollment_case
    started = await p.service.begin(p.owner, p.candidate["id"], meta("native-begin"))
    reader = RegisteredNativeEnrollmentEvidence(p.service)
    with pytest.raises(DomainError) as missing:
        await reader.current(started["proof_document"], owner=p.owner)
    assert missing.value.failure.code == "enrollment_native_confirmation_pending"
    # Controlled native outcome only: this verifies durable Reader/proof/current
    # binding, and explicitly does not claim an actual human native decision.
    evidence = await p.native.current(started["proof_document"], owner=p.owner)
    evidence["confirmation_ref"] = fixed_ref(
        "check",
        "native-enrollment-" + started["id"],
        {k: v for k, v in evidence.items() if k != "confirmation_ref"},
    )
    await p.control.records.put(
        p.service.controller,
        JOURNAL,
        started["id"],
        "RunnerNativePairingEvidence",
        evidence,
        expected_revision=0,
        request_id="native-fixture",
    )
    p.service.native = reader
    active = await p.service.complete(p.owner, started["id"], meta("native-complete", 1))
    assert active["state"] == "active"
    assert await p.service.get(p.owner, active["id"]) == active
    p.candidates.allowed = False
    with pytest.raises(DomainError):
        await reader.current(started["proof_document"], owner=p.owner)


async def test_native_enrollment_wrong_os_instance_never_opens_confirmation(
    enrollment_case, monkeypatch
):
    from uaw_runner.keys import ProtectedSigner

    from uaw.infrastructure import enrollment_native

    p = enrollment_case
    started = await p.service.begin(p.owner, p.candidate["id"], meta("native-begin"))
    directory = SimpleNamespace(lookup=lambda *args, **kw: None)
    native = enrollment_native.WindowsEnrollmentConfirmation(
        p.service, directory, ProtectedSigner(directory, None), device_credential_handle="not-used"
    )

    def unexpected_ui():
        raise AssertionError("OS mismatch must fail before any UI")

    monkeypatch.setattr(enrollment_native, "WindowsNativeDialog", unexpected_ui)
    with pytest.raises(DomainError) as denied:
        await native.confirm(p.owner, started["id"], control_proof="not-used")
    assert denied.value.failure.code == "enrollment_native_instance_denied" and not native.busy
    assert (await p.service.get(p.owner, started["id"]))["state"] == "pending"


async def test_first_device_gate_controlled_yes_original_activation_and_cleanup(
    enrollment_case, tmp_path, monkeypatch
):
    from uuid import uuid4

    from pydantic import SecretStr
    from uaw_runner.helper_host import HelperApplication
    from uaw_runner.ipc.windows_pipe import WindowsApi
    from uaw_runner.keys import ProtectedSigner
    from uaw_runner.state import LocalState

    from uaw.infrastructure import enrollment_native
    from uaw.infrastructure.credentials import WindowsCredentialStore
    from uaw.infrastructure.enrollment_bootstrap import FirstEnrollmentDeviceFactory
    from uaw.shared.runner_signatures import VerificationKey

    p = enrollment_case
    actual = WindowsApi().current()
    p.candidate["device"]["identity"] = {
        "pid": actual.pid,
        "created": str(actual.created),
        "user_sid": actual.user_sid,
        "logon_sid": actual.logon_sid,
    }
    for k in ("user_sid", "logon_sid"):
        p.candidate["control"]["identity"][k] = getattr(actual, k)
    started = await p.service.begin(p.owner, p.candidate["id"], meta("controlled-first-begin"))
    state = LocalState(tmp_path / "first-device-keys.sqlite")
    for role in ("control", "device"):
        state.register_key(
            VerificationKey(
                role + "-key",
                p.candidate["device_id"],
                p.keys[role].public_key().public_bytes_raw(),
                role,
            )
        )
    credentials = WindowsCredentialStore("first-device-test-" + uuid4().hex)
    handle = "device-" + uuid4().hex
    await credentials.put(
        handle, SecretStr(base64.b64encode(p.keys["device"].private_bytes_raw()).decode())
    )
    shown = []

    class ControlledDialog:
        def show(self, prompt, stopped, deadline):
            # Explicitly controlled native Yes. It is never a human acceptance receipt.
            shown.append(prompt.text())
            assert "不授予目录" in shown[-1]
            return None

    class Proofs:
        async def current(self, key, *, owner):
            assert key == started["id"] and owner == p.owner
            return sign(
                started["proof_document"],
                p.keys["control"].private_bytes_raw(),
                p.candidate["device_id"],
                "control-key",
                "command",
            )

    class OwnedHelper:
        closed = 0

        async def close(self):
            self.closed += 1

    owned = OwnedHelper()

    class Paired:
        changed = False

        async def create(self, identity):
            assert identity == actual
            assert (await p.service.get(p.owner, started["id"]))["state"] == "active"
            if self.changed:
                p.candidates.allowed = False
            return HelperApplication(owned)

    paired = Paired()
    monkeypatch.setattr(enrollment_native, "WindowsNativeDialog", ControlledDialog)
    p.service.native = enrollment_native.RegisteredNativeEnrollmentEvidence(p.service)
    native = enrollment_native.WindowsEnrollmentConfirmation(
        p.service, state, ProtectedSigner(state, credentials), device_credential_handle=handle
    )
    factory = FirstEnrollmentDeviceFactory(
        p.service,
        owner=p.owner,
        enrollment_id=started["id"],
        native=native,
        proofs=Proofs(),
        paired_factory=paired,
    )
    try:
        assert (await factory.create(actual)).helper is owned
        assert len(shown) == 1 and not owned.closed
        assert (await factory.create(actual)).helper is owned
        assert len(shown) == 1
        paired.changed = True
        with pytest.raises(DomainError):
            await factory.create(actual)
        assert owned.closed == 1 and len(shown) == 1
    finally:
        await credentials.delete(handle)
    with pytest.raises(DomainError) as cleaned:
        await credentials.resolve(handle)
    assert cleaned.value.status_code == 404


async def test_native_enrollment_invalid_control_signature_never_opens_ui(
    enrollment_case, monkeypatch
):
    from uaw_runner.ipc.windows_pipe import WindowsApi
    from uaw_runner.keys import ProtectedSigner

    from uaw.infrastructure import enrollment_native
    from uaw.shared.runner_signatures import VerificationKey

    p = enrollment_case
    actual = WindowsApi().current()
    p.candidate["device"]["identity"] = {
        "pid": actual.pid,
        "created": str(actual.created),
        "user_sid": actual.user_sid,
        "logon_sid": actual.logon_sid,
    }
    p.candidate["control"]["identity"]["user_sid"] = actual.user_sid
    p.candidate["control"]["identity"]["logon_sid"] = actual.logon_sid
    started = await p.service.begin(p.owner, p.candidate["id"], meta("bad-proof-begin"))

    class Directory:
        def lookup(self, key_id, *, device_id):
            role = "control" if key_id == "control-key" else "device"
            return VerificationKey(
                key_id, device_id, p.keys[role].public_key().public_bytes_raw(), role
            )

    directory = Directory()
    native = enrollment_native.WindowsEnrollmentConfirmation(
        p.service, directory, ProtectedSigner(directory, None), device_credential_handle="not-used"
    )

    def unexpected_ui():
        raise AssertionError("Invalid proof must fail before UI or protected key access")

    monkeypatch.setattr(enrollment_native, "WindowsNativeDialog", unexpected_ui)
    with pytest.raises(DomainError) as denied:
        await native.confirm(p.owner, started["id"], control_proof="invalid-signature")
    assert denied.value.failure.code == "enrollment_control_proof_denied" and not native.busy


async def test_control_enrollment_actual_os_protected_key_and_current_rechecks(
    enrollment_case, tmp_path
):
    from uuid import uuid4

    from pydantic import SecretStr
    from uaw_runner.ipc.windows_pipe import WindowsApi
    from uaw_runner.keys import ProtectedSigner
    from uaw_runner.state import LocalState

    from uaw.infrastructure.credentials import WindowsCredentialStore
    from uaw.infrastructure.enrollment_control import WindowsEnrollmentControlProof
    from uaw.shared.runner_signatures import VerificationKey, verify
    from uaw.shared.schema import ContractViolation

    p = enrollment_case
    actual = WindowsApi().current()
    p.candidate["control"]["identity"] = {
        "pid": actual.pid,
        "created": str(actual.created),
        "user_sid": actual.user_sid,
        "logon_sid": actual.logon_sid,
    }
    p.candidate["device"]["identity"]["user_sid"] = actual.user_sid
    p.candidate["device"]["identity"]["logon_sid"] = actual.logon_sid
    state = LocalState(tmp_path / "current-keys.sqlite")
    for role in ("control", "device"):
        state.register_key(
            VerificationKey(
                role + "-key",
                p.candidate["device_id"],
                p.keys[role].public_key().public_bytes_raw(),
                role,
            )
        )
    credentials = WindowsCredentialStore("enrollment-control-test-" + uuid4().hex)
    handle = "control-" + uuid4().hex
    await credentials.put(
        handle, SecretStr(base64.b64encode(p.keys["control"].private_bytes_raw()).decode())
    )
    try:
        started = await p.service.begin(p.owner, p.candidate["id"], meta("protected-control-begin"))
        issuer = WindowsEnrollmentControlProof(
            p.service, state, credentials, control_credential_handle=handle
        )
        proof = await issuer.issue(p.owner, started["id"])
        assert verify(
            started["proof_document"],
            proof,
            state.lookup("control-key", device_id=p.candidate["device_id"]),
            "command",
        )
        # Ordinary command signer must still refuse an enrollment document.
        with pytest.raises(ContractViolation):
            await ProtectedSigner(state, credentials).sign_document(
                started["proof_document"],
                device_id=p.candidate["device_id"],
                key_id="control-key",
                domain="command",
                credential_handle=handle,
            )
        await credentials.put(
            handle,
            SecretStr(base64.b64encode(Ed25519PrivateKey.generate().private_bytes_raw()).decode()),
        )
        with pytest.raises(DomainError) as mismatched:
            await issuer.issue(p.owner, started["id"])
        assert mismatched.value.failure.code == "enrollment_control_private_key_denied"
        state.revoke_key("device-key", expected_revision=0)
        with pytest.raises(DomainError) as revoked:
            await issuer.issue(p.owner, started["id"])
        assert revoked.value.failure.code == "enrollment_control_key_denied"
    finally:
        await credentials.delete(handle)
    with pytest.raises(DomainError) as cleaned:
        await credentials.resolve(handle)
    assert cleaned.value.status_code == 404


async def test_owned_prepared_helper_candidate_current_sql_os_and_revocation(
    enrollment_case, tmp_path
):
    import os
    import sys
    from pathlib import Path

    from uaw_runner.helper_process import HelperProcess
    from uaw_runner.state import LocalState

    from uaw.composition import assemble_enrollment_sources
    from uaw.infrastructure.enrollment_candidates import OwnedEnrollmentCandidates
    from uaw.shared.runner_signatures import VerificationKey

    p = enrollment_case
    state = LocalState(tmp_path / "candidate-current-keys.sqlite")
    for role in ("control", "device"):
        state.register_key(
            VerificationKey(
                role + "-key",
                p.candidate["device_id"],
                p.keys[role].public_key().public_bytes_raw(),
                role,
            )
        )
    # Actual fixed installed host, before start/assembly/handshake. The runtime
    # import roots belong to this test's installed source; no request supplies them.
    root = (await asyncio.to_thread(Path(__file__).resolve)).parents[3]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        map(str, (root / "src", root / "apps/local_runner", Path(sys.prefix) / "Lib/site-packages"))
    )
    helper = await HelperProcess.prepare(
        python=Path(sys._base_executable),
        assembly_module="uaw.infrastructure.enrollment_native",
        environment=environment,
    )
    p.control.runner_enrollments = p.service
    source = assemble_enrollment_sources(p.control, directory=state)
    try:
        candidate = await source.capture(
            p.owner,
            helper,
            device_id=p.candidate["device_id"],
            control_actor=Principal.model_validate(p.candidate["control"]["actor"]),
            device_actor=Principal.model_validate(p.candidate["device"]["actor"]),
            control_key_id="control-key",
            device_key_id="device-key",
        )
        assert candidate["device"]["identity"]["pid"] == helper.process.pid
        assert not helper.started and not helper.closed
        restarted = OwnedEnrollmentCandidates(p.service, state)
        assert await restarted.current(candidate["id"], owner=p.owner) == candidate
        p.service.candidates = restarted
        pending = await p.service.begin(p.owner, candidate["id"], meta("actual-launch-begin"))
        assert pending["state"] == "pending" and "pairing_ref" not in pending
        assert await p.service.challenge(p.owner, pending["id"]) == pending["proof_document"]
        with pytest.raises(DomainError) as no_human:
            await p.service.complete(p.owner, pending["id"], meta("no-native", 1))
        assert no_human.value.failure.code == "enrollment_native_confirmation_pending"
        other = p.owner.model_copy(update={"auth_session_id": "another-web-session"})
        with pytest.raises(DomainError):
            await restarted.current(candidate["id"], owner=other)
        state.revoke_key("device-key", expected_revision=0)
        with pytest.raises(DomainError) as revoked:
            await restarted.current(candidate["id"], owner=p.owner)
        assert revoked.value.failure.code == "enrollment_launcher_key_denied"
    finally:
        await helper.close()
    assert helper.process.poll() is not None
    with pytest.raises(DomainError):
        await source.current(candidate["id"], owner=p.owner)


async def test_first_device_factory_missing_source_never_opens_ui(enrollment_case, monkeypatch):
    from uaw.infrastructure import enrollment_native
    from uaw.infrastructure.enrollment_bootstrap import FirstEnrollmentDeviceFactory

    def unexpected_ui():
        raise AssertionError("Missing first bootstrap cannot open UI")

    monkeypatch.setattr(enrollment_native, "WindowsNativeDialog", unexpected_ui)
    factory = FirstEnrollmentDeviceFactory(
        enrollment_case.service,
        owner=enrollment_case.owner,
        enrollment_id="not-captured",
        native=None,
        proofs=None,
        paired_factory=None,
    )
    with pytest.raises(DomainError) as missing:
        await factory.create(None)
    assert missing.value.status_code == 503


async def test_first_device_factory_wrong_proof_never_calls_paired_factory(
    enrollment_case, monkeypatch
):
    from uaw_runner.ipc.windows_pipe import WindowsApi
    from uaw_runner.keys import ProtectedSigner

    from uaw.infrastructure import enrollment_native
    from uaw.infrastructure.enrollment_bootstrap import FirstEnrollmentDeviceFactory
    from uaw.shared.runner_signatures import VerificationKey

    p = enrollment_case
    actual = WindowsApi().current()
    p.candidate["device"]["identity"] = {
        "pid": actual.pid,
        "created": str(actual.created),
        "user_sid": actual.user_sid,
        "logon_sid": actual.logon_sid,
    }
    p.candidate["control"]["identity"]["user_sid"] = actual.user_sid
    p.candidate["control"]["identity"]["logon_sid"] = actual.logon_sid
    started = await p.service.begin(p.owner, p.candidate["id"], meta("first-device-begin"))

    class Directory:
        def lookup(self, key_id, *, device_id):
            role = "control" if key_id == "control-key" else "device"
            return VerificationKey(
                key_id, device_id, p.keys[role].public_key().public_bytes_raw(), role
            )

    class Proofs:
        async def current(self, enrollment_id, *, owner):
            assert owner == p.owner and enrollment_id == started["id"]
            return "invalid-proof"

    class Paired:
        async def create(self, identity):
            raise AssertionError("Pending or invalid proof must never become a paired helper")

    def unexpected_ui():
        raise AssertionError("Invalid first proof cannot open UI")

    monkeypatch.setattr(enrollment_native, "WindowsNativeDialog", unexpected_ui)
    directory = Directory()
    native = enrollment_native.WindowsEnrollmentConfirmation(
        p.service, directory, ProtectedSigner(directory, None), device_credential_handle="not-used"
    )
    factory = FirstEnrollmentDeviceFactory(
        p.service,
        owner=p.owner,
        enrollment_id=started["id"],
        native=native,
        proofs=Proofs(),
        paired_factory=Paired(),
    )
    with pytest.raises(DomainError) as denied:
        await factory.create(actual)
    assert denied.value.failure.code == "enrollment_control_proof_denied"
    assert (await p.service.get(p.owner, started["id"]))["state"] == "pending"
