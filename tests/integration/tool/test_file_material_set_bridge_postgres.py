"""Fixed published A bridge + C set; real SQL/crypto, controlled transport/authority.

No claim of installed/human source, production multi-attempt routing or model use.
"""

import pytest

from tests.integration.agent.test_file_bridge_postgres import Session
from tests.integration.agent.test_file_bridge_postgres import bridge_case as bridge_case
from tests.integration.test_runner_control import case as case
from tests.integration.tool.test_file_material_bridge_postgres import binding
from uaw.shared.errors import DomainError
from uaw.tool.providers.file_material import FileMaterialAdapter
from uaw.tool.providers.file_material_set import FileMaterialSetAdapter


async def test_published_a_bridge_set_preserves_original_call_command_and_restart(
    bridge_case, tmp_path
):
    p = bridge_case
    b = binding(p, tmp_path)
    await b.executor.execute(p.call, p.spec, p.ctx)
    reader = FileMaterialAdapter(b.receipts)
    material = await reader.export(p.call["action_id"], p.ctx)
    result = await FileMaterialSetAdapter(reader).read((material.material_ref,), p.ctx)
    assert result.materials == (material,) and result.refs == (material.material_ref,)
    assert material.command_ref.id == p.bridge.command_id(p.call, p.ctx)
    p.path.unlink()
    fresh = Session(p.c, p.signatures, p.path, p.journal)
    p.bridge.pipe = p.client(fresh)
    restored = FileMaterialSetAdapter(FileMaterialAdapter(binding(p, tmp_path).receipts))
    assert await restored.read(result.refs, p.ctx) == result
    assert fresh.opens == 0 and set(fresh.sent) == {"recover"}
    assert p.session.opens == 1 and p.ctx.budget_reservation_ref is None


async def test_published_a_original_reply_loss_set_recover_only_no_new_command(
    bridge_case, tmp_path
):
    p = bridge_case
    b = binding(p, tmp_path)
    p.session.lose_reply = True
    with pytest.raises(TimeoutError):
        await b.executor.execute(p.call, p.spec, p.ctx)
    p.path.unlink()
    fresh = Session(p.c, p.signatures, p.path, p.journal)
    p.bridge.pipe = p.client(fresh)
    reader = FileMaterialAdapter(binding(p, tmp_path).receipts)
    material = await reader.export(p.call["action_id"], p.ctx)
    result = await FileMaterialSetAdapter(reader).read((material.material_ref,), p.ctx)
    assert result.materials[0] == material and result.materials[0].text == "actual original 中😀\n"
    assert p.session.opens == 1 and fresh.opens == 0 and set(fresh.sent) == {"recover"}


async def test_published_a_data_revoke_set_ref_denied_before_transport(bridge_case, tmp_path):
    p = bridge_case
    b = binding(p, tmp_path)
    await b.executor.execute(p.call, p.spec, p.ctx)
    reader = FileMaterialAdapter(b.receipts)
    material = await reader.export(p.call["action_id"], p.ctx)
    sent = list(p.session.sent)
    p.access.allowed = False
    with pytest.raises(DomainError) as exc:
        await FileMaterialSetAdapter(reader).read((material.material_ref,), p.ctx)
    assert exc.value.status_code == 403 and p.session.sent == sent and p.session.opens == 1
