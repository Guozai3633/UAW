"""D pair consumer strictness: explicit registry/OS doubles, real temp key directory.

This is not actual OS pairing or native consent. Windows coverage is separate.
"""

import asyncio
import hashlib
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from threading import Event
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from uaw_runner.ipc.sessions import AuthenticatedPipeSession, RegisteredPeer
from uaw_runner.ipc.windows_pipe import OsIdentity
from uaw_runner.state import LocalState

from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import DomainError
from uaw.shared.runner_signatures import VerificationKey


@pytest.fixture
async def paired_case(tmp_path):
    directory = LocalState(tmp_path / "keys.sqlite")
    owner = Principal(id="pair-owner", kind="user", auth_session_id="pair-session")
    pairing = Ref(kind="content", id="pair-proof", version="1", content_hash="a" * 64)
    peers = []
    for index, role in enumerate(("control", "device"), 1):
        key = VerificationKey(
            role + "-key",
            "pair-device",
            Ed25519PrivateKey.generate().public_key().public_bytes_raw(),
            role,
        )
        directory.register_key(key)
        peers.append(
            RegisteredPeer(
                OsIdentity(index, index * 10, "fixture-user-SID", "fixture-logon-SID"),
                owner,
                owner,
                "pair-device",
                role,
                key.key_id,
                Ref(
                    kind="content",
                    id=key.key_id,
                    version="1",
                    content_hash=hashlib.sha256(key.public_bytes).hexdigest(),
                ),
                pairing,
                datetime.now(UTC) + timedelta(seconds=30),
            )
        )
    closed = Event()
    live = [True]

    async def close():
        closed.set()

    pipe = SimpleNamespace(timeout=0.1, live_sync=lambda: live[0], close=close, closed=closed)

    class Singles:
        def __init__(self):
            self.single_calls = []

        async def current(self, identity, *, role):
            self.single_calls.append(role)
            return peers[0 if role == "control" else 1]

    class Pairs(Singles):
        def __init__(self):
            super().__init__()
            self.calls, self.hook = [], None

        async def current_pair(self, control, device):
            self.calls.append((control, device))
            return await self.hook() if self.hook else tuple(peers)

    registry = Pairs()
    session = AuthenticatedPipeSession(
        pipe=pipe, registration=registry, directory=directory, signer=None
    )
    session.local, session.peer = peers[1], peers[0]
    session.channel_ref = Ref(
        kind="content", id="original-connection", version="1", content_hash="b" * 64
    )
    session.expires_at = min(p.expires_at for p in peers)
    session.monotonic_expiry = asyncio.get_running_loop().time() + 30
    return SimpleNamespace(
        session=session,
        registry=registry,
        peers=peers,
        directory=directory,
        closed=closed,
        live=live,
        singles=Singles,
    )


async def test_pair_one_call_original_order_and_legacy_two_calls(paired_case):
    c = paired_case
    await c.session.check()
    assert c.registry.calls == [(c.peers[0].identity, c.peers[1].identity)]
    assert c.registry.single_calls == []
    c.session.registration = c.singles()
    await c.session.check()
    assert c.session.registration.single_calls == ["control", "device"]
    assert not c.closed.is_set()


@pytest.mark.parametrize(
    "bad",
    [
        "list",
        "dict",
        "single",
        "short",
        "long",
        "swap",
        "duplicate",
        "peer_dict",
        "identity",
        "owner",
        "actor",
        "device",
        "key",
        "pairing",
        "expiry",
        "naive",
        "float_expiry",
        "missing_owner",
        "method",
    ],
)
async def test_bad_pair_never_falls_back(paired_case, bad):
    c = paired_case
    a, b = c.peers
    values = {
        "list": [a, b],
        "dict": {"control": a, "device": b},
        "single": a,
        "short": (a,),
        "long": (a, b, b),
        "swap": (b, a),
        "duplicate": (a, a),
        "peer_dict": (a.wire(), b),
        "identity": (replace(a, identity=replace(a.identity, created=0)), b),
        "owner": (replace(a, owner=a.owner.model_copy(update={"id": "other"})), b),
        "actor": (replace(a, actor=a.actor.model_copy(update={"auth_session_id": "other"})), b),
        "device": (replace(a, device_id="other"), b),
        "key": (replace(a, key_ref=a.key_ref.model_copy(update={"content_hash": "0" * 64})), b),
        "pairing": (replace(a, pairing_ref=a.pairing_ref.model_copy(update={"id": "other"})), b),
        "expiry": (replace(a, expires_at=datetime.now(UTC) - timedelta(seconds=1)), b),
        "naive": (replace(a, expires_at=datetime.now()), b),
        "float_expiry": (replace(a, expires_at=float("inf")), b),
        "missing_owner": (replace(a, owner=None), b),
    }

    async def result():
        return values[bad]

    c.registry.hook = result
    if bad == "method":
        c.registry.current_pair = None
    with pytest.raises(DomainError):
        await c.session.check()
    assert c.closed.is_set() and c.registry.single_calls == []


@pytest.mark.parametrize(
    "change",
    ["control_key", "device_key", "pipe", "expiry", "metadata", "exception", "timeout", "cancel"],
)
async def test_critical_pair_await_denial_cancel_expiry_never_falls_back(paired_case, change):
    c = paired_case

    async def pending():
        await asyncio.sleep(0)
        if change.endswith("_key"):
            c.directory.revoke_key(change.replace("_", "-"), expected_revision=0)
        elif change == "pipe":
            c.live[0] = False
        elif change == "expiry":
            c.session.monotonic_expiry = asyncio.get_running_loop().time() - 1
        elif change == "metadata":
            c.session.channel_ref = c.session.channel_ref.model_copy(update={"id": "changed"})
        elif change == "exception":
            raise RuntimeError("Explicit source failure")
        elif change == "timeout":
            await asyncio.sleep(0.2)
        elif change == "cancel":
            raise asyncio.CancelledError
        return tuple(c.peers)

    c.registry.hook = pending
    error = (
        asyncio.CancelledError
        if change == "cancel"
        else RuntimeError
        if change == "exception"
        else DomainError
    )
    with pytest.raises(error):
        await c.session.check()
    assert c.closed.is_set() and c.registry.single_calls == []


async def test_waiting_pair_is_cancelled_at_original_earlier_session_expiry(paired_case):
    c = paired_case
    drained = asyncio.Event()

    async def pending():
        try:
            await asyncio.Event().wait()
        finally:
            drained.set()

    c.registry.hook = pending
    started = asyncio.get_running_loop().time()
    c.session.monotonic_expiry = started + 0.02
    with pytest.raises(DomainError) as denied:
        await c.session.check()
    assert denied.value.failure.code == "ipc_timeout"
    assert asyncio.get_running_loop().time() - started < 0.1
    assert drained.is_set() and c.closed.is_set() and c.registry.single_calls == []
