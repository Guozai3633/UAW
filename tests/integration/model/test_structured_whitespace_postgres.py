"""Real SQL receipts and budgets; provider HTTP is an explicit controlled fixture."""

import json

import httpx
import pytest

from tests.integration.model.test_gateway import case as case
from tests.integration.model.test_gateway import domain as domain
from tests.integration.model.test_gateway import reply
from uaw.shared.schema import validate_contract

pytestmark = pytest.mark.parametrize("case", [{"json_object_mode": True}], indirect=True)


@pytest.mark.parametrize("extra_field", [False, True])
async def test_literal_whitespace_retains_raw_usage_and_strict_schema(
    case, domain, principal, extra_field
):
    prose = "标题\n正文\t第二列\r\n结束"
    content = (
        '{"answer":'
        + json.dumps(prose, ensure_ascii=False)
        + (',"unauthorized":true}' if extra_field else "}")
    )
    for encoded, literal in [("\\n", "\n"), ("\\r", "\r"), ("\\t", "\t")]:
        content = content.replace(encoded, literal)
    raw = json.dumps(reply(content), ensure_ascii=False).encode()
    case.request.update(
        output_protocol="json_schema",
        output_schema={
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
            "additionalProperties": False,
        },
    )
    case.responses[:] = [httpx.Response(200, content=raw)]
    result = await case.model.generate(case.request, case.ctx)
    assert await case.model.generate(case.request, case.ctx) == result
    assert len(case.requests) == 1
    assert json.loads(case.requests[0].content)["response_format"] == {"type": "json_object"}
    attempt = (await domain[1].store.get(principal, "model.attempts", case.ctx.attempt_id)).payload
    assert await case.inputs.blobs.get(principal, attempt["response_ref"]["id"]) == raw
    assert attempt["usage"]["billing_state"] == "pending"
    ledger = (await domain[1].store.get(principal, "budget.ledgers", case.run["id"])).payload
    assert ledger["used"]["model_calls"] == 1
    assert ledger["used"]["input_tokens"] == 20 and ledger["used"]["output_tokens"] == 8
    assert ledger["billing_pending"] and ledger["held"]["money"] == "0.250000000"
    if extra_field:
        assert result["failure"]["code"] == "provider_structured_output_invalid"
        assert attempt["state"] == "failed" and "output_ref" not in attempt
    else:
        assert result["kind"] == "ok" and attempt["state"] == "received"
        output = result["payload"]
        assert output["structured_data"] == {"answer": prose}
        assert output["text"] == content and output["text_complete"]
        assert (
            await case.inputs.blobs.get(principal, attempt["output_ref"]["id"])
        ).decode() == content
        validate_contract("ModelOutput", output)
