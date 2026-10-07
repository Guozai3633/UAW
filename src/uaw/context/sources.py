"""Authorized source resolution. No cache, persistence or synthetic reference IDs."""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime
from typing import Any

from uaw.context.contracts import Reading, SourcesRequest, digest, from_wire, ref_key
from uaw.context.ports import Cancellation, Reader
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, DomainError, error_result, reject
from uaw.shared.schema import ContractViolation, validate_contract


class Guard:
    def __init__(self, cancellation: Cancellation | None) -> None:
        self.cancellation = cancellation

    @staticmethod
    def remaining(ctx: TrustedExecutionContext) -> float:
        deadline = datetime.fromisoformat(ctx.deadline.replace("Z", "+00:00"))
        return (deadline - datetime.now(UTC)).total_seconds()

    async def check(self, ctx: TrustedExecutionContext) -> None:
        if ctx.task_id is not None and ctx.task_id != ctx.scope.task_id:
            raise reject("permission_denied", "Task does not match the trusted scope", 403)
        if self.remaining(ctx) <= 0:
            raise reject("deadline_exceeded", "Context deadline expired", 422, "timeout")
        if self.cancellation is None:
            raise CapabilityUnavailable("context.cancellation_reader")
        if await self.cancellation.is_cancelled(ctx):
            raise reject("cancelled", "Context operation cancelled", 422, "cancelled")


async def component_result(
    schema: str,
    ctx: TrustedExecutionContext,
    guard: Guard,
    operation: Callable[[], Awaitable[dict[str, Any]]],
) -> dict[str, Any]:
    try:
        async with asyncio.timeout(max(0, guard.remaining(ctx))):
            await guard.check(ctx)
            result = await operation()
            await guard.check(ctx)
    except ContractViolation, ValueError, TypeError:
        result = error_result(reject("schema_invalid", "Invalid context component input"))
    except DomainError as exc:
        result = error_result(exc)
    except TimeoutError:
        result = error_result(
            reject("deadline_exceeded", "Context deadline expired", 422, "timeout")
        )
    except asyncio.CancelledError:
        result = error_result(reject("cancelled", "Context operation cancelled", 422, "cancelled"))
    validate_contract(schema, result)
    return result


class SourceResolver:
    def __init__(self, readers: Mapping[str, Reader], guard: Guard) -> None:
        # Composition explicitly registers source kinds; no arbitrary URL/path reader.
        self.readers = dict(readers)
        self.guard = guard

    def reader(self, ref: Ref) -> Reader:
        adapter = self.readers.get(ref.kind)
        if adapter is None:
            raise CapabilityUnavailable(f"context.reader.{ref.kind}")
        return adapter

    async def recheck(self, ref: Ref, ctx: TrustedExecutionContext) -> None:
        await self.guard.check(ctx)
        await self.reader(ref).check(ref, ctx)
        await self.guard.check(ctx)

    async def read(self, ref: Ref, policy: str, ctx: TrustedExecutionContext) -> Reading:
        await self.recheck(ref, ctx)
        reading = await self.reader(ref).read(ref, policy, ctx)
        await self.guard.check(ctx)
        actual = reading.ref
        # Revalidate adapter output too; a frozen record is not a schema check.
        validate_contract("Ref", actual.wire())
        validate_contract("BlockKind", reading.kind)
        validate_contract("TrustLevel", reading.trust)
        if type(reading.required) is not bool:
            raise reject("schema_invalid", "Reader returned invalid preservation metadata")
        if actual.kind != ref.kind or actual.id != ref.id or actual.location != ref.location:
            raise reject("source_changed", "Reader returned a different source or location", 410)
        if policy == "pinned" and actual.version != ref.version:
            raise reject("source_changed", "Pinned source version changed", 410)
        text_hash = hashlib.sha256(reading.text.encode("utf-8")).hexdigest()
        if actual.content_hash != text_hash or (
            (policy == "pinned" or actual.version == ref.version)
            and ref.content_hash is not None
            and ref.content_hash != text_hash
        ):
            raise reject("source_changed", "Read content does not match the fixed hash", 410)
        if reading.trust == "external" and reading.kind in ("instruction", "skill", "user_input"):
            raise reject("permission_denied", "External data cannot become instructions", 403)
        # Recheck actual version after I/O: ACL may have been revoked during the read.
        await self.recheck(actual, ctx)
        return reading

    async def resolve(
        self, request: SourcesRequest, ctx: TrustedExecutionContext
    ) -> tuple[Reading, ...]:
        await self.guard.check(ctx)
        readings: list[Reading] = []
        seen: set[str] = set()
        for ref in request.source_refs:
            if ref_key(ref) not in seen:
                reading = await self.read(ref, request.source_revision_policy, ctx)
                if not any(ref_key(r.ref) == ref_key(reading.ref) for r in readings):
                    readings.append(reading)
                seen.add(ref_key(ref))
        for reading in readings:
            await self.recheck(reading.ref, ctx)
        return tuple(readings)

    async def handle(self, request: dict[str, Any], ctx: TrustedExecutionContext) -> dict[str, Any]:
        async def operation() -> dict[str, Any]:
            readings = await self.resolve(from_wire(SourcesRequest, request), ctx)
            refs = [reading.ref.wire() for reading in readings]
            return {
                "kind": "ok",
                "payload": {
                    "source_refs": refs,
                    "missing_refs": [],
                    "manifest": {
                        "version": "0.1",
                        "input_refs": refs,
                        "dependency_refs": [],
                        "content_hash": digest(refs),
                    },
                },
                "output_refs": refs,
            }

        return await component_result("ComponentContextSourcesResult", ctx, self.guard, operation)
