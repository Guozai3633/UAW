"""SQL command registry -> real Reader -> SQLite signed journal.

Channel/native root/consent and the received signed receipt are controlled;
this does not run a file action, IPC, pairing or the OS credential backend.
"""

import json
import os
from datetime import datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import SecretStr
from uaw_runner.keys import Ed25519SignatureAdapter
from uaw_runner.protocol import RunnerProtocol
from uaw_runner.receipts import ReceiptJournal
from uaw_runner.state import LocalState

from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.test_runner_control import case as case
from uaw.composition import compose
from uaw.context.cache import PureComputationCache
from uaw.run.runner_commands import pin
from uaw.run.runner_receipts import RegisteredReceiptCommandReader
from uaw.shared.contracts import Failure, Ref
from uaw.shared.errors import DomainError
from uaw.shared.runner_signatures import VerificationKey, sign
from uaw.shared.settings import Settings
from uaw.workspace.binding import RootBindings


async def journal_case(case, tmp_path):
    await case.dispatch()
    command = (await case.register())["command"]
    ref = Ref.model_validate(pin("content", command["command_id"], command))
    private = Ed25519PrivateKey.generate()
    keys = LocalState(tmp_path / "public-key-registry.sqlite")
    keys.register_key(
        VerificationKey(
            "fixture-device",
            case.device["device_id"],
            private.public_key().public_bytes_raw(),
            "device",
        )
    )
    protocol = RunnerProtocol(
        device_id=case.device["device_id"],
        bindings=RootBindings(keys),
        admissions=keys,
        signatures=Ed25519SignatureAdapter(keys),
    )
    reader = RegisteredReceiptCommandReader(case.commands)
    journal = ReceiptJournal(tmp_path / "receipts.sqlite", protocol=protocol, reader=reader)
    receipt = {
        "command_id": command["command_id"],
        "attempt_id": case.ctx.attempt_id,
        "kind": "failed",
        "failure": Failure(
            code="controlled_failure",
            category="infrastructure",
            message="Controlled signed terminal; no executor",
            retryable=False,
            failed_phase="execute",
        ).wire(),
        "usage": {
            "attempt_id": case.ctx.attempt_id,
            "billing_state": "pending",
            "resources": {"currency": "USD", "tool_calls": 1, "wall_time_ms": 37},
        },
    }
    receipt["signature"] = sign(
        receipt, private.private_bytes_raw(), case.device["device_id"], "fixture-device", "receipt"
    )
    return journal, reader, ref, receipt, keys


async def test_sql_registry_journal_fixed_content_and_restart(case, tmp_path):
    journal, reader, command_ref, receipt, _ = await journal_case(case, tmp_path)
    source = await reader.resolve(command_ref, authenticated_principal=case.actor)
    assert source.owner == case.ctx.principal and source.device_id == case.device["device_id"]
    first = await journal.publish(
        command_ref, json.dumps(receipt), authenticated_principal=case.actor
    )
    assert first.kind == "content" and first.version == "1"
    assert (
        await journal.publish(
            command_ref, json.dumps(receipt, indent=2), authenticated_principal=case.actor
        )
        == first
    )
    restarted = ReceiptJournal(
        journal.path,
        protocol=journal.protocol,
        reader=RegisteredReceiptCommandReader(case.commands),
    )
    assert (
        await restarted.read(first, authenticated_principal=case.ctx.principal)
    ).wire() == receipt
    assert receipt["usage"]["billing_state"] == "pending"
    assert "money" not in receipt["usage"]["resources"]
    # Journal recovery never adds a budget reserve/dispatch/accounting attempt.
    state = await case.budgets.execution_state(case.ctx.budget_reservation_ref.id, case.ctx)
    assert state["ledger"]["revision"] == 3 and state["reservation"]["revision"] == 1


async def test_cancelled_expired_command_keeps_original_recovery_data(case, tmp_path):
    journal, _, command_ref, receipt, _ = await journal_case(case, tmp_path)
    fixed = await journal.publish(
        command_ref, json.dumps(receipt), authenticated_principal=case.actor
    )
    await case.commands.revoke(
        command_ref.id, 1, meta("command-revoke"), authenticated_service=case.controller
    )
    await case.domain[1].control(
        case.ctx.principal,
        {
            "run_id": case.ctx.run_id,
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "stop"},
        },
        meta("cancel", 2),
    )
    case.gate.allowed = False  # Recovery does not ask for new execution consent.
    after_expiry = datetime.fromisoformat(case.registered["expires_at"]) + timedelta(seconds=1)
    case.devices.clock = lambda: after_expiry
    assert (await journal.read(fixed, authenticated_principal=case.actor)).wire() == receipt
    with pytest.raises(DomainError):
        await case.authority().current(
            (await case.commands.record(command_ref.id))["command"],
            authenticated_principal=case.actor,
        )


@pytest.mark.parametrize("change", ["actor", "device", "control-key", "receipt-key", "pin"])
async def test_actual_registry_and_current_keys_reject_recovery(case, tmp_path, change):
    journal, _, command_ref, receipt, keys = await journal_case(case, tmp_path)
    fixed = await journal.publish(
        command_ref, json.dumps(receipt), authenticated_principal=case.actor
    )
    actor = case.actor
    if change == "actor":
        actor = actor.model_copy(update={"auth_session_id": "foreign"})
    elif change == "device":
        await case.devices.revoke(
            case.device["device_id"],
            1,
            meta("device-revoke"),
            authenticated_service=case.controller,
        )
    elif change == "control-key":
        case.signer.revoked = True
    elif change == "receipt-key":
        keys.revoke_key("fixture-device", expected_revision=0)
    else:
        fixed = fixed.model_copy(update={"content_hash": "0" * 64})
    with pytest.raises(DomainError):
        await journal.read(fixed, authenticated_principal=actor)
    assert journal.path.exists()  # Revocation refuses access, never fabricates missing/not_applied.


async def test_reader_without_registry_refuses_without_journal_io(case, tmp_path):
    journal, _, command_ref, receipt, _ = await journal_case(case, tmp_path)
    fresh = ReceiptJournal(
        tmp_path / "not-created.sqlite",
        protocol=journal.protocol,
        reader=RegisteredReceiptCommandReader(None),
    )
    with pytest.raises(DomainError) as missing:
        await fresh.publish(command_ref, json.dumps(receipt), authenticated_principal=case.actor)
    assert missing.value.failure.code == "capability_unavailable"
    assert not fresh.path.exists()


@pytest.mark.parametrize("enabled", [False, True])
async def test_optional_cache_and_registered_reader_assembly(case, enabled):
    cache = PureComputationCache(max_entries=128, max_bytes=2097152) if enabled else None
    container = compose(
        Settings(
            profile="development",
            development_principal_id="fixture-user",
            database_url=SecretStr(os.environ["UAW_TEST_DATABASE_URL"]),
        ),
        context_cache=cache,
    )
    try:
        assert container.context_components.selection.cache is cache
        assert container.model_service.gateway.inputs.generic.cache is cache
        assert container.runner_receipt_commands.commands is container.runner_commands
        assert container.bindings.context is None and container.bindings.workspace is None
        assert container.bindings.tool is None and container.bindings.agent is None
    finally:
        await container.close()
