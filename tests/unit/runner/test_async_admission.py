"""Authority/mapping are explicit component records, not production SQL/IPC sources.

All new async admission scenarios use actual Ed25519, temporary current key directories.
"""

import asyncio
import copy
import json
from dataclasses import asdict
from datetime import timedelta
from threading import Event

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import ValidationError
from uaw_runner.admissions import PersistentAdmissions
from uaw_runner.keys import Ed25519SignatureAdapter
from uaw_runner.protocol import RunnerProtocol
from uaw_runner.state import LocalState

from uaw.shared.contracts import Principal
from uaw.shared.errors import CapabilityUnavailable, DomainError, reject
from uaw.shared.runner_signatures import VerificationKey, sign
from uaw.workspace.contracts import RunnerAuthoritySnapshot, RunnerCommand
from uaw.workspace.repository import MemoryAdmissionRepository

from .conftest import NOW, wire


class ComponentMapping:
    """Independent fixture device/channel ownership records; never reads command."""

    def __init__(self, owner):
        self.users = {"d1": owner}
        self.channels = {"s1": "d1", "runner-session": "d1"}
        self.calls = 0
        self.before = None

    async def owner(self, *, authenticated_principal, device_id):
        self.calls += 1
        if self.before:
            await self.before(self.calls)
        if device_id not in self.users:
            raise CapabilityUnavailable("fixture.registered_device_owner")
        if self.channels.get(authenticated_principal.auth_session_id) != device_id:
            raise reject(
                "permission_denied", "Fixture channel is not registered", 403, "permission"
            )
        return self.users[device_id]


class ComponentAuthority:
    """Published DTO from independently fixed component records, no claimed real service."""

    def __init__(self, snapshot):
        self.record = copy.deepcopy(snapshot)
        self.calls = []
        self.before = None

    async def current(self, command, *, authenticated_principal):
        self.calls.append(authenticated_principal)
        if self.before:
            await self.before(len(self.calls))
        return copy.deepcopy(self.record)


@pytest.fixture
def async_setup(setup, tmp_path):
    _, _, bindings, command, authority, _, _, _ = setup
    directory = LocalState(tmp_path / "keys.sqlite")
    private = Ed25519PrivateKey.generate()
    directory.register_key(
        VerificationKey("control1", "d1", private.public_key().public_bytes_raw(), "control")
    )
    data = command.wire()
    data["signature"] = sign(data, private.private_bytes_raw(), "d1", "control1", "command")
    command = RunnerCommand.model_validate_json(json.dumps(data))
    source = asdict(authority.value)
    source.update(
        context=command.trusted_context.wire(),
        workspace_ref=command.parameters["parameters"]["workspace_ref"],
        request_ref=command.request_ref.wire(),
        policy_ref=command.trusted_context.capability_policy_ref.wire(),
        lease_expires_at=authority.value.lease_expires_at.isoformat(),
        allowed_actions=["file.read"],
    )
    # asdict cannot preserve Ref/Pydantic types; override every contract-owned field above.
    clock = [NOW]
    owner = Principal(id="u1", kind="user", auth_session_id="s1")
    mapping = ComponentMapping(owner)
    current = ComponentAuthority(source)
    admissions = MemoryAdmissionRepository()
    protocol = RunnerProtocol(
        device_id="d1",
        bindings=bindings,
        admissions=admissions,
        signatures=Ed25519SignatureAdapter(directory),
        async_authority=current,
        principal_mapping=mapping,
        clock=lambda: clock[0],
    )
    return protocol, command, owner, current, mapping, clock, directory, private


@pytest.mark.asyncio
async def test_real_signed_async_admission_queries_fresh_records_on_every_retry(async_setup):
    protocol, command, actor, authority, mapping, *_ = async_setup
    first = await protocol.admit_async(wire(command), authenticated_principal=actor)
    assert first.state == "admitted"
    assert len(authority.calls) == 2 and mapping.calls == 2
    assert all(channel == actor for channel in authority.calls)
    assert await protocol.admit_async(wire(command), authenticated_principal=actor) == first
    assert len(authority.calls) == 4  # No cached execution authority.


@pytest.mark.asyncio
async def test_runner_channel_is_independent_and_needs_real_mapping_contract(async_setup):
    protocol, command, _, authority, mapping, *_ = async_setup
    actor = Principal(id="authenticated-device", kind="runner", auth_session_id="runner-session")
    assert (
        await protocol.admit_async(wire(command), authenticated_principal=actor)
    ).state == "admitted"
    assert authority.calls == [actor, actor]
    mapping.users.clear()
    with pytest.raises(CapabilityUnavailable):
        await protocol.admit_async(wire(command), authenticated_principal=actor)


