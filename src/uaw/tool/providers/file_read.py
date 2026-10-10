"""Exact file.read and injected registered-command/journal bridge, no local OS access."""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, cast

from uaw.shared.contracts import JsonObject, Ref, TrustedExecutionContext
from uaw.shared.schema import validate_contract
from uaw.tool.errors import fail, validate_dependency
from uaw.tool.ledger import action_key
from uaw.tool.providers.local import check_binding
from uaw.tool.schema import canonical
from uaw.workspace.contracts import RegisteredReceiptCommand, RunnerReceipt
from uaw.workspace.ports import SignaturePort

MAX_RETURN_BYTES = 65536
MAX_SNAPSHOT_BYTES = 1048576
MAX_FILE_ENVELOPE_BYTES = 524288


@dataclass(frozen=True)
class FileReadEvidence:
    """Independent registered command/journal plus original immutable UTF-8 snapshot.

    snapshot is the actual original full file bytes, NOT a fresh reread after reply
    loss. selection and next_cursor come from a trusted original cursor registry.
    They are internal evidence, never accepted from model/HTTP parameters.
    """

    command_ref: Ref
    receipt_ref: Ref
    source: RegisteredReceiptCommand
    receipt: RunnerReceipt
    snapshot: bytes
    selection: JsonObject
    next_cursor: str | None = None


