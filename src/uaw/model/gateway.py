"""Durable one-owner claims, bounded same-model retries and conservative attempt accounting."""

import asyncio
import hashlib
import json
from contextlib import suppress
from datetime import UTC, datetime
from time import monotonic

from pydantic import SecretStr

from uaw.infrastructure.db.records import PostgresRecordStore, parameter_hash
from uaw.infrastructure.db.transactions import (
    RecordTransaction,
    TransactionalStore,
    reference,
    timestamp,
)
from uaw.model.capability import bounded_schema
from uaw.model.contracts import (
    ModelPrompt,
    Payload,
    ProviderFailure,
    ProviderRequest,
    ProviderResponse,
)
from uaw.model.policy import PolicyResolver, Selection
from uaw.model.ports import ModelInputPort, ModelProviderPort
from uaw.run.budget import BudgetService
from uaw.run.facade import zero_resources
from uaw.shared.contracts import RequestMeta, TrustedExecutionContext
from uaw.shared.errors import DomainError, error_result, reject
from uaw.shared.observability import report_request_failure
from uaw.shared.schema import validate_contract
from uaw.shared.stores import BlobStorePort, StoreConflict


def request_meta(action: str, identity: str) -> RequestMeta:
    return RequestMeta(
        request_id=action + "-" + hashlib.sha256(identity.encode()).hexdigest(),
        schema_version="0.1",
    )


