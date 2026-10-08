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
            "lease_expires_at": (NOW + timedelta(minutes=5)).isoformat(),
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
        "expires_at": (NOW + timedelta(minutes=4)).isoformat(),
        "parameters": {
            "action": action,
            "parameters": parameters
            or {"workspace_ref": case["workspace"].wire(), "path": "file.txt"},
        },
    }
    signing = ControlCommandSigner(
        (ControlKeyBinding("d1", "control1", "control-private"),),
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
        device_key=DeviceSigningBinding("d1", "device1", "device-private"),
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
