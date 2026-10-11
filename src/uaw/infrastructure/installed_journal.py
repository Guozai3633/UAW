"""Original installed read journal recovery, with current independent sources.

Only deployment composition chooses these journals. No public path/body/Ref can
select a different directory, and a journal claim without publication is unknown.
"""

import asyncio

from uaw_runner.read_state import ReadExecutionJournal
from uaw_runner.receipts import ReceiptJournal, canonical

from uaw.infrastructure.runner_pipe import Payload, fixed_ref
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.workspace.ports import ReceiptCommandReaderPort


class InstalledJournalRecovery:
    def __init__(
        self,
        *,
        executions: ReadExecutionJournal,
        journal: ReceiptJournal,
        commands: ReceiptCommandReaderPort,
    ) -> None:
        if journal.reader is not commands or executions.path.parent != journal.path.parent:
            raise ValueError(
                "Original owning command reader and installed journal directory required"
            )
        self.executions, self.journal, self.commands = executions, journal, commands

    async def read(self, command_ref: Ref, *, actor: Principal) -> Payload:
        ref = fixed_ref(command_ref)
        actor = Principal.model_validate_json(canonical(actor.wire()))
        source = await self.commands.resolve(ref, authenticated_principal=actor)
        attempt = await asyncio.to_thread(self.executions.get, source, ref)
        if attempt is None or attempt.receipt_ref is None or attempt.receipt_data is None:
            raise CapabilityUnavailable("runner.installed.original_published_read_outcome")
        receipt = await self.journal.read(attempt.receipt_ref, authenticated_principal=actor)
        if canonical(receipt.wire()) != attempt.receipt_data:
            raise reject("installed_journal_changed", "Published and signed outcomes differ", 412)
        if await self.commands.resolve(ref, authenticated_principal=actor) != source:
            raise reject("installed_journal_source_changed", "Original command source changed", 412)
        if await asyncio.to_thread(self.executions.get, source, ref) != attempt:
            raise reject("installed_journal_changed", "Original read journal changed", 412)
        return {
            "command_ref": ref.wire(),
            "receipt_ref": attempt.receipt_ref.wire(),
            "receipt": receipt.wire(),
        }
