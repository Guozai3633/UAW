"""A/C bridge with real SQL/crypto and a controlled pipe; not native human approval."""

import hashlib
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from tests.integration.test_runner_control import case as case
from uaw.infrastructure.db.transactions import reference
from uaw.infrastructure.runner_pipe import RunnerPipeClient, digest
from uaw.run.file_bridge import FileDeviceRoute, RegisteredFileBridge
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.shared.errors import DomainError, reject
from uaw.shared.runner_signatures import VerificationKey, sign, verify
from uaw.tool.invocation.schema import normalize
from uaw.tool.ledger import ToolLedger, action_key
from uaw.tool.providers.file_read import file_read_spec
from uaw.tool.registry import ToolRegistry
from uaw.workspace.contracts import RunnerReceipt


class Access:
    allowed = True

    async def check(self, call, spec, ctx, *, provider):
        if not self.allowed:
            raise reject("fixture_data_revoked", "Controlled current data authority revoked", 403)


class Signatures:
    def __init__(self, c):
        self.c = c
        self.device = Ed25519PrivateKey.generate()

    def verify_command(self, command, *, device_id):
        return verify(
            command.wire(),
            command.signature,
            VerificationKey(
                "fixture-control",
                device_id,
                self.c.signer.private.public_key().public_bytes_raw(),
                "control",
                self.c.signer.revoked,
            ),
            "command",
        )

    def verify_receipt(self, receipt, *, device_id):
        return verify(
            receipt,
            receipt["signature"],
            VerificationKey(
                "fixture-device", device_id, self.device.public_key().public_bytes_raw(), "device"
            ),
            "receipt",
        )


class Session:
    """Controlled transport journal reads a temp file once, preserving original bytes."""

    def __init__(self, c, signatures, path, journal):
        self.c, self.signatures, self.path, self.journal = c, signatures, path, journal
        self.local = SimpleNamespace(role="control", device_id=c.device["device_id"])
        self.channel_ref = Ref.model_validate(c.channel.value["channel_ref"])
        self.pipe = SimpleNamespace(timeout=10)
        self.opens, self.sent, self.closed = 0, [], False
        self.lose_reply = self.tamper = False

    async def check(self):
        if self.closed:
            raise reject("fixture_closed", "Controlled transport closed", 409)

    async def close(self):
        self.closed = True

    async def send(self, kind, body):
        self.sent.append(kind)
        command_ref = body["command_ref"]
        record = await self.c.commands.record(command_ref["id"])
        command = record["command"]
        if kind == "command":
            assert command_ref["id"] not in self.journal
            self.opens += 1
            raw = self.path.read_bytes()
            ctx = command["trusted_context"]
            payload = {
                "action": "file.read",
                "result": {
                    **command["parameters"]["parameters"],
                    "encoding": "utf-8",
                    "text": raw.decode("utf-8"),
                    "location": {"kind": "whole"},
                    "content_hash": hashlib.sha256(raw).hexdigest(),
                },
            }
            value = {
                "command_id": command["command_id"],
                "attempt_id": ctx["attempt_id"],
                "kind": "ok",
                "payload": payload,
                "usage": {
                    "attempt_id": ctx["attempt_id"],
                    "billing_state": "pending",
                    "resources": {"tool_calls": 1, "currency": "USD"},
                },
            }
            value["signature"] = sign(
                value,
                self.signatures.device.private_bytes_raw(),
                self.local.device_id,
                "fixture-device",
                "receipt",
            )
            owner = Principal.model_validate(ctx["principal"])
            rid = "runner_receipt-" + digest_list(
                [
                    owner.kind,
                    owner.id,
                    self.local.device_id,
                    command["command_id"],
                    ctx["attempt_id"],
                ]
            )
            receipt = RunnerReceipt.model_validate(value)
            self.journal[command_ref["id"]] = {
                "command_ref": command_ref,
                "receipt_ref": {
                    "kind": "content",
                    "id": rid,
                    "version": "1",
                    "content_hash": digest(receipt.wire()),
                },
                "receipt": receipt.wire(),
            }
        self.reply = self.journal[command_ref["id"]]

    async def receive(self):
        if self.lose_reply:
            raise TimeoutError("Controlled original reply loss")
        body = self.reply
        if self.tamper:
            body = {**body, "receipt_ref": {**body["receipt_ref"], "content_hash": "0" * 64}}
        return {"kind": "receipt", "body": body}


