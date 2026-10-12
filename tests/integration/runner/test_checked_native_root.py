"""Real persisted native grants/Ed25519/temp roots; owner and native input are fixtures."""

import asyncio
import json
from datetime import timedelta

import pytest

from tests.integration.runner.test_native_root_source import (
    alter_grant,
    bind,
    current,
)
from tests.integration.runner.test_native_root_source import (
    native_case as native_case,
)
from tests.unit.runner.conftest import NOW
from uaw.shared.errors import DomainError


async def checked(case, callback):
    return await case["source"].checked_current(
        "d1", case["workspace"], case["ctx"], check=callback
    )


async def test_joint_same_complete_root_and_original_legacy(native_case):
    c = native_case
    await bind(c)
    expected = await current(c)
    calls = []
    c["owners"].calls = 0

    async def check(root):
        calls.append(json.loads(json.dumps(root)))
        assert root == expected and c["owners"].calls == 1
        await asyncio.sleep(0)

    result = await checked(c, check)
    assert result == expected and calls == [expected] and c["owners"].calls == 2
    assert result is not calls[0] and result["owner"] is not calls[0]["owner"]
    assert str(c["root"]) not in json.dumps(result)
    assert await current(c) == expected


@pytest.mark.parametrize("when", ["before", "callback", "final_owner"])
@pytest.mark.parametrize("mutation", ["owner", "key", "grant", "signature", "identity", "expiry"])
async def test_fresh_native_owner_key_root_and_expiry(native_case, when, mutation):
    c = native_case
    await bind(c)
    c["owners"].calls = 0
    calls = 0

    def change():
        if mutation == "owner":
            c["owners"].revoked = True
        elif mutation == "key":
            c["state"].revoke_key("device1", expected_revision=0)
        elif mutation == "grant":
            c["grants"].revoke("native-root1", expected_revision=0)
        elif mutation == "signature":
            alter_grant(c, selection_signature="invalid")
        elif mutation == "identity":
            alter_grant(c, file_identity=[0, 0])
        else:
            c["clock"][0] = NOW + timedelta(minutes=5)

    async def hook(n):
        if when == "final_owner" and n == 2:
            change()

    async def check(root):
        nonlocal calls
        calls += 1
        if when == "callback":
            change()

    c["owners"].hook = hook
    if when == "before":
        change()
    with pytest.raises(DomainError):
        await checked(c, check)
    assert calls == (0 if when == "before" else 1)


@pytest.mark.parametrize(
    "mutation", ["nested_owner", "actions", "request", "workspace", "deadline"]
)
async def test_callback_mutation_and_earlier_context_deadline_refused(native_case, mutation):
    c = native_case
    await bind(c)
    calls = 0

    async def check(root):
        nonlocal calls
        calls += 1
        if mutation == "nested_owner":
            root["owner"]["auth_session_id"] = "different"
        elif mutation == "actions":
            root["allowed_actions"].clear()
        elif mutation == "request":
            # Adversarial in-process corruption bypasses frozen DTO assignment.
            c["ctx"].__dict__["operation_id"] = "changed"
        elif mutation == "workspace":
            c["workspace"].__dict__["version"] = "2"
        else:
            c["clock"][0] = NOW + timedelta(hours=1)

    with pytest.raises(DomainError):
        await checked(c, check)
    assert calls == 1


@pytest.mark.parametrize("value", [False, True, {}, "approved", 0])
async def test_callback_non_none_result_has_no_fallback(native_case, value):
    c = native_case
    await bind(c)
    c["owners"].calls = 0

    async def check(root):
        return value

    with pytest.raises(DomainError) as error:
        await checked(c, check)
    assert error.value.failure.code == "dependency_protocol_invalid"
    assert c["owners"].calls == 1


async def test_callback_exception_is_original_no_fallback(native_case):
    c = native_case
    await bind(c)
    marker = RuntimeError("metadata check failed")
    c["owners"].calls = 0

    async def check(root):
        raise marker

    with pytest.raises(RuntimeError) as error:
        await checked(c, check)
    assert error.value is marker and c["owners"].calls == 1


@pytest.mark.parametrize("stop", ["cancel", "timeout"])
async def test_callback_cooperative_cancel_and_outer_earlier_deadline(native_case, stop):
    c = native_case
    await bind(c)
    started, drained = asyncio.Event(), asyncio.Event()
    c["owners"].calls = 0

    async def check(root):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            drained.set()

    async def limited():
        async with asyncio.timeout(0.05):
            await checked(c, check)

    task = asyncio.create_task(limited() if stop == "timeout" else checked(c, check))
    await started.wait()
    if stop == "cancel":
        task.cancel()
    with pytest.raises(asyncio.CancelledError if stop == "cancel" else TimeoutError):
        await task
    assert drained.is_set() and c["owners"].calls == 1


async def test_non_callable_callback_rejected_before_owner(native_case):
    c = native_case
    await bind(c)
    c["owners"].calls = 0
    with pytest.raises(DomainError):
        await checked(c, None)
    assert c["owners"].calls == 0
