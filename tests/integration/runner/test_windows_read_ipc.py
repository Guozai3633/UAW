"""Real two-process OS IPC + temp read/journal; authority/confirmation are fixtures."""

import asyncio
import json

import pytest
from uaw_runner.ipc.channel_source import ConnectionRegistry
from uaw_runner.ipc.read_endpoint import ReadOnlyPipeEndpoint
from uaw_runner.read_executor import ReadOnlyRunner
from uaw_runner.read_state import ReadExecutionJournal
from uaw_runner.receipts import canonical

from tests.integration.runner.test_native_root_source import bind, make_native_case
from tests.integration.runner.test_read_executor import configure
from tests.integration.runner.test_windows_ipc import ipc_case as _ipc_fixture
from tests.integration.runner.test_windows_ipc import start_peer
from uaw.shared.errors import CapabilityUnavailable, DomainError

ipc_case = _ipc_fixture


async def read_setup(case):
    native = await make_native_case(
        case["tmp"],
        credentials=case["store"],
        device_handle=case["handles"][0],
        control_handle=case["handles"][1],
        existing_keys=case["keys"],
    )
    await bind(native)
    native["tmp"] = case["tmp"]
    native["target"] = native["root"] / "file.txt"
    native["target"].write_bytes("actual IPC 中😀\n".encode())
    await configure(native)
    case["registry"]["command_ref"] = native["command_ref"].wire()
    return native


class FixtureAssembly:
    """Controlled assembly using independently pre-registered fixed command, not body."""

    def __init__(self, native, registry):
        self.native, self.registry = native, registry

    async def create(self, command_ref, *, channel_ref):
        case = self.native
        assert command_ref.wire() == case["command_ref"].wire()
        return ReadOnlyRunner(
            protocol=case["protocol"],
            command_ref=case["command_ref"],
            journal=case["journal"],
            executions=ReadExecutionJournal(case["tmp"] / "reads.sqlite"),
            currency="CNY",
            roots=case["source"],
            channel=self.registry,
            channel_ref=channel_ref,
            signer=case["runner"].signer,
            device_key=case["runner"].device_key,
        )


async def endpoint_setup(case, native, mode="read"):
    session, process, path = await start_peer(case, mode)
    await session.handshake()
    registry = ConnectionRegistry()
    await registry.add(session)
    endpoint = ReadOnlyPipeEndpoint(
        session=session,
        registry=registry,
        commands=native["reader"],
        runners=FixtureAssembly(native, registry),
    )
    return endpoint, process, registry


async def child_result(process):
    line = await asyncio.wait_for(asyncio.to_thread(process.stdout.readline), 5)
    if not line:
        await asyncio.to_thread(process.wait, timeout=5)
        raise AssertionError(await asyncio.to_thread(process.stderr.read))
    return json.loads(line)


async def test_actual_signed_read_receipt_over_two_process_pipe(ipc_case):
    native = await read_setup(ipc_case)
    endpoint, process, registry = await endpoint_setup(ipc_case, native)
    ref = await endpoint.serve_once()
    body = await child_result(process)
    assert body["receipt"]["kind"] == "ok"
    assert body["receipt"]["payload"]["result"]["text"] == "actual IPC 中😀\n"
    assert ref.wire() == body["receipt_ref"]
    native["protocol"].verify_receipt(canonical(body["receipt"]), command=native["command"])
    assert (
        await native["journal"].read(ref, authenticated_principal=native["owners"].value)
    ).wire() == body["receipt"]
    await registry.close()


async def test_lost_reply_reconnect_explicit_recovery_no_new_admission_or_read(ipc_case):
    native = await read_setup(ipc_case)
    first, process, registry = await endpoint_setup(ipc_case, native, "lost")
    frame = await first.session.receive()
    assert (await child_result(process))["sent"]
    # Drop only transport response after the actual signed journal has committed.
    original_send = first.session.send

    async def lose_reply(kind, body, *, deadline=None):
        await first.session.close()

    first.session.send = lose_reply
    ref = await first.dispatch(frame)
    first.session.send = original_send
    original = await native["journal"].read(ref, authenticated_principal=native["owners"].value)
    old_channel = first.session.channel_ref
    native["target"].unlink()  # any accidental second OS read would fail
    native["authority"].value["cancelled"] = True
    native["authority"].calls = 0
    recovered, child, new_registry = await endpoint_setup(ipc_case, native, "recover")
    assert recovered.session.channel_ref.wire() != old_channel.wire()
    new_ref = await recovered.serve_once()
    body = await child_result(child)
    assert new_ref.wire() == ref.wire() and body["receipt"] == original.wire()
    assert native["authority"].calls == 0
    await new_registry.close()
    await registry.close()


