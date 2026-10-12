"""D composite consumer: explicit registered fixtures, real crypto/OS/SQLite.

This fixture does not claim SQL witness, production IPC or human consent.
"""

import asyncio
import json
from dataclasses import replace

import pytest

from tests.integration.runner.test_read_executor import execute
from tests.integration.runner.test_read_executor import native_case as native_case
from tests.integration.runner.test_read_executor import read_case as read_case
from uaw.shared.errors import DomainError
from uaw.workspace.contracts import (
    RunnerAuthoritySnapshot,
    RunnerChannelSnapshot,
    RunnerRootSnapshot,
)
from uaw.workspace.ports import RegisteredReadCurrent


class ComponentComposite:
    def __init__(self, case):
        self.case = case
        case["authority"].value["allowed_actions"] = ["file.read", "file.list"]
        self.deadlines = []
        self.hook = None
        self.calls = 0

    async def current(self, ref, *, authenticated_principal, channel_ref, deadline):
        case = self.case
        assert ref == case["command_ref"] and channel_ref == case["channel"].ref
        assert authenticated_principal == case["owners"].value
        self.calls += 1
        self.deadlines.append(deadline)
        # Fixed independent source fixture predates incoming command.
        source = await case["reader"].resolve(ref, authenticated_principal=authenticated_principal)
        root = await case["source"].current("d1", case["workspace"], source.command.trusted_context)
        value = RegisteredReadCurrent(
            ref,
            source,
            RunnerAuthoritySnapshot.model_validate_json(json.dumps(case["authority"].value)),
            RunnerChannelSnapshot.model_validate_json(json.dumps(case["channel"].value)),
            RunnerRootSnapshot.model_validate_json(json.dumps(root)),
        )
        if self.hook:
            value = await self.hook(value, self.calls)
        return value

    async def wait_changed(self, *args, **kwargs):
        pytest.fail("full composite is not a cheap notification")


def inject(case, monkeypatch):
    source = ComponentComposite(case)
    case["runner"].current_source = source

    async def old_authority(*args, **kwargs):
        pytest.fail("composite checkpoint must not recursively query old authority")

    monkeypatch.setattr(case["authority"], "current", old_authority)
    return source


async def test_composite_actual_signed_read_and_original_cancelled_journal(read_case, monkeypatch):
    case = read_case
    source = inject(case, monkeypatch)
    until = asyncio.get_running_loop().time() + 10
    receipt = await case["runner"].execute(
        case["command"], authenticated_principal=case["owners"].value, response_deadline=until
    )
    assert receipt.kind == "ok"
    case["protocol"].verify_receipt(json.dumps(receipt.wire()), command=case["command"])
    assert source.calls and set(source.deadlines) == {until}
    previous = source.calls
    case["authority"].value["cancelled"] = True
    case["target"].write_bytes(b"changed after actual receipt")
    recovered = await execute(case)  # no active composite or new deadline needed for data recovery
    assert recovered.wire() == receipt.wire()
    assert source.calls == previous


