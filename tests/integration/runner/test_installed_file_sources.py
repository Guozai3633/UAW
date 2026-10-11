"""D A8 chain: real Web/SQL/Windows keys and child, labelled controlled decisions."""

import asyncio
from datetime import UTC, datetime

from tests.integration.runner.installed_file_fixture import installed_file_case
from tests.integration.test_browser_sessions import web as web


async def test_a8_sources_original_web_owner_os_roles_and_pipe(web, tmp_path, monkeypatch):
    async with installed_file_case(web, tmp_path, monkeypatch) as p:
        launch = p.container.installed_lifecycle.active.launch
        assert p.grant.owner == p.owner and p.grant.workspace_ref == p.workspace
        assert len(launch.keys) == 2 and {k.role for k in launch.keys} == {"control", "device"}
        assert launch.helper.identity.pid != __import__("os").getpid()
        assert p.bindings.bridge.pipe.session is launch.connection.session
        assert p.bindings.control.commands.signer is not None
        assert p.bindings.bridge.signatures.verify_document(
            {
                **(
                    await asyncio.to_thread(
                        launch.state.get, p.grant.selection_ticket_id, now=datetime.now(UTC)
                    )
                ).document(),
                "signature": p.grant.selection_signature,
            },
            device_id=p.grant.device_id,
            domain="root-selection",
        )
        assert p.metrics["sends"] == [] and (await p.child_metrics())["opens"] == 0
