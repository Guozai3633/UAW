"""Actual temp directories, persisted consumed-selection/grant and crypto.

Native user confirmation and device owner service are explicitly controlled fixtures, not IPC.
"""

import asyncio
import base64
import json
import subprocess
import sys
from dataclasses import replace
from datetime import timedelta
from threading import Event

import pytest
from uaw_runner.assembly import RegisteredPrincipalMapping, assemble_runner_adapters
from uaw_runner.control_signing import ControlKeyBinding
from uaw_runner.keys import ProtectedSigner
from uaw_runner.pairing import LocalRoots, PairingVerifier, PersistentRootSelection
from uaw_runner.root_source import NativeRootSource, PersistentRootGrants
from uaw_runner.state import LocalState

from tests.unit.runner.conftest import NOW
from tests.unit.runner.test_protocol import failure_receipt
from tests.unit.runner.test_real_keys import CredentialFixture
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, DomainError, reject
from uaw.shared.runner_signatures import VerificationKey, sign
from uaw.workspace.binding import RootBindings
from uaw.workspace.ports import NativeConfirmation
from uaw.workspace.repository import MemoryAdmissionRepository


class CurrentOwnerFixture:
    """Independent device/channel ownership registry; no command received by this adapter."""

    def __init__(self):
        self.value = Principal(id="u1", kind="user", auth_session_id="s1")
        self.device = "d1"
        self.revoked = False
        self.hook = None
        self.calls = 0

    async def owner(self, actor, device_id):
        self.calls += 1
        if self.hook:
            await self.hook(self.calls)
        if self.revoked or device_id != self.device or actor.wire() != self.value.wire():
            raise reject(
                "permission_denied", "Fixture actual device/channel denied", 403, "permission"
            )
        return self.value


class NativeConfirmationFixture:
    """Controlled test adapter only; NOT real OS user confirmation or production IPC."""

    def __init__(self, path):
        self.path = path

    async def confirm(self, **request):
        return NativeConfirmation(
            **request, native_path=self.path, expires_at=NOW + timedelta(minutes=5)
        )


@pytest.fixture
async def native_case(tmp_path):
    return await make_native_case(tmp_path)


async def make_native_case(
    tmp_path,
    *,
    credentials=None,
    device_handle="device-private",
    control_handle="control-private",
    existing_keys=None,
    defer_confirmation=False,
    clock_start=None,
):
    clock = [clock_start if clock_start is not None else NOW]
    state = (
        existing_keys
        if existing_keys is not None
        else LocalState(tmp_path / "control" / "keys-selections.sqlite")
    )
    local = LocalRoots(tmp_path / "native" / "roots.sqlite")
    grants = PersistentRootGrants(tmp_path / "native" / "grants.sqlite")
    vault = credentials if credentials is not None else CredentialFixture()
    protected = ProtectedSigner(state, vault)
    for key_id, handle, role in (
        ("device1", device_handle, "device"),
        ("control1", control_handle, "control"),
    ):
        if existing_keys is None:
            public = await protected.provision_private(credential_handle=handle)
            state.register_key(VerificationKey(key_id, "d1", public, role))
        else:
            assert state.lookup(key_id, device_id="d1").role == role
            if role == "device":
                await protected.check_private(
                    device_id="d1", key_id=key_id, credential_handle=handle
                )
    root = tmp_path / "selected-project"
    root.mkdir()
    workspace = Ref(kind="workspace", id="workspace1", version="1", content_hash="a" * 64)
    owners = CurrentOwnerFixture()
    mapping = RegisteredPrincipalMapping(owners)
    issued = state.issue(
        request_id="root-request",
        kind="root",
        principal_id="u1",
        device_id="d1",
        key_id="device1",
        public_bytes=state.lookup("device1", device_id="d1").public_bytes,
        expires_at=clock[0] + timedelta(minutes=10),
        now=clock[0],
        root_handle="native-root1",
        display_name="temporary test root",
    )
    verifier = PairingVerifier(
        state, native=NativeConfirmationFixture(root), clock=lambda: clock[0], roots=local
    )
    proof = await protected.sign_document(
        issued.ticket.document(),
        device_id="d1",
        key_id="device1",
        domain="pairing-proof",
        credential_handle=device_handle,
    )
    selection = None
    if not defer_confirmation:
        await verifier.approve(
            issued.ticket.ticket_id,
            expected_revision=0,
            principal_id="u1",
            code=issued.verification_code,
            proof_signature=proof,
        )
        selection = await verifier.root_selection(
            issued.ticket.ticket_id, signer=protected, credential_handle=device_handle
        )
    bindings = RootBindings(grants, PersistentRootSelection(state, local))
    source = NativeRootSource(
        bindings,
        grants=grants,
        selections=state,
        native_roots=local,
        mapping=mapping,
        directory=state,
        clock=lambda: clock[0],
    )
    ctx = TrustedExecutionContext.model_validate_json(
        json.dumps(
            {
                "principal": owners.value.wire(),
                "scope": {
                    "principal_id": "u1",
                    "resource_refs": [workspace.wire()],
                    "capabilities": ["file.read", "file.list"],
                },
                "operation_id": "op1",
                "trace_id": "trace1",
                "attempt_id": "attempt1",
                "deadline": (clock[0] + timedelta(hours=1)).isoformat(),
                "capability_policy_ref": {"kind": "policy", "id": "policy1", "version": "1"},
            }
        )
    )
    return dict(
        issued=issued,
        verifier=verifier,
        proof=proof,
        device_handle=device_handle,
        control_handle=control_handle,
        source=source,
        state=state,
        local=local,
        grants=grants,
        vault=vault,
        clock=clock,
        root=root,
        workspace=workspace,
        owners=owners,
        mapping=mapping,
        selection=selection,
        ctx=ctx,
        ticket_id=issued.ticket.ticket_id,
    )


