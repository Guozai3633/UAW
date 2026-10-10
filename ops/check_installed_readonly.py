"""Human-run Windows installed onboarding check; never reads project file contents.

Trusted deployment settings only. Optional workspace selector opens native UI;
there is no path/approval input or flag override. Own instance is closed afterwards.
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from starlette.requests import Request
from uaw_runner.keys import Ed25519SignatureAdapter
from uaw_runner.native_authorization import NativeDecisionJournal
from uaw_runner.pairing import LocalRoots
from uaw_runner.root_source import PersistentRootGrants

from uaw.api.authentication import authenticate
from uaw.composition import compose
from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch
from uaw.infrastructure.enrollment_native import JOURNAL
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.shared.contracts import Principal, Ref, RequestMeta
from uaw.shared.errors import DomainError, reject
from uaw.shared.settings import Settings


async def check(settings_path: Path, state_directory: Path, workspace: Ref | None) -> dict:
    settings = Settings.from_file(settings_path).model_copy(
        update={"agent_execution_enabled": False}
    )
    c = compose(settings)
    result = {"status": "preparing", "file_reads": 0, "model_calls": 0, "root_selected": False}
    launch, owner = None, None
    try:
        await c.start()
        if (
            not c.browser_sessions
            or not c.runner_enrollments
            or not settings.development_user_token
        ):
            raise reject("installed_sources_missing", "Actual Web/current user required", 503)
        actor = authenticate(
            Request(
                {
                    "type": "http",
                    "headers": [
                        (
                            b"authorization",
                            (
                                "Bearer " + settings.development_user_token.get_secret_value()
                            ).encode(),
                        )
                    ],
                }
            ),
            settings,
        )
        ticket = await c.browser_sessions.launch(
            actor, RequestMeta(request_id="installed-check-" + uuid4().hex, schema_version="0.1")
        )
        web, _ = await c.browser_sessions.exchange(ticket["launch_url"].split("#uaw_launch=", 1)[1])
        owner = Principal.model_validate(web["principal"])
        environment = os.environ.copy()
        root = (await asyncio.to_thread(Path(__file__).resolve)).parents[1]
        environment["PYTHONIOENCODING"] = "utf-8"
        environment["PYTHONPATH"] = os.pathsep.join(
            str(p)
            for p in (
                root / "src",
                root / "apps/local_runner",
                Path(sys.prefix) / "Lib/site-packages",
            )
        )
        launch = await PreparedEnrollmentLaunch.prepare(
            c,
            owner=owner,
            python=await asyncio.to_thread(Path(sys._base_executable).resolve),
            state_directory=state_directory,
            currency="USD",
            environment=environment,
            root_workspace=workspace,
        )
        print(json.dumps({"status": "waiting_native_device_confirmation"}), flush=True)
        await launch.start()
        record = await c.runner_enrollments.get(owner, launch.enrollment_id)
        decision = await c.records.get(c.configuration.platform, JOURNAL, launch.enrollment_id)
        result.update(
            native_human_confirmed=record["state"] == "active",
            native_journal_hash=parameter_hash(decision.payload),
        )
        channel = await launch.connect()
        result.update(status="connected", channel_hash=channel.content_hash)
        connection = launch.connection
        assert (
            connection
            and connection.session
            and connection.session.local
            and connection.session.peer
        )
        if workspace is not None:
            print(
                json.dumps(
                    {"status": "waiting_native_directory_selection", "scope": "bounded_read_only"}
                ),
                flush=True,
            )
            directory = launch.state.path.parent
            grants = await asyncio.to_thread(PersistentRootGrants, directory / "grants.sqlite")
            local = await asyncio.to_thread(LocalRoots, directory / "native.sqlite")
            async with asyncio.timeout(60):
                while True:
                    await connection.session.check()
                    try:
                        grant = await asyncio.to_thread(
                            grants.find,
                            principal_id=owner.id,
                            device_id=connection.control_key.device_id,
                            workspace_ref=workspace,
                        )
                    except DomainError as exc:
                        if exc.failure.message != "One actual root binding required":
                            raise
                        await asyncio.sleep(0.1)
                        continue
                    break
            ticket, _, expiry = await asyncio.to_thread(
                launch.state.consumed_root, grant.selection_ticket_id, now=datetime.now(UTC)
            )
            decisions = await asyncio.to_thread(NativeDecisionJournal, local)
            await asyncio.to_thread(
                decisions.check,
                grant.root_handle,
                ticket,
                owner,
                connection.session.local.actor,
            )
            if (
                grant.owner != owner
                or grant.revoked
                or grant.capabilities != frozenset({"read"})
                or expiry <= datetime.now(UTC)
                or grant.workspace_ref != workspace
                or not Ed25519SignatureAdapter(launch.state).verify_document(
                    {**ticket.document(), "signature": grant.selection_signature},
                    device_id=grant.device_id,
                    domain="root-selection",
                )
            ):
                raise reject(
                    "installed_native_root_changed", "Current original root proof differs", 412
                )
            await connection.session.check()
            result.update(
                status="native_root_bound",
                root_selected=True,
                root_revision=grant.revision,
                root_selection_hash=parameter_hash(ticket.document()),
            )
    except (DomainError, TimeoutError) as exc:
        result.update(
            status="failed",
            failure_code=exc.failure.code if isinstance(exc, DomainError) else "deadline_exceeded",
        )
    finally:
        try:
            if launch:
                await launch.close()
            result["owned_launch_cleanup"] = True
            if owner and c.browser_sessions:
                await c.browser_sessions.logout(
                    owner,
                    RequestMeta(
                        request_id="installed-check-close-" + uuid4().hex, schema_version="0.1"
                    ),
                )
        finally:
            await c.close()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--settings", type=Path, required=True)
    parser.add_argument("--state-directory", type=Path, required=True)
    parser.add_argument(
        "--workspace-id", help="Internal workspace pin; native UI chooses the directory"
    )
    args = parser.parse_args()
    if not args.state_directory.is_absolute():
        parser.error("state-directory must be an explicit absolute installed state directory")
    workspace = (
        Ref(kind="workspace", id=args.workspace_id, version="1") if args.workspace_id else None
    )
    try:
        result = asyncio.run(
            check(args.settings, args.state_directory.resolve(), workspace),
            loop_factory=control_plane_loop,
        )
    except Exception as exc:
        # Settings/vault/SQL exceptions must not print protected input or a traceback.
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "failure_code": exc.failure.code
                    if isinstance(exc, DomainError)
                    else "internal_error",
                }
            )
        )
        raise SystemExit(1) from None
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
