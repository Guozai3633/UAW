"""Immutable Runner source registration. Stored commands never authorize sending."""

import asyncio
import json
from collections.abc import Awaitable
from typing import Any

from uaw.infrastructure.db.records import PostgresRecordStore, parameter_hash
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore, reference
from uaw.run.permissions import require_snapshot
from uaw.run.runner_devices import AGGREGATE, DEVICES, RunnerDevices, instant
from uaw.shared.configuration import ConfigurationService
from uaw.shared.contracts import Principal, Ref, RequestMeta, TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.ports import (
    BudgetExecutionStatePort,
    ExecutionLeasePort,
    ExecutionPolicyPort,
    RunnerActionGatePort,
    RunnerCommandSigningPort,
    RunnerRootSourcePort,
)
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreConflict, StoreMissing
from uaw.tool.ledger import ToolLedger, action_key

Payload = dict[str, Any]
REQUESTS = "runner.requests"
TOOL_REQUESTS = "runner.tool.requests"
COMMANDS = "runner.commands"
ATTEMPTS = "runner.attempts"
READ_ACTIONS = {"file.read", "file.list"}


def pin(kind: str, identifier: str, payload: Payload) -> Payload:
    return {**reference(kind, identifier), "content_hash": parameter_hash(payload)}


def copy(data: Payload) -> Payload:
    result: Payload = json.loads(json.dumps(data, allow_nan=False))
    return result


async def require_none(operation: Awaitable[object], code: str) -> None:
    if await operation is not None:
        raise reject(code, "Authority source returned invalid data", 503)


