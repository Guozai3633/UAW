"""Implemented wire endpoints only. JSON Schema DTOs are validated at ingress and egress."""

from collections.abc import Awaitable, Callable, Coroutine
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.routing import APIRoute

from uaw.api.authentication import authenticate
from uaw.api.browser import COOKIE, authenticated
from uaw.composition import Container
from uaw.shared.contracts import RequestMeta
from uaw.shared.errors import CapabilityUnavailable, DomainError, reject
from uaw.shared.observability import report_request_failure
from uaw.shared.schema import ContractViolation, parse_json, validate_contract

# id, method, route, request schema, response schema. All unlisted contracts remain unavailable.
ROUTES = (
    ("web.launch", "POST", "/v1/web/launch", "WebLaunchRequest", "WebLaunch"),
    ("web.session.exchange", "POST", "/v1/web/session", "WebSessionExchangeRequest", "WebSession"),
    ("web.session.get", "GET", "/v1/web/session", "WebSessionGetRequest", "WebSession"),
    (
        "web.session.logout",
        "DELETE",
        "/v1/web/session",
        "WebSessionLogoutRequest",
        "Acknowledgement",
    ),
    (
        "conversations.create",
        "POST",
        "/v1/conversations",
        "ConversationsCreateRequest",
        "Conversation",
    ),
    (
        "conversations.get",
        "GET",
        "/v1/conversations/{conversation_id}",
        "ConversationsGetRequest",
        "Conversation",
    ),
    (
        "conversations.items",
        "GET",
        "/v1/conversations/{conversation_id}/items",
        "ConversationsItemsRequest",
        "ItemPage",
    ),
    (
        "turns.submit",
        "POST",
        "/v1/conversations/{conversation_id}/turns",
        "TurnsSubmitRequest",
        "RunRecord",
    ),
    ("runs.get", "GET", "/v1/runs/{run_id}", "RunsGetRequest", "RunRecord"),
    ("tasks.frame", "GET", "/v1/tasks/{task_id}/frame", "TasksFrameRequest", "TaskFrame"),
    ("runs.control", "POST", "/v1/runs/{run_id}/control", "RunsControlRequest", "Acknowledgement"),
    (
        "approvals.get",
        "GET",
        "/v1/approvals/{approval_id}",
        "ApprovalsGetRequest",
        "ApprovalRequest",
    ),
    (
        "approvals.decide",
        "POST",
        "/v1/approvals/{approval_id}/decisions",
        "ApprovalsDecideRequest",
        "ApprovalGrant",
    ),
    (
        "events.read",
        "GET",
        "/v1/conversations/{conversation_id}/events",
        "EventsReadRequest",
        "EventPage",
    ),
    (
        "events.payload",
        "GET",
        "/v1/events/{event_id}/payload",
        "EventsPayloadRequest",
        "EventPayload",
    ),
    ("models.list", "GET", "/v1/models", "ModelsListRequest", "ModelPage"),
    (
        "admin.providers.configure",
        "POST",
        "/v1/admin/providers",
        "AdminProvidersConfigureRequest",
        "ProviderBinding",
    ),
    (
        "admin.providers.revoke",
        "DELETE",
        "/v1/admin/providers/{provider_id}",
        "AdminProvidersRevokeRequest",
        "ProviderBinding",
    ),
    (
        "admin.models.register",
        "POST",
        "/v1/admin/models",
        "AdminModelsRegisterRequest",
        "ModelCatalogEntry",
    ),
    (
        "admin.policies.register",
        "POST",
        "/v1/admin/policies",
        "AdminPoliciesRegisterRequest",
        "Ref",
    ),
    (
        "admin.environments.register",
        "POST",
        "/v1/admin/environments",
        "AdminEnvironmentsRegisterRequest",
        "EnvironmentTemplate",
    ),
    ("admin.secrets.put", "POST", "/v1/admin/secrets", "AdminSecretsPutRequest", "SecretReceipt"),
    (
        "admin.configuration.stage",
        "POST",
        "/v1/admin/configuration/drafts",
        "AdminConfigurationStageRequest",
        "ConfigurationVersion",
    ),
    (
        "admin.configuration.get",
        "GET",
        "/v1/admin/configuration",
        "AdminConfigurationGetRequest",
        "ConfigurationVersion",
    ),
    (
        "admin.configuration.validate",
        "POST",
        "/v1/admin/configuration/drafts/{configuration_id}/validate",
        "AdminConfigurationValidateRequest",
        "ValidationReport",
    ),
    (
        "admin.configuration.activate",
        "POST",
        "/v1/admin/configuration/drafts/{configuration_id}/activate",
        "AdminConfigurationActivateRequest",
        "ConfigurationVersion",
    ),
)