@pytest.mark.parametrize(
    "actor",
    [
        Principal(id="wrong", kind="user", auth_session_id="s1"),
        Principal(id="u1", kind="user", auth_session_id="not-registered"),
        Principal(id="u1", kind="service", auth_session_id="s1"),
    ],
)
@pytest.mark.asyncio
async def test_wrong_authenticated_channel_cannot_use_command_principal(async_setup, actor):
    protocol, command, _, authority, *_ = async_setup
    with pytest.raises(DomainError):
        await protocol.admit_async(wire(command), authenticated_principal=actor)
    assert not authority.calls


@pytest.mark.parametrize("field", ["async_authority", "principal_mapping", "signatures"])
@pytest.mark.asyncio
async def test_missing_async_dependencies_never_fall_back_to_sync(async_setup, field):
    protocol, command, actor, *_ = async_setup
    setattr(protocol, field, None)
    with pytest.raises(CapabilityUnavailable):
        await protocol.admit_async(wire(command), authenticated_principal=actor)


@pytest.mark.parametrize("field", list(RunnerAuthoritySnapshot.model_fields))
@pytest.mark.asyncio
async def test_all_snapshot_fields_required_with_no_default_grant(async_setup, field):
    protocol, command, actor, authority, *_ = async_setup
    del authority.record[field]
    with pytest.raises(ValidationError):
        await protocol.admit_async(wire(command), authenticated_principal=actor)


@pytest.mark.parametrize(
    "changes",
    [
        {"feature_enabled": "true"},
        {"connected": 1},
        {"binding_revision": True},
        {"lease_expires_at": "2026-10-07T09:00:00"},
        {"cancelled": None},
        {"approved": True},
    ],
)
@pytest.mark.asyncio
async def test_snapshot_strict_types_formats_and_extra_fields(async_setup, changes):
    protocol, command, actor, authority, *_ = async_setup
    authority.record.update(changes)
    with pytest.raises(ValidationError):
        await protocol.admit_async(wire(command), authenticated_principal=actor)


@pytest.mark.parametrize(
    "change",
    [
        "context",
        "request",
        "parameters",
        "policy",
        "workspace",
        "root",
        "binding",
        "fence",
        "lease",
        "capability",
        "actions",
        "flag",
        "cancel",
        "connected",
    ],
)
@pytest.mark.asyncio
async def test_changes_during_await_are_not_admitted(async_setup, change):
    protocol, command, actor, authority, *_ = async_setup

    async def mutate(count):
        if count != 2:
            return
        if change == "context":
            authority.record["context"]["model_policy_ref"]["version"] = "2"
        elif change == "request":
            authority.record["request_ref"]["version"] = "2"
        elif change == "parameters":
            authority.record["request_parameters"]["parameters"]["path"] = "."
        elif change == "policy":
            authority.record["policy_ref"]["version"] = "2"
        elif change == "workspace":
            authority.record["workspace_ref"]["version"] = "2"
        elif change == "root":
            authority.record["root_handle"] = "r2"
        elif change == "binding":
            authority.record["binding_revision"] = 1
        elif change == "fence":
            authority.record["fencing_token"] += 1
        elif change == "lease":
            authority.record["lease_expires_at"] = (NOW + timedelta(minutes=5)).isoformat()
        elif change == "capability":
            authority.record["required_scope_capability"] = "other"
        elif change == "actions":
            authority.record["allowed_actions"] = []
        elif change == "flag":
            authority.record["feature_enabled"] = False
        elif change == "cancel":
            authority.record["cancelled"] = True
        else:
            authority.record["connected"] = False

    authority.before = mutate
    with pytest.raises(DomainError):
        await protocol.admit_async(wire(command), authenticated_principal=actor)
    assert not protocol.admissions._records


@pytest.mark.parametrize("phase", ["mapping", "first", "second", "CAS"])
@pytest.mark.asyncio
async def test_await_deadline_and_contended_cas_use_fresh_clock(async_setup, phase):
    protocol, command, actor, authority, mapping, clock, *_ = async_setup

    async def expire(count):
        if phase == "mapping" or count == (1 if phase == "first" else 2):
            clock[0] = NOW + timedelta(hours=1)

    if phase == "mapping":
        mapping.before = expire
    elif phase == "CAS":

        class ExpiringCAS(MemoryAdmissionRepository):
            def reserve_checked(self, *args, **kwargs):
                clock[0] = NOW + timedelta(hours=1)
                return super().reserve_checked(*args, **kwargs)

        protocol.admissions = ExpiringCAS()
    else:
        authority.before = expire
    with pytest.raises(DomainError) as error:
        await protocol.admit_async(wire(command), authenticated_principal=actor)
    assert error.value.failure.code == "deadline_exceeded"
    assert not protocol.admissions._records


