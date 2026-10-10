"""Actual OS/vault/pipe; A authenticated enrollment/challenge is a controlled port."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from uaw_runner.bootstrap import BootstrapConsumer, BootstrapNativeChallenges
from uaw_runner.keys import ProtectedSigner
from uaw_runner.read_executor import DeviceSigningBinding

from tests.integration.runner.test_native_authorization import lifecycle_setup
from tests.integration.runner.test_windows_ipc import ipc_case as _ipc_fixture
from uaw.shared.contracts import Principal
from uaw.shared.errors import CapabilityUnavailable, DomainError

ipc_case = _ipc_fixture


class ChallengeFixture:
    """Independent source double, NOT A production bootstrap or human approval."""

    def __init__(self, source):
        self.source, self.change, self.hook = source, None, None

    async def current(self, ticket_id):
        value = await self.source.current(ticket_id)
        if self.hook:
            await self.hook()
        return self.change(value) if self.change else value


async def bootstrap_setup(case):
    native = await lifecycle_setup(case, clock_start=datetime.now(UTC))
    external = ChallengeFixture(native["challenge"])
    bootstrap = BootstrapConsumer(
        registration=native["session"].registration,
        challenges=external,
        mapping=native["mapping"],
        directory=native["state"],
        signer=ProtectedSigner(native["state"], case["store"]),
        device_key=DeviceSigningBinding("d1", "device1", case["handles"][0]),
    )
    checked = BootstrapNativeChallenges(
        bootstrap=bootstrap,
        state=native["state"],
        registry=native["registry"],
        channel_ref=native["session"].channel_ref,
        device_id="d1",
        mapping=native["mapping"],
        clock=lambda: native["clock"][0],
    )
    native.update(bootstrap=bootstrap, external=external, checked=checked)
    return native


async def test_current_bootstrap_intersection_os_keys_full_session(ipc_case):
    native = await bootstrap_setup(ipc_case)
    current = await native["checked"].current(native["ticket_id"])
    assert current.owner.wire() == native["session"].local.owner.wire()
    assert current.identity.created == native["session"].local.identity.created
    assert current.channel_ref == native["session"].channel_ref
    assert current.ticket.document() == native["issued"].ticket.document()


@pytest.mark.parametrize("missing", ["registration", "challenges", "mapping", "credentials"])
async def test_missing_bootstrap_never_mounts(ipc_case, missing):
    native = await bootstrap_setup(ipc_case)
    if missing == "credentials":
        native["bootstrap"].signer.credentials = None
    else:
        setattr(native["bootstrap"], missing, None)
    with pytest.raises(CapabilityUnavailable):
        await native["bootstrap"].local(native["session"].local.identity)


@pytest.mark.parametrize(
    "change",
    [
        lambda c: replace(c, owner=Principal(id="u2", kind="user", auth_session_id="s2")),
        lambda c: replace(c, owner=Principal(id="u1", kind="user", auth_session_id="other")),
        lambda c: replace(c, actor=Principal(id="u1", kind="user", auth_session_id="other")),
        lambda c: replace(c, identity=replace(c.identity, created=c.identity.created + 1)),
        lambda c: replace(c, channel_ref=replace_ref(c.channel_ref)),
        lambda c: replace(c, ticket=replace(c.ticket, nonce="0" * 64)),
        lambda c: replace(c, ticket=replace(c.ticket, challenge="0" * 64)),
        lambda c: replace(c, ticket=replace(c.ticket, revision=c.ticket.revision + 1)),
        lambda c: replace(c, ticket=replace(c.ticket, state="approved")),
        lambda c: replace(c, ticket=replace(c.ticket, device_id="other")),
        lambda c: replace(c, ticket=replace(c.ticket, key_id="other")),
        lambda c: replace(c, expires_at=datetime.now(UTC) - timedelta(seconds=1)),
        lambda c: {"approved": True, "path": "C:/user"},
    ],
    ids=[
        "owner",
        "session",
        "actor",
        "OS-create",
        "channel",
        "nonce",
        "challenge",
        "revision",
        "state",
        "device",
        "key",
        "expiry",
        "body-approval",
    ],
)
async def test_bootstrap_source_mismatch_denied(ipc_case, change):
    native = await bootstrap_setup(ipc_case)
    native["external"].change = change
    with pytest.raises(DomainError):
        await native["checked"].current(native["ticket_id"])
    assert native["state"].get(native["ticket_id"], now=native["clock"][0]).state == "pending"


def replace_ref(ref):
    from uaw.shared.contracts import Ref

    return Ref(
        kind=ref.kind, id="other-channel", version=ref.version, content_hash=ref.content_hash
    )


@pytest.mark.parametrize("change", ["owner", "key", "expiry", "cancel"])
async def test_changes_during_bootstrap_await_fail(ipc_case, change):
    native = await bootstrap_setup(ipc_case)

    async def hook():
        await asyncio.sleep(0)
        if change == "owner":
            native["owners"].value = Principal(id="u1", kind="user", auth_session_id="changed")
        elif change == "key":
            native["state"].revoke_key("device1", expected_revision=0)
        elif change == "expiry":
            native["clock"][0] += timedelta(hours=1)
        else:
            raise asyncio.CancelledError

    native["external"].hook = hook
    with pytest.raises(asyncio.CancelledError if change == "cancel" else DomainError):
        await native["checked"].current(native["ticket_id"])
