"""Real Ed25519/SQLite; the independent command registry is a controlled component fixture."""

import asyncio
import json
import sqlite3
from dataclasses import replace
from threading import Event

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from uaw_runner.keys import Ed25519SignatureAdapter
from uaw_runner.receipts import ReceiptJournal, digest
from uaw_runner.state import LocalState

from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, DomainError, reject
from uaw.shared.runner_signatures import VerificationKey, sign
from uaw.workspace.contracts import RegisteredReceiptCommand, RunnerCommand

from .test_protocol import failure_receipt


class RegisteredSourceFixture:
    """Separate fixture registration and channel records; resolve never consumes receipt/body."""

    def __init__(self, command, device_id):
        self.record = RegisteredReceiptCommand(
            command, device_id, command.trusted_context.principal
        )
        self.ref = Ref(
            kind="artifact",
            id="registered-command-1",
            version="1",
            content_hash=digest(command.wire()),
        )
        self.channels = {json.dumps(self.record.owner.wire(), sort_keys=True)}
        self.revoked = False
        self.run_cancelled = False  # Execution cancellation does not revoke recovery data.
        self.calls = 0
        self.hook = None

    async def resolve(self, ref, *, authenticated_principal):
        self.calls += 1
        if self.hook:
            await self.hook(self.calls)
        if (
            self.revoked
            or json.dumps(authenticated_principal.wire(), sort_keys=True) not in self.channels
        ):
            raise reject(
                "permission_denied", "Fixture current data/channel access denied", 403, "permission"
            )
        if ref.wire() != self.ref.wire():
            raise reject("revision_conflict", "Fixture pinned command version differs", 409)
        return self.record


@pytest.fixture
def journal_case(setup, tmp_path):
    protocol = setup[-1]
    private = Ed25519PrivateKey.generate()
    control = Ed25519PrivateKey.generate()
    keys = LocalState(tmp_path / "current-keys.sqlite")
    keys.register_key(
        VerificationKey("device1", "d1", private.public_key().public_bytes_raw(), "device")
    )
    keys.register_key(
        VerificationKey("control1", "d1", control.public_key().public_bytes_raw(), "control")
    )
    command = setup[3].wire()
    command["signature"] = sign(command, control.private_bytes_raw(), "d1", "control1", "command")
    command = RunnerCommand.model_validate_json(json.dumps(command))
    protocol.signatures = Ed25519SignatureAdapter(keys)
    source = RegisteredSourceFixture(command, "d1")
    journal = ReceiptJournal(
        tmp_path / "private" / "receipts.sqlite", protocol=protocol, reader=source
    )
    receipt = failure_receipt(command)
    # Deliberately unknown money/tokens and nonzero observed resources: never infer zero costs.
    receipt["usage"]["resources"] = {"tool_calls": 1, "wall_time_ms": 37, "currency": "CNY"}
    return journal, source, receipt, keys, private, protocol


def signed(case, receipt=None, *, key_id="device1", device_id="d1", domain="receipt"):
    receipt = json.loads(json.dumps(case[2] if receipt is None else receipt))
    receipt["signature"] = sign(receipt, case[4].private_bytes_raw(), device_id, key_id, domain)
    return json.dumps(receipt, ensure_ascii=False, indent=2)


def rows(journal):
    if not journal.path.exists():
        return 0
    with sqlite3.connect(journal.path) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='terminal_receipts'").fetchone():
            return 0
        return db.execute("SELECT count(*) FROM terminal_receipts").fetchone()[0]


async def publish(case, data=None, actor=None):
    journal, source = case[:2]
    return await journal.publish(
        source.ref, data or signed(case), authenticated_principal=actor or source.record.owner
    )


async def read(case, ref, actor=None):
    return await case[0].read(ref, authenticated_principal=actor or case[1].record.owner)


