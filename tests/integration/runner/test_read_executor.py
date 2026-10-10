"""Real temp OS reads/crypto/SQLite. Registry, channel and authority are fixtures, NOT IPC."""

import asyncio
import hashlib
from copy import deepcopy
from datetime import timedelta

import pytest
from uaw_runner.admissions import PersistentAdmissions
from uaw_runner.control_signing import ControlCommandSigner, ControlKeyBinding
from uaw_runner.keys import Ed25519SignatureAdapter, ProtectedSigner
from uaw_runner.protocol import RunnerProtocol
from uaw_runner.read_executor import DeviceSigningBinding, ReadOnlyRunner
from uaw_runner.read_state import ReadExecutionJournal
from uaw_runner.receipts import ReceiptJournal, canonical, digest

from tests.integration.runner.test_native_root_source import bind
from tests.integration.runner.test_native_root_source import native_case as _native_fixture
from tests.unit.runner.conftest import NOW
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, DomainError, reject
from uaw.workspace.contracts import RegisteredReceiptCommand, RunnerCommand

native_case = _native_fixture


class RegisteredCommandFixture:
    """Fixed independent registry created before invocation; current data access checks."""

    def __init__(self, case, command, ref):
        self.case, self.command, self.ref = case, command, ref
        self.denied = False
        self.calls = 0
        self.hook = None

    async def resolve(self, command_ref, *, authenticated_principal):
        self.calls += 1
        if self.hook:
            await self.hook(self.calls)
        owner = await self.case["mapping"].owner(
            authenticated_principal=authenticated_principal, device_id="d1"
        )
        grant = self.case["grants"].get("native-root1")
        if self.denied or grant.revoked:
            raise reject(
                "permission_denied",
                "Fixture current receipt data permission denied",
                403,
                "permission",
            )
        if command_ref.wire() != self.ref.wire():
            raise reject("revision_conflict", "Fixture fixed command ref differs", 409)
        return RegisteredReceiptCommand(self.command, "d1", owner)


class RegisteredAuthorityFixture:
    """Explicit current component snapshot, never derives authority from received command."""

    def __init__(self, command, case):
        self.value = {
            "context": command.trusted_context.wire(),
            "device_id": "d1",
            "root_handle": "native-root1",
            "workspace_ref": case["workspace"].wire(),
            "binding_revision": 0,
            "fencing_token": command.fencing_token,
            "lease_expires_at": (case["clock"][0] + timedelta(minutes=5)).isoformat(),
            "request_ref": command.request_ref.wire(),
            "request_parameters": command.parameters,
            "policy_ref": command.trusted_context.capability_policy_ref.wire(),
            "required_scope_capability": "file.read",
            "allowed_actions": ["file.read"],
            "feature_enabled": True,
            "connected": True,
            "cancelled": False,
        }
        self.calls = 0
        self.hook = None

    async def current(self, command, *, authenticated_principal):
        self.calls += 1
        if self.hook:
            await self.hook(self.calls)
        return deepcopy(self.value)


class RegisteredChannelFixture:
    """Independent registered actor/owner/pairing/channel/key, not a transport implementation."""

    def __init__(self, case):
        self.ref = Ref(kind="content", id="test-channel", version="1", content_hash="c" * 64)
        self.value = {
            "device_id": "d1",
            "owner": case["owners"].value.wire(),
            "actor": case["owners"].value.wire(),
            "pairing_ref": {
                "kind": "content",
                "id": "test-pairing",
                "version": "1",
                "content_hash": "b" * 64,
            },
            "channel_ref": self.ref.wire(),
            "key_ref": {
                "kind": "content",
                "id": "device1",
                "version": "1",
                "content_hash": hashlib.sha256(
                    case["state"].lookup("device1", device_id="d1").public_bytes
                ).hexdigest(),
            },
            "connected": True,
            "expires_at": (NOW + timedelta(minutes=5)).isoformat(),
        }
        self.hook = None
        self.calls = 0

    async def read(self, channel_ref, *, device_id):
        self.calls += 1
        if self.hook:
            await self.hook(self.calls)
        if channel_ref.wire() != self.ref.wire() or device_id != "d1":
            raise reject("permission_denied", "Fixture channel not registered", 403, "permission")
        return deepcopy(self.value)


