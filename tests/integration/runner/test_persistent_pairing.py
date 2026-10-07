"""Real SQLite transactions/reopen/concurrency + real crypto; native IPC is a TEST adapter."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from uaw_runner.keys import ProtectedSigner
from uaw_runner.pairing import LocalRoots, PairingVerifier, PersistentRootSelection
from uaw_runner.state import LocalState

from tests.unit.runner.conftest import NOW
from tests.unit.runner.test_real_keys import CredentialFixture
from uaw.shared.errors import CapabilityUnavailable, DomainError
from uaw.shared.runner_signatures import VerificationKey, sign
from uaw.workspace.ports import NativeConfirmation

RUNNER_PACKAGE_PATH = str(Path(__file__).resolve().parents[3] / "apps/local_runner")


class NativeFixture:
    """Explicit test confirmation adapter. Does not prove an OS user/channel was authenticated."""

    def __init__(self, path=None):
        self.path = path
        self.change = {}
        self.before_return = None

    async def confirm(self, **request):
        if self.before_return:
            self.before_return()
        return replace(
            NativeConfirmation(
                **request, expires_at=NOW + timedelta(minutes=5), native_path=self.path
            ),
            **self.change,
        )


@pytest.fixture
def persistent(tmp_path):
    state = LocalState(tmp_path / "control" / "states.sqlite")
    roots = LocalRoots(tmp_path / "native" / "roots.sqlite")
    private = Ed25519PrivateKey.generate()
    issued = state.issue(
        request_id="request1",
        kind="pair",
        principal_id="u1",
        device_id="d1",
        key_id="device1",
        public_bytes=private.public_key().public_bytes_raw(),
        expires_at=NOW + timedelta(minutes=10),
        now=NOW,
    )
    return state, roots, private, issued


def proof(issued, private):
    return sign(
        issued.ticket.document(), private.private_bytes_raw(), "d1", "device1", "pairing-proof"
    )


def options(issued, private):
    return dict(
        expected_revision=0,
        principal_id="u1",
        code=issued.verification_code,
        proof_signature=proof(issued, private),
    )


@pytest.mark.asyncio
async def test_persistent_approve_consume_restart_and_code_not_stored(persistent):
    state, _, private, issued = persistent
    verifier = PairingVerifier(state, native=NativeFixture(), clock=lambda: NOW)
    approved = await verifier.approve(issued.ticket.ticket_id, **options(issued, private))
    assert approved.state == "approved" and approved.revision == 1
    reopened = LocalState(state.path)
    consumed = reopened.consume(approved.ticket_id, expected_revision=1, now=NOW)
    assert consumed.state == "consumed" and consumed.revision == 2
    assert LocalState(state.path).get(consumed.ticket_id, now=NOW).state == "consumed"
    with pytest.raises(DomainError):
        reopened.consume(approved.ticket_id, expected_revision=1, now=NOW)
    assert issued.verification_code.encode() not in state.path.read_bytes()
    assert issued.verification_code not in repr(issued)
    with pytest.raises(DomainError):
        state.lookup(
            "device1", device_id="d1"
        )  # Internal consume never pretends registered device.


@pytest.mark.asyncio
async def test_missing_ipc_legacy_completion_wrong_proof_and_code_deny(persistent):
    state, _, private, issued = persistent
    missing = PairingVerifier(state, native=None, clock=lambda: NOW)
    with pytest.raises(CapabilityUnavailable):
        await missing.approve(issued.ticket.ticket_id, **options(issued, private))
    with pytest.raises(CapabilityUnavailable):
        missing.complete_legacy()
    verifier = PairingVerifier(state, native=NativeFixture(), clock=lambda: NOW)
    for change in (
        {"proof_signature": "yes"},
        {"code": "wrong"},
        {"principal_id": "other"},
        {"proof_signature": proof(issued, Ed25519PrivateKey.generate())},
    ):
        with pytest.raises(DomainError):
            await verifier.approve(
                issued.ticket.ticket_id, **{**options(issued, private), **change}
            )
    assert state.get(issued.ticket.ticket_id, now=NOW).state == "pending"


@pytest.mark.parametrize(
    "change",
    [
        {"principal_id": "other"},
        {"device_id": "other"},
        {"ticket_id": "other"},
        {"document_hash": "self-asserted"},
        {"expires_at": NOW},
        {"expires_at": NOW + timedelta(hours=1)},
    ],
)
@pytest.mark.asyncio
async def test_native_confirmation_is_exact_and_live(persistent, change):
    state, _, private, issued = persistent
    native = NativeFixture()
    native.change = change
    verifier = PairingVerifier(state, native=native, clock=lambda: NOW)
    with pytest.raises(DomainError):
        await verifier.approve(issued.ticket.ticket_id, **options(issued, private))
    assert state.get(issued.ticket.ticket_id, now=NOW).state == "pending"


def test_reissue_is_idempotent_but_never_reemits_code_or_changes_nonce(persistent):
    state, _, private, issued = persistent
    arguments = dict(
        request_id="request1",
        kind="pair",
        principal_id="u1",
        device_id="d1",
        key_id="device1",
        public_bytes=private.public_key().public_bytes_raw(),
        expires_at=NOW + timedelta(minutes=10),
        now=NOW,
    )
    repeat = LocalState(state.path).issue(**arguments)
    assert repeat.ticket == issued.ticket and repeat.verification_code is None
    for change in ({"key_id": "other"}, {"expires_at": NOW + timedelta(minutes=11)}):
        with pytest.raises(DomainError):
            state.issue(**{**arguments, **change})


@pytest.mark.asyncio
async def test_deadline_after_confirmation_and_revoke_cas_are_terminal(persistent):
    state, _, private, issued = persistent
    native = NativeFixture()
    clock = [NOW]
    verifier = PairingVerifier(state, native=native, clock=lambda: clock[0])
    native.before_return = lambda: clock.__setitem__(0, NOW + timedelta(minutes=10))
    with pytest.raises(DomainError):
        await verifier.approve(issued.ticket.ticket_id, **options(issued, private))
    assert state.get(issued.ticket.ticket_id, now=clock[0]).state == "expired"
    assert state.get(issued.ticket.ticket_id, now=NOW).state == "expired"
    with pytest.raises(DomainError):
        state.revoke(issued.ticket.ticket_id, expected_revision=1, now=NOW)


@pytest.mark.asyncio
async def test_concurrent_approval_and_consumption_across_connections(persistent):
    state, _, private, issued = persistent

    def approve(_):
        verifier = PairingVerifier(
            LocalState(state.path), native=NativeFixture(), clock=lambda: NOW
        )
        try:
            return asyncio.run(
                verifier.approve(issued.ticket.ticket_id, **options(issued, private))
            ).state
        except DomainError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert list(pool.map(approve, range(16))).count("approved") == 1

    def consume(_):
        try:
            return (
                LocalState(state.path)
                .consume(issued.ticket.ticket_id, expected_revision=1, now=NOW)
                .state
            )
        except DomainError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert list(pool.map(consume, range(16))).count("consumed") == 1


@pytest.mark.asyncio
async def test_expired_and_revoked_approved_tickets_never_consume(persistent):
    state, _, private, issued = persistent
    verifier = PairingVerifier(state, native=NativeFixture(), clock=lambda: NOW)
    await verifier.approve(issued.ticket.ticket_id, **options(issued, private))
    revoked = state.revoke(issued.ticket.ticket_id, expected_revision=1, now=NOW)
    assert revoked.state == "revoked" and revoked.revision == 2
    with pytest.raises(DomainError):
        state.consume(issued.ticket.ticket_id, expected_revision=1, now=NOW)
    with pytest.raises(DomainError):
        await verifier.approve(issued.ticket.ticket_id, **options(issued, private))


@pytest.mark.asyncio
async def test_real_root_selection_signature_single_use_and_path_separation(persistent, tmp_path):
    state, roots, _, _ = persistent
    root = tmp_path / "fixture-project"
    root.mkdir()
    (root / "fixture.txt").write_text("原文 unchanged", encoding="utf-8")
    vault = CredentialFixture()
    signer = ProtectedSigner(state, vault)
    public = await signer.provision_private(credential_handle="private1")
    state.register_key(VerificationKey("device1", "d1", public, "device"))
    issued = state.issue(
        request_id="rootrequest",
        kind="root",
        principal_id="u1",
        device_id="d1",
        key_id="device1",
        public_bytes=public,
        expires_at=NOW + timedelta(minutes=10),
        now=NOW,
        root_handle="root1",
        display_name="fixture",
    )
    signature = await signer.sign_document(
        issued.ticket.document(),
        device_id="d1",
        key_id="device1",
        domain="pairing-proof",
        credential_handle="private1",
    )
    verifier = PairingVerifier(state, native=NativeFixture(root), clock=lambda: NOW, roots=roots)
    await verifier.approve(
        issued.ticket.ticket_id,
        expected_revision=0,
        principal_id="u1",
        code=issued.verification_code,
        proof_signature=signature,
    )
    selection = await verifier.root_selection(
        issued.ticket.ticket_id, signer=signer, credential_handle="private1"
    )
    consumer = PersistentRootSelection(state, roots)
    for tampered in (
        selection.model_copy(update={"display_name": "other"}),
        selection.model_copy(update={"selection_token": "bad"}),
        selection.model_copy(update={"expires_at": selection.expires_at.replace("+00:00", "Z")}),
    ):
        with pytest.raises(DomainError):
            consumer.consume(tampered, principal_id="u1", device_id="d1", now=NOW)

    def consume(_):
        try:
            return (
                PersistentRootSelection(LocalState(state.path), LocalRoots(roots.state.path))
                .consume(selection, principal_id="u1", device_id="d1", now=NOW)
                .root_handle
            )
        except DomainError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(consume, range(16)))
    assert results.count("root1") == 1
    assert LocalState(state.path).get(issued.ticket.ticket_id, now=NOW).state == "consumed"
    assert str(root).encode() not in state.path.read_bytes()
    assert "原文 unchanged" == (root / "fixture.txt").read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_current_key_revocation_invalidates_root_token(persistent, tmp_path):
    state, roots, private, _ = persistent
    state.register_key(
        VerificationKey("device1", "d1", private.public_key().public_bytes_raw(), "device")
    )
    root = tmp_path / "project"
    root.mkdir()
    issued = state.issue(
        request_id="rootrequest",
        kind="root",
        principal_id="u1",
        device_id="d1",
        key_id="device1",
        public_bytes=private.public_key().public_bytes_raw(),
        expires_at=NOW + timedelta(minutes=10),
        now=NOW,
        root_handle="root1",
        display_name="fixture",
    )
    verifier = PairingVerifier(state, native=NativeFixture(root), clock=lambda: NOW, roots=roots)
    await verifier.approve(issued.ticket.ticket_id, **options(issued, private))
    state.revoke_key("device1", expected_revision=0)
    assert LocalState(state.path).get(issued.ticket.ticket_id, now=NOW).state == "revoked"
    with pytest.raises(DomainError):
        state.consume(issued.ticket.ticket_id, expected_revision=1, now=NOW)


@pytest.mark.asyncio
async def test_confirmation_expiry_is_persistent_and_cannot_be_rolled_back(persistent):
    state, _, private, issued = persistent
    verifier = PairingVerifier(state, native=NativeFixture(), clock=lambda: NOW)
    await verifier.approve(issued.ticket.ticket_id, **options(issued, private))
    reopened = LocalState(state.path)
    with pytest.raises(DomainError):
        reopened.consume(
            issued.ticket.ticket_id, expected_revision=1, now=NOW + timedelta(minutes=5)
        )
    assert reopened.get(issued.ticket.ticket_id, now=NOW).state == "expired"


@pytest.mark.asyncio
async def test_revoke_while_waiting_for_confirmation_prevents_approval(persistent):
    state, _, private, issued = persistent
    native = NativeFixture()
    native.before_return = lambda: LocalState(state.path).revoke(
        issued.ticket.ticket_id, expected_revision=0, now=NOW
    )
    verifier = PairingVerifier(state, native=native, clock=lambda: NOW)
    with pytest.raises(DomainError):
        await verifier.approve(issued.ticket.ticket_id, **options(issued, private))
    assert state.get(issued.ticket.ticket_id, now=NOW).state == "revoked"


@pytest.mark.asyncio
async def test_pairing_consume_cas_across_real_python_processes(persistent):
    import os
    import subprocess
    import sys

    state, _, private, issued = persistent
    verifier = PairingVerifier(state, native=NativeFixture(), clock=lambda: NOW)
    await verifier.approve(issued.ticket.ticket_id, **options(issued, private))
    script = """
