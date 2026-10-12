"""Actual installed peer SQL coverage; native decisions controlled, no file command."""

import asyncio

import pytest

from tests.integration.runner.installed_file_fixture import installed_file_case
from tests.integration.test_browser_sessions import web as web
from uaw.api.browser import SESSIONS
from uaw.infrastructure.enrollment_candidates import CANDIDATES
from uaw.infrastructure.enrollment_native import JOURNAL
from uaw.run.enrollment import ENROLLMENTS
from uaw.shared.errors import DomainError


async def test_installed_both_peer_sources_and_native_account_journal_are_observed(
    web, tmp_path, monkeypatch
):
    async with installed_file_case(web, tmp_path, monkeypatch) as p:
        store = p.container.records
        launch = p.container.installed_lifecycle.active.launch
        peers = launch.connection.peers
        session = launch.connection.session
        assert peers.enrollments.records is store and session.registration is peers
        assert session.local.role == "control" and session.peer.role == "device"
        assert peers.enrollments.authentication == p.container.browser_sessions.principal
        polling = asyncio.Event()
        original = store._witness_rows
        polls = 0
        covered = set()
        reads = 0

        async def witness(*args):
            nonlocal polls
            result = await original(*args)
            polls += 1
            if polls == 3:
                polling.set()
            return result

        async def read():
            nonlocal reads
            reads += 1
            for original_peer in (session.local, session.peer):
                assert (
                    await peers.current(original_peer.identity, role=original_peer.role)
                ) == original_peer
            covered.update(key[1] for key in store._read_witness.get()[1])
            assert {SESSIONS, CANDIDATES, JOURNAL, ENROLLMENTS} <= covered

        async def revoke_native_account_evidence():
            await polling.wait()
            await store.delete(
                peers.enrollments.controller,
                JOURNAL,
                peers.enrollment_id,
                expected_revision=1,
                request_id="a15-revoke-original-native-journal",
            )

        store._witness_rows = witness
        revoked = asyncio.create_task(revoke_native_account_evidence())
        try:
            assert (
                await store.wait_for_read_change(
                    read,
                    deadline=asyncio.get_running_loop().time() + 10,
                    check=lambda: None,
                )
                is None
            )
            await revoked
            assert reads == 1 and polls >= 4
            with pytest.raises(DomainError):
                await peers.current(session.local.identity, role="control")
            assert p.metrics["sends"] == [] and (await p.child_metrics())["opens"] == 0
            p.metrics["a15_peer_sql_watch"] = {
                "owning_reads": reads,
                "fresh_sql_checks": polls,
                "covered_namespaces": sorted(covered),
                "native_journal_change_detected": True,
                "source_is_execution_permission": False,
            }
        finally:
            revoked.cancel()
            await asyncio.gather(revoked, return_exceptions=True)
            store._witness_rows = original
        assert store.database._record_observers.get() is None
    assert p.metrics["cleanup"] == {
        "credential_handles_absent": 4,
        "role_keys_revoked": 2,
        "child_exited": True,
        "proof_pipe_closed": True,
    }
