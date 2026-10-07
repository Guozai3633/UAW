import asyncio
import os
import socket
from pathlib import Path

import httpx
import pytest
import uvicorn
from fastapi.testclient import TestClient
from pydantic import SecretStr

from uaw.api.application import create_app
from uaw.composition import compose
from uaw.infrastructure.db.session import Database
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.shared.errors import CapabilityUnavailable
from uaw.shared.settings import ConfigurationError, Settings


def settings() -> Settings:
    return Settings(profile="development", development_principal_id="u1")


def test_lifespan_and_unimplemented_capabilities() -> None:
    container = compose(settings())
    assert not container.started
    with TestClient(create_app(container)) as client:
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert not any(response.json()["runtime_capabilities"].values())
        assert client.post("/v1/agents/invoke", json={"approved": True}).status_code == 404
        with pytest.raises(CapabilityUnavailable):
            container.bindings.require("agent")
    assert not container.started


def test_missing_configuration_and_public_development_host_fail(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        Settings.from_file(tmp_path / "missing.toml")
    path = tmp_path / "invalid.toml"
    path.write_text(
        'profile="development"\nhost="0.0.0.0"\ndevelopment_principal_id="u1"\n',
        encoding="utf-8",
    )
    with pytest.raises(ConfigurationError):
        Settings.from_file(path)


def test_missing_secret_variable_is_reported_without_secret_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("UAW_TEST_DATABASE_URL", raising=False)
    path = tmp_path / "database.toml"
    path.write_text(
        'profile="development"\ndevelopment_principal_id="u1"\n'
        'database_url_env="UAW_TEST_DATABASE_URL"\n',
        encoding="utf-8",
    )
    with pytest.raises(ConfigurationError, match="UAW_TEST_DATABASE_URL"):
        Settings.from_file(path)


async def test_actual_http_server_starts_and_closes() -> None:
    container = compose(settings())
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(create_app(container), log_level="error", proxy_headers=False)
    )
    running = asyncio.create_task(server.serve(sockets=[listener]))
    try:
        async with asyncio.timeout(10):
            while not server.started:
                if running.done():
                    await running
                    pytest.fail("Server ended before startup")
                await asyncio.sleep(0.01)
            async with httpx.AsyncClient(trust_env=False) as client:
                response = await client.get(f"http://127.0.0.1:{port}/health/live")
                assert response.status_code == 200
                assert response.json()["status"] == "alive"
    finally:
        server.should_exit = True
        await asyncio.wait_for(running, timeout=10)
        listener.close()
    assert not container.started


async def test_configured_database_is_checked_before_http_ready(
    database: Database, tmp_path: Path
) -> None:
    configured = Settings(
        profile="development",
        development_principal_id="u1",
        database_url=SecretStr(os.environ["UAW_TEST_DATABASE_URL"]),
        blob_directory=tmp_path,
    )
    container = compose(configured)
    with TestClient(
        create_app(container), backend_options={"loop_factory": control_plane_loop}
    ) as client:
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["persistence"] == "postgresql"
        assert response.json()["runtime_capabilities"]["run"]
        assert not response.json()["services"]["agent_execution"]
    assert not container.started