def result_schema(operation: str) -> str:
    return "Http" + "".join(part.capitalize() for part in operation.split(".")) + "Result"


async def body(request: Request, schema: str, maximum: int) -> tuple[RequestMeta, dict[str, Any]]:
    if request.headers.get("content-type", "").split(";", 1)[0].lower() != "application/json":
        raise reject("content_type_invalid", "Application/json is required", 415)
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > maximum:
            raise reject("request_too_large", "Request exceeds the configured byte limit", 413)
    try:
        value = parse_json(bytes(data))
        if (
            not isinstance(value, dict)
            or set(value) != {"meta", "payload"}
            or not isinstance(value["payload"], dict)
        ):
            raise ValueError
        meta = RequestMeta.model_validate(value["meta"])
        payload = value["payload"]
        for key, path_value in request.path_params.items():
            if key in payload:
                raise ValueError
            payload[key] = path_value
        validate_contract(schema, payload)
    except ValueError:
        raise reject(
            "request_invalid", "Request fields do not match the interface contract"
        ) from None
    return meta, payload


def install_routes(app: FastAPI, container: Container) -> None:
    class SafeRoute(APIRoute):
        def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
            route_handler = super().get_route_handler()

            async def protected(request: Request) -> Response:
                try:
                    return await route_handler(request)
                except DomainError:
                    raise
                except Exception as exc:
                    report_request_failure(self.name, type(exc).__name__)
                    error = reject(
                        "internal_error", "Control-plane request failed", 500, "infrastructure"
                    )
                    raise error from None

            return protected

    def handler(
        operation: str, method: str, schema: str, response_schema: str
    ) -> Callable[[Request], Awaitable[JSONResponse]]:
        async def endpoint(request: Request) -> JSONResponse:
            browser = container.browser_sessions
            if operation == "web.launch":
                actor = authenticate(request, container.settings)
                if request.headers.get("cookie"):
                    raise reject("web_launch_denied", "CLI user bearer required", 403, "permission")
            elif operation == "web.session.exchange":
                if browser is None:
                    raise CapabilityUnavailable("web.browser_session")
                browser.guard(request)
                if request.headers.get("authorization") or COOKIE in request.cookies:
                    raise reject(
                        "web_exchange_denied",
                        "Unauthenticated launch exchange required",
                        403,
                        "permission",
                    )
                actor = None
            else:
                actor = await authenticated(
                    request, container, admin=operation.startswith("admin.")
                )
            if operation in ("web.session.get", "web.session.logout") and (
                actor is None or not actor.auth_session_id.startswith("web-session-")
            ):
                raise reject(
                    "authentication_required", "Browser session required", 401, "permission"
                )
            configuration, run, records = (
                container.configuration,
                container.run_service,
                container.records,
            )
            if configuration is None or run is None or records is None:
                raise CapabilityUnavailable("development_persistence")
            if method == "GET":
                if set(request.path_params) & set(request.query_params):
                    raise reject(
                        "query_invalid", "Path parameters cannot be supplied as query fields"
                    )
                payload: dict[str, Any] = {**request.path_params, **dict(request.query_params)}
                if len(request.query_params.multi_items()) != len(request.query_params):
                    raise reject("query_invalid", "Duplicate query parameters are not allowed")
                if "limit" in payload:
                    if not payload["limit"].isascii() or not payload["limit"].isdigit():
                        raise reject("query_invalid", "Page limit must be an integer")
                    payload["limit"] = int(payload["limit"])
                try:
                    validate_contract(schema, payload)
                except ContractViolation:
                    raise reject(
                        "request_invalid", "Query does not match the interface contract"
                    ) from None
                meta = None
            else:
                meta, payload = await body(request, schema, container.settings.max_request_bytes)
            result: dict[str, Any]
            cookie: str | None = None
            if operation.startswith("web."):
                if browser is None:
                    raise CapabilityUnavailable("web.browser_session")
                if operation == "web.session.exchange":
                    result, cookie = await browser.exchange(payload["launch_code"])
                else:
                    assert actor is not None
                    if operation == "web.launch":
                        assert meta is not None
                        result = await browser.launch(actor, meta)
                    elif operation == "web.session.get":
                        result = browser.public(await browser.principal(actor))
                    else:
                        assert meta is not None
                        result = await browser.logout(actor, meta)
            elif actor is None:
                raise reject(
                    "authentication_required", "Authenticated user required", 401, "permission"
                )
            elif operation == "conversations.get":
                result = (
                    await records.get(actor, "conversations", payload["conversation_id"])
                ).payload
            elif operation == "runs.get":
                result = await run.get_run(actor, payload["run_id"])
            elif operation == "approvals.get":
                if container.approvals is None:
                    raise CapabilityUnavailable("approval.persistence")
                result = await container.approvals.get(actor, payload["approval_id"])
            elif operation == "tasks.frame":
                if container.intent_service is None:
                    raise CapabilityUnavailable("task_understanding")
                result = await container.intent_service.frames.current(actor, payload["task_id"])
            elif operation == "events.payload":
                result = (await records.get(actor, "event.payloads", payload["event_id"])).payload
            elif operation in ("conversations.items", "events.read"):
                result = await run.events.read(
                    actor,
                    payload["conversation_id"],
                    limit=payload.get("limit", 20),
                    cursor=payload.get("cursor"),
                    items=operation == "conversations.items",
                )
            elif operation == "models.list":
                result = await configuration.models()
                if "cursor" in payload or len(result["items"]) > payload.get("limit", 256):
                    raise CapabilityUnavailable("model_catalog_pagination")
            elif operation == "admin.configuration.get":
                result = await configuration.current()
            else:
                assert meta is not None
                if operation == "conversations.create":
                    result = await run.create_conversation(actor, payload, meta)
                elif operation == "turns.submit":
                    result = await run.submit(actor, payload, meta)
                elif operation == "runs.control":
                    result = await run.control(actor, payload, meta)
                elif operation == "approvals.decide":
                    if container.approvals is None:
                        raise CapabilityUnavailable("approval.persistence")
                    result = await container.approvals.decide(actor, payload, meta)
                elif operation == "admin.secrets.put":
                    result = await configuration.put_secret(actor, payload, meta)
                elif operation == "admin.providers.revoke":
                    result = await configuration.revoke_provider(
                        actor, payload["provider_id"], meta
                    )
                elif operation == "admin.configuration.stage":
                    result = await configuration.stage(actor, payload, meta)
                elif operation == "admin.configuration.validate":
                    result = await configuration.validate(actor, payload["configuration_id"], meta)
                elif operation == "admin.configuration.activate":
                    result = await configuration.activate(actor, payload["configuration_id"], meta)
                else:
                    kind = {
                        "admin.providers.configure": "provider",
                        "admin.models.register": "model",
                        "admin.policies.register": "policy",
                        "admin.environments.register": "environment",
                    }[operation]
                    result = await configuration.register(actor, kind, payload, meta)
            validate_contract(response_schema, result)
            wire = {"kind": "ok", "payload": result, "output_refs": []}
            if "revision" in result:
                wire["revision"] = result["revision"]
            validate_contract(result_schema(operation), wire)
            response = JSONResponse(
                status_code=202 if operation in ("turns.submit", "runs.control") else 200,
                content=wire,
                headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"},
            )
            if cookie is not None:
                response.set_cookie(
                    COOKIE,
                    cookie,
                    max_age=container.settings.browser_session_seconds,
                    httponly=True,
                    samesite="strict",
                    secure=False,
                    path="/v1",
                )
            if operation == "web.session.logout":
                response.delete_cookie(COOKIE, path="/v1", httponly=True, samesite="strict")
            return response

        return endpoint

    for operation, method, path, schema, response in ROUTES:
        app.router.add_api_route(
            path,
            handler(operation, method, schema, response),
            methods=[method],
            name=operation,
            operation_id=operation,
            route_class_override=SafeRoute,
        )