def digest_list(value):
    from uaw.infrastructure.runner_pipe import canonical

    return hashlib.sha256(canonical(value).encode()).hexdigest()


@pytest.fixture
async def bridge_case(case, tmp_path):
    import json

    c = case
    ctx = TrustedExecutionContext.model_validate_json(
        json.dumps({k: v for k, v in c.ctx.wire().items() if k != "budget_reservation_ref"})
    )
    provider_ref = Ref(kind="provider", id="fixture-provider", version="1")
    provider = Principal(
        id="fixture-file-service", kind="service", auth_session_id="fixture-service"
    )
    spec = file_read_spec(provider_ref)
    registry = ToolRegistry()
    registry.register(spec, expected_revision=0)
    call = normalize(
        {
            "tool_ref": registry.reference(registry.snapshot()[1][0]),
            "arguments": c.request["parameters"]["parameters"],
            "action_id": "bridge-file-read",
        },
        registry,
    )
    ledger = ToolLedger(c.commands.store)
    key = await ledger.bind(call, spec, ctx)
    reservation = await c.budgets.get_reservation(c.ctx.budget_reservation_ref.id, ctx)
    await ledger.save("tool.budget.reserved", ctx.attempt_id, "BudgetReservation", reservation, ctx)
    intent = {
        "validated_action_ref": reference("tool_call", key),
        "reservation_ref": reference("reservation", reservation["id"], reservation["revision"]),
        "provider_binding_ref": spec["provider_ref"],
    }
    await ledger.claim(intent, ctx, budget=await c.budgets.get_ledger(ctx), reservation=reservation)
    ack = await c.budgets.dispatch(
        ctx.principal, intent["reservation_ref"], meta("bridge-dispatch"), ctx
    )
    await ledger.acknowledge(ack, ctx)
    route = FileDeviceRoute(
        Ref.model_validate(c.registered["device_ref"]),
        Ref.model_validate(call["arguments"]["workspace_ref"]),
    )

    class Routes:
        async def current(self, workspace, context):
            assert workspace == route.workspace_ref and context == ctx
            return route

    class Registry:
        async def authenticated_principal(self, channel_ref, *, device_id):
            assert (
                channel_ref.wire() == c.channel.value["channel_ref"]
                and device_id == c.device["device_id"]
            )
            return c.actor

    from uaw.run.runner_receipts import RegisteredReceiptCommandReader

    signatures = Signatures(c)
    path = tmp_path / "read.txt"
    path.write_bytes("actual original 中😀\n".encode())
    journal = {}
    session = Session(c, signatures, path, journal)

    def client(s):
        return RunnerPipeClient(
            session=s,
            registry=Registry(),
            commands=RegisteredReceiptCommandReader(c.commands),
            signatures=signatures,
        )

    access = Access()
    bridge = RegisteredFileBridge(
        commands=c.commands,
        pipe=client(session),
        routes=Routes(),
        access=access,
        provider_ref=provider_ref,
        provider=provider,
        signatures=signatures,
    )
    return SimpleNamespace(
        c=c,
        ctx=ctx,
        call=call,
        spec=spec,
        bridge=bridge,
        session=session,
        path=path,
        client=client,
        signatures=signatures,
        journal=journal,
        access=access,
    )


async def test_file_bridge_signed_original_snapshot_and_recovery_no_open(bridge_case):
    p = bridge_case
    from uaw.tool.providers.file_store import FileResourceReader

    resources = await FileResourceReader(p.bridge.provider_ref, p.bridge).resolve(
        p.call, p.spec, p.ctx
    )
    assert resources == (Ref.model_validate(p.call["arguments"]["workspace_ref"]),)
    original = await p.bridge.execute(p.call, p.spec, p.ctx)
    assert original.snapshot == "actual original 中😀\n".encode()
    assert original.source.command.request_ref.id == action_key(p.ctx, p.call["action_id"])
    assert original.source.command.trusted_context == p.ctx
    p.path.write_text("changed after original read", encoding="utf-8")
    recovered = await p.bridge.recover(p.call, p.spec, p.ctx)
    assert (
        recovered == original and p.session.opens == 1 and p.session.sent == ["command", "recover"]
    )
    with pytest.raises(DomainError) as duplicate:
        await p.bridge.execute(p.call, p.spec, p.ctx)
    assert duplicate.value.failure.category == "unknown_effect" and p.session.opens == 1


