"""Optional trusted workspace selector; only native UI chooses an actual directory.

The workspace pin names the requested binding, not a path or read permission.
Default installed launches have no selector and never open a directory dialog.
"""

import asyncio
import json
from pathlib import Path
from uuid import uuid4

from uaw_runner.runtime import ReadOnlyHelper

from uaw.infrastructure.enrollment_peers import EnrolledPeerRegistry
from uaw.shared.contracts import Ref
from uaw.shared.errors import CapabilityUnavailable, DomainError


def workspace_pin(ref: Ref) -> Ref:
    fixed = Ref.model_validate_json(json.dumps(ref.wire(), allow_nan=False))
    if fixed.kind != "workspace" or fixed.location is not None or fixed.access_scope is not None:
        raise ValueError("An internal fixed workspace reference is required")
    return fixed


class InstalledRootSelection:
    def __init__(
        self, workspace: Ref, peers: EnrolledPeerRegistry, *, diagnostic_path: Path | None = None
    ) -> None:
        self.workspace = workspace_pin(workspace)
        self.peers = peers
        self.used = False
        self.diagnostic_path = diagnostic_path
        self.phase = "connected"

    async def __call__(self, helper: ReadOnlyHelper) -> None:
        try:
            await self.select(helper)
        except BaseException as exc:
            if self.diagnostic_path is not None:
                # Private deployment diagnostics carry no path, proof or permission.
                value = {
                    "phase": self.phase,
                    "error_type": type(exc).__name__,
                    "failure_code": exc.failure.code
                    if isinstance(exc, DomainError)
                    else "internal_error",
                }
                writing = asyncio.create_task(
                    asyncio.to_thread(
                        self.diagnostic_path.write_text, json.dumps(value), encoding="utf-8"
                    )
                )
                try:
                    await asyncio.shield(writing)
                except asyncio.CancelledError:
                    await writing
                except OSError:
                    pass  # Diagnostic storage never changes the original denial.
            raise

    async def select(self, helper: ReadOnlyHelper) -> None:
        if self.used:
            # Reconnection does not reopen UI or imply the first selection succeeded.
            # Every subsequent command/recover still checks the owning current root.
            if helper.session is None:
                raise CapabilityUnavailable("runner.installed.connected_root_selection")
            await helper.bootstrap.connected(helper.session)
            return
        self.used = True
        self.phase = "current_session"
        session = helper.session
        if session is None or session.local is None:
            raise CapabilityUnavailable("runner.installed.connected_root_selection")
        await helper.bootstrap.connected(session)
        peer = await self.peers.current(session.local.identity, role="device")
        selections = helper.roots.selections
        if selections is None:
            raise CapabilityUnavailable("runner.installed.root_ticket_source")
        key = await asyncio.to_thread(
            helper.bootstrap.directory.lookup, peer.key_id, device_id=peer.device_id
        )
        expiry = min(session.expires_at, peer.expires_at)
        self.phase = "issue_ticket"
        issuing = asyncio.create_task(
            asyncio.to_thread(
                selections.issue,
                request_id="installed-root-" + uuid4().hex,
                kind="root",
                principal_id=peer.owner.id,
                device_id=peer.device_id,
                key_id=peer.key_id,
                public_bytes=key.public_bytes,
                expires_at=expiry,
                now=helper.protocol.clock(),
                root_handle="root-" + uuid4().hex,
                display_name="UAW 单用户工作区（仅本次有界只读）",
            )
        )
        try:
            issued = await asyncio.shield(issuing)
        except asyncio.CancelledError:
            await issuing  # No late persistent ticket writer after cancellation completes.
            raise
        if issued.verification_code is None:
            raise CapabilityUnavailable("runner.installed.original_root_code")
        await helper.bootstrap.connected(session)
        self.phase = "sign_original_proof"
        binding = helper.bootstrap.device_key
        signature = await helper.bootstrap.signer.sign_document(
            issued.ticket.document(),
            device_id=peer.device_id,
            key_id=peer.key_id,
            credential_handle=binding.credential_handle,
            domain="pairing-proof",
        )
        self.phase = "authorization_assembly"
        auth = await helper.authorization()
        # NativeReadAuthorization verifies this independently issued original ticket,
        # current account/channel/key and the human native decision. No path is supplied.
        self.phase = "native_select"
        selection = await auth.select(
            issued.ticket.ticket_id,
            expected_revision=0,
            code=issued.verification_code,
            proof_signature=signature,
        )
        await helper.bootstrap.connected(session)
        self.phase = "bind_selection"
        await auth.bind(selection, self.workspace)
        await helper.bootstrap.connected(session)
        self.phase = "complete"
