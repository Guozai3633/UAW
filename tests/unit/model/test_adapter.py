"""Protocol evidence only. The local HTTP fixture is not an LLM provider."""

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx
import pytest
from pydantic import SecretStr

from tests.integration.model.test_gateway import reply
from uaw.model.adapters import MAX_RESPONSE_BYTES, ChatCompletionsAdapter, tool_name
from uaw.model.contracts import ModelPrompt, ProviderFailure, ProviderRequest
from uaw.shared.schema import validate_contract


def request(endpoint: str = "https://protocol.invalid/v1") -> ProviderRequest:
    return ProviderRequest(
        endpoint,
        SecretStr("fixture-only-secret"),
        {
            "model_name": "fixture-model",
            "timeout_ms": 1000,
            "output_token_parameter": "max_completion_tokens",
            "allow_temperature": False,
            "reservation_money": "0.25",
        },
        {"max_output_tokens": 128},
        ModelPrompt(({"role": "user", "content": "Original prompt"},), (), 80),
        "text",
        None,
        "operation-fixture",
    )


async def test_actual_loopback_http_without_environment_proxy(monkeypatch):
    captured = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            captured.append(
                (
                    self.path,
                    self.headers["Authorization"],
                    json.loads(self.rfile.read(int(self.headers["Content-Length"]))),
                )
            )
            body = json.dumps(reply()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    adapter = ChatCompletionsAdapter()
    try:
        result = await adapter.generate(request(f"http://127.0.0.1:{server.server_port}/v1"))
        assert result.text == "Protocol fixture" and result.cached_input_tokens == 5
        assert captured[0][0] == "/v1/chat/completions"
        assert captured[0][1] == "Bearer fixture-only-secret"
        assert captured[0][2]["model"] == "fixture-model"
        assert captured[0][2]["max_completion_tokens"] == 128
        assert captured[0][2]["stream"] is False
    finally:
        await adapter.close()
        await asyncio.to_thread(server.shutdown)
        server.server_close()
        worker.join(timeout=2)


async def test_redirect_does_not_forward_credentials():
    captured = []

    async def redirect(req):
        captured.append(req)
        return httpx.Response(302, headers={"Location": "https://never-follow.invalid"})

    adapter = ChatCompletionsAdapter(httpx.AsyncClient(transport=httpx.MockTransport(redirect)))
    try:
        with pytest.raises(ProviderFailure) as failed:
            await adapter.generate(request())
        assert failed.value.failure.code == "provider_http_302" and len(captured) == 1
    finally:
        await adapter.close()


async def test_bounded_response_and_non_integral_usage():
    adapter = ChatCompletionsAdapter(
        httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda req: httpx.Response(200, content=b"x" * (MAX_RESPONSE_BYTES + 1)),
            )
        )
    )
    try:
        with pytest.raises(ProviderFailure, match="Model attempt failed") as failed:
            await adapter.generate(request())
        assert failed.value.failure.code == "provider_response_too_large"
    finally:
        await adapter.close()
    bad = reply()
    bad["usage"]["prompt_tokens"] = 20.0
    with pytest.raises(ProviderFailure) as failed:
        ChatCompletionsAdapter.parse(json.dumps(bad).encode(), request())
    assert failed.value.failure.code == "provider_usage_invalid"


def test_tool_proposals_bind_to_registered_schema_and_stable_action():
    tool = {
        "id": "file.read",
        "version": "1",
        "description": "Read-only fixture",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
        "output_schema": {"type": "object"},
        "categories": [],
        "required_capabilities": [],
        "effect": "read",
        "provider_ref": {"kind": "provider", "id": "fixture-tool", "version": "1"},
        "retry_policy_ref": {"kind": "policy", "id": "fixture-retry", "version": "1"},
    }
    validate_contract("ToolSpec", tool)
    base = request()
    req = ProviderRequest(
        base.endpoint,
        base.credential,
        base.settings,
        base.config,
        ModelPrompt(base.prompt.messages, (tool,), 80),
        "tool_calls",
        None,
        base.operation_id,
    )
    data = reply("")
    data["choices"][0]["finish_reason"] = "tool_calls"
    data["choices"][0]["message"]["tool_calls"] = [
        {
            "id": "provider-call-1",
            "type": "function",
            "function": {"name": tool_name(tool), "arguments": '{"path":"src/main.py"}'},
        }
    ]
    result = ChatCompletionsAdapter.parse(json.dumps(data).encode(), req)
    validate_contract("ToolCall", result.tool_calls[0])
    assert result.tool_calls[0]["tool_ref"]["id"] == "file.read"
    data["choices"][0]["message"]["tool_calls"][0]["id"] = "provider-call-2"
    assert (
        ChatCompletionsAdapter.parse(json.dumps(data).encode(), req).tool_calls == result.tool_calls
    )
    data["choices"][0]["message"]["tool_calls"][0]["function"]["name"] = "unregistered"
    with pytest.raises(ProviderFailure) as failed:
        ChatCompletionsAdapter.parse(json.dumps(data).encode(), req)
    assert failed.value.failure.code == "provider_unknown_tool"
