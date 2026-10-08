"""Actual Ed25519 with explicit memory credential fixture; OS checks are separate."""

import asyncio
import json
from datetime import timedelta

import pytest
from uaw_runner.control_signing import ControlCommandSigner, ControlKeyBinding
from uaw_runner.keys import ProtectedSigner
from uaw_runner.state import LocalState

from uaw.shared.errors import CapabilityUnavailable, DomainError
from uaw.shared.runner_signatures import VerificationKey

from .conftest import NOW
from .test_real_keys import CredentialFixture


@pytest.fixture
async def control_case(setup, tmp_path):
    state = LocalState(tmp_path / "keys.sqlite")
    vault = CredentialFixture()
    protected = ProtectedSigner(state, vault)
    public = await protected.provision_private(credential_handle="control-private")
    state.register_key(VerificationKey("control1", "d1", public, "control"))
    clock = [NOW]
    adapter = ControlCommandSigner(
        (ControlKeyBinding("d1", "control1", "control-private"),),
        directory=state,
        signer=protected,
        clock=lambda: clock[0],
    )
    draft = setup[3].wire()
    draft.pop("signature")
    return adapter, draft, state, vault, clock


async def test_sign_exact_published_draft_verify_restart_and_historical_recovery(control_case):
    adapter, draft, state, vault, clock = control_case
    before = json.loads(json.dumps(draft))
    signed = await adapter.sign(draft, device_id="d1")
    assert {k: v for k, v in signed.items() if k != "signature"} == before == draft
    assert await adapter.verify(signed, device_id="d1") is None
    reopened = LocalState(state.path)
    recovered = ControlCommandSigner(
        tuple(adapter.bindings.values()),
        directory=reopened,
        signer=ProtectedSigner(reopened, vault),
        clock=lambda: clock[0],
    )
    clock[0] += timedelta(days=1)
    assert await recovered.verify(signed, device_id="d1") is None
    with pytest.raises(DomainError, match="deadline"):
        await recovered.sign(draft, device_id="d1")


@pytest.mark.parametrize(
    "mutation", ["extra_key", "extra_handle", "signature", "missing", "operation", "bool"]
)
async def test_draft_strict_and_no_body_key_selection(control_case, mutation):
    adapter, draft, *_ = control_case
    if mutation == "extra_key":
        draft["key_id"] = "control1"
    elif mutation == "extra_handle":
        draft["credential_handle"] = "control-private"
    elif mutation == "signature":
        draft["signature"] = "caller-signature"
    elif mutation == "missing":
        draft.pop("request_ref")
    elif mutation == "operation":
        draft["operation_id"] = "other"
    else:
        draft["fencing_token"] = True
    with pytest.raises(ValueError if mutation != "operation" else DomainError):
        await adapter.sign(draft, device_id="d1")


@pytest.mark.parametrize("missing", ["device", "signer", "vault"])
async def test_no_binding_signer_or_os_fallback(control_case, missing):
    adapter, draft, *_ = control_case
    if missing == "signer":
        adapter.signer = None
    elif missing == "vault":
        adapter.signer.credentials = None
    with pytest.raises(CapabilityUnavailable):
        await adapter.sign(draft, device_id="d2" if missing == "device" else "d1")


@pytest.mark.parametrize("mutation", ["tamper", "device", "unbound_key", "revoked", "device_role"])
async def test_current_binding_role_and_signature_rejected(control_case, mutation):
    adapter, draft, state, *_ = control_case
    command = await adapter.sign(draft, device_id="d1")
    device_id = "d1"
    if mutation == "tamper":
        command["parameters"]["parameters"]["path"] = "other.txt"
    elif mutation == "device":
        device_id = "d2"
    elif mutation == "revoked":
        state.revoke_key("control1", expected_revision=0)
    else:
        original = state.lookup("control1", device_id="d1")
        import base64

        from uaw.shared.runner_signatures import sign

        key_id = "unbound"
        state.register_key(
            VerificationKey(
                key_id,
                "d1",
                original.public_bytes,
                "device" if mutation == "device_role" else "control",
            )
        )
        private = base64.b64decode(
            adapter.signer.credentials.values["control-private"].get_secret_value()
        )
        command["signature"] = sign(command, private, "d1", key_id, "command")
    with pytest.raises(DomainError):
        await adapter.verify(command, device_id=device_id)


@pytest.mark.parametrize("change", ["expires_at", "deadline", "revoked", "private", "body"])
async def test_async_credential_changes_and_fixed_body(control_case, change):
    adapter, draft, state, vault, clock = control_case
    original = json.loads(json.dumps(draft))

    def mutate():
        if change in ("expires_at", "deadline"):
            clock[0] += timedelta(hours=1)
        elif change == "revoked":
            state.revoke_key("control1", expected_revision=0)
        elif change == "private":
            from pydantic import SecretStr

            vault.values["control-private"] = SecretStr("invalid")
        else:
            draft["parameters"]["parameters"]["path"] = "mutable-caller.txt"

    vault.on_resolve = mutate
    if change == "body":
        signed = await adapter.sign(draft, device_id="d1")
        assert {k: v for k, v in signed.items() if k != "signature"} == original
    else:
        with pytest.raises(DomainError):
            await adapter.sign(draft, device_id="d1")


async def test_cancellation_during_secure_store_propagates(control_case):
    adapter, draft, state, vault, _ = control_case
    started = asyncio.Event()

    class BlockedVault:
        async def resolve(self, handle):
            started.set()
            await asyncio.Event().wait()

    adapter.signer = ProtectedSigner(state, BlockedVault())
    task = asyncio.create_task(adapter.sign(draft, device_id="d1"))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


async def test_wrong_provisioned_control_role_cannot_sign(control_case):
    adapter, draft, state, *_ = control_case
    key = state.lookup("control1", device_id="d1")
    state.register_key(VerificationKey("device1", "d1", key.public_bytes, "device"))
    wrong = ControlCommandSigner(
        (ControlKeyBinding("d1", "device1", "control-private"),),
        directory=state,
        signer=adapter.signer,
        clock=lambda: NOW,
    )
    with pytest.raises(DomainError):
        await wrong.sign(draft, device_id="d1")
