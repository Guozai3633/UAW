"""Internal dispatch timing seam; never an approval or deadline override."""

from typing import TYPE_CHECKING, Protocol

from uaw.shared.contracts import TrustedExecutionContext

if TYPE_CHECKING:
    from uaw.infrastructure.db.transactions import RecordTransaction


class ToolDispatchTimingPort(Protocol):
    async def check(self, tx: RecordTransaction, ctx: TrustedExecutionContext) -> None:
        """Check fresh owning time inside the caller's original claim transaction.

        Return exactly None or raise. No new transaction, external action, mint,
        renewal, or replacement of Tool's access/approval/reservation checks.
        A composition may acquire the original conversation lock after Tool's
        tool-run lock; the reverse lock order is forbidden.
        """
        ...
