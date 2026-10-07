"""Only registered, actually read pins are resolvable; every open checks current ACL."""

from __future__ import annotations

from typing import Any

from uaw.context.contracts import from_wire
from uaw.context.repository import ContextRepository
from uaw.context.sources import SourceResolver, component_result
from uaw.shared.contracts import Location, Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import validate_contract


class References:
    def __init__(self, sources: SourceResolver, repository: ContextRepository) -> None:
        self.sources, self.repository = sources, repository

    async def resolve(self, ref: Ref, ctx: TrustedExecutionContext) -> dict[str, Any]:
        await self.sources.recheck(ref, ctx)
        record = await self.repository.reference(ref, ctx)
        pin = from_wire(Ref, record["content_ref"])
        await self.sources.read(pin, "pinned", ctx)
        for provenance in record["provenance_refs"]:
            await self.sources.recheck(from_wire(Ref, provenance), ctx)
        await self.sources.guard.check(ctx)
        return {"record": record, "citations": []}

    async def read(self, request: dict[str, Any], ctx: TrustedExecutionContext) -> dict[str, Any]:
        validate_contract("ReferencesReadRequest", request)
        if "cursor" in request:
            raise CapabilityUnavailable("context.reference_pagination")
        ref = from_wire(Ref, request["reference"])
        record = (await self.resolve(ref, ctx))["record"]
        pin = from_wire(Ref, record["content_ref"])
        reading = await self.sources.read(pin, "pinned", ctx)
        location = (
            from_wire(Location, request["location"])
            if "location" in request
            else pin.location or Location(kind="whole")
        )
        text = reading.text
        if pin.location is not None and pin.location != location:
            raise reject(
                "location_stale", "Requested location differs from the registered slice", 410
            )
        if pin.location is None and location.wire() != {"kind": "whole"}:
            if (
                location.kind != "text_span"
                or set(location.wire()) != {"kind", "start", "end"}
                or location.start is None
                or location.end is None
                or not 0 <= location.start <= location.end <= len(text)
            ):
                raise reject("location_stale", "Requested location is outside the read text", 410)
            text = text[location.start : location.end]
        await self.sources.recheck(pin, ctx)
        result = {"reference_ref": record["ref"], "text": text, "location": location.wire()}
        validate_contract("ReadResult", result)
        return result

    async def handle(self, request: dict[str, Any], ctx: TrustedExecutionContext) -> dict[str, Any]:
        async def operation() -> dict[str, Any]:
            validate_contract("InternalContextReferencesRequest", request)
            action = request["action"]
            if action == "register":
                # Registration happens in Composer's transaction, from actual readings.
                raise CapabilityUnavailable("context.arbitrary_reference_registration")
            if action == "read":
                result = await self.read(request["parameters"], ctx)
            else:
                result = await self.resolve(from_wire(Ref, request["parameters"]["reference"]), ctx)
            return {
                "kind": "ok",
                "payload": {"action": action, "result": result},
                "output_refs": [result["reference_ref"]]
                if action == "read"
                else [result["record"]["ref"]],
            }

        return await component_result(
            "ComponentContextReferencesResult", ctx, self.sources.guard, operation
        )

    async def resolve_runtime(
        self, request: dict[str, Any], ctx: TrustedExecutionContext
    ) -> dict[str, Any]:
        async def operation() -> dict[str, Any]:
            validate_contract("RefRequest", request)
            result = await self.resolve(from_wire(Ref, request["ref"]), ctx)
            return {"kind": "ok", "payload": result, "output_refs": [result["record"]["ref"]]}

        return await component_result(
            "RuntimeContextruntimeResolveReferenceResult", ctx, self.sources.guard, operation
        )
