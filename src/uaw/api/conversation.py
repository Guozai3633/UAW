"""Authenticated conversation-v1 handlers; acceptance is distinct from execution."""

import json
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from uaw.composition import Container
from uaw.run.conversation_control import ConversationControls
from uaw.shared.contracts import Principal
from uaw.shared.conversation import (
    ConversationRequestMeta,
    RunClarificationAnswerRequest,
    RunCorrectionRequest,
)
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.schema import parse_json, validate_contract

OPERATIONS = frozenset(
    {
        "runs.conversation.get",
        "runs.clarification.get",
        "runs.clarification.answer",
        "runs.correction.create",
        "runs.continuation.get",
    }
)


async def control_body(
    request: Request, schema: str, maximum: int
) -> tuple[ConversationRequestMeta, dict[str, Any]]:
    if request.headers.get("content-type", "").split(";", 1)[0].lower() != "application/json":
        raise reject("content_type_invalid", "Application/json is required", 415)
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > maximum:
            raise reject("request_too_large", "Request exceeds the configured byte limit", 413)
    try:
        value = parse_json(bytes(data))
        if not isinstance(value, dict) or set(value) != {"meta", "payload"}:
            raise ValueError
        meta = ConversationRequestMeta.model_validate(value["meta"])
        payload = value["payload"]
        if not isinstance(payload, dict) or set(request.path_params) & set(payload):
            raise ValueError
        payload = {**payload, **request.path_params}
        validate_contract(schema, payload)
    except ValueError:
        raise reject(
            "request_invalid", "Request fields do not match the interface contract"
        ) from None
    return meta, payload


async def endpoint(
    request: Request,
    container: Container,
    actor: Principal,
    operation: str,
    schema: str,
    response_schema: str,
) -> JSONResponse:
    if container.records is None:
        raise CapabilityUnavailable("conversation.persistence")
    service = ConversationControls(container.records)
    if request.method == "GET":
        versions = request.headers.getlist("X-UAW-Schema-Version")
        if versions and versions != ["0.2"]:
            raise reject("schema_version_invalid", "Conversation reads use version 0.2")
        if request.query_params:
            raise reject("query_invalid", "Conversation read accepts path parameters only")
        payload = dict(request.path_params)
        try:
            validate_contract(schema, payload)
        except ValueError:
            raise reject("request_invalid", "Path fields do not match the contract") from None
        if operation == "runs.conversation.get":
            result = (await service.view(actor, payload["run_id"])).wire()
        elif operation == "runs.clarification.get":
            result = (
                await service.question(actor, payload["run_id"], payload["question_item_id"])
            ).wire()
        else:
            result = (await service.lookup(actor, payload["run_id"], payload["request_id"])).wire()
    else:
        meta, payload = await control_body(request, schema, container.settings.max_request_bytes)
        if operation == "runs.clarification.answer":
            parsed = RunClarificationAnswerRequest.model_validate_json(json.dumps(payload))
            result = (await service.answer(actor, parsed, meta)).wire()
        else:
            correction = RunCorrectionRequest.model_validate_json(json.dumps(payload))
            result = (await service.correct(actor, correction, meta)).wire()
    validate_contract(response_schema, result)
    wire = {"kind": "ok", "payload": result, "output_refs": []}
    name = "Http" + "".join(part.capitalize() for part in operation.split(".")) + "Result"
    validate_contract(name, wire)
    return JSONResponse(
        content=wire, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}
    )