@pytest.mark.parametrize("kind", ["ok", "failed", "cancelled"])
async def test_terminal_raw_usage_restart_and_replay(journal_case, kind):
    case = journal_case
    receipt = json.loads(json.dumps(case[2]))
    receipt["kind"] = kind
    if kind == "ok":
        del receipt["failure"]
        receipt["payload"] = {
            "action": "file.read",
            "result": {
                "workspace_ref": case[1].record.command.parameters["parameters"]["workspace_ref"],
                "path": "source.txt",
                "text": "  原文\n未改写  ",
                "encoding": "utf-8",
                "content_hash": "a" * 64,
                "location": {"kind": "whole"},
            },
        }
    elif kind == "cancelled":
        receipt["failure"]["category"] = "cancelled"
        receipt["failure"]["code"] = "cancelled"
    data = signed(case, receipt)
    ref = await publish(case, data)
    assert ref.kind == "content" and ref.id.startswith("runner_receipt-") and ref.version == "1"
    assert ref.content_hash == digest(json.loads(data))
    assert await publish(case, json.dumps(json.loads(data))) == ref  # JSON layout is not content.
    rebuilt = ReceiptJournal(case[0].path, protocol=case[5], reader=case[1])
    case[1].run_cancelled = True
    case[5].authority.value = replace(
        case[5].authority.value, cancelled=True, feature_enabled=False
    )
    recovered = await rebuilt.read(ref, authenticated_principal=case[1].record.owner)
    assert recovered.wire() == json.loads(data)
    assert recovered.usage == receipt["usage"]
    assert (
        "money" not in recovered.usage["resources"]
        and "input_tokens" not in recovered.usage["resources"]
    )
    assert rows(case[0]) == 1
    with sqlite3.connect(case[0].path) as db:
        assert db.execute("SELECT receipt_data,revision FROM terminal_receipts").fetchone() == (
            data,
            1,
        )
    assert case[4].private_bytes_raw() not in case[0].path.read_bytes()
    assert len(case[5].admissions._records) == 0  # No admission, dispatch, reserve or attempt.


async def test_conflict_does_not_replace_history(journal_case):
    case = journal_case
    first = signed(case)
    ref = await publish(case, first)
    changed = json.loads(first)
    changed["failure"]["message"] = "Different signed terminal content"
    with pytest.raises(DomainError, match="Different terminal"):
        await publish(case, signed(case, changed))
    assert (await read(case, ref)).wire() == json.loads(first)
    assert rows(case[0]) == 1


async def test_waiting_is_explicitly_unsupported(journal_case):
    case = journal_case
    pending = json.loads(signed(case))
    pending.pop("failure")
    pending.update(kind="waiting", wait_ref=case[1].ref.wire())
    with pytest.raises(CapabilityUnavailable, match="progress"):
        await publish(case, signed(case, pending))
    assert rows(case[0]) == 0


@pytest.mark.parametrize("missing", ["reader", "signatures"])
async def test_missing_dependencies_fail_closed(journal_case, missing):
    case = journal_case
    ref = await publish(case)
    if missing == "reader":
        case[0].reader = None
    else:
        case[5].signatures = None
    with pytest.raises(CapabilityUnavailable):
        await publish(case)
    with pytest.raises(CapabilityUnavailable):
        await read(case, ref)
    assert rows(case[0]) == 1


@pytest.mark.parametrize("mutation", ["command", "attempt", "usage", "action", "workspace", "path"])
async def test_true_signature_does_not_authorize_wrong_binding(journal_case, mutation):
    case = journal_case
    data = json.loads(signed(case))
    if mutation == "command":
        data["command_id"] = "wrong"
    elif mutation == "attempt":
        data["attempt_id"] = "wrong"
    elif mutation == "usage":
        data["usage"]["attempt_id"] = "wrong"
    else:
        del data["failure"]
        data["kind"] = "ok"
        data["payload"] = {
            "action": "file.read",
            "result": {
                "workspace_ref": case[1].record.command.parameters["parameters"]["workspace_ref"],
                "path": "source.txt",
                "encoding": "utf-8",
                "text": "fixture",
                "content_hash": "a" * 64,
                "location": {"kind": "whole"},
            },
        }
        if mutation == "action":
            data["payload"] = {
                "action": "file.list",
                "result": {"items": [], "snapshot_revision": 1},
            }
        elif mutation == "workspace":
            data["payload"]["result"]["workspace_ref"]["version"] = "2"
        else:
            data["payload"]["result"]["path"] = "other.txt"
    with pytest.raises(DomainError):
        await publish(case, signed(case, data))
    assert rows(case[0]) == 0


@pytest.mark.parametrize("mutation", ["tamper", "domain", "device", "control_role", "revoked"])
async def test_real_signature_current_key_role_domain_and_device(journal_case, mutation):
    case = journal_case
    data = signed(case)
    if mutation == "tamper":
        changed = json.loads(data)
        changed["failure"]["message"] = "tampered"
        data = json.dumps(changed)
    elif mutation == "domain":
        data = signed(case, domain="pairing-proof")
    elif mutation == "device":
        data = signed(case, device_id="d2")
    elif mutation == "control_role":
        case[3].register_key(
            VerificationKey("wrong-role", "d1", case[4].public_key().public_bytes_raw(), "control")
        )
        data = signed(case, key_id="wrong-role")
    else:
        case[3].revoke_key("device1", expected_revision=0)
    with pytest.raises(DomainError, match="signature"):
        await publish(case, data)
    assert rows(case[0]) == 0