@pytest.mark.parametrize("revoke", ["key", "root", "owner"])
@pytest.mark.asyncio
async def test_revocation_or_owner_change_during_second_authority_await(async_setup, revoke):
    protocol, command, actor, authority, mapping, _, keys, _ = async_setup

    async def change(count):
        if count == 2:
            if revoke == "key":
                keys.revoke_key("control1", expected_revision=0)
            elif revoke == "root":
                protocol.bindings.revoke("r1", expected_revision=0)
            else:
                authority.record["context"]["principal"]["id"] = "other"
                authority.record["context"]["scope"]["principal_id"] = "other"
        if revoke == "owner" and count == 1:
            mapping.users["d1"] = Principal(id="other", kind="user", auth_session_id="s1")

    authority.before = change
    with pytest.raises(DomainError):
        await protocol.admit_async(wire(command), authenticated_principal=actor)
    assert not protocol.admissions._records


@pytest.mark.asyncio
async def test_tampered_signature_is_rejected_before_cas(async_setup):
    protocol, command, actor, *_ = async_setup
    data = command.wire()
    data["signature"] = "uaw-ed25519-v1:control1:" + "A" * 86
    with pytest.raises(DomainError):
        await protocol.admit_async(json.dumps(data), authenticated_principal=actor)
    assert not protocol.admissions._records


@pytest.mark.asyncio
async def test_cancellation_during_authority_wait_is_prompt_and_no_cas(async_setup):
    protocol, command, actor, authority, *_ = async_setup
    entered, release = asyncio.Event(), asyncio.Event()

    async def hold(_):
        entered.set()
        await release.wait()

    authority.before = hold
    task = asyncio.create_task(protocol.admit_async(wire(command), authenticated_principal=actor))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, timeout=1)
    assert not protocol.admissions._records


@pytest.mark.asyncio
async def test_blocking_local_check_off_loop_and_cancelled_worker_never_cas(async_setup):
    protocol, command, actor, *_ = async_setup
    entered, release, exited = Event(), Event(), Event()
    actual = protocol.signatures

    class BlockingSignature:
        def verify_command(self, *args, **kwargs):
            entered.set()
            try:
                assert release.wait(timeout=5)
                return actual.verify_command(*args, **kwargs)
            finally:
                exited.set()

        def verify_receipt(self, *args, **kwargs):
            return actual.verify_receipt(*args, **kwargs)

    protocol.signatures = BlockingSignature()
    task = asyncio.create_task(protocol.admit_async(wire(command), authenticated_principal=actor))
    await asyncio.wait_for(asyncio.to_thread(entered.wait, 5), timeout=6)
    # Event loop still handles cancellation while synchronous key IO remains blocked in a worker.
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, timeout=1)
    release.set()
    await asyncio.to_thread(exited.wait, 5)
    assert not protocol.admissions._records


@pytest.mark.asyncio
async def test_cancellation_while_waiting_for_cas_blocks_late_insert(async_setup):
    protocol, command, actor, *_ = async_setup
    entered, release, exited = Event(), Event(), Event()

    class DelayedCAS(MemoryAdmissionRepository):
        def reserve_checked(self, *args, **kwargs):
            entered.set()
            try:
                assert release.wait(timeout=5)
                return super().reserve_checked(*args, **kwargs)
            finally:
                exited.set()

    protocol.admissions = DelayedCAS()
    task = asyncio.create_task(protocol.admit_async(wire(command), authenticated_principal=actor))
    await asyncio.wait_for(asyncio.to_thread(entered.wait, 5), timeout=6)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, timeout=1)
    release.set()
    await asyncio.to_thread(exited.wait, 5)
    assert not protocol.admissions._records


@pytest.mark.asyncio
async def test_persistent_concurrent_restart_and_cancelled_admission_replay(async_setup, tmp_path):
    protocol, command, actor, authority, _, _, _, private = async_setup
    path = tmp_path / "admissions.sqlite"
    protocol.admissions = PersistentAdmissions(path)
    results = await asyncio.gather(
        *(protocol.admit_async(wire(command), authenticated_principal=actor) for _ in range(16))
    )
    assert len(set(results)) == 1
    first = results[0]
    protocol.admissions = PersistentAdmissions(path)
    assert await protocol.admit_async(wire(command), authenticated_principal=actor) == first
    data = command.wire()
    data["trusted_context"].update(attempt_id="a2", trace_id="t2")
    data["signature"] = sign(data, private.private_bytes_raw(), "d1", "control1", "command")
    authority.record["context"] = copy.deepcopy(data["trusted_context"])
    retry = RunnerCommand.model_validate_json(json.dumps(data))
    assert await protocol.admit_async(wire(retry), authenticated_principal=actor) == first
    protocol.admissions.cancel("u1", "d1", "cmd1", expected_revision=0)
    protocol.admissions = PersistentAdmissions(path)
    assert (
        await protocol.admit_async(wire(retry), authenticated_principal=actor)
    ).state == "cancelled"
    data["parameters"]["parameters"]["path"] = "."
    data["signature"] = sign(data, private.private_bytes_raw(), "d1", "control1", "command")
    authority.record["request_parameters"] = copy.deepcopy(data["parameters"])
    with pytest.raises(DomainError) as error:
        await protocol.admit_async(json.dumps(data), authenticated_principal=actor)
    assert error.value.failure.code == "revision_conflict"


