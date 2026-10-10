"""Published A RegisteredFileBridge/C owning material sample; actual SQL and crypto.

Pipe/current route/root/provider registration inputs are controlled fixture sources,
not native human confirmation, production bootstrap or a model/Context acceptance.
C imports only the fixed accepted baseline and writes no A/Context/Agent code.
"""

import hashlib

import pytest

from tests.integration.agent.test_file_bridge_postgres import Session
from tests.integration.agent.test_file_bridge_postgres import bridge_case as bridge_case
from tests.integration.test_runner_control import case as case
from tests.integration.test_stage_wiring import container
from uaw.composition import assemble_file_tool
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.tool.invocation.schema import normalize
from uaw.tool.providers.file_material import FileMaterialAdapter
from uaw.tool.registry import ToolRegistry


def binding(p, tmp_path):
    registry = ToolRegistry()
    registry.register(p.spec, expected_revision=0)
    tool_ref = Ref.model_validate(registry.reference(registry.snapshot()[1][0]))
    c = container(p.c.commands.store, p.c.domain[0], tmp_path)
    return assemble_file_tool(
        c,
        registry=registry,
        tool_ref=tool_ref,
        provider=p.bridge.provider,
        bridge=p.bridge,
        recovery_access=p.access,
        signatures=p.signatures,
        money_ceiling="0.10",
    )


async def test_actual_a_bridge_c_material_fixed_command_ref_and_original_journal(
    bridge_case, tmp_path
):
    p = bridge_case
    b = binding(p, tmp_path)
    # Fixture owns an independently fixed Tool dispatch; no product/native grant claim.
    await b.executor.execute(p.call, p.spec, p.ctx)
    material = await FileMaterialAdapter(b.receipts).export(p.call["action_id"], p.ctx)
    assert material.text == "actual original 中😀\n"
    assert material.content["location"] == {"kind": "whole"}
    assert (
        material.file_hash
        == material.fragment_ref.content_hash
        == hashlib.sha256(material.text.encode()).hexdigest()
    )
    assert material.command_ref.id == p.bridge.command_id(p.call, p.ctx)
    assert (
        material.usage["billing_state"] == "pending" and "money" not in material.usage["resources"]
    )
    p.path.unlink()
    fresh = Session(p.c, p.signatures, p.path, p.journal)
    p.bridge.pipe = p.client(fresh)
    restored = binding(p, tmp_path)
    again = await FileMaterialAdapter(restored.receipts).read(material.material_ref, p.ctx)
    assert again == material and fresh.opens == 0
    assert p.session.opens == 1 and set(fresh.sent) == {"recover"}
    assert p.ctx.budget_reservation_ref is None


async def test_a_bridge_lost_actual_reply_exports_original_material_without_new_open(
    bridge_case, tmp_path
):
    p = bridge_case
    b = binding(p, tmp_path)
    p.session.lose_reply = True
    with pytest.raises(TimeoutError):
        await b.executor.execute(p.call, p.spec, p.ctx)
    assert p.session.opens == 1
    p.path.unlink()
    fresh = Session(p.c, p.signatures, p.path, p.journal)
    p.bridge.pipe = p.client(fresh)
    material = await FileMaterialAdapter(binding(p, tmp_path).receipts).export(
        p.call["action_id"], p.ctx
    )
    assert material.text == "actual original 中😀\n"
    assert fresh.opens == 0 and set(fresh.sent) == {"recover"}


async def test_a_current_data_revoke_blocks_material_before_cached_ref_or_transport(
    bridge_case, tmp_path
):
    p = bridge_case
    b = binding(p, tmp_path)
    await b.executor.execute(p.call, p.spec, p.ctx)
    reader = FileMaterialAdapter(b.receipts)
    material = await reader.export(p.call["action_id"], p.ctx)
    sent = list(p.session.sent)
    p.access.allowed = False
    with pytest.raises(DomainError) as denied:
        await reader.read(material.material_ref, p.ctx)
    assert denied.value.status_code == 403
    assert p.session.sent == sent and p.session.opens == 1


@pytest.mark.parametrize(
    "arguments",
    [
        {"location": {"kind": "lines", "start": 1, "end": 1}},
        {"location": {"kind": "text_span", "start": 0, "end": 1}},
        {"cursor": "requested-page"},
    ],
)
async def test_current_a_bridge_paging_snapshot_is_unavailable_never_open(bridge_case, arguments):
    p = bridge_case
    registry = ToolRegistry()
    registry.register(p.spec, expected_revision=0)
    call = normalize(
        {
            "tool_ref": p.call["tool_ref"],
            "action_id": p.call["action_id"],
            "arguments": {**p.call["arguments"], **arguments},
        },
        registry,
    )
    with pytest.raises(DomainError) as unavailable:
        await p.bridge.resolve(call, p.spec, p.ctx)
    assert unavailable.value.status_code == 503
    assert p.session.opens == 0 and p.session.sent == []


async def test_actual_a_16384_limit_rejects_larger_whole_without_truncation(bridge_case, tmp_path):
    p = bridge_case
    p.path.write_bytes(b"x" * 16385)
    b = binding(p, tmp_path)
    with pytest.raises(DomainError) as too_large:
        await b.executor.execute(p.call, p.spec, p.ctx)
    assert too_large.value.status_code == 413
    assert p.session.opens == 1
    with pytest.raises(DomainError):
        await FileMaterialAdapter(b.receipts).export(p.call["action_id"], p.ctx)
    assert p.session.opens == 1


@pytest.mark.parametrize("missing", ["routes", "pipe", "access", "signatures"])
async def test_a_production_material_missing_port_remains_explicitly_unavailable(
    bridge_case, tmp_path, missing
):
    p = bridge_case
    b = binding(p, tmp_path)
    setattr(p.bridge, missing, None)
    with pytest.raises(DomainError) as unavailable:
        await FileMaterialAdapter(b.receipts).export(p.call["action_id"], p.ctx)
    assert unavailable.value.status_code == 503
    assert p.session.opens == 0 and p.session.sent == []


@pytest.mark.parametrize("changed", ["device-version", "key"])
async def test_a_current_device_version_or_key_change_denies_old_material(
    bridge_case, tmp_path, changed
):
    p = bridge_case
    b = binding(p, tmp_path)
    await b.executor.execute(p.call, p.spec, p.ctx)
    reader = FileMaterialAdapter(b.receipts)
    material = await reader.export(p.call["action_id"], p.ctx)
    if changed == "key":
        p.c.signer.revoked = True
    else:
        from dataclasses import replace

        current = p.bridge.routes.current

        async def stale(*args):
            route = await current(*args)
            return replace(route, device_ref=route.device_ref.model_copy(update={"version": "999"}))

        p.bridge.routes.current = stale
    with pytest.raises(DomainError):
        await reader.read(material.material_ref, p.ctx)
    assert p.session.opens == 1
