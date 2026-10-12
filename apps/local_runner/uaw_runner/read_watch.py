"""Independent local invalidation alongside an owning SQL-only change watch.

No snapshots escape this watch, and no return value grants execution. Full current
sources still bracket actual effects. Recovery never uses the active SQL watch.
"""

import asyncio
from collections.abc import Coroutine
from typing import Any

from uaw.shared.contracts import Principal
from uaw.shared.errors import reject
from uaw.workspace.contracts import RegisteredReceiptCommand, RunnerRootSnapshot
from uaw_runner.ipc.channel_source import ConnectionRegistry
from uaw_runner.ipc.sessions import AuthenticatedPipeSession
from uaw_runner.read_current import reply_deadline
from uaw_runner.read_executor import ReadOnlyRunner, command_workspace
from uaw_runner.receipts import canonical, digest
from uaw_runner.root_source import NativeRootSource


async def stop_on_change(*checks: Coroutine[Any, Any, None]) -> None:
    """Any monitor completion (including ordinary return) aborts owned work."""
    tasks = [asyncio.create_task(check) for check in checks]
    try:
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            await task
        raise reject("runner_current_changed", "Original monitored source changed", 412)
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


async def owned_thread[T](operation: Coroutine[Any, Any, T]) -> T:
    """Drain short owned local metadata IO on cancellation, retaining no OS handles."""
    task = asyncio.create_task(operation)
    try:
        return await asyncio.shield(task)
    except BaseException:
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                continue
            except Exception:
                break
        raise


class LocalReadInvalidation:
    def __init__(self, roots: NativeRootSource) -> None:
        self.roots = roots

    async def watch_connection(self, session: AuthenticatedPipeSession, *, deadline: float) -> None:
        # Starts while the independent Reader and SQL initial pass are still awaiting.
        while True:
            reply_deadline(deadline)
            await session.check_local(deadline=deadline)
            reply_deadline(deadline)
            await asyncio.sleep(min(0.05, max(0, deadline - asyncio.get_running_loop().time())))

    async def watch(
        self,
        runner: ReadOnlyRunner,
        source: RegisteredReceiptCommand,
        *,
        authenticated_principal: Principal,
        session: AuthenticatedPipeSession,
        registry: ConnectionRegistry,
        deadline: float,
    ) -> None:
        runner.available()
        if (
            runner.roots is not self.roots
            or runner.channel is not registry
            or runner.channel_ref is None
            or runner.signer is None
            or runner.device_key is None
            or self.roots.directory is not session.directory
            or runner.signer.directory is not session.directory
            or runner.signer.credentials is not session.signer.credentials
            or runner.device_key.key_id != session.signer.binding.key_id
            or runner.device_key.credential_handle != session.signer.binding.credential_handle
            or runner.device_key.device_id != session.signer.binding.device_id
        ):
            raise reject("binding_mismatch", "Local monitor must share actual runner sources", 503)
        command = source.command
        if (
            source.device_id != runner.protocol.device_id
            or runner.command_ref.content_hash != digest(command.wire())
            or source.owner != command.trusted_context.principal
        ):
            raise reject("binding_mismatch", "Independent monitored command differs", 403)
        workspace = command_workspace(command)
        comparison: str | None = None
        while True:
            reply_deadline(deadline)
            runner.admission.deadline(command)
            channel = registry._snapshot(session, runner.channel_ref, device_id=source.device_id)
            if channel.owner != source.owner or channel.actor != authenticated_principal:
                raise reject("binding_mismatch", "Original monitored channel owner differs", 403)
            root = RunnerRootSnapshot.model_validate_json(
                canonical(
                    await owned_thread(
                        asyncio.to_thread(
                            self.roots._read, source.device_id, workspace, source.owner
                        )
                    )
                )
            )
            if (
                root.owner != source.owner
                or root.device_id != source.device_id
                or root.workspace_ref != workspace
            ):
                raise reject("binding_mismatch", "Actual monitored native source differs", 403)

            # Current signature/key and actual root scope, never an allowed cache.
            def external(root: RunnerRootSnapshot = root) -> None:
                assert runner.protocol.signatures is not None
                if not runner.protocol.signatures.verify_command(
                    command, device_id=source.device_id
                ):
                    raise reject("ipc_signature_denied", "Original command signature rejected", 403)
                parameters = command.parameters["parameters"]
                assert isinstance(parameters, dict) and isinstance(parameters["path"], str)
                self.roots.bindings.check_scope(
                    root_handle=root.root_handle,
                    principal_id=source.owner.id,
                    device_id=source.device_id,
                    workspace_ref=workspace,
                    expected_revision=root.binding_revision,
                    relative_path=parameters["path"],
                    now=runner.protocol.clock(),
                )

            await owned_thread(asyncio.to_thread(external))
            observed = canonical(root.wire())
            if comparison is not None and observed != comparison:
                raise reject("runner_current_changed", "Original local root source changed", 412)
            comparison = observed
            reply_deadline(deadline)
            runner.admission.deadline(command)
            await asyncio.sleep(min(0.05, max(0, deadline - asyncio.get_running_loop().time())))