class RunnerCommands:
    def __init__(
        self,
        store: PostgresRecordStore,
        devices: RunnerDevices,
        configuration: ConfigurationService,
        permissions: ExecutionPolicyPort,
        budgets: BudgetExecutionStatePort,
        leases: ExecutionLeasePort,
        *,
        roots: RunnerRootSourcePort | None = None,
        gate: RunnerActionGatePort | None = None,
        signer: RunnerCommandSigningPort | None = None,
    ) -> None:
        self.store, self.devices, self.configuration = store, devices, configuration
        self.permissions, self.budgets, self.leases = permissions, budgets, leases
        self.roots, self.gate, self.signer = roots, gate, signer
        self.transactions = TransactionalStore(store.database)

    async def _request(self, ref: Ref) -> Payload:
        if ref.kind == "tool_call":
            row = await self.store.get(self.devices.controller, TOOL_REQUESTS, ref.id)
            validate_contract("RunnerToolRequestRecord", row.payload)
            record = row.payload
            ctx = TrustedExecutionContext.model_validate_json(json.dumps(record["context"]))
            await self._tool_sources(record["call"], record["spec"], ctx)
            if (
                row.revision != 1
                or ref.wire() != pin("tool_call", row.resource_id, record["call"])
                or record["parameters"]
                != {"action": "file.read", "parameters": record["call"]["arguments"]}
            ):
                raise reject("runner_request_changed", "Original Tool request differs", 412)
            return {k: record[k] for k in ("id", "context", "parameters")}
        row = await self.store.get(self.devices.controller, REQUESTS, ref.id)
        validate_contract("RunnerRequestRecord", row.payload)
        if row.revision != 1 or ref.wire() != pin("check", row.resource_id, row.payload):
            raise reject("runner_request_changed", "Registered request differs from its pin", 412)
        return row.payload

    async def _tool_sources(
        self, call: Payload, spec: Payload, ctx: TrustedExecutionContext
    ) -> str:
        validate_contract("ValidatedCall", call)
        validate_contract("ToolSpec", spec)
        ledger = ToolLedger(self.store)
        fixed_call, fixed_spec, _ = await ledger.action(call["action_id"], ctx)
        original_context = await ledger.get("tool.attempt.contexts", ctx.attempt_id, ctx)
        key = action_key(ctx, call["action_id"])
        if (
            fixed_call != call
            or fixed_spec != spec
            or await ledger.attempt(ctx) != call
            or original_context != ctx.wire()
            or spec["id"] != "file.read"
            or call["tool_ref"]["id"] != spec["id"]
            or call["tool_ref"]["version"] != spec["version"]
            or call["tool_ref"].get("content_hash") != parameter_hash(spec)
        ):
            raise reject("runner_original_tool_denied", "Independent original Tool differs", 403)
        validate_contract("ToolFileReadInput", call["arguments"])
        return key

    async def register_tool_request(
        self,
        call: Payload,
        spec: Payload,
        ctx: TrustedExecutionContext,
        meta: RequestMeta,
        *,
        authenticated_service: Principal,
    ) -> Payload:
        self.devices.service(authenticated_service)
        key = await self._tool_sources(call, spec, ctx)
        record = {
            "id": key,
            "context": ctx.wire(),
            "parameters": {"action": "file.read", "parameters": copy(call["arguments"])},
            "call": copy(call),
            "spec": copy(spec),
        }
        self.workspace(record)
        await self._run(ctx)

        async def write(tx: RecordTransaction) -> Payload:
            await tx.write(TOOL_REQUESTS, key, "RunnerToolRequestRecord", record)
            return pin("tool_call", key, call)

        result = await self.transactions.execute(
            self.devices.controller,
            AGGREGATE,
            meta,
            {"action": "tool.request.register", "record": record},
            write,
        )
        await self._run(ctx)
        await self._request(Ref.model_validate(result))
        return result

    async def _tool_reservation(self, request: Payload, ref: Payload) -> Ref:
        if ref["kind"] != "tool_call":
            raise CapabilityUnavailable("runner.attempt_budget")
        ctx = TrustedExecutionContext.model_validate_json(json.dumps(request["context"]))
        ledger = ToolLedger(self.store)
        intent = await ledger.get("tool.dispatch.intents", ref["id"], ctx)
        reserved = await ledger.get("tool.budget.reserved", ctx.attempt_id, ctx)
        dispatched = await ledger.get("tool.budget.dispatched", ctx.attempt_id, ctx)
        spec = (await self.store.get(ctx.principal, "tool.specs", ref["id"])).payload
        if (
            intent is None
            or reserved is None
            or dispatched is None
            or intent["validated_action_ref"] != reference("tool_call", ref["id"])
            or intent["provider_binding_ref"] != spec["provider_ref"]
            or intent["reservation_ref"]
            != reference("reservation", reserved["id"], reserved["revision"])
            or dispatched["operation_id"] != ctx.operation_id
            or dispatched["status"] not in ("accepted", "unchanged")
        ):
            raise reject(
                "runner_original_budget_denied", "Original Tool dispatch budget missing", 403
            )
        return Ref.model_validate(intent["reservation_ref"])

    async def _run(self, ctx: TrustedExecutionContext) -> Payload:
        snapshot = require_snapshot(await self.permissions.resolve(ctx), ctx)
        if snapshot["feature_flag_refs"]:
            raise CapabilityUnavailable("runner.policy_flag_source")
        binding = (await self.store.get(ctx.principal, "run.bindings", ctx.run_id or "")).payload
        if (
            ctx.model_policy_ref is None
            or binding["model_policy_ref"] != ctx.model_policy_ref.wire()
        ):
            raise reject("runner_model_binding_changed", "Fixed user model differs", 412)
        return {"policy": snapshot, "binding": binding}

    def workspace(self, request: Payload) -> Ref:
        parameters = request["parameters"]
        action = parameters["action"]
        if action not in READ_ACTIONS:
            raise CapabilityUnavailable("runner.execution_D03")
        scope = request["context"]["scope"]
        if action not in scope["capabilities"]:
            raise reject("runner_capability_denied", "Required read capability is absent", 403)
        value = parameters["parameters"]
        if action == "file.read":
            workspace = Ref.model_validate(value["workspace_ref"])
        else:
            candidates = [
                r
                for r in scope["resource_refs"]
                if r["kind"] == "workspace" and r["id"] == value["workspace_id"]
            ]
            if len(candidates) != 1:
                raise reject("runner_workspace_ambiguous", "One fixed workspace is required", 403)
            workspace = Ref.model_validate(candidates[0])
        if workspace.kind != "workspace" or workspace.wire() not in scope["resource_refs"]:
            raise reject("runner_workspace_denied", "Workspace is outside the fixed scope", 403)
        return workspace

    async def register_request(
        self,
        request: Payload,
        meta: RequestMeta,
        ctx: TrustedExecutionContext,
        *,
        authenticated_service: Principal,
    ) -> Payload:
        self.devices.service(authenticated_service)
        validate_contract("RunnerRequestRegisterRequest", request)
        validate_contract("TrustedExecutionContext", ctx.wire())
        record = {
            "id": request["id"],
            "parameters": copy(request["parameters"]),
            "context": ctx.wire(),
        }
        self.workspace(record)
        await self._run(ctx)

        async def write(tx: RecordTransaction) -> Payload:
            await tx.write(REQUESTS, record["id"], "RunnerRequestRecord", record)
            return pin("check", record["id"], record)

        result = await self.transactions.execute(
            self.devices.controller,
            AGGREGATE,
            meta,
            {"action": "request.register", "record": record},
            write,
        )
        await self._run(ctx)
        await self._request(Ref.model_validate(result))
        return result

    async def _collect(self, record: Payload, actor: Principal) -> Payload:
        command = record["command"]
        request = await self._request(Ref.model_validate(command["request_ref"]))
        ctx = TrustedExecutionContext.model_validate_json(json.dumps(request["context"]))
        if (
            command["trusted_context"] != ctx.wire()
            or command["parameters"] != request["parameters"]
        ):
            raise reject(
                "runner_command_binding_denied", "Command differs from independent request", 403
            )
        workspace = self.workspace(request)
        device = await self.devices.current(
            record["device_ref"]["id"], authenticated_principal=actor
        )
        if (
            record["device_ref"]
            != {
                **reference("device", device["device_id"], device["revision"]),
                "content_hash": parameter_hash(device),
            }
            or device["source"]["owner"] != ctx.principal.wire()
        ):
            raise reject("runner_device_changed", "Device/owner binding changed", 412)
        run = await self._run(ctx)
        await self.configuration.require_capability(
            "local_files",
            run["binding"]["configuration_ref"],
            ctx.scope.wire(),
            implemented=True,
            boundary="call",
        )
        if self.roots is None or self.gate is None or self.signer is None:
            raise CapabilityUnavailable("runner.root_action_signing_sources")
        before = parameter_hash(request)
        await require_none(self.gate.check(copy(request), ctx), "runner_gate_protocol_invalid")
        if parameter_hash(request) != before:
            raise StoreConflict()
        root = copy(await self.roots.current(device["device_id"], workspace, ctx))
        validate_contract("RunnerRootSnapshot", root)
        if "root" in record and root != record["root"]:
            raise reject("runner_root_changed", "Registered root binding changed", 412)
        if (
            root["owner"] != ctx.principal.wire()
            or root["device_id"] != device["device_id"]
            or root["workspace_ref"] != workspace.wire()
            or request["parameters"]["action"] not in root["allowed_actions"]
            or not set(root["allowed_actions"]) <= READ_ACTIONS
        ):
            raise reject("runner_root_denied", "Actual root does not allow the request", 403)
        budget_ref = ctx.budget_reservation_ref
        if budget_ref is None:
            budget_ref = await self._tool_reservation(request, command["request_ref"])
        budget = copy(await self.budgets.execution_state(budget_ref.id, ctx))
        validate_contract("BudgetExecutionSnapshot", budget)
        attempt = budget["attempt"]
        if (
            attempt["reservation_ref"] != budget_ref.wire()
            or any(
                attempt[key] != getattr(ctx, key)
                for key in ("run_id", "operation_id", "trace_id", "attempt_id")
            )
            or budget["reservation"]["status"] != "reserved"
            or not attempt["dispatched"]
            or budget["ledger"]["cancel_requested"]
            or budget["ledger"]["overdrawn"]
        ):
            raise reject("runner_budget_denied", "Actual attempt no longer permits admission", 409)
        lease = copy(
            await self.leases.current(
                Ref.model_validate(record["lease_ref"]),
                command["fencing_token"],
                ctx,
                holder=Principal.model_validate(record["holder"]),
            )
        )
        validate_contract("ExecutionLease", lease)
        config = await self.configuration.current()
        deadlines = [
            ctx.deadline,
            budget["ledger"]["deadline"],
            attempt["deadline"],
            lease["expires_at"],
            root["expires_at"],
            device["source"]["expires_at"],
        ]
        expiry = instant(command["expires_at"])
        if not self.devices.now() < expiry <= min(instant(d) for d in deadlines):
            raise reject("runner_deadline_denied", "Command deadline exceeds current sources", 409)
        if "signature" in command:
            await require_none(
                self.signer.verify(copy(command), device_id=device["device_id"]),
                "runner_signature_protocol_invalid",
            )
        return {
            "request": request,
            "device": device,
            "run": run,
            "budget": budget,
            "lease": lease,
            "root": root,
            "configuration": config,
        }

    async def collect(self, record: Payload, actor: Principal) -> Payload:
        deadline = instant(record["command"]["expires_at"])
        seconds = max(0, (deadline - self.devices.now()).total_seconds())
        async with asyncio.timeout(seconds):
            first = await self._collect(record, actor)
            second = await self._collect(record, actor)
        if first != second or self.devices.now() >= deadline:
            raise reject("runner_authority_changed", "Authority changed during checks", 412)
        return second

    async def register(
        self, request: Payload, meta: RequestMeta, *, authenticated_service: Principal
    ) -> Payload:
        self.devices.service(authenticated_service)
        validate_contract("RunnerCommandRegisterRequest", request)
        registered = await self._request(Ref.model_validate(request["request_ref"]))
        device = await self.devices._load(request["device_ref"]["id"])
        actor = Principal.model_validate(device["source"]["actor"])
        draft = {
            "command_id": request["command_id"],
            "operation_id": registered["context"]["operation_id"],
            "request_ref": request["request_ref"],
            "trusted_context": registered["context"],
            "parameters": registered["parameters"],
            "fencing_token": request["fencing_token"],
            "expires_at": request["expires_at"],
        }
        validate_contract("RunnerCommandDraft", draft)
        provisional = {
            "command": draft,
            "device_ref": request["device_ref"],
            "lease_ref": request["lease_ref"],
            "holder": authenticated_service.wire(),
        }
        sources = await self.collect(provisional, actor)
        attempt_key = "attempt-" + parameter_hash(
            {
                key: registered["context"].get(key)
                for key in ("principal", "run_id", "operation_id", "trace_id", "attempt_id")
            }
        )
        # Recover actual registered signed bytes instead of re-signing after response loss.
        try:
            old = await self.store.get(self.devices.controller, COMMANDS, draft["command_id"])
        except StoreMissing:
            old = None
        if old:
            record = old.payload
        else:
            assert self.signer is not None
            seconds = max(0, (instant(draft["expires_at"]) - self.devices.now()).total_seconds())
            async with asyncio.timeout(seconds):
                signed = copy(await self.signer.sign(copy(draft), device_id=device["device_id"]))
            validate_contract("RunnerCommand", signed)
            if {k: v for k, v in signed.items() if k != "signature"} != draft:
                raise reject("runner_signer_binding_denied", "Signer changed command fields", 403)
            record = {
                **provisional,
                "command": signed,
                "root": sources["root"],
                "revision": 1,
                "state": "active",
            }
        validate_contract("RunnerCommandRecord", record)
        if (
            {k: v for k, v in record["command"].items() if k != "signature"} != draft
            or any(record[k] != provisional[k] for k in ("device_ref", "lease_ref", "holder"))
            or record["root"] != sources["root"]
            or record["state"] != "active"
        ):
            raise StoreConflict()
        await self.collect(record, actor)

        async def write(tx: RecordTransaction) -> Payload:
            actual = await tx.load(DEVICES, device["device_id"])
            if actual.payload != sources["device"]:
                raise StoreConflict()
            try:
                await tx.load(ATTEMPTS, attempt_key)
            except StoreMissing:
                pass
            else:
                raise StoreConflict("runner_attempt_already_registered")
            if self.devices.now() >= instant(draft["expires_at"]):
                raise reject("runner_deadline_denied", "Command expired while waiting", 409)
            await tx.write(COMMANDS, draft["command_id"], "RunnerCommandRecord", record)
            await tx.write(
                ATTEMPTS, attempt_key, "Ref", pin("content", draft["command_id"], record["command"])
            )
            return record

        result = await self.transactions.execute(
            self.devices.controller,
            AGGREGATE,
            meta,
            {
                "action": "command.register",
                "request": request,
                "service": authenticated_service.wire(),
            },
            write,
        )
        current = await self.record(draft["command_id"])
        if current != result:
            raise StoreConflict()
        await self.collect(current, actor)
        return current

    async def record(self, command_id: str) -> Payload:
        row = await self.store.get(self.devices.controller, COMMANDS, command_id)
        validate_contract("RunnerCommandRecord", row.payload)
        if (
            row.revision != row.payload["revision"]
            or row.payload["command"]["command_id"] != command_id
        ):
            raise StoreConflict()
        return row.payload

    async def read(self, command_ref: Ref, *, authenticated_principal: Principal) -> Payload:
        record = await self.record(command_ref.id)
        request = await self._request(Ref.model_validate(record["command"]["request_ref"]))
        if (
            record["command"]["trusted_context"] != request["context"]
            or record["command"]["parameters"] != request["parameters"]
        ):
            raise reject(
                "runner_command_binding_denied", "Command differs from independent request", 403
            )
        if command_ref.wire() != pin("content", command_ref.id, record["command"]):
            raise reject("runner_command_changed", "Command pin differs", 412)
        device = await self.devices.current(
            record["device_ref"]["id"], authenticated_principal=authenticated_principal
        )
        if device["source"]["owner"] != record["command"]["trusted_context"]["principal"]:
            raise reject("runner_owner_denied", "Command belongs to another owner", 403)
        if self.signer is None:
            raise CapabilityUnavailable("runner.control_signature_source")
        await require_none(
            self.signer.verify(copy(record["command"]), device_id=device["device_id"]),
            "runner_signature_protocol_invalid",
        )
        again = await self.record(command_ref.id)
        if again["command"] != record["command"]:
            raise StoreConflict()
        await self.devices.current(
            device["device_id"], authenticated_principal=authenticated_principal
        )
        return record

    async def revoke(
        self,
        command_id: str,
        expected_revision: int,
        meta: RequestMeta,
        *,
        authenticated_service: Principal,
    ) -> Payload:
        self.devices.service(authenticated_service)
        validate_contract("Revision", expected_revision)

        async def write(tx: RecordTransaction) -> Payload:
            row = await tx.load(COMMANDS, command_id)
            if row.revision != expected_revision:
                raise StoreConflict()
            result = {**row.payload, "revision": row.revision + 1, "state": "revoked"}
            await tx.write(COMMANDS, command_id, "RunnerCommandRecord", result, row.revision)
            return result

        return await self.transactions.execute(
            self.devices.controller,
            AGGREGATE,
            meta,
            {"action": "command.revoke", "id": command_id, "expected": expected_revision},
            write,
        )
