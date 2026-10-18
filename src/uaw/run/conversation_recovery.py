"""Recover durable accepted input without replaying a model or Tool invocation.

Only negative retry timing is kept in memory. Accepted patches and original job
records are authoritative across restarts; the owning resumer checks every grant.
"""

import asyncio
import json
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from time import monotonic
from typing import Any

from sqlalchemy import and_, exists, or_, select
from sqlalchemy.orm import aliased

from uaw.agent.contracts import identifier
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import (
    RecordTransaction,
    TransactionalStore,
    reference,
    timestamp,
)
from uaw.run.conversation_control import PATCHES, TERMINAL, ConversationControls
from uaw.run.jobs import JOBS
from uaw.shared.contracts import Principal
from uaw.shared.errors import DomainError, reject
from uaw.shared.observability import report_request_failure
from uaw.shared.stores import StoreMissing

Payload = dict[str, Any]
Resume = Callable[[Principal, str], Awaitable[bool]]
FAILURES = "run.continuation.recovery.failures"


def feedback(failure: Payload) -> str:
    code, category = failure["code"], failure["category"]
    if category == "unknown_effect" or code == "conversation_effect_pending":
        return "补充已保存，正在核对上一次调用的最终状态；不会重复执行。"
    if category in ("authentication", "authorization") or "identity" in code or "owner" in code:
        return "补充已保存。当前登录或权限无法继续原任务，请重新连接后查看。"
    if category in ("timeout", "budget") or "deadline" in code:
        return "补充已保存，当前执行额度或有效期不足，任务尚未恢复。"
    if category == "dependency":
        return "补充已保存，恢复任务所需的执行组件暂不可用。"
    return "补充已保存，任务暂未恢复；原记录已保留。"


async def close_notices(tx: RecordTransaction, run_id: str) -> None:
    """Join a proven terminal commit; never imply that a pending patch applied."""
    run = await tx.load("runs", run_id)
    status = run.payload["status"]
    if status not in TERMINAL:
        raise reject("conversation_notice_terminal", "Actual terminal Run required", 409)
    rows = list(
        await tx.session.scalars(
            select(RecordRow).where(
                RecordRow.principal_id == tx.owner,
                RecordRow.namespace == "items",
                RecordRow.deleted.is_(False),
                RecordRow.resource_id.startswith("recovery-notice-"),
                RecordRow.payload["run_id"].astext == run_id,
                RecordRow.payload["status"].astext == "waiting",
            )
        )
    )
    for row in rows:
        item = {
            **row.payload,
            "revision": row.revision + 1,
            "status": "cancelled" if status == "cancelled" else "completed",
            "text": {
                "completed": "任务已完成，补充和执行记录已保留。",
                "failed": "本次任务未能完成，补充和失败记录已保留。",
                "cancelled": "任务已停止，补充和执行记录已保留。",
            }[status],
            "updated_at": timestamp(),
        }
        await tx.write("items", row.resource_id, "InteractionItem", item, row.revision)
        await tx.emit(
            run.payload["conversation_id"],
            "item.updated",
            item,
            item_ref=reference("item", row.resource_id, item["revision"]),
        )