@pytest.mark.parametrize(
    "mutation", ["user", "session", "delegation", "runner", "admin", "service"]
)
async def test_current_channel_cannot_self_assert_owner(journal_case, mutation):
    case = journal_case
    actor = case[1].record.owner.wire()
    if mutation == "user":
        actor["id"] = "intruder"
    elif mutation == "session":
        actor["auth_session_id"] = "other"
    elif mutation == "delegation":
        actor["delegated_by"] = "intruder"
    else:
        actor["kind"] = mutation
    actor = Principal.model_validate_json(json.dumps(actor))
    # Even a faulty source accepting all actor kinds is not a self-asserted user permit.
    if mutation in ("user", "session", "delegation", "admin", "service"):
        case[1].channels.add(json.dumps(actor.wire(), sort_keys=True))
    with pytest.raises(DomainError):
        await publish(case, actor=actor)
    assert rows(case[0]) == 0


async def test_registered_runner_channel_uses_independent_user_owner(journal_case):
    case = journal_case
    actor = Principal(id="channel-runner", kind="runner", auth_session_id="trusted-session")
    case[1].channels.add(json.dumps(actor.wire(), sort_keys=True))
    ref = await publish(case, actor=actor)
    assert (await read(case, ref, actor=actor)).attempt_id == "a1"


@pytest.mark.parametrize("mutation", ["device", "owner", "owner_session", "content"])
async def test_bad_registered_fields_and_same_ref_content_rejected(journal_case, mutation):
    case = journal_case
    source = case[1]
    if mutation == "device":
        source.record = replace(source.record, device_id="d2")
    elif mutation in ("owner", "owner_session"):
        owner = source.record.owner.wire()
        owner["id" if mutation == "owner" else "auth_session_id"] = "changed"
        source.record = replace(
            source.record, owner=Principal.model_validate_json(json.dumps(owner))
        )
    else:
        command = source.record.command.wire()
        command["fencing_token"] += 1
        source.record = replace(
            source.record, command=RunnerCommand.model_validate_json(json.dumps(command))
        )
    with pytest.raises(DomainError):
        await publish(case)
    assert rows(case[0]) == 0


@pytest.mark.parametrize("phase", ["publish", "read", "replay"])
@pytest.mark.parametrize("revocation", ["source", "key", "channel"])
async def test_saved_receipt_is_not_cached_data_permission(journal_case, phase, revocation):
    case = journal_case
    ref = await publish(case)
    if revocation == "source":
        case[1].revoked = True
    elif revocation == "key":
        case[3].revoke_key("device1", expected_revision=0)
    else:
        case[1].channels.clear()
    with pytest.raises(DomainError):
        if phase == "read":
            await read(case, ref)
        else:
            await publish(case)
    assert rows(case[0]) == 1


@pytest.mark.parametrize(
    "field", ["version", "content_hash", "kind", "id", "location", "access_scope"]
)
async def test_exact_receipt_ref_is_required(journal_case, field):
    case = journal_case
    ref = (await publish(case)).wire()
    if field == "location":
        ref[field] = {"kind": "whole"}
    elif field == "access_scope":
        ref[field] = {"principal_id": "u1"}
    elif field == "content_hash":
        ref[field] = "b" * 64
    elif field == "kind":
        ref[field] = "usage"
    else:
        ref[field] = "other"
    with pytest.raises(DomainError):
        await read(case, Ref.model_validate_json(json.dumps(ref)))
    assert rows(case[0]) == 1


@pytest.mark.parametrize("field", ["version", "content_hash", "missing_hash"])
async def test_command_ref_pinning(journal_case, field):
    case = journal_case
    ref = case[1].ref.wire()
    if field == "missing_hash":
        ref.pop("content_hash")
    elif field == "content_hash":
        ref[field] = "a" * 64
    else:
        ref[field] = "latest"
    with pytest.raises(DomainError):
        await case[0].publish(
            Ref.model_validate_json(json.dumps(ref)),
            signed(case),
            authenticated_principal=case[1].record.owner,
        )
    assert rows(case[0]) == 0


