"""Fixed installed first-device assembly; all launch selectors are protected locally.

This module is never chosen by a request/model. It reads no user project or file
command at bootstrap. Native confirmation and current server sources remain gates.
"""

import asyncio
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import SecretStr
from uaw_runner.admissions import PersistentAdmissions
from uaw_runner.bootstrap import BootstrapConsumer
from uaw_runner.helper_host import HelperApplication
from uaw_runner.ipc.channel_source import ConnectionRegistry
from uaw_runner.ipc.windows_pipe import OsIdentity, WindowsApi
from uaw_runner.keys import Ed25519SignatureAdapter, ProtectedSigner
from uaw_runner.native_confirmation import NativeChallenge, RegisteredNativeChallenges
from uaw_runner.pairing import LocalRoots, PersistentRootSelection
from uaw_runner.protocol import RunnerProtocol
from uaw_runner.read_executor import DeviceSigningBinding
from uaw_runner.read_state import ReadExecutionJournal
from uaw_runner.receipts import ReceiptJournal
from uaw_runner.root_source import NativeRootSource, PersistentRootGrants
from uaw_runner.runtime import ReadOnlyHelper
from uaw_runner.state import LocalState

from uaw.composition import Container, assemble_enrollment_sources, compose
from uaw.infrastructure.credentials import WindowsCredentialStore
from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.enrollment_bootstrap import FirstEnrollmentDeviceFactory
from uaw.infrastructure.enrollment_candidates import OwnedEnrollmentCandidates
from uaw.infrastructure.enrollment_native import WindowsEnrollmentConfirmation
from uaw.infrastructure.enrollment_peers import EnrolledPeerRegistry
from uaw.infrastructure.enrollment_pipe import EnrollmentProofClient, decode
from uaw.run.runner_authority import RegisteredRunnerAuthority
from uaw.run.runner_commands import RunnerCommands
from uaw.run.runner_devices import RunnerDevices
from uaw.run.runner_receipts import RegisteredReceiptCommandReader
from uaw.shared.contracts import Principal
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.runner_bootstrap import FirstStartProgressPort
from uaw.shared.schema import validate_contract
from uaw.shared.settings import Settings
from uaw.workspace.binding import RootBindings
from uaw.workspace.ports import ReceiptCommandReaderPort

NAMESPACE_ENV = "UAW_INSTALLED_HELPER_NAMESPACE"
HANDLE_ENV = "UAW_INSTALLED_HELPER_LAUNCH"
MODULE = "uaw.infrastructure.installed_helper"


@dataclass(frozen=True)
class InstalledLaunch:
    """Internal protected selectors, not a public wire DTO or permission grant."""

    owner: Principal
    enrollment_id: str
    challenge_hash: str
    device_id: str
    device_key_id: str
    device_credential_handle: str
    state_directory: Path
    proof_pipe_name: str
    settings_handle: str
    identity: OsIdentity
    expires_at: datetime
    currency: str

    @classmethod
    def from_bytes(cls, raw: bytes) -> InstalledLaunch:
        value = decode(raw)
        expected = {
            "owner",
            "enrollment_id",
            "challenge_hash",
            "device_id",
            "device_key_id",
            "device_credential_handle",
            "state_directory",
            "proof_pipe_name",
            "settings_handle",
            "identity",
            "expires_at",
            "currency",
        }
        if set(value) != expected:
            raise ValueError("Exact installed launch fields required")
        for name in (
            "enrollment_id",
            "device_id",
            "device_key_id",
            "device_credential_handle",
            "settings_handle",
        ):
            validate_contract("ID", value[name])
        validate_contract("Hash", value["challenge_hash"])
        owner = Principal.model_validate(value["owner"])
        if owner.kind != "user" or not owner.auth_session_id.startswith("web-session-"):
            raise ValueError("Current Web owner required")
        directory = Path(value["state_directory"])
        if not directory.is_absolute() or directory.resolve() != directory:
            raise ValueError("Installed absolute state directory required")
        if not isinstance(value["proof_pipe_name"], str) or not value["proof_pipe_name"].startswith(
            "uaw-enroll-"
        ):
            raise ValueError("Original proof pipe required")
        instance = value["identity"]
        if (
            set(instance) != {"pid", "created", "user_sid", "logon_sid"}
            or type(instance["pid"]) is not int
            or instance["pid"] <= 0
            or type(instance["created"]) is not int
            or instance["created"] <= 0
            or any(
                not isinstance(instance[x], str) or not instance[x]
                for x in ("user_sid", "logon_sid")
            )
        ):
            raise ValueError("Exact actual OS instance required")
        expiry = datetime.fromisoformat(value["expires_at"].replace("Z", "+00:00"))
        if expiry.tzinfo is None or expiry.utcoffset() is None:
            raise ValueError("Aware original expiry required")
        currency = value["currency"]
        if (
            not isinstance(currency, str)
            or len(currency) != 3
            or not currency.isascii()
            or not currency.isalpha()
            or not currency.isupper()
        ):
            raise ValueError("Explicit configured accounting currency required")
        return cls(
            owner,
            value["enrollment_id"],
            value["challenge_hash"],
            value["device_id"],
            value["device_key_id"],
            value["device_credential_handle"],
            directory,
            value["proof_pipe_name"],
            value["settings_handle"],
            OsIdentity(**instance),
            expiry,
            currency,
        )


