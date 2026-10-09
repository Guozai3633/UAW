"""Signed read-only execution with independent current sources and durable once use.

Construction does not authenticate a channel. A trusted transport supplies actor;
RunnerChannelSourcePort and mapping independently validate its registered relationship.
"""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Event
from typing import TypeVar

from uaw.shared.contracts import JsonObject, Principal, Ref
from uaw.shared.errors import CapabilityUnavailable, DomainError, reject
from uaw.shared.ports import RunnerChannelSourcePort, RunnerRootSourcePort
from uaw.shared.schema import validate_contract
from uaw.workspace.binding import aware
from uaw.workspace.contracts import (
    RegisteredReceiptCommand,
    RunnerAuthoritySnapshot,
    RunnerChannelSnapshot,
    RunnerCommand,
    RunnerReceipt,
    RunnerRootSnapshot,
)
from uaw_runner.async_admission import AsyncAdmission
from uaw_runner.handle_read import WindowsReadHandle
from uaw_runner.keys import ProtectedSigner
from uaw_runner.protocol import RunnerProtocol, timestamp
from uaw_runner.read_state import ReadAttempt, ReadExecutionJournal
from uaw_runner.receipts import ReceiptJournal, canonical, fixed_ref

T = TypeVar("T")


@dataclass(frozen=True)
class DeviceSigningBinding:
    device_id: str
    key_id: str
    credential_handle: str = field(repr=False)

    def __post_init__(self) -> None:
        for value in (self.device_id, self.key_id, self.credential_handle):
            validate_contract("ID", value)