@pytest.mark.parametrize("operation", ["publish", "read"])
@pytest.mark.parametrize("change", ["source", "key", "owner", "command"])
async def test_current_source_rechecked_after_external_work(journal_case, operation, change):
    case = journal_case
    ref = await publish(case) if operation == "read" else None
    case[1].calls = 0

    async def hook(n):
        if n != 2:
            return
        if change == "source":
            case[1].revoked = True
        elif change == "key":
            case[3].revoke_key("device1", expected_revision=0)
        elif change == "owner":
            case[1].record = replace(
                case[1].record, owner=Principal(id="other", kind="user", auth_session_id="s1")
            )
        else:
            command = case[1].record.command.wire()
            command["fencing_token"] += 1
            case[1].record = replace(
                case[1].record, command=RunnerCommand.model_validate_json(json.dumps(command))
            )

    case[1].hook = hook
    with pytest.raises(DomainError):
        if operation == "read":
            await read(case, ref)
        else:
            await publish(case)
    assert rows(case[0]) == (1 if operation == "read" else 0)


async def test_concurrent_instances_dedup_and_return_isolation(journal_case):
    case = journal_case
    journals = [ReceiptJournal(case[0].path, protocol=case[5], reader=case[1]) for _ in range(16)]
    refs = await asyncio.gather(
        *(
            j.publish(case[1].ref, signed(case), authenticated_principal=case[1].record.owner)
            for j in journals
        )
    )
    assert all(ref == refs[0] for ref in refs) and rows(case[0]) == 1
    receipt = await read(case, refs[0])
    receipt.usage["resources"]["tool_calls"] = 999
    assert (await read(case, refs[0])).usage["resources"]["tool_calls"] == 1


async def test_reader_cancellation_propagates_without_insert(journal_case):
    case = journal_case
    started = asyncio.Event()

    async def hook(n):
        started.set()
        await asyncio.Event().wait()

    case[1].hook = hook
    task = asyncio.create_task(publish(case))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert rows(case[0]) == 0


async def test_blocked_sqlite_is_off_loop_and_cancel_rolls_back(journal_case):
    case = journal_case
    # Initialize lazily without adding a receipt.
    with case[0]._transaction():
        pass
    lock = sqlite3.connect(case[0].path, isolation_level=None)
    lock.execute("BEGIN IMMEDIATE")
    reached = Event()
    original = case[0]._save
    done = Event()

    def blocked(*args):
        reached.set()
        try:
            return original(*args)
        finally:
            done.set()

    case[0]._save = blocked
    task = asyncio.create_task(publish(case))
    await asyncio.to_thread(reached.wait, 2)
    assert reached.is_set()
    await asyncio.sleep(0)  # Loop remains available while worker waits on actual SQLite lock.
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    lock.rollback()
    lock.close()
    assert await asyncio.to_thread(done.wait, 2)
    assert rows(case[0]) == 0


@pytest.mark.parametrize("when", ["before_commit", "after_commit"])
async def test_interrupted_publish_preserves_truthful_atomic_state(journal_case, when):
    case = journal_case
    original = case[0]._save
    if when == "before_commit":

        def interrupted(saved, source, check):
            calls = 0

            def fail_after_insert():
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise RuntimeError("fixture interrupted transaction")

            return original(saved, source, fail_after_insert)

        case[0]._save = interrupted
    else:

        async def hook(n):
            if n == 3:
                case[1].revoked = True

        case[1].hook = hook
    with pytest.raises((RuntimeError, DomainError)):
        await publish(case)
    assert rows(case[0]) == (1 if when == "after_commit" else 0)
    case[0]._save = original
    case[1].hook = None
    case[1].revoked = False
    ref = await publish(case)
    assert (await read(case, ref)).kind == "failed" and rows(case[0]) == 1


async def test_corrupt_stored_receipt_is_not_returned_or_replaced(journal_case):
    case = journal_case
    ref = await publish(case)
    with sqlite3.connect(case[0].path) as db:
        raw = json.loads(db.execute("SELECT receipt_data FROM terminal_receipts").fetchone()[0])
        raw["failure"]["message"] = "corrupt at same Ref"
        db.execute("UPDATE terminal_receipts SET receipt_data=?", (json.dumps(raw),))
    with pytest.raises(DomainError):
        await read(case, ref)
    with pytest.raises(DomainError):
        await publish(case)
    assert rows(case[0]) == 1


async def test_sqlite_unavailable_is_explicit(journal_case, tmp_path):
    case = journal_case
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("fixture")
    case[0].path = blocked / "journal.sqlite"
    with pytest.raises(CapabilityUnavailable, match="receipt_journal"):
        await publish(case)


@pytest.mark.parametrize("data", ['{"command_id":"one","command_id":"two"}', '{"usage":NaN}', "{}"])
async def test_strict_received_json_no_record(journal_case, data):
    with pytest.raises(DomainError):
        await publish(journal_case, data)
    assert rows(journal_case[0]) == 0


