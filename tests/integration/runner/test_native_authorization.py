"""Real Windows IPC/OS keys/temp roots; affirmative UI is an explicit double."""

import asyncio
from dataclasses import replace
from datetime import timedelta

import pytest
from uaw_runner.keys import ProtectedSigner
from uaw_runner.native_authorization import NativeReadAuthorization
from uaw_runner.native_confirmation import RegisteredNativeChallenges, WindowsNativeConfirmation
from uaw_runner.native_dialog import NativeDirectoryDecision
from uaw_runner.pairing import LocalRoots, PairingVerifier, PersistentRootSelection
from uaw_runner.read_executor import DeviceSigningBinding
from uaw_runner.state import LocalState

from tests.integration.runner.test_native_root_source import make_native_case
from tests.integration.runner.test_windows_ipc import ipc_case as _ipc_fixture
from tests.integration.runner.test_windows_ipc import ready_registry
from uaw.shared.errors import DomainError

ipc_case = _ipc_fixture


async def lifecycle_setup(case, *, clock_start=None):
    native = await make_native_case(
        case["tmp"],
        credentials=case["store"],
        device_handle=case["handles"][0],
        control_handle=case["handles"][1],
        existing_keys=case["keys"],
        defer_confirmation=True,
        clock_start=clock_start,
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
        source=challenge,
        directory=native["state"],
        clock=lambda: native["clock"][0],
        local_roots=native["local"],
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
            stat = native["root"].stat()
            return NativeDirectoryDecision(native["root"], (stat.st_dev, stat.st_ino))

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


async def read_native(native, case, mode="read"):
    from tests.integration.runner.test_read_executor import configure
    from tests.integration.runner.test_windows_read_ipc import endpoint_setup

    native["target"] = native["root"] / "file.txt"
    native["target"].write_bytes("Native selected read 原文\r\n".encode())
    await configure(native)
    case["registry"]["command_ref"] = native["command_ref"].wire()
    return await endpoint_setup(case, native, mode)


async def test_native_selection_to_actual_dual_process_read_reconnect_and_recovery(
    ipc_case, monkeypatch
):
    from uaw_runner.receipts import canonical

    from tests.integration.runner.test_windows_read_ipc import child_result

    native = await lifecycle_setup(ipc_case)
    ui_double(monkeypatch, native)
    selection = await select(native)
    await native["lifecycle"].bind(selection, native["workspace"])
    endpoint, process, registry = await read_native(native, ipc_case)
    receipt_ref = await endpoint.serve_once()
    reply = await child_result(process)
    assert reply["receipt"]["payload"]["result"]["text"] == "Native selected read 原文\r\n"
    native["protocol"].verify_receipt(canonical(reply["receipt"]), command=native["command"])
    assert native["state"].get(native["ticket_id"], now=native["clock"][0]).state == "consumed"
    await registry.close()
    old_ref = endpoint.session.channel_ref
    native["authority"].value["cancelled"] = True
    native["target"].unlink()
    from tests.integration.runner.test_windows_read_ipc import endpoint_setup

    recovered, child, recovered_registry = await endpoint_setup(ipc_case, native, "recover")
    assert recovered.session.channel_ref.wire() != old_ref.wire()
    assert (await recovered.serve_once()).wire() == receipt_ref.wire()
    assert (await child_result(child))["receipt"] == reply["receipt"]
    await recovered_registry.close()
    await native["registry"].close()


@pytest.mark.parametrize("change", ["root_revoke", "key_revoke", "owner", "expiry", "replace_root"])
async def test_native_grant_changes_block_new_file_read(ipc_case, monkeypatch, change):
    from uaw_runner.root_source import PersistentRootGrants

    native = await lifecycle_setup(ipc_case)
    ui_double(monkeypatch, native)
    selection = await select(native)
    await native["lifecycle"].bind(selection, native["workspace"])
    endpoint, process, registry = await read_native(native, ipc_case)
    if change == "root_revoke":
        await native["lifecycle"].revoke("native-root1", expected_revision=0)
        assert PersistentRootGrants(native["grants"].state.path).get("native-root1").revoked
    elif change == "key_revoke":
        native["state"].revoke_key("device1", expected_revision=0)
    elif change == "owner":
        native["owners"].revoked = True
    elif change == "expiry":
        native["clock"][0] += timedelta(minutes=10)
    elif change == "replace_root":
        native["root"].rename(native["root"].with_name("old-native-root"))
        native["root"].mkdir()
        native["target"].write_bytes(b"replacement")
    monkeypatch.setattr(
        "uaw_runner.read_executor.WindowsReadHandle",
        lambda *args: pytest.fail("no revoked root OS open"),
    )
    with pytest.raises(DomainError):
        await endpoint.serve_once()
    await registry.close()
    await native["registry"].close()


async def test_native_pending_real_window_cancellation_does_not_approve(ipc_case):
    import hashlib

    from uaw.shared.runner_signatures import signing_bytes

    native = await lifecycle_setup(ipc_case)
    value = await native["challenge"].current(native["ticket_id"])
    doc_hash = hashlib.sha256(
        signing_bytes(value.ticket.document(), "d1", "device1", "pairing-proof")
    ).hexdigest()
    native["native_confirmation"].timeout = 0.8
    with pytest.raises(DomainError) as exc:
        await native["native_confirmation"].confirm(
            ticket_id=value.ticket.ticket_id,
            principal_id="u1",
            device_id="d1",
            document_hash=doc_hash,
        )
    assert exc.value.failure.code == "native_timeout"
    assert native["state"].get(native["ticket_id"], now=native["clock"][0]).state == "pending"
    await native["registry"].close()


@pytest.mark.parametrize("change", ["expiry", "cancel"])
async def test_checked_ticket_approval_cas_rolls_back_current_change(ipc_case, change):
    native = await lifecycle_setup(ipc_case)
    calls = [0]

    def check():
        calls[0] += 1
        if calls[0] == 3:
            if change == "expiry":
                return native["clock"][0] + timedelta(minutes=10)
            from uaw.shared.errors import reject

            raise reject("native_cancelled", "Fixture cancelled at CAS", 409, "cancelled")
        return native["clock"][0]

    with pytest.raises(DomainError):
        await asyncio.to_thread(
            native["state"].approve,
            native["ticket_id"],
            expected_revision=0,
            code=native["issued"].verification_code,
            confirmation_hash="a" * 64,
            confirmation_expires_at=native["clock"][0] + timedelta(minutes=1),
            now=native["clock"][0],
            check=check,
        )
    assert native["state"].get(native["ticket_id"], now=native["clock"][0]).state == "pending"
    await native["registry"].close()


async def test_original_decision_full_session_survives_reopen_and_cannot_rebind_new_owner(
    ipc_case, monkeypatch
):
    from uaw_runner.native_authorization import NativeDecisionJournal

    from uaw.shared.contracts import Principal

    native = await lifecycle_setup(ipc_case)
    ui_double(monkeypatch, native)
    selection = await select(native)
    decision = NativeDecisionJournal(LocalRoots(native["local"].state.path))
    ticket = native["state"].get(native["ticket_id"], now=native["clock"][0])
    owner = native["owners"].value
    decision.check(selection.root_handle, ticket, owner, owner)
    changed = Principal(id="u1", kind="user", auth_session_id="new-session")
    with pytest.raises(DomainError):
        decision.check(selection.root_handle, ticket, changed, changed)
    await native["lifecycle"].bind(selection, native["workspace"])
    await native["registry"].close()


async def test_native_junction_selection_is_rejected_without_consumption(ipc_case, monkeypatch):
    import subprocess

    native = await lifecycle_setup(ipc_case)
    target = native["root"].with_name("junction-target")
    native["root"].rename(target)
    await asyncio.to_thread(
        subprocess.run,
        ["cmd", "/c", "mklink", "/J", str(native["root"]), str(target)],
        capture_output=True,
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    try:
        ui_double(monkeypatch, native)
        with pytest.raises(DomainError):
            await select(native)
        assert native["state"].get(native["ticket_id"], now=native["clock"][0]).state == "pending"
    finally:
        native["root"].rmdir()  # junction only, owned temporary target stays until fixture cleanup
        await native["registry"].close()
