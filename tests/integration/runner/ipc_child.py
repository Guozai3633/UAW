"""Hidden separate Windows test process; no private key bytes in input/output."""

import asyncio
import ctypes
import json
import struct
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
        if mode in {"raw-long", "raw-zero", "raw-truncated", "raw-silent"}:
            await pipe.receive()  # actual server hello, no proof accepted
            if mode == "raw-silent":
                await asyncio.to_thread(sys.stdin.readline)
                return
            data = struct.pack("!I", 256 * 1024 + 1 if mode == "raw-long" else 0)
            if mode == "raw-truncated":
                data = struct.pack("!I", 100) + b"partial"
            buffer = ctypes.create_string_buffer(data)
            await pipe.operation(pipe.overlapped, "write", buffer, len(data), pipe.deadline(None))
            if mode == "raw-truncated":
                return
            await asyncio.to_thread(sys.stdin.readline)
            return
        await session.handshake()
        if mode == "max-frame":
            from uaw_runner.ipc.frames import encode
            from uaw_runner.ipc.windows_pipe import MAX_FRAME

            frame = session.frame("command", {"data": ""}, 1)
            frame["signature"] = await session.signer.signature(frame)
            frame["body"]["data"] = "x" * (MAX_FRAME - len(encode(frame)))
            frame["signature"] = await session.signer.signature(frame)
            assert len(encode(frame)) == MAX_FRAME
            await pipe.send(encode(frame))
            await asyncio.to_thread(sys.stdin.readline)
        elif mode in {"bad-signature", "old-nonce", "replay", "body-authority"}:
            from uaw_runner.ipc.frames import encode

            body = {"command_ref": registry.get("command_ref", {})}
            if mode == "body-authority":
                body["approved"] = True
                body["principal"] = {"id": "admin", "kind": "user"}
            frame = session.frame("command", body, 1)
            if mode == "old-nonce":
                frame["peer_nonce"] = "f" * 64
            frame["signature"] = await session.signer.signature(frame)
            if mode == "bad-signature":
                parts = frame["signature"].split(":")
                parts[-1] = ("A" if parts[-1][0] != "A" else "B") + parts[-1][1:]
                frame["signature"] = ":".join(parts)
            await pipe.send(encode(frame))
            if mode == "replay":
                await pipe.send(encode(frame))
            await asyncio.to_thread(sys.stdin.readline)
        elif mode == "echo":
            await session.send("command", {"id": "test-message"})
            frame = await session.receive()
            print(
                json.dumps(
                    {
                        "kind": frame["kind"],
                        "body": frame["body"],
                        "connected": True,
                        "channel_ref": session.channel_ref.wire(),
                    }
                ),
                flush=True,
            )
        elif mode in {"read", "recover"}:
            kind = "recover" if mode == "recover" else "command"
            await session.send(kind, {"command_ref": registry["command_ref"]})
            frame = await session.receive()
            from uaw_runner.keys import Ed25519SignatureAdapter
            from uaw_runner.receipts import canonical, digest

            assert frame["kind"] == "receipt"
            body = frame["body"]
            assert body["command_ref"] == registry["command_ref"]
            assert body["receipt_ref"]["content_hash"] == digest(body["receipt"])
            assert Ed25519SignatureAdapter(session.directory).verify_receipt(
                body["receipt"], device_id="d1"
            )
            print(canonical(body), flush=True)
            await asyncio.to_thread(sys.stdin.readline)
        elif mode == "lost":
            await session.send("command", {"command_ref": registry["command_ref"]})
            print(json.dumps({"sent": True}), flush=True)
            await asyncio.to_thread(sys.stdin.readline)
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
