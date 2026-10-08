"""Independent controlled SQL receipt registration/lookup, never a product source."""

from copy import deepcopy

from uaw.infrastructure.db.transactions import reference
from uaw.shared.contracts import Ref
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreMissing
from uaw.tool.errors import fail
from uaw.tool.ledger import action_key


async def register_lookup(case, ref):
    # Owning test component registers an actual receipt from the original source.
    # The facade/model only supplies action_id; it never supplies this reference.
    row = await case.ledger.store.get(case.ctx.principal, "tool.fixture.receipts", ref.id)
    assert row.payload["receipt_ref"] == ref.wire() and str(row.revision) == ref.version
    key = action_key(case.ctx, case.call["action_id"])
    try:
        previous = await case.ledger.store.get(case.ctx.principal, "tool.fixture.lookup", key)
        revision = previous.revision
    except StoreMissing:
        revision = 0
    await case.ledger.store.put(
        case.ctx.principal,
        "tool.fixture.lookup",
        key,
        "ToolReconciliationReceipt",
        deepcopy(row.payload),
        expected_revision=revision,
        request_id="fixture-lookup-" + ref.id + "-" + ref.version,
    )


class ControlledActionReceiptLookup:
    """Current source lookup from its own registration, not EffectRecord or budget.

    These named DTO rows are isolated fixture data. A supplies the actual owning
    domain implementation and authenticated provenance/Reader in production.
    """

    def __init__(self, case, *, receipts=None):
        self.case, self.receipts = case, receipts
        self.allowed, self.calls = True, 0

    async def find(self, action_id, ctx):
        self.calls += 1
        if not self.allowed or ctx != self.case.ctx:
            raise reject(
                "lookup_source_revoked", "Controlled recovery source denied", 403, "authorization"
            )
        key = action_key(ctx, action_id)
        try:
            row = await self.case.ledger.store.get(ctx.principal, "tool.fixture.lookup", key)
        except StoreMissing:
            return None
        registered = row.payload
        validate_contract("ToolReconciliationReceipt", registered)
        call = await self.case.ledger.attempt(ctx)
        _, spec, _ = await self.case.ledger.action(action_id, ctx)
        if (
            call["action_id"] != action_id
            or registered["action_ref"] != reference("tool_call", key)
            or registered["attempt_id"] != ctx.attempt_id
            or registered["usage"]["attempt_id"] != ctx.attempt_id
            or registered["provider_ref"] != spec["provider_ref"]
        ):
            raise reject("lookup_binding_conflict", "Registered original source differs", 409)
        if self.receipts is None:
            raise fail(
                "dependency_unavailable",
                "Controlled source Reader is not wired",
                phase="receipt_lookup",
                category="dependency",
                status=503,
            )
        ref = Ref.model_validate(registered["receipt_ref"])
        try:
            actual = await self.receipts.read(ref, ctx)
        except StoreMissing:
            return None
        if actual != registered:
            raise reject("lookup_binding_conflict", "Fixed registered source changed", 409)
        if not self.allowed:
            raise reject(
                "lookup_source_revoked", "Controlled recovery access changed", 403, "authorization"
            )
        return ref


class NoNewExecutionAccess:
    async def snapshot(self, ctx):
        raise AssertionError("Recovery must not call the new-execution access gate")
