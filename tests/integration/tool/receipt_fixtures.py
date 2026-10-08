"""Controlled SQL component Readers. These do not prove actual provider execution."""

from copy import deepcopy
from datetime import UTC, datetime

from uaw.infrastructure.db.transactions import reference
from uaw.shared.contracts import Ref
from uaw.shared.errors import reject
from uaw.tool.ledger import action_key


class ControlledReceiptReader:
    def __init__(self, case):
        self.case = case
        self.allowed = True
        self.reads = 0

    async def read(self, ref, ctx):
        self.reads += 1
        if not self.allowed or ctx.principal.id != self.case.ctx.principal.id:
            raise reject(
                "receipt_source_revoked",
                "Controlled source access was revoked",
                403,
                "authorization",
            )
        row = await self.case.ledger.store.get(ctx.principal, "tool.fixture.receipts", ref.id)
        if str(row.revision) != ref.version or row.payload["receipt_ref"] != ref.wire():
            raise reject("receipt_version_stale", "Controlled receipt version changed", 412)
        return deepcopy(row.payload)


class ControlledEvidenceReader:
    def __init__(self, case):
        self.case = case
        self.allowed = True
        self.checks = 0

    async def check(self, ref, ctx):
        self.checks += 1
        if (
            not self.allowed
            or ref.kind != "input"
            or ref.wire() not in [r.wire() for r in ctx.scope.resource_refs]
        ):
            raise reject(
                "evidence_source_revoked",
                "Controlled evidence is not currently accessible",
                403,
                "authorization",
            )
        row = await self.case.ledger.store.get(ctx.principal, "inputs", ref.id)
        if (
            str(row.revision) != ref.version
            or row.payload["conversation_id"] != ctx.conversation_id
        ):
            raise reject("evidence_version_stale", "Controlled evidence changed", 412)
        return ref


def confirmed_usage(ctx, *, money="0.03"):
    return {
        "attempt_id": ctx.attempt_id,
        "billing_state": "confirmed",
        "resources": {
            "input_tokens": 0,
            "output_tokens": 0,
            "model_calls": 0,
            "tool_calls": 1,
            "child_agents": 0,
            "wall_time_ms": 100,
            "money": money,
            "currency": "USD",
        },
    }


async def receipt(case, *, name="fixture-receipt", outcome="applied", usage=None, version=1):
    ref = Ref(kind="trace", id=name, version=str(version))
    value = {
        "action_ref": reference("tool_call", action_key(case.ctx, case.call["action_id"])),
        "attempt_id": case.ctx.attempt_id,
        "provider_ref": case.spec["provider_ref"],
        "receipt_ref": ref.wire(),
        "outcome": outcome,
        "evidence_refs": [case.reader.source] if outcome != "unknown" else [],
        "usage": usage if usage is not None else confirmed_usage(case.ctx),
        "observed_at": datetime.now(UTC).isoformat(),
    }
    await case.ledger.store.put(
        case.ctx.principal,
        "tool.fixture.receipts",
        name,
        "ToolReconciliationReceipt",
        value,
        expected_revision=version - 1,
        request_id="fixture-receipt-" + name + "-" + str(version),
    )
    return ref
