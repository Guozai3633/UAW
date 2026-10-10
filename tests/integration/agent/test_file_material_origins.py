"""Real SQL owning origins; original pipe/data authority remain controlled here."""

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from tests.integration.agent.test_file_bridge_postgres import bridge_case as bridge_case
from tests.integration.agent.test_file_bridge_postgres import case as case
from tests.integration.agent.test_file_bridge_postgres import domain as domain
from tests.integration.test_stage_wiring import container
from uaw.composition import assemble_file_tool
from uaw.run.file_context import (
    MATERIAL_INDEX,
    FileContextMaterials,
    RegisteredFileMaterialReader,
)
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.tool.providers.file_material_set import FileMaterialSetAdapter
from uaw.tool.registry import ToolRegistry


@pytest.fixture
async def material_case(bridge_case, tmp_path):
    p = bridge_case
    registry = ToolRegistry()
    registry.register(p.spec, expected_revision=0)
    c = container(p.c.commands.store, p.c.domain[0], tmp_path)
    binding = assemble_file_tool(
        c,
        registry=registry,
        tool_ref=Ref.model_validate(registry.reference(registry.snapshot()[1][0])),
        provider=p.bridge.provider,
        bridge=p.bridge,
        recovery_access=p.access,
        signatures=p.signatures,
        money_ceiling="0.10",
    )
    await binding.executor.execute(p.call, p.spec, p.ctx)
    origins = FileContextMaterials(c.records, c.configuration.platform, binding.materials)
    fragment = await origins.register(
        p.call["action_id"], p.ctx, authenticated_service=c.configuration.platform
    )
    material = await binding.materials.export(p.call["action_id"], p.ctx)
    p.path.unlink()
    current = p.ctx.model_copy(
        update={"operation_id": "later-context-build", "attempt_id": "later-context-attempt"}
    )
    restarted = FileContextMaterials(c.records, c.configuration.platform, binding.materials)
    return SimpleNamespace(
        p=p,
        c=c,
        origins=restarted,
        reader=RegisteredFileMaterialReader(restarted),
        material=material,
        fragment=fragment,
        current=current,
        sent_before_read=list(p.session.sent),
    )


async def test_material_origin_new_context_attempt_reads_original_no_new_execution(material_case):
    m = material_case
    result = await FileMaterialSetAdapter(m.reader).read((m.material.material_ref,), m.current)
    assert result.materials == (m.material,)
    reading = await m.origins.read(m.fragment, m.current)
    assert reading.trust == "external" and reading.ref == m.fragment
    assert reading.text == m.material.text and not reading.required
    assert m.p.session.opens == 1 and m.p.session.sent.count("command") == 1
    assert all(kind == "recover" for kind in m.p.session.sent[1:])
    assert await m.origins.read_many((m.fragment,), m.current) == (reading,)
    row = await m.c.records.get(m.current.principal, MATERIAL_INDEX, m.material.material_ref.id)
    assert row.revision == 1 and row.schema_name == "Ref" and row.payload == m.fragment.wire()
    assert (
        await m.origins.register(
            m.p.call["action_id"], m.p.ctx, authenticated_service=m.c.configuration.platform
        )
        == m.fragment
    )
    assert (
        await m.c.records.get(m.current.principal, MATERIAL_INDEX, m.material.material_ref.id)
        == row
    )


@pytest.mark.parametrize("change", ["session", "model", "policy", "deadline"])
async def test_material_origin_changed_scope_never_reuses_original_context(material_case, change):
    m = material_case
    ctx = m.current
    if change == "session":
        ctx = ctx.model_copy(
            update={
                "principal": ctx.principal.model_copy(update={"auth_session_id": "other-session"})
            }
        )
    elif change == "model":
        ctx = ctx.model_copy(
            update={
                "model_policy_ref": (ctx.model_policy_ref or ctx.capability_policy_ref).model_copy(
                    update={"id": "other-model"}
                )
            }
        )
    elif change == "policy":
        ctx = ctx.model_copy(
            update={
                "capability_policy_ref": ctx.capability_policy_ref.model_copy(
                    update={"version": "99"}
                )
            }
        )
    else:
        deadline = datetime.fromisoformat(ctx.deadline.replace("Z", "+00:00")) + timedelta(
            seconds=1
        )
        ctx = ctx.model_copy(update={"deadline": deadline.isoformat()})
    with pytest.raises(DomainError) as error:
        await m.reader.read(m.material.material_ref, ctx)
    assert error.value.failure.code == "file_context_scope_denied"
    assert m.p.session.opens == 1 and m.p.session.sent == m.sent_before_read


async def test_material_origin_exact_hash_required_and_controller_only_registration(material_case):
    m = material_case
    changed = m.material.material_ref.model_copy(update={"content_hash": "0" * 64})
    with pytest.raises(DomainError) as error:
        await m.reader.read(changed, m.current)
    assert error.value.failure.code == "file_context_material_pin_changed"
    with pytest.raises(DomainError) as error:
        await m.origins.register(
            m.p.call["action_id"], m.p.ctx, authenticated_service=m.current.principal
        )
    assert error.value.failure.code == "file_context_controller_denied"
    with pytest.raises(DomainError) as error:
        await m.reader.export(m.p.call["action_id"], m.current)
    assert error.value.status_code == 503
    assert m.p.session.opens == 1


async def test_material_origin_current_data_revocation_prevents_context_return(material_case):
    m = material_case
    m.p.access.allowed = False
    with pytest.raises(DomainError) as error:
        await FileMaterialSetAdapter(m.reader).read((m.material.material_ref,), m.current)
    assert error.value.failure.code == "fixture_data_revoked"
    assert m.p.session.opens == 1 and m.p.session.sent == m.sent_before_read
