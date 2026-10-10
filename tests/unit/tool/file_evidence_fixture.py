"""Actual Ed25519 and exact snapshot evidence; registration/authorization controlled."""

import hashlib
from dataclasses import replace

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from uaw.shared.contracts import Ref
from uaw.shared.runner_signatures import VerificationKey, sign, verify
from uaw.tool.invocation.schema import normalize
from uaw.tool.ledger import action_key
from uaw.tool.providers.file_read import FileReadEvidence, file_read_spec, select_text
from uaw.tool.registry import ToolRegistry
from uaw.tool.schema import canonical, digest
from uaw.workspace.contracts import RegisteredReceiptCommand, RunnerCommand, RunnerReceipt

PROVIDER = Ref(kind="provider", id="controlled-file-provider", version="1")
WORKSPACE = Ref(kind="workspace", id="controlled-workspace", version="1")


class ControlledKeyDirectorySignatures:
    """Real crypto with two in-memory ephemeral keys; no production key registration."""

    def __init__(self):
        self.control = Ed25519PrivateKey.generate()
        self.device = Ed25519PrivateKey.generate()
        self.revoked = False

    def signed(self, document, domain):
        key = self.control if domain == "command" else self.device
        return {
            **document,
            "signature": sign(
                document, key.private_bytes_raw(), "controlled-device", domain, domain
            ),
        }

    def verify_command(self, command, *, device_id):
        return device_id == "controlled-device" and verify(
            command.wire(),
            command.signature,
            VerificationKey(
                "command",
                device_id,
                self.control.public_key().public_bytes_raw(),
                "control",
                self.revoked,
            ),
            "command",
        )

    def verify_receipt(self, receipt, *, device_id):
        return device_id == "controlled-device" and verify(
            receipt,
            receipt["signature"],
            VerificationKey(
                "receipt",
                device_id,
                self.device.public_key().public_bytes_raw(),
                "device",
                self.revoked,
            ),
            "receipt",
        )


def make_evidence(
    ctx,
    *,
    text="first\r\n第二行😀\nlast",
    arguments=None,
    signatures=None,
    provider_ref=PROVIDER,
    call=None,
):
    signatures = signatures or ControlledKeyDirectorySignatures()
    spec = file_read_spec(provider_ref)
    registry = ToolRegistry()
    registry.register(spec, expected_revision=0)
    arguments = arguments or {"workspace_ref": WORKSPACE.wire(), "path": "file.txt"}
    if call is None:
        call = normalize(
            {
                "tool_ref": registry.reference(registry.snapshot()[1][0]),
                "arguments": arguments,
                "action_id": "file-action",
            },
            registry,
        )
    snapshot = text.encode("utf-8")
    location = arguments.get("location", {"kind": "whole"})
    data = {
        "workspace_ref": arguments["workspace_ref"],
        "path": arguments["path"],
        "text": select_text(text, location),
        "encoding": "utf-8",
        "location": location,
        "content_hash": hashlib.sha256(snapshot).hexdigest(),
    }
    command = RunnerCommand.model_validate_json(
        canonical(
            signatures.signed(
                {
                    "command_id": "file-command-" + ctx.attempt_id,
                    "operation_id": ctx.operation_id,
                    "request_ref": {
                        "kind": "tool_call",
                        "id": action_key(ctx, call["action_id"]),
                        "version": "1",
                        "content_hash": digest(call),
                    },
                    "trusted_context": ctx.wire(),
                    "fencing_token": 1,
                    "expires_at": ctx.deadline,
                    "parameters": {"action": "file.read", "parameters": arguments},
                },
                "command",
            )
        )
    )
    usage = {
        "attempt_id": ctx.attempt_id,
        "billing_state": "pending",
        "resources": {"currency": "USD", "wall_time_ms": 1},
    }
    receipt = RunnerReceipt.model_validate(
        signatures.signed(
            {
                "command_id": command.command_id,
                "attempt_id": ctx.attempt_id,
                "kind": "ok",
                "usage": usage,
                "payload": {"action": "file.read", "result": data},
            },
            "receipt",
        )
    )
    command_ref = Ref(
        kind="content",
        id="command-" + ctx.attempt_id,
        version="1",
        content_hash=digest(command.wire()),
    )
    ident = hashlib.sha256(
        canonical(
            [
                ctx.principal.kind,
                ctx.principal.id,
                "controlled-device",
                command.command_id,
                ctx.attempt_id,
            ]
        )
    ).hexdigest()
    receipt_ref = Ref(
        kind="content",
        id="runner_receipt-" + ident,
        version="1",
        content_hash=hashlib.sha256(canonical(receipt.wire(), max_bytes=524288)).hexdigest(),
    )
    evidence = FileReadEvidence(
        command_ref,
        receipt_ref,
        RegisteredReceiptCommand(command, "controlled-device", ctx.principal),
        receipt,
        snapshot,
        location,
    )
    return registry, call, spec, evidence, signatures


def resign_evidence(evidence, data, signatures):
    receipt = RunnerReceipt.model_validate(
        signatures.signed(
            {**evidence.receipt.wire(), "payload": {"action": "file.read", "result": data}},
            "receipt",
        )
    )
    pin = evidence.receipt_ref.model_copy(
        update={
            "content_hash": hashlib.sha256(canonical(receipt.wire(), max_bytes=524288)).hexdigest()
        }
    )
    return replace(evidence, receipt=receipt, receipt_ref=pin)
