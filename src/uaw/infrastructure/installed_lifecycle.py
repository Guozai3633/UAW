"""One browser-owned installed launch. Persisted progress is never a permission source."""

import asyncio
import json
import os
import re
import sys
import sysconfig
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import uaw_runner

from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch
from uaw.infrastructure.installed_receipt import current_root
from uaw.shared.contracts import Principal, Ref, RequestMeta
from uaw.shared.errors import CapabilityUnavailable, DomainError, reject
from uaw.shared.stores import StoreMissing

if TYPE_CHECKING:
    from uaw.composition import Container

NAMESPACE = "runner.installed.launches"
TERMINAL = frozenset({"closed", "failed", "unavailable"})
Payload = dict[str, Any]


def detached(value: Payload) -> Payload:
    return json.loads(json.dumps(value, allow_nan=False))  # type: ignore[no-any-return]


def installed_environment() -> dict[str, str]:
    # Fixed installed code/libraries; model/admin credentials and arbitrary import
    # selectors from the parent's environment are not forwarded to this process.
    allowed = {
        "SystemRoot",
        "WINDIR",
        "TEMP",
        "TMP",
        "LOCALAPPDATA",
        "APPDATA",
        "USERPROFILE",
        "PATH",
        "PATHEXT",
        "COMSPEC",
        "ProgramData",
    }
    environment = {
        k: v for k, v in os.environ.items() if k.casefold() in {key.casefold() for key in allowed}
    }
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONPATH"] = os.pathsep.join(
        str(p)
        for p in (
            Path(__file__).resolve().parents[2],
            Path(uaw_runner.__file__).resolve().parent.parent,
            Path(sysconfig.get_path("purelib")),
        )
    )
    return environment


@dataclass
class OwnedLaunch:
    id: str
    owner: Principal
    launch: PreparedEnrollmentLaunch | None = None
    task: asyncio.Task[None] | None = None
    stopping: bool = False
    running: bool = False
    cleaning: bool = False
    done: asyncio.Event = field(default_factory=asyncio.Event)
    cleanup_failed: bool = False
    persistence_failed: bool = False
    stop_code: str | None = None


