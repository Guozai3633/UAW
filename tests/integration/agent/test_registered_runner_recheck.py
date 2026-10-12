"""SQL/Ed25519 current/watch source; channel/root/consent are controlled."""

import asyncio

import pytest

from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.test_runner_control import case as case
from uaw.run.runner_commands import pin
from uaw.run.runner_recheck import RegisteredRunnerRechecks
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.shared.stores import StoreConflict


async def prepared(case):
    await case.dispatch()
    record = await case.register()
    ref = Ref.model_validate(pin("content", record["command"]["command_id"], record["command"]))
    channel = Ref.model_validate(case.device["source"]["channel_ref"])
    return RegisteredRunnerRechecks(case.commands), ref, channel, record


@pytest.mark.parametrize(
    "change", ["none", "ref", "actor", "channel", "key", "consent", "command", "lease"]
)
async def test_recheck_reads_actual_original_source_not_ref_claims(case, change):
    source, ref, channel, record = await prepared(case)
    actor = case.actor
    expected = await case.authority().current(record["command"], authenticated_principal=actor)
    if change == "ref":
        ref = ref.model_copy(update={"content_hash": "0" * 64})
    elif change == "actor":
        actor = actor.model_copy(update={"auth_session_id": "other-peer-session"})
    elif change == "channel":
        channel = channel.model_copy(update={"id": "other-channel"})
    elif change == "key":
        case.signer.revoked = True
    elif change == "consent":
        case.gate.allowed = False
    elif change == "command":
        await case.commands.revoke(
            "command-one", 1, meta("recheck-revoke"), authenticated_service=case.controller
        )
    elif change == "lease":
        await case.leases.release(
            {
                "lease_ref": case.registered["lease_ref"],
                "fencing_token": case.lease["fencing_token"],
            },
            meta("recheck-release"),
            case.ctx,
            holder=case.controller,
        )
    if change == "none":
        assert (
            await source.recheck(ref, authenticated_principal=actor, channel_ref=channel)
        ).wire() == expected
    else:
        with pytest.raises(DomainError):
            await source.recheck(ref, authenticated_principal=actor, channel_ref=channel)
    assert case.commands.store._current_reads.get() is None


async def test_watch_observes_real_cancellation_and_releases_read_scope(case):
    source, ref, channel, _ = await prepared(case)
    calls = 0

    async def changed():
        nonlocal calls
        calls += 1
        if calls == 3:
            await case.domain[1].control(
                case.ctx.principal,
                {
                    "run_id": case.ctx.run_id,
                    "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop"},
                },
                meta("watch-cancel", 2),
            )
        else:
            # The shared controlled signer consumes its hook once. Re-arm
            # explicitly so cancellation occurs in the next watch iteration.
            case.signer.hook = changed

    case.signer.hook = changed
    with pytest.raises(DomainError) as cancelled:
        await source.wait_changed(
            ref,
            authenticated_principal=case.actor,
            channel_ref=channel,
            deadline=asyncio.get_running_loop().time() + 5,
        )
    assert cancelled.value.failure.code == "execution_cancelled"
    assert calls >= 3
    assert case.commands.store._current_reads.get() is None


async def test_watch_original_deadline_cancels_io_and_next_call_has_fresh_scope(case):
    source, ref, channel, _ = await prepared(case)
    with pytest.raises(DomainError) as expired:
        await source.wait_changed(
            ref,
            authenticated_principal=case.actor,
            channel_ref=channel,
            deadline=asyncio.get_running_loop().time() + 0.001,
        )
    assert expired.value.failure.code == "runner_watch_timeout"
    assert case.commands.store._current_reads.get() is None
    await source.recheck(ref, authenticated_principal=case.actor, channel_ref=channel)
    with pytest.raises(DomainError) as denied:
        await source.wait_changed(
            ref,
            authenticated_principal=case.actor,
            channel_ref=channel,
            deadline=asyncio.get_running_loop().time() + 11,
        )
    assert denied.value.failure.code == "runner_watch_deadline_denied"


async def test_composite_current_returns_original_detached_sources(case):
    source, ref, channel, record = await prepared(case)
    state = await source.current(
        ref,
        authenticated_principal=case.actor,
        channel_ref=channel,
        deadline=asyncio.get_running_loop().time() + 5,
    )
    assert state.command_ref == ref
    assert state.source.command.wire() == record["command"]
    assert state.source.owner == state.channel.owner == state.root.owner == case.ctx.principal
    assert state.channel.actor == case.actor and state.channel.channel_ref == channel
    assert state.root.wire() == case.root.value
    assert state.authority.wire() == await case.authority().current(
        record["command"], authenticated_principal=case.actor
    )
    state.source.command.parameters["action"] = "exec"
    state.authority.request_parameters["action"] = "exec"
    current = await source.current(
        ref,
        authenticated_principal=case.actor,
        channel_ref=channel,
        deadline=asyncio.get_running_loop().time() + 5,
    )
    assert current.source.command.parameters["action"] == "file.read"
    assert current.authority.request_parameters["action"] == "file.read"


async def test_current_catches_actual_run_cancel_during_final_command_lookup(case):
    source, ref, channel, _ = await prepared(case)
    original = case.commands.record
    calls = 0

    async def cancel_on_final(identifier):
        nonlocal calls
        calls += 1
        if calls == 2:
            await case.domain[1].control(
                case.ctx.principal,
                {
                    "run_id": case.ctx.run_id,
                    "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop"},
                },
                meta("current-final-cancel", 2),
            )
        return await original(identifier)

    case.commands.record = cancel_on_final
    with pytest.raises(StoreConflict) as denied:
        await source.current(
            ref,
            authenticated_principal=case.actor,
            channel_ref=channel,
            deadline=asyncio.get_running_loop().time() + 5,
        )
    assert calls == 2 and denied.value.failure.code == "current_read_source_changed"
    assert case.commands.store._read_witness.get() is None


async def test_current_keeps_original_deadline_through_final_witness(case):
    source, ref, channel, _ = await prepared(case)
    original = case.commands.store._witness_rows

    async def delayed(*args):
        await asyncio.sleep(5)
        return await original(*args)

    case.commands.store._witness_rows = delayed
    with pytest.raises(DomainError) as denied:
        await source.current(
            ref,
            authenticated_principal=case.actor,
            channel_ref=channel,
            deadline=asyncio.get_running_loop().time() + 0.5,
        )
    assert denied.value.failure.code == "runner_recheck_timeout"
    assert case.commands.store._read_witness.get() is None
    assert case.commands.store._current_reads.get() is None
