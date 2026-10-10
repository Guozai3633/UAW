"""Two actual original SQL/file/crypto sources; routing and current grants controlled.

This test port is never installed as a product capability. Each entry pins an
independent original ctx; request identity/scope is checked before delegating.
"""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from tests.integration.tool.file_pipeline_fixture import approve_file, file_pipeline, recover_file
from uaw.shared.errors import reject
from uaw.tool.invocation.schema import normalize
from uaw.tool.providers.file_material import FileMaterialAdapter


class ControlledRegisteredMaterialReader:
    def __init__(self, entries):
        self.entries = entries
        self.calls = []
        self.before = None
        self.after = None

    async def read(self, ref, ctx):
        self.calls.append(ref.wire())
        if self.before:
            await self.before(ref, ctx)
        entry = self.entries.get(ref.id)
        if entry is None:
            raise reject("controlled_material_missing", "Original registered source missing", 503)
        original, reader = entry
        if (
            ctx.principal != original.principal
            or ctx.scope != original.scope
            or ctx.run_id != original.run_id
            or ctx.model_policy_ref != original.model_policy_ref
        ):
            raise reject(
                "controlled_material_scope_denied", "Current registered source denied", 403
            )
        material = await reader.read(ref, original)
        if self.after:
            await self.after(ref, ctx)
        return material


@pytest.fixture
async def material_pair(tool_case, tmp_path):
    pipelines = []
    for index in range(2):
        directory = tmp_path / str(index)
        directory.mkdir()
        p = await file_pipeline.__wrapped__(tool_case, directory)
        ctx = p.case.ctx.model_copy(
            update={
                "attempt_id": "set-original-attempt-" + str(index),
                "trace_id": "set-original-trace-" + str(index),
            }
        )
        p.raw["action_id"] = "set-original-action-" + str(index)
        p.case = replace(p.case, ctx=ctx, call=normalize(p.raw, p.case.registry))
        p.bridge.case = p.bridge.data_authority.case = p.case
        pipelines.append(p)
    return SimpleNamespace(pipelines=tuple(pipelines), ctx=pipelines[0].case.ctx)


async def exported_pair(pair, texts=None):
    materials = []
    for index, p in enumerate(pair.pipelines):
        if texts is not None:
            (p.root / "file.txt").write_bytes(texts[index].encode("utf-8"))
        await approve_file(p)
        actual = await p.facade.invoke(p.raw, p.case.ctx)
        assert actual["kind"] == "ok", actual
        materials.append(
            await FileMaterialAdapter(p.source).export(p.case.call["action_id"], p.case.ctx)
        )
    return tuple(materials)


def registered_reader(pair, materials, *, restart=False):
    entries = {}
    recovered = []
    for p, material in zip(pair.pipelines, materials, strict=True):
        source = recover_file(p) if restart else p
        recovered.append(source)
        entries[material.material_ref.id] = (p.case.ctx, FileMaterialAdapter(source.source))
    return ControlledRegisteredMaterialReader(entries), tuple(recovered)
