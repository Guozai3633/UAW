"""Separate process: actual once CAS/recovery, explicit independent fixture registration.
No OS private secrets, production channel, or permission reconstructed from command input.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "apps/local_runner"))

from uaw_runner.admissions import PersistentAdmissions  # noqa: E402
from uaw_runner.assembly import RegisteredPrincipalMapping  # noqa: E402
from uaw_runner.keys import Ed25519SignatureAdapter, ProtectedSigner  # noqa: E402
from uaw_runner.protocol import RunnerProtocol  # noqa: E402
from uaw_runner.read_executor import DeviceSigningBinding, ReadOnlyRunner  # noqa: E402
from uaw_runner.read_state import ReadExecutionJournal  # noqa: E402
from uaw_runner.receipts import ReceiptJournal, canonical  # noqa: E402
from uaw_runner.root_source import PersistentRootGrants  # noqa: E402
from uaw_runner.state import LocalState  # noqa: E402

from tests.integration.runner.test_native_root_source import CurrentOwnerFixture  # noqa: E402
from tests.integration.runner.test_read_executor import RegisteredCommandFixture  # noqa: E402
from tests.unit.runner.test_real_keys import CredentialFixture  # noqa: E402
from uaw.shared.contracts import Principal, Ref  # noqa: E402
from uaw.shared.errors import DomainError  # noqa: E402
from uaw.workspace.binding import RootBindings  # noqa: E402
from uaw.workspace.contracts import RunnerCommand  # noqa: E402


class UnusedExecutionSource:
    async def current(self, *args, **kwargs):
        raise AssertionError("Recovery cannot request new execution authority/root")


class RegisteredChannel:
    def __init__(self, path):
        self.path = path

    async def read(self, ref, *, device_id):
        registry = json.loads(await asyncio.to_thread(self.path.read_text, encoding="utf-8"))
        value = registry["channel"]
        assert value["channel_ref"] == ref.wire() and device_id == value["device_id"]
        return value


async def main():
    path, operation = Path(sys.argv[1]), sys.argv[2]
    registry = json.loads(await asyncio.to_thread(path.read_text, encoding="utf-8"))
    command = RunnerCommand.model_validate_json(canonical(registry["command"]))
    actor = Principal.model_validate_json(canonical(registry["actor"]))
    command_ref = Ref.model_validate_json(canonical(registry["command_ref"]))
    owners = CurrentOwnerFixture()
    owners.value = Principal.model_validate_json(canonical(registry["owner"]))
    grants = PersistentRootGrants(Path(registry["grants"]))
    mapping = RegisteredPrincipalMapping(owners)
    case = {"mapping": mapping, "grants": grants}
    reader = RegisteredCommandFixture(case, command, command_ref)
    reader.denied = registry["denied"]
    state = LocalState(Path(registry["keys"]))
    protocol = RunnerProtocol(
        device_id="d1",
        bindings=RootBindings(grants),
        admissions=PersistentAdmissions(Path(registry["admissions"])),
        signatures=Ed25519SignatureAdapter(state),
        principal_mapping=mapping,
        async_authority=UnusedExecutionSource(),
        clock=lambda: datetime.fromisoformat(registry["now"]),
    )
    journal = ReceiptJournal(Path(registry["receipts"]), protocol=protocol, reader=reader)
    executions = ReadExecutionJournal(Path(registry["reads"]))
    try:
        if operation == "claim":
            source = await reader.resolve(command_ref, authenticated_principal=actor)
            attempt, won = await asyncio.to_thread(
                executions.claim,
                source,
                command_ref,
                root_handle="native-root1",
                root_revision=0,
                check=lambda: None,
            )
            print(json.dumps({"won": won, "token": attempt.token}))
        else:
            runner = ReadOnlyRunner(
                protocol=protocol,
                command_ref=command_ref,
                journal=journal,
                executions=executions,
                currency="CNY",
                roots=UnusedExecutionSource(),
                channel=RegisteredChannel(path),
                channel_ref=Ref.model_validate_json(canonical(registry["channel"]["channel_ref"])),
                signer=ProtectedSigner(state, CredentialFixture()),
                device_key=DeviceSigningBinding("d1", "device1", "unused-no-secret"),
            )
            value = await runner.execute(command, authenticated_principal=actor)
            print(json.dumps({"receipt": value.wire()}, ensure_ascii=True))
    except DomainError as exc:
        print(json.dumps({"failure": exc.failure.code, "message": exc.failure.message}))


if __name__ == "__main__":
    asyncio.run(main())  # Independent test process only; never a runtime async bridge.
