"""Test-only new-process root recovery from separate controlled ownership registration.

No private keys, actual IPC/native user confirmation or user file actions.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "apps/local_runner"))

from uaw_runner.assembly import RegisteredPrincipalMapping  # noqa: E402
from uaw_runner.pairing import LocalRoots, PersistentRootSelection  # noqa: E402
from uaw_runner.root_source import NativeRootSource, PersistentRootGrants  # noqa: E402
from uaw_runner.state import LocalState  # noqa: E402

from uaw.shared.contracts import Principal, Ref, TrustedExecutionContext  # noqa: E402
from uaw.shared.errors import reject  # noqa: E402
from uaw.workspace.binding import RootBindings  # noqa: E402


async def main():
    root, registry_file = Path(sys.argv[1]), Path(sys.argv[2])
    registration = json.loads(await asyncio.to_thread(registry_file.read_text, encoding="utf-8"))

    class ActualFixtureOwnerRegistry:
        async def owner(self, actor, device_id):
            current = json.loads(await asyncio.to_thread(registry_file.read_text, encoding="utf-8"))
            if device_id != current["device_id"] or actor.wire() != current["owner"]:
                raise reject("permission_denied", "Fixture actual owner/channel differs", 403)
            return Principal.model_validate_json(json.dumps(current["owner"]))

    state = await asyncio.to_thread(LocalState, root / "control" / "keys-selections.sqlite")
    local = await asyncio.to_thread(LocalRoots, root / "native" / "roots.sqlite")
    grants = await asyncio.to_thread(PersistentRootGrants, root / "native" / "grants.sqlite")
    source = NativeRootSource(
        RootBindings(grants, PersistentRootSelection(state, local)),
        grants=grants,
        selections=state,
        native_roots=local,
        directory=state,
        mapping=RegisteredPrincipalMapping(ActualFixtureOwnerRegistry()),
        clock=lambda: datetime.fromisoformat(registration["now"]),
    )
    result = await source.current(
        registration["device_id"],
        Ref.model_validate_json(json.dumps(registration["workspace"])),
        TrustedExecutionContext.model_validate_json(json.dumps(registration["context"])),
    )
    print(json.dumps(result))


if __name__ == "__main__":
    asyncio.run(main())  # Test process entry only; no production sync/async bridge.