@pytest.mark.parametrize(
    "field",
    [
        "type",
        "command",
        "ref",
        "owner",
        "actor",
        "channel",
        "key",
        "device",
        "root",
        "context",
        "actions",
        "schema",
    ],
)
async def test_composite_strict_cross_binding_rejected_before_open(read_case, monkeypatch, field):
    case = read_case
    source = inject(case, monkeypatch)

    async def changed(value, calls):
        await asyncio.sleep(0)
        if field == "type":
            return value.authority
        if field == "command":
            return replace(
                value,
                source=replace(
                    value.source,
                    command=value.source.command.model_copy(
                        update={"operation_id": "changed-operation"}
                    ),
                ),
            )
        if field == "ref":
            return replace(
                value, command_ref=value.command_ref.model_copy(update={"content_hash": "d" * 64})
            )
        if field == "owner":
            return replace(
                value,
                source=replace(
                    value.source, owner=value.source.owner.model_copy(update={"id": "other-user"})
                ),
            )
        if field == "actor":
            return replace(
                value,
                channel=value.channel.model_copy(
                    update={
                        "actor": value.channel.actor.model_copy(
                            update={"auth_session_id": "other-session"}
                        )
                    }
                ),
            )
        if field == "channel":
            return replace(
                value,
                channel=value.channel.model_copy(
                    update={
                        "channel_ref": value.channel.channel_ref.model_copy(
                            update={"id": "other-channel"}
                        )
                    }
                ),
            )
        if field == "key":
            return replace(
                value,
                channel=value.channel.model_copy(
                    update={"key_ref": value.channel.key_ref.model_copy(update={"id": "other-key"})}
                ),
            )
        if field == "device":
            return replace(
                value, channel=value.channel.model_copy(update={"device_id": "other-device"})
            )
        if field == "root":
            return replace(value, root=value.root.model_copy(update={"root_handle": "other-root"}))
        if field == "context":
            return replace(
                value,
                authority=value.authority.model_copy(
                    update={
                        "context": value.authority.context.model_copy(
                            update={"attempt_id": "other-attempt"}
                        )
                    }
                ),
            )
        if field == "actions":
            return replace(
                value, root=value.root.model_copy(update={"allowed_actions": ("file.read",)})
            )
        if field == "schema":
            return replace(value, authority={"connected": True})
        return value

    source.hook = changed
    monkeypatch.setattr(
        "uaw_runner.read_executor.WindowsReadHandle",
        lambda *a: pytest.fail("invalid source must not open"),
    )
    with pytest.raises(DomainError):
        await case["runner"].execute(
            case["command"],
            authenticated_principal=case["owners"].value,
            response_deadline=asyncio.get_running_loop().time() + 10,
        )


@pytest.mark.parametrize(
    "change",
    [
        "cancel",
        "fence",
        "lease",
        "flags",
        "request",
        "policy",
        "channel",
        "owner",
        "root",
        "control_key",
        "device_key",
    ],
)
async def test_composite_after_external_wait_current_change_no_open(read_case, monkeypatch, change):
    case = read_case
    source = inject(case, monkeypatch)

    async def changed(value, calls):
        if calls == 1:
            await asyncio.sleep(0)
            actual = case["authority"].value
            if change == "cancel":
                actual["cancelled"] = True
            elif change == "fence":
                actual["fencing_token"] += 1
            elif change == "lease":
                actual["lease_expires_at"] = case["clock"][0].isoformat()
            elif change == "flags":
                actual["feature_enabled"] = False
            elif change == "request":
                actual["request_ref"]["version"] = "2"
            elif change == "policy":
                actual["policy_ref"]["version"] = "2"
            elif change == "channel":
                case["channel"].value["connected"] = False
            elif change == "owner":
                case["owners"].revoked = True
            elif change == "root":
                case["grants"].revoke("native-root1", expected_revision=0)
            else:
                case["state"].revoke_key(
                    "control1" if change == "control_key" else "device1", expected_revision=0
                )
        return value

    source.hook = changed
    monkeypatch.setattr(
        "uaw_runner.read_executor.WindowsReadHandle",
        lambda *a: pytest.fail("changed source must not open"),
    )
    with pytest.raises(DomainError):
        await case["runner"].execute(
            case["command"],
            authenticated_principal=case["owners"].value,
            response_deadline=asyncio.get_running_loop().time() + 10,
        )


async def test_composite_reply_expiry_after_source_await_no_open(read_case, monkeypatch):
    case = read_case
    source = inject(case, monkeypatch)
    until = asyncio.get_running_loop().time() + 0.05

    async def delayed(value, calls):
        await asyncio.sleep(0.06)
        return value

    source.hook = delayed
    monkeypatch.setattr(
        "uaw_runner.read_executor.WindowsReadHandle",
        lambda *a: pytest.fail("deadline cannot reopen"),
    )
    with pytest.raises(DomainError):
        await case["runner"].execute(
            case["command"], authenticated_principal=case["owners"].value, response_deadline=until
        )
    assert set(source.deadlines) == {until}