@pytest.fixture
async def read_case(native_case, tmp_path):
    case = native_case
    await bind(case)
    case["target"] = case["root"] / "file.txt"
    case["target"].write_bytes("hello 中😀\n".encode())
    case["tmp"] = tmp_path
    return await configure(case)


async def configure(case, *, parameters=None, action="file.read"):
    draft = {
        "command_id": "read-command",
        "operation_id": "op1",
        "request_ref": {
            "kind": "check",
            "id": "request1",
            "version": "1",
            "content_hash": "e" * 64,
        },
        "trusted_context": case["ctx"].wire(),
        "fencing_token": 1,
        "expires_at": (case["clock"][0] + timedelta(minutes=4)).isoformat(),
        "parameters": {
            "action": action,
            "parameters": parameters
            or {"workspace_ref": case["workspace"].wire(), "path": "file.txt"},
        },
    }
    signing = ControlCommandSigner(
        (ControlKeyBinding("d1", "control1", case.get("control_handle", "control-private")),),
        directory=case["state"],
        signer=ProtectedSigner(case["state"], case["vault"]),
        clock=lambda: case["clock"][0],
    )
    command = RunnerCommand.model_validate_json(
        canonical(await signing.sign(draft, device_id="d1"))
    )
    # Registered fixed Ref belongs to fixture registry, not inferred during execute.
    ref = Ref(
        kind="content", id="registered-command", version="1", content_hash=digest(command.wire())
    )
    reader = RegisteredCommandFixture(case, command, ref)
    authority = RegisteredAuthorityFixture(command, case)
    protocol = RunnerProtocol(
        device_id="d1",
        bindings=case["source"].bindings,
        admissions=PersistentAdmissions(case["tmp"] / "admissions.sqlite"),
        signatures=Ed25519SignatureAdapter(case["state"]),
        async_authority=authority,
        principal_mapping=case["mapping"],
        clock=lambda: case["clock"][0],
    )
    journal = ReceiptJournal(case["tmp"] / "receipts.sqlite", protocol=protocol, reader=reader)
    channel = RegisteredChannelFixture(case)
    executions = ReadExecutionJournal(case["tmp"] / "reads.sqlite")
    runner = ReadOnlyRunner(
        protocol=protocol,
        command_ref=ref,
        journal=journal,
        executions=executions,
        currency="CNY",
        roots=case["source"],
        channel=channel,
        channel_ref=channel.ref,
        signer=ProtectedSigner(case["state"], case["vault"]),
        device_key=DeviceSigningBinding(
            "d1", "device1", case.get("device_handle", "device-private")
        ),
    )
    case.update(
        command=command,
        command_ref=ref,
        reader=reader,
        authority=authority,
        protocol=protocol,
        journal=journal,
        channel=channel,
        runner=runner,
        executions=executions,
    )
    return case


async def execute(case):
    return await case["runner"].execute(
        case["command"], authenticated_principal=case["owners"].value
    )


async def test_actual_read_signed_terminal_pinned_ref(read_case):
    case = read_case
    receipt = await execute(case)
    assert receipt.kind == "ok"
    content = receipt.payload["result"]
    assert content["text"] == "hello 中😀\n"
    assert content["content_hash"] == hashlib.sha256(case["target"].read_bytes()).hexdigest()
    assert receipt.usage["billing_state"] == "pending"
    assert "money" not in receipt.usage["resources"]
    assert "wall_time_ms" in receipt.usage["resources"]
    assert str(case["root"]) not in canonical(receipt.wire())
    case["protocol"].verify_receipt(canonical(receipt.wire()), command=case["command"])
    source = await case["reader"].resolve(
        case["command_ref"], authenticated_principal=case["owners"].value
    )
    attempt = await asyncio.to_thread(case["executions"].get, source, case["command_ref"])
    assert attempt.receipt_ref.kind == "content" and attempt.receipt_ref.version == "1"
    assert attempt.receipt_ref.content_hash == digest(receipt.wire())
    assert (
        await case["journal"].read(
            attempt.receipt_ref, authenticated_principal=case["owners"].value
        )
    ).wire() == receipt.wire()


