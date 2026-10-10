"""A-owned per-launch protected delivery to the fixed installed device module.

Only trusted local composition calls prepare. There is no model/HTTP launch body,
shell/module selection, native approval boolean or user directory argument.
"""

import asyncio
import base64
import inspect
import json
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any, Literal, Protocol, cast
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import SecretStr
from uaw_runner.helper_process import HelperProcess
from uaw_runner.ipc.sessions import IpcSigningBinding
from uaw_runner.state import LocalState

from uaw.composition import Container, assemble_enrollment_sources
from uaw.infrastructure.credentials import WindowsCredentialStore
from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.enrollment_candidates import OwnedEnrollmentCandidates
from uaw.infrastructure.enrollment_control import WindowsEnrollmentControlProof
from uaw.infrastructure.enrollment_pipe import EnrollmentProofServer
from uaw.infrastructure.installed_control import InstalledControlConnection
from uaw.infrastructure.installed_helper import HANDLE_ENV, MODULE, NAMESPACE_ENV, InstalledLaunch
from uaw.infrastructure.installed_roots import workspace_pin
from uaw.shared.contracts import Principal, Ref, RequestMeta
from uaw.shared.errors import CapabilityUnavailable
from uaw.shared.runner_bootstrap import FirstStartPolicy, FirstStartProgressPort
from uaw.shared.runner_signatures import VerificationKey
from uaw.shared.schema import validate_contract


class FirstHelperStart(Protocol):
    async def start(
        self,
        *,
        first_start: FirstStartPolicy | None = None,
        on_progress: FirstStartProgressPort | None = None,
    ) -> dict[str, Any]: ...