import sys
from pathlib import Path
from datetime import datetime
from uaw_runner.state import LocalState
from uaw.shared.errors import DomainError
try:
    LocalState(Path(sys.argv[1])).consume(sys.argv[2], expected_revision=1,
                                        now=datetime.fromisoformat(sys.argv[3]))
    print('consumed')
except DomainError:
    print('rejected')
"""
    env = {
        **os.environ,
        "PYTHONPATH": RUNNER_PACKAGE_PATH,
    }

    def consume(_):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                script,
                str(state.path),
                issued.ticket.ticket_id,
                NOW.isoformat(),
            ],
            capture_output=True,
            text=True,
            env=env,
            check=True,
        )
        return result.stdout.strip()

    with ThreadPoolExecutor(max_workers=6) as pool:
        assert list(pool.map(consume, range(6))).count("consumed") == 1


@pytest.mark.asyncio
async def test_challenge_nonce_and_signed_fields_cannot_replay_between_tickets(persistent):
    state, _, private, issued = persistent
    other = state.issue(
        request_id="request2",
        kind="pair",
        principal_id="u1",
        device_id="d1",
        key_id="device1",
        public_bytes=private.public_key().public_bytes_raw(),
        expires_at=NOW + timedelta(minutes=10),
        now=NOW,
    )
    assert issued.ticket.nonce != other.ticket.nonce
    assert issued.ticket.challenge != other.ticket.challenge
    verifier = PairingVerifier(state, native=NativeFixture(), clock=lambda: NOW)
    with pytest.raises(DomainError):
        await verifier.approve(
            other.ticket.ticket_id,
            expected_revision=0,
            principal_id="u1",
            code=other.verification_code,
            proof_signature=proof(issued, private),
        )
    changed = {**issued.ticket.document(), "nonce": "model-supplied"}
    invalid = sign(changed, private.private_bytes_raw(), "d1", "device1", "pairing-proof")
    with pytest.raises(DomainError):
        await verifier.approve(
            issued.ticket.ticket_id, **{**options(issued, private), "proof_signature": invalid}
        )


@pytest.mark.asyncio
async def test_root_without_native_path_is_not_authorized(persistent):
    state, roots, private, _ = persistent
    state.register_key(
        VerificationKey("device1", "d1", private.public_key().public_bytes_raw(), "device")
    )
    issued = state.issue(
        request_id="rootrequest",
        kind="root",
        principal_id="u1",
        device_id="d1",
        key_id="device1",
        public_bytes=private.public_key().public_bytes_raw(),
        expires_at=NOW + timedelta(minutes=10),
        now=NOW,
        root_handle="root1",
        display_name="fixture",
    )
    verifier = PairingVerifier(state, native=NativeFixture(), clock=lambda: NOW, roots=roots)
    with pytest.raises(DomainError):
        await verifier.approve(issued.ticket.ticket_id, **options(issued, private))
    assert state.get(issued.ticket.ticket_id, now=NOW).state == "pending"


@pytest.mark.asyncio
async def test_concurrent_revoke_versus_consume_has_one_terminal_winner(persistent):
    state, _, private, issued = persistent
    verifier = PairingVerifier(state, native=NativeFixture(), clock=lambda: NOW)
    await verifier.approve(issued.ticket.ticket_id, **options(issued, private))

    def transition(index):
        local = LocalState(state.path)
        try:
            method = local.consume if index % 2 else local.revoke
            return method(issued.ticket.ticket_id, expected_revision=1, now=NOW).state
        except DomainError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(transition, range(16)))
    assert sum(value != "rejected" for value in results) == 1
    terminal = LocalState(state.path).get(issued.ticket.ticket_id, now=NOW)
    assert terminal.state in ("consumed", "revoked") and terminal.revision == 2


@pytest.mark.asyncio
async def test_pending_ticket_expiry_boundary_survives_restart(persistent):
    state, _, private, issued = persistent
    now = issued.ticket.expires_at
    verifier = PairingVerifier(LocalState(state.path), native=NativeFixture(), clock=lambda: now)
    with pytest.raises(DomainError):
        await verifier.approve(issued.ticket.ticket_id, **options(issued, private))
    assert LocalState(state.path).get(issued.ticket.ticket_id, now=NOW).state == "expired"
