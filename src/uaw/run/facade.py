"""Run entry point. Admission is durable; it does not pretend the Agent has executed."""

import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import (
    RecordTransaction,
    TransactionalStore,
    identifier,
    reference,
    timestamp,
)
from uaw.run.events import EventReader
from uaw.run.history import append_input
from uaw.run.state import validate_transition, validate_worker_transition
from uaw.shared.configuration import ConfigurationService
from uaw.shared.contracts import JsonObject, Principal, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, DomainError, error_result, reject
from uaw.shared.schema import ContractViolation, validate_contract
from uaw.shared.stores import StoreConflict, StoreMissing

Payload = dict[str, Any]
DEFAULT_LIMITS = {
    "input_tokens": 100000,
    "output_tokens": 16000,
    "model_calls": 16,
    "tool_calls": 32,
    "child_agents": 4,
    "wall_time_ms": 3600000,
    "money": "5.000000",
    "currency": "USD",
}


def zero_resources(currency: str) -> Payload:
    return {
        **dict.fromkeys((k for k in DEFAULT_LIMITS if k not in ("money", "currency")), 0),
        "money": "0",
        "currency": currency,
    }


class RunFacade:
    def __init__(
        self, store: PostgresRecordStore, configuration: ConfigurationService, events: EventReader
    ) -> None:
        self.store = store
        self.transactions = TransactionalStore(store.database)
        self.configuration = configuration
        self.events = events

    async def create(
        self, request: JsonObject, meta: RequestMeta, ctx: TrustedExecutionContext
    ) -> JsonObject:
        try:
            return await self._create(request, meta, ctx)
        except ContractViolation:
            result = error_result(
                reject("request_invalid", "Runtime request does not match its contract")
            )
        except DomainError as exc:
            result = error_result(exc)
        validate_contract("RuntimeRunruntimeCreateResult", result)
        return result

    async def _create(
        self, request: JsonObject, meta: RequestMeta, ctx: TrustedExecutionContext
    ) -> JsonObject:
        validate_contract("RunCreateRequest", request)
        if ctx.run_id or ctx.scope.conversation_id != request.get("conversation_id"):
            raise reject(
                "run_creation_scope_denied",
                "Run admission requires an ingress conversation scope",
                403,
                "authorization",
            )
        if datetime.fromisoformat(ctx.deadline.replace("Z", "+00:00")) <= datetime.now(UTC):
            raise reject(
                "admission_deadline_expired", "Ingress deadline has passed", 409, "timeout"
            )
        original = request["input"]
        if (
            not isinstance(original, dict)
            or original["conversation_id"] != request["conversation_id"]
        ):
            raise reject(
                "input_scope_denied",
                "Original input does not belong to this conversation",
                403,
                "authorization",
            )
        if "task_ref" in request:
            raise CapabilityUnavailable("cross_conversation_task_revision")
        submission = {
            "conversation_id": request["conversation_id"],
            "text": original["text"],
            "attachment_refs": original["attachment_refs"],
            "budget": request["budget"],
        }
        result = await self.submit(
            ctx.principal,
            submission,
            meta,
            execution_deadline=ctx.deadline,
            original_input=original,
        )
        wire = {"kind": "ok", "payload": result, "revision": result["revision"], "output_refs": []}
        validate_contract("RuntimeRunruntimeCreateResult", wire)
        return wire

    async def create_conversation(
        self, actor: Principal, request: Payload, meta: RequestMeta
    ) -> Payload:
        validate_contract("ConversationsCreateRequest", request)
        if "project_ref" in request:
            raise CapabilityUnavailable("project_binding")
        if request.get("approval_mode", "manual") != "manual":
            raise CapabilityUnavailable("non_manual_approval")
        if (
            request["memory_policy"]["read_enabled"]
            or request["memory_policy"]["contribute_enabled"]
        ):
            raise CapabilityUnavailable("memory")
        if request["model_choice"]["mode"] != "explicit":
            raise CapabilityUnavailable("automatic_model_routing")

        async def write(tx: RecordTransaction) -> Payload:
            config = await self.configuration.current()
            await self.configuration.require_model(request["model_choice"]["model_id"], config)
            conversation_id = identifier("conversation")
            now = timestamp()
            # A real authenticated configuration action supplies the human-source proof.
            source: Payload = {
                "id": identifier("action"),
                "conversation_id": conversation_id,
                "turn_id": identifier("configuration-turn"),
                "text": json.dumps(request["model_choice"], ensure_ascii=False, sort_keys=True),
                "attachment_refs": [],
                "created_at": now,
            }
            await tx.write("inputs", source["id"], "InputRecord", source)
            policy = {
                "id": identifier("model-policy"),
                "revision": 1,
                "mode": "explicit",
                "fixed_model_id": request["model_choice"]["model_id"],
                "allowed_model_ids": [],
                "source_input_ref": reference("input", source["id"]),
            }
            await tx.write("model.policies", policy["id"], "ResolvedModelPolicy", policy)
            conversation = {
                "id": conversation_id,
                "owner_id": actor.id,
                "title": request["title"],
                "revision": 1,
                "model_policy_ref": reference("policy", policy["id"]),
                "memory_policy": {
                    **request["memory_policy"],
                    "scope": {"conversation_id": conversation_id},
                },
                "created_at": now,
                "updated_at": now,
                "approval_mode": "manual",
            }
            await tx.write("conversations", conversation_id, "Conversation", conversation)
            return conversation

        return await self.transactions.execute(
            actor, "conversations.create", meta, {"action": "create", "request": request}, write
        )

    async def submit(
        self,
        actor: Principal,
        request: Payload,
        meta: RequestMeta,
        *,
        execution_deadline: str | None = None,
        original_input: Payload | None = None,
        on_admitted: Callable[[RecordTransaction, Payload], Awaitable[None]] | None = None,
    ) -> Payload:
        validate_contract("TurnsSubmitRequest", request)
        if request["attachment_refs"]:
            raise CapabilityUnavailable("attachment_ingestion")
        if "task_id" in request:
            raise CapabilityUnavailable("cross_conversation_task_revision")
        conversation_id = request["conversation_id"]
        await self.store.get(actor, "conversations", conversation_id)

        async def write(tx: RecordTransaction) -> Payload:
            conversation = await tx.load("conversations", conversation_id)
            if (
                meta.expected_revision is not None
                and meta.expected_revision != conversation.revision
            ):
                raise StoreConflict()
            config = await self.configuration.current()
            policy = (
                await tx.load("model.policies", conversation.payload["model_policy_ref"]["id"])
            ).payload
            await self.configuration.require_model(policy["fixed_model_id"], config)
            run_id, task_id, turn_id = identifier("run"), identifier("task"), identifier("turn")
            original = await append_input(
                tx,
                conversation_id,
                original_input["turn_id"] if original_input else turn_id,
                request["text"],
                [],
                run_id=run_id,
                original=original_input,
            )
            default_deadline = datetime.now(UTC) + timedelta(hours=1)
            if execution_deadline:
                default_deadline = min(
                    default_deadline,
                    datetime.fromisoformat(execution_deadline.replace("Z", "+00:00")),
                )
            budget = request.get("budget") or {
                "limits": dict(DEFAULT_LIMITS),
                "max_steps": 64,
                "max_depth": 2,
                "deadline": default_deadline.isoformat(),
            }
            self._budget(budget)
            if (
                execution_deadline
                and datetime.fromisoformat(budget["deadline"].replace("Z", "+00:00"))
                > default_deadline
            ):
                raise reject(
                    "budget_deadline_invalid", "Budget exceeds the ingress deadline", 422, "budget"
                )
            run = {
                "id": run_id,
                "task_id": task_id,
                "conversation_id": conversation_id,
                "revision": 1,
                "status": "queued",
                "budget": budget,
                "created_at": timestamp(),
            }
            await tx.write("runs", run_id, "RunRecord", run)
            task = {
                "id": task_id,
                "revision": 1,
                "conversation_refs": [reference("conversation", conversation_id)],
                "active_run_refs": [reference("run", run_id)],
                "artifact_refs": [],
                "created_at": run["created_at"],
            }
            await tx.write("tasks", task_id, "TaskRecord", task)
            await tx.write(
                "run.input_sets",
                run_id,
                "RunInputState",
                {
                    "run_id": run_id,
                    "conversation_id": conversation_id,
                    "revision": 1,
                    "original_input_ref": reference("input", original["id"]),
                    "patch_refs": [],
                },
            )
            await tx.write(
                "run.bindings",
                run_id,
                "RunAdmissionBinding",
                {
                    "input_ref": reference("input", original["id"]),
                    "model_policy_ref": conversation.payload["model_policy_ref"],
                    "configuration_ref": reference(
                        "configuration", config["id"], config["revision"]
                    ),
                    "turn_id": original["turn_id"],
                },
            )
            ledger = {
                "id": run_id,
                "run_id": run_id,
                "revision": 1,
                "limits": budget["limits"],
                "held": zero_resources(budget["limits"]["currency"]),
                "used": zero_resources(budget["limits"]["currency"]),
                "billing_pending": False,
                "overdrawn": False,
                "cancel_requested": False,
                "deadline": budget["deadline"],
            }
            await tx.write("budget.ledgers", run_id, "RootBudgetLedger", ledger)
            await tx.write(
                "budget.reservations",
                f"root-{run_id}",
                "BudgetReservation",
                {
                    "id": f"root-{run_id}",
                    "estimates": budget["limits"],
                    "settled_usage_refs": [],
                    "status": "reserved",
                    "revision": 1,
                },
            )
            await tx.emit(conversation_id, "run.updated", run)
            if on_admitted is not None:
                await on_admitted(tx, run)
            return run

        return await self.transactions.execute(
            actor,
            f"conversation:{conversation_id}",
            meta,
            {
                "action": "submit",
                "request": request,
                "original_input": original_input,
                "expected": meta.expected_revision,
            },
            write,
        )

    @staticmethod
    def _budget(budget: Payload) -> None:
        validate_contract("Budget", budget)
        if "parent_reservation_ref" in budget:
            raise reject("root_budget_invalid", "A public turn cannot attach another budget")
        deadline = datetime.fromisoformat(budget["deadline"].replace("Z", "+00:00"))
        remaining = (deadline - datetime.now(UTC)).total_seconds()
        if (
            not 0 < remaining <= 3600
            or not 1 <= budget["max_steps"] <= 64
            or budget["max_depth"] > 2
        ):
            raise reject(
                "budget_limit_invalid", "Budget exceeds development admission limits", 422, "budget"
            )
        limits = budget["limits"]
        if limits["currency"] != DEFAULT_LIMITS["currency"] or any(
            Decimal(str(limits[k])) > Decimal(str(DEFAULT_LIMITS[k]))
            for k in limits
            if k != "currency"
        ):
            raise reject(
                "budget_limit_invalid", "Budget exceeds development resource limits", 422, "budget"
            )

    async def get_run(self, actor: Principal, run_id: str) -> Payload:
        return (await self.store.get(actor, "runs", run_id)).payload

    async def create_execution_item(
        self, actor: Principal, run_id: str, kind: str, meta: RequestMeta
    ) -> Payload:
        if kind not in ("agent_message", "understanding", "plan"):
            raise CapabilityUnavailable("interaction_producer")
        initial = await self.get_run(actor, run_id)

        async def write(tx: RecordTransaction) -> Payload:
            run = await tx.load("runs", run_id)
            ledger = await tx.load("budget.ledgers", run_id)
            if (
                run.payload["status"] in ("completed", "failed", "cancelled")
                or ledger.payload["cancel_requested"]
            ):
                raise reject(
                    "run_not_writable",
                    "Run is not accepting new interaction items",
                    409,
                    "cancelled",
                )
            now = timestamp()
            item = {
                "id": identifier("item"),
                "conversation_id": initial["conversation_id"],
                "run_id": run_id,
                "type": kind,
                "status": "pending",
                "revision": 1,
                "text": "",
                "resource_refs": [],
                "created_at": now,
                "updated_at": now,
            }
            await tx.write("items", item["id"], "InteractionItem", item)
            await tx.emit(
                initial["conversation_id"],
                "item.updated",
                item,
                item_ref=reference("item", item["id"]),
            )
            return item

        return await self.transactions.execute(
            actor,
            f"conversation:{initial['conversation_id']}",
            meta,
            {"action": "item.create", "run_id": run_id, "kind": kind},
            write,
        )

    async def update_execution_item(
        self, actor: Principal, item_id: str, target: str, text: str, meta: RequestMeta
    ) -> Payload:
        initial = (await self.store.get(actor, "items", item_id)).payload
        if initial["type"] not in ("agent_message", "understanding", "plan"):
            raise reject(
                "immutable_user_item", "User input items cannot be rewritten", 403, "policy"
            )

        async def write(tx: RecordTransaction) -> Payload:
            row = await tx.load("items", item_id)
            if row.revision != meta.expected_revision:
                raise StoreConflict()
            ledger = await tx.load("budget.ledgers", initial["run_id"])
            if ledger.payload["cancel_requested"]:
                raise reject("cancel_requested", "Run has a cancellation request", 409, "cancelled")
            validate_transition(row.payload["status"], target, item=True)
            base = row.revision
            value = {
                **row.payload,
                "revision": base + 1,
                "status": target,
                "text": text,
                "updated_at": timestamp(),
            }
            await tx.write("items", item_id, "InteractionItem", value, base)
            await tx.emit(
                initial["conversation_id"],
                "item.updated",
                value,
                item_ref=reference("item", item_id, base + 1),
                base_revision=base,
                result_revision=base + 1,
            )
            return value

        return await self.transactions.execute(
            actor,
            f"conversation:{initial['conversation_id']}",
            meta,
            {
                "action": "item.update",
                "item_id": item_id,
                "target": target,
                "text": text,
                "expected": meta.expected_revision,
            },
            write,
        )

    async def advance(
        self, actor: Principal, run_id: str, target: str, meta: RequestMeta
    ) -> Payload:
        initial = await self.get_run(actor, run_id)

        async def write(tx: RecordTransaction) -> Payload:
            row = await tx.load("runs", run_id)
            if meta.expected_revision != row.revision:
                raise StoreConflict()
            ledger = await tx.load("budget.ledgers", run_id)
            if ledger.payload["cancel_requested"]:
                raise reject("cancel_requested", "Run has a cancellation request", 409, "cancelled")
            validate_worker_transition(row.payload["status"], target)
            base = row.revision
            value = {**row.payload, "revision": base + 1, "status": target}
            await tx.write("runs", run_id, "RunRecord", value, base)
            await tx.emit(
                value["conversation_id"],
                "run.updated",
                value,
                base_revision=base,
                result_revision=base + 1,
            )
            return value

        return await self.transactions.execute(
            actor,
            f"conversation:{initial['conversation_id']}",
            meta,
            {
                "action": "advance",
                "run_id": run_id,
                "target": target,
                "expected": meta.expected_revision,
            },
            write,
        )

    async def control(self, actor: Principal, request: Payload, meta: RequestMeta) -> Payload:
        validate_contract("RunsControlRequest", request)
        control = request["control"]
        if control["mode"] != "cancel" or control["preserve_refs"] or "input_ref" in control:
            raise CapabilityUnavailable("user_control_mode")
        initial = await self.get_run(actor, request["run_id"])

        async def write(tx: RecordTransaction) -> Payload:
            run = await tx.load("runs", initial["id"])
            if meta.expected_revision != run.revision:
                raise StoreConflict()
            if run.payload["status"] in ("completed", "failed", "cancelled"):
                raise reject("run_terminal", "Run is already terminal", 409, "conflict")
            ledger = await tx.load("budget.ledgers", run.resource_id)
            await tx.write(
                "budget.ledgers",
                run.resource_id,
                "RootBudgetLedger",
                {**ledger.payload, "revision": ledger.revision + 1, "cancel_requested": True},
                ledger.revision,
            )
            base = run.revision
            value = {**run.payload, "revision": base + 1}
            stopped = run.payload["status"] == "queued"
            if stopped:
                validate_transition("queued", "cancelled")
                value.update(status="cancelled", outcome="cancelled", ended_at=timestamp())
                root = await tx.load("budget.reservations", f"root-{run.resource_id}")
                await tx.write(
                    "budget.reservations",
                    root.resource_id,
                    "BudgetReservation",
                    {**root.payload, "revision": root.revision + 1, "status": "released"},
                    root.revision,
                )
                task = await tx.load("tasks", value["task_id"])
                await tx.write(
                    "tasks",
                    task.resource_id,
                    "TaskRecord",
                    {**task.payload, "revision": task.revision + 1, "active_run_refs": []},
                    task.revision,
                )
            await tx.write("runs", run.resource_id, "RunRecord", value, base)
            await tx.emit(
                value["conversation_id"],
                "run.updated",
                value,
                base_revision=base,
                result_revision=base + 1,
            )
            now = timestamp()
            source = {
                "id": identifier("control-input"),
                "conversation_id": value["conversation_id"],
                "turn_id": identifier("control-turn"),
                "text": control["reason"],
                "attachment_refs": [],
                "created_at": now,
            }
            await tx.write("inputs", source["id"], "InputRecord", source)
            item = {
                "id": identifier("item"),
                "conversation_id": value["conversation_id"],
                "run_id": value["id"],
                "type": "user_control",
                "status": "completed",
                "revision": 1,
                "text": control["reason"],
                "resource_refs": [reference("input", source["id"])],
                "created_at": now,
                "updated_at": now,
            }
            await tx.write("items", item["id"], "InteractionItem", item)
            await tx.emit(
                value["conversation_id"],
                "item.updated",
                item,
                item_ref=reference("item", item["id"]),
            )
            return {
                "operation_id": meta.request_id,
                "status": "completed" if stopped else "accepted",
                "related_refs": [reference("run", run.resource_id, base + 1)],
            }

        return await self.transactions.execute(
            actor,
            f"conversation:{initial['conversation_id']}",
            meta,
            {"action": "control", "request": request, "expected": meta.expected_revision},
            write,
        )

    async def append_requirement(
        self, actor: Principal, run_id: str, text: str, meta: RequestMeta
    ) -> Payload:
        """Internal authenticated user adapter; not an LLM tool or full steer protocol."""
        if actor.kind != "user":
            raise reject("user_source_required", "Requirements must come from a user adapter", 403)
        if not isinstance(text, str) or not text.strip() or len(text.encode()) > 65536:
            raise reject("input_invalid", "A bounded non-empty requirement is required")
        initial = await self.get_run(actor, run_id)

        async def write(tx: RecordTransaction) -> Payload:
            run = await tx.load("runs", run_id)
            try:
                state = await tx.load("run.input_sets", run_id)
            except StoreMissing as exc:
                raise reject(
                    "intent_input_set_unavailable",
                    "This Run predates source-set tracking; submit a new turn",
                    503,
                    "dependency",
                ) from exc
            ledger = await tx.load("budget.ledgers", run_id)
            if state.revision != meta.expected_revision:
                raise StoreConflict()
            if (
                run.payload["status"] not in ("preparing", "running")
                or ledger.payload["cancel_requested"]
            ):
                raise reject("run_not_editable", "Run is not accepting requirement updates", 409)
            if datetime.fromisoformat(
                run.payload["budget"]["deadline"].replace("Z", "+00:00")
            ) <= datetime.now(UTC):
                raise reject(
                    "intent_deadline_expired",
                    "Requirement update deadline has passed",
                    409,
                    "timeout",
                )
            if len(state.payload["patch_refs"]) >= 16:
                raise reject("input_patch_limit", "Requirement update limit reached")
            originals = [state.payload["original_input_ref"], *state.payload["patch_refs"]]
            size = len(text.encode())
            for ref in originals:
                source_row = await tx.load("inputs", ref["id"])
                size += len(source_row.payload["text"].encode())
            if size > 65536:
                raise reject(
                    "intent_input_too_large", "Understanding source set exceeds 64 KiB", 413
                )
            source = await append_input(
                tx, initial["conversation_id"], identifier("patch-turn"), text, [], run_id=run_id
            )
            value = {
                **state.payload,
                "revision": state.revision + 1,
                "patch_refs": [*state.payload["patch_refs"], reference("input", source["id"])],
            }
            await tx.write("run.input_sets", run_id, "RunInputState", value, state.revision)
            # Old frame records remain immutable history; current pointers are invalidated.
            for namespace, record_id, schema in (
                ("runs", run_id, "RunRecord"),
                ("tasks", run.payload["task_id"], "TaskRecord"),
            ):
                row = await tx.load(namespace, record_id)
                changed = {**row.payload, "revision": row.revision + 1}
                changed.pop("frame_ref", None)
                await tx.write(namespace, record_id, schema, changed, row.revision)
                if namespace == "runs":
                    await tx.emit(
                        initial["conversation_id"],
                        "run.updated",
                        changed,
                        base_revision=row.revision - 1,
                        result_revision=row.revision,
                    )
            try:
                understanding = await tx.load("items", "understanding-" + run.payload["task_id"])
            except StoreMissing:
                understanding = None
            if understanding:
                item_base = understanding.revision
                item = {
                    **understanding.payload,
                    "revision": item_base + 1,
                    "status": "waiting",
                    "updated_at": timestamp(),
                }
                await tx.write(
                    "items", understanding.resource_id, "InteractionItem", item, item_base
                )
                await tx.emit(
                    initial["conversation_id"],
                    "item.updated",
                    item,
                    item_ref=reference("item", understanding.resource_id, item_base + 1),
                    base_revision=item_base,
                    result_revision=item_base + 1,
                )
            return value

        return await self.transactions.execute(
            actor,
            f"conversation:{initial['conversation_id']}",
            meta,
            {
                "action": "run.append_requirement",
                "run_id": run_id,
                "text": text,
                "expected": meta.expected_revision,
            },
            write,
        )
