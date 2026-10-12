"""Real SQL/signatures; paired metadata observes both roles, no cached permission."""

import asyncio
import json

import pytest
from sqlalchemy import event
from uaw_runner.ipc.windows_pipe import OsIdentity

from tests.integration.agent.test_enrolled_peer_current import active_registry
from tests.integration.agent.test_enrollment_postgres import enrollment_case as enrollment_case
from tests.integration.test_browser_sessions import web as web
from tests.integration.test_control_plane import meta
from uaw.infrastructure.enrollment_native import JOURNAL
from uaw.shared.errors import DomainError
from uaw.shared.runner_signatures import VerificationKey


async def identities(m):
    return tuple(
        [await m.observe(m.peers[role]["identity"]["pid"]) for role in ("control", "device")]
    )


async def test_joint_result_equals_two_single_results_with_one_owning_recheck(
    enrollment_case, tmp_path
):
    m = await active_registry(enrollment_case)
    control, device = await identities(m)
    original = m.p.service.recheck_owned
    checks = 0
    reads = 0

    async def recheck(*args):
        nonlocal checks
        checks += 1
        return await original(*args)

    def sql(_connection, _cursor, statement, _parameters, _context, _many):
        nonlocal reads
        if statement.lstrip().upper().startswith("SELECT") and "uaw_records" in statement:
            reads += 1

    m.p.service.recheck_owned = recheck
    engine = m.p.control.database.engine.sync_engine
    event.listen(engine, "before_cursor_execute", sql)
    try:
        singles = (
            await m.registry.current(control, role="control"),
            await m.registry.current(device, role="device"),
        )
        single_counts = {"owning_rechecks": checks, "record_selects": reads}
        checks = reads = 0
        pair = await m.registry.current_pair(control, device)
        pair_counts = {"owning_rechecks": checks, "record_selects": reads}
        assert pair == singles
        assert single_counts["owning_rechecks"] == 2 and checks == 1
        assert pair_counts["record_selects"] < single_counts["record_selects"]
        assert not m.p.control.records.checked_metadata
        assert m.p.control.records._read_witness.get() is None
        (tmp_path / "a20-pair-measurement.json").write_text(
            json.dumps(
                {
                    "same_complete_results": True,
                    "single": single_counts,
                    "pair": pair_counts,
                    "os_native": "controlled",
                    "sql_signatures": "actual",
                    "not_production_ratio": True,
                }
            ),
            encoding="utf-8",
        )
    finally:
        m.p.service.recheck_owned = original
        event.remove(engine, "before_cursor_execute", sql)


@pytest.mark.parametrize(
    "change", ["control_key", "device_key", "candidate", "journal", "owner", "enrollment", "swap"]
)
async def test_each_new_pair_requires_live_original_relationship(enrollment_case, change):
    m = await active_registry(enrollment_case)
    control, device = await identities(m)
    await m.registry.current_pair(control, device)
    if change.endswith("_key"):
        role = change.removesuffix("_key")
        key = m.keys[role]
        m.keys[role] = VerificationKey(key.key_id, key.device_id, key.public_bytes, key.role, True)
    elif change == "candidate":
        m.p.candidates.allowed = False
    elif change == "journal":
        await m.p.control.records.delete(
            m.p.service.controller,
            JOURNAL,
            m.active["id"],
            expected_revision=1,
            request_id="pair-journal-delete",
        )
    elif change == "owner":
        await m.p.control.browser_sessions.logout(m.p.owner, meta("pair-logout"))
    elif change == "enrollment":
        await m.p.service.revoke(m.p.owner, m.active["id"], meta("pair-revoke", 2))
    else:
        control, device = device, control
    with pytest.raises(DomainError):
        await m.registry.current_pair(control, device)


@pytest.mark.parametrize("role", ["control", "device"])
async def test_both_keys_rechecked_after_final_witness_wait(enrollment_case, role):
    m = await active_registry(enrollment_case)
    control, device = await identities(m)

    def revoked(_connection, _cursor, statement, _parameters, _context, _many):
        if statement.lstrip().upper().startswith("SELECT") and " IN " in statement:
            key = m.keys[role]
            m.keys[role] = VerificationKey(
                key.key_id, key.device_id, key.public_bytes, key.role, True
            )

    engine = m.p.control.database.engine.sync_engine
    event.listen(engine, "before_cursor_execute", revoked)
    try:
        with pytest.raises(DomainError) as caught:
            await m.registry.current_pair(control, device)
        assert caught.value.failure.code == "enrolled_current_key_denied"
    finally:
        event.remove(engine, "before_cursor_execute", revoked)


async def test_pair_checks_both_roles_after_owning_journal_wait(enrollment_case):
    m = await active_registry(enrollment_case)
    control, device = await identities(m)
    original = m.p.service.recheck_owned

    async def recheck(*args):
        result = await original(*args)
        key = m.keys["device"]
        m.keys["device"] = VerificationKey(
            key.key_id, key.device_id, key.public_bytes, key.role, True
        )
        return result

    m.p.service.recheck_owned = recheck
    with pytest.raises(DomainError) as caught:
        await m.registry.current_pair(control, device)
    assert caught.value.failure.code == "enrolled_current_key_denied"


async def test_cancelled_pair_discards_read_scope_and_next_call_checks_again(enrollment_case):
    m = await active_registry(enrollment_case)
    control, device = await identities(m)
    original = m.p.service.recheck_owned
    entered = asyncio.Event()

    async def wait(*args):
        entered.set()
        await asyncio.Event().wait()

    m.p.service.recheck_owned = wait
    task = asyncio.create_task(m.registry.current_pair(control, device))
    try:
        await asyncio.wait_for(entered.wait(), 5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        m.p.service.recheck_owned = original
    assert m.p.control.records._current_reads.get() is None
    assert m.p.control.records._read_witness.get() is None
    pair = await m.registry.current_pair(control, device)
    assert (pair[0].role, pair[1].role) == ("control", "device")


@pytest.mark.parametrize("role", ["control", "device"])
async def test_both_os_instances_rechecked_after_owning_wait(enrollment_case, role):
    m = await active_registry(enrollment_case)
    control, device = await identities(m)
    original = m.p.service.recheck_owned
    changed = False

    async def recheck(*args):
        nonlocal changed
        result = await original(*args)
        changed = True
        return result

    async def observe(pid):
        identity = await m.observe(pid)
        if changed and pid == m.peers[role]["identity"]["pid"]:
            return OsIdentity(
                identity.pid, identity.created + 1, identity.user_sid, identity.logon_sid
            )
        return identity

    m.p.service.recheck_owned = recheck
    m.registry.observe = observe
    with pytest.raises(DomainError) as caught:
        await m.registry.current_pair(control, device)
    assert caught.value.failure.code == "enrolled_os_instance_changed"


async def test_owning_journal_deleted_after_full_check_rejected_by_final_witness(enrollment_case):
    m = await active_registry(enrollment_case)
    control, device = await identities(m)
    original = m.p.service.recheck_owned

    async def recheck(*args):
        result = await original(*args)
        await m.p.control.records.delete(
            m.p.service.controller,
            JOURNAL,
            m.active["id"],
            expected_revision=1,
            request_id="pair-delete-after-owning",
        )
        return result

    m.p.service.recheck_owned = recheck
    with pytest.raises(DomainError) as caught:
        await m.registry.current_pair(control, device)
    assert caught.value.failure.code == "current_read_source_changed"