class PreparedEnrollmentLaunch:
    def __init__(
        self, container: Container, vault: WindowsCredentialStore, state: LocalState
    ) -> None:
        self.container, self.vault, self.state = container, vault, state
        self.helper: HelperProcess | None = None
        self.proof: EnrollmentProofServer | None = None
        self.handles: list[str] = []
        self.keys: list[VerificationKey] = []
        self.enrollment_id: str | None = None
        self.candidate_id: str | None = None
        self.policy: FirstStartPolicy | None = None
        self.closed = False
        self.closing: asyncio.Task[None] | None = None
        self.candidates: OwnedEnrollmentCandidates | None = None
        self.owner: Principal | None = None
        self.control_key: IpcSigningBinding | None = None
        self.ready: dict[str, Any] | None = None
        self.connection: InstalledControlConnection | None = None
        self.connecting: asyncio.Task[Any] | None = None
        self.previous_native = (
            container.runner_enrollments.native if container.runner_enrollments else None
        )

    @classmethod
    async def prepare(
        cls,
        container: Container,
        *,
        owner: Principal,
        python: Path,
        state_directory: Path,
        currency: str,
        environment: Mapping[str, str],
        root_workspace: Ref | None = None,
    ) -> PreparedEnrollmentLaunch:
        service = container.runner_enrollments
        if service is None:
            raise CapabilityUnavailable("enrollment.installed.current_server_sources")
        async with service.local_launch_lock:
            if service.candidates is not None:
                raise CapabilityUnavailable("enrollment.installed.current_launch_busy")
            return await cls._prepare(
                container,
                owner=owner,
                python=python,
                state_directory=state_directory,
                currency=currency,
                environment=environment,
                root_workspace=root_workspace,
            )

    @classmethod
    async def _prepare(
        cls,
        container: Container,
        *,
        owner: Principal,
        python: Path,
        state_directory: Path,
        currency: str,
        environment: Mapping[str, str],
        root_workspace: Ref | None,
    ) -> PreparedEnrollmentLaunch:
        service = container.runner_enrollments
        if service is None or container.settings.database_url is None:
            raise CapabilityUnavailable("enrollment.installed.current_server_sources")
        # No OS allocation or credential provisioning before actual current Web auth.
        await service.actor(owner)
        workspace = workspace_pin(root_workspace) if root_workspace is not None else None
        validate_contract("ID", container.settings.platform_id)
        if (
            not isinstance(currency, str)
            or len(currency) != 3
            or not currency.isascii()
            or not currency.isalpha()
            or not currency.isupper()
        ):
            raise ValueError("Explicit configured accounting currency required")
        base = await asyncio.to_thread(state_directory.resolve)
        if not state_directory.is_absolute() or base != state_directory:
            raise ValueError("Explicit installed state directory required")
        # New isolated local state per launch; persisted journals are not deleted.
        directory = base / ("launch-" + uuid4().hex)
        state = await asyncio.to_thread(LocalState, directory / "roles.sqlite")
        launch = cls(container, WindowsCredentialStore(container.settings.platform_id), state)
        try:
            candidates = assemble_enrollment_sources(container, directory=state)
            launch.candidates = candidates
            device_id = "device-" + uuid4().hex
            bindings = {}
            roles: tuple[Literal["control", "device"], ...] = ("control", "device")
            for role in roles:
                private = Ed25519PrivateKey.generate()
                key_id, handle = role + "-key-" + uuid4().hex, role + "-private-" + uuid4().hex
                # Track before await: a cancelled OS write may complete late.
                launch.handles.append(handle)
                writing = asyncio.create_task(
                    launch.vault.put(
                        handle, SecretStr(base64.b64encode(private.private_bytes_raw()).decode())
                    )
                )
                try:
                    await asyncio.shield(writing)
                except asyncio.CancelledError:
                    await writing
                    raise
                key = VerificationKey(
                    key_id, device_id, private.public_key().public_bytes_raw(), role
                )
                registering = asyncio.create_task(asyncio.to_thread(state.register_key, key))
                try:
                    await asyncio.shield(registering)
                except asyncio.CancelledError:
                    await registering
                    launch.keys.append(key)
                    raise
                launch.keys.append(key)
                bindings[role] = (key_id, handle)
            selector, settings_handle = "launch-" + uuid4().hex, "launch-settings-" + uuid4().hex
            child_env = dict(environment)
            child_env[NAMESPACE_ENV], child_env[HANDLE_ENV] = (
                container.settings.platform_id,
                selector,
            )
            launch.helper = await HelperProcess.prepare(
                python=python, assembly_module=MODULE, environment=child_env
            )
            candidate = await candidates.capture(
                owner,
                launch.helper,
                device_id=device_id,
                control_actor=Principal(
                    id="control-" + device_id,
                    kind="runner",
                    auth_session_id="control-" + uuid4().hex,
                ),
                device_actor=Principal(
                    id="actor-" + device_id, kind="runner", auth_session_id="device-" + uuid4().hex
                ),
                control_key_id=bindings["control"][0],
                device_key_id=bindings["device"][0],
            )
            launch.candidate_id = candidate["id"]
            launch.owner = Principal.model_validate(owner.wire())
            launch.control_key = IpcSigningBinding(
                device_id, bindings["control"][0], "control", bindings["control"][1]
            )
            record = await service.begin(
                owner,
                candidate["id"],
                RequestMeta(request_id="first-launch-" + uuid4().hex, schema_version="0.1"),
            )
            launch.enrollment_id = record["id"]
            document = record["proof_document"]
            launch.proof = EnrollmentProofServer(
                WindowsEnrollmentControlProof(
                    service, state, launch.vault, control_credential_handle=bindings["control"][1]
                ),
                owner=owner,
                enrollment_id=record["id"],
            )
            name = await launch.proof.prepare()
            launch.policy = FirstStartPolicy(
                expires_at=service.instant(document["expires_at"]),
                challenge_hash=parameter_hash(document),
            )
            # Omit CLI admin credentials, model credentials, worker flags and user data.
            settings = container.settings
            private_settings: dict[str, Any] = {
                "profile": "development",
                "platform_id": settings.platform_id,
                "development_principal_id": settings.development_principal_id,
                "development_admin_id": settings.development_admin_id,
                "browser_origin": settings.browser_origin,
                "host": settings.host,
            }
            for field in (
                "database_url",
                "development_user_token",
                "cursor_signing_key",
                "browser_session_signing_key",
            ):
                secret = getattr(settings, field)
                if not isinstance(secret, SecretStr):
                    raise CapabilityUnavailable("enrollment.installed.protected_settings")
                private_settings[field] = secret.get_secret_value()
            delivery = {
                "owner": owner.wire(),
                "enrollment_id": record["id"],
                "challenge_hash": launch.policy.challenge_hash,
                "device_id": device_id,
                "device_key_id": bindings["device"][0],
                "device_credential_handle": bindings["device"][1],
                "state_directory": str(directory),
                "proof_pipe_name": name,
                "settings_handle": settings_handle,
                "identity": asdict(launch.helper.identity),
                "expires_at": document["expires_at"],
                "currency": currency,
            }
            if workspace is not None:
                delivery["root_workspace"] = workspace.wire()
            InstalledLaunch.from_bytes(json.dumps(delivery).encode())
            for handle, value in ((settings_handle, private_settings), (selector, delivery)):
                raw = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
                if len(raw.encode("utf-8")) > 4096 or len(raw.encode("utf-16-le")) > 4800:
                    raise CapabilityUnavailable("enrollment.installed.bounded_credential_delivery")
                launch.handles.append(handle)
                writing = asyncio.create_task(launch.vault.put(handle, SecretStr(raw)))
                try:
                    await asyncio.shield(writing)
                except asyncio.CancelledError:
                    await writing
                    raise
            # After awaited OS delivery, current user/challenge/keys/process must still match.
            if await service.challenge(owner, record["id"]) != document:
                raise CapabilityUnavailable("enrollment.installed.current_launch_changed")
            return launch
        except BaseException:
            await launch.close()
            raise

    async def start(self, *, on_progress: FirstStartProgressPort | None = None) -> dict[str, Any]:
        helper, proof, policy = self.helper, self.proof, self.policy
        if self.closed or helper is None or proof is None or policy is None:
            raise CapabilityUnavailable("enrollment.installed.prepared_launch")
        # D's stage is a real dependency, not a fallback to the old 15-second start.
        parameters = inspect.signature(helper.start).parameters
        if not {"first_start", "on_progress"} <= set(parameters):
            raise CapabilityUnavailable("enrollment.installed.first_start_adapter")
        work = asyncio.create_task(proof.serve_once())
        try:
            value = await cast(FirstHelperStart, helper).start(
                first_start=policy, on_progress=on_progress
            )
            await work
            self.ready = json.loads(json.dumps(value, allow_nan=False))
            return value
        except BaseException:
            await self.close()
            raise
        finally:
            if not work.done():
                work.cancel()
            await asyncio.gather(work, return_exceptions=True)

    async def connect(self) -> Ref:
        if (
            self.closed
            or self.ready is None
            or self.owner is None
            or self.control_key is None
            or self.enrollment_id is None
            or self.helper is None
            or self.connection is not None
        ):
            raise CapabilityUnavailable("enrollment.installed.original_ready_connection")
        # Set ownership before awaited connection allocation; no address/body argument.
        self.connection = InstalledControlConnection(
            container=self.container,
            owner=self.owner,
            enrollment_id=self.enrollment_id,
            directory=self.state,
            credentials=self.vault,
            control_key=self.control_key,
        )
        self.connecting = asyncio.current_task()
        try:
            return await self.connection.connect(self.helper, self.ready)
        except BaseException:
            if self.closing is None:
                self.connecting = None
                await self.close()
            raise
        finally:
            self.connecting = None

    async def close(self) -> None:
        if self.closing is None:
            self.closed = True
            self.closing = asyncio.create_task(self._close())
        try:
            await asyncio.shield(self.closing)
        except asyncio.CancelledError:
            await self.closing
            raise

    async def _close(self) -> None:
        failures = []
        task = self.connecting
        if task is not None and task is not asyncio.current_task() and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        if self.connection is not None:
            try:
                await self.connection.close()
            except Exception as exc:
                failures.append(exc)
        for resource in (self.helper, self.proof):
            if resource is not None:
                try:
                    await resource.close()
                except Exception as exc:
                    failures.append(exc)
        for key in self.keys:
            try:
                if not (
                    await asyncio.to_thread(self.state.lookup, key.key_id, device_id=key.device_id)
                ).revoked:
                    await asyncio.to_thread(self.state.revoke_key, key.key_id, expected_revision=0)
            except Exception as exc:
                failures.append(exc)
        for handle in reversed(self.handles):
            try:
                await self.vault.delete(handle)
            except Exception as exc:
                # Not-yet-created handles after a failed OS write are not secrets to retain.
                try:
                    await self.vault.resolve(handle)
                except Exception as missing:
                    if (
                        getattr(getattr(missing, "failure", None), "code", None)
                        == "credential_missing"
                    ):
                        continue
                failures.append(exc)
        if failures:
            raise CapabilityUnavailable("enrollment.installed.cleanup_incomplete")
        service = self.container.runner_enrollments
        if service is not None and service.candidates is self.candidates:
            service.candidates = None
            service.native = self.previous_native
