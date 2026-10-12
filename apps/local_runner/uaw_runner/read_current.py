"""Strict internal A composite consumer. Projection is metadata, never a grant."""

import asyncio
import math

from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import reject
from uaw.workspace.contracts import (
    RegisteredReceiptCommand,
    RunnerAuthoritySnapshot,
    RunnerChannelSnapshot,
    RunnerCommand,
    RunnerRootSnapshot,
)
from uaw.workspace.ports import RegisteredReadCurrent
from uaw_runner.receipts import canonical, digest, fixed_ref


def reply_deadline(deadline: float) -> None:
    now = asyncio.get_running_loop().time()
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise reject("dependency_protocol_invalid", "Finite original reply deadline required", 503)
    if deadline <= now:
        raise reject("ipc_timeout", "Original reply deadline expired", 410, "timeout")
    if deadline > now + 10:
        raise reject(
            "dependency_protocol_invalid", "Original reply budget exceeds ten seconds", 503
        )


def checked_current(
    value: RegisteredReadCurrent,
    *,
    command_ref: Ref,
    channel_ref: Ref,
    actor: Principal,
    device_id: str,
    key_id: str,
    command: RunnerCommand,
    source: RegisteredReceiptCommand,
) -> RegisteredReadCurrent:
    if not isinstance(value, RegisteredReadCurrent) or not (
        isinstance(value.source, RegisteredReceiptCommand)
        and isinstance(value.command_ref, Ref)
        and isinstance(value.source.command, RunnerCommand)
        and isinstance(value.source.owner, Principal)
        and isinstance(value.authority, RunnerAuthoritySnapshot)
        and isinstance(value.channel, RunnerChannelSnapshot)
        and isinstance(value.root, RunnerRootSnapshot)
    ):
        raise reject("dependency_protocol_invalid", "Full registered read projection required", 503)
    try:
        ref = fixed_ref(value.command_ref)
        signed = RunnerCommand.model_validate_json(canonical(value.source.command.wire()))
        owner = Principal.model_validate_json(canonical(value.source.owner.wire()))
        authority = RunnerAuthoritySnapshot.model_validate_json(canonical(value.authority.wire()))
        channel = RunnerChannelSnapshot.model_validate_json(canonical(value.channel.wire()))
        root = RunnerRootSnapshot.model_validate_json(canonical(value.root.wire()))
    except ValueError, TypeError, AttributeError:
        raise reject(
            "dependency_protocol_invalid", "Invalid complete read projection", 503
        ) from None
    if (
        ref.wire() != command_ref.wire()
        or ref.content_hash != digest(signed.wire())
        or signed.wire() != command.wire()
        or signed.wire() != source.command.wire()
        or value.source.device_id != device_id
        or source.device_id != device_id
        or owner.kind != "user"
        or owner.wire() != source.owner.wire()
        or owner.wire() != signed.trusted_context.principal.wire()
        or channel.actor.wire() != actor.wire()
        or channel.owner.wire() != owner.wire()
        or channel.device_id != device_id
        or channel.channel_ref.wire() != channel_ref.wire()
        or channel.key_ref.id != key_id
        or root.owner.wire() != owner.wire()
        or root.device_id != device_id
        or authority.device_id != device_id
        or authority.context.wire() != signed.trusted_context.wire()
        or root.workspace_ref.wire() != authority.workspace_ref.wire()
        or root.root_handle != authority.root_handle
        or root.binding_revision != authority.binding_revision
        or root.allowed_actions != authority.allowed_actions
        or not channel.connected
        or actor.kind not in {"user", "runner"}
        or (actor.kind == "user" and actor.wire() != owner.wire())
    ):
        raise reject(
            "binding_mismatch", "Original composite read binding differs", 403, "permission"
        )
    fixed_ref(channel.pairing_ref)
    fixed_ref(channel.key_ref)
    return RegisteredReadCurrent(
        ref, RegisteredReceiptCommand(signed, device_id, owner), authority, channel, root
    )
