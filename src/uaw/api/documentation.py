"""Publish schemas for implemented operations only, with authentication and wire bodies."""

import copy
import json
import re
from typing import Any

from fastapi import FastAPI

from uaw.api.routes import ROUTES, result_schema
from uaw.shared.schema import contract_schema


def install_openapi(app: FastAPI) -> None:
    def build() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        definitions = copy.deepcopy(contract_schema()["$defs"])
        paths: dict[str, Any] = {}
        for operation, method, path, request_type, _ in ROUTES:
            request = copy.deepcopy(definitions[request_type])
            path_fields = re.findall(r"{([^}]+)}", path)
            entry: dict[str, Any] = {
                "operationId": operation,
                "security": [{"developmentBearer": []}],
                "x-required-role": "admin" if operation.startswith("admin.") else "user",
                "description": "Implemented development control-plane operation.",
                "parameters": [
                    {"name": key, "in": "path", "required": True, "schema": {"$ref": "#/$defs/ID"}}
                    for key in path_fields
                ],
                "responses": {},
            }
            if operation.startswith("web.session."):
                entry["security"] = [] if operation.endswith("exchange") else [{"webCookie": []}]
                entry["x-required-role"] = (
                    "public-launch-exchange" if operation.endswith("exchange") else "user"
                )
            elif not operation.startswith("admin.") and operation != "web.launch":
                entry["security"] = [{"developmentBearer": []}, {"webCookie": []}]
            if operation.startswith("web.session."):
                entry["parameters"].append(
                    {
                        "name": "Origin",
                        "in": "header",
                        "required": method != "GET",
                        "schema": {"type": "string"},
                    }
                )
            if method != "GET" and operation != "web.launch":
                entry["parameters"].append(
                    {
                        "name": "X-UAW-CSRF",
                        "in": "header",
                        "required": operation == "web.session.logout",
                        "schema": {"$ref": "#/$defs/Hash"},
                        "description": "Required for authenticated cookie writes.",
                    }
                )
            for key in path_fields:
                request["properties"].pop(key, None)
                if key in request["required"]:
                    request["required"].remove(key)
            if method == "GET":
                entry["parameters"].extend(
                    {
                        "name": key,
                        "in": "query",
                        "required": key in request["required"],
                        "schema": value,
                    }
                    for key, value in request["properties"].items()
                )
            else:
                entry["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "meta": {"$ref": "#/$defs/RequestMeta"},
                                    "payload": request,
                                },
                                "required": ["meta", "payload"],
                                "additionalProperties": False,
                            }
                        }
                    },
                }
            code = "202" if operation in ("turns.submit", "runs.control") else "200"
            for status in (code, "401", "403", "404", "409", "412", "413", "422", "500", "503"):
                entry["responses"][status] = {
                    "description": "Typed operation result",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/$defs/{result_schema(operation)}"}
                        }
                    },
                }
            paths.setdefault(path, {})[method.lower()] = entry
        value = {
            "openapi": "3.1.0",
            "info": {"title": app.title, "version": app.version},
            "paths": paths,
            "components": {
                "schemas": definitions,
                "securitySchemes": {
                    "developmentBearer": {"type": "http", "scheme": "bearer"},
                    "webCookie": {"type": "apiKey", "in": "cookie", "name": "uaw_web_session"},
                },
            },
        }
        app.openapi_schema = json.loads(
            json.dumps(value).replace("#/$defs/", "#/components/schemas/")
        )
        return app.openapi_schema

    app.openapi = build  # type: ignore[method-assign]