async def bind(case):
    await case["source"].bind(
        case["selection"],
        case["workspace"],
        device_id="d1",
        authenticated_principal=case["owners"].value,
    )


async def current(case):
    return await case["source"].current("d1", case["workspace"], case["ctx"])


def alter_grant(case, **changes):
    with case["grants"].state.transaction() as db:
        row = db.execute("SELECT grant_data FROM root_grants").fetchone()
        data = json.loads(row[0])
        data.update(changes)
        db.execute("UPDATE root_grants SET grant_data=?", (json.dumps(data),))


async def test_actual_consumption_persisted_grant_restart_opaque_snapshot(native_case):
    case = native_case
    await bind(case)
    assert case["state"].get(case["ticket_id"], now=NOW).state == "consumed"
    first = await current(case)
    assert first == {
        "owner": case["owners"].value.wire(),
        "device_id": "d1",
        "workspace_ref": case["workspace"].wire(),
        "root_handle": "native-root1",
        "binding_revision": 0,
        "allowed_actions": ["file.read", "file.list"],
        "expires_at": (NOW + timedelta(minutes=5)).isoformat(),
    }
    assert "native_path" not in json.dumps(first) and str(case["root"]) not in json.dumps(first)
    grants = PersistentRootGrants(case["grants"].state.path)
    state = LocalState(case["state"].path)
    local = LocalRoots(case["local"].state.path)
    rebuilt = NativeRootSource(
        RootBindings(grants, PersistentRootSelection(state, local)),
        grants=grants,
        selections=state,
        native_roots=local,
        mapping=case["mapping"],
        directory=state,
        clock=lambda: NOW,
    )
    assert await rebuilt.current("d1", case["workspace"], case["ctx"]) == first
    with pytest.raises(DomainError):
        await bind(case)  # Selection cannot be consumed again.


@pytest.mark.parametrize(
    "missing", ["mapping", "grants", "selections", "native_roots", "directory"]
)
async def test_missing_actual_sources_never_use_command_owner(native_case, missing):
    case = native_case
    await bind(case)
    setattr(case["source"], missing, None)
    with pytest.raises(CapabilityUnavailable):
        await current(case)