class EnrolledNativeChallenges:
    def __init__(
        self, *, peers: EnrolledPeerRegistry, state: LocalState, registry: ConnectionRegistry
    ) -> None:
        self.peers, self.state, self.registry = peers, state, registry
        self.helper: ReadOnlyHelper | None = None

    async def current(self, ticket_id: str) -> NativeChallenge:
        helper = self.helper
        if helper is None or helper.session is None or helper.session.channel_ref is None:
            raise CapabilityUnavailable("runner.native.current_installed_connection")
        actual = await asyncio.to_thread(WindowsApi().current)
        peer = await self.peers.current(actual, role="device")
        current = await RegisteredNativeChallenges(
            state=self.state,
            registry=self.registry,
            channel_ref=helper.session.channel_ref,
            device_id=peer.device_id,
            mapping=self.peers,
            clock=lambda: datetime.now(UTC),
        ).current(ticket_id)
        if current.owner != peer.owner or current.expires_at > peer.expires_at:
            raise reject("enrollment_root_source_changed", "Current root/enrollment differs", 412)
        await self.peers.current(actual, role="device")
        return current


class InstalledReadOnlyHelper(ReadOnlyHelper):
    """The child owns its DB/model clients as well as the ordinary helper resources."""

    def __init__(
        self,
        *,
        container: Container,
        bootstrap: BootstrapConsumer,
        protocol: RunnerProtocol,
        commands: ReceiptCommandReaderPort,
        journal: ReceiptJournal,
        executions: ReadExecutionJournal,
        roots: NativeRootSource,
        registry: ConnectionRegistry,
        currency: str,
    ) -> None:
        super().__init__(
            bootstrap=bootstrap,
            protocol=protocol,
            commands=commands,
            journal=journal,
            executions=executions,
            roots=roots,
            registry=registry,
            currency=currency,
        )
        self.container = container

    async def close(self) -> None:
        try:
            await super().close()
        finally:
            await self.container.close()


class PairedInstalledFactory:
    def __init__(
        self,
        container: Container,
        launch: InstalledLaunch,
        state: LocalState,
        vault: WindowsCredentialStore,
    ) -> None:
        self.container, self.launch, self.state, self.vault = container, launch, state, vault

    async def create(self, identity: OsIdentity) -> HelperApplication:
        c, launch, state = self.container, self.launch, self.state
        service = c.runner_enrollments
        if (
            not service
            or not c.records
            or not c.configuration
            or not c.execution_permissions
            or not c.budgets
            or not c.execution_leases
        ):
            raise CapabilityUnavailable("runner.installed.current_server_sources")
        peers = EnrolledPeerRegistry(
            service, owner=launch.owner, enrollment_id=launch.enrollment_id, directory=state
        )
        await peers.current(identity, role="device")
        registry = ConnectionRegistry()
        signer = ProtectedSigner(state, self.vault)
        local = LocalRoots(launch.state_directory / "native.sqlite")
        grants = PersistentRootGrants(launch.state_directory / "grants.sqlite")
        roots = NativeRootSource(
            RootBindings(grants, PersistentRootSelection(state, local)),
            grants=grants,
            selections=state,
            native_roots=local,
            mapping=peers,
            directory=state,
        )
        devices = RunnerDevices(c.records, c.configuration.platform, registry)
        commands = RunnerCommands(
            c.records,
            devices,
            c.configuration,
            c.execution_permissions,
            c.budgets,
            c.execution_leases,
            roots=roots,
        )
        reader = RegisteredReceiptCommandReader(commands)
        protocol = RunnerProtocol(
            device_id=launch.device_id,
            bindings=roots.bindings,
            admissions=PersistentAdmissions(launch.state_directory / "admissions.sqlite"),
            signatures=Ed25519SignatureAdapter(state),
            async_authority=RegisteredRunnerAuthority(commands),
            principal_mapping=peers,
        )
        challenges = EnrolledNativeChallenges(peers=peers, state=state, registry=registry)
        bootstrap = BootstrapConsumer(
            registration=peers,
            challenges=challenges,
            mapping=peers,
            directory=state,
            signer=signer,
            device_key=DeviceSigningBinding(
                launch.device_id, launch.device_key_id, launch.device_credential_handle
            ),
        )
        helper = InstalledReadOnlyHelper(
            container=c,
            bootstrap=bootstrap,
            protocol=protocol,
            commands=reader,
            journal=ReceiptJournal(
                launch.state_directory / "receipts.sqlite", protocol=protocol, reader=reader
            ),
            executions=ReadExecutionJournal(launch.state_directory / "reads.sqlite"),
            roots=roots,
            registry=registry,
            currency=launch.currency,
        )
        challenges.helper = helper
        try:
            await bootstrap.local(identity)
        except BaseException:
            await helper.close()
            raise
        return HelperApplication(helper)


