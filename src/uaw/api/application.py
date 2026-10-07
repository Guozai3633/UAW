from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from uaw import __version__
from uaw.api.documentation import install_openapi
from uaw.api.routes import install_routes
from uaw.composition import Container
from uaw.shared.errors import DomainError, error_result


def create_app(container: Container) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await container.start()
        app.state.container = container
        try:
            yield
        finally:
            await container.close()

    app = FastAPI(title="UAW Runtime", version=__version__, lifespan=lifespan)

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_result(exc),
        )

    @app.get("/health/live", include_in_schema=False)
    async def liveness() -> dict[str, Any]:
        return {"status": "alive", "version": __version__}

    @app.get("/health/ready", include_in_schema=False)
    async def readiness() -> JSONResponse:
        return JSONResponse(
            status_code=200 if container.started else 503,
            content={
                "status": "ready" if container.started else "starting",
                "profile": container.settings.profile,
                "runtime_capabilities": container.bindings.availability(),
                "persistence": "postgresql" if container.database else "not_configured",
                "services": {
                    "configuration": container.configuration is not None,
                    "run_admission": container.run_service is not None,
                    "resource_ledger": container.budgets is not None,
                    "agent_execution": container.bindings.agent is not None,
                },
            },
        )

    install_routes(app, container)
    install_openapi(app)
    return app