@pytest.mark.parametrize(
    "missing", ["channel", "channel_ref", "roots", "signer", "device_key", "executions"]
)
async def test_missing_real_dependencies_are_unavailable_before_read(
    read_case, monkeypatch, missing
):
    case = read_case
    setattr(case["runner"], missing, None)
    monkeypatch.setattr(
        "uaw_runner.read_executor.WindowsReadHandle", lambda *args: pytest.fail("must not open")
    )
    with pytest.raises(CapabilityUnavailable):
        await execute(case)


async def test_wrong_authenticated_channel_and_body_claim_are_denied(read_case):
    case = read_case
    stranger = Principal(id="u2", kind="user", auth_session_id="s2")
    with pytest.raises(DomainError):
        await case["runner"].execute(case["command"], authenticated_principal=stranger)
    case["channel"].value["actor"] = stranger.wire()
    with pytest.raises(DomainError):
        await execute(case)


@pytest.mark.parametrize(
    "location",
    [
        {"kind": "lines", "start": 1, "end": 2},
        {"kind": "whole", "relative_path": "file.txt"},
        {"kind": "text_span"},
    ],
)
async def test_unsupported_location_never_opened(read_case, location):
    case = read_case
    await configure(
        case,
        parameters={
            "workspace_ref": case["workspace"].wire(),
            "path": "file.txt",
            "location": location,
        },
    )
    with pytest.raises(CapabilityUnavailable):
        await execute(case)


async def test_authority_after_open_rechecked_before_read(read_case, monkeypatch):
    from uaw_runner.handle_read import WindowsReadHandle

    case = read_case
    real = WindowsReadHandle.__init__

    def opened(self, *args):
        real(self, *args)
        case["authority"].value["cancelled"] = True

    monkeypatch.setattr(WindowsReadHandle, "__init__", opened)
    monkeypatch.setattr(
        WindowsReadHandle, "read", lambda *args: pytest.fail("no read after cancellation")
    )
    with pytest.raises(DomainError) as error:
        await execute(case)
    assert error.value.failure.category == "cancelled"
    case["target"].write_text("handle was closed", encoding="utf-8")


async def test_actual_threaded_read_keeps_event_loop_responsive(read_case, monkeypatch):
    import threading

    from uaw_runner.handle_read import WindowsReadHandle

    case = read_case
    entered, resume = threading.Event(), threading.Event()
    original = WindowsReadHandle.read

    def blocked(self, parameters):
        entered.set()
        assert resume.wait(3)
        return original(self, parameters)

    monkeypatch.setattr(WindowsReadHandle, "read", blocked)
    task = asyncio.create_task(execute(case))
    assert await asyncio.to_thread(entered.wait, 3)
    tick = False

    async def responsive():
        nonlocal tick
        tick = True
        resume.set()

    await responsive()
    assert tick
    assert (await task).kind == "ok"


async def saved_attempt(case):
    source = await case["reader"].resolve(
        case["command_ref"], authenticated_principal=case["owners"].value
    )
    return source, await asyncio.to_thread(case["executions"].get, source, case["command_ref"])


@pytest.mark.parametrize(
    "data",
    [b"", "中😀\n".encode(), b"\xff", b"abc\0", b"a" * 1048577],
    ids=["empty", "unicode", "invalid_utf8", "binary", "over_1MiB"],
)
async def test_actual_read_success_or_observed_failure_terminal_recovery(
    read_case, monkeypatch, data
):
    case = read_case
    case["target"].write_bytes(data)
    receipt = await execute(case)
    assert receipt.kind == ("ok" if data in (b"", "中😀\n".encode()) else "failed")
    if receipt.kind == "failed":
        assert "payload" not in receipt.wire() and "money" not in receipt.usage["resources"]
    monkeypatch.setattr(
        "uaw_runner.read_executor.WindowsReadHandle",
        lambda *args: pytest.fail("recovery cannot open"),
    )
    case["target"].write_bytes(b"changed after original execution")
    assert (await execute(case)).wire() == receipt.wire()


