"""Hidden separate Windows test process; no private key bytes in input/output."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "apps/local_runner"))

from uaw_runner.ipc.sessions import (  # noqa: E402
    AuthenticatedPipeSession,
    IpcSigner,
    IpcSigningBinding,
)
from uaw_runner.ipc.windows_pipe import WindowsApi, connect_pipe  # noqa: E402
from uaw_runner.state import LocalState  # noqa: E402

from tests.integration.runner.ipc_fixture import FixturePeerRegistry  # noqa: E402
from uaw.infrastructure.credentials import WindowsCredentialStore  # noqa: E402
from uaw.shared.errors import DomainError  # noqa: E402


async def main():
    path, mode = Path(sys.argv[1]), sys.argv[2]
    registry = json.loads(await asyncio.to_thread(path.read_text, encoding="utf-8"))
    identity = await asyncio.to_thread(WindowsApi().current)
    print(json.dumps({"identity": identity.__dict__}), flush=True)
    await asyncio.to_thread(
        sys.stdin.readline
    )  # trusted test orchestration installs this PID+creation
    registry = json.loads(await asyncio.to_thread(path.read_text, encoding="utf-8"))
    pipe = await connect_pipe(
        name=registry["pipe"], logon_sid=identity.logon_sid, timeout=registry.get("timeout", 10)
    )
    session = AuthenticatedPipeSession(
        pipe=pipe,
        registration=FixturePeerRegistry(path),
        directory=LocalState(Path(registry["keys"])),
        signer=IpcSigner(
            binding=IpcSigningBinding(
                "d1", registry["client"]["key_id"], "control", registry["control_handle"]
            ),
            directory=LocalState(Path(registry["keys"])),
            credentials=WindowsCredentialStore(registry["namespace"]),
        ),
    )
    try:
        await session.handshake()
        if mode == "echo":
            await session.send("command", {"id": "test-message"})
            frame = await session.receive()
            print(
                json.dumps({"kind": frame["kind"], "body": frame["body"], "connected": True}),
                flush=True,
            )
        elif mode == "idle":
            await asyncio.to_thread(sys.stdin.readline)
        elif mode == "disconnect":
            pass
    except DomainError as exc:
        print(json.dumps({"failure": exc.failure.code}), flush=True)
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
