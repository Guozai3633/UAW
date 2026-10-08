"""Control-key binding and published signing port; caller must be a trusted service adapter."""

import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import MappingProxyType

from uaw.shared.contracts import JsonObject
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.runner_signatures import VerificationKey
from uaw.shared.schema import validate_contract
from uaw.workspace.binding import aware
from uaw.workspace.contracts import RunnerCommand
from uaw.workspace.ports import CurrentKeyDirectory
from uaw_runner.keys import Ed25519SignatureAdapter, ProtectedSigner, signature_key_id
from uaw_runner.protocol import timestamp


@dataclass(frozen=True)
class ControlKeyBinding:
    device_id: str
    key_id: str
    credential_handle: str = field(repr=False)


class ControlCommandSigner:
    def __init__(
        self,
        bindings: tuple[ControlKeyBinding, ...],
        *,
        directory: CurrentKeyDirectory,
        signer: ProtectedSigner | None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        # Independent construction source; no key/credential/owner is accepted in draft.
        bound = {}
        for binding in bindings:
            for value in (binding.device_id, binding.key_id, binding.credential_handle):
                validate_contract("ID", value)
            if binding.device_id in bound:
                raise ValueError("One fixed control binding per device is required")
            bound[binding.device_id] = binding
        if signer is not None and signer.directory is not directory:
            raise ValueError("Signer and verifier require the same current key directory")
        self.bindings = MappingProxyType(bound)
        self.directory, self.signer = directory, signer
        self.clock = clock or (lambda: datetime.now(UTC))

    def _binding(self, device_id: str) -> ControlKeyBinding:
        validate_contract("ID", device_id)
        binding = self.bindings.get(device_id)
        if binding is None:
            raise CapabilityUnavailable("runner.control_key_binding")
        return binding

    def _deadline(self, command: RunnerCommand) -> None:
        if min(timestamp(command.expires_at), timestamp(command.trusted_context.deadline)) <= aware(
            self.clock()
        ):
            raise reject("deadline_exceeded", "Control signing deadline exceeded", 410, "timeout")

    async def _key(self, binding: ControlKeyBinding) -> VerificationKey:
        key = await asyncio.to_thread(
            self.directory.lookup, binding.key_id, device_id=binding.device_id
        )
        if (
            key.key_id != binding.key_id
            or key.device_id != binding.device_id
            or key.role != "control"
            or key.revoked
        ):
            raise reject(
                "permission_denied", "Current control key binding rejected", 403, "permission"
            )
        return key

    async def sign(self, draft: JsonObject, *, device_id: str) -> JsonObject:
        validate_contract("RunnerCommandDraft", draft)
        snapshot = json.loads(json.dumps(draft, ensure_ascii=False, allow_nan=False))
        command = RunnerCommand.model_validate_json(
            json.dumps({**snapshot, "signature": "pending"})
        )
        if command.operation_id != command.trusted_context.operation_id:
            raise reject("binding_mismatch", "Control command operation differs", 403, "permission")
        binding = self._binding(device_id)
        if self.signer is None:
            raise CapabilityUnavailable("runner.protected_control_signer")
        self._deadline(command)
        key = await self._key(binding)
        self._deadline(command)
        signature = await self.signer.sign_document(
            command.wire(),
            device_id=device_id,
            key_id=binding.key_id,
            domain="command",
            credential_handle=binding.credential_handle,
        )
        self._deadline(command)
        if await self._key(binding) != key:
            raise reject(
                "permission_denied", "Control key changed during signing", 403, "permission"
            )
        self._deadline(command)
        result = {**snapshot, "signature": signature}
        signed = RunnerCommand.model_validate_json(json.dumps(result))
        if not await asyncio.to_thread(
            Ed25519SignatureAdapter(self.directory).verify_command, signed, device_id=device_id
        ):
            raise reject(
                "permission_denied", "Control signature verification failed", 403, "permission"
            )
        self._deadline(command)
        return signed.wire()

    async def verify(self, command: JsonObject, *, device_id: str) -> None:
        signed = RunnerCommand.model_validate_json(
            json.dumps(command, ensure_ascii=False, allow_nan=False)
        )
        binding = self._binding(device_id)
        if signature_key_id(signed.signature) != binding.key_id:
            raise reject(
                "permission_denied",
                "Signature differs from registered control key",
                403,
                "permission",
            )
        key = await self._key(binding)
        if not await asyncio.to_thread(
            Ed25519SignatureAdapter(self.directory).verify_command, signed, device_id=device_id
        ):
            raise reject("permission_denied", "Control signature rejected", 403, "permission")
        if await self._key(binding) != key:
            raise reject(
                "permission_denied", "Control key changed during verification", 403, "permission"
            )
        # Historical verification serves recovery too. It is never new admission or dispatch.
