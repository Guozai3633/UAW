"""Hidden actual Windows control process; independent test registration, no private bytes."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "apps/local_runner"))

from uaw_runner.ipc.channel_source import ConnectionRegistry  # noqa: E402
from uaw_runner.ipc.sessions import (  # noqa: E402
    AuthenticatedPipeSession,
    IpcSigner,
    IpcSigningBinding,
)
from uaw_runner.ipc.windows_pipe import WindowsApi, connect_pipe  # noqa: E402
from uaw_runner.keys import Ed25519SignatureAdapter  # noqa: E402
from uaw_runner.state import LocalState  # noqa: E402

from tests.integration.runner.ipc_fixture import FixturePeerRegistry  # noqa: E402
from uaw.infrastructure.credentials import WindowsCredentialStore  # noqa: E402
from uaw.infrastructure.runner_pipe import RunnerPipeClient, canonical  # noqa: E402
from uaw.shared.contracts import Ref  # noqa: E402
from uaw.shared.errors import reject  # noqa: E402
from uaw.workspace.contracts import RegisteredReceiptCommand, RunnerCommand  # noqa: E402


class IndependentCommandFixture:
    """Trusted test orchestration writes this before transport; body grants no access."""

    def __init__(self, path):
        self.path = path

    async def resolve(self, command_ref, *, authenticated_principal):
        data = json.loads(await asyncio.to_thread(self.path.read_text, encoding="utf-8"))
        command = RunnerCommand.model_validate_json(canonical(data["command_snapshot"]))
        if (
            command_ref.wire() != data["command_ref"]
            or authenticated_principal != command.trusted_context.principal
        ):
            raise reject("permission_denied", "Independent registered command differs", 403)
        return RegisteredReceiptCommand(command, "d1", authenticated_principal)


async def main():
    path = Path(sys.argv[1])
    identity = await asyncio.to_thread(WindowsApi().current)
    print(json.dumps({"identity": identity.__dict__}), flush=True)
    await asyncio.to_thread(sys.stdin.readline)
    data = json.loads(await asyncio.to_thread(path.read_text, encoding="utf-8"))
    keys = LocalState(Path(data["keys"]))
    pipe = await connect_pipe(name=data["pipe"], logon_sid=identity.logon_sid, timeout=10)
    session = AuthenticatedPipeSession(
        pipe=pipe,
        registration=FixturePeerRegistry(path),
        directory=keys,
        signer=IpcSigner(
            binding=IpcSigningBinding("d1", "control1", "control", data["control_handle"]),
            directory=keys,
            credentials=WindowsCredentialStore(data["namespace"]),
        ),
    )
    registry = ConnectionRegistry()
    try:
        await session.handshake()
        await registry.add(session)
        client = RunnerPipeClient(
            session=session,
            registry=registry,
            commands=IndependentCommandFixture(path),
            signatures=Ed25519SignatureAdapter(keys),
        )
        actual = await client.read(Ref.model_validate(data["command_ref"]))
        print(
            canonical({"receipt_ref": actual.receipt_ref.wire(), "receipt": actual.receipt.wire()}),
            flush=True,
        )
        await asyncio.to_thread(sys.stdin.readline)
    finally:
        await registry.close()
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
