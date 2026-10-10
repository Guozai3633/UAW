"""Explicit test factory. No A production bootstrap; no human affirmative evidence.

All storage/OS credentials/paths are random owned Session D temporary fixtures.
"""

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from uaw_runner.admissions import PersistentAdmissions
from uaw_runner.assembly import RegisteredPrincipalMapping
from uaw_runner.bootstrap import BootstrapConsumer
from uaw_runner.helper_host import HelperApplication
from uaw_runner.ipc.channel_source import ConnectionRegistry
from uaw_runner.keys import Ed25519SignatureAdapter, ProtectedSigner
from uaw_runner.native_confirmation import RegisteredNativeChallenges
from uaw_runner.native_dialog import NativeDirectoryDecision
from uaw_runner.pairing import LocalRoots, PersistentRootSelection
from uaw_runner.protocol import RunnerProtocol
from uaw_runner.read_executor import DeviceSigningBinding
from uaw_runner.read_state import ReadExecutionJournal
from uaw_runner.receipts import ReceiptJournal, canonical
from uaw_runner.root_source import NativeRootSource, PersistentRootGrants
from uaw_runner.runtime import ReadOnlyHelper
from uaw_runner.state import LocalState

from tests.integration.runner.ipc_fixture import FixturePeerRegistry
from tests.integration.runner.test_read_executor import (
    RegisteredAuthorityFixture,
    RegisteredCommandFixture,
)
from uaw.infrastructure.credentials import WindowsCredentialStore
from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.workspace.binding import RootBindings
from uaw.workspace.contracts import RunnerCommand


class FixtureOwner:
    def __init__(self, path):
        self.path = path

    async def owner(self, actor, device_id):
        record = json.loads(await asyncio.to_thread(self.path.read_text, encoding="utf-8"))
        owner = Principal.model_validate_json(canonical(record["server"]["owner"]))
        if record.get("revoked") or device_id != "d1" or actor.wire() != owner.wire():
            raise reject("permission_denied", "Controlled current owner denied", 403, "permission")
        return owner


class FixtureChallenge:
    """Fixture independently selects original Ticket id; not an enrollment service."""

    def __init__(self, case):
        self.case, self.helper = case, None

    async def current(self, ticket_id):
        if ticket_id != self.case["ticket_id"]:
            raise reject("permission_denied", "Controlled original challenge denied", 403)
        helper = self.helper
        return await RegisteredNativeChallenges(
            state=self.case["state"],
            registry=helper.registry,
            channel_ref=helper.session.channel_ref,
            device_id="d1",
            mapping=self.case["mapping"],
            clock=lambda: datetime.now(UTC),
        ).current(ticket_id)


def build_helper(case, registration, challenges, registry):
    bootstrap = BootstrapConsumer(
        registration=registration,
        challenges=challenges,
        mapping=case["mapping"],
        directory=case["state"],
        signer=ProtectedSigner(case["state"], case["vault"]),
        device_key=DeviceSigningBinding("d1", "device1", case["device_handle"]),
    )
    helper = ReadOnlyHelper(
        bootstrap=bootstrap,
        protocol=case["protocol"],
        commands=case["reader"],
        journal=case["journal"],
        executions=case["executions"],
        roots=case["source"],
        registry=registry,
        currency="CNY",
    )
    challenges.helper = helper
    return helper