async def test_no_grant_or_no_native_confirmation_cannot_authorize(native_case):
    case = native_case
    with pytest.raises(DomainError):
        await current(case)
    verifier = PairingVerifier(case["state"], native=None, clock=lambda: NOW, roots=case["local"])
    with pytest.raises(CapabilityUnavailable):
        await verifier.approve(
            case["ticket_id"],
            expected_revision=0,
            principal_id="u1",
            code="fixture",
            proof_signature="not-a-proof",
        )
    case["source"].bindings.selection_port = None
    with pytest.raises(CapabilityUnavailable):
        await bind(case)


@pytest.mark.parametrize(
    "field",
    [
        "owner",
        "expires_at",
        "confirmation_expires_at",
        "selection_ticket_id",
        "selection_key_id",
        "selection_signature",
    ],
)
async def test_old_grants_without_proof_or_bounded_deadline_are_refused(native_case, field):
    case = native_case
    await bind(case)
    alter_grant(case, **{field: None})
    with pytest.raises(DomainError, match="lacks actual"):
        await current(case)


@pytest.mark.parametrize(
    "mutation", ["owner_id", "session", "delegation", "device", "workspace", "scope"]
)
async def test_actual_principal_device_and_pinned_workspace(native_case, mutation):
    case = native_case
    await bind(case)
    ctx = case["ctx"].wire()
    device = "d1"
    workspace = case["workspace"]
    if mutation in ("owner_id", "session", "delegation"):
        field = {"owner_id": "id", "session": "auth_session_id", "delegation": "delegated_by"}[
            mutation
        ]
        ctx["principal"][field] = "different"
        if field == "id":
            ctx["scope"]["principal_id"] = "different"
    elif mutation == "device":
        device = "d2"
    elif mutation == "workspace":
        workspace = Ref(kind="workspace", id="workspace1", version="2", content_hash="b" * 64)
        ctx["scope"]["resource_refs"] = [workspace.wire()]
    else:
        ctx["scope"]["resource_refs"] = []
    with pytest.raises(DomainError):
        await case["source"].current(
            device, workspace, TrustedExecutionContext.model_validate_json(json.dumps(ctx))
        )


@pytest.mark.parametrize(
    "mutation", ["key", "grant", "owner", "confirmation", "ticket", "signature", "identity"]
)
async def test_current_root_key_proof_grant_and_directory_revocation(native_case, mutation):
    case = native_case
    await bind(case)
    if mutation == "key":
        case["state"].revoke_key("device1", expected_revision=0)
    elif mutation == "grant":
        case["grants"].revoke("native-root1", expected_revision=0)
    elif mutation == "owner":
        case["owners"].revoked = True
    elif mutation in ("confirmation", "ticket"):
        with case["state"].transaction() as db:
            field = "confirmation_hash" if mutation == "confirmation" else "state"
            db.execute(
                f"UPDATE tickets SET {field}=? WHERE ticket_id=?",
                ("a" * 64 if mutation == "confirmation" else "approved", case["ticket_id"]),
            )
    elif mutation == "signature":
        alter_grant(case, selection_signature="not-a-signature")
    else:
        alter_grant(case, file_identity=[0, 0])
    with pytest.raises(DomainError):
        await current(case)


@pytest.mark.parametrize("when", ["before", "during_mapping", "during_final_mapping"])
async def test_expiry_is_checked_with_fresh_time_after_await(native_case, when):
    case = native_case
    await bind(case)
    case["owners"].calls = 0
    if when == "before":
        case["clock"][0] = NOW + timedelta(minutes=5)
    else:

        async def expire(n):
            if n == (1 if when == "during_mapping" else 2):
                case["clock"][0] = NOW + timedelta(minutes=5)

        case["owners"].hook = expire
    with pytest.raises(DomainError) as error:
        await current(case)
    assert error.value.failure.code == "deadline_exceeded"


