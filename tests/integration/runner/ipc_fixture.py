"""Controlled independently provisioned UAW pairing registry; actual OS/key sources.
This is NOT native user confirmation, production account mapping or pairing V2.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from uaw_runner.ipc.sessions import RegisteredPeer
from uaw_runner.ipc.windows_pipe import OsIdentity
from uaw_runner.receipts import canonical

from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import reject


class FixturePeerRegistry:
    def __init__(self, path: Path):
        self.path = path

    async def current(self, identity, *, role):
        registry = json.loads(await asyncio.to_thread(self.path.read_text, encoding="utf-8"))
        if registry.get("revoked", False):
            raise reject(
                "permission_denied", "Fixture independent registration revoked", 403, "permission"
            )
        key = "server" if role == "device" else "client"
        value = registry[key]
        if identity != OsIdentity(**value["identity"]):
            raise reject(
                "ipc_identity_denied",
                "OS process not in independent fixture registry",
                403,
                "permission",
            )
        return RegisteredPeer(
            identity,
            Principal.model_validate_json(canonical(value["owner"])),
            Principal.model_validate_json(canonical(value["actor"])),
            value["device_id"],
            role,
            value["key_id"],
            Ref.model_validate_json(canonical(value["key_ref"])),
            Ref.model_validate_json(canonical(value["pairing_ref"])),
            datetime.fromisoformat(value["expires_at"]),
        )