class ToolFileReadBridgePort(Protocol):
    def ready(self) -> None:
        """Fail if actual command/current authority/transport/journal sources absent."""
        ...

    async def resolve(
        self, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> tuple[Ref, ...]:
        """Current workspace/root/project read authorization and versions, no send."""
        ...

    async def execute(
        self, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> FileReadEvidence:
        """Register exact command before ONE transport send; persist refs before reply.

        Called only by Tool dispatch CAS owner. No transparent resend/reconnect.
        """
        ...

    async def recover(
        self, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> FileReadEvidence | None:
        """Current DATA authority + original immutable command/journal, never execute.

        Recheck full owner/session/project/root/device/key and original snapshots.
        None means no original observed receipt; not zero cost or not_applied.
        """
        ...


def file_read_spec(provider_ref: Ref) -> JsonObject:
    pin: JsonObject = {
        "type": "object",
        "properties": {
            "kind": {"type": "string", "const": "workspace"},
            "id": {"type": "string", "minLength": 1, "maxLength": 128},
            "version": {"type": "string", "minLength": 1, "maxLength": 128},
            "content_hash": {"type": "string", "minLength": 64, "maxLength": 64},
        },
        "required": ["kind", "id", "version"],
        "additionalProperties": False,
    }
    location: JsonObject = {
        "type": "object",
        "properties": {
            "kind": {"type": "string", "enum": ["whole", "text_span", "lines"]},
            "start": {"type": "integer", "minimum": 0, "maximum": MAX_SNAPSHOT_BYTES},
            "end": {"type": "integer", "minimum": 0, "maximum": MAX_SNAPSHOT_BYTES},
        },
        "required": ["kind"],
        "additionalProperties": False,
    }
    path: JsonObject = {"type": "string", "minLength": 1, "maxLength": 1024}
    cursor: JsonObject = {"type": "string", "minLength": 1, "maxLength": 2048}
    return {
        "id": "file.read",
        "version": "1",
        "description": "Read authorized UTF-8 file content with original signed evidence",
        "categories": ["file"],
        "required_capabilities": ["workspace.process"],
        "effect": "read",
        "feature_flag": "file_access",
        "provider_ref": provider_ref.wire(),
        "retry_policy_ref": {"kind": "policy", "id": "no-automatic-retry", "version": "1"},
        "input_schema": {
            "type": "object",
            "properties": {
                "workspace_ref": pin,
                "path": path,
                "location": location,
                "cursor": cursor,
            },
            "required": ["workspace_ref", "path"],
            "additionalProperties": False,
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "workspace_ref": pin,
                "path": path,
                "encoding": {"type": "string", "const": "utf-8"},
                "text": {"type": "string", "maxLength": MAX_RETURN_BYTES},
                "content_hash": {"type": "string", "minLength": 64, "maxLength": 64},
                "location": location,
                "next_cursor": cursor,
            },
            "required": ["workspace_ref", "path", "encoding", "text", "content_hash", "location"],
            "additionalProperties": False,
        },
    }


def file_estimates(currency: str = "USD") -> JsonObject:
    # This is an admission ceiling, NOT a tariff or actual charge claim.
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "model_calls": 0,
        "tool_calls": 1,
        "child_agents": 0,
        "wall_time_ms": 10000,
        "money": "0.00",
        "currency": currency,
    }


def file_arguments(call: JsonObject, spec: JsonObject, provider_ref: Ref) -> JsonObject:
    args = check_binding(call, spec, provider_ref, file_read_spec)
    validate_contract("ToolFileReadInput", args)
    path = cast(str, args["path"])
    if (
        "\\" in path
        or ":" in path
        or "\x00" in path
        or path.endswith("/")
        or any(part in {"", ".", ".."} or part.endswith((" ", ".")) for part in path.split("/"))
    ):
        raise ValueError("Expected a canonical root-relative file path")
    pin = cast(JsonObject, args["workspace_ref"])
    if set(pin) - {"kind", "id", "version", "content_hash"} or pin["kind"] != "workspace":
        raise ValueError("Exact workspace version required")
    location = cast(JsonObject, args.get("location", {"kind": "whole"}))
    select_text("", location, validate_only=True)
    return args


def select_text(text: str, location: JsonObject, *, validate_only: bool = False) -> str:
    validate_contract("Location", location)
    if location == {"kind": "whole"}:
        return text
    if (
        set(location) != {"kind", "start", "end"}
        or location["kind"] not in {"text_span", "lines"}
        or type(location["start"]) is not int
        or type(location["end"]) is not int
    ):
        raise ValueError("Only whole, bounded text_span or lines supported")
    start, end = location["start"], location["end"]
    if not 0 <= start <= end <= MAX_SNAPSHOT_BYTES or (location["kind"] == "lines" and start < 1):
        raise ValueError("Invalid file range")
    if validate_only:
        return ""
    if location["kind"] == "text_span":
        if end > len(text):
            raise ValueError("Span exceeds actual file")
        return text[start:end]
    lines = text.splitlines(keepends=True)
    if end > len(lines):
        raise ValueError("Line range exceeds actual file")
    return "".join(lines[start - 1 : end])


def _pin(ref: Ref) -> None:
    validate_contract("Ref", ref.wire())
    if (
        ref.kind != "content"
        or ref.content_hash is None
        or ref.version != "1"
        or ref.location is not None
        or ref.access_scope is not None
    ):
        raise ValueError("Original complete content Ref required")


def verify_file_evidence(
    evidence: FileReadEvidence,
    call: JsonObject,
    spec: JsonObject,
    ctx: TrustedExecutionContext,
    provider_ref: Ref,
    signatures: SignaturePort,
) -> JsonObject:
    args = file_arguments(call, spec, provider_ref)
    _pin(evidence.command_ref)
    _pin(evidence.receipt_ref)
    command, receipt, owner = evidence.source.command, evidence.receipt, evidence.source.owner
    validate_dependency("RunnerCommand", command.wire(), "file_evidence")
    validate_dependency("RunnerReceipt", receipt.wire(), "file_evidence")
    command_bytes = canonical(command.wire())
    receipt_bytes = canonical(receipt.wire(), max_bytes=MAX_FILE_ENVELOPE_BYTES)
    expected_receipt_id = (
        "runner_receipt-"
        + hashlib.sha256(
            canonical(
                [
                    owner.kind,
                    owner.id,
                    evidence.source.device_id,
                    command.command_id,
                    ctx.attempt_id,
                ]
            )
        ).hexdigest()
    )
    if (
        owner != ctx.principal
        or command.trusted_context.wire() != ctx.wire()
        or command.operation_id != ctx.operation_id
        or command.request_ref.kind != "tool_call"
        or command.request_ref.id != action_key(ctx, str(call["action_id"]))
        or command.request_ref.version != "1"
        or command.request_ref.content_hash != hashlib.sha256(canonical(call)).hexdigest()
        or command.parameters != {"action": "file.read", "parameters": args}
        or datetime.fromisoformat(command.expires_at.replace("Z", "+00:00"))
        > datetime.fromisoformat(ctx.deadline.replace("Z", "+00:00"))
        or evidence.command_ref.content_hash != hashlib.sha256(command_bytes).hexdigest()
        or receipt.command_id != command.command_id
        or receipt.attempt_id != ctx.attempt_id
        or receipt.usage["attempt_id"] != ctx.attempt_id
        or evidence.receipt_ref.id != expected_receipt_id
        or evidence.receipt_ref.content_hash != hashlib.sha256(receipt_bytes).hexdigest()
        or not signatures.verify_command(command, device_id=evidence.source.device_id)
        or not signatures.verify_receipt(receipt.wire(), device_id=evidence.source.device_id)
    ):
        raise fail(
            "receipt_binding_conflict",
            "Original signed file command/owner/attempt differs",
            phase="file_evidence",
            category="conflict",
            status=409,
        )
    if receipt.kind != "ok" or receipt.payload is None:
        raise fail(
            "unknown_effect",
            "Runner result has no verified successful file content",
            phase="file_evidence",
            category="unknown_effect",
            status=409,
        )
    if set(receipt.payload) != {"action", "result"} or receipt.payload["action"] != "file.read":
        raise ValueError("Exact file result payload required")
    data = cast(JsonObject, receipt.payload["result"])
    validate_dependency("FileContent", data, "file_evidence")
    if type(evidence.snapshot) is not bytes or len(evidence.snapshot) > MAX_SNAPSHOT_BYTES:
        raise ValueError("Actual bounded original snapshot required")
    text = evidence.snapshot.decode("utf-8", errors="strict")
    selected = select_text(text, evidence.selection)
    location = args.get("location", {"kind": "whole"})
    # A trusted cursor registry is still constrained by the fixed original range.
    if evidence.selection != location:
        if not isinstance(location, dict):
            raise ValueError("Exact original file location required")
        selected_range = evidence.selection
        kind = "text_span" if location == {"kind": "whole"} else location["kind"]
        lower = 0 if location == {"kind": "whole"} else cast(int, location["start"])
        upper = len(text) if location == {"kind": "whole"} else cast(int, location["end"])
        if (
            selected_range.get("kind") != kind
            or set(selected_range) != {"kind", "start", "end"}
            or not lower
            <= cast(int, selected_range["start"])
            <= cast(int, selected_range["end"])
            <= upper
            or ("cursor" not in args and selected_range["start"] != lower)
        ):
            raise ValueError("Registered page escapes original fixed range")
    if "cursor" not in args and evidence.selection != location and evidence.next_cursor is None:
        raise ValueError("Original unpaged selection differs")
    if (
        "cursor" not in args
        and evidence.next_cursor is None
        and data.get("next_cursor") is not None
    ):
        raise ValueError("Unregistered continuation cursor")
    if (
        data["workspace_ref"] != args["workspace_ref"]
        or data["path"] != args["path"]
        or data["location"] != location
        or data["encoding"] != "utf-8"
        or data["text"] != selected
        or len(selected.encode("utf-8")) > MAX_RETURN_BYTES
        or len(selected) > MAX_RETURN_BYTES
        or data["content_hash"] != hashlib.sha256(evidence.snapshot).hexdigest()
        or data.get("next_cursor") != evidence.next_cursor
        or (evidence.next_cursor is not None and evidence.next_cursor == args.get("cursor"))
    ):
        raise fail(
            "tool_output_invalid",
            "Actual file bytes/range/hash/cursor evidence differs",
            phase="file_evidence",
            category="conflict",
            status=409,
        )
    return data