async def test_file_bridge_reply_loss_recovers_only_original_journal(bridge_case):
    p = bridge_case
    p.session.lose_reply = True
    with pytest.raises(TimeoutError):
        await p.bridge.execute(p.call, p.spec, p.ctx)
    assert p.session.closed and p.session.opens == 1
    p.path.unlink()
    fresh = Session(p.c, p.signatures, p.path, p.journal)
    p.bridge.pipe = p.client(fresh)
    value = await p.bridge.recover(p.call, p.spec, p.ctx)
    assert value.snapshot == "actual original 中😀\n".encode()
    assert fresh.opens == 0 and fresh.sent == ["recover"]


async def test_file_bridge_data_revocation_blocks_recovery_before_transport(bridge_case):
    p = bridge_case
    await p.bridge.execute(p.call, p.spec, p.ctx)
    p.access.allowed = False
    with pytest.raises(DomainError):
        await p.bridge.recover(p.call, p.spec, p.ctx)
    assert p.session.sent == ["command"]


async def test_file_bridge_rejects_tampered_receipt_and_missing_dependency(bridge_case):
    p = bridge_case
    p.session.tamper = True
    with pytest.raises(DomainError):
        await p.bridge.execute(p.call, p.spec, p.ctx)
    assert p.session.closed and p.session.opens == 1
    p.bridge.pipe = None
    with pytest.raises(DomainError) as missing:
        await p.bridge.resolve(p.call, p.spec, p.ctx)
    assert missing.value.status_code == 503


async def test_file_bridge_executor_persists_actual_c_evidence_and_reads_original(
    bridge_case, tmp_path
):
    from tests.integration.test_stage_wiring import container
    from uaw.composition import assemble_file_tool

    p = bridge_case
    registry = ToolRegistry()
    registry.register(p.spec, expected_revision=0)
    pin = Ref.model_validate(registry.reference(registry.snapshot()[1][0]))
    c = container(p.c.commands.store, p.c.domain[0], tmp_path)
    binding = assemble_file_tool(
        c,
        registry=registry,
        tool_ref=pin,
        provider=p.bridge.provider,
        bridge=p.bridge,
        recovery_access=p.access,
        signatures=p.signatures,
        money_ceiling="0.10",
    )
    # The owning Tool dispatch was independently fixed in this component fixture.
    # This direct executor check is not a product approval or native human grant.
    receipt = await binding.executor.execute(p.call, p.spec, p.ctx)
    assert receipt["attempt_id"] == p.ctx.attempt_id
    original = await binding.receipts.read_observation(p.call["action_id"], p.ctx)
    assert original.snapshot == "actual original 中😀\n".encode()
    p.path.unlink()
    reread = await binding.receipts.read_observation(p.call["action_id"], p.ctx)
    assert reread == original and p.session.opens == 1
    from uaw.run.file_context import FileContextMaterials

    reader = FileContextMaterials(c.records, c.configuration.platform, binding.materials)
    pin = await reader.register(
        p.call["action_id"], p.ctx, authenticated_service=c.configuration.platform
    )
    # Reconstruct the A consumer after deleting the original file. Every read still
    # traverses C's current owning journal/verifier, never opens or copies a new blob.
    restarted = FileContextMaterials(c.records, c.configuration.platform, binding.materials)
    data = await restarted.read(pin, p.ctx)
    assert data.text == "actual original 中😀\n" and data.trust == "external"
    assert data.kind == "material" and not data.required and data.ref == pin
    assert p.session.opens == 1
    spoof = p.ctx.model_copy(
        update={
            "principal": p.ctx.principal.model_copy(
                update={"auth_session_id": "different-user-session"}
            )
        }
    )
    with pytest.raises(DomainError):
        await restarted.read(pin, spoof)
    p.access.allowed = False
    with pytest.raises(DomainError):
        await restarted.read(pin, p.ctx)
    assert p.session.opens == 1