class ConversationRecovery:
    def __init__(
        self,
        records: PostgresRecordStore,
        *,
        owner_id: str,
        resume: Resume,
        batch_size: int = 8,
        now: Callable[[], float] = monotonic,
    ) -> None:
        if not 1 <= batch_size <= 16:
            raise ValueError("Bounded recovery scan required")
        self.records, self.owner_id, self.resume = records, owner_id, resume
        self.batch_size, self.now = batch_size, now
        self.controls = ConversationControls(records)
        self.transactions = TransactionalStore(records.database)
        self.backoff: OrderedDict[tuple[str, str, int], tuple[int, float]] = OrderedDict()
        self.active: set[tuple[str, str, int]] = set()
        self.cursor = ""
        self.scan_after = 0.0

    def signal(self, actor: Principal, run_id: str) -> None:
        """Only nudge a bounded persisted scan; ingress never executes the model."""
        if actor.kind != "user" or actor.id != self.owner_id:
            raise reject("conversation_recovery_owner", "Original queue user required", 403)
        self.scan_after = 0.0

    async def notify(self, actor: Principal, run_id: str) -> bool:
        """Best effort AFTER durable acceptance; failure must not erase its receipt."""
        if actor.kind != "user" or actor.id != self.owner_id:
            raise reject("conversation_recovery_owner", "Original queue user required", 403)
        view = await self.controls.view(actor, run_id)
        if view.run["status"] in TERMINAL:
            return False
        job = await self.records.get(actor, JOBS, run_id)
        if job.payload["principal"] != actor.wire():
            raise reject("conversation_recovery_session", "Original full session required", 403)
        key = (actor.auth_session_id, run_id, view.input_revision)
        prior = self.backoff.get(key)
        if key in self.active or len(self.active) >= 8 or prior and prior[1] > self.now():
            return False
        self.active.add(key)
        failure: Payload | None = None
        try:
            try:
                async with asyncio.timeout(15):
                    woken = await self.resume(actor, run_id)
            except DomainError as exc:
                failure = exc.failure.wire()
                woken = False
            except Exception as exc:
                report_request_failure("conversation.recovery", type(exc).__name__)
                failure = reject(
                    "conversation_recovery_incomplete",
                    "Recovery did not finish; original input retained",
                    503,
                    "infrastructure",
                ).failure.wire()
                woken = False
            if woken:
                self.backoff.pop(key, None)
                await self.notice(actor, run_id, view.input_revision, None)
            else:
                attempts = (prior[0] if prior else 0) + 1
                self.backoff[key] = attempts, self.now() + min(30, 2 ** min(attempts, 5))
                self.backoff.move_to_end(key)
                while len(self.backoff) > 256:
                    self.backoff.popitem(last=False)
                if failure is not None:
                    await self.notice(actor, run_id, view.input_revision, failure)
            return woken
        finally:
            self.active.discard(key)

    async def notice(
        self, actor: Principal, run_id: str, epoch: int, failure: Payload | None
    ) -> None:
        key = identifier("recovery-notice-", {"run": run_id, "input_revision": epoch})

        async def write(tx: RecordTransaction) -> Payload:
            run = await self.controls.owned(tx, actor, run_id)
            inputs = await tx.load("run.input_sets", run_id)
            job = await tx.load(JOBS, run_id)
            if inputs.revision != epoch:
                return {}  # Do not label a newer correction using an older attempt.
            if failure and (run["status"] in TERMINAL or job.payload["state"] != "blocked"):
                return {}
            try:
                previous = await tx.load("items", key)
            except StoreMissing:
                previous = None
            if failure is None and previous is None:
                return {}
            if failure:
                try:
                    original = await tx.load(FAILURES, key)
                except StoreMissing:
                    original = None
                if original is None or original.payload != failure:
                    await tx.write(
                        FAILURES, key, "Failure", failure, original.revision if original else 0
                    )
            text = feedback(failure) if failure else "已接续原任务，正在处理你的补充。"
            if failure is None and run["status"] in TERMINAL:
                text = "任务已结束，补充和执行记录已保留。"
            status = "waiting" if failure else "completed"
            if (
                previous
                and previous.payload["text"] == text
                and previous.payload["status"] == status
            ):
                return {}
            now = timestamp()
            item = {
                "id": key,
                "conversation_id": run["conversation_id"],
                "run_id": run_id,
                "type": "user_control",
                "status": status,
                "revision": previous.revision + 1 if previous else 1,
                "text": text,
                "resource_refs": inputs.payload["patch_refs"],
                "created_at": previous.payload["created_at"] if previous else now,
                "updated_at": now,
            }
            await tx.write(
                "items", key, "InteractionItem", item, previous.revision if previous else 0
            )
            await tx.emit(
                run["conversation_id"],
                "item.updated",
                item,
                item_ref=reference("item", key, item["revision"]),
            )
            return {}

        try:
            await self.transactions.inspect(
                actor, await self.controls.aggregate(actor, run_id), write
            )
        except Exception as exc:
            # Durable accepted input remains the restart signal even if feedback
            # storage fails; do not make the caller resubmit that original input.
            report_request_failure("conversation.recovery_notice", type(exc).__name__)

    async def scan(self) -> bool:
        if self.scan_after > self.now():
            return False
        self.scan_after = self.now() + 2
        job, run, patch, decision = (aliased(RecordRow) for _ in range(4))
        query = (
            select(job.payload)
            .join(
                run,
                and_(
                    run.principal_id == job.principal_id,
                    run.namespace == "runs",
                    run.resource_id == job.resource_id,
                    run.deleted.is_(False),
                ),
            )
            .where(
                job.principal_id == self.owner_id,
                job.namespace == JOBS,
                job.deleted.is_(False),
                job.payload["state"].astext == "blocked",
                run.payload["status"].astext.in_(("preparing", "running", "waiting_for_user")),
                or_(
                    exists(
                        select(patch.resource_id).where(
                            patch.principal_id == job.principal_id,
                            patch.namespace == PATCHES,
                            patch.deleted.is_(False),
                            patch.payload["run_id"].astext == job.resource_id,
                            patch.payload["state"].astext == "accepted",
                        )
                    ),
                    and_(
                        job.payload["stage"].astext == "delivery",
                        exists(
                            select(decision.resource_id).where(
                                decision.principal_id == job.principal_id,
                                decision.namespace == "run.completion.acceptance",
                                decision.resource_id == job.payload["proposal_ref"]["id"].astext,
                                decision.deleted.is_(False),
                                decision.payload["decision"].astext == "accept",
                            )
                        ),
                    ),
                ),
            )
            .order_by(job.resource_id)
            .limit(self.batch_size)
        )
        async with self.records.database.sessions() as sql:
            rows: list[Payload] = list(
                await sql.scalars(query.where(job.resource_id > self.cursor))
            )
            if not rows and self.cursor:
                self.cursor = ""
                rows = list(await sql.scalars(query))
        woken = False
        for value in rows:
            self.cursor = value["run_id"]
            actor = Principal.model_validate_json(json.dumps(value["principal"]))
            try:
                woken = await self.notify(actor, value["run_id"]) or woken
            except DomainError:
                continue  # A source changed after selection; the owning gate decides.
            except Exception as exc:
                report_request_failure("conversation.recovery_scan", type(exc).__name__)
        return woken