class InstalledHelperAssembly:
    def __init__(self) -> None:
        self.used = False

    async def create(self, identity: OsIdentity) -> HelperApplication:
        if self.used:
            raise CapabilityUnavailable("runner.installed.launch_already_consumed")
        self.used = True
        namespace, handle = os.environ.get(NAMESPACE_ENV), os.environ.get(HANDLE_ENV)
        if not namespace or not handle:
            raise CapabilityUnavailable("runner.installed.protected_launch_locator")
        validate_contract("ID", namespace)
        validate_contract("ID", handle)
        vault = WindowsCredentialStore(namespace)
        c = None
        try:
            launch = InstalledLaunch.from_bytes(
                (await vault.resolve(handle)).get_secret_value().encode("utf-8")
            )
            if (
                identity != launch.identity
                or await asyncio.to_thread(WindowsApi().current) != identity
                or datetime.now(UTC) >= launch.expires_at
            ):
                raise reject(
                    "enrollment_installed_instance_denied",
                    "Original launch instance/expiry differs",
                    403,
                )
            # These settings are protected credentials, not plaintext config or request fields.
            settings_value = decode(
                (await vault.resolve(launch.settings_handle)).get_secret_value().encode("utf-8")
            )
            for name in (
                "database_url",
                "development_user_token",
                "cursor_signing_key",
                "browser_session_signing_key",
            ):
                if name in settings_value:
                    settings_value[name] = SecretStr(settings_value[name])
            settings_value["blob_directory"] = launch.state_directory / "blobs"
            settings = Settings.model_validate(settings_value)
            if (
                settings.platform_id != namespace
                or settings.development_principal_id != launch.owner.id
                or settings.agent_execution_enabled
            ):
                raise reject(
                    "enrollment_installed_settings_denied",
                    "Original installed settings differ",
                    403,
                )
            c = compose(settings)
            state = await asyncio.to_thread(LocalState, launch.state_directory / "roles.sqlite")
            assemble_enrollment_sources(c, directory=state)
            assert c.runner_enrollments is not None
            document = await c.runner_enrollments.challenge(launch.owner, launch.enrollment_id)
            if (
                parameter_hash(document) != launch.challenge_hash
                or document["device_id"] != launch.device_id
                or document["device"]["key_id"] != launch.device_key_id
                or document["device"]["identity"] != OwnedEnrollmentCandidates.identity(identity)
                or c.runner_enrollments.instant(document["expires_at"]) != launch.expires_at
            ):
                raise reject(
                    "enrollment_installed_source_changed", "Original protected source differs", 412
                )
            signer = ProtectedSigner(state, vault)
            native = WindowsEnrollmentConfirmation(
                c.runner_enrollments,
                state,
                signer,
                device_credential_handle=launch.device_credential_handle,
            )
            # D's new emitter is a milestone dependency, never silently replace it.
            from uaw_runner import helper_host

            progress_type = getattr(helper_host, "HelperBootstrapProgress", None)
            if progress_type is None:
                raise CapabilityUnavailable("runner.installed.first_start_progress")
            progress: FirstStartProgressPort = progress_type()
            application = await FirstEnrollmentDeviceFactory(
                c.runner_enrollments,
                owner=launch.owner,
                enrollment_id=launch.enrollment_id,
                native=native,
                proofs=EnrollmentProofClient(
                    c.runner_enrollments,
                    state,
                    owner=launch.owner,
                    enrollment_id=launch.enrollment_id,
                    pipe_name=launch.proof_pipe_name,
                ),
                paired_factory=PairedInstalledFactory(c, launch, state, vault),
                progress=progress,
            ).create(identity)
            return application
        except BaseException:
            if c is not None:
                await c.close()
            raise


assembly = InstalledHelperAssembly()
