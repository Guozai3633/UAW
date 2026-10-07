"""Real Ed25519; credential backend is an explicit in-memory TEST fixture, not OS acceptance."""

import base64
import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from uaw_runner.keys import Ed25519SignatureAdapter, ProtectedSigner
from uaw_runner.state import LocalState

from uaw.shared.errors import CapabilityUnavailable, DomainError
from uaw.shared.runner_signatures import VerificationKey, sign
from uaw.workspace.contracts import RunnerCommand

from .conftest import NOW, wire
from .test_protocol import failure_receipt


class CredentialFixture:
    """Test double; never injected into product composition."""

    def __init__(self):
        self.values = {}
        self.on_resolve = None

    async def put(self, handle, secret):
        if handle in self.values:
            raise ValueError("Fixture credential exists")
        self.values[handle] = secret

    async def resolve(self, handle):
        if self.on_resolve:
            self.on_resolve()
        if handle not in self.values:
            from uaw.shared.errors import reject

            raise reject("credential_missing", "Fixture key missing", 404, "dependency")
        return self.values[handle]

    async def delete(self, handle):
        del self.values[handle]


def test_real_command_adapter_tamper_live_revocation_and_restart(setup, tmp_path):
    *_, protocol = setup
    command = setup[3]
    directory = LocalState(tmp_path / "control" / "keys.sqlite")
    private = Ed25519PrivateKey.generate()
    key = VerificationKey("control1", "d1", private.public_key().public_bytes_raw(), "control")
    directory.register_key(key)
    adapter = Ed25519SignatureAdapter(directory)
    data = command.wire()
    data["signature"] = sign(data, private.private_bytes_raw(), "d1", "control1", "command")
    signed = RunnerCommand.model_validate_json(json.dumps(data))
    protocol.signatures = adapter
    assert protocol.admit(wire(signed), now=NOW).state == "admitted"
    for field, value in (("fencing_token", 9), ("expires_at", "2026-10-08T00:00:00Z")):
        tampered = {**data, field: value}
        with pytest.raises(DomainError):
            protocol.admit(json.dumps(tampered), now=NOW)
    tampered = signed.wire()
    tampered["parameters"]["parameters"]["path"] = "."
    assert not adapter.verify_command(
        RunnerCommand.model_validate_json(json.dumps(tampered)), device_id="d1"
    )
    assert not adapter.verify_command(signed, device_id="d2")
    directory.revoke_key("control1", expected_revision=0)
    reopened = LocalState(directory.path)
    assert not Ed25519SignatureAdapter(reopened).verify_command(signed, device_id="d1")
    with pytest.raises(DomainError):
        reopened.register_key(key)  # Tombstone cannot be overwritten or role-changed.


def test_actual_roles_and_receipt_domain_are_not_interchangeable(setup, tmp_path):
    command = setup[3]
    state = LocalState(tmp_path / "keys.sqlite")
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    state.register_key(VerificationKey("device1", "d1", public, "device"))
    state.register_key(VerificationKey("control1", "d1", public, "control"))
    adapter = Ed25519SignatureAdapter(state)
    data = command.wire()
    data["signature"] = sign(data, private.private_bytes_raw(), "d1", "device1", "command")
    assert not adapter.verify_command(
        RunnerCommand.model_validate_json(json.dumps(data)), device_id="d1"
    )
    receipt = failure_receipt(command)
    receipt["signature"] = sign(receipt, private.private_bytes_raw(), "d1", "device1", "receipt")
    assert adapter.verify_receipt(receipt, device_id="d1")
    for domain in ("command", "root-selection", "pairing-proof"):
        receipt["signature"] = sign(receipt, private.private_bytes_raw(), "d1", "device1", domain)
        assert not adapter.verify_receipt(receipt, device_id="d1")
    receipt["signature"] = sign(receipt, private.private_bytes_raw(), "d1", "control1", "receipt")
    assert not adapter.verify_receipt(receipt, device_id="d1")


@pytest.mark.asyncio
async def test_protected_signer_no_plaintext_directory_or_insecure_fallback(tmp_path):
    state = LocalState(tmp_path / "keys.sqlite")
    vault = CredentialFixture()
    signer = ProtectedSigner(state, vault)
    public = await signer.provision_private(credential_handle="private-device1")
    state.register_key(VerificationKey("device1", "d1", public, "device"))
    document = {"challenge": "原文  空白\n"}
    signature = await signer.sign_document(
        document,
        device_id="d1",
        key_id="device1",
        domain="pairing-proof",
        credential_handle="private-device1",
    )
    assert Ed25519SignatureAdapter(state).verify_document(
        {**document, "signature": signature}, device_id="d1", domain="pairing-proof"
    )
    raw = base64.b64decode(vault.values["private-device1"].get_secret_value())
    assert raw not in state.path.read_bytes()
    assert (
        vault.values["private-device1"].get_secret_value().encode() not in state.path.read_bytes()
    )
    assert "private-device1" not in state.path.read_bytes().decode("latin1")
    assert raw.hex() not in repr(vault.values["private-device1"])
    with pytest.raises(CapabilityUnavailable):
        await ProtectedSigner(state, None).provision_private(credential_handle="missing")
    with pytest.raises(DomainError):
        await signer.sign_document(
            document,
            device_id="d1",
            key_id="device1",
            domain="command",
            credential_handle="private-device1",
        )
    vault.on_resolve = lambda: state.revoke_key("device1", expected_revision=0)
    with pytest.raises(DomainError):
        await signer.sign_document(
            document,
            device_id="d1",
            key_id="device1",
            domain="pairing-proof",
            credential_handle="private-device1",
        )


@pytest.mark.asyncio
async def test_protected_key_handle_cannot_be_overwritten(tmp_path):
    state, vault = LocalState(tmp_path / "keys.sqlite"), CredentialFixture()
    signer = ProtectedSigner(state, vault)
    await signer.provision_private(credential_handle="once")
    original = vault.values["once"]
    with pytest.raises(DomainError):
        await signer.provision_private(credential_handle="once")
    assert vault.values["once"] == original