@pytest.mark.parametrize("mutation", ["owner", "key", "grant"])
async def test_owner_and_external_local_state_rechecked_after_second_mapping(native_case, mutation):
    case = native_case
    await bind(case)
    case["owners"].calls = 0

    async def change(n):
        if n != 2:
            return
        if mutation == "owner":
            case["owners"].revoked = True
        elif mutation == "key":
            case["state"].revoke_key("device1", expected_revision=0)
        else:
            case["grants"].revoke("native-root1", expected_revision=0)

    case["owners"].hook = change
    with pytest.raises(DomainError):
        await current(case)


async def test_replaced_native_directory_not_reused_after_restart(native_case):
    case = native_case
    await bind(case)
    case["root"].rename(case["root"].with_name("old-selected-project"))
    case["root"].mkdir()
    with pytest.raises(DomainError):
        await current(case)


async def test_real_native_junction_escape_preserves_only_temporary_roots(native_case, tmp_path):
    case = native_case
    await bind(case)
    outside = tmp_path / "outside"
    outside.mkdir()
    link = case["root"] / "escape"
    if sys.platform == "win32":
        result = await asyncio.to_thread(
            subprocess.run,
            ["cmd.exe", "/c", "mklink", "/J", str(link), str(outside)],
            capture_output=True,
        )
        assert result.returncode == 0
    else:
        link.symlink_to(outside, target_is_directory=True)
    try:
        with pytest.raises(DomainError):
            case["source"].bindings.check_scope(
                root_handle="native-root1",
                principal_id="u1",
                device_id="d1",
                workspace_ref=case["workspace"],
                expected_revision=0,
                relative_path="escape",
                now=NOW,
            )
    finally:
        if sys.platform == "win32":
            link.rmdir()
        else:
            link.unlink()