async def test_span_full_hash_and_real_signature_tamper_range(read_case):
    import base64

    from uaw.shared.runner_signatures import sign

    case = read_case
    data = "中😀é-tail".encode()
    case["target"].write_bytes(data)
    await configure(
        case,
        parameters={
            "workspace_ref": case["workspace"].wire(),
            "path": "file.txt",
            "location": {"kind": "text_span", "start": 1, "end": 4},
        },
    )
    receipt = await execute(case)
    assert receipt.payload["result"]["text"] == "😀é"
    assert receipt.payload["result"]["content_hash"] == hashlib.sha256(data).hexdigest()
    tampered = receipt.wire()
    tampered["payload"]["result"]["text"] = "changed"
    with pytest.raises(DomainError):
        case["protocol"].verify_receipt(canonical(tampered), command=case["command"])
    tampered = receipt.wire()
    tampered["payload"]["result"]["location"] = {"kind": "whole"}
    tampered["signature"] = sign(
        tampered,
        base64.b64decode(case["vault"].values["device-private"].get_secret_value()),
        "d1",
        "device1",
        "receipt",
    )
    with pytest.raises(DomainError, match="resource"):
        case["protocol"].verify_receipt(canonical(tampered), command=case["command"])


@pytest.mark.parametrize(
    "change",
    [
        "cancelled",
        "fencing_token",
        "policy_ref",
        "request_ref",
        "request_parameters",
        "workspace_ref",
        "feature_enabled",
        "connected",
        "lease_expires_at",
        "owner",
        "device_key",
        "control_key",
        "root",
        "channel",
        "clock",
    ],
)
async def test_after_read_current_authority_and_sources_reject(read_case, monkeypatch, change):
    from uaw_runner.handle_read import WindowsReadHandle

    case = read_case
    original = WindowsReadHandle.read

    def read(self, parameters):
        result = original(self, parameters)
        if change in ("cancelled",):
            case["authority"].value[change] = True
        elif change in ("connected", "feature_enabled"):
            case["authority"].value[change] = False
        elif change == "fencing_token":
            case["authority"].value[change] = 2
        elif change in ("policy_ref", "request_ref", "workspace_ref"):
            case["authority"].value[change]["version"] = "2"
        elif change == "request_parameters":
            case["authority"].value[change]["parameters"]["path"] = "other.txt"
        elif change == "lease_expires_at":
            case["authority"].value[change] = NOW.isoformat()
        elif change == "owner":
            case["owners"].revoked = True
        elif change == "device_key":
            case["state"].revoke_key("device1", expected_revision=0)
        elif change == "control_key":
            case["state"].revoke_key("control1", expected_revision=0)
        elif change == "root":
            case["grants"].revoke("native-root1", expected_revision=0)
        elif change == "channel":
            case["channel"].value["actor"]["auth_session_id"] = "changed-session"
        elif change == "clock":
            case["clock"][0] = NOW + timedelta(minutes=4)
        return result

    monkeypatch.setattr(WindowsReadHandle, "read", read)
    with pytest.raises(DomainError):
        await execute(case)
    case["target"].write_bytes(b"handles closed on rejection")
    with case["executions"].transaction() as db:
        row = db.execute("SELECT receipt_data FROM file_read_attempts").fetchone()
        assert row and row[0] is None


@pytest.mark.parametrize("dependency", ["reader", "channel", "authority"])
async def test_await_expiry_rechecked_and_no_open(read_case, monkeypatch, dependency):
    case = read_case

    async def hook(calls):
        await asyncio.sleep(0)
        case["clock"][0] = NOW + timedelta(minutes=4)

    case[dependency].hook = hook
    monkeypatch.setattr(
        "uaw_runner.read_executor.WindowsReadHandle",
        lambda *args: pytest.fail("expired await must not open"),
    )
    with pytest.raises(DomainError):
        await execute(case)


