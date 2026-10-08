"""Platform-owned Runner identities. Registration requires an independent channel source."""

import asyncio
import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore
from uaw.shared.contracts import Principal, Ref, RequestMeta
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.ports import RunnerChannelSourcePort
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreConflict, StoreMissing

Payload = dict[str, Any]
DEVICES = "runner.devices"
AGGREGATE = "runner-control"


def instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class RunnerDevices:
    def __init__(
        self,
        store: PostgresRecordStore,
        controller: Principal,
        channels: RunnerChannelSourcePort | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        validate_contract("Principal", controller.wire())
        if controller.kind != "service":
            raise ValueError("Runner controller must be an authenticated internal service")
        self.store, self.controller, self.channels = store, controller, channels
        self.transactions = TransactionalStore(store.database)
        self.clock = clock or (lambda: datetime.now(UTC))

    def now(self) -> datetime:
        now = self.clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("Runner clock must be timezone aware")
        return now

    def service(self, actor: Principal) -> None:
        validate_contract("Principal", actor.wire())
        if actor.wire() != self.controller.wire():
            raise reject("runner_service_denied", "Authenticated controller required", 403)

    async def source(self, device_id: str, channel_ref: Ref) -> Payload:
        if self.channels is None:
            raise CapabilityUnavailable("runner.trusted_channel_source")
        async with asyncio.timeout(30):
            raw = await self.channels.read(channel_ref, device_id=device_id)
        source: Payload = json.loads(json.dumps(raw, allow_nan=False))
        validate_contract("RunnerChannelSnapshot", source)
        if (
            source["device_id"] != device_id
            or source["channel_ref"] != channel_ref.wire()
            or source["owner"]["kind"] != "user"
            or source["actor"]["kind"] != "runner"
        ):
            raise reject("runner_channel_binding_denied", "Channel identity differs", 403)
        if not source["connected"] or instant(source["expires_at"]) <= self.now():
            raise reject("runner_channel_unavailable", "Channel is disconnected or expired", 409)
        return source

    async def _load(self, device_id: str) -> Payload:
        validate_contract("ID", device_id)

        async def inspect(tx: RecordTransaction) -> Payload:
            row = await tx.load(DEVICES, device_id)
            binding = dict(row.payload)
            validate_contract("RunnerDeviceBinding", binding)
            if binding["device_id"] != device_id or binding["revision"] != row.revision:
                raise StoreConflict()
            if (
                binding["state"] == "active"
                and instant(binding["source"]["expires_at"]) <= self.now()
            ):
                binding = {**binding, "state": "expired", "revision": row.revision + 1}
                await tx.write(DEVICES, device_id, "RunnerDeviceBinding", binding, row.revision)
            return binding

        # Seal observed expiry even if the caller later receives an error.
        return await self.transactions.inspect(self.controller, AGGREGATE, inspect)

    async def current(self, device_id: str, *, authenticated_principal: Principal) -> Payload:
        validate_contract("Principal", authenticated_principal.wire())
        binding = await self._load(device_id)
        source = binding["source"]
        if authenticated_principal.wire() not in (source["actor"], source["owner"]):
            raise reject("runner_actor_denied", "Current device principal differs", 403)
        if binding["state"] != "active":
            raise reject("runner_device_inactive", "Device binding is inactive", 409)
        current = await self.source(device_id, Ref.model_validate(source["channel_ref"]))
        again = await self._load(device_id)
        if current != source or again != binding:
            raise reject("runner_device_changed", "Current channel or binding changed", 412)
        if instant(source["expires_at"]) <= self.now():
            await self._load(device_id)
            raise reject("runner_device_inactive", "Device binding expired", 409)
        return binding

    async def owner(self, actor: Principal, device_id: str) -> Principal:
        binding = await self.current(device_id, authenticated_principal=actor)
        return Principal.model_validate(binding["source"]["owner"])

    async def bind(
        self, request: Payload, meta: RequestMeta, *, authenticated_service: Principal
    ) -> Payload:
        self.service(authenticated_service)
        validate_contract("RunnerDeviceBindRequest", request)
        source = await self.source(request["device_id"], Ref.model_validate(request["channel_ref"]))

        async def write(tx: RecordTransaction) -> Payload:
            try:
                old = await tx.load(DEVICES, request["device_id"])
            except StoreMissing:
                old = None
            expected = request["expected_revision"]
            if (old.revision if old else 0) != expected:
                raise StoreConflict()
            if old:
                validate_contract("RunnerDeviceBinding", old.payload)
                if old.payload["source"]["owner"] != source["owner"]:
                    raise reject("runner_owner_transfer_denied", "Device owner cannot change", 403)
                if (
                    old.payload["source"]["channel_ref"] == source["channel_ref"]
                    and old.payload["source"] != source
                ):
                    raise reject(
                        "runner_channel_changed", "Pinned channel content cannot change", 412
                    )
                if (
                    old.payload["state"] != "active"
                    or instant(old.payload["source"]["expires_at"]) <= self.now()
                ) and old.payload["source"]["pairing_ref"] == source["pairing_ref"]:
                    raise reject("runner_pairing_stale", "A fresh proven pairing is required", 412)
            if instant(source["expires_at"]) <= self.now():
                raise reject("runner_channel_unavailable", "Channel expired while waiting", 409)
            result = {
                "device_id": request["device_id"],
                "revision": expected + 1,
                "source": source,
                "state": "active",
            }
            await tx.write(DEVICES, request["device_id"], "RunnerDeviceBinding", result, expected)
            return result

        result = await self.transactions.execute(
            self.controller,
            AGGREGATE,
            meta,
            {"action": "device.bind", "request": request, "service": authenticated_service.wire()},
            write,
        )
        actual = await self.current(
            request["device_id"], authenticated_principal=Principal.model_validate(source["actor"])
        )
        if actual != result:
            raise StoreConflict()
        return actual

    async def revoke(
        self,
        device_id: str,
        expected_revision: int,
        meta: RequestMeta,
        *,
        authenticated_service: Principal,
    ) -> Payload:
        self.service(authenticated_service)
        validate_contract("Revision", expected_revision)

        async def write(tx: RecordTransaction) -> Payload:
            row = await tx.load(DEVICES, device_id)
            if row.revision != expected_revision:
                raise StoreConflict()
            result = {**row.payload, "state": "revoked", "revision": row.revision + 1}
            await tx.write(DEVICES, device_id, "RunnerDeviceBinding", result, row.revision)
            return result

        return await self.transactions.execute(
            self.controller,
            AGGREGATE,
            meta,
            {"action": "device.revoke", "id": device_id, "expected": expected_revision},
            write,
        )