class Factory:
    async def create(self, identity):
        try:
            return await self.build(identity)
        except Exception as exc:
            import traceback

            path = Path(os.environ["UAW_D_TEST_HELPER_INPUT"]).parent / "helper-fixture-error.log"
            # No values/code/proof/credential bytes; diagnostic stack locations only.
            path.write_text(
                type(exc).__name__ + "\n" + "".join(traceback.format_tb(exc.__traceback__)),
                encoding="utf-8",
            )
            raise

    async def build(self, identity):
        path = Path(os.environ["UAW_D_TEST_HELPER_INPUT"])
        data = json.loads(await asyncio.to_thread(path.read_text, encoding="utf-8"))
        tmp = Path(data["temp"])
        if identity.__dict__ != data["server"]["identity"]:
            raise reject("permission_denied", "Test independent OS binding mismatch", 403)
        state = LocalState(Path(data["keys"]))
        local = LocalRoots(tmp / "native" / "roots.sqlite")
        grants = PersistentRootGrants(tmp / "native" / "grants.sqlite")
        mapping = RegisteredPrincipalMapping(FixtureOwner(path))
        roots = NativeRootSource(
            RootBindings(grants, PersistentRootSelection(state, local)),
            grants=grants,
            selections=state,
            native_roots=local,
            mapping=mapping,
            directory=state,
        )
        command = RunnerCommand.model_validate_json(canonical(data["command"]))
        workspace = Ref.model_validate_json(canonical(data["workspace"]))
        case = dict(
            tmp=tmp,
            state=state,
            local=local,
            grants=grants,
            mapping=mapping,
            source=roots,
            vault=WindowsCredentialStore(data["namespace"]),
            device_handle=data["device_handle"],
            ticket_id=data["ticket_id"],
            workspace=workspace,
            ctx=TrustedExecutionContext.model_validate_json(canonical(data["ctx"])),
            clock=[datetime.now(UTC)],
        )
        ref = Ref.model_validate_json(canonical(data["command_ref"]))
        reader = RegisteredCommandFixture(case, command, ref)
        authority = RegisteredAuthorityFixture(command, case)
        authority.value = data["authority"]
        protocol = RunnerProtocol(
            device_id="d1",
            bindings=roots.bindings,
            admissions=PersistentAdmissions(tmp / "admissions.sqlite"),
            signatures=Ed25519SignatureAdapter(state),
            async_authority=authority,
            principal_mapping=mapping,
        )
        case.update(
            protocol=protocol,
            reader=reader,
            journal=ReceiptJournal(tmp / "receipts.sqlite", protocol=protocol, reader=reader),
            executions=ReadExecutionJournal(tmp / "reads.sqlite"),
        )
        challenges = FixtureChallenge(case)
        helper = build_helper(case, FixturePeerRegistry(path), challenges, ConnectionRegistry())

        async def activate_inner(current):
            ticket = await asyncio.to_thread(state.get, data["ticket_id"], now=datetime.now(UTC))
            operation = data.get("trusted_local_operation", "select-if-pending")
            if operation == "revoke":
                await (await current.authorization()).revoke("native-root1", expected_revision=0)
                return
            if operation == "bind-again":
                from uaw.workspace.contracts import RootSelection

                selected = RootSelection.model_validate_json(
                    await asyncio.to_thread(
                        (tmp / "native-selected.json").read_text, encoding="utf-8"
                    )
                )
                await (await current.authorization()).bind(selected, workspace)
                return
            if ticket.state == "pending" or operation == "repeat-select":
                lifecycle = await current.authorization()
                if data["ui"] == "typed-double":
                    from uaw_runner import native_confirmation

                    class ExplicitUiDouble:
                        def show(self, prompt, stopped, deadline):
                            root = tmp / "selected-project"
                            stat = root.stat()
                            return NativeDirectoryDecision(root, (stat.st_dev, stat.st_ino))

                    native_confirmation.WindowsNativeDialog = ExplicitUiDouble
                elif data["ui"] == "actual-timeout":
                    lifecycle.native.timeout = 0.1
                selection = await lifecycle.select(
                    data["ticket_id"],
                    expected_revision=0,
                    code=data["code"],
                    proof_signature=data["proof"],
                )
                # Harness may bind/read ONLY its own freshly prepared root.
                if (
                    await asyncio.to_thread(local.current, ticket)
                    != (tmp / "selected-project").resolve()
                ):
                    raise reject("permission_denied", "Manual harness root differs", 403)
                await lifecycle.bind(selection, workspace)
                await asyncio.to_thread(
                    (tmp / "native-selected.json").write_text,
                    canonical(selection.wire()),
                    encoding="utf-8",
                )

        async def activate(current):
            try:
                await activate_inner(current)
            except Exception as exc:
                import traceback

                (tmp / "helper-activate-error.log").write_text(
                    type(exc).__name__ + "\n" + "".join(traceback.format_tb(exc.__traceback__)),
                    encoding="utf-8",
                )
                raise

        return HelperApplication(helper, activate)


assembly = Factory()