class InstalledLifecycle:
    def __init__(self, container: Container) -> None:
        if not container.records or not container.configuration or not container.browser_sessions:
            raise CapabilityUnavailable("runner.installed.current_web_sources")
        self.container = container
        self.records, self.controller, self.browser = (
            container.records,
            container.configuration.platform,
            container.browser_sessions,
        )
        self.active: OwnedLaunch | None = None
        self.lock = asyncio.Lock()
        self.closed = False

    async def actor(self, owner: Principal) -> None:
        if owner.kind != "user" or not owner.auth_session_id.startswith("web-session-"):
            raise reject("installed_web_required", "Current browser session required", 403)
        await self.browser.principal(owner)

    async def record(self, owner: Principal, identifier: str) -> Payload:
        row = await self.records.get(self.controller, NAMESPACE, identifier)
        if row.payload["owner"] != owner.wire():
            raise reject("installed_owner_denied", "Original browser session required", 403)
        return detached(row.payload["view"])

    async def update(
        self, entry: OwnedLaunch, *, if_active: bool = False, **changes: Any
    ) -> Payload:
        async with self.lock:
            old = await self.record(entry.owner, entry.id)
            if if_active and old["state"] in TERMINAL:
                return old
            value = {
                **old,
                **changes,
                "revision": old["revision"] + 1,
                "updated_at": datetime.now(UTC).isoformat(),
            }
            await self.records.put(
                self.controller,
                NAMESPACE,
                entry.id,
                "InstalledLaunchRecord",
                {"owner": entry.owner.wire(), "view": value},
                expected_revision=old["revision"],
                request_id="stage-" + str(value["revision"]),
            )
            return value

    async def begin(self, owner: Principal, meta: RequestMeta) -> Payload:
        await self.actor(owner)
        settings = self.container.settings
        if (
            self.closed
            or settings.installed_state_directory is None
            or not settings.installed_workspace_id
        ):
            raise CapabilityUnavailable("runner.installed.deployment_configuration")
        if meta.expected_revision not in (None, 0):
            raise reject("installed_begin_revision", "New launch revision must be zero", 409)
        identifier = "installed-" + parameter_hash(
            {"owner": owner.wire(), "request": meta.request_id}
        )
        async with self.lock:
            try:
                previous = await self.record(owner, identifier)
            except StoreMissing:
                previous = None
            if previous is not None:
                # Unknown HTTP result or process restart never creates another native instance.
                return previous
            if self.active is not None and not self.active.done.is_set():
                raise reject("installed_launch_busy", "One installed launch is still owned", 409)
            await self.actor(owner)
            now = datetime.now(UTC).isoformat()
            view: Payload = {
                "id": identifier,
                "request_id": meta.request_id,
                "revision": 1,
                "state": "starting",
                "created_at": now,
                "updated_at": now,
                "workspace_ref": Ref(
                    kind="workspace", id=settings.installed_workspace_id, version="1"
                ).wire(),
            }
            await self.records.put(
                self.controller,
                NAMESPACE,
                identifier,
                "InstalledLaunchRecord",
                {"owner": owner.wire(), "view": view},
                expected_revision=0,
                request_id="begin",
            )
            entry = OwnedLaunch(identifier, Principal.model_validate(owner.wire()))
            self.active = entry
            entry.task = asyncio.create_task(self.run(entry))
            return detached(view)

    async def get(self, owner: Principal, identifier: str) -> Payload:
        await self.actor(owner)
        view = await self.record(owner, identifier)
        entry = self.active
        if view["state"] not in TERMINAL:
            if entry is None or entry.id != identifier or entry.done.is_set():
                # Persistent history cannot resurrect a missing in-memory OS process.
                temporary = OwnedLaunch(identifier, owner)
                view = await self.update(
                    temporary,
                    if_active=True,
                    state="unavailable",
                    failure_code="installed_instance_lost",
                )
            elif view["state"] == "ready":
                try:
                    assert entry.launch is not None
                    await current_root(entry.launch)
                except DomainError as exc:
                    await self.stop_entry(entry, code=exc.failure.code)
                    view = await self.record(owner, identifier)
        await self.actor(owner)
        return view

    async def close_owner(self, owner: Principal) -> None:
        # Used after Web logout too: it may only close this process's exact owned instance.
        entry = self.active
        if entry is not None and entry.owner == owner:
            await self.stop_entry(entry)

    async def owned_source(self, owner: Principal, workspace: Ref) -> PreparedEnrollmentLaunch:
        """Actual original instance only. Consumers still require current native proof."""
        entry = self.active
        if entry is None or entry.owner != owner:
            raise CapabilityUnavailable("file.current_browser_owned_launch")
        view = await self.record(owner, entry.id)
        await self.actor(owner)
        if (
            self.active is not entry
            or entry.stopping
            or entry.done.is_set()
            or entry.launch is None
            or view["state"] != "ready"
            or view["workspace_ref"] != workspace.wire()
            or entry.launch.root_workspace != workspace
        ):
            raise CapabilityUnavailable("file.current_browser_owned_root")
        return entry.launch

    async def owned_ready(self, owner: Principal, workspace: Ref) -> PreparedEnrollmentLaunch:
        launch = await self.owned_source(owner, workspace)
        await current_root(launch)
        if await self.owned_source(owner, workspace) is not launch:
            raise reject("installed_original_source_changed", "Original instance changed", 412)
        return launch

    async def stop(self, owner: Principal, identifier: str, meta: RequestMeta) -> Payload:
        await self.actor(owner)
        view = await self.record(owner, identifier)
        if meta.expected_revision is not None and meta.expected_revision != view["revision"]:
            raise reject("installed_revision_changed", "Observed launch revision changed", 409)
        entry = self.active
        if entry is not None and entry.id == identifier:
            await self.stop_entry(entry)
        return await self.get(owner, identifier)

    async def stop_entry(self, entry: OwnedLaunch, *, code: str | None = None) -> None:
        if entry.task is not None and not entry.task.done():
            first_stop = not entry.stopping
            entry.stopping = True
            if first_stop:
                entry.stop_code = code
            if first_stop and entry.running and not entry.cleaning:
                entry.task.cancel()
            # run's finally drains PreparedEnrollmentLaunch's own native/process/key cleanup.
            try:
                await asyncio.shield(entry.task)
            except asyncio.CancelledError:
                await entry.task
                raise
        if not entry.done.is_set():
            raise CapabilityUnavailable("runner.installed.cleanup_incomplete")
        if entry.cleanup_failed or entry.persistence_failed:
            raise CapabilityUnavailable("runner.installed.cleanup_or_receipt_incomplete")

    async def run(self, entry: OwnedLaunch) -> None:
        entry.running = True
        outcome, code = "closed", None
        lifecycle: asyncio.Task[None] | None = None
        try:
            if entry.stopping:
                raise asyncio.CancelledError
            settings = self.container.settings
            assert (
                settings.installed_state_directory is not None and settings.installed_workspace_id
            )
            await self.actor(entry.owner)
            entry.launch = await PreparedEnrollmentLaunch.prepare(
                self.container,
                owner=entry.owner,
                python=await asyncio.to_thread(
                    Path(getattr(sys, "_base_executable", sys.executable)).resolve
                ),
                state_directory=settings.installed_state_directory,
                currency="USD",
                environment=await asyncio.to_thread(installed_environment),
                root_workspace=Ref(
                    kind="workspace", id=settings.installed_workspace_id, version="1"
                ),
            )
            await self.update(
                entry, state="waiting_device", enrollment_id=entry.launch.enrollment_id
            )
            await entry.launch.start()
            await self.update(entry, state="connecting")
            await entry.launch.connect()
            connection = entry.launch.connection
            assert connection is not None and connection.session is not None
            await self.update(
                entry,
                state="selecting_directory",
                expires_at=connection.session.expires_at.isoformat(),
            )
            # One original deadline, no extension from polling, UI or progress.
            remaining = (connection.session.expires_at - datetime.now(UTC)).total_seconds()
            assert entry.launch.helper is not None

            async def child_failure() -> None:
                assert entry.launch is not None and entry.launch.helper is not None
                receipt_seen = False
                deadline = asyncio.get_running_loop().time() + max(0.0, remaining)
                while True:
                    frame = await entry.launch.helper.event(deadline=deadline)
                    child_code = frame.get("code")
                    if (
                        set(frame) == {"event", "code"}
                        and frame["event"] == "failure"
                        and isinstance(child_code, str)
                        and re.fullmatch(r"[a-z][a-z0-9_]{0,127}", child_code)
                    ):
                        raise reject(child_code, "Installed child stopped", 503, "dependency")
                    if (
                        set(frame) == {"event", "receipt_ref"}
                        and frame["event"] == "receipt"
                        and not receipt_seen
                    ):
                        pin = Ref.model_validate(frame["receipt_ref"])
                        if (
                            pin.kind != "content"
                            or pin.content_hash is None
                            or pin.location is not None
                            or pin.access_scope is not None
                        ):
                            raise reject(
                                "dependency_protocol_invalid", "Unexpected receipt progress", 503
                            )
                        # Progress is not receipt evidence, permission or task completion.
                        # The owning Tool Reader verifies actual signed journal bytes.
                        receipt_seen = True
                        continue
                    raise reject(
                        "dependency_protocol_invalid", "Unexpected installed lifecycle", 503
                    )

            lifecycle = asyncio.create_task(child_failure())
            async with asyncio.timeout(max(0.0, remaining)):
                while True:
                    if lifecycle.done():
                        await lifecycle
                    await self.actor(entry.owner)
                    try:
                        grant = await current_root(entry.launch)
                        break
                    except DomainError as exc:
                        if exc.failure.code != "installed_callback_pending":
                            raise
                        await asyncio.sleep(0.2)
                binding = await connection.devices.current(
                    grant.device_id, authenticated_principal=entry.owner
                )
                await self.actor(entry.owner)
                await self.update(
                    entry,
                    state="ready",
                    device_ref={
                        "kind": "device",
                        "id": grant.device_id,
                        "version": str(binding["revision"]),
                        "content_hash": parameter_hash(binding),
                    },
                )
            # Root existence alone is not permission. All consumers call the owning
            # RootSource/Tool/Run gates again; this timer owns cleanup of this launch.
            await asyncio.sleep(
                max(0.0, (connection.session.expires_at - datetime.now(UTC)).total_seconds())
            )
            outcome, code = "unavailable", "installed_connection_expired"
        except asyncio.CancelledError:
            if entry.stop_code is not None:
                outcome, code = "failed", entry.stop_code
            elif not entry.stopping:
                outcome, code = "failed", "installed_cancelled"
        except DomainError as exc:
            outcome, code = "failed", exc.failure.code
        except TimeoutError:
            outcome, code = "failed", "installed_deadline_exceeded"
        except Exception:
            outcome, code = "failed", "installed_internal_error"
        finally:
            # Source failure may already be draining its own launch. A later
            # stop must await that cleanup rather than cancelling it again.
            entry.cleaning = True
            entry.running = False
            try:
                if entry.launch is not None:
                    await entry.launch.close()
            except asyncio.CancelledError:
                entry.cleanup_failed = True
                outcome, code = "failed", "installed_cleanup_cancelled"
            except Exception:
                entry.cleanup_failed = True
                outcome, code = "failed", "installed_cleanup_incomplete"
            try:
                changes: Payload = {"state": outcome}
                if code is not None:
                    changes["failure_code"] = code
                await self.update(entry, **changes)
            except Exception:
                # Avoid a detached task traceback with protected SQL/configuration.
                # Ended processes are unavailable on read, never resurrected as ready.
                entry.persistence_failed = True
            finally:
                if lifecycle is not None:
                    lifecycle.cancel()
                    await asyncio.gather(lifecycle, return_exceptions=True)
                entry.done.set()

    async def close(self) -> None:
        self.closed = True
        if self.active is not None:
            await self.stop_entry(self.active)