@pytest.mark.parametrize("missing", ["connected", "actor", "key_ref", "owner", "expires_at"])
async def test_channel_strict_schema_missing_fields_denied(read_case, missing):
    del read_case["channel"].value[missing]
    with pytest.raises(ValueError):
        await execute(read_case)


async def test_absent_private_key_refused_before_file_open(read_case, monkeypatch):
    await read_case["vault"].delete("device-private")
    monkeypatch.setattr(
        "uaw_runner.read_executor.WindowsReadHandle",
        lambda *args: pytest.fail("missing private key must not open"),
    )
    with pytest.raises(DomainError, match="missing"):
        await execute(read_case)


async def test_recovery_after_run_cancel_or_command_expiry_no_admission_no_reopen(
    read_case, monkeypatch
):
    case = read_case
    receipt = await execute(case)
    case["authority"].value["cancelled"] = True
    case["clock"][0] = NOW + timedelta(minutes=4, seconds=1)
    case["protocol"].admissions.cancel("u1", "d1", "read-command", expected_revision=0)
    monkeypatch.setattr(
        case["protocol"],
        "admit_async",
        lambda *args, **kwargs: pytest.fail("no admission on recovery"),
    )
    monkeypatch.setattr(
        "uaw_runner.read_executor.WindowsReadHandle", lambda *args: pytest.fail("no recovery open")
    )
    assert (await execute(case)).wire() == receipt.wire()


@pytest.mark.parametrize(
    "change", ["root", "owner", "device_key", "control_key", "reader", "channel", "root_expired"]
)
async def test_recovery_requires_current_data_sources(read_case, change):
    case = read_case
    await execute(case)
    if change == "root":
        case["grants"].revoke("native-root1", expected_revision=0)
    elif change == "owner":
        case["owners"].revoked = True
    elif change == "device_key":
        case["state"].revoke_key("device1", expected_revision=0)
    elif change == "control_key":
        case["state"].revoke_key("control1", expected_revision=0)
    elif change == "reader":
        case["reader"].denied = True
    elif change == "channel":
        case["channel"].value["connected"] = False
    elif change == "root_expired":
        case["clock"][0] = NOW + timedelta(minutes=5)
    with pytest.raises(DomainError):
        await execute(case)


async def test_unknown_interrupted_attempt_never_reexecutes_after_restart(read_case, monkeypatch):
    case = read_case
    source, _ = await saved_attempt(case)
    await asyncio.to_thread(
        case["executions"].claim,
        source,
        case["command_ref"],
        root_handle="native-root1",
        root_revision=0,
        check=lambda: None,
    )
    case["runner"].executions = ReadExecutionJournal(case["executions"].path)
    monkeypatch.setattr(
        "uaw_runner.read_executor.WindowsReadHandle",
        lambda *args: pytest.fail("unknown must not reopen"),
    )
    with pytest.raises(CapabilityUnavailable, match="unknown"):
        await execute(case)


async def test_signed_unpublished_result_recovered_without_second_read(read_case, monkeypatch):
    case = read_case
    original = case["journal"].publish

    async def interrupted(*args, **kwargs):
        raise CapabilityUnavailable("controlled_publication_failure")

    monkeypatch.setattr(case["journal"], "publish", interrupted)
    with pytest.raises(CapabilityUnavailable):
        await execute(case)
    _, attempt = await saved_attempt(case)
    assert attempt.receipt_data and attempt.receipt_ref is None
    monkeypatch.setattr(case["journal"], "publish", original)
    case["runner"].executions = ReadExecutionJournal(case["executions"].path)
    monkeypatch.setattr(
        "uaw_runner.read_executor.WindowsReadHandle",
        lambda *args: pytest.fail("signed recovery must not reopen"),
    )
    receipt = await execute(case)
    assert canonical(receipt.wire()) == attempt.receipt_data