@pytest.mark.parametrize(
    "field",
    [
        "operation_id",
        "attempt_id",
        "trace_id",
        "run_id",
        "agent_id",
        "node_id",
        "conversation_id",
        "task_id",
        "deadline",
        "model_policy_ref",
        "budget_reservation_ref",
    ],
)
@pytest.mark.asyncio
async def test_entire_current_context_must_match_signed_declaration(async_setup, field):
    protocol, command, actor, authority, *_ = async_setup
    context = authority.record["context"]
    if field.endswith("_ref"):
        context[field] = {"kind": "policy", "id": "changed", "version": "2"}
    elif field == "deadline":
        context[field] = "2026-10-08T09:00:00Z"
    elif field == "conversation_id":
        context[field] = "changed"
        context["scope"]["conversation_id"] = "changed"
    else:
        context[field] = "changed"
    with pytest.raises((DomainError, ValidationError)):
        await protocol.admit_async(wire(command), authenticated_principal=actor)
    assert not protocol.admissions._records


@pytest.mark.asyncio
async def test_post_cas_expiry_returns_failure_preserving_committed_record(async_setup):
    protocol, command, actor, _, _, clock, *_ = async_setup

    class ExpiresAfterCommit(MemoryAdmissionRepository):
        def reserve_checked(self, *args, **kwargs):
            result = super().reserve_checked(*args, **kwargs)
            clock[0] = NOW + timedelta(hours=1)
            return result

    protocol.admissions = ExpiresAfterCommit()
    with pytest.raises(DomainError) as error:
        await protocol.admit_async(wire(command), authenticated_principal=actor)
    assert error.value.failure.code == "deadline_exceeded"
    assert len(protocol.admissions._records) == 1  # Real earlier CAS, no claim of execution.


@pytest.mark.asyncio
async def test_second_mapping_await_revocation_propagates(async_setup):
    protocol, command, actor, _, mapping, *_ = async_setup

    async def change(count):
        if count == 2:
            mapping.channels.clear()

    mapping.before = change
    with pytest.raises(DomainError):
        await protocol.admit_async(wire(command), authenticated_principal=actor)
    assert not protocol.admissions._records


@pytest.mark.asyncio
async def test_real_sql_lock_wait_does_not_block_loop_and_rechecks_deadline(async_setup, tmp_path):
    import sqlite3

    protocol, command, actor, _, _, clock, *_ = async_setup
    path = tmp_path / "cas.sqlite"
    entered = Event()

    class ContendedAdmissions(PersistentAdmissions):
        def reserve_checked(self, *args, **kwargs):
            entered.set()
            return super().reserve_checked(*args, **kwargs)

    protocol.admissions = ContendedAdmissions(path)
    connection = sqlite3.connect(path, isolation_level=None)
    connection.execute("BEGIN IMMEDIATE")
    task = asyncio.create_task(protocol.admit_async(wire(command), authenticated_principal=actor))
    try:
        assert await asyncio.wait_for(asyncio.to_thread(entered.wait, 5), timeout=6)
        clock[0] = NOW + timedelta(hours=1)
        connection.rollback()
        with pytest.raises(DomainError) as error:
            await asyncio.wait_for(task, timeout=2)
        assert error.value.failure.code == "deadline_exceeded"
        assert connection.execute("SELECT count(*) FROM admissions").fetchone()[0] == 0
    finally:
        connection.rollback()
        connection.close()
        if not task.done():
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task


@pytest.mark.asyncio
async def test_legacy_cas_without_guard_is_unavailable_for_async_only(async_setup):
    protocol, command, actor, *_ = async_setup

    class LegacyRepository:
        def reserve(self, *args):
            raise AssertionError("Async path must not use an unguarded legacy reserve")

    protocol.admissions = LegacyRepository()
    with pytest.raises(CapabilityUnavailable, match="checked_admission_CAS"):
        await protocol.admit_async(wire(command), authenticated_principal=actor)
