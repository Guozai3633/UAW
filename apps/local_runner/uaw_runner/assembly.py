"""Explicit local adapter assembly, never runtime/API activation or native approval."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from uaw.shared.contracts import Principal
from uaw.shared.credentials import CredentialStorePort
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.ports import AsyncRunnerAuthorityPort
from uaw.shared.schema import validate_contract
from uaw.workspace.binding import RootBindings
from uaw.workspace.ports import (
    AdmissionRepository,
    CurrentKeyDirectory,
    ReceiptCommandReaderPort,
    RootGrantLookup,
    RunnerPrincipalMappingPort,
)
from uaw_runner.control_signing import ControlCommandSigner, ControlKeyBinding
from uaw_runner.keys import Ed25519SignatureAdapter, ProtectedSigner
from uaw_runner.pairing import LocalRoots, PersistentRootSelection
from uaw_runner.protocol import RunnerProtocol
from uaw_runner.receipts import ReceiptJournal
from uaw_runner.root_source import NativeRootSource
from uaw_runner.state import LocalState


class DeviceOwnerReader(Protocol):
    async def owner(self, actor: Principal, device_id: str) -> Principal:
        """Actual registered devices/channel service, e.g. Container.runner_devices."""
        ...


class RegisteredPrincipalMapping:
    def __init__(self, devices: DeviceOwnerReader | None) -> None:
        self.devices = devices

    async def owner(self, *, authenticated_principal: Principal, device_id: str) -> Principal:
        if self.devices is None:
            raise CapabilityUnavailable("runner.registered_device_owner")
        validate_contract("Principal", authenticated_principal.wire())
        validate_contract("ID", device_id)
        result = await self.devices.owner(authenticated_principal, device_id)
        if not isinstance(result, Principal):
            raise reject("dependency_protocol_invalid", "Registered owner source is invalid", 503)
        validate_contract("Principal", result.wire())
        return Principal.model_validate_json(
            json.dumps(result.wire())
        )  # Never command.trusted_context.principal or incoming owner assertions.


@dataclass(frozen=True)
class RunnerAdapters:
    control_signing: ControlCommandSigner
    roots: NativeRootSource
    bindings: RootBindings
    protocol: RunnerProtocol
    journal: ReceiptJournal


def assemble_runner_adapters(
    *,
    device_id: str,
    control_bindings: tuple[ControlKeyBinding, ...],
    directory: CurrentKeyDirectory,
    credentials: CredentialStorePort | None,
    grants: RootGrantLookup,
    admissions: AdmissionRepository,
    selections: LocalState | None,
    native_roots: LocalRoots | None,
    mapping: RunnerPrincipalMappingPort | None,
    authority: AsyncRunnerAuthorityPort | None,
    receipt_commands: ReceiptCommandReaderPort | None,
    journal_path: Path,
    clock: Callable[[], datetime] | None = None,
) -> RunnerAdapters:
    validate_contract("ID", device_id)
    selection_port = (
        PersistentRootSelection(selections, native_roots, directory=directory)
        if selections is not None and native_roots is not None
        else None
    )
    bindings = RootBindings(grants, selection_port)
    roots = NativeRootSource(
        bindings,
        grants=grants,
        selections=selections,
        native_roots=native_roots,
        mapping=mapping,
        directory=directory,
        clock=clock,
    )
    signing = ControlCommandSigner(
        control_bindings,
        directory=directory,
        signer=ProtectedSigner(directory, credentials),
        clock=clock,
    )
    protocol = RunnerProtocol(
        device_id=device_id,
        bindings=bindings,
        admissions=admissions,
        signatures=Ed25519SignatureAdapter(directory),
        async_authority=authority,
        principal_mapping=mapping,
        clock=clock,
    )
    journal = ReceiptJournal(journal_path, protocol=protocol, reader=receipt_commands)
    return RunnerAdapters(signing, roots, bindings, protocol, journal)
