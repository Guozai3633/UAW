"""Actual bounded local text inspection, explicitly injected; no product registration."""

import hashlib
import math
import time

from uaw.shared.contracts import JsonObject, Principal, Ref, TrustedExecutionContext
from uaw.tool.errors import fail, validate_dependency
from uaw.tool.ports import ToolExecutorPort, ToolOutputVerifierPort
from uaw.tool.receipt_store import ToolResponseStore
from uaw.tool.schema import canonical, digest

MAX_TEXT_BYTES = 32768


def text_spec(provider_ref: Ref) -> JsonObject:
    """Return immutable versioned metadata; caller must explicitly register/bind it."""
    return {
        "id": "text.inspect",
        "version": "1",
        "description": "Inspect supplied UTF-8 text exactly",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string", "maxLength": MAX_TEXT_BYTES}},
            "required": ["text"],
            "additionalProperties": False,
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "characters": {"type": "integer", "minimum": 0},
                "utf8_bytes": {"type": "integer", "minimum": 0, "maximum": MAX_TEXT_BYTES},
                "lines": {"type": "integer", "minimum": 0},
                "sha256": {"type": "string", "minLength": 64, "maxLength": 64},
            },
            "required": ["characters", "utf8_bytes", "lines", "sha256"],
            "additionalProperties": False,
        },
        "categories": ["text"],
        "required_capabilities": ["tool.invoke"],
        "effect": "read",
        "provider_ref": provider_ref.wire(),
        "retry_policy_ref": {"kind": "policy", "id": "no-automatic-retry", "version": "1"},
    }


def inspect_text(text: str) -> JsonObject:
    if type(text) is not str:
        raise ValueError("Expected exact text")
    encoded = text.encode("utf-8")
    if len(encoded) > MAX_TEXT_BYTES:
        raise ValueError("Text exceeds UTF-8 byte limit")
    # Python splitlines handles CRLF as one line; trailing separators do not add a line.
    return {
        "characters": len(text),
        "utf8_bytes": len(encoded),
        "lines": len(text.splitlines()),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def check_text_binding(call: JsonObject, spec: JsonObject, provider_ref: Ref) -> str:
    validate_dependency("ValidatedCall", call, "text_adapter")
    if canonical(spec) != canonical(text_spec(provider_ref)) or call["tool_ref"] != {
        "kind": "configuration",
        "id": "text.inspect",
        "version": "1",
        "content_hash": digest(spec),
    }:
        raise fail(
            "executor_binding_conflict",
            "Executor only implements this exact text.inspect version",
            phase="text_adapter",
            category="conflict",
            status=409,
        )
    args = call["arguments"]
    if (
        type(args) is not dict
        or set(args) != {"text"}
        or type(args["text"]) is not str
        or call["arguments_hash"] != digest(args)
    ):
        raise ValueError("Text arguments differ from fixed call")
    return args["text"]


def text_estimates(currency: str = "USD") -> JsonObject:
    # Fixed local free tariff. This adapter creates no model/child/network charges.
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "model_calls": 0,
        "tool_calls": 1,
        "child_agents": 0,
        "wall_time_ms": 1000,
        "money": "0.00",
        "currency": currency,
    }


class TextInspectVerifier(ToolOutputVerifierPort):
    def __init__(self, provider_ref: Ref) -> None:
        self.provider_ref = provider_ref

    async def verify(
        self, data: JsonObject, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> None:
        text = check_text_binding(call, spec, self.provider_ref)
        if canonical(data) != canonical(inspect_text(text)):
            raise fail(
                "tool_output_invalid",
                "Stored output differs from actual text inspection",
                phase="normalize_result",
                category="conflict",
                status=409,
            )


class TextInspectExecutor(ToolExecutorPort):
    def __init__(
        self, source: ToolResponseStore, *, provider: Principal, currency: str = "USD"
    ) -> None:
        source.authenticate(provider)
        self.source, self.provider, self.currency = source, provider, currency

    def check(self, call: JsonObject, spec: JsonObject) -> None:
        inspect_text(check_text_binding(call, spec, self.source.provider_ref))

    async def execute(
        self, call: JsonObject, spec: JsonObject, ctx: TrustedExecutionContext
    ) -> JsonObject:
        started = time.perf_counter_ns()
        self.check(call, spec)
        data = inspect_text(check_text_binding(call, spec, self.source.provider_ref))
        measured_ms = math.ceil((time.perf_counter_ns() - started) / 1_000_000)
        usage: JsonObject = {
            "attempt_id": ctx.attempt_id,
            "billing_state": "confirmed",
            "resources": {**text_estimates(self.currency), "wall_time_ms": measured_ms},
        }
        # The strict receipt is returned only after actual response bytes/usage are durable.
        return await self.source.save_response(
            data, usage, ctx, authenticated_provider=self.provider
        )