async def test_unknown_explicit_recovery_cannot_start_a_read(ipc_case):
    native = await read_setup(ipc_case)
    endpoint, process, registry = await endpoint_setup(ipc_case, native, "recover")
    with pytest.raises(CapabilityUnavailable):
        await endpoint.serve_once()
    source = await native["reader"].resolve(
        native["command_ref"], authenticated_principal=native["owners"].value
    )
    assert await asyncio.to_thread(native["executions"].get, source, native["command_ref"]) is None
    assert native["authority"].calls == 0
    await registry.close()


async def test_missing_production_assembly_is_unavailable(ipc_case):
    native = await read_setup(ipc_case)
    endpoint, process, registry = await endpoint_setup(ipc_case, native)
    endpoint.runners = None
    with pytest.raises(CapabilityUnavailable):
        await endpoint.serve_once()
    assert native["authority"].calls == 0
    await registry.close()


async def test_body_cannot_self_authorize_or_choose_a_native_path(ipc_case):
    native = await read_setup(ipc_case)
    endpoint, process, registry = await endpoint_setup(ipc_case, native, "body-authority")
    with pytest.raises(DomainError) as exc:
        await endpoint.serve_once()
    assert exc.value.failure.code == "ipc_request_invalid"
    assert native["authority"].calls == 0
    await registry.close()


@pytest.mark.parametrize(
    "change", ["cancel", "disconnect", "authority_revoke", "root_revoke", "expired"]
)
async def test_current_changes_during_runner_authority_await(ipc_case, change):
    native = await read_setup(ipc_case)
    endpoint, process, registry = await endpoint_setup(ipc_case, native)
    entered, released = asyncio.Event(), asyncio.Event()

    async def pending(call):
        entered.set()
        await released.wait()

    native["authority"].hook = pending
    work = asyncio.create_task(endpoint.serve_once())
    await asyncio.wait_for(entered.wait(), 3)
    if change == "cancel":
        work.cancel()
    elif change == "disconnect":
        process.terminate()
        await asyncio.to_thread(process.wait, timeout=5)
    elif change == "authority_revoke":
        native["authority"].value["cancelled"] = True
        released.set()
    elif change == "root_revoke":
        native["grants"].revoke("native-root1", expected_revision=0)
        released.set()
    elif change == "expired":
        from datetime import timedelta

        native["clock"][0] += timedelta(minutes=10)
        released.set()
    with pytest.raises((DomainError, asyncio.CancelledError)):
        await asyncio.wait_for(work, 2)
    assert endpoint.session.pipe.closed.is_set()
    source = native["reader"].command
    # No terminal receipt can be fabricated from cancellation/admission.
    assert native["target"].is_file() and source.command_id == "read-command"
    await registry.close()


async def test_two_live_connections_share_once_read_journal(ipc_case, monkeypatch):
    from threading import Lock

    from uaw_runner.handle_read import WindowsReadHandle

    native = await read_setup(ipc_case)
    count, lock = [0], Lock()
    original = WindowsReadHandle.read

    def measured(handle, parameters):
        with lock:
            count[0] += 1
        return original(handle, parameters)

    monkeypatch.setattr(WindowsReadHandle, "read", measured)
    first, child1, registry1 = await endpoint_setup(ipc_case, native)
    second, child2, registry2 = await endpoint_setup(ipc_case, native)
    outcomes = await asyncio.gather(first.serve_once(), second.serve_once(), return_exceptions=True)
    successes = [result for result in outcomes if not isinstance(result, BaseException)]
    assert len(successes) >= 1 and count[0] == 1
    for result in successes:
        assert result.wire() == successes[0].wire()
    for result, child in zip(outcomes, [child1, child2], strict=True):
        if not isinstance(result, BaseException):
            assert (await child_result(child))["receipt_ref"] == result.wire()
        else:
            assert isinstance(result, DomainError)
    await registry1.close()
    await registry2.close()


async def test_read_assembly_timeout_cancels_authority_and_closes_pipe(ipc_case):
    native = await read_setup(ipc_case)
    endpoint, process, registry = await endpoint_setup(ipc_case, native)
    entered, cancelled = asyncio.Event(), asyncio.Event()

    async def pending(call):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    native["authority"].hook = pending
    endpoint.session.pipe.timeout = 0.3
    with pytest.raises(DomainError) as exc:
        await endpoint.serve_once()
    assert entered.is_set() and cancelled.is_set()
    assert exc.value.failure.code == "ipc_timeout" and endpoint.session.pipe.closed.is_set()
    await registry.close()
