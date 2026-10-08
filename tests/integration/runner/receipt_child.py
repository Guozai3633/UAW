"""Independent test process: controlled registry file + real Ed25519 and development journal.

No private keys, IPC endpoint, executor or actual Runner execution is involved.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "apps/local_runner"))

from uaw_runner.keys import Ed25519SignatureAdapter  # noqa: E402
from uaw_runner.protocol import RunnerProtocol  # noqa: E402
from uaw_runner.receipts import ReceiptJournal  # noqa: E402
from uaw_runner.state import LocalState  # noqa: E402

from uaw.shared.contracts import Principal, Ref  # noqa: E402
from uaw.shared.errors import DomainError, reject  # noqa: E402
from uaw.workspace.binding import RootBindings  # noqa: E402
from uaw.workspace.contracts import RegisteredReceiptCommand, RunnerCommand  # noqa: E402
from uaw.workspace.repository import MemoryAdmissionRepository, MemoryRootRepository  # noqa: E402


class ComponentFileReader:
    """Read ONLY separate fixture registration, never reconstruct it from request/receipt."""

    def __init__(self, path):
        self.path = path

    async def resolve(self, ref, *, authenticated_principal):
        raw = await asyncio.to_thread(self.path.read_text, encoding="utf-8")
        registry = json.loads(raw)
        if registry["revoked"] or authenticated_principal.wire() not in registry["channels"]:
            raise reject("permission_denied", "Fixture source/channel revoked", 403, "permission")
        if ref.wire() != registry["command_ref"]:
            raise reject("revision_conflict", "Fixture actual command Ref differs", 409)
        return RegisteredReceiptCommand(
            RunnerCommand.model_validate_json(json.dumps(registry["command"])),
            registry["device_id"],
            Principal.model_validate_json(json.dumps(registry["owner"])),
        )


async def main():
    directory, operation, input_file = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    incoming = json.loads(await asyncio.to_thread(input_file.read_text, encoding="utf-8"))
    actor = Principal.model_validate_json(json.dumps(incoming["actor"]))
    keys = await asyncio.to_thread(LocalState, directory / "keys.sqlite")
    protocol = RunnerProtocol(
        device_id="device1",
        bindings=RootBindings(MemoryRootRepository()),
        admissions=MemoryAdmissionRepository(),
        signatures=Ed25519SignatureAdapter(keys),
    )
    journal = ReceiptJournal(
        directory / "journal.sqlite",
        protocol=protocol,
        reader=ComponentFileReader(directory / "registry.json"),
    )
    try:
        if operation == "publish":
            result = await journal.publish(
                Ref.model_validate_json(json.dumps(incoming["command_ref"])),
                incoming["receipt_data"],
                authenticated_principal=actor,
            )
        else:
            result = await journal.read(
                Ref.model_validate_json(json.dumps(incoming["receipt_ref"])),
                authenticated_principal=actor,
            )
        print(json.dumps({"value": result.wire()}, ensure_ascii=True))
    except DomainError as exc:
        print(json.dumps({"failure": exc.failure.code, "status": exc.status_code}))


if __name__ == "__main__":
    # Process entry point only, not a synchronous bridge inside any production service.
    asyncio.run(main())
