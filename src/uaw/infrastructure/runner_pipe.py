"""Explicit control-side read transport; independent command and receipt verification."""

import asyncio
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Protocol

from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.workspace.contracts import RegisteredReceiptCommand, RunnerReceipt
from uaw.workspace.ports import ReceiptCommandReaderPort, SignaturePort

Payload = dict[str, Any]


def canonical(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    )


def digest(value: Payload) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def fixed_ref(ref: Ref) -> Ref:
    if (
        ref.kind != "content"
        or ref.content_hash is None
        or ref.location is not None
        or ref.access_scope is not None
    ):
        raise reject("runner_pipe_ref_invalid", "Complete content Ref required", 412)
    return ref


class PeerPort(Protocol):
    @property
    def role(self) -> str: ...
    @property
    def device_id(self) -> str: ...


class PipePort(Protocol):
    @property
    def timeout(self) -> float: ...


class ControlPipeSession(Protocol):
    @property
    def local(self) -> PeerPort | None: ...
    @property
    def channel_ref(self) -> Ref | None: ...
    @property
    def pipe(self) -> PipePort: ...
    async def check(self) -> None: ...
    async def send(self, kind: str, body: Payload) -> None: ...
    async def receive(self) -> Payload: ...
    async def close(self) -> None: ...


class LiveChannelRegistry(Protocol):
    async def authenticated_principal(self, channel_ref: Ref, *, device_id: str) -> Principal: ...


@dataclass(frozen=True)
class CheckedPipeReceipt:
    command_ref: Ref
    receipt_ref: Ref
    receipt: RunnerReceipt


def verify_receipt_body(
    body: Payload,
    source: RegisteredReceiptCommand,
    command_ref: Ref,
    signatures: SignaturePort,
) -> CheckedPipeReceipt:
    if (
        set(body) != {"command_ref", "receipt_ref", "receipt"}
        or body["command_ref"] != command_ref.wire()
    ):
        raise reject("runner_pipe_response_invalid", "Exact original command receipt required", 412)
    ref = fixed_ref(Ref.model_validate_json(canonical(body["receipt_ref"])))
    receipt = RunnerReceipt.model_validate_json(canonical(body["receipt"]))
    command = source.command
    expected_id = (
        "runner_receipt-"
        + hashlib.sha256(
            canonical(
                [
                    source.owner.kind,
                    source.owner.id,
                    source.device_id,
                    command.command_id,
                    command.trusted_context.attempt_id,
                ]
            ).encode("utf-8")
        ).hexdigest()
    )
    if ref.id != expected_id or ref.version != "1" or ref.content_hash != digest(receipt.wire()):
        raise reject("runner_pipe_receipt_changed", "Signed receipt digest differs", 412)
    if (
        not signatures.verify_receipt(receipt.wire(), device_id=source.device_id)
        or receipt.command_id != command.command_id
        or receipt.attempt_id != command.trusted_context.attempt_id
        or receipt.usage["attempt_id"] != receipt.attempt_id
    ):
        raise reject(
            "runner_pipe_receipt_denied", "Device signature or original attempt differs", 403
        )
    if command.parameters["action"] != "file.read":
        raise CapabilityUnavailable("runner.pipe.read_only")
    if receipt.payload is not None:
        if receipt.payload["action"] != "file.read":
            raise reject("runner_pipe_receipt_changed", "Result action differs", 412)
        result = receipt.payload["result"]
        parameters = command.parameters["parameters"]
        if not isinstance(result, dict) or not isinstance(parameters, dict):
            raise reject("runner_pipe_response_invalid", "Actual FileContent required", 412)
        text = result["text"]
        if not isinstance(text, str):
            raise reject("runner_pipe_response_invalid", "Actual UTF-8 text required", 412)
        if (
            result["workspace_ref"] != parameters["workspace_ref"]
            or result["path"] != parameters["path"]
            or result["location"] != parameters.get("location", {"kind": "whole"})
            or result["encoding"] != "utf-8"
            or len(text.encode("utf-8")) > 65536
        ):
            raise reject("runner_pipe_receipt_changed", "Actual file result binding differs", 412)
        # Whole-file hashes cannot be checked from partial/line/cursor content.
        if (
            result["location"] == {"kind": "whole"}
            and not result.get("next_cursor")
            and hashlib.sha256(text.encode("utf-8")).hexdigest() != result["content_hash"]
        ):
            raise reject("runner_pipe_content_changed", "Whole-file content hash differs", 412)
    return CheckedPipeReceipt(command_ref, ref, receipt)


class RunnerPipeClient:
    def __init__(
        self,
        *,
        session: ControlPipeSession,
        registry: LiveChannelRegistry,
        commands: ReceiptCommandReaderPort | None,
        signatures: SignaturePort | None,
    ) -> None:
        self.session, self.registry, self.commands = session, registry, commands
        self.signatures = signatures
        self.busy = False

    async def read(self, command_ref: Ref, *, recover: bool = False) -> CheckedPipeReceipt:
        if self.busy:
            raise reject("ipc_busy", "Original control exchange is still pending", 409)
        if (
            self.commands is None
            or self.signatures is None
            or self.session.local is None
            or self.session.local.role != "control"
        ):
            raise CapabilityUnavailable("runner.pipe.registered_control_source")
        ref = fixed_ref(command_ref)
        channel = self.session.channel_ref
        if channel is None:
            raise CapabilityUnavailable("runner.ipc.handshake")
        self.busy = True
        try:
            async with asyncio.timeout(self.session.pipe.timeout):
                device = self.session.local.device_id
                actor = await self.registry.authenticated_principal(channel, device_id=device)
                source = await self.commands.resolve(ref, authenticated_principal=actor)
                if source.device_id != device or ref.content_hash != digest(source.command.wire()):
                    raise reject(
                        "runner_pipe_source_denied", "Independent command/device differs", 403
                    )
                await self.session.check()
                await self.session.send(
                    "recover" if recover else "command", {"command_ref": ref.wire()}
                )
                frame = await self.session.receive()
                if frame["kind"] != "receipt":
                    raise reject(
                        "runner_pipe_response_invalid", "Actual signed receipt required", 412
                    )
                actual = verify_receipt_body(frame["body"], source, ref, self.signatures)
                if await self.commands.resolve(ref, authenticated_principal=actor) != source:
                    raise reject("runner_pipe_source_changed", "Recovery source changed", 412)
                await self.session.check()
                return actual
        except BaseException:
            # No transparent reconnect or resend of an unknown original command.
            await self.session.close()
            raise
        finally:
            self.busy = False