async def test_cooperative_cancel_mapping_and_blocking_grants_leave_loop_available(native_case):
    case = native_case
    await bind(case)
    started = asyncio.Event()

    async def blocked(n):
        started.set()
        await asyncio.Event().wait()

    case["owners"].hook = blocked
    task = asyncio.create_task(current(case))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    case["owners"].hook = None
    entered, release, done = Event(), Event(), Event()
    original = case["grants"].find

    def slow(**kwargs):
        entered.set()
        release.wait(3)
        try:
            return original(**kwargs)
        finally:
            done.set()

    case["grants"].find = slow
    task = asyncio.create_task(current(case))
    assert await asyncio.to_thread(entered.wait, 2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    release.set()
    assert await asyncio.to_thread(done.wait, 2)


async def test_actual_component_assembly_root_sign_admission_and_original_journal(native_case):
    case = native_case
    await bind(case)
    command_draft = {
        "command_id": "assembled-command",
        "operation_id": "op1",
        "request_ref": {"kind": "check", "id": "assembled-request", "version": "1"},
        "trusted_context": case["ctx"].wire(),
        "expires_at": (NOW + timedelta(minutes=4)).isoformat(),
        "fencing_token": 2,
        "parameters": {
            "action": "file.list",
            "parameters": {"workspace_id": "workspace1", "path": "."},
        },
    }

    class CurrentAuthorityFixture:
        """Component source assembled from pre-registered exact command and real root adapter.

        It does not consume incoming command claims. Actual platform authority belongs to A.
        """

        async def current(self, ignored_command, *, authenticated_principal):
            root = await case["source"].current("d1", case["workspace"], case["ctx"])
            return {
                "context": case["ctx"].wire(),
                "device_id": "d1",
                "root_handle": root["root_handle"],
                "workspace_ref": case["workspace"].wire(),
                "binding_revision": root["binding_revision"],
                "fencing_token": 2,
                "lease_expires_at": (NOW + timedelta(minutes=4)).isoformat(),
                "request_ref": command_draft["request_ref"],
                "request_parameters": command_draft["parameters"],
                "policy_ref": case["ctx"].capability_policy_ref.wire(),
                "required_scope_capability": "file.list",
                "allowed_actions": root["allowed_actions"],
                "feature_enabled": True,
                "connected": True,
                "cancelled": False,
            }

    from tests.unit.runner.test_receipts import RegisteredSourceFixture
    from uaw.workspace.contracts import RunnerCommand

    first = assemble_runner_adapters(
        device_id="d1",
        control_bindings=(ControlKeyBinding("d1", "control1", "control-private"),),
        directory=case["state"],
        credentials=case["vault"],
        grants=case["grants"],
        admissions=MemoryAdmissionRepository(),
        selections=case["state"],
        native_roots=case["local"],
        mapping=case["mapping"],
        authority=CurrentAuthorityFixture(),
        receipt_commands=None,
        journal_path=case["root"].parent / "journal.sqlite",
        clock=lambda: case["clock"][0],
    )
    signed = await first.control_signing.sign(command_draft, device_id="d1")
    assert await first.control_signing.verify(signed, device_id="d1") is None
    admission = await first.protocol.admit_async(
        json.dumps(signed), authenticated_principal=case["owners"].value
    )
    assert admission.attempt_id == "attempt1"
    receipt_reader = RegisteredSourceFixture(
        RunnerCommand.model_validate_json(json.dumps(signed)), "d1"
    )
    first.journal.reader = receipt_reader
    receipt = failure_receipt(receipt_reader.record.command)
    receipt["attempt_id"] = receipt["usage"]["attempt_id"] = "attempt1"
    receipt["signature"] = sign(
        receipt,
        base64.b64decode(case["vault"].values["device-private"].get_secret_value()),
        "d1",
        "device1",
        "receipt",
    )
    # This is deliberately a signed protocol fixture, not a claim that admission executed.
    ref = await first.journal.publish(
        receipt_reader.ref, json.dumps(receipt), authenticated_principal=case["owners"].value
    )
    assert (
        ref.kind == "content"
        and (await first.journal.read(ref, authenticated_principal=case["owners"].value)).wire()
        == receipt
    )
    first.protocol.admissions.cancel("u1", "d1", "assembled-command")
    case["clock"][0] = NOW + timedelta(days=1)
    assert (
        await first.journal.read(ref, authenticated_principal=case["owners"].value)
    ).wire() == receipt
    with pytest.raises(DomainError):
        await first.protocol.admit_async(
            json.dumps(signed), authenticated_principal=case["owners"].value
        )
    with pytest.raises(DomainError):
        await first.roots.current("d1", case["workspace"], case["ctx"])


async def test_mapping_missing_registered_device_service(native_case):
    case = native_case
    with pytest.raises(CapabilityUnavailable):
        await RegisteredPrincipalMapping(None).owner(
            authenticated_principal=case["owners"].value, device_id="d1"
        )


@pytest.mark.parametrize("mutation", ["role", "domain", "public_key", "revoked"])
async def test_independent_current_directory_cannot_use_stale_selection_key(native_case, mutation):
    case = native_case
    await bind(case)
    key = case["state"].lookup("device1", device_id="d1")

    class CurrentDirectoryFixture:
        def lookup(self, key_id, *, device_id):
            if mutation == "role":
                return replace(key, role="control")
            if mutation == "public_key":
                return replace(key, public_bytes=b"x" * 32)
            if mutation == "revoked":
                return replace(key, revoked=True)
            return key

    case["source"].directory = CurrentDirectoryFixture()
    if mutation == "domain":
        ticket = case["state"].get(case["ticket_id"], now=NOW)
        signature = sign(
            ticket.document(),
            base64.b64decode(case["vault"].values["device-private"].get_secret_value()),
            "d1",
            "device1",
            "pairing-proof",
        )
        alter_grant(case, selection_signature=signature)
    with pytest.raises(DomainError):
        await current(case)


async def test_expiry_guard_on_actual_async_admission(native_case):
    case = native_case
    await bind(case)
    # The existing async admission path now checks bounded grant time in its final external
    # root check too; no authority fixture can turn an expired root into a fresh permit.
    options = dict(
        root_handle="native-root1",
        principal_id="u1",
        device_id="d1",
        workspace_ref=case["workspace"],
        expected_revision=0,
        relative_path=".",
    )
    assert case["source"].bindings.check_scope(**options, now=NOW) == case["root"]
    with pytest.raises(DomainError) as error:
        case["source"].bindings.check_scope(**options, now=NOW + timedelta(minutes=5))
    assert error.value.failure.code == "deadline_exceeded"


async def test_root_grant_revoke_cas_survives_reopen(native_case):
    case = native_case
    await bind(case)
    revoked = case["grants"].revoke("native-root1", expected_revision=0)
    assert revoked.revoked and revoked.revision == 1
    reopened = PersistentRootGrants(case["grants"].state.path)
    assert reopened.get("native-root1") == revoked
    with pytest.raises(DomainError):
        reopened.revoke("native-root1", expected_revision=0)


async def test_root_request_deadline_after_mapping(native_case):
    case = native_case
    await bind(case)
    data = case["ctx"].wire()
    data["deadline"] = (NOW + timedelta(seconds=1)).isoformat()
    case["ctx"] = TrustedExecutionContext.model_validate_json(json.dumps(data))

    async def expire(n):
        case["clock"][0] = NOW + timedelta(seconds=1)

    case["owners"].hook = expire
    with pytest.raises(DomainError) as error:
        await current(case)
    assert error.value.failure.code == "deadline_exceeded"


async def test_root_expiry_is_persisted_and_clock_rollback_never_restores_grant(native_case):
    case = native_case
    await bind(case)
    case["clock"][0] = NOW + timedelta(minutes=5)
    with pytest.raises(DomainError):
        await current(case)
    assert case["grants"].get("native-root1").revoked
    case["clock"][0] = NOW
    with pytest.raises(DomainError):
        await current(case)
    reopened = PersistentRootGrants(case["grants"].state.path)
    assert reopened.get("native-root1").revoked


@pytest.mark.parametrize(
    "field", ["owner", "expires_at", "confirmation_expires_at", "selection_signature"]
)
async def test_old_serialized_grant_missing_fields_does_not_gain_defaults(native_case, field):
    case = native_case
    await bind(case)
    with case["grants"].state.transaction() as db:
        data = json.loads(db.execute("SELECT grant_data FROM root_grants").fetchone()[0])
        data.pop(field)
        db.execute("UPDATE root_grants SET grant_data=?", (json.dumps(data),))
    with pytest.raises(DomainError):
        await current(case)


async def test_persistent_grant_single_cas_under_thread_competition(native_case):
    case = native_case
    await bind(case)
    from concurrent.futures import ThreadPoolExecutor

    def revoke():
        try:
            return case["grants"].revoke("native-root1", expected_revision=0).revision
        except DomainError as exc:
            return exc.failure.code

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: revoke(), range(8)))
    assert results.count(1) == 1 and results.count("revision_conflict") == 7