@pytest.mark.parametrize("identity", ["owner", "attempt", "device"])
async def test_independent_identity_isolation_on_same_sqlite(journal_case, identity):
    case = journal_case
    first_ref = await publish(case)
    data = case[1].record.command.wire()
    if identity == "owner":
        data["trusted_context"]["principal"]["id"] = "owner2"
        data["trusted_context"]["scope"]["principal_id"] = "owner2"
    elif identity == "attempt":
        data["trusted_context"]["attempt_id"] = "attempt2"
    # Independent trusted fixture registration; command signature is irrelevant to recovery,
    # but preserve a actual signed command for this component's source evidence.
    control = Ed25519PrivateKey.generate()
    device_id = "d2" if identity == "device" else "d1"
    case[3].register_key(
        VerificationKey("control2", device_id, control.public_key().public_bytes_raw(), "control")
    )
    data["signature"] = sign(data, control.private_bytes_raw(), device_id, "control2", "command")
    command = RunnerCommand.model_validate_json(json.dumps(data))
    other_source = RegisteredSourceFixture(command, device_id)
    other_source.ref = Ref(
        kind="artifact", id="registered-command-2", version="1", content_hash=digest(data)
    )
    from uaw_runner.protocol import RunnerProtocol

    other_protocol = RunnerProtocol(
        device_id=device_id,
        bindings=case[5].bindings,
        admissions=case[5].admissions,
        signatures=case[5].signatures,
    )
    other_journal = ReceiptJournal(case[0].path, protocol=other_protocol, reader=other_source)
    receipt = json.loads(signed(case))
    if identity == "attempt":
        receipt["attempt_id"] = "attempt2"
        receipt["usage"]["attempt_id"] = "attempt2"
    key_id = "device2" if identity == "device" else "device1"
    if identity == "device":
        case[3].register_key(
            VerificationKey(key_id, device_id, case[4].public_key().public_bytes_raw(), "device")
        )
    raw = signed(case, receipt, device_id=device_id, key_id=key_id)
    second_ref = await other_journal.publish(
        other_source.ref, raw, authenticated_principal=other_source.record.owner
    )
    assert second_ref.id != first_ref.id and rows(case[0]) == 2
    assert (await read(case, first_ref)).attempt_id == "a1"
    assert (
        await other_journal.read(second_ref, authenticated_principal=other_source.record.owner)
    ).wire() == json.loads(raw)
    with pytest.raises(DomainError):
        await other_journal.read(first_ref, authenticated_principal=other_source.record.owner)


async def test_invalid_reader_type_is_not_accepted(journal_case):
    case = journal_case

    class BrokenSource:
        async def resolve(self, ref, *, authenticated_principal):
            return {"command": case[1].record.command.wire(), "approved": True}

    case[0].reader = BrokenSource()
    with pytest.raises(DomainError) as error:
        await publish(case)
    assert error.value.failure.code == "dependency_protocol_invalid"
    assert rows(case[0]) == 0


async def test_source_and_key_revoked_during_final_commit_are_rechecked(journal_case):
    case = journal_case
    original = case[0]._save

    def revoke_after_commit(*args):
        result = original(*args)
        case[3].revoke_key("device1", expected_revision=0)
        return result

    case[0]._save = revoke_after_commit
    with pytest.raises(DomainError, match="signature"):
        await publish(case)
    assert rows(case[0]) == 1  # Truthful commit retained; no cached access or replacement.


async def test_saved_same_ref_changes_even_with_valid_signature_are_rejected(journal_case):
    case = journal_case
    ref = await publish(case)
    changed = json.loads(signed(case))
    changed["failure"]["message"] = "Different signed content at the same saved Ref"
    changed = signed(case, changed)
    with sqlite3.connect(case[0].path) as db:
        db.execute("UPDATE terminal_receipts SET receipt_data=?", (changed,))
    with pytest.raises(DomainError, match="content/binding"):
        await read(case, ref)
    assert rows(case[0]) == 1


async def test_missing_reader_default_does_not_touch_storage(journal_case):
    case = journal_case
    default = ReceiptJournal(case[0].path, protocol=case[5])
    with pytest.raises(CapabilityUnavailable):
        await default.publish(
            case[1].ref, signed(case), authenticated_principal=case[1].record.owner
        )
    with pytest.raises(CapabilityUnavailable):
        await default.read(case[1].ref, authenticated_principal=case[1].record.owner)
    assert not case[0].path.exists()


async def test_invalid_utf8_bytes_never_creates_journal(journal_case):
    with pytest.raises(DomainError) as error:
        await publish(journal_case, b"\xff")
    assert error.value.failure.code == "schema_invalid"
    assert rows(journal_case[0]) == 0
