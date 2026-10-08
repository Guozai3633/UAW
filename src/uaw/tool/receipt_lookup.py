"""Internal recovery lookup; owning domains supply production implementations."""

from typing import Protocol

from uaw.shared.contracts import Ref, TrustedExecutionContext


class ActionReceiptLookupPort(Protocol):
    """Find an actual fixed receipt from an independently registered original attempt.

    The owner checks current recovery data access, principal/Run/action/attempt and
    provider binding. Lookup is never execution permission or evidence of outcome.
    None means no readable receipt was found; it does not mean not_applied or free.
    Controlled fixtures must never be registered as production sources.
    """

    async def find(self, action_id: str, ctx: TrustedExecutionContext) -> Ref | None: ...