async def test_concurrent_execution_opens_once_and_loser_is_unknown_or_same_receipt(
    read_case, monkeypatch
):
    from uaw_runner.handle_read import WindowsReadHandle

    case = read_case
    opened = 0
    real = WindowsReadHandle.__init__

    def counted(self, *args):
        nonlocal opened
        opened += 1
        real(self, *args)

    monkeypatch.setattr(WindowsReadHandle, "__init__", counted)
    results = await asyncio.gather(*(execute(case) for _ in range(6)), return_exceptions=True)
    receipts = [result for result in results if not isinstance(result, BaseException)]
    assert opened == 1 and receipts
    assert all(result.wire() == receipts[0].wire() for result in receipts)
    assert all(
        isinstance(result, CapabilityUnavailable)
        for result in results
        if isinstance(result, BaseException)
    )
    assert (await execute(case)).wire() == receipts[0].wire()


async def test_cooperative_cancel_in_reader_propagates_without_claim(read_case):
    case = read_case
    entered = asyncio.Event()

    async def hook(calls):
        entered.set()
        await asyncio.Event().wait()

    case["reader"].hook = hook
    task = asyncio.create_task(execute(case))
    await asyncio.wait_for(entered.wait(), 3)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    with case["executions"].transaction() as db:
        assert db.execute("SELECT count(*) FROM file_read_attempts").fetchone()[0] == 0


async def test_cancel_during_os_read_closes_handles_and_preserves_unknown(read_case, monkeypatch):
    import threading

    from uaw_runner.handle_read import WindowsReadHandle

    case = read_case
    entered, release = threading.Event(), threading.Event()
    original = WindowsReadHandle.read

    def blocked(self, parameters):
        entered.set()
        assert release.wait(3)
        return original(self, parameters)

    monkeypatch.setattr(WindowsReadHandle, "read", blocked)
    task = asyncio.create_task(execute(case))
    assert await asyncio.to_thread(entered.wait, 3)
    task.cancel()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    case["target"].write_bytes(b"closed after cancellation")
    _, attempt = await saved_attempt(case)
    assert attempt.receipt_data is None
    with pytest.raises(CapabilityUnavailable, match="unknown"):
        await execute(case)


async def test_true_terminal_commit_retained_when_cancelled_after_publish(read_case, monkeypatch):
    case = read_case
    original = case["journal"].publish

    async def publish(*args, **kwargs):
        ref = await original(*args, **kwargs)
        case["authority"].value["cancelled"] = True
        return ref

    monkeypatch.setattr(case["journal"], "publish", publish)
    with pytest.raises(DomainError) as error:
        await execute(case)
    assert error.value.failure.category == "cancelled"
    _, attempt = await saved_attempt(case)
    assert attempt.receipt_data and attempt.receipt_ref is None
    monkeypatch.setattr(case["journal"], "publish", original)
    recovered = await execute(case)
    assert canonical(recovered.wire()) == attempt.receipt_data


@pytest.mark.parametrize(
    "path",
    ["../outside.txt", "/absolute.txt", "C:relative.txt", "file.txt:stream", "CON", "file.txt."],
)
async def test_unsafe_signed_paths_never_open(read_case, monkeypatch, path):
    case = read_case
    try:
        await configure(case, parameters={"workspace_ref": case["workspace"].wire(), "path": path})
    except ValueError:
        return  # Public schema rejects first; no access occurred.
    monkeypatch.setattr(
        "uaw_runner.read_executor.WindowsReadHandle", lambda *args: pytest.fail("unsafe open")
    )
    with pytest.raises(DomainError):
        await execute(case)