async def test_persistent_root_source_read_in_new_python_process(native_case):
    case = native_case
    await bind(case)
    from pathlib import Path

    registry = case["root"].parent / "root-registry-fixture.json"
    registry.write_text(
        json.dumps(
            {
                "owner": case["owners"].value.wire(),
                "device_id": "d1",
                "context": case["ctx"].wire(),
                "workspace": case["workspace"].wire(),
                "now": NOW.isoformat(),
            }
        ),
        encoding="utf-8",
    )
    result = await asyncio.to_thread(
        subprocess.run,
        [
            sys.executable,
            str(Path(__file__).with_name("root_source_child.py")),
            str(case["root"].parent),
            str(registry),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == await current(case)
    assert str(case["root"]) not in result.stdout


async def test_global_key_revocation_rejects_selection_before_consume(native_case):
    case = native_case
    key = case["state"].lookup("device1", device_id="d1")

    class RevokedCurrentDirectory:
        def lookup(self, key_id, *, device_id):
            return replace(key, revoked=True)

    case["source"].bindings.selection_port = PersistentRootSelection(
        case["state"], case["local"], directory=RevokedCurrentDirectory()
    )
    with pytest.raises(DomainError):
        await bind(case)
    assert case["state"].get(case["ticket_id"], now=NOW).state == "approved"
    with pytest.raises(DomainError):
        case["grants"].get("native-root1")