class ModelGateway:
    def __init__(
        self,
        store: PostgresRecordStore,
        policies: PolicyResolver,
        inputs: ModelInputPort,
        budgets: BudgetService,
        blobs: BlobStorePort,
        adapter: ModelProviderPort,
    ) -> None:
        self.store, self.policies, self.inputs = store, policies, inputs
        self.budgets, self.blobs, self.adapter = budgets, blobs, adapter
        self.transactions = TransactionalStore(store.database)

    async def close(self) -> None:
        await self.adapter.close()

    async def generate(self, request: Payload, ctx: TrustedExecutionContext) -> Payload:
        validate_contract("ModelCall", request)
        if not ctx.run_id or request["attempt_id"] != ctx.attempt_id:
            raise reject(
                "model_attempt_scope_denied", "Model call requires its trusted Run attempt", 403
            )
        selection = await self.policies.resolve(request["model_config"], ctx)
        prompt = await self.inputs.resolve(request["context_snapshot_ref"], ctx)
        protocol = request["output_protocol"]
        if protocol not in selection.model["capabilities"]:
            raise reject(
                "model_protocol_unsupported", "Protocol is not approved for the selected model", 409
            )
        if protocol == "json_schema":
            bounded_schema(request["output_schema"])
            if request["output_schema"].get("type") != "object":
                raise reject(
                    "model_output_schema_unsupported", "Structured output requires an object schema"
                )
            prompt = ModelPrompt(
                prompt.messages,
                prompt.tools,
                prompt.estimated_tokens + len(json.dumps(request["output_schema"]).encode()) + 64,
            )
        elif "output_schema" in request:
            raise reject("model_schema_unexpected", "Only structured output accepts output_schema")
        if (
            prompt.estimated_tokens + selection.config["max_output_tokens"]
            > selection.model["context_limit_tokens"]
        ):
            raise reject("model_context_limit", "Input and output reserve exceed the model window")
        if protocol == "tool_calls":
            if not prompt.tools:
                raise reject(
                    "model_tools_unavailable", "No approved tool definitions are available", 409
                )
            for tool in prompt.tools:
                validate_contract("ToolSpec", tool)
                bounded_schema(tool["input_schema"])
                if not set(tool["required_capabilities"]).issubset(ctx.scope.capabilities):
                    raise reject(
                        "model_tool_capability_denied",
                        "Tool candidate exceeds trusted capabilities",
                        403,
                    )
                if tool.get("feature_flag"):
                    await self.policies.configuration.require_capability(
                        tool["feature_flag"],
                        selection.binding["configuration_ref"],
                        ctx.scope.wire(),
                        implemented=False,
                        boundary="discovery",
                    )
        credential = None
        if "credential_handle" in selection.provider:
            credential = await self.policies.configuration.credentials.resolve(
                selection.provider["credential_handle"]
            )
        deadline = datetime.fromisoformat(ctx.deadline.replace("Z", "+00:00"))
        if deadline <= datetime.now(UTC):
            raise reject("model_deadline_expired", "Execution deadline has passed", 409, "timeout")
        digest = parameter_hash({"request": request, "context": ctx.wire()})
        aggregate = f"conversation:{ctx.scope.conversation_id}"

        async def claim(tx: RecordTransaction) -> Payload:
            await tx.write(
                "model.invocations",
                ctx.attempt_id,
                "ModelInvocation",
                {
                    "id": ctx.attempt_id,
                    "run_id": ctx.run_id,
                    "request_hash": digest,
                    "request": request,
                    "operation_id": ctx.operation_id,
                    "trace_id": ctx.trace_id,
                    "state": "claimed",
                    "created_at": timestamp(),
                },
            )
            return {"new": True}

        claimed = await self.transactions.execute(
            ctx.principal,
            aggregate,
            request_meta("model-claim", ctx.attempt_id),
            {"action": "model.claim", "hash": digest},
            claim,
            on_replay=lambda previous: {"new": False},
        )
        if not claimed["new"]:
            previous = await self.store.get(ctx.principal, "model.invocations", ctx.attempt_id)
            if previous.payload["state"] == "finished":
                return previous.payload["result"]  # type: ignore[no-any-return]
            raise reject(
                "model_invocation_pending",
                "Existing send intent requires reconciliation; no request was resent",
                409,
                "unknown_effect",
            )

        result: Payload
        try:
            result = await self._run(request, ctx, selection, prompt, credential)
        except asyncio.CancelledError:
            result = error_result(
                reject(
                    "model_cancelled",
                    "Model call was interrupted; billing may be pending",
                    409,
                    "cancelled",
                )
            )
            await asyncio.shield(self._finish(ctx, result))
            raise
        except DomainError as exc:
            result = error_result(exc)
        except Exception as exc:
            report_request_failure("ModelRuntime.generate", type(exc).__name__)
            result = error_result(
                reject(
                    "model_internal_failure",
                    "Model operation could not be finalized; inspect its receipt",
                    500,
                    "infrastructure",
                )
            )
        await self._finish(ctx, result)
        return result

    async def _finish(self, ctx: TrustedExecutionContext, result: Payload) -> None:
        validate_contract("RuntimeModelruntimeGenerateResult", result)

        async def finish(tx: RecordTransaction) -> Payload:
            row = await tx.load("model.invocations", ctx.attempt_id)
            value = {**row.payload, "state": "finished", "result": result}
            await tx.write(
                "model.invocations", ctx.attempt_id, "ModelInvocation", value, row.revision
            )
            return result

        await self.transactions.execute(
            ctx.principal,
            f"conversation:{ctx.scope.conversation_id}",
            request_meta("model-finish", ctx.attempt_id),
            {"result": result},
            finish,
        )

    async def _run(
        self,
        request: Payload,
        ctx: TrustedExecutionContext,
        selection: Selection,
        prompt: ModelPrompt,
        credential: SecretStr | None,
    ) -> Payload:
        for index in range(2):
            attempt_ctx = (
                ctx
                if index == 0
                else ctx.model_copy(
                    update={
                        "attempt_id": "retry-"
                        + hashlib.sha256(f"{ctx.attempt_id}:{index}".encode()).hexdigest(),
                    }
                )
            )
            selection = await self.policies.resolve(request["model_config"], attempt_ctx)
            provider_request = ProviderRequest(
                selection.provider["endpoint"],
                credential,
                selection.provider["settings"],
                selection.config,
                prompt,
                request["output_protocol"],
                request.get("output_schema"),
                ctx.operation_id,
            )
            try:
                output, output_ref = await self._attempt(
                    provider_request, attempt_ctx, ctx.attempt_id
                )
                return {"kind": "ok", "payload": output, "output_refs": [output_ref]}
            except ProviderFailure as exc:
                if not exc.safe_retry or index == 1:
                    return error_result(exc)
                # Backoff is within the original deadline; every retry owns a new reservation.
                await asyncio.sleep(0.1)
        raise AssertionError("Bounded attempt loop did not terminate")

    async def _reserve(self, ctx: TrustedExecutionContext, request: ProviderRequest) -> Payload:
        assert ctx.run_id
        settings = request.settings
        for retry in range(2):
            ledger = (await self.store.get(ctx.principal, "budget.ledgers", ctx.run_id)).payload
            remaining_ms = int(
                (
                    datetime.fromisoformat(ctx.deadline.replace("Z", "+00:00")) - datetime.now(UTC)
                ).total_seconds()
                * 1000
            )
            if remaining_ms <= 0:
                raise reject(
                    "model_deadline_expired", "Execution deadline has passed", 409, "timeout"
                )
            estimates = {
                **zero_resources(ledger["limits"]["currency"]),
                "input_tokens": request.prompt.estimated_tokens,
                "output_tokens": request.config["max_output_tokens"],
                "model_calls": 1,
                "wall_time_ms": min(remaining_ms, settings["timeout_ms"]),
                "money": settings["reservation_money"],
            }
            reserve = {
                "reservation_id": "reservation-"
                + hashlib.sha256(ctx.attempt_id.encode()).hexdigest(),
                "parent_run_id": ctx.run_id,
                "estimates": estimates,
                "deadline": ctx.deadline,
                "expected_ledger_revision": ledger["revision"],
            }
            try:
                return await self.budgets.reserve(
                    ctx.principal, reserve, request_meta("model-reserve", ctx.attempt_id), ctx
                )
            except StoreConflict as exc:
                if exc.failure.code != "revision_conflict" or retry == 1:
                    raise
        raise AssertionError("Bounded reservation loop did not terminate")

    async def _attempt(
        self, request: ProviderRequest, ctx: TrustedExecutionContext, invocation_id: str
    ) -> tuple[Payload, Payload]:
        reservation = await self._reserve(ctx, request)
        reservation_ref = reference("reservation", reservation["id"], reservation["revision"])
        try:
            metadata: Payload = {
                "id": ctx.attempt_id,
                "run_id": ctx.run_id,
                "invocation_id": invocation_id,
                "actual_config": request.config,
                "state": "prepared",
                "created_at": timestamp(),
            }
            await self.store.put(
                ctx.principal,
                "model.attempts",
                ctx.attempt_id,
                "ModelAttemptRecord",
                metadata,
                expected_revision=0,
                request_id="prepared",
            )
        except Exception:
            await self.budgets.release(
                ctx.principal, reservation_ref, request_meta("model-release", ctx.attempt_id), ctx
            )
            raise
        try:
            await self.policies.resolve(request.config, ctx)
            ack = await self.budgets.dispatch(
                ctx.principal, reservation_ref, request_meta("model-dispatch", ctx.attempt_id), ctx
            )
        except DomainError as exc:
            await self.budgets.release(
                ctx.principal, reservation_ref, request_meta("model-release", ctx.attempt_id), ctx
            )
            await self.store.put(
                ctx.principal,
                "model.attempts",
                ctx.attempt_id,
                "ModelAttemptRecord",
                {**metadata, "state": "failed", "failure": exc.failure.wire()},
                expected_revision=1,
                request_id="not-dispatched",
            )
            raise
        if ack["status"] != "accepted":
            raise ProviderFailure("model_dispatch_already_recorded", category="unknown_effect")
        started = monotonic()
        response = None
        failure: ProviderFailure | None = None
        cancelled = False
        try:
            response = await self._cancelable(request, ctx)
        except asyncio.CancelledError:
            failure, cancelled = ProviderFailure("model_cancelled", category="cancelled"), True
        except ProviderFailure as exc:
            failure = exc
        except DomainError as exc:
            failure = ProviderFailure(exc.failure.code, category=exc.failure.category)
        except Exception:
            failure = ProviderFailure("provider_adapter_failure", category="infrastructure")
        observed = response.resources if response else failure.resources if failure else {}
        usage: Payload = {
            "attempt_id": ctx.attempt_id,
            "billing_state": "pending",
            "resources": {
                **{
                    k: v
                    for k, v in zero_resources(reservation["estimates"]["currency"]).items()
                    if k not in ("money", "input_tokens", "output_tokens")
                },
                **observed,
                "model_calls": 1,
                "wall_time_ms": max(0, int((monotonic() - started) * 1000)),
            },
        }
        if response and response.cached_input_tokens is not None:
            usage["cached_input_tokens"] = response.cached_input_tokens
        if response and response.receipt_id:
            usage["provider_receipt_id"] = response.receipt_id
        raw = response.raw if response else failure.response_raw if failure else None
        if raw:
            raw_hash = await self.blobs.put(ctx.principal, raw)
            metadata["response_ref"] = {**reference("blob", raw_hash), "content_hash": raw_hash}
        metadata.update(state="received" if response else "failed", usage=usage)
        if failure:
            metadata["failure"] = failure.failure.wire()
        output: Payload = {}
        if response:
            content_hash = await self.blobs.put(ctx.principal, response.text.encode())
            content_ref = {**reference("blob", content_hash), "content_hash": content_hash}
            metadata["output_ref"] = content_ref
            output = {
                "attempt_id": ctx.attempt_id,
                "actual_config": {**request.config, "response_model_name": response.model_name},
                "text": response.text[:16384],
                "text_complete": len(response.text) <= 16384,
                "content_ref": content_ref,
                "tool_calls": list(response.tool_calls),
                "finish_reason": response.finish_reason,
                "usage": usage,
            }
            if response.structured_data is not None:
                output["structured_data"] = response.structured_data
            validate_contract("ModelOutput", output)
        await asyncio.shield(
            self.store.put(
                ctx.principal,
                "model.attempts",
                ctx.attempt_id,
                "ModelAttemptRecord",
                metadata,
                expected_revision=1,
                request_id="observed",
            )
        )
        # Settle against the latest CAS version; local contention does not repeat provider work.
        for retry in range(3):
            ledger = await self.store.get(ctx.principal, "budget.ledgers", ctx.run_id or "")
            try:
                await asyncio.shield(
                    self.budgets.settle(
                        ctx.principal,
                        {
                            "reservation_ref": reservation_ref,
                            "usage": usage,
                            "expected_ledger_revision": ledger.revision,
                        },
                        request_meta("model-settle", ctx.attempt_id),
                        ctx,
                        status="cancelled" if cancelled else "failed" if failure else "succeeded",
                    )
                )
                break
            except StoreConflict as exc:
                if exc.failure.code != "revision_conflict" or retry == 2:
                    raise
        if cancelled:
            raise asyncio.CancelledError
        if failure:
            raise failure
        await self.store.put(
            ctx.principal,
            "model.outputs",
            ctx.attempt_id,
            "ModelOutput",
            output,
            expected_revision=0,
            request_id="output",
        )
        return output, reference("content", ctx.attempt_id)

    async def _cancelable(
        self, request: ProviderRequest, ctx: TrustedExecutionContext
    ) -> ProviderResponse:
        duration = min(
            request.settings["timeout_ms"] / 1000,
            (
                datetime.fromisoformat(ctx.deadline.replace("Z", "+00:00")) - datetime.now(UTC)
            ).total_seconds(),
        )
        task = asyncio.create_task(self.adapter.generate(request))
        try:
            async with asyncio.timeout(max(0, duration)):
                while True:
                    done, _ = await asyncio.wait({task}, timeout=0.1)
                    ledger = (
                        await self.store.get(ctx.principal, "budget.ledgers", ctx.run_id or "")
                    ).payload
                    if ledger["cancel_requested"]:
                        raise ProviderFailure("model_run_cancelled", category="cancelled")
                    access = await self.store.get(
                        ctx.principal, "execution.policies", ctx.capability_policy_ref.id
                    )
                    if str(access.revision) != ctx.capability_policy_ref.version:
                        raise ProviderFailure("model_capability_changed", category="authorization")
                    live = (
                        await self.store.get(
                            self.policies.configuration.platform,
                            "providers",
                            request.config["provider_ref"]["id"],
                        )
                    ).payload
                    if live["state"] == "revoked":
                        raise ProviderFailure("provider_revoked", category="authorization")
                    if done:
                        return task.result()
        except TimeoutError:
            raise ProviderFailure("provider_timeout", category="timeout") from None
        finally:
            if not task.done():
                task.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await task
