"""Actual SQL/SQLite/crypto; original execution/transport are controlled fixtures."""

import asyncio

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from uaw_runner.admissions import PersistentAdmissions
from uaw_runner.protocol import RunnerProtocol
from uaw_runner.read_state import ReadExecutionJournal
from uaw_runner.receipts import ReceiptJournal, canonical
from uaw_runner.root_source import PersistentRootGrants

from tests.integration.agent.test_file_bridge_postgres import bridge_case as bridge_case
from tests.integration.agent.test_file_bridge_postgres import case as case
from tests.integration.agent.test_file_bridge_postgres import domain as domain
from tests.integration.test_control_plane import meta
from uaw.infrastructure.installed_journal import InstalledJournalRecovery
from uaw.shared.errors import DomainError
from uaw.workspace.binding import RootBindings


@pytest.mark.parametrize("mode", ["valid", "missing", "unpublished", "device", "signature", "wait"])
async def test_original_journal_recovery_never_sends_or_opens_again(bridge_case, tmp_path, mode):
    p = bridge_case
    original = await p.bridge.execute(p.call, p.spec, p.ctx)
    p.path.unlink()  # Recovery must use original signed bytes, never reopen the file.
    reader = p.bridge.pipe.commands
    journal = ReceiptJournal(
        tmp_path / "receipts.sqlite",
        protocol=RunnerProtocol(
            device_id=original.source.device_id,
            bindings=RootBindings(PersistentRootGrants(tmp_path / "grants.sqlite")),
            admissions=PersistentAdmissions(tmp_path / "admissions.sqlite"),
            signatures=p.signatures,
        ),
        reader=reader,
    )
    executions = ReadExecutionJournal(tmp_path / "reads.sqlite")
    if mode != "missing":
        record = await p.c.commands.record(original.command_ref.id)
        attempt, acquired = await asyncio.to_thread(
            executions.claim,
            original.source,
            original.command_ref,
            root_handle=record["root"]["root_handle"],
            root_revision=record["root"]["binding_revision"],
            check=lambda: None,
        )
        assert acquired
        data = canonical(original.receipt.wire())
        await asyncio.to_thread(executions.signed, attempt, data, check=lambda: None)
        receipt_ref = await journal.publish(
            original.command_ref, data, authenticated_principal=p.c.actor
        )
        assert receipt_ref == original.receipt_ref
        if mode != "unpublished":
            await asyncio.to_thread(executions.published, attempt, receipt_ref)

    async def revoke_device():
        await p.c.devices.revoke(
            original.source.device_id,
            1,
            meta("journal-revoke-device", 1),
            authenticated_service=p.c.commands.devices.controller,
        )

    if mode == "device":
        await revoke_device()
    elif mode == "signature":
        p.signatures.device = Ed25519PrivateKey.generate()
    elif mode == "wait":
        read = journal.read

        async def changed_after_read(*args, **kwargs):
            result = await read(*args, **kwargs)
            await revoke_device()
            return result

        journal.read = changed_after_read
    p.bridge.pipe.recovery = InstalledJournalRecovery(
        executions=executions, journal=journal, commands=reader
    )
    if mode == "valid":
        assert await p.bridge.recover(p.call, p.spec, p.ctx) == original
        assert await p.bridge.recover(p.call, p.spec, p.ctx) == original
    else:
        with pytest.raises(DomainError):
            await p.bridge.recover(p.call, p.spec, p.ctx)
    assert p.session.sent == ["command"] and p.session.opens == 1