async def child_registry(case):
    from pathlib import Path

    source = await case["reader"].resolve(
        case["command_ref"], authenticated_principal=case["owners"].value
    )
    registry = {
        "command": source.command.wire(),
        "command_ref": case["command_ref"].wire(),
        "actor": case["owners"].value.wire(),
        "owner": source.owner.wire(),
        "grants": str(case["grants"].state.path),
        "keys": str(case["state"].path),
        "admissions": str(case["tmp"] / "admissions.sqlite"),
        "receipts": str(case["journal"].path),
        "reads": str(case["executions"].path),
        "channel": case["channel"].value,
        "now": case["clock"][0].isoformat(),
        "denied": False,
    }
    path = Path(case["tmp"]) / "independent-registration.json"
    path.write_text(canonical(registry), encoding="utf-8")
    return path


async def child_run(path, operation):
    import json
    import subprocess
    import sys
    from pathlib import Path

    result = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, str(Path(__file__).with_name("read_child.py")), str(path), operation],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


async def test_new_process_original_receipt_recovery_no_file_reopen(read_case):
    case = read_case
    receipt = await execute(case)
    path = await child_registry(case)
    case["target"].unlink()  # Recovery must not open or require the old target to still exist.
    result = await child_run(path, "recover")
    assert result["receipt"] == receipt.wire()


async def test_real_cross_process_once_claim_and_unknown_recovery(read_case):
    case = read_case
    path = await child_registry(case)
    results = await asyncio.gather(*(child_run(path, "claim") for _ in range(5)))
    assert sum(result["won"] for result in results) == 1
    assert len({result["token"] for result in results}) == 1
    result = await child_run(path, "recover")
    assert result["failure"] == "capability_unavailable" and "unknown" in result["message"]


async def test_new_process_current_device_revocation_denies_original_receipt(read_case):
    case = read_case
    await execute(case)
    path = await child_registry(case)
    case["state"].revoke_key("device1", expected_revision=0)
    result = await child_run(path, "recover")
    assert result["failure"] == "permission_denied"


async def test_same_command_changed_attempt_or_signed_content_conflicts(read_case):
    case = read_case
    await execute(case)
    source, _ = await saved_attempt(case)
    command = source.command.wire()
    command["trusted_context"]["attempt_id"] = "other-attempt"
    changed = RegisteredReceiptCommand(
        RunnerCommand.model_validate_json(canonical(command)), "d1", source.owner
    )
    with pytest.raises(DomainError, match="changed"):
        await asyncio.to_thread(case["executions"].get, changed, case["command_ref"])


async def test_signed_persisted_receipt_or_ref_tamper_is_not_recovered(read_case):
    case = read_case
    await execute(case)
    with case["executions"].transaction() as db:
        row = db.execute("SELECT receipt_ref FROM file_read_attempts").fetchone()
        import json

        ref = json.loads(row[0])
        ref["content_hash"] = "f" * 64
        db.execute("UPDATE file_read_attempts SET receipt_ref=?", (canonical(ref),))
    with pytest.raises(DomainError, match="digest"):
        await execute(case)


@pytest.mark.parametrize("outside", [False, True])
async def test_actual_junction_rejected_before_file_read(read_case, outside):
    import subprocess

    case = read_case
    destination = case["tmp"] / "other-root" if outside else case["root"] / "nested"
    destination.mkdir()
    target = destination / "data.txt"
    target.write_bytes(b"controlled test file only")
    link = case["root"] / "linked"
    result = await asyncio.to_thread(
        subprocess.run,
        ["cmd.exe", "/c", "mklink", "/J", str(link), str(destination)],
        capture_output=True,
    )
    assert result.returncode == 0
    try:
        await configure(
            case, parameters={"workspace_ref": case["workspace"].wire(), "path": "linked/data.txt"}
        )
        try:
            receipt = await execute(case)
        except DomainError:
            pass  # Outside is refused by RootBindings before opening.
        else:
            assert receipt.kind == "failed" and receipt.failure.code == "file_identity_invalid"
        assert target.read_bytes() == b"controlled test file only"
    finally:
        link.rmdir()  # Only the temporary junction, never recursive target cleanup.