class ReadOnlyRunner:
    def __init__(
        self,
        *,
        protocol: RunnerProtocol,
        command_ref: Ref,
        journal: ReceiptJournal,
        executions: ReadExecutionJournal | None,
        currency: str,
        roots: RunnerRootSourcePort | None = None,
        channel: RunnerChannelSourcePort | None = None,
        channel_ref: Ref | None = None,
        signer: ProtectedSigner | None = None,
        device_key: DeviceSigningBinding | None = None,
    ) -> None:
        # Fixed Ref supplied by trusted registration/assembly, never computed from input.
        self.protocol, self.command_ref, self.journal = protocol, fixed_ref(command_ref), journal
        self.executions, self.currency, self.roots = executions, currency, roots
        self.channel, self.channel_ref = channel, fixed_ref(channel_ref) if channel_ref else None
        self.signer, self.device_key = signer, device_key
        validate_contract("MeasuredResources", {"currency": currency})
        if journal.protocol is not protocol:
            raise reject("binding_mismatch", "Executor/journal protocol must be identical")
        if device_key is not None and device_key.device_id != protocol.device_id:
            raise reject("binding_mismatch", "Receipt key device differs")
        self.admission = AsyncAdmission(
            device_id=protocol.device_id,
            bindings=protocol.bindings,
            admissions=protocol.admissions,
            signatures=protocol.signatures,
            authority=protocol.async_authority,
            mapping=protocol.principal_mapping,
            clock=protocol.clock,
        )

    def available(self) -> None:
        for name, dependency in [
            ("channel", self.channel),
            ("channel_ref", self.channel_ref),
            ("root_source", self.roots),
            ("protected_signer", self.signer),
            ("device_key", self.device_key),
            ("read_journal", self.executions),
            ("command_reader", self.journal.reader),
            ("authority", self.protocol.async_authority),
            ("owner_mapping", self.protocol.principal_mapping),
            ("signature", self.protocol.signatures),
        ]:
            if dependency is None:
                raise CapabilityUnavailable("runner.file_read." + name)
        if self.signer is not None and self.signer.credentials is None:
            raise CapabilityUnavailable("runner.file_read.protected_credentials")

    async def channel_current(self, actor: Principal, owner: Principal) -> RunnerChannelSnapshot:
        assert (
            self.channel is not None
            and self.channel_ref is not None
            and self.device_key is not None
        )
        data = await self.channel.read(self.channel_ref, device_id=self.protocol.device_id)
        snapshot = RunnerChannelSnapshot.model_validate_json(canonical(data))
        if (
            snapshot.device_id != self.protocol.device_id
            or snapshot.owner.wire() != owner.wire()
            or snapshot.actor.wire() != actor.wire()
            or snapshot.channel_ref.wire() != self.channel_ref.wire()
            or snapshot.key_ref.id != self.device_key.key_id
        ):
            raise reject(
                "permission_denied", "Current channel/owner/actor/key mismatch", 403, "permission"
            )
        fixed_ref(snapshot.pairing_ref)
        fixed_ref(snapshot.key_ref)
        if not snapshot.connected:
            raise CapabilityUnavailable("runner.file_read.connected_channel")
        if timestamp(snapshot.expires_at) <= aware(self.protocol.clock()):
            raise reject("deadline_exceeded", "Authenticated channel expired", 410, "timeout")
        return snapshot

    async def current(
        self,
        command: RunnerCommand,
        actor: Principal,
        source: RegisteredReceiptCommand,
        expected: RunnerAuthoritySnapshot | None = None,
        channel_expected: RunnerChannelSnapshot | None = None,
    ) -> tuple[RunnerAuthoritySnapshot, RunnerChannelSnapshot]:
        self.admission.deadline(command)
        await self.journal._resolve(self.command_ref, actor, source)
        self.admission.deadline(command)
        owner = await self.admission.owner(command, actor)
        if owner.wire() != source.owner.wire():
            raise reject("binding_mismatch", "Registered owner changed", 403, "permission")
        channel = await self.channel_current(actor, owner)
        self.admission.deadline(command)
        if channel_expected is not None and channel.wire() != channel_expected.wire():
            raise reject("revision_conflict", "Authenticated channel version changed", 409)
        assert self.roots is not None
        root = RunnerRootSnapshot.model_validate_json(
            canonical(
                await self.roots.current(
                    self.protocol.device_id, command_workspace(command), command.trusted_context
                )
            )
        )
        self.admission.deadline(command)
        current = await self.admission.current(command, actor, owner)
        if (
            root.owner.wire() != owner.wire()
            or root.device_id != current.device_id
            or root.workspace_ref.wire() != current.workspace_ref.wire()
            or root.root_handle != current.root_handle
            or root.binding_revision != current.binding_revision
            or "file.read" not in root.allowed_actions
            or timestamp(root.expires_at) <= aware(self.protocol.clock())
        ):
            raise reject(
                "binding_mismatch", "Current root differs from authority", 403, "permission"
            )
        if expected is not None and current.wire() != expected.wire():
            raise reject("revision_conflict", "Read authority changed", 409)
        await asyncio.to_thread(self.admission.external, command, current)
        self.admission.deadline(command, current)
        # Query current authority AFTER critical external work, with a fresh owner/channel.
        final_owner = await self.admission.owner(command, actor)
        final_channel = await self.channel_current(actor, final_owner)
        self.admission.deadline(command, current)
        if final_channel.wire() != channel.wire():
            raise reject("revision_conflict", "Channel changed during external checks", 409)
        final = await self.admission.current(command, actor, final_owner)
        if final.wire() != current.wire():
            raise reject("revision_conflict", "Authority changed during external checks", 409)
        return final, final_channel

    def guard(
        self,
        command: RunnerCommand,
        current: RunnerAuthoritySnapshot,
        stopped: Event,
        handle: WindowsReadHandle | None = None,
    ) -> None:
        if stopped.is_set():
            raise reject("cancelled", "Read coroutine cancelled", 409, "cancelled")
        self.admission.external(command, current)
        if handle is not None:
            handle.check()
        self.admission.deadline(command, current)

    async def restore(
        self, attempt: ReadAttempt, source: RegisteredReceiptCommand, actor: Principal
    ) -> RunnerReceipt:
        assert self.executions is not None and self.protocol.principal_mapping is not None
        # Data recovery is distinct from new authority/admission; cancellation does not
        # authorize rerun. Current Reader, channel, mapping, root and device key still apply.
        await self.journal._resolve(self.command_ref, actor, source)
        owner = await self.protocol.principal_mapping.owner(
            authenticated_principal=actor, device_id=self.protocol.device_id
        )
        if owner.wire() != source.owner.wire():
            raise reject("permission_denied", "Recovery owner changed", 403, "permission")
        await self.channel_current(actor, owner)

        def root_access() -> None:
            if self.protocol.signatures is None or not self.protocol.signatures.verify_command(
                source.command, device_id=source.device_id
            ):
                raise reject(
                    "permission_denied", "Recovery command key rejected", 403, "permission"
                )
            grant = self.protocol.bindings.repository.get(attempt.root_handle)
            if (
                grant.revoked
                or grant.revision != attempt.root_revision
                or grant.owner is None
                or grant.owner.wire() != owner.wire()
                or grant.device_id != source.device_id
                or grant.workspace_ref.wire() != command_workspace(source.command).wire()
                or "read" not in grant.capabilities
                or grant.expires_at is None
                or grant.confirmation_expires_at is None
                or min(grant.expires_at, grant.confirmation_expires_at)
                <= aware(self.protocol.clock())
            ):
                raise reject(
                    "permission_denied", "Current root data access rejected", 403, "permission"
                )

        await asyncio.to_thread(root_access)
        if attempt.receipt_data is None:
            raise CapabilityUnavailable("runner.file_read.outcome_unknown_or_in_progress")
        expected = self.executions.expected_receipt(source, attempt.receipt_data)
        if attempt.receipt_ref is not None and attempt.receipt_ref.wire() != expected.wire():
            raise reject("revision_conflict", "Read receipt digest differs", 409)
        # Also validates actual signature/resource/command before recovering an unpublished
        # candidate. Recovery cannot make a new receipt or alter the original Usage.
        await asyncio.to_thread(self.journal._verify, attempt.receipt_data, source)
        if attempt.receipt_ref is None:
            actual = await self.journal.publish(
                self.command_ref, attempt.receipt_data, authenticated_principal=actor
            )
            if actual.wire() != expected.wire():
                raise reject("revision_conflict", "Published read Ref differs", 409)
            await asyncio.to_thread(self.executions.published, attempt, actual)
        receipt = await self.journal.read(expected, authenticated_principal=actor)
        await asyncio.to_thread(root_access)
        await self.channel_current(actor, owner)
        await self.journal._resolve(self.command_ref, actor, source)
        await asyncio.to_thread(root_access)
        await asyncio.to_thread(self.journal._verify, canonical(receipt.wire()), source)
        return receipt

    async def execute(
        self, command: RunnerCommand, *, authenticated_principal: Principal
    ) -> RunnerReceipt:
        self.available()
        command = RunnerCommand.model_validate_json(canonical(command.wire()))
        actor = Principal.model_validate_json(canonical(authenticated_principal.wire()))
        if command.parameters["action"] != "file.read":
            raise CapabilityUnavailable("runner.file_read.other_actions")
        parameters = command.parameters["parameters"]
        assert isinstance(parameters, dict)
        if "cursor" in parameters:
            raise CapabilityUnavailable("runner.file_read.cursor")
        location = parameters.get("location", {"kind": "whole"})
        if not isinstance(location, dict) or not (
            location == {"kind": "whole"}
            or (
                set(location) == {"kind", "start", "end"}
                and location["kind"] == "text_span"
                and isinstance(location["start"], int)
                and isinstance(location["end"], int)
                and 0 <= location["start"] <= location["end"]
            )
        ):
            raise CapabilityUnavailable("runner.file_read.location")
        source = await self.journal._resolve(self.command_ref, actor)
        if source.command.wire() != command.wire():
            raise reject(
                "revision_conflict", "Input differs from independently registered command", 409
            )
        assert self.executions is not None
        previous = await asyncio.to_thread(self.executions.get, source, self.command_ref)
        if previous is not None:
            return await self.restore(previous, source, actor)
        stopped = Event()
        handle: WindowsReadHandle | None = None
        started = time.perf_counter_ns()
        try:
            first, channel = await self.current(command, actor, source)
            assert self.signer is not None and self.device_key is not None
            await self.signer.check_private(
                device_id=self.protocol.device_id,
                key_id=self.device_key.key_id,
                credential_handle=self.device_key.credential_handle,
            )
            self.admission.deadline(command, first)
            await self.current(command, actor, source, first, channel)
            admitted = await self.protocol.admit_async(
                canonical(command.wire()), authenticated_principal=actor
            )
            self.admission.deadline(command, first)
            if (
                admitted.state != "admitted"
                or admitted.attempt_id != command.trusted_context.attempt_id
            ):
                raise reject(
                    "cancelled",
                    "Original admission is cancelled or belongs to another attempt",
                    409,
                    "cancelled",
                )
            current, _ = await self.current(command, actor, source, first, channel)
            attempt, won = await asyncio.to_thread(
                self.executions.claim,
                source,
                self.command_ref,
                root_handle=current.root_handle,
                root_revision=current.binding_revision,
                check=lambda: self.guard(command, current, stopped),
            )
            if not won:
                return await self.restore(attempt, source, actor)
            self.admission.deadline(command, current)
            result: JsonObject | None = None
            failure: DomainError | None = None

            async def io(operation: Callable[[], T]) -> T:
                # Bound OS work finishes before closing its handles on cancellation.
                task = asyncio.create_task(asyncio.to_thread(operation))
                try:
                    return await asyncio.shield(task)
                except asyncio.CancelledError:
                    stopped.set()
                    try:
                        await asyncio.shield(task)
                    except Exception:
                        pass
                    raise

            def opened() -> None:
                nonlocal handle
                self.guard(command, current, stopped)
                grant = self.protocol.bindings.repository.get(current.root_handle)
                handle = WindowsReadHandle(grant, str(parameters["path"]))
                self.guard(command, current, stopped, handle)

            try:
                await io(opened)
                assert handle is not None
                current, _ = await self.current(command, actor, source, first, channel)

                def read() -> JsonObject:
                    assert handle is not None
                    self.guard(command, current, stopped, handle)
                    content = handle.read(parameters)
                    self.guard(command, current, stopped, handle)
                    return content

                result = await io(read)
            except DomainError as exc:
                if exc.failure.code not in {
                    "file_not_regular",
                    "file_unavailable",
                    "file_identity_invalid",
                    "file_too_large",
                    "file_not_text",
                    "file_read_failed",
                    "read_range_too_large",
                    "unsupported_location",
                }:
                    raise
                failure = exc
            current, _ = await self.current(command, actor, source, first, channel)
            # Failed observed read has no payload; it does not imply not_applied/zero charge.
            draft: JsonObject = {
                "command_id": command.command_id,
                "attempt_id": command.trusted_context.attempt_id,
                "kind": "failed" if failure else "ok",
                "usage": {
                    "attempt_id": command.trusted_context.attempt_id,
                    "billing_state": "pending",
                    "resources": {
                        "currency": self.currency,
                        "wall_time_ms": (time.perf_counter_ns() - started) // 1_000_000,
                    },
                },
                "signature": "pending",
            }
            if failure is not None:
                draft["failure"] = failure.failure.wire()
            else:
                assert result is not None
                draft["payload"] = {"action": "file.read", "result": result}
            assert self.signer is not None and self.device_key is not None
            signature = await self.signer.sign_document(
                draft,
                device_id=self.protocol.device_id,
                key_id=self.device_key.key_id,
                domain="receipt",
                credential_handle=self.device_key.credential_handle,
            )
            draft["signature"] = signature
            current, _ = await self.current(command, actor, source, first, channel)
            data = canonical(draft)
            await asyncio.to_thread(self.journal._verify, data, source)
            # Final authority query follows signing/verification, then local guard in CAS.
            current, _ = await self.current(command, actor, source, first, channel)
            await asyncio.to_thread(
                self.executions.signed,
                attempt,
                data,
                check=lambda: self.guard(
                    command, current, stopped, handle if failure is None else None
                ),
            )
            self.admission.deadline(command, current)
            # Once recorded, a late cancelled publication can only recover this signature.
            actual = await self.journal.publish(
                self.command_ref, data, authenticated_principal=actor
            )
            current, _ = await self.current(command, actor, source, first, channel)
            await asyncio.to_thread(
                self.guard, command, current, stopped, handle if failure is None else None
            )
            await asyncio.to_thread(self.executions.published, attempt, actual)
            self.admission.deadline(command, current)
            return await self.restore(
                ReadAttempt(
                    attempt.id,
                    attempt.binding,
                    attempt.token,
                    attempt.root_handle,
                    attempt.root_revision,
                    data,
                    actual,
                ),
                source,
                actor,
            )
        except asyncio.CancelledError:
            stopped.set()
            raise
        finally:
            if handle is not None:
                await asyncio.to_thread(handle.close)


def command_workspace(command: RunnerCommand) -> Ref:
    parameters = command.parameters["parameters"]
    assert isinstance(parameters, dict) and isinstance(parameters["workspace_ref"], dict)
    return Ref.model_validate_json(canonical(parameters["workspace_ref"]))
