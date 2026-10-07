"""Run-owned Context adapters; references never grant access to other conversations."""

import hashlib
from datetime import UTC, datetime

from uaw.context.contracts import Reading, from_wire
from uaw.context.seed import revision
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.run.permissions import ExecutionPolicyResolver, require_snapshot
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, DomainError, reject
from uaw.shared.ports import ExecutionPolicyPort


class RunContextSources:
    def __init__(
        self, store: PostgresRecordStore, permissions: ExecutionPolicyPort | None = None
    ) -> None:
        self.store = store
        self.permissions = permissions or ExecutionPolicyResolver(store)

    async def is_cancelled(self, ctx: TrustedExecutionContext) -> bool:
        if not ctx.run_id:
            raise CapabilityUnavailable("context.preview_authority")
        run = (await self.store.get(ctx.principal, "runs", ctx.run_id)).payload
        if (
            run["conversation_id"] != ctx.scope.conversation_id
            or (ctx.task_id and ctx.task_id != run["task_id"])
            or (ctx.scope.task_id and ctx.scope.task_id != run["task_id"])
            or ctx.scope.project_id is not None
        ):
            raise reject("permission_denied", "Context source is outside the Run scope", 403)
        ledger = (await self.store.get(ctx.principal, "budget.ledgers", ctx.run_id)).payload
        if ledger["cancel_requested"] or run["status"] == "cancelled":
            return True
        if run["status"] not in ("preparing", "running"):
            raise reject("context_run_unavailable", "Run is not active", 409)
        if datetime.fromisoformat(run["budget"]["deadline"].replace("Z", "+00:00")) <= datetime.now(
            UTC
        ):
            raise reject("deadline_exceeded", "Run deadline expired", 422, "timeout")
        return False

    async def authorize(self, ctx: TrustedExecutionContext) -> None:
        if await self.is_cancelled(ctx):
            raise reject("cancelled", "Run has been cancelled", 422, "cancelled")
        if datetime.fromisoformat(ctx.deadline.replace("Z", "+00:00")) <= datetime.now(UTC):
            raise reject("deadline_exceeded", "Context deadline expired", 422, "timeout")
        if not set(ctx.scope.capabilities).intersection(
            {"model.generate", "intent.understand", "context.build"}
        ):
            raise reject("permission_denied", "Current policy denies Context source access", 403)
        try:
            snapshot = await self.permissions.resolve(ctx)
            require_snapshot(snapshot, ctx)
        except DomainError as exc:
            if exc.failure.code == "execution_policy_stale":
                raise reject(
                    "context_capability_stale", "Execution permission changed", 412
                ) from None
            raise

    async def _reading(self, ref: Ref, ctx: TrustedExecutionContext) -> Reading:
        await self.authorize(ctx)
        state = (await self.store.get(ctx.principal, "run.input_sets", ctx.run_id or "")).payload
        binding = (await self.store.get(ctx.principal, "run.bindings", ctx.run_id or "")).payload
        if (
            state["run_id"] != ctx.run_id
            or state["conversation_id"] != ctx.scope.conversation_id
            or state["original_input_ref"] != binding["input_ref"]
        ):
            raise reject("source_changed", "Run input set no longer matches its binding", 410)
        pins = (state["original_input_ref"], *state["patch_refs"])
        if not any(
            (pin["kind"], pin["id"], pin["version"]) == (ref.kind, ref.id, ref.version)
            for pin in pins
        ):
            raise reject("permission_denied", "Input is not in this Run's admitted source set", 403)
        value = (
            await self.store.get(
                ctx.principal, "inputs", ref.id, revision=revision(ref.wire(), "input")
            )
        ).payload
        if value["conversation_id"] != ctx.scope.conversation_id:
            raise reject("permission_denied", "Input belongs to another conversation", 403)
        text = value["text"]
        location = ref.location
        if location is not None:
            if location.kind == "text_span" and set(location.wire()) == {"kind", "start", "end"}:
                assert location.start is not None and location.end is not None
                if not 0 <= location.start <= location.end <= len(text):
                    raise reject("source_changed", "Text span is outside the fixed source", 410)
                text = text[location.start : location.end]
            elif location.wire() != {"kind": "whole"}:
                raise CapabilityUnavailable("context.input_location")
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if ref.content_hash is not None and ref.content_hash != content_hash:
            raise reject("source_changed", "Input text does not match its pinned hash", 410)
        actual = {key: ref.wire()[key] for key in ("kind", "id", "version")}
        if location is not None:
            actual["location"] = location.wire()
        actual["content_hash"] = content_hash
        return Reading(from_wire(Ref, actual), text, kind="user_input", trust="user", required=True)

    async def check(self, ref: Ref, ctx: TrustedExecutionContext) -> None:
        await self._reading(ref, ctx)

    async def read(self, ref: Ref, revision_policy: str, ctx: TrustedExecutionContext) -> Reading:
        if revision_policy != "pinned":
            raise CapabilityUnavailable("context.run_input_latest")
        return await self._reading(ref, ctx)
