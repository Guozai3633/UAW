"""Timing/framing unit doubles; no OS identity, real factory or human approval claim."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from uaw_runner.helper_host import HelperBootstrapProgress
from uaw_runner.helper_process import HelperProcess
from uaw_runner.ipc.windows_pipe import OsIdentity

from uaw.shared.errors import DomainError
from uaw.shared.runner_bootstrap import FirstStartPolicy


class ReaderDouble:
    def __init__(self, frames):
        self.frames = list(frames)

    async def readline(self, limit):
        delay, value = self.frames.pop(0)
        await asyncio.sleep(delay)
        return value if isinstance(value, bytes) else (json.dumps(value) + "\n").encode()


class InputDouble:
    def write(self, value):
        assert value == b"start\n"

    def flush(self):
        pass


def case(frames):
    process = HelperProcess.__new__(HelperProcess)
    process.identity = OsIdentity(7, 1, "test-user", "test-logon")
    process.process = SimpleNamespace(stdin=InputDouble())
    process.closed = process.started = False
    process.read_lock = asyncio.Lock()
    process.reader = ReaderDouble(frames)
    process.closing = None

    async def close():
        process.closed = True

    process.close = close
    return process


def policy(seconds=2):
    return FirstStartPolicy(datetime.now(UTC) + timedelta(seconds=seconds), "a" * 64, seconds)


def waiting(p):
    return dict(
        event="bootstrap_waiting",
        stage="enrollment",
        expires_at=p.expires_at.isoformat(),
        challenge_hash=p.challenge_hash,
    )


READY = dict(
    event="ready", name="owned-pipe", identity=OsIdentity(7, 1, "test-user", "test-logon").__dict__
)


async def test_waiting_returns_only_actual_ready_and_same_policy_observer():
    p = policy()
    seen = []

    class Observer:
        async def waiting(self, value):
            seen.append(value)

    process = case([(0, waiting(p)), (0, READY)])
    assert await process.start(first_start=p, on_progress=Observer()) == READY
    assert seen == [p] and not process.closed


@pytest.mark.parametrize(
    "change",
    [
        "repeat",
        "hash",
        "expiry",
        "stage",
        "extra",
        "ordinary",
        "type",
        "utc",
        "duplicate",
        "nan",
        "utf8",
        "oversize",
        "closed",
        "EOF",
        "fake-ready",
    ],
)
async def test_strict_waiting_and_lifecycle_rejection_closes(change):
    p = policy()
    event = waiting(p)
    frames = [(0, event), (0, READY)]
    if change == "repeat":
        frames.insert(1, (0, event))
    elif change in {"hash", "expiry", "stage", "extra", "type", "utc"}:
        if change == "hash":
            event["challenge_hash"] = "b" * 64
        elif change == "expiry":
            event["expires_at"] = (p.expires_at + timedelta(seconds=1)).isoformat()
        elif change == "stage":
            event["stage"] = "approved"
        elif change == "extra":
            event["approved"] = True
        elif change == "type":
            event["expires_at"] = 10
        else:
            event["expires_at"] = p.expires_at.astimezone(
                __import__("datetime").timezone(timedelta(hours=8))
            ).isoformat()
    elif change == "duplicate":
        frames = [(0, b'{"event":"ready","event":"ready"}\n')]
    elif change == "nan":
        frames = [(0, b'{"event":"ready","x":NaN}\n')]
    elif change == "utf8":
        frames = [(0, b"\xff\n")]
    elif change == "oversize":
        # Defence at both event and actual Windows pipe reader.
        frames = [(0, b"x" * 4096 + b"\n")]
    elif change == "closed":
        frames = [(0, {"event": "closed"})]
    elif change == "EOF":
        frames = [(0, b"")]
    elif change == "fake-ready":
        frames = [(0, {**READY, "identity": {"pid": 8}})]
    process = case(frames)
    with pytest.raises(DomainError):
        await process.start(first_start=None if change == "ordinary" else p)
    assert process.closed


async def test_callback_and_frames_share_one_deadline():
    p = policy(0.2)

    class SlowObserver:
        async def waiting(self, value):
            await asyncio.sleep(0.15)

    process = case([(0.1, waiting(p)), (0.01, READY)])
    start = asyncio.get_running_loop().time()
    with pytest.raises(DomainError):
        await process.start(first_start=p, on_progress=SlowObserver())
    assert asyncio.get_running_loop().time() - start < 0.4 and process.closed


async def test_expired_policy_never_writes_start():
    p = FirstStartPolicy(datetime.now(UTC) - timedelta(seconds=1), "a" * 64)
    process = case([])
    with pytest.raises(DomainError):
        await process.start(first_start=p)
    assert process.closed


async def test_cancel_observer_propagates_and_closes():
    begun = asyncio.Event()

    class Observer:
        async def waiting(self, value):
            begun.set()
            await asyncio.Event().wait()

    p = policy()
    process = case([(0, waiting(p))])
    task = asyncio.create_task(process.start(first_start=p, on_progress=Observer()))
    await begun.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert process.closed


async def test_failure_retains_original_public_code():
    process = case([(0, dict(event="failure", code="native_denied"))])
    with pytest.raises(DomainError) as exc:
        await process.start()
    assert exc.value.failure.code == "native_denied" and process.closed


async def test_progress_emits_only_fixed_fields_once(capsys):
    p = policy()
    progress = HelperBootstrapProgress()
    await progress.waiting(p)
    value = json.loads(capsys.readouterr().out)
    assert set(value) == {"event", "stage", "expires_at", "challenge_hash"}
    assert value["event"] == "bootstrap_waiting" and value["challenge_hash"] == p.challenge_hash
    with pytest.raises(DomainError):
        await progress.waiting(p)


async def test_progress_expired_emits_nothing(capsys):
    progress = HelperBootstrapProgress()
    with pytest.raises(DomainError):
        await progress.waiting(FirstStartPolicy(datetime.now(UTC) - timedelta(seconds=1), "a" * 64))
    assert capsys.readouterr().out == ""
