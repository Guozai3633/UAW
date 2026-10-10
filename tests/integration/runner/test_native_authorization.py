"""Real Windows IPC/OS keys/temp roots; affirmative UI is an explicit double."""

import asyncio
from dataclasses import replace
from datetime import timedelta

import pytest
from uaw_runner.keys import ProtectedSigner
from uaw_runner.native_authorization import NativeReadAuthorization
from uaw_runner.native_confirmation import RegisteredNativeChallenges, WindowsNativeConfirmation
from uaw_runner.pairing import LocalRoots, PairingVerifier, PersistentRootSelection
from uaw_runner.read_executor import DeviceSigningBinding
from uaw_runner.state import LocalState

from tests.integration.runner.test_native_root_source import make_native_case
from tests.integration.runner.test_windows_ipc import ipc_case as _ipc_fixture
from tests.integration.runner.test_windows_ipc import ready_registry
from uaw.shared.errors import DomainError

ipc_case = _ipc_fixture


async def lifecycle_setup(case):
    native = await make_native_case(
        case["tmp"],
        credentials=case["store"],
        device_handle=case["handles"][0],
        control_handle=case["handles"][1],
        existing_keys=case["keys"],
        defer_confirmation=True,
    )
    session, process, path, registry, ref = await ready_registry(case)
    # Run clock is controlled; OS process/IPC clock/keyring remain real.
    challenge = RegisteredNativeChallenges(
        state=native["state"],
        registry=registry,
        channel_ref=ref,
        device_id="d1",
        mapping=native["mapping"],
        clock=lambda: native["clock"][0],
    )
    confirmation = WindowsNativeConfirmation(
        source=challenge, directory=native["state"], clock=lambda: native["clock"][0]
    )
    verifier = PairingVerifier(
        native["state"],
        native=confirmation,
        roots=native["local"],
        clock=lambda: native["clock"][0],
    )
    lifecycle = NativeReadAuthorization(
        native=confirmation,
        challenges=challenge,
        verifier=verifier,
        signer=ProtectedSigner(native["state"], native["vault"]),
        device_key=DeviceSigningBinding("d1", "device1", case["handles"][0]),
        roots=native["source"],
    )
    native.update(
        lifecycle=lifecycle,
        session=session,
        process=process,
        registry=registry,
        challenge=challenge,
        native_confirmation=confirmation,
        tmp=case["tmp"],
    )
    return native


def ui_double(monkeypatch, native, *, hook=None):
    class SelectionUiDouble:
        def show(self, prompt, stopped, deadline):
            assert prompt.select_root and prompt.account == "u1" and prompt.device == "d1"
            if hook:
                hook()
            return native["root"]

    monkeypatch.setattr("uaw_runner.native_confirmation.WindowsNativeDialog", SelectionUiDouble)


async def select(native):
    return await native["lifecycle"].select(
        native["ticket_id"],
        expected_revision=0,
        code=native["issued"].verification_code,
        proof_signature=native["proof"],
    )


async def test_registered_os_channel_to_once_selection_bind_and_revoke(ipc_case, monkeypatch):
    native = await lifecycle_setup(ipc_case)
    ui_double(monkeypatch, native)
    selection = await select(native)
    assert str(native["root"]) not in str(selection.wire())
    assert native["state"].get(native["ticket_id"], now=native["clock"][0]).state == "approved"
    await native["lifecycle"].bind(selection, native["workspace"])
    assert native["state"].get(native["ticket_id"], now=native["clock"][0]).state == "consumed"
    with pytest.raises(DomainError):
        await native["lifecycle"].bind(selection, native["workspace"])
    await native["lifecycle"].revoke("native-root1", expected_revision=0)
    assert native["grants"].get("native-root1").revoked
    with pytest.raises(DomainError):
        await native["source"].current("d1", native["workspace"], native["ctx"])
    await native["registry"].close()


@pytest.mark.parametrize(
    "change",
    ["bad_proof", "bad_code", "owner", "device_key", "expiry", "owner_after_ui", "revoke_after_ui"],
)
async def test_lifecycle_never_consumes_mismatched_or_changed_confirmation(
    ipc_case, monkeypatch, change
):
    native = await lifecycle_setup(ipc_case)
    if change == "bad_proof":
        native["proof"] = "uaw-ed25519-v1:device1:invalid"
    elif change == "bad_code":
        native["issued"] = replace(native["issued"], verification_code="wrong")
    elif change == "owner":
        native["owners"].revoked = True
    elif change == "device_key":
        native["state"].revoke_key("device1", expected_revision=0)
    elif change == "expiry":
        native["clock"][0] += timedelta(minutes=10)

    def hook():
        if change == "owner_after_ui":
            native["owners"].revoked = True
        elif change == "revoke_after_ui":
            native["state"].revoke_key("device1", expected_revision=0)

    ui_double(monkeypatch, native, hook=hook)
    with pytest.raises(DomainError):
        await select(native)
    assert native["state"].get(native["ticket_id"], now=native["clock"][0]).state != "consumed"
    await native["registry"].close()


async def test_approved_selection_restart_keeps_original_proof_and_once_consumption(
    ipc_case, monkeypatch
):
    native = await lifecycle_setup(ipc_case)
    ui_double(monkeypatch, native)
    selection = await select(native)
    state = LocalState(native["state"].path)
    roots = LocalRoots(native["local"].state.path)
    port = PersistentRootSelection(state, roots)
    result = await asyncio.to_thread(
        port.consume, selection, principal_id="u1", device_id="d1", now=native["clock"][0]
    )
    assert result.native_path == native["root"] and result.capabilities == {"read"}
    with pytest.raises(DomainError):
        await asyncio.to_thread(
            port.consume, selection, principal_id="u1", device_id="d1", now=native["clock"][0]
        )
    await native["registry"].close()
