"""Controlled UI/source doubles only; approval is NOT a human acceptance receipt."""

import asyncio
import hashlib
from dataclasses import replace
from datetime import timedelta
from threading import Event

import pytest
from uaw_runner.ipc.windows_pipe import WindowsApi
from uaw_runner.keys import ProtectedSigner
from uaw_runner.native_confirmation import NativeChallenge, WindowsNativeConfirmation
from uaw_runner.native_dialog import NativePrompt
from uaw_runner.state import LocalState

from tests.unit.runner.conftest import NOW
from tests.unit.runner.test_real_keys import CredentialFixture
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, DomainError, reject
from uaw.shared.runner_signatures import VerificationKey, signing_bytes


@pytest.fixture
async def native_input(tmp_path):
    state = LocalState(tmp_path / "keys.sqlite")
    protected = ProtectedSigner(state, CredentialFixture())
    pub = await protected.provision_private(credential_handle="fixture-private")
    state.register_key(VerificationKey("device1", "d1", pub, "device"))
    issued = state.issue(
        request_id="r1",
        kind="root",
        principal_id="u1",
        device_id="d1",
        key_id="device1",
        public_bytes=pub,
        expires_at=NOW + timedelta(minutes=5),
        now=NOW,
        root_handle="root1",
        display_name="temporary test root",
    )
    owner = Principal(id="u1", kind="user", auth_session_id="s1")
    value = NativeChallenge(
        issued.ticket,
        owner,
        owner,
        Ref(kind="content", id="ch1", version="1", content_hash="a" * 64),
        WindowsApi().current(),
        NOW + timedelta(minutes=1),
    )

    class FixtureSource:
        async def current(self, ticket_id):
            return self.value

    source = FixtureSource()
    source.value = value
    doc_hash = hashlib.sha256(
        signing_bytes(value.ticket.document(), "d1", "device1", "pairing-proof")
    ).hexdigest()
    adapter = WindowsNativeConfirmation(
        source=source, directory=state, clock=lambda: NOW, timeout_seconds=1
    )
    return dict(
        state=state,
        source=source,
        value=value,
        adapter=adapter,
        args=dict(
            ticket_id=value.ticket.ticket_id,
            principal_id="u1",
            device_id="d1",
            document_hash=doc_hash,
        ),
        root=tmp_path,
    )


def test_prompt_displays_read_scope_and_exact_identifiers():
    text = NativePrompt("user-原文", "device-1", "2026-10-10T10:00:00Z", "hash", True).text()
    assert "user-原文" in text and "device-1" in text and "只读" in text
    assert "不授权写入、安装或执行" in text and "2026-10-10T10:00:00Z" in text


@pytest.mark.parametrize("field", ["ticket_id", "principal_id", "device_id", "document_hash"])
async def test_request_cannot_self_attest_registered_challenge(native_input, monkeypatch, field):
    case = native_input
    monkeypatch.setattr(
        "uaw_runner.native_confirmation.WindowsNativeDialog",
        lambda: pytest.fail("no mismatched UI"),
    )
    case["args"][field] = "other"
    with pytest.raises(DomainError):
        await case["adapter"].confirm(**case["args"])


@pytest.mark.parametrize(
    "change", ["revoked", "expired", "owner", "os_identity", "state", "public_key"]
)
async def test_current_source_rejected_before_user_interaction(native_input, monkeypatch, change):
    case = native_input
    value = case["value"]
    if change == "revoked":
        case["state"].revoke_key("device1", expected_revision=0)
    elif change == "expired":
        value = replace(value, expires_at=NOW)
    elif change == "owner":
        value = replace(value, owner=Principal(id="other", kind="user", auth_session_id="s1"))
    elif change == "os_identity":
        value = replace(value, identity=replace(value.identity, created=value.identity.created + 1))
    elif change == "state":
        value = replace(value, ticket=replace(value.ticket, state="approved"))
    elif change == "public_key":
        value = replace(value, ticket=replace(value.ticket, public_bytes=b"x" * 32))
    case["source"].value = value
    monkeypatch.setattr(
        "uaw_runner.native_confirmation.WindowsNativeDialog", lambda: pytest.fail("no denied UI")
    )
    with pytest.raises(DomainError):
        await case["adapter"].confirm(**case["args"])


async def test_absent_source_never_approves(native_input):
    case = native_input
    case["adapter"].source = None
    with pytest.raises(CapabilityUnavailable):
        await case["adapter"].confirm(**case["args"])


async def test_explicit_fixture_selection_binding_not_human_acceptance(native_input, monkeypatch):
    case = native_input

    class UiDouble:
        def show(self, prompt, stopped, deadline):
            assert prompt.select_root and prompt.account == "u1"
            return case["root"]

    monkeypatch.setattr("uaw_runner.native_confirmation.WindowsNativeDialog", UiDouble)
    result = await case["adapter"].confirm(**case["args"])
    assert (
        result.native_path == case["root"] and result.document_hash == case["args"]["document_hash"]
    )
    assert case["state"].get(case["args"]["ticket_id"], now=NOW).state == "pending"


@pytest.mark.parametrize("change", ["owner_session", "channel", "key", "cancel", "timeout"])
async def test_waiting_ui_current_changes_cancel_worker(native_input, monkeypatch, change):
    case = native_input
    entered, finished = Event(), Event()

    class WaitingUiDouble:
        def show(self, prompt, stopped, deadline):
            entered.set()
            stopped.wait(3)
            finished.set()
            raise reject("native_cancelled", "Fixture UI stopped", 409, "cancelled")

    monkeypatch.setattr("uaw_runner.native_confirmation.WindowsNativeDialog", WaitingUiDouble)
    if change == "timeout":
        case["adapter"].timeout = 0.2
    work = asyncio.create_task(case["adapter"].confirm(**case["args"]))
    assert await asyncio.to_thread(entered.wait, 1)
    if change == "owner_session":
        case["source"].value = replace(
            case["value"], owner=Principal(id="u1", kind="user", auth_session_id="s2")
        )
    elif change == "channel":
        case["source"].value = replace(
            case["value"],
            channel_ref=Ref(kind="content", id="newch", version="1", content_hash="b" * 64),
        )
    elif change == "key":
        case["state"].revoke_key("device1", expected_revision=0)
    elif change == "cancel":
        work.cancel()
    with pytest.raises((DomainError, asyncio.CancelledError)):
        await asyncio.wait_for(work, 2)
    assert finished.is_set() and not case["adapter"].busy