async def test_actual_directory_to_junction_race_after_scope_before_open(read_case, monkeypatch):
    import subprocess

    from uaw_runner.handle_read import WindowsReadHandle

    case = read_case
    nested = case["root"] / "nested"
    nested.mkdir()
    (nested / "data.txt").write_bytes(b"registered temporary target")
    outside = case["tmp"] / "outside-race"
    outside.mkdir()
    (outside / "data.txt").write_bytes(b"never read this temporary file")
    await configure(
        case, parameters={"workspace_ref": case["workspace"].wire(), "path": "nested/data.txt"}
    )
    original = WindowsReadHandle.__init__
    replaced = False

    def opened(self, *args):
        nonlocal replaced
        nested.rename(case["root"] / "old-nested")
        result = subprocess.run(
            ["cmd.exe", "/c", "mklink", "/J", str(nested), str(outside)], capture_output=True
        )
        assert result.returncode == 0
        replaced = True
        original(self, *args)

    monkeypatch.setattr(WindowsReadHandle, "__init__", opened)
    try:
        with pytest.raises(DomainError):
            await execute(case)  # Opened reparse target denied, then current scope rejects too.
        assert (outside / "data.txt").read_bytes() == b"never read this temporary file"
    finally:
        if replaced:
            nested.rmdir()


async def test_real_writer_attempt_during_signing_keeps_original_content(read_case):
    case = read_case
    attempted = False

    def during_credential_resolve():
        nonlocal attempted
        if not attempted and case["target"].exists():
            # check_private is pre-read; only attempt once actual handle is held.
            try:
                with case["target"].open("ab"):
                    pass
            except OSError:
                attempted = True
            else:
                return
            with pytest.raises(OSError):
                case["target"].write_bytes(b"changed")

    case["vault"].on_resolve = during_credential_resolve
    receipt = await execute(case)
    assert attempted and receipt.payload["result"]["text"] == "hello 中😀\n"
    assert case["target"].read_bytes() == "hello 中😀\n".encode()


@pytest.mark.parametrize("change", ["cancelled", "clock", "owner", "device_key", "root", "channel"])
async def test_after_actual_device_signature_current_sources_rechecked(
    read_case, monkeypatch, change
):
    case = read_case
    original = case["runner"].signer.sign_document

    async def signed(*args, **kwargs):
        signature = await original(*args, **kwargs)
        await asyncio.sleep(0)
        if change == "cancelled":
            case["authority"].value["cancelled"] = True
        elif change == "clock":
            case["clock"][0] = NOW + timedelta(minutes=4)
        elif change == "owner":
            case["owners"].revoked = True
        elif change == "device_key":
            case["state"].revoke_key("device1", expected_revision=0)
        elif change == "root":
            case["grants"].revoke("native-root1", expected_revision=0)
        elif change == "channel":
            case["channel"].value["channel_ref"]["version"] = "2"
        return signature

    monkeypatch.setattr(case["runner"].signer, "sign_document", signed)
    with pytest.raises(DomainError):
        await execute(case)
    with case["executions"].transaction() as db:
        assert db.execute("SELECT receipt_data FROM file_read_attempts").fetchone()[0] is None


async def test_registered_input_change_does_not_claim_or_open(read_case, monkeypatch):
    case = read_case
    changed = case["command"].wire()
    changed["parameters"]["parameters"]["path"] = "other.txt"
    command = RunnerCommand.model_validate_json(canonical(changed))
    monkeypatch.setattr(
        "uaw_runner.read_executor.WindowsReadHandle",
        lambda *args: pytest.fail("no changed command open"),
    )
    with pytest.raises(DomainError, match="independently"):
        await case["runner"].execute(command, authenticated_principal=case["owners"].value)
    with case["executions"].transaction() as db:
        assert db.execute("SELECT count(*) FROM file_read_attempts").fetchone()[0] == 0


async def test_invalid_currency_not_inferred_from_command(read_case):
    case = read_case
    with pytest.raises(ValueError):
        ReadOnlyRunner(
            protocol=case["protocol"],
            command_ref=case["command_ref"],
            journal=case["journal"],
            executions=case["executions"],
            currency="unknown",
        )
